#!/bin/bash

# RTX Trading System - Server Setup Script
# Run this script ON your DigitalOcean droplet to set everything up

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${PURPLE}"
cat << "EOF"
 ██████╗ ████████╗██╗  ██╗    ████████╗██████╗  █████╗ ██████╗ ██╗███╗   ██╗ ██████╗ 
 ██╔══██╗╚══██╔══╝╚██╗██╔╝    ╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║██╔════╝ 
 ██████╔╝   ██║    ╚███╔╝        ██║   ██████╔╝███████║██║  ██║██║██╔██╗ ██║██║  ███╗
 ██╔══██╗   ██║    ██╔██╗        ██║   ██╔══██╗██╔══██║██║  ██║██║██║╚██╗██║██║   ██║
 ██║  ██║   ██║   ██╔╝ ██╗       ██║   ██║  ██║██║  ██║██████╔╝██║██║ ╚████║╚██████╔╝
 ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝ 

 🚀 SERVER SETUP & AUTOMATED LAUNCH
 ☁️  One-command server deployment
EOF
echo -e "${NC}"

echo -e "${CYAN}🚀 Setting up RTX Trading System on this server${NC}"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ This script must be run as root${NC}"
   echo -e "${YELLOW}💡 Please run: sudo bash setup_server.sh${NC}"
   exit 1
fi

echo -e "${GREEN}✅ Running as root${NC}"

# Update system
echo -e "${BLUE}📦 Updating system packages...${NC}"
apt-get update && apt-get upgrade -y

# Install Docker if not installed
if ! command -v docker &> /dev/null; then
    echo -e "${BLUE}🐳 Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
    rm get-docker.sh
    echo -e "${GREEN}✅ Docker installed${NC}"
else
    echo -e "${GREEN}✅ Docker already installed${NC}"
fi

# Install Docker Compose if not installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${BLUE}🔧 Installing Docker Compose...${NC}"
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✅ Docker Compose installed${NC}"
else
    echo -e "${GREEN}✅ Docker Compose already installed${NC}"
fi

# Install Git if not installed
if ! command -v git &> /dev/null; then
    echo -e "${BLUE}📚 Installing Git...${NC}"
    apt-get install -y git
    echo -e "${GREEN}✅ Git installed${NC}"
else
    echo -e "${GREEN}✅ Git already installed${NC}"
fi

# Configure firewall
echo -e "${BLUE}🔥 Configuring firewall...${NC}"
ufw --force enable
ufw allow ssh
ufw allow 80
ufw allow 443
ufw allow 7496  # IBKR live port
ufw allow 7497  # IBKR paper port
ufw allow 3000  # Grafana
ufw allow 9090  # Prometheus
ufw allow 5900  # VNC
echo -e "${GREEN}✅ Firewall configured${NC}"

# Create application directory
APP_DIR="/opt/rtx-trading"
echo -e "${BLUE}📁 Creating application directory: $APP_DIR${NC}"
mkdir -p $APP_DIR
cd $APP_DIR

# Collect API keys and configuration
echo -e "${CYAN}🔑 Configuration Setup${NC}"
echo ""

# OpenAI API Key
while [[ -z "$OPENAI_API_KEY" ]]; do
    read -p "🤖 OpenAI API Key (required): " OPENAI_API_KEY
    if [[ -z "$OPENAI_API_KEY" ]]; then
        echo -e "${RED}❌ OpenAI API key is required for the trading system${NC}"
    fi
done

# Telegram Bot Token (optional)
read -p "📱 Telegram Bot Token (optional, press Enter to skip): " TELEGRAM_BOT_TOKEN
if [[ -n "$TELEGRAM_BOT_TOKEN" ]]; then
    read -p "📱 Telegram Chat ID: " TELEGRAM_CHAT_ID
fi

# IBKR Credentials (optional)
read -p "🏦 IBKR Username (optional, press Enter to skip): " IBKR_USERNAME
if [[ -n "$IBKR_USERNAME" ]]; then
    read -s -p "🏦 IBKR Password: " IBKR_PASSWORD
    echo ""
fi

# Trading Configuration
echo -e "${YELLOW}⚙️  Trading Configuration:${NC}"
read -p "💰 Enable Trading? (y/N): " -n 1 -r ENABLE_TRADING
echo ""
if [[ $ENABLE_TRADING =~ ^[Yy]$ ]]; then
    TRADING_ENABLED="true"
    read -p "📄 Paper Trading? (Y/n): " -n 1 -r PAPER_MODE
    echo ""
    if [[ $PAPER_MODE =~ ^[Nn]$ ]]; then
        PAPER_TRADING="false"
        echo -e "${RED}⚠️  LIVE TRADING MODE ENABLED - USE WITH EXTREME CAUTION!${NC}"
        read -p "Are you sure? Type 'CONFIRM' to proceed: " CONFIRM
        if [[ "$CONFIRM" != "CONFIRM" ]]; then
            echo -e "${YELLOW}Switching to paper trading for safety${NC}"
            PAPER_TRADING="true"
        fi
    else
        PAPER_TRADING="true"
    fi
else
    TRADING_ENABLED="false"
    PAPER_TRADING="true"
fi

# Create .env file
echo -e "${BLUE}📝 Creating environment configuration...${NC}"
cat > .env << EOL
# RTX Trading System Environment
TRADING_ENABLED=${TRADING_ENABLED}
PAPER_TRADING=${PAPER_TRADING}
PREDICTION_ONLY=false
IBKR_REQUIRED=false
AUTO_CONNECT_IBKR=true

# API Keys
OPENAI_API_KEY=${OPENAI_API_KEY}
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}

# IBKR Credentials
IBKR_USERNAME=${IBKR_USERNAME}
IBKR_PASSWORD=${IBKR_PASSWORD}

# System Configuration
STARTING_CAPITAL=1000
MAX_POSITION_SIZE=200
MAX_DAILY_LOSS=50
LOG_LEVEL=INFO
PREDICTION_INTERVAL_MINUTES=15
CONFIDENCE_THRESHOLD=0.35

# Monitoring
GRAFANA_PASSWORD=rtx2024
EOL

# Set secure permissions on .env
chmod 600 .env
echo -e "${GREEN}✅ Environment file created securely${NC}"

# Create Docker Compose file
echo -e "${BLUE}🐳 Creating Docker Compose configuration...${NC}"
cat > docker-compose.yml << 'EOL'
version: '3.8'

services:
  rtx-trading:
    build: .
    container_name: rtx-trading-app
    restart: unless-stopped
    env_file: .env
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    ports:
      - "8000:8000"
    depends_on:
      - redis
    networks:
      - trading-network

  redis:
    image: redis:7-alpine
    container_name: rtx-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - trading-network

  grafana:
    image: grafana/grafana:latest
    container_name: rtx-grafana
    restart: unless-stopped
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=rtx2024
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - trading-network

  prometheus:
    image: prom/prometheus:latest
    container_name: rtx-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - trading-network

volumes:
  redis_data:
  grafana_data:
  prometheus_data:

networks:
  trading-network:
    driver: bridge
EOL

# Create Dockerfile
echo -e "${BLUE}🏗️  Creating Dockerfile...${NC}"
cat > Dockerfile << 'EOL'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data

# Run the trading system
CMD ["python", "run_server.py"]
EOL

# Create monitoring directory and config
echo -e "${BLUE}📊 Setting up monitoring...${NC}"
mkdir -p monitoring
cat > monitoring/prometheus.yml << 'EOL'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'rtx-trading'
    static_configs:
      - targets: ['rtx-trading:8000']
EOL

# Create run_server.py if it doesn't exist
if [[ ! -f "run_server.py" ]]; then
    echo -e "${BLUE}🎯 Creating server runner...${NC}"
    cat > run_server.py << 'EOL'
#!/usr/bin/env python3
"""
RTX Trading System - Production Server
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.scheduler import TradingScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TradingServer:
    def __init__(self):
        self.scheduler = TradingScheduler()
        self.running = False
    
    async def start(self):
        """Start the trading server"""
        logger.info("🚀 Starting RTX Trading Server")
        
        try:
            self.running = True
            await self.scheduler.start()
            
            # Keep running until shutdown
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Server error: {e}")
            raise
    
    async def stop(self):
        """Stop the trading server"""
        logger.info("🛑 Stopping RTX Trading Server")
        self.running = False
        await self.scheduler.stop()

# Global server instance
server = TradingServer()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"📡 Received signal {signum}")
    asyncio.create_task(server.stop())

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    logger.info("🎯 RTX Trading System - Production Mode")
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("👋 Shutdown requested by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)
EOL
fi

# Ensure the repository code is in place
if [[ ! -d "src" ]]; then
    echo -e "${YELLOW}⚠️  No application source code found${NC}"
    echo -e "${BLUE}📥 Please upload your RTX trading code to: $APP_DIR${NC}"
    echo -e "${YELLOW}💡 You can use: scp -r ./src root@YOUR_SERVER_IP:$APP_DIR/${NC}"
    echo -e "${YELLOW}💡 Or git clone your repository here${NC}"
    read -p "Press Enter when you've uploaded the code..."
fi

# Create necessary directories
mkdir -p logs data

# Start the system
echo -e "${CYAN}🚀 Starting RTX Trading System...${NC}"
echo ""

# Build and start containers
docker-compose up -d --build

# Wait a moment for containers to start
sleep 10

# Check if containers are running
echo -e "${BLUE}📊 Checking system status...${NC}"
docker-compose ps

# Get server IP
SERVER_IP=$(curl -s ifconfig.me)

# Final status
echo ""
echo -e "${GREEN}🎉 RTX TRADING SYSTEM IS LIVE!${NC}"
echo -e "${CYAN}================================${NC}"
echo ""
echo -e "${BLUE}📊 Server Details:${NC}"
echo "   • Server IP: $SERVER_IP"
echo "   • Application Directory: $APP_DIR"
echo ""
echo -e "${BLUE}🔗 Access URLs:${NC}"
echo "   • Grafana (monitoring): http://$SERVER_IP:3000"
echo "     └─ Username: admin | Password: rtx2024"
echo "   • Prometheus (metrics): http://$SERVER_IP:9090"
echo ""
echo -e "${BLUE}📱 Monitoring:${NC}"
if [[ -n "$TELEGRAM_BOT_TOKEN" ]]; then
    echo -e "   • Telegram notifications: ${GREEN}Enabled ✅${NC}"
else
    echo -e "   • Telegram notifications: ${YELLOW}Disabled ⚠️${NC}"
fi
echo ""
echo -e "${BLUE}💰 Trading Mode:${NC}"
if [[ "$TRADING_ENABLED" == "true" ]]; then
    if [[ "$PAPER_TRADING" == "true" ]]; then
        echo -e "   • Mode: ${GREEN}Paper Trading (Safe)${NC} ✅"
    else
        echo -e "   • Mode: ${RED}Live Trading (Real Money)${NC} ⚠️"
    fi
else
    echo -e "   • Mode: ${YELLOW}Predictions Only${NC} 📊"
fi
echo ""
echo -e "${YELLOW}💡 Useful Commands:${NC}"
echo "   • View logs: docker logs rtx-trading-app -f"
echo "   • Restart system: docker-compose restart"
echo "   • Stop system: docker-compose down"
echo "   • Update system: docker-compose up -d --build"
echo "   • System status: docker-compose ps"
echo ""
echo -e "${GREEN}✅ Setup complete! Your RTX Trading System is autonomous and operational.${NC}"
echo -e "${PURPLE}🤖 The system will start making predictions and trades according to your configuration.${NC}"

# Save important info
cat > SYSTEM_INFO.txt << EOF
RTX Trading System - Server Information
=======================================

Server IP: $SERVER_IP
Installation Directory: $APP_DIR
Setup Date: $(date)

Access URLs:
- Grafana: http://$SERVER_IP:3000 (admin/rtx2024)
- Prometheus: http://$SERVER_IP:9090

Configuration:
- Trading Enabled: $TRADING_ENABLED
- Paper Trading: $PAPER_TRADING
- Telegram Notifications: $(if [[ -n "$TELEGRAM_BOT_TOKEN" ]]; then echo "Yes"; else echo "No"; fi)

Useful Commands:
- View logs: docker logs rtx-trading-app -f
- Restart: docker-compose restart
- Stop: docker-compose down
- Status: docker-compose ps
EOF

echo -e "${BLUE}💾 System info saved to: SYSTEM_INFO.txt${NC}"
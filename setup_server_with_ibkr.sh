#!/bin/bash

# RTX Trading System - Complete Setup with IBKR Gateway
# Optimized for DigitalOcean droplets with IBKR integration
# Run this ON your DigitalOcean droplet: sudo bash setup_server_with_ibkr.sh

set -e

echo "🚀 RTX Trading System - Complete Setup with IBKR"
echo "================================================="
echo "💡 Installing AlgoSlayer + IBKR Gateway for autonomous trading"

# Check root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Run as root: sudo bash setup_server_with_ibkr.sh"
   exit 1
fi

echo "✅ Running as root"

# Check system resources
echo "🔍 Checking system resources..."
TOTAL_MEM=$(grep MemTotal /proc/meminfo | awk '{print $2}')
TOTAL_MEM_GB=$((TOTAL_MEM / 1024 / 1024))
echo "💾 Available RAM: ${TOTAL_MEM_GB}GB"

if [[ $TOTAL_MEM_GB -lt 2 ]]; then
    echo "⚠️  Warning: Less than 2GB RAM detected. IBKR Gateway needs 2GB+ recommended"
fi

# Update system
echo "📦 Updating system..."
apt-get update && apt-get upgrade -y

# Install essentials + GUI components for IBKR
echo "🔧 Installing essentials..."
apt-get install -y curl git python3 python3-pip python3-venv htop nano \
    xvfb x11vnc fluxbox openjdk-11-jdk wget unzip

# Configure swap for smaller droplets
if [[ $TOTAL_MEM_GB -lt 4 ]]; then
    echo "💾 Setting up swap for IBKR Gateway..."
    if [[ ! -f /swapfile ]]; then
        fallocate -l 2G /swapfile
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
        echo "✅ 2GB swap file created"
    else
        echo "✅ Swap already configured"
    fi
fi

# Configure firewall
echo "🔥 Configuring firewall..."
ufw --force enable
ufw allow ssh
ufw allow 80
ufw allow 443
ufw allow 3000  # Grafana
ufw allow 8000  # AlgoSlayer API
ufw allow 5900  # VNC for IBKR access
ufw allow 7497  # IBKR Paper Trading
ufw allow 7496  # IBKR Live Trading

# Create app directory
APP_DIR="/opt/rtx-trading"
echo "📁 Creating directory: $APP_DIR"
mkdir -p $APP_DIR
cd $APP_DIR

# Collect configuration
echo ""
echo "🔑 Configuration Setup"
echo "====================="

# Get IBKR credentials
echo "🏦 IBKR Configuration:"
read -p "📝 IBKR Username: " IBKR_USERNAME
read -s -p "🔒 IBKR Password: " IBKR_PASSWORD
echo ""

# Trading mode
read -p "💰 Enable Paper Trading? (Y/n): " -n 1 ENABLE_PAPER
echo ""
if [[ $ENABLE_PAPER =~ ^[Nn]$ ]]; then
    PAPER_TRADING="false"
    IBKR_PORT="7496"
    echo "⚠️  LIVE TRADING MODE ENABLED!"
    read -p "Type 'CONFIRM-LIVE' for live trading: " CONFIRM_LIVE
    if [[ "$CONFIRM_LIVE" != "CONFIRM-LIVE" ]]; then
        echo "❌ Live trading not confirmed. Exiting for safety."
        exit 1
    fi
else
    PAPER_TRADING="true"
    IBKR_PORT="7497"
    echo "✅ Paper trading mode selected"
fi

# Get OpenAI API key
while [[ -z "$OPENAI_API_KEY" ]]; do
    read -p "🤖 OpenAI API Key (required): " OPENAI_API_KEY
done

# Get Telegram info (optional)
read -p "📱 Telegram Bot Token (optional): " TELEGRAM_BOT_TOKEN
if [[ -n "$TELEGRAM_BOT_TOKEN" ]]; then
    read -p "📱 Telegram Chat ID: " TELEGRAM_CHAT_ID
fi

# Create comprehensive .env file
echo "📝 Creating .env file..."
cat > .env << EOF
# Trading Configuration
TRADING_ENABLED=true
PAPER_TRADING=${PAPER_TRADING}
PREDICTION_ONLY=false
IBKR_REQUIRED=true
AUTO_CONNECT_IBKR=true

# API Keys
OPENAI_API_KEY=${OPENAI_API_KEY}
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}

# IBKR Configuration
IBKR_HOST=127.0.0.1
IBKR_PAPER_PORT=7497
IBKR_LIVE_PORT=7496
IBKR_CLIENT_ID=1
IB_USERNAME=${IBKR_USERNAME}
IB_PASSWORD=${IBKR_PASSWORD}

# RTX-Focused Strategy Settings
STARTING_CAPITAL=1000
TARGET_RTX_SHARES=9
MAX_OPTION_INVESTMENT=400
MAX_DAILY_LOSS=200
CONFIDENCE_THRESHOLD=0.80
MIN_SIGNALS_AGREEING=3
MIN_EXPECTED_MOVE=0.03

# System Configuration
LOG_LEVEL=INFO
PREDICTION_INTERVAL_MINUTES=15
DAILY_REPORT_TIME=17:00
ENABLE_DAILY_REPORTS=true

# Database
DATABASE_URL=sqlite:///${APP_DIR}/data/rtx_trading.db

# Performance Settings for Server
MAX_MEMORY_USAGE=1500MB
PARALLEL_SIGNALS=true
CACHE_MARKET_DATA=true
EOF

chmod 600 .env
echo "✅ Environment configured"

# Create directories
mkdir -p logs data ibkr

# Install IBKR Gateway
echo ""
echo "🏦 Installing IBKR Gateway..."
cd $APP_DIR/ibkr

# Download IB Gateway (standalone version)
IBKR_VERSION="10.25.1d"
IBKR_INSTALLER="ibgateway-${IBKR_VERSION}-standalone-linux-x64.sh"

if [[ ! -f "$IBKR_INSTALLER" ]]; then
    echo "📥 Downloading IBKR Gateway..."
    wget "https://download2.interactivebrokers.com/installers/ibgateway/stable-standalone/${IBKR_INSTALLER}"
    chmod +x "$IBKR_INSTALLER"
fi

# Install IBKR Gateway
echo "📦 Installing IBKR Gateway..."
./"$IBKR_INSTALLER" -q -dir $APP_DIR/ibkr/IBJts

# Create IBKR configuration
echo "⚙️ Configuring IBKR Gateway..."
mkdir -p $APP_DIR/ibkr/config

# Create IBKR jts.ini configuration
cat > $APP_DIR/ibkr/config/jts.ini << EOF
[IBGateway]
TrustedIPs=127.0.0.1
LocalServerPort=${IBKR_PORT}
UseSSL=0
ReadOnlyApi=false
AcceptIncomingConnectionAction=accept
AllowBlindTradingAction=accept
EOF

# Create IBKR startup script
cat > $APP_DIR/ibkr/start_gateway.sh << 'SCRIPT_EOF'
#!/bin/bash
# IBKR Gateway startup script for headless server

APP_DIR="/opt/rtx-trading"
IBKR_DIR="$APP_DIR/ibkr/IBJts"
CONFIG_DIR="$APP_DIR/ibkr/config"

echo "🏦 Starting IBKR Gateway..."

# Set DISPLAY for headless operation
export DISPLAY=:1

# Start virtual X server if not running
if ! pgrep Xvfb > /dev/null; then
    echo "🖥️ Starting virtual display..."
    Xvfb :1 -screen 0 1024x768x24 &
    sleep 2
fi

# Start window manager
if ! pgrep fluxbox > /dev/null; then
    echo "🪟 Starting window manager..."
    DISPLAY=:1 fluxbox &
    sleep 1
fi

# Start VNC server for remote access
if ! pgrep x11vnc > /dev/null; then
    echo "📺 Starting VNC server on port 5900..."
    x11vnc -display :1 -nopw -listen localhost -xkb -ncache 10 -ncache_cr -forever &
fi

# Start IBKR Gateway
echo "🚀 Starting IBKR Gateway..."
cd "$IBKR_DIR"

# Use the configuration from our config directory
cp "$CONFIG_DIR/jts.ini" ./jts.ini

# Start gateway with auto-login
DISPLAY=:1 ./ibgateway &

echo "✅ IBKR Gateway started"
echo "📺 VNC access: ssh -L 5900:localhost:5900 root@your-server-ip"
echo "🌐 Then connect VNC viewer to localhost:5900"
SCRIPT_EOF

chmod +x $APP_DIR/ibkr/start_gateway.sh

# Check for application code
if [[ ! -d "src" ]]; then
    echo ""
    echo "⚠️  No application code found in current directory"
    echo "💡 If you're running from git repo, you're in the wrong directory"
    echo "📂 Expected to be in: /path/to/AlgoSlayer/"
    echo ""
    echo "🔄 Two options:"
    echo "   1. Run from AlgoSlayer repo: cd /path/to/AlgoSlayer && sudo ./setup_server_with_ibkr.sh"
    echo "   2. Or upload code manually:"
    echo "      scp -r ./src root@YOUR_SERVER_IP:$APP_DIR/"
    echo "      scp -r ./config root@YOUR_SERVER_IP:$APP_DIR/"
    echo "      scp requirements.txt run_server.py root@YOUR_SERVER_IP:$APP_DIR/"
    echo ""
    read -p "Press Enter when ready to continue..."
fi

# Create Python virtual environment
cd $APP_DIR
echo "🐍 Setting up Python virtual environment..."
python3 -m venv rtx-env
source rtx-env/bin/activate

# Install Python dependencies
if [[ -f "requirements.txt" ]]; then
    echo "📦 Installing Python dependencies..."
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt --no-cache-dir
    echo "✅ Dependencies installed"
else
    echo "📦 Installing core dependencies..."
    pip install yfinance pandas numpy scikit-learn aiohttp loguru ib_insync python-dotenv
    echo "✅ Core dependencies installed"
fi

# Create comprehensive systemd service
echo "⚙️ Creating system services..."

# AlgoSlayer service
cat > /etc/systemd/system/rtx-trading.service << EOF
[Unit]
Description=RTX Trading System - AI Trading with IBKR
After=network.target rtx-ibkr.service
Wants=rtx-ibkr.service

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/rtx-env/bin:/usr/bin:/usr/local/bin
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/rtx-env/bin/python run_server.py
Restart=always
RestartSec=30
StartLimitBurst=5

# Resource limits
MemoryLimit=1500M
MemoryAccounting=true
CPUQuota=80%

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=rtx-trading

# Security
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_DIR

[Install]
WantedBy=multi-user.target
EOF

# IBKR Gateway service
cat > /etc/systemd/system/rtx-ibkr.service << EOF
[Unit]
Description=IBKR Gateway for RTX Trading
After=network.target

[Service]
Type=forking
User=root
WorkingDirectory=$APP_DIR/ibkr
ExecStart=$APP_DIR/ibkr/start_gateway.sh
Restart=always
RestartSec=60
StartLimitBurst=3

# Resource limits
MemoryLimit=1000M
CPUQuota=50%

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=rtx-ibkr

[Install]
WantedBy=multi-user.target
EOF

# Create monitoring script
cat > $APP_DIR/monitor_system.sh << 'EOF'
#!/bin/bash
echo "=== RTX Trading System Status ==="
echo "Time: $(date)"
echo ""
echo "💰 Trading Services:"
echo "  AlgoSlayer: $(systemctl is-active rtx-trading)"
echo "  IBKR Gateway: $(systemctl is-active rtx-ibkr)"
echo ""
echo "🖥️ System Resources:"
echo "  Memory: $(free -h | grep Mem | awk '{print $3"/"$2}')"
echo "  Disk: $(df -h $APP_DIR | tail -1 | awk '{print $3"/"$2" ("$5")"}')"
echo ""
echo "📊 Network Ports:"
echo "  IBKR Gateway (${IBKR_PORT}): $(ss -tuln | grep :${IBKR_PORT} > /dev/null && echo 'OPEN' || echo 'CLOSED')"
echo "  VNC (5900): $(ss -tuln | grep :5900 > /dev/null && echo 'OPEN' || echo 'CLOSED')"
echo ""
echo "📋 Recent Logs:"
journalctl -u rtx-trading -n 3 --no-pager
EOF
chmod +x $APP_DIR/monitor_system.sh

# Enable and start services
systemctl daemon-reload
systemctl enable rtx-ibkr rtx-trading

# Get server info
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "Unable to detect")

echo ""
echo "🎉 RTX TRADING SYSTEM WITH IBKR SETUP COMPLETE!"
echo "==============================================="
echo ""
echo "🖥️ Server Info:"
echo "   IP: $SERVER_IP"
echo "   RAM: ${TOTAL_MEM_GB}GB"
echo "   Directory: $APP_DIR"
echo ""
echo "🏦 IBKR Configuration:"
echo "   Mode: $(if [[ "$PAPER_TRADING" == "true" ]]; then echo "Paper Trading"; else echo "LIVE TRADING"; fi)"
echo "   Port: $IBKR_PORT"
echo "   VNC Access: Port 5900"
echo ""
echo "🚀 Starting Services:"
echo "   Starting IBKR Gateway..."
systemctl start rtx-ibkr
sleep 5

echo "   Starting AlgoSlayer..."
systemctl start rtx-trading
sleep 3

echo ""
echo "📊 Service Status:"
echo "   IBKR Gateway: $(systemctl is-active rtx-ibkr)"
echo "   AlgoSlayer: $(systemctl is-active rtx-trading)"
echo ""
echo "💡 Management Commands:"
echo "   systemctl status rtx-trading      # Check AlgoSlayer status"
echo "   systemctl status rtx-ibkr         # Check IBKR Gateway status" 
echo "   journalctl -u rtx-trading -f      # View AlgoSlayer logs"
echo "   journalctl -u rtx-ibkr -f         # View IBKR Gateway logs"
echo "   $APP_DIR/monitor_system.sh        # System health check"
echo ""
echo "🖥️ IBKR Gateway Access:"
echo "   VNC: ssh -L 5900:localhost:5900 root@$SERVER_IP"
echo "   Then connect VNC viewer to localhost:5900"
echo "   Login to IBKR Gateway manually first time"
echo ""
echo "📱 Trading Summary:"
echo "   Phase 1: System learning and paper trading active"
echo "   Phase 2: High-conviction RTX options trading"
echo "   AI Signals: 8 signals analyzing RTX every 15 minutes"
echo "   Target: 80%+ confidence trades, 1-2x per month"
echo ""

# Save setup info
cat > SETUP_INFO_IBKR.txt << EOF
RTX Trading System - Complete IBKR Setup
========================================

Server: $SERVER_IP
Setup Date: $(date)
Mode: $(if [[ "$PAPER_TRADING" == "true" ]]; then echo "Paper Trading"; else echo "LIVE TRADING"; fi)

Services:
- rtx-trading: AlgoSlayer main system
- rtx-ibkr: Interactive Brokers Gateway

IBKR Access:
- VNC: ssh -L 5900:localhost:5900 root@$SERVER_IP
- Gateway Port: $IBKR_PORT
- First login: Manual setup required via VNC

Management:
- systemctl status rtx-trading
- systemctl status rtx-ibkr  
- ./monitor_system.sh

Strategy:
- 9 RTX shares base position
- Options trading on 80%+ confidence
- 8 AI signals every 15 minutes
- Target: 1-2 trades per month
EOF

echo "✅ Setup complete! Your autonomous RTX trading system is running!"
echo "📋 Next: Access VNC to complete IBKR Gateway login"
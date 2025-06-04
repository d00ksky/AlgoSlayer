#!/bin/bash

# RTX Autonomous Trading System - DigitalOcean Deployment Script
# One-command deployment to the cloud

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
 ██████╗ ███████╗██████╗ ██╗      ██████╗ ██╗   ██╗
 ██╔══██╗██╔════╝██╔══██╗██║     ██╔═══██╗╚██╗ ██╔╝
 ██║  ██║█████╗  ██████╔╝██║     ██║   ██║ ╚████╔╝ 
 ██║  ██║██╔══╝  ██╔═══╝ ██║     ██║   ██║  ╚██╔╝  
 ██████╔╝███████╗██║     ███████╗╚██████╔╝   ██║   
 ╚═════╝ ╚══════╝╚═╝     ╚══════╝ ╚═════╝    ╚═╝   

 🚀 RTX AUTONOMOUS TRADING SYSTEM
 ☁️  DigitalOcean Deployment
EOF
echo -e "${NC}"

# Configuration
DROPLET_NAME="rtx-trading-server"
DROPLET_SIZE="s-2vcpu-4gb"  # $24/month
DROPLET_IMAGE="ubuntu-22-04-x64"
DROPLET_REGION="nyc1"  # New York (close to markets)

echo -e "${CYAN}🚀 Starting DigitalOcean deployment for RTX Trading System${NC}"
echo ""

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo -e "${RED}❌ doctl (DigitalOcean CLI) is not installed${NC}"
    echo -e "${YELLOW}💡 Please install it first:${NC}"
    echo "   - Download from: https://github.com/digitalocean/doctl/releases"
    echo "   - Or use: snap install doctl"
    echo "   - Then authenticate: doctl auth init"
    exit 1
fi

# Check if user is authenticated
if ! doctl account get &> /dev/null; then
    echo -e "${RED}❌ Not authenticated with DigitalOcean${NC}"
    echo -e "${YELLOW}💡 Please authenticate first: doctl auth init${NC}"
    exit 1
fi

echo -e "${GREEN}✅ DigitalOcean CLI is ready${NC}"

# Check for SSH key
SSH_KEY_NAME="rtx-trading-key"
if ! doctl compute ssh-key list --format Name --no-header | grep -q "$SSH_KEY_NAME"; then
    echo -e "${YELLOW}🔑 Creating SSH key for server access...${NC}"
    
    # Generate SSH key if it doesn't exist
    if [[ ! -f ~/.ssh/id_rsa ]]; then
        ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
    fi
    
    # Add SSH key to DigitalOcean
    doctl compute ssh-key import $SSH_KEY_NAME --public-key-file ~/.ssh/id_rsa.pub
    echo -e "${GREEN}✅ SSH key added to DigitalOcean${NC}"
fi

# Get SSH key ID
SSH_KEY_ID=$(doctl compute ssh-key list --format ID,Name --no-header | grep "$SSH_KEY_NAME" | awk '{print $1}')

# Check if droplet already exists
if doctl compute droplet list --format Name --no-header | grep -q "$DROPLET_NAME"; then
    echo -e "${YELLOW}⚠️  Droplet $DROPLET_NAME already exists${NC}"
    read -p "Do you want to destroy and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}🗑️  Destroying existing droplet...${NC}"
        DROPLET_ID=$(doctl compute droplet list --format ID,Name --no-header | grep "$DROPLET_NAME" | awk '{print $1}')
        doctl compute droplet delete $DROPLET_ID --force
        echo -e "${GREEN}✅ Existing droplet destroyed${NC}"
        sleep 10  # Wait for cleanup
    else
        echo -e "${BLUE}ℹ️  Using existing droplet${NC}"
        DROPLET_ID=$(doctl compute droplet list --format ID,Name --no-header | grep "$DROPLET_NAME" | awk '{print $1}')
    fi
else
    DROPLET_ID=""
fi

# Create droplet if needed
if [[ -z "$DROPLET_ID" ]]; then
    echo -e "${BLUE}🏗️  Creating DigitalOcean droplet...${NC}"
    echo "   • Name: $DROPLET_NAME"
    echo "   • Size: $DROPLET_SIZE ($24/month)"
    echo "   • Region: $DROPLET_REGION"
    echo "   • Image: $DROPLET_IMAGE"
    
    doctl compute droplet create $DROPLET_NAME \
        --size $DROPLET_SIZE \
        --image $DROPLET_IMAGE \
        --region $DROPLET_REGION \
        --ssh-keys $SSH_KEY_ID \
        --wait
    
    DROPLET_ID=$(doctl compute droplet list --format ID,Name --no-header | grep "$DROPLET_NAME" | awk '{print $1}')
    echo -e "${GREEN}✅ Droplet created with ID: $DROPLET_ID${NC}"
fi

# Get droplet IP
DROPLET_IP=$(doctl compute droplet get $DROPLET_ID --format PublicIPv4 --no-header)
echo -e "${GREEN}🌐 Droplet IP: $DROPLET_IP${NC}"

# Wait for SSH to be ready
echo -e "${BLUE}⏳ Waiting for SSH to be ready...${NC}"
while ! ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@$DROPLET_IP exit 2>/dev/null; do
    echo -n "."
    sleep 5
done
echo -e "\n${GREEN}✅ SSH is ready${NC}"

# Collect API keys
echo -e "${CYAN}🔑 Please provide your API keys:${NC}"
echo ""

# OpenAI API Key
read -p "🤖 OpenAI API Key: " OPENAI_API_KEY
if [[ -z "$OPENAI_API_KEY" ]]; then
    echo -e "${RED}❌ OpenAI API key is required${NC}"
    exit 1
fi

# Telegram Bot Token
read -p "📱 Telegram Bot Token (optional): " TELEGRAM_BOT_TOKEN
read -p "📱 Telegram Chat ID (optional): " TELEGRAM_CHAT_ID

# IBKR Credentials
read -p "🏦 IBKR Username (optional): " IBKR_USERNAME
read -s -p "🏦 IBKR Password (optional): " IBKR_PASSWORD
echo ""

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
    else
        PAPER_TRADING="true"
    fi
else
    TRADING_ENABLED="false"
    PAPER_TRADING="true"
fi

# Create deployment script
echo -e "${BLUE}📝 Creating deployment script...${NC}"

cat > /tmp/deploy_rtx.sh << EOF
#!/bin/bash
set -e

# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Configure firewall
ufw --force enable
ufw allow ssh
ufw allow 80
ufw allow 443
ufw allow 7496  # IBKR live port
ufw allow 7497  # IBKR paper port

# Create application directory
mkdir -p /opt/rtx-trading
cd /opt/rtx-trading

# Create .env file
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

# Set permissions
chmod 600 .env

echo "✅ Server setup complete!"
echo "🚀 Ready for application deployment"
EOF

# Copy and execute deployment script
echo -e "${BLUE}🚀 Deploying to server...${NC}"
scp -o StrictHostKeyChecking=no /tmp/deploy_rtx.sh root@$DROPLET_IP:/tmp/
ssh -o StrictHostKeyChecking=no root@$DROPLET_IP "bash /tmp/deploy_rtx.sh"

# Copy application files
echo -e "${BLUE}📦 Uploading application files...${NC}"
rsync -avz --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='logs' \
    --exclude='data' \
    ./ root@$DROPLET_IP:/opt/rtx-trading/

# Start the application
echo -e "${BLUE}🎯 Starting RTX Trading System...${NC}"
ssh -o StrictHostKeyChecking=no root@$DROPLET_IP << 'EOF'
cd /opt/rtx-trading
docker-compose up -d --build
EOF

# Final status
echo ""
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
echo -e "${CYAN}================================${NC}"
echo -e "${GREEN}✅ RTX Trading System is now running in the cloud!${NC}"
echo ""
echo -e "${BLUE}📊 Server Details:${NC}"
echo "   • IP Address: $DROPLET_IP"
echo "   • SSH Access: ssh root@$DROPLET_IP"
echo "   • Monthly Cost: ~$24"
echo ""
echo -e "${BLUE}🔗 Access URLs:${NC}"
echo "   • Grafana (monitoring): http://$DROPLET_IP:3000"
echo "   • Prometheus (metrics): http://$DROPLET_IP:9090"
echo "   • IBKR VNC (trading): http://$DROPLET_IP:5900"
echo ""
echo -e "${BLUE}📱 Monitoring:${NC}"
if [[ -n "$TELEGRAM_BOT_TOKEN" ]]; then
    echo "   • Telegram notifications: Enabled ✅"
else
    echo "   • Telegram notifications: Disabled ⚠️"
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
echo -e "${YELLOW}💡 Next Steps:${NC}"
echo "   1. Monitor Telegram for system status"
echo "   2. Check Grafana dashboard for performance"
echo "   3. SSH to server if needed: ssh root@$DROPLET_IP"
echo "   4. View logs: docker logs rtx-trading-app"
echo ""
echo -e "${GREEN}🚀 Your RTX Trading System is autonomous and operational!${NC}"

# Save connection info
cat > connection_info.txt << EOF
RTX Trading System - Connection Information
==========================================

Server IP: $DROPLET_IP
SSH Access: ssh root@$DROPLET_IP
Grafana: http://$DROPLET_IP:3000 (admin/rtx2024)
Prometheus: http://$DROPLET_IP:9090
IBKR VNC: http://$DROPLET_IP:5900

Useful Commands:
- View logs: docker logs rtx-trading-app
- Restart system: docker-compose restart
- Stop system: docker-compose down
- Update system: git pull && docker-compose up -d --build

Generated: $(date)
EOF

echo -e "${BLUE}💾 Connection info saved to: connection_info.txt${NC}" 
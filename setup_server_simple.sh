#!/bin/bash

# RTX Trading System - Simple Server Setup Script
# Run this ON your DigitalOcean droplet: sudo bash setup_server_simple.sh

set -e

echo "🚀 RTX Trading System - Server Setup"
echo "====================================="

# Check root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Run as root: sudo bash setup_server_simple.sh"
   exit 1
fi

echo "✅ Running as root"

# Update system
echo "📦 Updating system..."
apt-get update && apt-get upgrade -y

# Install essentials
echo "🔧 Installing essentials..."
apt-get install -y curl git python3 python3-pip

# Install Docker
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo "✅ Docker installed"
else
    echo "✅ Docker already installed"
fi

# Configure firewall
echo "🔥 Configuring firewall..."
ufw --force enable
ufw allow ssh
ufw allow 80
ufw allow 443
ufw allow 3000
ufw allow 8000

# Create app directory
APP_DIR="/opt/rtx-trading"
echo "📁 Creating directory: $APP_DIR"
mkdir -p $APP_DIR
cd $APP_DIR

# Collect configuration
echo ""
echo "🔑 Configuration Setup"
echo "====================="

# Get OpenAI API key
while [[ -z "$OPENAI_API_KEY" ]]; do
    read -p "🤖 OpenAI API Key (required): " OPENAI_API_KEY
done

# Get Telegram info (optional)
read -p "📱 Telegram Bot Token (optional): " TELEGRAM_BOT_TOKEN
if [[ -n "$TELEGRAM_BOT_TOKEN" ]]; then
    read -p "📱 Telegram Chat ID: " TELEGRAM_CHAT_ID
fi

# Trading settings
read -p "💰 Enable Trading? (y/N): " -n 1 ENABLE_TRADING
echo ""
if [[ $ENABLE_TRADING =~ ^[Yy]$ ]]; then
    TRADING_ENABLED="true"
    read -p "📄 Paper Trading? (Y/n): " -n 1 PAPER_MODE
    echo ""
    PAPER_TRADING="true"
    if [[ $PAPER_MODE =~ ^[Nn]$ ]]; then
        echo "⚠️  LIVE TRADING ENABLED!"
        read -p "Type 'CONFIRM' for live trading: " CONFIRM
        if [[ "$CONFIRM" == "CONFIRM" ]]; then
            PAPER_TRADING="false"
        fi
    fi
else
    TRADING_ENABLED="false"
    PAPER_TRADING="true"
fi

# Create .env file
echo "📝 Creating .env file..."
cat > .env << EOF
TRADING_ENABLED=${TRADING_ENABLED}
PAPER_TRADING=${PAPER_TRADING}
PREDICTION_ONLY=false
IBKR_REQUIRED=false
AUTO_CONNECT_IBKR=true

OPENAI_API_KEY=${OPENAI_API_KEY}
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}

STARTING_CAPITAL=1000
MAX_POSITION_SIZE=200
MAX_DAILY_LOSS=50
LOG_LEVEL=INFO
PREDICTION_INTERVAL_MINUTES=15
CONFIDENCE_THRESHOLD=0.35
EOF

chmod 600 .env
echo "✅ Environment configured"

# Create directories
mkdir -p logs data

# Check for application code
if [[ ! -d "src" ]]; then
    echo ""
    echo "⚠️  No application code found"
    echo "📥 Please upload your RTX trading code to: $APP_DIR"
    echo ""
    echo "💡 Upload commands:"
    echo "   scp -r ./src root@YOUR_SERVER_IP:$APP_DIR/"
    echo "   scp -r ./config root@YOUR_SERVER_IP:$APP_DIR/"
    echo "   scp requirements.txt root@YOUR_SERVER_IP:$APP_DIR/"
    echo "   scp run_server.py root@YOUR_SERVER_IP:$APP_DIR/"
    echo ""
    read -p "Press Enter when code is uploaded..."
fi

# Install Python dependencies
if [[ -f "requirements.txt" ]]; then
    echo "📦 Installing Python dependencies..."
    pip3 install -r requirements.txt --break-system-packages
    echo "✅ Dependencies installed"
fi

# Create systemd service
echo "⚙️  Creating system service..."
cat > /etc/systemd/system/rtx-trading.service << EOF
[Unit]
Description=RTX Trading System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
Environment=PATH=/usr/bin:/usr/local/bin
ExecStart=/usr/bin/python3 run_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Start service
systemctl daemon-reload
systemctl enable rtx-trading

# Only start if we have the app code
if [[ -f "run_server.py" && -d "src" ]]; then
    echo "🚀 Starting RTX Trading System..."
    systemctl start rtx-trading
    sleep 3
    
    # Check status
    if systemctl is-active --quiet rtx-trading; then
        echo "✅ RTX Trading System is RUNNING!"
    else
        echo "⚠️  Service may have issues. Check logs with:"
        echo "   journalctl -u rtx-trading -f"
    fi
else
    echo "⏳ Service created but not started (waiting for application code)"
fi

# Get server info
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "Unable to detect")

# Final summary
echo ""
echo "🎉 SETUP COMPLETE!"
echo "=================="
echo ""
echo "📊 Server: $SERVER_IP"
echo "📁 Directory: $APP_DIR"
echo ""
echo "💰 Trading: $(if [[ "$TRADING_ENABLED" == "true" ]]; then echo "Enabled"; else echo "Disabled"; fi)"
echo "📄 Mode: $(if [[ "$PAPER_TRADING" == "true" ]]; then echo "Paper Trading"; else echo "LIVE TRADING"; fi)"
echo "📱 Telegram: $(if [[ -n "$TELEGRAM_BOT_TOKEN" ]]; then echo "Enabled"; else echo "Disabled"; fi)"
echo ""
echo "💡 Useful commands:"
echo "   systemctl status rtx-trading    # Check status"
echo "   journalctl -u rtx-trading -f    # View logs"
echo "   systemctl restart rtx-trading   # Restart"
echo "   systemctl stop rtx-trading      # Stop"
echo ""

# Save info
cat > SETUP_INFO.txt << EOF
RTX Trading System Setup
========================

Server IP: $SERVER_IP
Directory: $APP_DIR
Setup: $(date)

Configuration:
- Trading: $TRADING_ENABLED
- Paper Mode: $PAPER_TRADING
- Telegram: $(if [[ -n "$TELEGRAM_BOT_TOKEN" ]]; then echo "Yes"; else echo "No"; fi)

Commands:
- Status: systemctl status rtx-trading
- Logs: journalctl -u rtx-trading -f
- Restart: systemctl restart rtx-trading
- Stop: systemctl stop rtx-trading
EOF

echo "💾 Setup info saved to: SETUP_INFO.txt"
echo ""
if [[ -f "run_server.py" && -d "src" ]]; then
    echo "🤖 Your RTX Trading System is operational!"
else
    echo "📤 Upload your application code and run:"
    echo "   systemctl start rtx-trading"
fi 
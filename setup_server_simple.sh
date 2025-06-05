#!/bin/bash

# RTX Trading System - Lightweight Server Setup Script
# Optimized for 1GB RAM DigitalOcean droplets
# Run this ON your DigitalOcean droplet: sudo bash setup_server_simple.sh

set -e

echo "🚀 RTX Trading System - Lightweight Setup"
echo "========================================="
echo "💡 Optimized for 1GB RAM droplets"

# Check root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Run as root: sudo bash setup_server_simple.sh"
   exit 1
fi

echo "✅ Running as root"

# Check system resources
echo "🔍 Checking system resources..."
TOTAL_MEM=$(grep MemTotal /proc/meminfo | awk '{print $2}')
TOTAL_MEM_GB=$((TOTAL_MEM / 1024 / 1024))
echo "💾 Available RAM: ${TOTAL_MEM_GB}GB"

if [[ $TOTAL_MEM_GB -lt 1 ]]; then
    echo "⚠️  Warning: Less than 1GB RAM detected"
fi

# Update system
echo "📦 Updating system..."
apt-get update && apt-get upgrade -y

# Install essentials (lightweight selection)
echo "🔧 Installing essentials..."
apt-get install -y curl git python3 python3-pip python3-venv htop nano

# Configure swap for 1GB droplets
if [[ $TOTAL_MEM_GB -eq 1 ]]; then
    echo "💾 Setting up swap for 1GB droplet..."
    if [[ ! -f /swapfile ]]; then
        fallocate -l 1G /swapfile
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
        echo "✅ 1GB swap file created"
    else
        echo "✅ Swap already configured"
    fi
fi

# Skip Docker for lightweight deployment
echo "🚫 Skipping Docker (lightweight deployment)"
echo "💡 Using direct Python deployment for better resource utilization"

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

# Create .env file with enhanced RTX strategy settings
echo "📝 Creating .env file..."
cat > .env << EOF
# Trading Configuration
TRADING_ENABLED=${TRADING_ENABLED}
PAPER_TRADING=${PAPER_TRADING}
PREDICTION_ONLY=false
IBKR_REQUIRED=false
AUTO_CONNECT_IBKR=true

# API Keys
OPENAI_API_KEY=${OPENAI_API_KEY}
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}

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

# Lightweight ML Settings
ML_MODEL_DIR=/opt/rtx-trading/data/models
ML_RETRAIN_DAYS=7
ML_MIN_DATA_POINTS=100

# Database
DATABASE_URL=sqlite:///opt/rtx-trading/data/rtx_trading.db

# Performance Settings
MAX_MEMORY_USAGE=800MB
PARALLEL_SIGNALS=true
CACHE_MARKET_DATA=true
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

# Create Python virtual environment for better resource management
echo "🐍 Setting up Python virtual environment..."
python3 -m venv rtx-env
source rtx-env/bin/activate

# Upgrade pip and install wheel
pip install --upgrade pip setuptools wheel

# Install Python dependencies optimized for lightweight deployment
if [[ -f "requirements.txt" ]]; then
    echo "📦 Installing Python dependencies..."
    # Install with optimizations for low memory
    pip install -r requirements.txt --no-cache-dir --disable-pip-version-check
    echo "✅ Dependencies installed"
else
    echo "📦 Installing core dependencies..."
    pip install --no-cache-dir yfinance pandas numpy scikit-learn aiohttp asyncio loguru python-telegram-bot
    echo "✅ Core dependencies installed"
fi

# Create requirements.txt if it doesn't exist
if [[ ! -f "requirements.txt" ]]; then
    echo "📝 Creating requirements.txt..."
    cat > requirements.txt << EOF
# Core trading dependencies
yfinance==0.2.18
pandas==2.0.3
numpy==1.24.3

# Machine Learning (lightweight)
scikit-learn==1.3.0
joblib==1.3.2

# Async and HTTP
aiohttp==3.8.5
asyncio-mqtt==0.13.0

# Interactive Brokers
ib_insync==0.9.86

# Telegram
python-telegram-bot==20.4

# Logging and utilities
loguru==0.7.0
python-dotenv==1.0.0

# Data processing
requests==2.31.0
beautifulsoup4==4.12.2

# Database
sqlalchemy==2.0.19
alembic==1.11.1
EOF
    pip install -r requirements.txt --no-cache-dir
fi

# Create systemd service with virtual environment
echo "⚙️  Creating system service..."
cat > /etc/systemd/system/rtx-trading.service << EOF
[Unit]
Description=RTX Trading System - Lightweight AI Trading Bot
After=network.target
StartLimitIntervalSec=0

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

# Memory and resource limits for 1GB droplet
MemoryLimit=800M
MemoryAccounting=true
CPUQuota=90%
CPUAccounting=true

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

# Create log rotation for the service
echo "📝 Setting up log rotation..."
cat > /etc/logrotate.d/rtx-trading << EOF
/var/log/rtx-trading.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
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

# Set up memory monitoring
echo "📊 Setting up system monitoring..."
cat > $APP_DIR/monitor_system.sh << 'EOF'
#!/bin/bash
# System monitoring script for 1GB droplet
echo "=== RTX Trading System Status ==="
echo "Time: $(date)"
echo "Memory Usage: $(free -h | grep Mem | awk '{print $3"/"$2}')"
echo "Disk Usage: $(df -h $APP_DIR | tail -1 | awk '{print $3"/"$2" ("$5")"}')"
echo "Service Status: $(systemctl is-active rtx-trading)"
echo "Last 5 log entries:"
journalctl -u rtx-trading -n 5 --no-pager
EOF
chmod +x $APP_DIR/monitor_system.sh

# Create maintenance script
echo "🔧 Creating maintenance scripts..."
cat > $APP_DIR/maintenance.sh << 'EOF'
#!/bin/bash
# Maintenance script for RTX Trading System
echo "🔧 Running maintenance..."

# Clean up old logs
find /var/log -name "*.log.*.gz" -mtime +30 -delete 2>/dev/null || true

# Clear Python cache
find $APP_DIR -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Check disk space
DISK_USAGE=$(df $APP_DIR | tail -1 | awk '{print $5}' | sed 's/%//')
if [[ $DISK_USAGE -gt 85 ]]; then
    echo "⚠️ Warning: Disk usage is ${DISK_USAGE}%"
fi

# Check memory
MEMORY_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [[ $MEMORY_USAGE -gt 85 ]]; then
    echo "⚠️ Warning: Memory usage is ${MEMORY_USAGE}%"
fi

echo "✅ Maintenance complete"
EOF
chmod +x $APP_DIR/maintenance.sh

# Set up cron for daily maintenance
echo "⏰ Setting up daily maintenance..."
(crontab -l 2>/dev/null; echo "0 2 * * * $APP_DIR/maintenance.sh") | crontab -

# Final summary with enhanced information
echo ""
echo "🎉 RTX TRADING SYSTEM SETUP COMPLETE!"
echo "====================================="
echo ""
echo "🖥️  Server Info:"
echo "   IP: $SERVER_IP"
echo "   RAM: ${TOTAL_MEM_GB}GB (optimized for 1GB)"
echo "   Directory: $APP_DIR"
echo ""
echo "💰 Trading Configuration:"
echo "   Trading: $(if [[ "$TRADING_ENABLED" == "true" ]]; then echo "Enabled"; else echo "Disabled"; fi)"
echo "   Mode: $(if [[ "$PAPER_TRADING" == "true" ]]; then echo "Paper Trading"; else echo "LIVE TRADING"; fi)"
echo "   Target: 9 RTX shares + selective options"
echo "   Confidence: 80%+ required for trades"
echo ""
echo "📱 Notifications:"
echo "   Telegram: $(if [[ -n "$TELEGRAM_BOT_TOKEN" ]]; then echo "Enabled"; else echo "Disabled"; fi)"
echo "   Daily Reports: 5:00 PM ET"
echo ""
echo "🤖 AI Engine:"
echo "   Signals: 8 active signals"
echo "   ML System: Lightweight scikit-learn"
echo "   Learning: 180x speed backtesting"
echo ""
echo "💡 Management Commands:"
echo "   systemctl status rtx-trading     # Check status"
echo "   journalctl -u rtx-trading -f     # View live logs"
echo "   systemctl restart rtx-trading    # Restart system"
echo "   $APP_DIR/monitor_system.sh       # System health check"
echo "   $APP_DIR/maintenance.sh          # Run maintenance"
echo ""
echo "📊 Strategy Summary:"
echo "   Phase 1: Learn & paper trade (2-3 months)"
echo "   Phase 2: Live options trading (1-2x/month)"
echo "   High conviction only (3+ signals, 80%+ confidence)"
echo ""

# Save comprehensive setup info
cat > SETUP_INFO.txt << EOF
RTX Trading System - Lightweight Setup
======================================

Server Details:
- IP: $SERVER_IP
- RAM: ${TOTAL_MEM_GB}GB (optimized for 1GB droplets)
- Directory: $APP_DIR
- Setup Date: $(date)
- Python Environment: $APP_DIR/rtx-env

Trading Configuration:
- Trading Enabled: $TRADING_ENABLED
- Trading Mode: $(if [[ "$PAPER_TRADING" == "true" ]]; then echo "Paper Trading"; else echo "LIVE TRADING"; fi)
- Target Position: 9 RTX shares
- Options Budget: \$400 per trade
- Confidence Threshold: 80%
- Min Signals Required: 3/8
- Telegram Alerts: $(if [[ -n "$TELEGRAM_BOT_TOKEN" ]]; then echo "Enabled"; else echo "Disabled"; fi)

Strategy:
- Phase 1: Learn & paper trade (2-3 months)
- Phase 2: Selective live options trading (1-2x/month)
- High conviction only (80%+ confidence, 3+ signals)
- Hold RTX shares as stable base position

System Management:
- Status: systemctl status rtx-trading
- Logs: journalctl -u rtx-trading -f
- Restart: systemctl restart rtx-trading
- Stop: systemctl stop rtx-trading
- Health Check: $APP_DIR/monitor_system.sh
- Maintenance: $APP_DIR/maintenance.sh

Files:
- Configuration: $APP_DIR/.env
- Logs: journalctl -u rtx-trading
- Data: $APP_DIR/data/
- Models: $APP_DIR/data/models/

AI Components:
- 8 Trading Signals (news, technical, options flow, etc.)
- Lightweight ML with scikit-learn
- Real-time learning and adaptation
- Daily performance reports at 5 PM ET

Memory Optimization:
- Virtual environment: $APP_DIR/rtx-env
- Memory limit: 800MB
- Swap configured: 1GB
- Log rotation: Daily
- Cache cleanup: Automated
EOF

echo "💾 Setup info saved to: SETUP_INFO.txt"
echo ""

# Test system if application code is present
if [[ -f "run_server.py" && -d "src" ]]; then
    echo "🧪 Testing system components..."
    
    # Test Python environment
    if $APP_DIR/rtx-env/bin/python -c "import yfinance, pandas, sklearn; print('✅ Core dependencies OK')" 2>/dev/null; then
        echo "✅ Python environment healthy"
    else
        echo "⚠️  Python environment may have issues"
    fi
    
    # Test RTX data access
    if $APP_DIR/rtx-env/bin/python -c "import yfinance; yf.Ticker('RTX').info; print('✅ RTX data access OK')" 2>/dev/null; then
        echo "✅ RTX market data accessible"
    else
        echo "⚠️  RTX data access may have issues"
    fi
    
    echo ""
    echo "🤖 Your RTX Trading System is ready to deploy!"
    echo "🚀 Start with: systemctl start rtx-trading"
else
    echo "📤 Upload your application code to get started:"
    echo ""
    echo "Required files:"
    echo "   - run_server.py (main application)"
    echo "   - src/ (source code directory)"
    echo "   - config/ (configuration files)"
    echo ""
    echo "Upload commands:"
    echo "   scp -r ./src root@$SERVER_IP:$APP_DIR/"
    echo "   scp -r ./config root@$SERVER_IP:$APP_DIR/"
    echo "   scp run_server.py root@$SERVER_IP:$APP_DIR/"
    echo ""
    echo "Then start: systemctl start rtx-trading"
fi

echo ""
echo "📋 Quick Start Checklist:"
echo "  ☐ Upload application code (if not done)"
echo "  ☐ Test Telegram bot (if configured)"
echo "  ☐ Start the service: systemctl start rtx-trading"
echo "  ☐ Monitor logs: journalctl -u rtx-trading -f"
echo "  ☐ Check system health: ./monitor_system.sh"
echo ""
echo "💡 The system will start learning RTX patterns immediately"
echo "📊 Daily reports will be sent at 5 PM ET"
echo "🎯 High-confidence trade alerts will notify you via Telegram" 
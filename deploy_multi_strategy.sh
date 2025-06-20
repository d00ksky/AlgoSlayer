#!/bin/bash

# Multi-Strategy Trading System Deployment Script
# Deploy the 3-way AI competition system

set -e

echo "🚀 DEPLOYING MULTI-STRATEGY TRADING SYSTEM"
echo "=========================================="

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Stop current service
echo "⏹️ Stopping current RTX trading service..."
systemctl stop rtx-trading || true

# Enable trading and paper trading
echo "⚙️ Configuring for multi-strategy trading..."
sed -i 's/TRADING_ENABLED=false/TRADING_ENABLED=true/' /opt/rtx-trading/.env
sed -i 's/PAPER_TRADING=false/PAPER_TRADING=true/' /opt/rtx-trading/.env

# Create the new multi-strategy service
echo "🎯 Creating multi-strategy service..."
cat > /etc/systemd/system/multi-strategy-trading.service << 'EOF'
[Unit]
Description=Multi-Strategy RTX Options Trading System
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/rtx-trading
Environment=PATH=/opt/rtx-trading/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/opt/rtx-trading/venv/bin/python /opt/rtx-trading/run_multi_strategy.py

# Enhanced timeout and kill settings
TimeoutStartSec=300
TimeoutStopSec=30
TimeoutSec=0
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopFailureMode=terminate
FinalKillSignal=SIGKILL

# Resource limits
MemoryMax=1500M
CPUQuota=80%

# Restart behavior
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=multi-strategy-trading

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the new service
echo "🔄 Enabling and starting multi-strategy service..."
systemctl daemon-reload
systemctl enable multi-strategy-trading
systemctl start multi-strategy-trading

# Check status
echo "📊 Checking service status..."
sleep 5
systemctl status multi-strategy-trading --no-pager

# Show logs
echo "📋 Recent logs:"
journalctl -u multi-strategy-trading --since='30 seconds ago' --no-pager

echo ""
echo "🎉 MULTI-STRATEGY DEPLOYMENT COMPLETE!"
echo "======================================"
echo "✅ 3 AI strategies now competing:"
echo "   🥇 Conservative: 75% conf, 4+ signals"  
echo "   🥈 Moderate: 60% conf, 3+ signals"
echo "   🥉 Aggressive: 50% conf, 2+ signals"
echo ""
echo "💰 Each strategy starts with $1000"
echo "📱 Telegram notifications enabled"
echo "📊 Leaderboard tracking active"
echo ""
echo "🏆 MAY THE BEST STRATEGY WIN!"
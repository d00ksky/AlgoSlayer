#!/bin/bash

# Deploy Telegram Dashboard Fix to Server
# This script copies the necessary files to the server and restarts the service

SERVER_IP="164.90.157.100"
SERVER_USER="root"
SERVER_PATH="/opt/rtx-trading"

echo "🚀 Deploying Telegram Dashboard Fix"
echo "===================================="

# Check if we can reach the server
echo "🔍 Testing server connectivity..."
if ping -c 1 -W 5 $SERVER_IP > /dev/null 2>&1; then
    echo "✅ Server is reachable"
else
    echo "❌ Server is not reachable"
    echo "   Check if server is running and accessible"
    exit 1
fi

# Test SSH connection
echo "🔍 Testing SSH connection..."
if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "echo 'SSH test successful'" > /dev/null 2>&1; then
    echo "✅ SSH connection successful"
else
    echo "❌ SSH connection failed"
    echo "   Check SSH access to $SERVER_USER@$SERVER_IP"
    exit 1
fi

echo "📋 Files to deploy:"
echo "   - src/core/telegram_bot.py (updated with new commands)"
echo "   - src/core/dashboard.py (dashboard generation)" 
echo "   - src/core/dynamic_thresholds.py (threshold management)"
echo "   - Debug scripts for troubleshooting"

# Copy files to server
echo "📤 Copying files to server..."

# Copy main bot file
scp -o StrictHostKeyChecking=no src/core/telegram_bot.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/src/core/
echo "   ✅ telegram_bot.py"

# Copy dashboard file
scp -o StrictHostKeyChecking=no src/core/dashboard.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/src/core/
echo "   ✅ dashboard.py"

# Copy dynamic thresholds file
scp -o StrictHostKeyChecking=no src/core/dynamic_thresholds.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/src/core/
echo "   ✅ dynamic_thresholds.py"

# Copy debug scripts
scp -o StrictHostKeyChecking=no debug_telegram_bot.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/
echo "   ✅ debug_telegram_bot.py"

scp -o StrictHostKeyChecking=no test_dashboard_command.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/
echo "   ✅ test_dashboard_command.py"

scp -o StrictHostKeyChecking=no fix_telegram_dashboard.sh $SERVER_USER@$SERVER_IP:$SERVER_PATH/
echo "   ✅ fix_telegram_dashboard.sh"

# Make scripts executable
echo "🔧 Making scripts executable..."
ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "cd $SERVER_PATH && chmod +x debug_telegram_bot.py test_dashboard_command.py fix_telegram_dashboard.sh"

# Restart the service
echo "🔄 Restarting RTX trading service..."
ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "systemctl restart rtx-trading"

# Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 5

# Check service status
echo "🔍 Checking service status..."
SERVICE_STATUS=$(ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "systemctl is-active rtx-trading" 2>/dev/null)

if [ "$SERVICE_STATUS" = "active" ]; then
    echo "✅ RTX trading service is running"
    
    # Show recent logs
    echo "📋 Recent logs:"
    ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "journalctl -u rtx-trading --no-pager -n 5" | sed 's/^/   /'
    
else
    echo "❌ RTX trading service failed to start"
    echo "🔍 Error logs:"
    ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "journalctl -u rtx-trading --no-pager -n 10" | sed 's/^/   /'
fi

echo ""
echo "🎯 DEPLOYMENT COMPLETE"
echo "======================"
echo "✅ Files copied to server"
echo "✅ Service restarted"
echo ""
echo "📱 TEST INSTRUCTIONS:"
echo "   1. Send /dashboard to your Telegram bot"
echo "   2. If it still fails, run on server:"
echo "      ssh $SERVER_USER@$SERVER_IP"
echo "      cd $SERVER_PATH"
echo "      python3 test_dashboard_command.py"
echo ""
echo "🔧 TROUBLESHOOTING:"
echo "   - Run: ./fix_telegram_dashboard.sh fix"
echo "   - Check logs: journalctl -u rtx-trading -f"
echo "   - Debug: python3 debug_telegram_bot.py"
echo ""
echo "🕐 Deployment completed at $(date)"
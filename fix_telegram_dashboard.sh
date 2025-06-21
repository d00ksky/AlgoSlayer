#!/bin/bash

echo "🔧 RTX Trading - Fix Telegram Dashboard Issue"
echo "=============================================="

# Change to project directory
cd /opt/rtx-trading || {
    echo "❌ Cannot access /opt/rtx-trading directory"
    exit 1
}

echo "📁 Working directory: $(pwd)"

# Check if we have the latest code
echo "🔍 Checking code status..."

if [ -f "src/core/dashboard.py" ]; then
    echo "✅ dashboard.py exists"
else
    echo "❌ dashboard.py missing!"
fi

if [ -f "src/core/dynamic_thresholds.py" ]; then
    echo "✅ dynamic_thresholds.py exists"
else
    echo "❌ dynamic_thresholds.py missing!"
fi

# Check if telegram_bot.py has the new commands
echo "🔍 Checking telegram_bot.py for new commands..."
if grep -q "send_dashboard_message" src/core/telegram_bot.py; then
    echo "✅ Dashboard command found in telegram_bot.py"
else
    echo "❌ Dashboard command missing from telegram_bot.py"
    echo "   Need to update the code!"
fi

if grep -q "send_thresholds_message" src/core/telegram_bot.py; then
    echo "✅ Thresholds command found in telegram_bot.py"
else
    echo "❌ Thresholds command missing from telegram_bot.py"
fi

# Check current service status
echo "🔍 Checking service status..."
if systemctl is-active --quiet rtx-trading; then
    echo "✅ rtx-trading service is running"
    
    # Get process info
    PID=$(pgrep -f "run_server.py")
    if [ -n "$PID" ]; then
        echo "✅ Process PID: $PID"
        echo "   Memory usage: $(ps -p $PID -o rss= | awk '{print $1/1024 " MB"}')"
        echo "   Start time: $(ps -p $PID -o lstart= | cut -c1-20)"
    fi
else
    echo "❌ rtx-trading service is not running"
fi

# Check recent logs for errors
echo "🔍 Checking recent logs for errors..."
ERROR_COUNT=$(journalctl -u rtx-trading --since="5 minutes ago" | grep -i error | wc -l)
if [ $ERROR_COUNT -gt 0 ]; then
    echo "🚨 Found $ERROR_COUNT recent errors:"
    journalctl -u rtx-trading --since="5 minutes ago" | grep -i error | tail -3
else
    echo "✅ No recent errors in logs"
fi

# Test Python imports
echo "🔍 Testing Python imports..."
cd /opt/rtx-trading

# Test dashboard import
if python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from src.core.dashboard import dashboard
    print('✅ Dashboard import successful')
except Exception as e:
    print(f'❌ Dashboard import failed: {e}')
"; then
    echo "Dashboard import test completed"
fi

# Test dynamic thresholds import
if python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from src.core.dynamic_thresholds import dynamic_threshold_manager
    print('✅ Dynamic thresholds import successful')
except Exception as e:
    print(f'❌ Dynamic thresholds import failed: {e}')
"; then
    echo "Dynamic thresholds import test completed"
fi

echo "🔧 RECOMMENDED FIXES:"
echo "====================="

# Check if git pull is needed
if [ -d ".git" ]; then
    echo "1. Update code:"
    echo "   git pull"
    echo ""
fi

echo "2. Restart service:"
echo "   systemctl restart rtx-trading"
echo ""

echo "3. Monitor service:"
echo "   journalctl -u rtx-trading -f"
echo ""

echo "4. Test telegram commands:"
echo "   Send /dashboard to your bot"
echo ""

echo "5. Debug if still failing:"
echo "   python3 test_dashboard_command.py"
echo ""

# Offer to auto-fix
echo "🤖 AUTO-FIX OPTIONS:"
echo "===================="
echo "Run this script with 'fix' argument to automatically:"
echo "  - Pull latest code (if git repo)"
echo "  - Restart the service"
echo "  - Show live logs"
echo ""
echo "Usage: $0 fix"

if [ "$1" == "fix" ]; then
    echo ""
    echo "🚀 AUTO-FIXING..."
    echo "=================="
    
    # Pull latest code if git repo
    if [ -d ".git" ]; then
        echo "📥 Pulling latest code..."
        git pull
    fi
    
    # Restart service
    echo "🔄 Restarting service..."
    systemctl restart rtx-trading
    
    # Wait a moment
    sleep 3
    
    # Check if it started successfully
    if systemctl is-active --quiet rtx-trading; then
        echo "✅ Service restarted successfully"
        echo ""
        echo "📱 Try your /dashboard command now!"
        echo ""
        echo "📋 Live logs (Ctrl+C to exit):"
        journalctl -u rtx-trading -f
    else
        echo "❌ Service failed to start"
        echo "🔍 Error logs:"
        journalctl -u rtx-trading --no-pager -n 10
    fi
fi

echo "🎯 Fix script completed at $(date)"
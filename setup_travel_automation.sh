#!/bin/bash
# Setup Travel-Optimized ML Automation
# Run this once to set up all automation for irregular laptop usage

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Setting up travel-optimized ML automation..."

# 1. Update cron jobs for multiple triggers
echo "📅 Setting up multiple cron triggers..."

# Remove old cron job
crontab -l | grep -v "run_ml_training.sh" | crontab - 2>/dev/null || true

# Add new comprehensive cron jobs
(crontab -l 2>/dev/null || echo "") | {
    cat
    echo ""
    echo "# AlgoSlayer ML Training - Travel Optimized"
    echo "@reboot sleep 120 && $SCRIPT_DIR/run_smart_ml_training.sh"
    echo "@reboot sleep 180 && $SCRIPT_DIR/start_telegram_bot.sh start"
    echo "0 */6 * * * $SCRIPT_DIR/run_smart_ml_training.sh  # Every 6 hours"
    echo "0 9,21 * * * $SCRIPT_DIR/run_smart_ml_training.sh  # 9 AM and 9 PM daily"
    echo "*/30 * * * * $SCRIPT_DIR/check_urgent_training.sh  # Check for urgent training every 30 min"
    echo "*/5 * * * * $SCRIPT_DIR/start_telegram_bot.sh status > /dev/null 2>&1 || $SCRIPT_DIR/start_telegram_bot.sh start  # Keep bot alive"
} | crontab -

echo "✅ Cron jobs updated"

# 2. Create urgent training checker
cat > check_urgent_training.sh << 'EOF'
#!/bin/bash
# Quick check for urgent ML training needs
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLOUD_SERVER="root@64.226.96.90"

# Only check if we have internet and laptop has been on for >30 minutes
UPTIME_MINUTES=$(awk '{print int($1/60)}' /proc/uptime)
if [ $UPTIME_MINUTES -lt 30 ]; then
    exit 0
fi

# Quick connectivity check
if ! ping -c 1 -W 3 google.com > /dev/null 2>&1; then
    exit 0
fi

# Check if cloud has >10 new predictions and we haven't trained in >6 hours
if ssh -o ConnectTimeout=5 $CLOUD_SERVER "cd /opt/rtx-trading && sqlite3 data/signal_performance.db 'SELECT COUNT(*) FROM predictions WHERE datetime(timestamp) > datetime(\"now\", \"-6 hours\")'" 2>/dev/null | grep -q "^[1-9][0-9]"; then
    
    LAST_TRAINING_FILE="$SCRIPT_DIR/ml_training_data/last_training_time"
    if [ -f "$LAST_TRAINING_FILE" ]; then
        LAST_TRAINING=$(cat "$LAST_TRAINING_FILE")
        HOURS_SINCE=$(( ($(date +%s) - LAST_TRAINING) / 3600 ))
        
        if [ $HOURS_SINCE -gt 6 ]; then
            echo "$(date): 🚨 Urgent training triggered - >10 predictions and >6h since last training" >> logs/ml_training_$(date +%Y%m%d).log
            $SCRIPT_DIR/run_smart_ml_training.sh
        fi
    else
        echo "$(date): 🚨 Urgent training triggered - >10 predictions and no previous training" >> logs/ml_training_$(date +%Y%m%d).log
        $SCRIPT_DIR/run_smart_ml_training.sh
    fi
fi
EOF

chmod +x check_urgent_training.sh

# 3. Create control scripts
cat > disable_auto_ml.sh << 'EOF'
#!/bin/bash
# Disable automatic ML training
touch DISABLE_AUTO_ML
echo "🛑 Automatic ML training disabled"
echo "   To re-enable: ./enable_auto_ml.sh"
EOF

cat > enable_auto_ml.sh << 'EOF'
#!/bin/bash
# Enable automatic ML training
rm -f DISABLE_AUTO_ML
echo "✅ Automatic ML training enabled"
echo "   To disable: ./disable_auto_ml.sh"
EOF

chmod +x disable_auto_ml.sh enable_auto_ml.sh

# 4. Create status checker
cat > check_ml_status.sh << 'EOF'
#!/bin/bash
# Check ML training status and stats
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🤖 AlgoSlayer ML Status"
echo "======================"

# Check if auto-training is enabled
if [ -f "DISABLE_AUTO_ML" ]; then
    echo "❌ Auto-training: DISABLED"
else
    echo "✅ Auto-training: ENABLED"
fi

# Check last training time
if [ -f "ml_training_data/last_training_time" ]; then
    LAST_TRAINING=$(cat ml_training_data/last_training_time)
    HOURS_AGO=$(( ($(date +%s) - LAST_TRAINING) / 3600 ))
    echo "⏰ Last training: ${HOURS_AGO} hours ago"
else
    echo "⚠️  Last training: NEVER"
fi

# Check connectivity
if ping -c 1 -W 3 google.com > /dev/null 2>&1; then
    echo "🌐 Internet: CONNECTED"
    
    if ssh -o ConnectTimeout=5 root@64.226.96.90 "echo test" > /dev/null 2>&1; then
        echo "☁️  Cloud server: REACHABLE"
        
        # Get cloud stats
        NEW_PREDICTIONS=$(ssh root@64.226.96.90 "cd /opt/rtx-trading && sqlite3 data/signal_performance.db 'SELECT COUNT(*) FROM predictions WHERE datetime(timestamp) > datetime(\"now\", \"-24 hours\")'" 2>/dev/null || echo "unknown")
        echo "📊 New predictions (24h): $NEW_PREDICTIONS"
        
        TOTAL_PREDICTIONS=$(ssh root@64.226.96.90 "cd /opt/rtx-trading && sqlite3 data/signal_performance.db 'SELECT COUNT(*) FROM predictions'" 2>/dev/null || echo "unknown")
        echo "📈 Total predictions: $TOTAL_PREDICTIONS"
    else
        echo "☁️  Cloud server: UNREACHABLE"
    fi
else
    echo "🌐 Internet: DISCONNECTED"
fi

# Show recent log
echo ""
echo "📋 Recent training log:"
if [ -f "logs/ml_training_$(date +%Y%m%d).log" ]; then
    tail -5 "logs/ml_training_$(date +%Y%m%d).log"
else
    echo "   No log file for today"
fi

echo ""
echo "🔧 Control commands:"
echo "   ./run_smart_ml_training.sh  - Force training now"
echo "   ./disable_auto_ml.sh        - Disable auto-training" 
echo "   ./enable_auto_ml.sh         - Enable auto-training"
echo "   ./check_ml_status.sh        - Show this status"
EOF

chmod +x check_ml_status.sh

# 5. Test the setup
echo "🧪 Testing setup..."
./check_ml_status.sh

echo ""
echo "🎉 Travel automation setup complete!"
echo ""
echo "📋 What was configured:"
echo "   ✅ Smart training script (with connectivity checks)"
echo "   ✅ Multiple cron triggers (boot + every 6h + urgent checks)"
echo "   ✅ Urgent training for high-activity periods"
echo "   ✅ Enable/disable controls"
echo "   ✅ Status monitoring"
echo ""
echo "🚀 Available commands:"
echo "   ./check_ml_status.sh        - Check current status"
echo "   ./run_smart_ml_training.sh  - Force training now"
echo "   ./disable_auto_ml.sh        - Disable auto-training"
echo "   ./enable_auto_ml.sh         - Enable auto-training"
echo ""
echo "📱 The system will now:"
echo "   • Train on every boot (after 2 min delay)"
echo "   • Start Telegram bot daemon on boot"
echo "   • Train every 6 hours if laptop is on"
echo "   • Train at 9 AM and 9 PM daily"
echo "   • Emergency training if >10 predictions accumulate"
echo "   • Keep Telegram bot alive (restarts if needed)"
echo "   • Skip training if no internet/unreachable server"
echo "   • Send Telegram notifications for all training events"
echo "   • Log everything for debugging while traveling"
echo ""
echo "🤖 Telegram Commands Available:"
echo "   /status - Check ML system status"
echo "   /train  - Force training now"
echo "   /cloud  - Check cloud server status"
echo "   /logs   - View recent training logs"
echo "   /enable - Enable auto-training"
echo "   /disable - Disable auto-training"
echo "   /restart - Restart cloud trading service"
echo ""
echo "✈️ Perfect for travel! Your ML will stay updated automatically"
echo "   and you can control everything via Telegram from anywhere!"
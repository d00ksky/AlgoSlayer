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

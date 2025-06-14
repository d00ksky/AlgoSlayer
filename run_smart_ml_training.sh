#!/bin/bash
# Smart ML Training - Runs automatically and handles various scenarios
# Optimized for travel laptop with irregular usage

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
CLOUD_SERVER="root@64.226.96.90"
LOG_FILE="logs/ml_training_$(date +%Y%m%d).log"
DISABLE_FILE="$SCRIPT_DIR/DISABLE_AUTO_ML"
LAST_TRAINING_FILE="$SCRIPT_DIR/ml_training_data/last_training_time"

# Create logs directory
mkdir -p logs

echo "$(date): 🤖 Smart ML Training Starting..." >> "$LOG_FILE"

# Send Telegram notification function
send_telegram() {
    if [ -f "$SCRIPT_DIR/telegram_ml_bot.py" ]; then
        python3 "$SCRIPT_DIR/telegram_ml_bot.py" "$1" "true" 2>/dev/null || true
    fi
}

# Check if auto-training is disabled
if [ -f "$DISABLE_FILE" ]; then
    echo "$(date): ⏸️ Auto-training disabled (found $DISABLE_FILE)" >> "$LOG_FILE"
    echo "To re-enable: rm $DISABLE_FILE"
    exit 0
fi

# Check internet connectivity
if ! ping -c 1 google.com > /dev/null 2>&1; then
    echo "$(date): ❌ No internet connection - skipping ML training" >> "$LOG_FILE"
    exit 1
fi

# Check if cloud server is reachable
if ! ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no $CLOUD_SERVER "echo 'Server reachable'" > /dev/null 2>&1; then
    echo "$(date): ❌ Cannot reach cloud server - skipping ML training" >> "$LOG_FILE"
    exit 1
fi

# Determine if we should run training
SHOULD_TRAIN=false
REASON=""

# 1. If this is first time ever
if [ ! -f "$LAST_TRAINING_FILE" ]; then
    SHOULD_TRAIN=true
    REASON="First time training"
fi

# 2. If last training was more than 24 hours ago
if [ -f "$LAST_TRAINING_FILE" ]; then
    LAST_TRAINING=$(cat "$LAST_TRAINING_FILE")
    CURRENT_TIME=$(date +%s)
    TIME_DIFF=$((CURRENT_TIME - LAST_TRAINING))
    HOURS_SINCE=$((TIME_DIFF / 3600))
    
    if [ $HOURS_SINCE -gt 24 ]; then
        SHOULD_TRAIN=true
        REASON="Last training was $HOURS_SINCE hours ago"
    fi
fi

# 3. Check if there's new data on cloud server
NEW_DATA_COUNT=$(ssh $CLOUD_SERVER "cd /opt/rtx-trading && sqlite3 data/signal_performance.db 'SELECT COUNT(*) FROM predictions WHERE datetime(timestamp) > datetime(\"now\", \"-24 hours\")'" 2>/dev/null || echo "0")

if [ "$NEW_DATA_COUNT" -gt 0 ]; then
    SHOULD_TRAIN=true
    REASON="Found $NEW_DATA_COUNT new predictions in last 24h"
fi

# 4. Force training if laptop was off for more than 48 hours
BOOT_TIME=$(uptime -s)
BOOT_TIMESTAMP=$(date -d "$BOOT_TIME" +%s)
HOURS_SINCE_BOOT=$(( ($(date +%s) - BOOT_TIMESTAMP) / 3600 ))

if [ $HOURS_SINCE_BOOT -lt 2 ] && [ -f "$LAST_TRAINING_FILE" ]; then
    LAST_TRAINING=$(cat "$LAST_TRAINING_FILE")
    HOURS_SINCE_LAST=$(( ($(date +%s) - LAST_TRAINING) / 3600 ))
    
    if [ $HOURS_SINCE_LAST -gt 48 ]; then
        SHOULD_TRAIN=true
        REASON="Laptop was off for $HOURS_SINCE_LAST hours (>48h threshold)"
    fi
fi

# Execute training if needed
if [ "$SHOULD_TRAIN" = true ]; then
    echo "$(date): ✅ Starting ML training - $REASON" >> "$LOG_FILE"
    send_telegram "🚀 **Starting ML Training**\n\nReason: $REASON\nThis may take up to 30 minutes..."
    
    # Run training with timeout (max 30 minutes)
    # Use full python path for cron compatibility
    PYTHON_PATH=$(which python3 || which python)
    if timeout 1800 "$PYTHON_PATH" sync_and_train_ml.py >> "$LOG_FILE" 2>&1; then
        echo "$(date): ✅ ML training completed successfully" >> "$LOG_FILE"
        
        # Update last training time
        mkdir -p ml_training_data
        date +%s > "$LAST_TRAINING_FILE"
        
        # Get training results for notification
        TOTAL_DATA=$(grep "Loaded.*records" "$LOG_FILE" | tail -1 | grep -o '[0-9]\+' | head -1 || echo "0")
        FEATURES=$(grep "Created.*features" "$LOG_FILE" | tail -1 | grep -o '[0-9]\+' | head -1 || echo "0")
        
        send_telegram "✅ **ML Training Complete!**\n\n📊 Data: $TOTAL_DATA records\n🔧 Features: $FEATURES\n⏰ Duration: $(date)\n\nModels uploaded to cloud server"
        
        # Send success notification to cloud server
        ssh $CLOUD_SERVER "echo '$(date): Local ML training completed successfully' >> /opt/rtx-trading/logs/ml_updates.log" 2>/dev/null || true
        
    else
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 124 ]; then
            echo "$(date): ⏰ ML training timed out after 30 minutes" >> "$LOG_FILE"
            send_telegram "⏰ **ML Training Timeout**\n\nTraining exceeded 30 minute limit\nCheck logs for details"
        else
            echo "$(date): ❌ ML training failed with exit code $EXIT_CODE" >> "$LOG_FILE"
            send_telegram "❌ **ML Training Failed**\n\nExit code: $EXIT_CODE\nCheck logs for details"
        fi
    fi
else
    echo "$(date): ⏭️ Skipping ML training - no new data or recent training completed" >> "$LOG_FILE"
fi

# Cleanup old logs (keep 14 days for travel debugging)
find logs/ -name "ml_training_*.log" -mtime +14 -delete 2>/dev/null || true

# Show summary
echo "$(date): 🏁 Smart ML training finished" >> "$LOG_FILE"

# Also log basic stats for monitoring
echo "  - Uptime: ${HOURS_SINCE_BOOT}h since boot" >> "$LOG_FILE"
echo "  - New predictions: $NEW_DATA_COUNT" >> "$LOG_FILE"
echo "  - Training executed: $SHOULD_TRAIN" >> "$LOG_FILE"
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

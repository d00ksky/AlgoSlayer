#!/bin/bash
# ML Training Wrapper Script for Cron
cd "$(dirname "$0")"

# Log file with timestamp
LOG_FILE="logs/ml_training_$(date +%Y%m%d).log"

echo "$(date): Starting ML training..." >> "$LOG_FILE"

# Run ML training with timeout (max 30 minutes)
timeout 1800 python sync_and_train_ml.py >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "$(date): ML training completed successfully" >> "$LOG_FILE"
elif [ $EXIT_CODE -eq 124 ]; then
    echo "$(date): ML training timed out after 30 minutes" >> "$LOG_FILE"
else
    echo "$(date): ML training failed with exit code $EXIT_CODE" >> "$LOG_FILE"
fi

# Keep only last 7 days of logs
find logs/ -name "ml_training_*.log" -mtime +7 -delete 2>/dev/null || true

echo "$(date): ML training wrapper finished" >> "$LOG_FILE"

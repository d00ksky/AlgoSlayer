#!/bin/bash
# Automated Cloud Deployment Script
# Ensures cloud server always has latest configurations and code

set -e

CLOUD_SERVER="root@64.226.96.90"
CLOUD_PATH="/opt/rtx-trading"
LOCAL_REPO="/home/dooksky/repo/AlgoSlayer"

echo "🚀 Starting automated deployment to cloud server..."
echo "=================================="

# Function to check if file changed
file_changed() {
    local file=$1
    local local_file="${LOCAL_REPO}/${file}"
    local cloud_file="${CLOUD_PATH}/${file}"
    
    if [ ! -f "$local_file" ]; then
        echo "❌ Local file not found: $local_file"
        return 1
    fi
    
    # Get file hashes
    local_hash=$(md5sum "$local_file" | cut -d' ' -f1)
    cloud_hash=$(ssh "$CLOUD_SERVER" "md5sum '$cloud_file' 2>/dev/null | cut -d' ' -f1" || echo "missing")
    
    if [ "$local_hash" != "$cloud_hash" ]; then
        echo "📝 File changed: $file"
        return 0
    else
        echo "✅ File up to date: $file"
        return 1
    fi
}

# Function to deploy file
deploy_file() {
    local file=$1
    local local_file="${LOCAL_REPO}/${file}"
    local cloud_file="${CLOUD_PATH}/${file}"
    
    echo "📤 Deploying: $file"
    scp "$local_file" "${CLOUD_SERVER}:${cloud_file}"
}

# Check connectivity
echo "🔍 Checking cloud server connectivity..."
if ! ssh "$CLOUD_SERVER" "echo 'Connected'" >/dev/null 2>&1; then
    echo "❌ Cannot connect to cloud server"
    exit 1
fi
echo "✅ Cloud server reachable"

# Files to sync
FILES_TO_SYNC=(
    "run_server.py"
    "src/core/telegram_bot.py"
    "src/core/scheduler.py"
    "src/core/options_scheduler.py"
    "src/core/options_prediction_engine.py"
    "src/core/options_paper_trader.py"
    "src/core/options_data_engine.py"
    "src/core/options_ml_integration.py"
    "src/core/learning_system.py"
    "src/signals/mean_reversion_signal.py"
    "config/options_config.py"
    "config/trading_config.py"
    ".env"
)

# Check which files need updating
NEEDS_UPDATE=false
echo "🔍 Checking for file changes..."

for file in "${FILES_TO_SYNC[@]}"; do
    if file_changed "$file"; then
        NEEDS_UPDATE=true
    fi
done

if [ "$NEEDS_UPDATE" = false ]; then
    echo "✅ All files are up to date - no deployment needed"
    exit 0
fi

echo ""
echo "📦 Deploying updated files..."

# Deploy changed files
for file in "${FILES_TO_SYNC[@]}"; do
    if file_changed "$file"; then
        deploy_file "$file"
    fi
done

# Restart service if needed
echo ""
echo "🔄 Restarting trading service..."
ssh "$CLOUD_SERVER" "systemctl restart rtx-trading"

# Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 5

# Check service status
echo "🔍 Checking service status..."
if ssh "$CLOUD_SERVER" "systemctl is-active rtx-trading --quiet"; then
    echo "✅ Service restarted successfully"
    
    # Show recent logs
    echo ""
    echo "📋 Recent logs:"
    ssh "$CLOUD_SERVER" "journalctl -u rtx-trading --since '10 seconds ago' --no-pager | tail -10"
else
    echo "❌ Service failed to start"
    echo "📋 Error logs:"
    ssh "$CLOUD_SERVER" "journalctl -u rtx-trading --since '30 seconds ago' --no-pager | tail -20"
    exit 1
fi

echo ""
echo "✅ Deployment completed successfully!"
echo "🔗 Monitor logs: ssh $CLOUD_SERVER \"journalctl -u rtx-trading -f\""
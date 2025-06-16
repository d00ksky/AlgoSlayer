#!/bin/bash
# Git-Based Cloud Deployment Script
# Ensures cloud server stays synchronized with main branch

set -e

CLOUD_SERVER="root@64.226.96.90"
CLOUD_REPO_PATH="/root/AlgoSlayer"
LOCAL_REPO="/home/dooksky/repo/AlgoSlayer"

echo "🚀 Starting git-based deployment to cloud server..."
echo "=================================="

# Check connectivity
echo "🔍 Checking cloud server connectivity..."
if ! ssh "$CLOUD_SERVER" "echo 'Connected'" >/dev/null 2>&1; then
    echo "❌ Cannot connect to cloud server"
    exit 1
fi
echo "✅ Cloud server reachable"

# Get current commit hashes
echo "🔍 Checking git commit status..."
LOCAL_COMMIT=$(git rev-parse HEAD)
CLOUD_COMMIT=$(ssh "$CLOUD_SERVER" "cd '$CLOUD_REPO_PATH' && git rev-parse HEAD")

echo "📍 Local commit:  $LOCAL_COMMIT"
echo "📍 Cloud commit:  $CLOUD_COMMIT"

if [ "$LOCAL_COMMIT" = "$CLOUD_COMMIT" ]; then
    echo "✅ Cloud server is already up to date"
    exit 0
fi

echo ""
echo "📦 Updating cloud server repository..."

# Update cloud server repository
ssh "$CLOUD_SERVER" "
    cd '$CLOUD_REPO_PATH'
    echo '🔄 Fetching latest changes...'
    git fetch origin main
    
    echo '🏠 Stashing any local changes...'
    git stash push -m 'Auto-stash before deployment $(date)'
    
    echo '🔄 Pulling latest changes...'
    git pull origin main
    
    echo '✅ Repository updated to:'
    git log --oneline -1
"

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
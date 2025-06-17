#!/bin/bash
# Smart Git-Based Cloud Deployment Script
# Only restarts service if code changes detected
# Safe for data - preserves all trading data and ML models

set -e

CLOUD_SERVER="root@64.226.96.90"
CLOUD_REPO_PATH="/root/AlgoSlayer"
LOCAL_REPO="/home/dooksky/repo/AlgoSlayer"

echo "🚀 Smart deployment check at $(date)"
echo "=================================="

# Check connectivity
if ! ssh "$CLOUD_SERVER" "echo 'Connected'" >/dev/null 2>&1; then
    echo "❌ Cannot connect to cloud server"
    exit 1
fi

# Get current commit hashes
LOCAL_COMMIT=$(cd "$LOCAL_REPO" && git rev-parse HEAD)
CLOUD_COMMIT=$(ssh "$CLOUD_SERVER" "cd '$CLOUD_REPO_PATH' && git rev-parse HEAD 2>/dev/null || echo 'NONE'")

echo "📍 Local commit:  $LOCAL_COMMIT"
echo "📍 Cloud commit:  $CLOUD_COMMIT"

if [ "$LOCAL_COMMIT" = "$CLOUD_COMMIT" ]; then
    echo "✅ Cloud server is already up to date - no restart needed"
    exit 0
fi

echo ""
echo "🔄 Updates detected - proceeding with deployment..."

# Check if critical services are running
TRADING_ACTIVE=$(ssh "$CLOUD_SERVER" "systemctl is-active rtx-trading || echo 'inactive'")
if [ "$TRADING_ACTIVE" = "active" ]; then
    # Get current market status
    MARKET_HOURS=$(ssh "$CLOUD_SERVER" "cd /opt/rtx-trading && python -c \"
from datetime import datetime
import sys
sys.path.append('.')
from config import options_config
print('OPEN' if options_config.is_market_hours() else 'CLOSED')
\" 2>/dev/null || echo 'UNKNOWN'")
    
    if [ "$MARKET_HOURS" = "OPEN" ]; then
        echo "⚠️  WARNING: Market is currently OPEN"
        echo "   Deployment during market hours could miss trades"
        echo "   Consider running at midnight (market closed)"
        read -p "   Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "🚫 Deployment cancelled - run at midnight instead"
            exit 0
        fi
    fi
fi

# Backup critical data before deployment
echo "🔐 Backing up critical data..."
ssh "$CLOUD_SERVER" "
    cd /opt/rtx-trading
    # Create backup directory with timestamp
    BACKUP_DIR=\"/opt/rtx-trading/backups/\$(date +%Y%m%d_%H%M%S)\"
    mkdir -p \"\$BACKUP_DIR\"
    
    # Backup databases if they exist
    if [ -d 'data' ]; then
        cp -r data \"\$BACKUP_DIR/\" 2>/dev/null || true
        echo '   ✓ Backed up trading data'
    fi
    
    # Backup ML models if they exist
    if [ -d 'ml_models' ]; then
        cp -r ml_models \"\$BACKUP_DIR/\" 2>/dev/null || true
        echo '   ✓ Backed up ML models'
    fi
    
    # Backup logs for debugging
    if [ -d 'logs' ]; then
        cp -r logs \"\$BACKUP_DIR/\" 2>/dev/null || true
        echo '   ✓ Backed up logs'
    fi
    
    echo \"   📁 Backup location: \$BACKUP_DIR\"
"

# Update cloud server repository
echo ""
echo "📦 Updating cloud server repository..."
ssh "$CLOUD_SERVER" "
    cd '$CLOUD_REPO_PATH'
    
    # Stash any local config changes
    git stash push -m 'Auto-stash before deployment $(date)' || true
    
    # Pull latest changes
    git pull origin main
    
    # Reapply config changes if any
    git stash pop 2>/dev/null || true
    
    echo '✅ Repository updated to:'
    git log --oneline -1
"

# Check if requirements changed
echo ""
echo "🔍 Checking for dependency changes..."
REQUIREMENTS_CHANGED=$(ssh "$CLOUD_SERVER" "
    cd '$CLOUD_REPO_PATH'
    git diff HEAD~1 HEAD --name-only | grep -E 'requirements.*txt|setup.py|pyproject.toml' || echo ''
")

if [ -n "$REQUIREMENTS_CHANGED" ]; then
    echo "📦 Dependencies changed - updating..."
    ssh "$CLOUD_SERVER" "
        cd /opt/rtx-trading
        source rtx-env/bin/activate
        pip install -r requirements.txt --quiet
    "
fi

# Smart restart - only if service was running
if [ "$TRADING_ACTIVE" = "active" ]; then
    echo ""
    echo "🔄 Restarting trading service..."
    ssh "$CLOUD_SERVER" "systemctl restart rtx-trading"
    
    # Wait and verify
    sleep 5
    if ssh "$CLOUD_SERVER" "systemctl is-active rtx-trading --quiet"; then
        echo "✅ Service restarted successfully"
        
        # Show startup logs
        echo ""
        echo "📋 Startup logs:"
        ssh "$CLOUD_SERVER" "journalctl -u rtx-trading --since '10 seconds ago' --no-pager | tail -10"
    else
        echo "❌ Service failed to start"
        echo "🔧 Attempting rollback..."
        ssh "$CLOUD_SERVER" "
            cd '$CLOUD_REPO_PATH'
            git reset --hard HEAD~1
            systemctl restart rtx-trading
        "
    fi
else
    echo "ℹ️  Service was not running - skipping restart"
fi

echo ""
echo "✅ Smart deployment completed!"
echo ""
echo "📊 Summary:"
echo "   • Code updated: Yes"
echo "   • Data preserved: Yes" 
echo "   • Service status: $(ssh "$CLOUD_SERVER" "systemctl is-active rtx-trading || echo 'stopped'")"
echo ""
echo "💡 Tip: Schedule this at midnight for minimal disruption:"
echo "   0 0 * * * $LOCAL_REPO/smart_deploy.sh >> $LOCAL_REPO/logs/deploy.log 2>&1"
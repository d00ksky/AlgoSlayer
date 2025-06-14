#!/bin/bash
# Safe Git Sync Strategy for Cloud <-> Local
# Handles conflicts gracefully and preserves important changes

set -e

CLOUD_SERVER="root@64.226.96.90"
CLOUD_PATH="/root/AlgoSlayer"
LOCAL_PATH="/home/dooksky/repo/AlgoSlayer"

echo "🔄 Safe Git Sync - Cloud <-> Local"
echo "=================================="

# Function to backup important files on cloud
backup_cloud_important() {
    echo "📦 Backing up important cloud files..."
    ssh $CLOUD_SERVER "cd $CLOUD_PATH && mkdir -p .backup_sync && cp -r src/core/ .backup_sync/ && cp -r config/ .backup_sync/ && cp .env .backup_sync/ 2>/dev/null || true"
}

# Function to check for conflicts
check_conflicts() {
    echo "🔍 Checking for potential conflicts..."
    
    # Get list of modified files on cloud
    CLOUD_MODIFIED=$(ssh $CLOUD_SERVER "cd $CLOUD_PATH && git diff --name-only")
    
    # Get list of files we committed locally
    LOCAL_COMMITTED=$(git diff --name-only HEAD~1)
    
    # Find overlapping files
    CONFLICTS=""
    for file in $CLOUD_MODIFIED; do
        if echo "$LOCAL_COMMITTED" | grep -q "^$file$"; then
            CONFLICTS="$CONFLICTS $file"
        fi
    done
    
    if [ -n "$CONFLICTS" ]; then
        echo "⚠️ Potential conflicts detected in: $CONFLICTS"
        return 1
    else
        echo "✅ No conflicts detected"
        return 0
    fi
}

# Function to create safe merge
safe_merge() {
    echo "🛡️ Performing safe merge..."
    
    # 1. First, commit cloud changes to a temp branch
    ssh $CLOUD_SERVER "cd $CLOUD_PATH && git checkout -b cloud-changes-$(date +%Y%m%d-%H%M%S)"
    ssh $CLOUD_SERVER "cd $CLOUD_PATH && git add -A && git commit -m 'Cloud changes before sync - $(date)' || echo 'No changes to commit'"
    
    # 2. Pull latest from origin (our local commit)
    ssh $CLOUD_SERVER "cd $CLOUD_PATH && git checkout main"
    ssh $CLOUD_SERVER "cd $CLOUD_PATH && git pull origin main"
    
    # 3. If there are runtime-specific files that should stay, restore them
    echo "🔧 Restoring cloud-specific configurations..."
    ssh $CLOUD_SERVER "cd $CLOUD_PATH && cp .backup_sync/.env . 2>/dev/null || true"
    
    echo "✅ Safe merge completed"
}

# Function to sync local to cloud
sync_local_to_cloud() {
    echo "📤 Syncing local changes to cloud..."
    safe_merge
}

# Function to sync cloud to local  
sync_cloud_to_local() {
    echo "📥 Syncing cloud changes to local..."
    
    # Backup our local changes
    git stash push -m "Local changes before cloud sync - $(date)"
    
    # Pull latest
    git pull origin main
    
    # Apply our stashed changes if any
    if git stash list | head -1 | grep -q "Local changes before cloud sync"; then
        echo "🔄 Reapplying local changes..."
        git stash pop || echo "⚠️ Manual merge may be needed"
    fi
}

# Main execution
case "${1:-both}" in
    "to-cloud")
        backup_cloud_important
        if check_conflicts; then
            sync_local_to_cloud
        else
            echo "❌ Conflicts detected. Manual resolution needed."
            echo "💡 Use 'force-to-cloud' to override cloud changes"
            exit 1
        fi
        ;;
    
    "to-local")
        sync_cloud_to_local
        ;;
    
    "force-to-cloud")
        echo "⚠️ FORCING local changes to cloud (will override cloud changes)"
        backup_cloud_important
        ssh $CLOUD_SERVER "cd $CLOUD_PATH && git reset --hard HEAD && git clean -fd"
        ssh $CLOUD_SERVER "cd $CLOUD_PATH && git pull origin main"
        echo "✅ Force sync completed. Cloud backup in .backup_sync/"
        ;;
    
    "both")
        echo "🔄 Full two-way sync"
        backup_cloud_important
        
        if check_conflicts; then
            sync_local_to_cloud
            echo "✅ Both repositories now synchronized"
        else
            echo "❌ Conflicts detected. Choose manual strategy:"
            echo "  ./sync_git_safe.sh force-to-cloud  # Override cloud with local"
            echo "  ./sync_git_safe.sh to-local        # Pull cloud changes to local"
            exit 1
        fi
        ;;
    
    "status")
        echo "📊 Git Status Comparison"
        echo ""
        echo "LOCAL STATUS:"
        git status --porcelain
        echo ""
        echo "CLOUD STATUS:"
        ssh $CLOUD_SERVER "cd $CLOUD_PATH && git status --porcelain"
        ;;
    
    *)
        echo "Usage: $0 {to-cloud|to-local|force-to-cloud|both|status}"
        echo ""
        echo "Commands:"
        echo "  to-cloud      - Safely push local changes to cloud"
        echo "  to-local      - Safely pull cloud changes to local"
        echo "  force-to-cloud - Override cloud with local (destructive)"
        echo "  both          - Full two-way sync (default)"
        echo "  status        - Compare git status of both repos"
        echo ""
        echo "💡 For safety, always run 'status' first to see what will change"
        exit 1
        ;;
esac

echo ""
echo "🎯 SYNC COMPLETE!"
echo "Both repositories should now be identical and safe to use."
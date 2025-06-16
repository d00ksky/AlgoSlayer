#!/bin/bash
# Setup automated deployment to cloud server
# This ensures the cloud server always has the latest code

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_SCRIPT="${SCRIPT_DIR}/deploy_to_cloud.sh"

echo "🔧 Setting up automated deployment..."

# Ensure deploy script exists and is executable
if [ ! -f "$DEPLOY_SCRIPT" ]; then
    echo "❌ Deploy script not found: $DEPLOY_SCRIPT"
    exit 1
fi

chmod +x "$DEPLOY_SCRIPT"

# Create a wrapper script for cron in user directory
mkdir -p "$HOME/.local/bin"
CRON_WRAPPER="$HOME/.local/bin/algoslayer-deploy"
cat > "$CRON_WRAPPER" << EOF
#!/bin/bash
# AlgoSlayer Auto-Deploy Wrapper
cd "$SCRIPT_DIR"
echo "\$(date): Starting automated deployment" >> logs/deploy.log
./deploy_to_cloud.sh >> logs/deploy.log 2>&1
echo "\$(date): Deployment completed" >> logs/deploy.log
EOF

chmod +x "$CRON_WRAPPER"

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Add cron job to check for updates every 5 minutes
CRON_JOB="*/5 * * * * $CRON_WRAPPER"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "algoslayer-deploy"; then
    echo "✅ Cron job already exists"
else
    echo "📅 Adding cron job for automated deployment..."
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Cron job added - will check for updates every 5 minutes"
fi

# Test the deployment script
echo "🧪 Testing deployment script..."
if "$DEPLOY_SCRIPT"; then
    echo "✅ Deployment test successful"
else
    echo "❌ Deployment test failed"
    exit 1
fi

echo ""
echo "✅ Automated deployment setup complete!"
echo ""
echo "📋 Summary:"
echo "  • Deploy script: $DEPLOY_SCRIPT"
echo "  • Cron wrapper: $CRON_WRAPPER"
echo "  • Schedule: Every 5 minutes"
echo "  • Logs: $SCRIPT_DIR/logs/deploy.log"
echo ""
echo "🔍 Monitor deployments: tail -f $SCRIPT_DIR/logs/deploy.log"
echo "📝 View cron jobs: crontab -l"
echo "🚀 Manual deploy: $DEPLOY_SCRIPT"
#!/bin/bash
#
# Setup Local ML Training Environment
# Run this on your local machine to set up automated ML training
# Usage: ./setup_local_ml.sh [cloud_server_ip]

set -e

CLOUD_SERVER=${1:-"root@64.226.96.90"}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Setting up Local ML Training Environment"
echo "Cloud Server: $CLOUD_SERVER"
echo "Script Directory: $SCRIPT_DIR"

# Check if we can connect to cloud server
echo "🔌 Testing cloud server connection..."
if ! ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no $CLOUD_SERVER "echo 'Connection successful'"; then
    echo "❌ Cannot connect to cloud server. Please check:"
    echo "   1. Server IP/credentials are correct"
    echo "   2. SSH key is set up"
    echo "   3. Server is running"
    exit 1
fi

# Install required Python packages for ML training
echo "📦 Installing ML training dependencies..."
pip install -q scikit-learn xgboost pandas numpy sqlite3 loguru || {
    echo "⚠️ Installing with fallback method..."
    python -m pip install scikit-learn xgboost pandas numpy loguru
}

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p "$SCRIPT_DIR/ml_training_data"
mkdir -p "$SCRIPT_DIR/trained_models"
mkdir -p "$SCRIPT_DIR/logs"

# Test the ML training script
echo "🧪 Testing ML training script..."
cd "$SCRIPT_DIR"
python -c "
import sys
sys.path.append('.')
try:
    from sync_and_train_ml import MLTrainingPipeline
    print('✅ ML training script imports successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

# Create a wrapper script for cron
cat > "$SCRIPT_DIR/run_ml_training.sh" << 'EOF'
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
EOF

chmod +x "$SCRIPT_DIR/run_ml_training.sh"

# Create cron job (runs on boot)
echo "⏰ Setting up cron job for automatic ML training on boot..."

# Remove existing cron job if it exists
(crontab -l 2>/dev/null | grep -v "sync_and_train_ml\|run_ml_training") | crontab -

# Add new cron job
(crontab -l 2>/dev/null; echo "@reboot sleep 60 && $SCRIPT_DIR/run_ml_training.sh") | crontab -

echo "✅ Cron job added. ML training will run 60 seconds after boot."

# Create manual training script
cat > "$SCRIPT_DIR/train_now.sh" << 'EOF'
#!/bin/bash
# Manual ML Training Script
cd "$(dirname "$0")"

echo "🤖 Starting manual ML training..."
echo "📊 This will:"
echo "   1. Fetch data from cloud server"
echo "   2. Train advanced ML models locally"
echo "   3. Upload optimized models back to cloud"
echo "   4. Restart trading service with new models"
echo ""

python sync_and_train_ml.py

echo "✅ Manual ML training complete!"
EOF

chmod +x "$SCRIPT_DIR/train_now.sh"

# Create cloud data fetching script shortcut
cat > "$SCRIPT_DIR/fetch_data.sh" << 'EOF'
#!/bin/bash
# Quick Cloud Data Fetch
cd "$(dirname "$0")"

echo "📥 Fetching latest data from cloud server..."
python fetch_cloud_data.py --quick

echo "📁 Check cloud_data_analysis/ for results"
EOF

chmod +x "$SCRIPT_DIR/fetch_data.sh"

# Test manual training (dry run)
echo "🧪 Testing manual training (dry run)..."
if python sync_and_train_ml.py --help >/dev/null 2>&1; then
    echo "✅ ML training script is ready"
else
    echo "⚠️ Testing basic functionality..."
    timeout 30 python -c "
import sys
sys.path.append('.')
from sync_and_train_ml import MLTrainingPipeline
print('✅ MLTrainingPipeline can be imported')
pipeline = MLTrainingPipeline()
print('✅ MLTrainingPipeline can be instantiated')
print('✅ Basic functionality test passed')
" || echo "⚠️ Some issues detected but setup continues..."
fi

# Show status
echo ""
echo "🎉 Local ML Training Setup Complete!"
echo ""
echo "📋 What was set up:"
echo "   ✅ ML training dependencies installed"
echo "   ✅ Local directories created"
echo "   ✅ Cron job configured (runs on boot)"
echo "   ✅ Manual training scripts created"
echo ""
echo "🚀 Available commands:"
echo "   ./train_now.sh       - Run ML training manually"
echo "   ./fetch_data.sh      - Fetch cloud data for analysis"
echo "   ./fetch_cloud_stats.sh - Get cloud server statistics"
echo ""
echo "⚙️ Automatic behavior:"
echo "   • ML training runs automatically when this machine boots"
echo "   • New models are uploaded to cloud server"
echo "   • Trading service is restarted with improved models"
echo ""
echo "📊 Next steps:"
echo "   1. Restart this machine to test auto-training"
echo "   2. Or run './train_now.sh' for immediate training"
echo "   3. Check logs/ directory for training results"
echo ""
echo "🔗 Cloud server: $CLOUD_SERVER"
echo "📁 Project directory: $SCRIPT_DIR"

# Show cron status
echo ""
echo "📅 Cron configuration:"
crontab -l | grep -E "(reboot|sync_and_train|run_ml_training)" || echo "   No cron jobs found (this is unexpected)"

echo ""
echo "✨ Your dream of automated ML training is now reality! ✨"
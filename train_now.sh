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

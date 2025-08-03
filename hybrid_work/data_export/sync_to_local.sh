#!/bin/bash
# Data Sync Script for Local Machine Training
# Generated: 2025-07-24T19:26:26.960650

echo "🔄 Syncing AlgoSlayer training data from server..."

# Create local data directory
mkdir -p ./algoslayer_data
cd ./algoslayer_data

# Sync exported data files
rsync -av --progress server:/opt/rtx-trading/data_export/ ./server_export/

# Sync models directory
rsync -av --progress server:/opt/rtx-trading/trained_models/ ./models/

# Sync source code for reference
rsync -av --progress server:/root/AlgoSlayer/src/ml/ ./ml_source/

echo "✅ Data sync completed!"
echo "📊 Ready for local machine training"
echo ""
echo "Next steps:"
echo "1. Review data in ./server_export/"
echo "2. Run Phase 2 training: python3 sync_and_train_ml_phase2.py"
echo "3. Upload results back to server"

#!/bin/bash
#
# Fetch cloud server statistics and predictions
# Usage: ./fetch_cloud_stats.sh

CLOUD_SERVER="root@64.226.96.90"
OUTPUT_DIR="cloud_data_analysis"

echo "🚀 Fetching data from cloud server: $CLOUD_SERVER"
mkdir -p "$OUTPUT_DIR"

# 1. System Status
echo "📊 Getting system status..."
ssh $CLOUD_SERVER "systemctl status rtx-trading --no-pager -n 0" > "$OUTPUT_DIR/service_status.txt" 2>/dev/null

# 2. Recent Predictions (last 100)
echo "🎯 Fetching recent predictions..."
ssh $CLOUD_SERVER "grep -E 'Prediction cycle complete' /opt/rtx-trading/logs/rtx_trading_*.log | tail -100" > "$OUTPUT_DIR/predictions.txt" 2>/dev/null

# 3. High Confidence Predictions
echo "🔥 Finding high-confidence predictions (≥80%)..."
ssh $CLOUD_SERVER "grep -E 'BUY.*[8-9][0-9]\.[0-9]%|BUY.*100\.[0-9]%' /opt/rtx-trading/logs/rtx_trading_*.log | tail -50" > "$OUTPUT_DIR/high_confidence.txt" 2>/dev/null

# 4. Configuration
echo "⚙️  Getting configuration..."
ssh $CLOUD_SERVER "grep -E '^(TRADING_ENABLED|PAPER_TRADING|PREDICTION_ONLY|CONFIDENCE_THRESHOLD|MIN_SIGNALS_AGREEING|TARGET_RTX_SHARES)=' /opt/rtx-trading/.env" > "$OUTPUT_DIR/config.txt" 2>/dev/null

# 5. Signal Performance Summary
echo "📈 Analyzing signal performance..."
for signal in news_sentiment technical_analysis options_flow volatility_analysis momentum sector_correlation mean_reversion market_regime; do
    echo -e "\n=== $signal ===" >> "$OUTPUT_DIR/signal_summary.txt"
    ssh $CLOUD_SERVER "grep -A3 \"$signal\" /opt/rtx-trading/logs/rtx_trading_*.log | grep -E 'BUY|SELL|HOLD' | tail -10" >> "$OUTPUT_DIR/signal_summary.txt" 2>/dev/null
done

# 6. Error Summary
echo "❌ Checking for errors..."
ssh $CLOUD_SERVER "tail -50 /opt/rtx-trading/logs/rtx_errors_*.log 2>/dev/null || echo 'No errors found'" > "$OUTPUT_DIR/errors.txt"

# 7. Generate Summary Report
echo -e "\n📝 Generating summary report..."
cat > "$OUTPUT_DIR/SUMMARY.md" << EOF
# RTX Trading System - Cloud Data Summary

Generated: $(date)
Server: $CLOUD_SERVER

## System Status
$(grep -E "Active:|Main PID:" "$OUTPUT_DIR/service_status.txt" || echo "Status unknown")

## Configuration
\`\`\`
$(cat "$OUTPUT_DIR/config.txt")
\`\`\`

## Recent Predictions Summary
- Total predictions in sample: $(wc -l < "$OUTPUT_DIR/predictions.txt")
- High confidence (≥80%): $(wc -l < "$OUTPUT_DIR/high_confidence.txt")

### Latest Predictions
\`\`\`
$(tail -10 "$OUTPUT_DIR/predictions.txt")
\`\`\`

### High Confidence Signals
\`\`\`
$(tail -5 "$OUTPUT_DIR/high_confidence.txt")
\`\`\`

## Errors
\`\`\`
$(tail -10 "$OUTPUT_DIR/errors.txt")
\`\`\`
EOF

echo "✅ Data fetched successfully!"
echo "📁 Output directory: $OUTPUT_DIR/"
echo ""
echo "Files created:"
ls -la "$OUTPUT_DIR/"
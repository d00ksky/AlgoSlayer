#!/bin/bash

# Test IBKR Gateway download URLs
echo "🧪 Testing IBKR Gateway Download URLs"
echo "===================================="

# Test stable version
echo "📥 Testing stable version..."
if curl -I "https://download.interactivebrokers.com/installers/ibgateway/stable-standalone/ibgateway-stable-standalone-linux-x64.sh" 2>/dev/null | grep -q "200 OK"; then
    echo "✅ Stable version URL works"
    STABLE_SIZE=$(curl -sI "https://download.interactivebrokers.com/installers/ibgateway/stable-standalone/ibgateway-stable-standalone-linux-x64.sh" | grep -i content-length | awk '{print $2}' | tr -d '\r')
    echo "   Size: $((STABLE_SIZE / 1024 / 1024)) MB"
else
    echo "❌ Stable version URL failed"
fi

echo ""

# Test latest version
echo "📥 Testing latest version..."
if curl -I "https://download.interactivebrokers.com/installers/ibgateway/latest-standalone/ibgateway-latest-standalone-linux-x64.sh" 2>/dev/null | grep -q "200 OK"; then
    echo "✅ Latest version URL works"
    LATEST_SIZE=$(curl -sI "https://download.interactivebrokers.com/installers/ibgateway/latest-standalone/ibgateway-latest-standalone-linux-x64.sh" | grep -i content-length | awk '{print $2}' | tr -d '\r')
    echo "   Size: $((LATEST_SIZE / 1024 / 1024)) MB"
else
    echo "❌ Latest version URL failed"
fi

echo ""
echo "🎯 Recommendation: Use the working URL in your setup script"
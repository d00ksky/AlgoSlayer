#!/usr/bin/env bash
set -euo pipefail

PLIST_NAME="com.algoslayer.heavytraining.plist"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME"

if [[ -f "$PLIST_PATH" ]]; then
  launchctl unload "$PLIST_PATH" || true
  rm -f "$PLIST_PATH"
  echo "✅ Removed LaunchAgent: $PLIST_PATH"
else
  echo "No LaunchAgent found at $PLIST_PATH"
fi


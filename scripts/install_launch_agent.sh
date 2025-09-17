#!/usr/bin/env bash
set -euo pipefail

# Install a user LaunchAgent to run the heavy-training checker periodically with approval.

REPO_DIR="$(cd "$(dirname "$0")"/.. && pwd)"
PLIST_NAME="com.algoslayer.heavytraining.plist"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME"

mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST_PATH" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>com.algoslayer.heavytraining</string>

    <key>ProgramArguments</key>
    <array>
      <string>/bin/bash</string>
      <string>-lc</string>
      <string>source .venv/bin/activate && python scripts/check_and_prompt_train.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>__REPO_DIR__</string>

    <!-- Every 6 hours -->
    <key>StartInterval</key>
    <integer>21600</integer>

    <key>RunAtLoad</key>
    <true/>

    <key>StandardOutPath</key>
    <string>__HOME__/Library/Logs/algoslayer_heavytraining.log</string>
    <key>StandardErrorPath</key>
    <string>__HOME__/Library/Logs/algoslayer_heavytraining.err</string>
  </dict>
</plist>
PLIST

# Templating
sed -i '' "s#__REPO_DIR__#${REPO_DIR//\//\\/}#g" "$PLIST_PATH"
sed -i '' "s#__HOME__#${HOME//\//\\/}#g" "$PLIST_PATH"

echo "Loading LaunchAgent: $PLIST_PATH"
launchctl unload "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl load -w "$PLIST_PATH"

echo "✅ Installed and loaded com.algoslayer.heavytraining"
echo "Logs: ~/Library/Logs/algoslayer_heavytraining.log"


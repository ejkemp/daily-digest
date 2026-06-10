#!/bin/bash
# Install (or reinstall) the launchd schedule for the daily digest.
# Generates the plist from this repo's actual location, so it works regardless
# of where the repo was cloned or which user runs it.
set -euo pipefail
cd "$(dirname "$0")"

REPO_DIR="$(pwd)"
LABEL="com.ethan.daily-digest"
PLIST_DST="$HOME/Library/LaunchAgents/$LABEL.plist"

mkdir -p "$HOME/Library/LaunchAgents" logs

cat > "$PLIST_DST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$REPO_DIR/run.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>6</integer>
        <key>Minute</key>
        <integer>30</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>$REPO_DIR/logs/launchd.out.log</string>
    <key>StandardErrorPath</key>
    <string>$REPO_DIR/logs/launchd.err.log</string>
</dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"

echo "Installed for repo at: $REPO_DIR"
echo "Next run: daily at 06:30."
echo "Run now with: launchctl kickstart gui/$(id -u)/$LABEL"

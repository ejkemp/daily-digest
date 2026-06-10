#!/bin/bash
# Install (or reinstall) the launchd schedule for the daily digest.
set -euo pipefail
cd "$(dirname "$0")"

PLIST_SRC="launchd/com.ethan.daily-digest.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.ethan.daily-digest.plist"

mkdir -p "$HOME/Library/LaunchAgents"
launchctl bootout "gui/$(id -u)/com.ethan.daily-digest" 2>/dev/null || true
cp "$PLIST_SRC" "$PLIST_DST"
launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
echo "Installed. Next run: daily at 06:30."
echo "Run now with: launchctl kickstart gui/$(id -u)/com.ethan.daily-digest"

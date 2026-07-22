#!/usr/bin/env bash
# Install a launchd job that refreshes value.json from live prices on an interval.
# Usage: ./scripts/schedule-macos.sh [interval_seconds]   (default 900 = 15 min)
#   Stop with: launchctl unload ~/Library/LaunchAgents/com.deskfolio.update.plist
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$(command -v python3 || echo /usr/bin/python3)"
INTERVAL="${1:-900}"
PLIST="$HOME/Library/LaunchAgents/com.deskfolio.update.plist"

mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.deskfolio.update</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PY</string>
    <string>$ROOT/scripts/live-update.py</string>
  </array>
  <key>WorkingDirectory</key><string>$ROOT</string>
  <key>StartInterval</key><integer>$INTERVAL</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$ROOT/.update.log</string>
  <key>StandardErrorPath</key><string>$ROOT/.update.log</string>
</dict>
</plist>
PL

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load -w "$PLIST"
echo "Scheduled com.deskfolio.update every ${INTERVAL}s."
echo "Logs:  $ROOT/.update.log"
echo "Stop:  launchctl unload $PLIST"

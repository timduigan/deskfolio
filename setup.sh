#!/usr/bin/env bash
# One-time setup for the EasyEquities widget.
# - seeds your personal data files from the examples (never overwrites)
# - installs the Übersicht widget with the correct data path
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

# 1. Seed personal data files (gitignored) from the committed examples.
[ -f "$ROOT/holdings.json" ] || { cp "$ROOT/holdings.example.json" "$ROOT/holdings.json"; echo "Created holdings.json (edit it with your account values)"; }
[ -f "$ROOT/value.json" ]    || { cp "$ROOT/value.example.json" "$ROOT/value.json";    echo "Created value.json (sample data — run scripts/build.py to replace)"; }

# 2. Install the Übersicht widget if Übersicht is present.
WIDGETS="$HOME/Library/Application Support/Übersicht/widgets"
if [ -d "$WIDGETS" ]; then
  DEST="$WIDGETS/easyequities"
  mkdir -p "$DEST"
  sed "s#__DATA_DIR__#$ROOT#g" "$ROOT/ubersicht-widget/easyequities.jsx" > "$DEST/easyequities.jsx"
  echo "Installed Übersicht widget -> $DEST"
  echo "It reads its data from: $ROOT"
else
  echo "Übersicht not found."
  echo "  Install it:  brew install --cask ubersicht"
  echo "  Then re-run: ./setup.sh"
fi

echo
echo "Next:"
echo "  1. Edit holdings.json with your EasyEquities account values"
echo "  2. Run:  python3 scripts/build.py"
echo "  3. Preview in a browser:  python3 -m http.server 8000  then open http://localhost:8000/widget.html"

#!/usr/bin/env bash
# start.sh - one-click launcher for sprinkler-tools (macOS / Linux)

set -e
cd "$(dirname "$0")/backend"

if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# shellcheck source=/dev/null
source .venv/bin/activate

echo "Installing dependencies..."
pip install -q -r requirements.txt

echo
echo "============================================================"
echo " sprinkler-tools API starting on http://localhost:8000"
echo " Open ../frontend/index.html in your browser to use the demo."
echo " Press Ctrl+C to stop the server."
echo "============================================================"
echo

uvicorn app:app --host 0.0.0.0 --port 8000 --reload

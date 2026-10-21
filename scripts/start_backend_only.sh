#!/bin/bash
# Start only the Python backend
# Usage: ./scripts/start_backend_only.sh
# Then in another terminal: ./scripts/start_frontend_only.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "================================================"
echo "  Starting Backend Only"
echo "================================================"
echo ""

# Activate venv
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
fi

# Clear Python cache
echo "▶ Clearing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

echo ""
echo "📡 Starting Flask backend on http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 -m kicli_code_assist.web.server

#!/bin/bash
# Start only the Vite frontend dev server
# Usage: ./scripts/start_frontend_only.sh
# Then in another terminal: ./scripts/start_backend_only.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT/web/frontend"

echo "================================================"
echo "  Starting Frontend Only"
echo "================================================"
echo ""

# Check npm installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found"
    exit 1
fi

# Clear Vite cache
echo "▶ Clearing Vite cache..."
rm -rf node_modules/.vite 2>/dev/null || true

echo ""
echo "🎨 Starting Vite dev server on http://localhost:3000"
echo ""
echo "Backend should be running on :8000 (in another terminal)"
echo ""
echo "Press Ctrl+C to stop"
echo ""

HOST=0.0.0.0 PORT=3000 npm run dev

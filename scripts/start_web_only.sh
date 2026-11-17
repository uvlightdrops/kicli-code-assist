#!/bin/bash
# Quick start script for kicli-assist Web IDE
# only start , no deps

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PID=""
FRONTEND_PID=""

echo "================================================"
echo "  kicli-assist only launcher"
echo "================================================"
echo ""

# Check prerequisites
echo "▶ Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm not found"
    exit 1
fi


# Start servers
echo "▶ Starting servers..."
echo ""

cd "$PROJECT_ROOT"
source .venv/bin/activate

echo "📡 Starting backend on http://127.0.0.1:8100"
python -m kicli_code_assist.web.server > /tmp/kicli-web-backend.log 2>&1 &
BACKEND_PID=$!
sleep 2

echo "🎨 Starting frontend on http://127.0.0.1:5173"
cd web/frontend
VITE_API_URL=http://127.0.0.1:8100 npm run dev -- --host 127.0.0.1 --port 5173 --strictPort > /tmp/kicli-web-frontend.log 2>&1 &
FRONTEND_PID=$!
sleep 3

echo ""
echo "================================================"
echo "  ✅ Web IDE is running!"
echo "================================================"
echo ""
echo "  Frontend: http://127.0.0.1:5173"
echo "  Backend:  http://127.0.0.1:8100/api/health"
echo ""
echo "Logs:"
echo "  Backend:  tail -f /tmp/kicli-web-backend.log"
echo "  Frontend: tail -f /tmp/kicli-web-frontend.log"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Trap Ctrl+C
trap "echo ''; echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; exit" INT

# Keep running
wait

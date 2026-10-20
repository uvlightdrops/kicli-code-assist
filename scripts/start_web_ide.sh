#!/bin/bash
# Quick start script for kicli-assist Web IDE
# Run this from the project root: bash scripts/start_web_ide.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PID=""
FRONTEND_PID=""

echo "================================================"
echo "  kicli-assist Web IDE Launcher"
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

echo "✅ Python and npm found"
echo ""

# Setup backend
echo "▶ Setting up backend..."
cd "$PROJECT_ROOT"

if [ ! -f ".venv/bin/python" ]; then
    echo "⚠ Virtual environment not found, creating..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q flask flask-socketio python-socketio python-engineio flask-cors >/dev/null 2>&1 || true

echo "✅ Backend dependencies ready"
echo ""

# Setup frontend
echo "▶ Setting up frontend..."
cd "$PROJECT_ROOT/web/frontend"

if [ ! -d "node_modules" ]; then
    echo "⚠ Dependencies not installed, running npm install..."
    npm install -q
fi

echo "✅ Frontend dependencies ready"
echo ""

# Start servers
echo "▶ Starting servers..."
echo ""

cd "$PROJECT_ROOT"
source .venv/bin/activate

echo "📡 Starting backend on http://localhost:8000"
python -m kicli_code_assist.web.server > /tmp/kicli-web-backend.log 2>&1 &
BACKEND_PID=$!
sleep 2

echo "🎨 Starting frontend on http://localhost:3000"
cd web/frontend
npm run dev > /tmp/kicli-web-frontend.log 2>&1 &
FRONTEND_PID=$!
sleep 3

echo ""
echo "================================================"
echo "  ✅ Web IDE is running!"
echo "================================================"
echo ""
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000/api/health"
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


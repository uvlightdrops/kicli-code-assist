#!/bin/bash
# Local testing for semi-prod deployment scenarios
#
# Simulates Apache2 reverse proxy on localhost
# No root required, no Apache2 needed
#
# Usage: ./scripts/test_deployment_local.sh [option]

OPTION="${1:-1}"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo ""
echo "🧪 Local Deployment Test - Option $OPTION"
echo ""

if [[ "$OPTION" == "1" ]]; then
    echo "Testing Option 1 (Single-port):"
    echo ""
    echo "  1. Collect static files..."
    cd "$PROJECT_ROOT"
    
    if [[ ! -d "web/frontend/dist" ]]; then
        echo "     Building frontend..."
        npm run build --prefix web/frontend
    fi
    
    echo "     Copying to static/"
    ./scripts/collect_static.sh --no-build
    
    echo ""
    echo "  2. Start Flask backend..."
    echo "     → http://localhost:8000"
    echo ""
    echo "  Run in terminal:"
    echo "    cd $PROJECT_ROOT"
    echo "    source .venv/bin/activate"
    echo "    python -m kicli_code_assist.web.server"
    echo ""
    echo "  Test in another terminal:"
    echo "    curl http://localhost:8000/api/health"
    echo "    curl http://localhost:8000/"
    echo ""
    
elif [[ "$OPTION" == "2" ]]; then
    echo "Testing Option 2 (Dual-port):"
    echo ""
    echo "  1. Start Flask backend..."
    echo "     → http://localhost:8000"
    echo ""
    echo "  Run in terminal 1:"
    echo "    cd $PROJECT_ROOT"
    echo "    source .venv/bin/activate"
    echo "    python -m kicli_code_assist.web.server"
    echo ""
    echo "  2. Start Vite frontend..."
    echo "     → http://localhost:3000"
    echo ""
    echo "  Run in terminal 2:"
    echo "    cd $PROJECT_ROOT/web/frontend"
    echo "    npm install  # if needed"
    echo "    npm run dev"
    echo ""
    echo "  Test in another terminal:"
    echo "    curl http://localhost:8000/api/health"
    echo "    curl http://localhost:3000/"
    echo ""
else
    echo "❌ Invalid option. Use 1 or 2."
    exit 1
fi

echo "Documentation:"
echo "  docs/deployment/SEMI_PROD_DEPLOYMENT.md"
echo ""

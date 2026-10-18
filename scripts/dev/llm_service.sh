#!/bin/bash
# Start LLM service for development

set -e

cd "$(dirname "$0")/../.."

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "ERROR: .venv not found. Run: make dev-setup"
    exit 1
fi

source .venv/bin/activate

# Check if FastAPI/uvicorn installed
if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "Installing FastAPI and uvicorn..."
    pip install -q fastapi uvicorn httpx
fi

echo "Starting LLM Service on http://127.0.0.1:9001"
echo "Reload code changes with: curl -X POST http://127.0.0.1:9001/reload"
echo "Stop service: Ctrl+C"
echo ""

python3 -m kicli_code_assist.services.llm_service "$@"

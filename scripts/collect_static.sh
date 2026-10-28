#!/bin/bash
# Collect static files from frontend build for semi-prod deployment
# 
# Option 1 only: copies Vite dist/ to Flask static/
# 
# Usage: ./scripts/collect_static.sh [--no-build]
#   --no-build: Skip npm run build (use existing dist/)

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="${PROJECT_ROOT}/web/frontend"
STATIC_DIR="${PROJECT_ROOT}/kicli-code-assist/web/static"
#STATIC_DIR="${PROJECT_ROOT}/kicli_code_assist/web/static"
BUILD_FIRST=true

# Parse args
[[ "$1" == "--no-build" ]] && BUILD_FIRST=false

echo "📦 Collecting static files for Option 1 (single-port)"
echo ""

# Step 1: Build frontend if needed
if [[ "$BUILD_FIRST" == true ]]; then
    echo "▶ Building frontend..."
    cd "$FRONTEND_DIR"
		echo "XXX run build"
    npm run build
    echo "✅ Build complete: dist/"
    echo ""
fi

# Step 2: Clear existing static
echo "▶ Clearing existing static files..."
rm -rf "$STATIC_DIR"
mkdir -p "$STATIC_DIR"

# Step 3: Copy dist to static
echo "▶ Copying dist/ → static/..."
cp -r "${FRONTEND_DIR}/dist/"* "$STATIC_DIR/"

# Step 4: Verify
FILE_COUNT=$(find "$STATIC_DIR" -type f | wc -l)
echo "✅ Static files ready ($FILE_COUNT files)"
echo ""

echo "📍 Location: $STATIC_DIR"
echo "🚀 Deploy with: python -m kicli_code_assist.web.server"
echo ""

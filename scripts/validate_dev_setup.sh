#!/bin/bash
set -e

echo "=== Development Stack Validation ==="
echo

# Check KI_STAGE
if [ -z "$KI_STAGE" ]; then
    echo "❌ KI_STAGE not set. Run: export KI_STAGE=development"
    exit 1
fi
echo "✅ KI_STAGE=$KI_STAGE"

# Check .env.local exists
if [ ! -f .env.local ]; then
    echo "⚠️  .env.local not found (optional but recommended)"
else
    echo "✅ .env.local exists"
fi

# Test API health
echo -n "Testing API health... "
if curl -s http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
    echo "✅"
else
    echo "❌ API not responding on :8000"
    exit 1
fi

# Test API root message
echo -n "Testing API message... "
API_MSG=$(curl -s http://127.0.0.1:8000/)
if echo "$API_MSG" | grep -q "5173"; then
    echo "✅ (points to :5173)"
else
    echo "❌ (doesn't point to :5173)"
    echo "   Response: $API_MSG"
    exit 1
fi

# Test Vite
echo -n "Testing Vite... "
VITE_RESPONSE=$(curl -I http://127.0.0.1:5173/ 2>&1)
if echo "$VITE_RESPONSE" | grep -q "200"; then
    echo "✅"
else
    echo "❌ Vite not responding correctly on :5173"
    echo "$VITE_RESPONSE"
    exit 1
fi

# Show config merge
echo
echo "=== Merged Config (stack.yaml services) ==="
.venv/bin/python -m stackctl -t local spec 2>/dev/null | grep -A 25 "services:" | head -30 || echo "(Could not retrieve merged config)"

echo
echo "=== All Checks Passed ✅ ==="
echo "Ready for development!"

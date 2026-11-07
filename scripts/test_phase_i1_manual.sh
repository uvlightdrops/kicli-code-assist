#!/bin/bash
# Phase I1 Manual Testing Guide
# Backend must be running on port 8000

set -e

PROJECT_ROOT="/home/flow/dev_flow/kicli-code-assist"
BACKEND_URL="http://localhost:8000"

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║  Phase I1: Real LLM Integration - Manual Testing Guide          ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Check 1: Backend health
echo "📋 STEP 1: Checking backend health..."
if curl -s "$BACKEND_URL/api/health" | grep -q "ok"; then
    echo "✅ Backend is healthy at $BACKEND_URL"
else
    echo "❌ Backend unreachable at $BACKEND_URL"
    echo "   Start with: KI_STAGE=development python -m stackenv start"
    exit 1
fi
echo ""

# Check 2: Integration test
echo "📋 STEP 2: Running integration test..."
cd "$PROJECT_ROOT"
if python3 scripts/test_phase_i1_integration.py > /tmp/test_result.log 2>&1; then
    echo "✅ Integration test passed"
    grep "Response success\|Agents used\|Answer length\|Chunks:" /tmp/test_result.log
else
    echo "❌ Integration test failed"
    cat /tmp/test_result.log
    exit 1
fi
echo ""

# Check 3: Interactive TUI test
echo "📋 STEP 3: Launching TUI for interactive testing..."
echo ""
echo "Instructions for TUI Testing:"
echo "────────────────────────────────────────────────────────────────────"
echo "1. FileTree (left panel):"
echo "   • Navigate using arrow keys ↑/↓"
echo "   • Expand folders by pressing Enter"
echo "   • Click on a Python file to select it"
echo ""
echo "2. Preview (center panel):"
echo "   • File content appears when selected"
echo "   • Scroll with Page Up/Down"
echo ""
echo "3. Agent Tabs (right panel):"
echo "   • Click 'Analyze' button to trigger analysis"
echo "   • Watch response populate in split panels:"
echo "     - Top: Agent's conversational response"
echo "     - Bottom: Chunks (observations, issues, solutions)"
echo ""
echo "4. Expected Flow:"
echo "   FileTree: Select file.py"
echo "     ↓"
echo "   Preview: Shows file content"
echo "     ↓"
echo "   Agent Tabs: Context updated"
echo "     ↓"
echo "   Click 'Analyze' button"
echo "     ↓"
echo "   Response appears (2-5 seconds)"
echo ""
echo "5. Quit: Press 'q' to exit"
echo "────────────────────────────────────────────────────────────────────"
echo ""

# Launch TUI
python3 -m kicli_code_assist.ui.tui_client

echo ""
echo "✅ Testing complete"
echo ""

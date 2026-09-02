#!/bin/bash
set -euo pipefail

echo "🚀 Setting up KI Code Assistant..."

# Check Python version
PYTHON_VERSION=$(python3 --version | grep -oE "[0-9]+\.[0-9]+")
MIN_VERSION="3.10"

if (( $(echo "$PYTHON_VERSION < $MIN_VERSION" | bc -l) )); then
    echo "❌ Python 3.10+ required, found $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION"

# Create venv
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -q --upgrade pip setuptools wheel
pip install -q -e .

# Check tmux (optional)
if command -v tmux &> /dev/null; then
    echo "✓ Tmux installed"
else
    echo "⚠️  Tmux not found (optional, needed for tmux mode)"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Quick start:"
echo "  source venv/bin/activate"
echo "  kicli-assist --help"
echo ""
echo "Modes:"
echo "  kicli-assist tui          # Terminal UI"
echo "  kicli-assist tmux         # Tmux layout"
echo "  kicli-assist chat         # Simple chat"

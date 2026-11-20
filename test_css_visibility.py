#!/usr/bin/env python3
"""Test if CSS changes are visible."""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Label
from kicli_code_assist.ui.textual_app import CodeAssistantMain

# Create a test to see the actual CSS
print("=== Testing CSS Visibility ===\n")

# Test 1: Import the main app
try:
    screen = CodeAssistantMain()
    print(f"✅ CodeAssistantMain screen created")
    print(f"   CSS_PATH: {screen.CSS_PATH}")
except Exception as e:
    print(f"❌ Failed: {e}")

# Test 2: Check the layout structure
print("\n=== Checking Layout Structure ===\n")

# Try to find which CSS file is actually used
from pathlib import Path
css_path = Path("kicli_code_assist/ui/styles/textual_app.tcss")

if css_path.exists():
    with open(css_path, 'r') as f:
        content = f.read()
    
    # Count specific rules
    border_none_count = content.count("border: none")
    border_heavy_count = content.count("border: heavy")
    padding_01_count = content.count("padding: 0 1")
    
    print(f"CSS Statistics:")
    print(f"  - 'border: none' occurrences: {border_none_count}")
    print(f"  - 'border: heavy' occurrences: {border_heavy_count}")
    print(f"  - 'padding: 0 1' occurrences: {padding_01_count}")
    
    if border_none_count > 0 and border_heavy_count == 0:
        print(f"\n✅ CSS is in MINIMALIST MODE (no heavy borders)")
    elif border_heavy_count > 0:
        print(f"\n❌ CSS is in OLD MODE (has heavy borders)")
    else:
        print(f"\n❓ CSS state unclear")

print("\n=== Looking for CSS Loading Issues ===\n")

# Check if maybe there's another CSS layer
import os
ui_dir = Path("kicli_code_assist/ui")
all_css = list(ui_dir.rglob("*.tcss"))
print(f"All CSS files found in UI:")
for f in all_css:
    print(f"  - {f.relative_to(ui_dir)}")
    
# Check if there's inline CSS that might override
print("\n=== Checking for inline CSS overrides ===\n")
app_py = Path("kicli_code_assist/ui/app.py")
if app_py.exists():
    with open(app_py, 'r') as f:
        content = f.read()
    
    # Look for inline CSS in DEFAULT_CSS
    if "DEFAULT_CSS" in content:
        print("⚠️  Found DEFAULT_CSS in app.py (might override file-based CSS)")
        # Find the line
        for i, line in enumerate(content.split('\n'), 1):
            if "DEFAULT_CSS" in line:
                print(f"   Line {i}: {line.strip()}")
    else:
        print("✅ No inline DEFAULT_CSS found (good)")

print("\n" + "="*50)
print("If CSS doesn't show changes: Problem is likely rendering,")
print("not CSS loading. Try:")
print("  1. Clear .venv pycache")
print("  2. Reinstall package: pip install -e .")
print("  3. Check if other CSS files override settings")
print("="*50)

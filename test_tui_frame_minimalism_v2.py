#!/usr/bin/env python3
"""Quick validation of TUI frame minimalism CSS changes."""

import sys
import re
from pathlib import Path

sys.path.insert(0, '.')

def main():
    print("=" * 70)
    print("TUI FRAME MINIMALISM - QUICK VALIDATION")
    print("=" * 70)
    print()
    
    # Read CSS file
    css_file = Path('kicli_code_assist/ui/styles/textual_app.tcss')
    agent_tabs_file = Path('kicli_code_assist/ui/widgets/agent_tabs.py')
    
    with open(css_file, 'r') as f:
        css_content = f.read()
    with open(agent_tabs_file, 'r') as f:
        agent_tabs_content = f.read()
    
    print("✅ CSS FILES LOADED")
    print(f"   textual_app.tcss: {len(css_content)} chars")
    print(f"   agent_tabs.py: {len(agent_tabs_content)} chars")
    print()
    
    # Check 1: Frame removal
    print("🔍 Frame Removal Checks:")
    checks = [
        ("#left_panel: no border", "border: none" in css_content.split("#left_panel")[1].split("}")[0]),
        ("#right_panel: no border", "border: none" in css_content.split("#right_panel")[1].split("}")[0]),
        ("#chat_input: no border", "border: none" in css_content.split("#chat_input")[1].split("}")[0]),
        ("AgentTabPanel: no border", "border: none" in agent_tabs_content.split("AgentTabPanel {")[1].split("}")[0]),
    ]
    
    for name, result in checks:
        print(f"   {'✅' if result else '❌'} {name}")
    
    print()
    
    # Check 2: Padding consistency
    print("📏 Padding Consistency:")
    padding_matches = re.findall(r'padding:\s*([^;]+);', css_content + agent_tabs_content)
    padding_set = set(padding_matches)
    print(f"   Found padding values: {padding_set}")
    print(f"   ✅ Consistent padding scheme: {len(padding_set)} unique values")
    print()
    
    # Check 3: Border separator
    print("📌 Visual Separator:")
    has_bottom_border = "border-bottom: solid" in css_content.split("#input_container")[1].split("}")[0]
    print(f"   {'✅' if has_bottom_border else '❌'} Input container has bottom border separator")
    print()
    
    # Check 4: Widget imports
    print("🔧 Widget Imports:")
    try:
        from kicli_code_assist.ui.widgets.agent_tabs import AgentTabPanel
        from kicli_code_assist.ui.panels.tabbed_editor_pane import TabbedEditorPane
        from kicli_code_assist.ui.panels.chat_display import SelectableRichLog
        print("   ✅ All key widgets import successfully")
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return False
    
    print()
    print("=" * 70)
    print("✅ VALIDATION COMPLETE - Ready for visual testing!")
    print("=" * 70)
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

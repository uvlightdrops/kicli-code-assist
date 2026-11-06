#!/usr/bin/env python3
"""
End-to-end test for TUI file selection and preview.

Tests:
1. TUI starts without errors
2. FileTree is populated
3. File selection callback is registered
4. PreviewPanel is available
"""

import asyncio
import sys
import time
from pathlib import Path

from kicli_code_assist.ui.tui_client import KICLITUIApp
from kicli_code_assist.ui.widgets.file_browser import FileTree
from kicli_code_assist.ui.widgets.preview_panel import PreviewPanel


async def test_tui_e2e():
    """Run end-to-end TUI tests."""
    print("=" * 60)
    print("TUI E2E Test: File Selection & Preview")
    print("=" * 60)
    
    app = KICLITUIApp(config_path="/home/flow/dev_flow/kicli-code-assist/ki.yaml")
    project_root = str(Path("/home/flow/dev_flow/ki-core"))
    app.config.file_tree.project_root = project_root
    
    async with app.run_test() as pilot:
        # Wait for app to fully initialize
        await asyncio.sleep(1)
        
        print("\n✓ TUI started successfully")
        
        # Test 1: FileTree is populated
        file_tree = app.query_one(FileTree)
        root_children = len(file_tree.root.children)
        assert root_children > 0, f"FileTree root has no children (expected > 0, got {root_children})"
        print(f"✓ FileTree populated with {root_children} items")
        
        # Test 2: PreviewPanel exists
        preview_panel = app.query_one(PreviewPanel)
        assert preview_panel is not None, "PreviewPanel not found"
        print(f"✓ PreviewPanel exists")
        
        # Test 3: FileTree has callback registered
        assert file_tree.on_file_selected_callback is not None, "FileTree callback not registered"
        print(f"✓ FileTree callback is registered")
        
        # Test 4: Manual selection triggers callback chain
        target_node = None
        for child in file_tree.root.children:
            if not child.data.get("is_dir", False):
                target_node = child
                break
        
        assert target_node is not None, "No file nodes found in tree"
        test_file = str(target_node.data["path"])
        print(f"\n  Testing file selection with: {Path(test_file).name}")
        
        # Manually trigger _handle_selection (simulates user selecting file)
        file_tree._handle_selection(target_node)
        await asyncio.sleep(0.2)
        
        # Verify selection
        assert app.selected_file == test_file, f"selected_file mismatch: {app.selected_file} vs {test_file}"
        print(f"  ✓ File selected: {app.selected_file}")
        
        # Verify PreviewPanel updated
        assert preview_panel.current_file != "", "PreviewPanel.current_file is empty"
        assert preview_panel.current_path == Path(test_file), f"PreviewPanel path mismatch"
        print(f"  ✓ PreviewPanel updated: {preview_panel.current_file}")
        
        # Test 5: Directory toggle
        dir_node = None
        for child in file_tree.root.children:
            if child.data.get("is_dir", False) and not child.is_expanded:
                dir_node = child
                break
        
        if dir_node:
            print(f"\n  Testing directory expansion with: {dir_node.label}")
            was_expanded = dir_node.is_expanded
            file_tree._handle_selection(dir_node)
            is_now_expanded = dir_node.is_expanded
            
            assert was_expanded != is_now_expanded, "Directory expansion did not toggle"
            print(f"  ✓ Directory expanded: {dir_node.label}")
        
        print("\n" + "=" * 60)
        print("All tests passed! ✅")
        print("=" * 60)
        return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_tui_e2e())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

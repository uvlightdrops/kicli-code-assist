"""
Unit tests for the 3 new tabbed editor features:
1. Highlight New Files in FileTree
2. Populate Tabbed Editor with Code
3. Tab Navigation Shortcuts
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from textual.widgets.tree import TreeNode

# Import the classes we're testing
from kicli_code_assist.ui.widgets.file_browser import FileTree
from kicli_code_assist.ui.panels.tabbed_editor_pane import TabbedEditorPane, FileTab, FileStatus
from kicli_code_assist.ui.widgets.code_generation_panel import CodeGenerationPanel


# ============================================================================
# Feature 1: Highlight New Files in FileTree
# ============================================================================

class TestFileTreeHighlighting:
    """Test suite for FileTree highlighting feature."""
    
    def test_file_tree_init_highlight_set(self):
        """Test that FileTree initializes with empty highlight_files set."""
        tree = FileTree(project_root=".")
        assert hasattr(tree, 'highlight_files')
        assert isinstance(tree.highlight_files, set)
        assert len(tree.highlight_files) == 0
    
    def test_scan_project_accepts_highlight_files(self):
        """Test that scan_project accepts highlight_files parameter."""
        tree = FileTree(project_root=".")
        highlight_set = {"/path/to/file1.py", "/path/to/file2.py"}
        
        # Mock the actual directory scanning
        with patch.object(tree, '_add_directory'):
            tree.scan_project(highlight_files=highlight_set)
        
        # Verify highlight_files was set
        assert tree.highlight_files == highlight_set
    
    def test_highlight_files_persists(self):
        """Test that highlight files persist after scan_project call."""
        tree = FileTree(project_root=".")
        highlight_set = {"/path/file1.py"}
        
        with patch.object(tree, '_add_directory'):
            tree.scan_project(highlight_files=highlight_set)
        
        assert tree.highlight_files == highlight_set
        
        # Verify no highlight_files parameter doesn't clear it
        with patch.object(tree, '_add_directory'):
            tree.scan_project()
        
        assert tree.highlight_files == highlight_set
    
    def test_code_generation_panel_tracks_saved_files(self):
        """Test that CodeGenerationPanel tracks saved files in session."""
        panel = CodeGenerationPanel(project_root=".")
        
        # Verify the saved_files_this_session attribute exists
        assert hasattr(panel, 'saved_files_this_session')
        assert isinstance(panel.saved_files_this_session, set)
        assert len(panel.saved_files_this_session) == 0
    
    def test_refresh_file_tree_handles_errors(self):
        """Test that _refresh_file_tree handles errors gracefully."""
        panel = CodeGenerationPanel(project_root=".")
        
        # _refresh_file_tree should handle exceptions gracefully
        # Method should log and continue rather than crash
        try:
            # Try to refresh - will fail without active screen, but should handle it
            panel._refresh_file_tree(highlight_files={"/path/file.py"})
        except Exception as e:
            # Only Textual widget-related errors expected
            assert "screen" in str(e).lower() or "widget" in str(e).lower()


# ============================================================================
# Feature 2: Populate Tabbed Editor with Code
# ============================================================================

class TestTabbedEditorPopulation:
    """Test suite for populating TabbedEditorPane with code."""
    
    def test_add_file_tab_creates_file_tab(self):
        """Test that add_file_tab creates a FileTab with correct status."""
        editor = TabbedEditorPane()
        
        filepath = "/path/to/test.py"
        content = "print('hello')"
        
        editor.add_file_tab(filepath=filepath, content=content, status="new")
        
        assert filepath in editor.tabs
        assert editor.tabs[filepath].content == content
        assert editor.tabs[filepath].status == FileStatus.NEW
    
    def test_add_file_tab_sets_as_active(self):
        """Test that first added tab becomes active."""
        editor = TabbedEditorPane()
        
        filepath = "/path/to/test.py"
        editor.add_file_tab(filepath=filepath, content="code", status="new")
        
        assert editor.active_tab == filepath
    
    def test_add_multiple_file_tabs(self):
        """Test adding multiple file tabs."""
        editor = TabbedEditorPane()
        
        files = [
            ("/path/file1.py", "print(1)"),
            ("/path/file2.py", "print(2)"),
            ("/path/file3.py", "print(3)"),
        ]
        
        for filepath, content in files:
            editor.add_file_tab(filepath=filepath, content=content, status="new")
        
        assert len(editor.tabs) == 3
        for filepath, content in files:
            assert filepath in editor.tabs
            assert editor.tabs[filepath].content == content
    
    def test_add_file_tab_handles_large_content(self):
        """Test that add_file_tab handles large files gracefully."""
        editor = TabbedEditorPane()
        
        filepath = "/path/large_file.py"
        # Create content larger than 10MB
        large_content = "x = 1\n" * (2 * 1024 * 1024)  # ~12MB
        
        # Should not raise exception
        editor.add_file_tab(filepath=filepath, content=large_content, status="new")
        
        # Verify file was added (content should be truncated)
        assert filepath in editor.tabs
        assert len(editor.tabs[filepath].content) < len(large_content)
        assert "truncated" in editor.tabs[filepath].content.lower()
    
    def test_add_file_to_editor_integration(self):
        """Test that add_file_to_editor method works without screen access."""
        panel = CodeGenerationPanel(project_root=".")
        
        # We can't easily test this without a full Textual app,
        # but we can verify the method exists and handles errors gracefully
        assert hasattr(panel, '_add_file_to_editor')
        
        # Method should handle missing screen gracefully
        try:
            result = panel._add_file_to_editor(
                filepath="/path/test.py",
                content="print('test')"
            )
            # Should return False when screen is not available
            assert result is False
        except Exception as e:
            # Should not raise unhandled exceptions
            assert "screen" in str(e).lower() or isinstance(e, AttributeError)


# ============================================================================
# Feature 3: Tab Navigation Shortcuts
# ============================================================================

class TestTabNavigation:
    """Test suite for tab navigation shortcuts."""
    
    def test_next_tab_cycles_forward(self):
        """Test action_next_tab cycles to next tab."""
        editor = TabbedEditorPane()
        
        # Add 3 tabs
        for i in range(3):
            filepath = f"/path/file{i}.py"
            editor.add_file_tab(filepath=filepath, content=f"code{i}", status="new")
        
        tab_list = list(editor.tabs.keys())
        
        # First tab should be active
        assert editor.active_tab == tab_list[0]
        
        # Move to next
        editor.action_next_tab()
        assert editor.active_tab == tab_list[1]
        
        # Move to next
        editor.action_next_tab()
        assert editor.active_tab == tab_list[2]
        
        # Wrap around to first
        editor.action_next_tab()
        assert editor.active_tab == tab_list[0]
    
    def test_prev_tab_cycles_backward(self):
        """Test action_prev_tab cycles to previous tab."""
        editor = TabbedEditorPane()
        
        # Add 3 tabs
        for i in range(3):
            filepath = f"/path/file{i}.py"
            editor.add_file_tab(filepath=filepath, content=f"code{i}", status="new")
        
        tab_list = list(editor.tabs.keys())
        
        # Move to last tab
        editor.active_tab = tab_list[2]
        
        # Move to previous
        editor.action_prev_tab()
        assert editor.active_tab == tab_list[1]
        
        # Move to previous
        editor.action_prev_tab()
        assert editor.active_tab == tab_list[0]
        
        # Wrap around to last
        editor.action_prev_tab()
        assert editor.active_tab == tab_list[2]
    
    def test_close_tab_removes_current(self):
        """Test action_close_tab removes current tab."""
        editor = TabbedEditorPane()
        
        # Add 3 tabs
        filepaths = [f"/path/file{i}.py" for i in range(3)]
        for filepath in filepaths:
            editor.add_file_tab(filepath=filepath, content="code", status="new")
        
        # Close first tab
        editor.action_close_tab()
        
        assert filepaths[0] not in editor.tabs
        assert len(editor.tabs) == 2
    
    def test_close_tab_selects_previous(self):
        """Test that close_tab selects previous tab if available."""
        editor = TabbedEditorPane()
        
        # Add 3 tabs
        filepaths = [f"/path/file{i}.py" for i in range(3)]
        for filepath in filepaths:
            editor.add_file_tab(filepath=filepath, content="code", status="new")
        
        # Navigate to second tab and close it
        editor.action_next_tab()
        second_tab = editor.active_tab
        editor.action_close_tab()
        
        # Should select first tab (previous)
        assert second_tab not in editor.tabs
        assert editor.active_tab == filepaths[0]
    
    def test_close_tab_selects_first_if_at_start(self):
        """Test that close_tab selects first remaining tab."""
        editor = TabbedEditorPane()
        
        # Add 2 tabs
        filepaths = [f"/path/file{i}.py" for i in range(2)]
        for filepath in filepaths:
            editor.add_file_tab(filepath=filepath, content="code", status="new")
        
        # Close first tab (should select second which becomes first)
        editor.action_close_tab()
        
        assert filepaths[0] not in editor.tabs
        assert editor.active_tab == filepaths[1]
    
    def test_close_tab_no_tabs(self):
        """Test that close_tab handles empty editor gracefully."""
        editor = TabbedEditorPane()
        
        # Should not raise exception
        editor.action_close_tab()
        
        assert len(editor.tabs) == 0
        assert editor.active_tab is None
    
    def test_bindings_include_shortcuts(self):
        """Test that TabbedEditorPane has correct key bindings."""
        editor = TabbedEditorPane()
        
        binding_dict = {binding.key: binding.action for binding in editor.BINDINGS}
        
        # Check for the new shortcuts
        assert "ctrl+tab" in binding_dict
        assert binding_dict["ctrl+tab"] == "next_tab"
        
        assert "ctrl+shift+tab" in binding_dict
        assert binding_dict["ctrl+shift+tab"] == "prev_tab"
        
        assert "ctrl+w" in binding_dict
        assert binding_dict["ctrl+w"] == "close_tab"
    
    def test_next_tab_no_tabs(self):
        """Test next_tab with no tabs does nothing."""
        editor = TabbedEditorPane()
        
        # Should not raise exception
        editor.action_next_tab()
        
        assert editor.active_tab is None
        assert len(editor.tabs) == 0
    
    def test_prev_tab_no_tabs(self):
        """Test prev_tab with no tabs does nothing."""
        editor = TabbedEditorPane()
        
        # Should not raise exception
        editor.action_prev_tab()
        
        assert editor.active_tab is None
        assert len(editor.tabs) == 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for all three features working together."""
    
    def test_editor_tab_workflow(self):
        """Test complete editor tab workflow: add, navigate, close."""
        editor = TabbedEditorPane()
        
        # Step 1: Add multiple files
        files = [
            ("/path/app.py", "def main(): pass"),
            ("/path/utils.py", "def helper(): pass"),
            ("/path/config.py", "DEBUG = True"),
        ]
        
        for filepath, content in files:
            editor.add_file_tab(filepath=filepath, content=content, status="new")
        
        assert len(editor.tabs) == 3
        assert editor.active_tab == files[0][0]
        
        # Step 2: Navigate through tabs
        editor.action_next_tab()
        assert editor.active_tab == files[1][0]
        
        editor.action_next_tab()
        assert editor.active_tab == files[2][0]
        
        editor.action_prev_tab()
        assert editor.active_tab == files[1][0]
        
        # Step 3: Close middle tab
        editor.action_close_tab()
        assert files[1][0] not in editor.tabs
        assert len(editor.tabs) == 2
        assert editor.active_tab == files[0][0]
        
        # Step 4: Verify remaining tabs
        remaining = list(editor.tabs.keys())
        assert files[0][0] in remaining
        assert files[2][0] in remaining
    
    def test_file_tree_and_editor_integration(self):
        """Test integration between FileTree highlighting and editor population."""
        # Create both components
        tree = FileTree(project_root=".")
        editor = TabbedEditorPane()
        
        # Test that they can be used together
        highlight_files = {"/path/file1.py", "/path/file2.py"}
        
        with patch.object(tree, '_add_directory'):
            tree.scan_project(highlight_files=highlight_files)
        
        # Add files to editor
        for filepath in highlight_files:
            editor.add_file_tab(filepath=filepath, content="# code", status="new")
        
        # Verify integration worked
        assert tree.highlight_files == highlight_files
        assert len(editor.tabs) == 2
        assert editor.active_tab == list(highlight_files)[0]
    
    def test_file_status_tracking(self):
        """Test that file statuses are properly tracked."""
        editor = TabbedEditorPane()
        
        filepath = "/path/test.py"
        editor.add_file_tab(filepath=filepath, content="code", status="new")
        
        assert editor.tabs[filepath].status == FileStatus.NEW
        
        # Mark as saved
        editor.mark_file_status(filepath, "saved")
        assert editor.tabs[filepath].status == FileStatus.SAVED
        
        # Mark as modified
        editor.mark_file_status(filepath, "modified")
        assert editor.tabs[filepath].status == FileStatus.MODIFIED
        
        # Mark as error
        editor.mark_file_status(filepath, "error")
        assert editor.tabs[filepath].status == FileStatus.ERROR


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

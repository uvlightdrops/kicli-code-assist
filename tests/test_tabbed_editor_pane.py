"""Tests for TabbedEditorPane - Multi-file editor system.

Tests cover:
- Tab creation and removal
- Tab navigation (previous/next)
- Status marking and tracking
- File content access
- Save operations
- Language detection

Note: These are primarily unit tests that don't require Textual rendering.
"""

import pytest
from pathlib import Path

from kicli_code_assist.ui.panels.tabbed_editor_pane import (
    TabbedEditorPane,
    FileStatus,
    FileTab,
    FileContentViewer,
)


class TestFileTab:
    """Test FileTab data class."""
    
    def test_file_tab_creation(self):
        """Test creating a file tab."""
        tab = FileTab(
            filepath="/path/to/file.py",
            content="print('hello')",
            status=FileStatus.NEW,
        )
        
        assert tab.filepath == "/path/to/file.py"
        assert tab.content == "print('hello')"
        assert tab.status == FileStatus.NEW
    
    def test_language_detection_python(self):
        """Test language detection for Python files."""
        tab = FileTab(filepath="/test.py", content="")
        assert tab.get_language() == "python"
    
    def test_language_detection_javascript(self):
        """Test language detection for JavaScript files."""
        tab = FileTab(filepath="/test.js", content="")
        assert tab.get_language() == "javascript"
    
    def test_language_detection_yaml(self):
        """Test language detection for YAML files."""
        tab = FileTab(filepath="/test.yaml", content="")
        assert tab.get_language() == "yaml"
    
    def test_language_detection_unknown(self):
        """Test language detection for unknown files."""
        tab = FileTab(filepath="/test.unknown", content="")
        assert tab.get_language() is None
    
    def test_explicit_language_override(self):
        """Test explicit language parameter."""
        tab = FileTab(filepath="/test.py", content="", language="rust")
        assert tab.get_language() == "rust"
    
    def test_language_detection_various_extensions(self):
        """Test language detection for multiple file types."""
        test_cases = [
            ("/file.ts", "typescript"),
            ("/file.jsx", "jsx"),
            ("/file.tsx", "tsx"),
            ("/file.yml", "yaml"),
            ("/file.json", "json"),
            ("/file.html", "html"),
            ("/file.css", "css"),
            ("/file.sql", "sql"),
            ("/file.sh", "bash"),
            ("/file.go", "go"),
            ("/file.rs", "rust"),
            ("/file.java", "java"),
            ("/file.cpp", "cpp"),
            ("/file.c", "c"),
            ("/file.md", "markdown"),
        ]
        
        for filepath, expected_lang in test_cases:
            tab = FileTab(filepath=filepath, content="")
            assert tab.get_language() == expected_lang, f"Failed for {filepath}"


class TestTabbedEditorPaneLogic:
    """Test TabbedEditorPane core logic (without rendering)."""
    
    def setup_method(self):
        """Create a fresh pane for each test."""
        self.pane = TabbedEditorPane()
    
    def test_initialization(self):
        """Test pane initializes empty."""
        assert len(self.pane.tabs) == 0
        assert self.pane.active_tab is None
    
    def test_add_single_file_tab(self):
        """Test adding a single file tab."""
        self.pane.add_file_tab(
            filepath="/test/file.py",
            content="print('hello')",
            status="new"
        )
        
        assert len(self.pane.tabs) == 1
        assert "/test/file.py" in self.pane.tabs
        assert self.pane.active_tab == "/test/file.py"
        assert self.pane.tabs["/test/file.py"].status == FileStatus.NEW
    
    def test_add_multiple_file_tabs(self):
        """Test adding multiple file tabs."""
        self.pane.add_file_tab("/test1.py", "content1", "new")
        self.pane.add_file_tab("/test2.js", "content2", "modified")
        self.pane.add_file_tab("/test3.yaml", "content3", "saved")
        
        assert len(self.pane.tabs) == 3
        assert self.pane.active_tab == "/test1.py"  # First tab is active
    
    def test_add_tab_maintains_active_tab(self):
        """Test that adding new tabs doesn't change active tab."""
        self.pane.add_file_tab("/file1.py", "content1")
        active_1 = self.pane.active_tab
        
        self.pane.add_file_tab("/file2.py", "content2")
        active_2 = self.pane.active_tab
        
        assert active_1 == active_2
        assert active_1 == "/file1.py"
    
    def test_remove_file_tab(self):
        """Test removing a file tab."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.add_file_tab("/file2.py", "content2")
        
        self.pane.remove_file_tab("/file1.py")
        
        assert len(self.pane.tabs) == 1
        assert "/file1.py" not in self.pane.tabs
    
    def test_remove_active_tab_switches_to_other(self):
        """Test that removing active tab switches to another tab."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.add_file_tab("/file2.py", "content2")
        
        assert self.pane.active_tab == "/file1.py"
        
        self.pane.remove_file_tab("/file1.py")
        
        assert self.pane.active_tab == "/file2.py"
    
    def test_remove_last_tab(self):
        """Test removing the last tab."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.remove_file_tab("/file1.py")
        
        assert len(self.pane.tabs) == 0
        assert self.pane.active_tab is None
    
    def test_remove_nonexistent_tab(self):
        """Test removing a tab that doesn't exist."""
        self.pane.add_file_tab("/file1.py", "content1")
        
        # Should not raise
        self.pane.remove_file_tab("/file2.py")
        
        assert len(self.pane.tabs) == 1
    
    def test_mark_file_status_new(self):
        """Test marking file as new."""
        self.pane.add_file_tab("/file1.py", "content1", "saved")
        self.pane.mark_file_status("/file1.py", "new")
        
        assert self.pane.tabs["/file1.py"].status == FileStatus.NEW
        assert self.pane.tabs["/file1.py"].status.value == "🆕"
    
    def test_mark_file_status_modified(self):
        """Test marking file as modified."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.mark_file_status("/file1.py", "modified")
        
        assert self.pane.tabs["/file1.py"].status == FileStatus.MODIFIED
        assert self.pane.tabs["/file1.py"].status.value == "⚡"
    
    def test_mark_file_status_saved(self):
        """Test marking file as saved."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.mark_file_status("/file1.py", "saved")
        
        assert self.pane.tabs["/file1.py"].status == FileStatus.SAVED
        assert self.pane.tabs["/file1.py"].status.value == "💾"
    
    def test_mark_file_status_saving(self):
        """Test marking file as saving."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.mark_file_status("/file1.py", "saving")
        
        assert self.pane.tabs["/file1.py"].status == FileStatus.SAVING
        assert self.pane.tabs["/file1.py"].status.value == "⏳"
    
    def test_mark_file_status_error(self):
        """Test marking file with error status."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.mark_file_status("/file1.py", "error")
        
        assert self.pane.tabs["/file1.py"].status == FileStatus.ERROR
        assert self.pane.tabs["/file1.py"].status.value == "❌"
    
    def test_mark_nonexistent_file_status(self):
        """Test marking status on nonexistent file (should not error)."""
        # Should not raise
        self.pane.mark_file_status("/nonexistent.py", "saved")
    
    def test_get_active_file(self):
        """Test getting active file content."""
        self.pane.add_file_tab("/file1.py", "content1")
        
        filepath, content = self.pane.get_active_file()
        
        assert filepath == "/file1.py"
        assert content == "content1"
    
    def test_get_active_file_no_file(self):
        """Test getting active file when none selected."""
        result = self.pane.get_active_file()
        assert result is None
    
    def test_get_active_file_multiple_tabs(self):
        """Test getting active file among multiple tabs."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.add_file_tab("/file2.py", "content2")
        
        filepath, content = self.pane.get_active_file()
        assert filepath == "/file1.py"
        assert content == "content1"
    
    def test_next_tab_navigation(self):
        """Test navigating to next tab."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.add_file_tab("/file2.py", "content2")
        self.pane.add_file_tab("/file3.py", "content3")
        
        assert self.pane.active_tab == "/file1.py"
        
        self.pane.action_next_tab()
        assert self.pane.active_tab == "/file2.py"
        
        self.pane.action_next_tab()
        assert self.pane.active_tab == "/file3.py"
    
    def test_next_tab_wraps_around(self):
        """Test next tab wraps to beginning."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.add_file_tab("/file2.py", "content2")
        
        self.pane.action_next_tab()
        self.pane.action_next_tab()
        
        # Should wrap back to first
        assert self.pane.active_tab == "/file1.py"
    
    def test_prev_tab_navigation(self):
        """Test navigating to previous tab."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.add_file_tab("/file2.py", "content2")
        self.pane.add_file_tab("/file3.py", "content3")
        
        self.pane.action_next_tab()
        self.pane.action_next_tab()
        assert self.pane.active_tab == "/file3.py"
        
        self.pane.action_prev_tab()
        assert self.pane.active_tab == "/file2.py"
    
    def test_prev_tab_wraps_around(self):
        """Test previous tab wraps to end."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.add_file_tab("/file2.py", "content2")
        
        self.pane.action_prev_tab()
        
        # Should wrap to last
        assert self.pane.active_tab == "/file2.py"
    
    def test_save_all_files(self, tmp_path):
        """Test saving all files to disk."""
        file1 = tmp_path / "test1.py"
        file2 = tmp_path / "test2.js"
        
        self.pane.add_file_tab(str(file1), "content1")
        self.pane.add_file_tab(str(file2), "content2")
        
        results = self.pane.save_all_files()
        
        assert results[str(file1)] is True
        assert results[str(file2)] is True
        
        assert file1.read_text() == "content1"
        assert file2.read_text() == "content2"
    
    def test_save_all_files_creates_directories(self, tmp_path):
        """Test save creates necessary directories."""
        file_path = tmp_path / "subdir" / "nested" / "file.py"
        
        self.pane.add_file_tab(str(file_path), "content")
        results = self.pane.save_all_files()
        
        assert results[str(file_path)] is True
        assert file_path.exists()
        assert file_path.read_text() == "content"
    
    def test_save_updates_file_status(self, tmp_path):
        """Test save updates file status to saved."""
        file_path = tmp_path / "test.py"
        
        self.pane.add_file_tab(str(file_path), "content", "new")
        self.pane.save_all_files()
        
        assert self.pane.tabs[str(file_path)].status == FileStatus.SAVED
    
    def test_save_handles_permission_error(self, tmp_path):
        """Test save handles permission errors gracefully."""
        # Use a path with invalid characters or no permission
        file_path = "/proc/test_file_should_not_exist_12345.py"
        
        self.pane.add_file_tab(file_path, "content")
        results = self.pane.save_all_files()
        
        assert results[file_path] is False
        assert self.pane.tabs[file_path].status == FileStatus.ERROR
    
    def test_tab_order_preserved(self):
        """Test that tab order is preserved during operations."""
        for i in range(5):
            self.pane.add_file_tab(f"/file{i}.py", f"content{i}")
        
        tab_list = list(self.pane.tabs.keys())
        
        # Verify order
        for i, filepath in enumerate(tab_list):
            assert filepath == f"/file{i}.py"


class TestFileContentViewer:
    """Test FileContentViewer rendering and navigation."""
    
    def test_content_viewer_creation(self):
        """Test creating a content viewer."""
        tab = FileTab(filepath="/test.py", content="line1\nline2\nline3")
        viewer = FileContentViewer(tab)
        
        assert viewer.file_tab == tab
        assert viewer.cursor_line == 0
        assert viewer.scroll_offset == 0
    
    def test_cursor_down_movement(self):
        """Test cursor down movement."""
        tab = FileTab(filepath="/test.py", content="line1\nline2\nline3")
        viewer = FileContentViewer(tab)
        
        viewer.action_cursor_down()
        assert viewer.cursor_line == 1
        
        viewer.action_cursor_down()
        assert viewer.cursor_line == 2
    
    def test_cursor_up_movement(self):
        """Test cursor up movement."""
        tab = FileTab(filepath="/test.py", content="line1\nline2\nline3")
        viewer = FileContentViewer(tab)
        viewer.cursor_line = 2
        
        viewer.action_cursor_up()
        assert viewer.cursor_line == 1
        
        viewer.action_cursor_up()
        assert viewer.cursor_line == 0
    
    def test_cursor_bounds(self):
        """Test cursor stays within bounds."""
        tab = FileTab(filepath="/test.py", content="line1\nline2")
        viewer = FileContentViewer(tab)
        
        # Try to go above beginning
        viewer.action_cursor_up()
        assert viewer.cursor_line == 0
        
        # Try to go below end
        viewer.cursor_line = 1
        viewer.action_cursor_down()
        assert viewer.cursor_line == 1
    
    def test_page_down_movement(self):
        """Test page down scrolling."""
        lines = "\n".join([f"line{i}" for i in range(50)])
        tab = FileTab(filepath="/test.py", content=lines)
        viewer = FileContentViewer(tab)
        viewer.page_size = 10
        
        viewer.action_page_down()
        assert viewer.cursor_line == 10
    
    def test_page_up_movement(self):
        """Test page up scrolling."""
        lines = "\n".join([f"line{i}" for i in range(50)])
        tab = FileTab(filepath="/test.py", content=lines)
        viewer = FileContentViewer(tab)
        viewer.cursor_line = 20
        viewer.page_size = 10
        
        viewer.action_page_up()
        assert viewer.cursor_line == 10
    
    def test_goto_line(self):
        """Test jumping to specific line."""
        lines = "\n".join([f"line{i}" for i in range(50)])
        tab = FileTab(filepath="/test.py", content=lines)
        viewer = FileContentViewer(tab)
        
        viewer.action_goto_line(25)
        assert viewer.cursor_line == 24  # 1-indexed input, 0-indexed storage
    
    def test_goto_line_bounds(self):
        """Test goto line respects bounds."""
        lines = "\n".join([f"line{i}" for i in range(10)])
        tab = FileTab(filepath="/test.py", content=lines)
        viewer = FileContentViewer(tab)
        
        viewer.action_goto_line(100)  # Beyond end
        assert viewer.cursor_line == 9
        
        viewer.action_goto_line(0)  # Before start
        assert viewer.cursor_line == 0
    
    def test_ensure_cursor_visible(self):
        """Test scroll offset adjusts to keep cursor visible."""
        lines = "\n".join([f"line{i}" for i in range(50)])
        tab = FileTab(filepath="/test.py", content=lines)
        viewer = FileContentViewer(tab)
        viewer.page_size = 10
        
        # Cursor above viewport
        viewer.cursor_line = 0
        viewer._ensure_cursor_visible()
        assert viewer.scroll_offset == 0
        
        # Cursor below viewport
        viewer.cursor_line = 20
        viewer._ensure_cursor_visible()
        assert viewer.scroll_offset > 0
        assert viewer.cursor_line >= viewer.scroll_offset


class TestStatusMessages:
    """Test status message indicators."""
    
    def test_status_enum_values(self):
        """Test FileStatus enum has correct values."""
        assert FileStatus.NEW.value == "🆕"
        assert FileStatus.MODIFIED.value == "⚡"
        assert FileStatus.SAVED.value == "💾"
        assert FileStatus.SAVING.value == "⏳"
        assert FileStatus.ERROR.value == "❌"
    
    def test_status_enum_members(self):
        """Test FileStatus has all expected members."""
        members = FileStatus.__members__
        assert "NEW" in members
        assert "MODIFIED" in members
        assert "SAVED" in members
        assert "SAVING" in members
        assert "ERROR" in members


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



class TestFileTab:
    """Test FileTab data class."""
    
    def test_file_tab_creation(self):
        """Test creating a file tab."""
        tab = FileTab(
            filepath="/path/to/file.py",
            content="print('hello')",
            status=FileStatus.NEW,
        )
        
        assert tab.filepath == "/path/to/file.py"
        assert tab.content == "print('hello')"
        assert tab.status == FileStatus.NEW
    
    def test_language_detection_python(self):
        """Test language detection for Python files."""
        tab = FileTab(filepath="/test.py", content="")
        assert tab.get_language() == "python"
    
    def test_language_detection_javascript(self):
        """Test language detection for JavaScript files."""
        tab = FileTab(filepath="/test.js", content="")
        assert tab.get_language() == "javascript"
    
    def test_language_detection_yaml(self):
        """Test language detection for YAML files."""
        tab = FileTab(filepath="/test.yaml", content="")
        assert tab.get_language() == "yaml"
    
    def test_language_detection_unknown(self):
        """Test language detection for unknown files."""
        tab = FileTab(filepath="/test.unknown", content="")
        assert tab.get_language() is None
    
    def test_explicit_language_override(self):
        """Test explicit language parameter."""
        tab = FileTab(filepath="/test.py", content="", language="rust")
        assert tab.get_language() == "rust"


class TestTabbedEditorPane:
    """Test TabbedEditorPane main functionality."""
    
    def setup_method(self):
        """Create a fresh pane for each test."""
        self.pane = TabbedEditorPane()
    
    def test_initialization(self):
        """Test pane initializes empty."""
        assert len(self.pane.tabs) == 0
        assert self.pane.active_tab is None
    
    def test_add_single_file_tab(self):
        """Test adding a single file tab."""
        self.pane.add_file_tab(
            filepath="/test/file.py",
            content="print('hello')",
            status="new"
        )
        
        assert len(self.pane.tabs) == 1
        assert "/test/file.py" in self.pane.tabs
        assert self.pane.active_tab == "/test/file.py"
        assert self.pane.tabs["/test/file.py"].status == FileStatus.NEW
    
    def test_add_multiple_file_tabs(self):
        """Test adding multiple file tabs."""
        self.pane.add_file_tab("/test1.py", "content1", "new")
        self.pane.add_file_tab("/test2.js", "content2", "modified")
        self.pane.add_file_tab("/test3.yaml", "content3", "saved")
        
        assert len(self.pane.tabs) == 3
        assert self.pane.active_tab == "/test1.py"  # First tab is active
    
    def test_add_tab_maintains_active_tab(self):
        """Test that adding new tabs doesn't change active tab."""
        self.pane.add_file_tab("/file1.py", "content1")
        active_1 = self.pane.active_tab
        
        self.pane.add_file_tab("/file2.py", "content2")
        active_2 = self.pane.active_tab
        
        assert active_1 == active_2
        assert active_1 == "/file1.py"
    
    def test_remove_file_tab(self):
        """Test removing a file tab."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.add_file_tab("/file2.py", "content2")
        
        self.pane.remove_file_tab("/file1.py")
        
        assert len(self.pane.tabs) == 1
        assert "/file1.py" not in self.pane.tabs
    
    def test_remove_active_tab_switches_to_other(self):
        """Test that removing active tab switches to another tab."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.add_file_tab("/file2.py", "content2")
        
        assert self.pane.active_tab == "/file1.py"
        
        self.pane.remove_file_tab("/file1.py")
        
        assert self.pane.active_tab == "/file2.py"
    
    def test_remove_last_tab(self):
        """Test removing the last tab."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.remove_file_tab("/file1.py")
        
        assert len(self.pane.tabs) == 0
        assert self.pane.active_tab is None
    
    def test_remove_nonexistent_tab(self):
        """Test removing a tab that doesn't exist."""
        self.pane.add_file_tab("/file1.py", "content1")
        
        # Should not raise
        self.pane.remove_file_tab("/file2.py")
        
        assert len(self.pane.tabs) == 1
    
    def test_mark_file_status_new(self):
        """Test marking file as new."""
        self.pane.add_file_tab("/file1.py", "content1", "saved")
        self.pane.mark_file_status("/file1.py", "new")
        
        assert self.pane.tabs["/file1.py"].status == FileStatus.NEW
        assert self.pane.tabs["/file1.py"].status.value == "🆕"
    
    def test_mark_file_status_modified(self):
        """Test marking file as modified."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.mark_file_status("/file1.py", "modified")
        
        assert self.pane.tabs["/file1.py"].status == FileStatus.MODIFIED
        assert self.pane.tabs["/file1.py"].status.value == "⚡"
    
    def test_mark_file_status_saved(self):
        """Test marking file as saved."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.mark_file_status("/file1.py", "saved")
        
        assert self.pane.tabs["/file1.py"].status == FileStatus.SAVED
        assert self.pane.tabs["/file1.py"].status.value == "💾"
    
    def test_mark_file_status_saving(self):
        """Test marking file as saving."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.mark_file_status("/file1.py", "saving")
        
        assert self.pane.tabs["/file1.py"].status == FileStatus.SAVING
        assert self.pane.tabs["/file1.py"].status.value == "⏳"
    
    def test_mark_file_status_error(self):
        """Test marking file with error status."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.mark_file_status("/file1.py", "error")
        
        assert self.pane.tabs["/file1.py"].status == FileStatus.ERROR
        assert self.pane.tabs["/file1.py"].status.value == "❌"
    
    def test_mark_nonexistent_file_status(self):
        """Test marking status on nonexistent file (should not error)."""
        # Should not raise
        self.pane.mark_file_status("/nonexistent.py", "saved")
    
    def test_get_active_file(self):
        """Test getting active file content."""
        self.pane.add_file_tab("/file1.py", "content1")
        
        filepath, content = self.pane.get_active_file()
        
        assert filepath == "/file1.py"
        assert content == "content1"
    
    def test_get_active_file_no_file(self):
        """Test getting active file when none selected."""
        result = self.pane.get_active_file()
        assert result is None
    
    def test_get_active_file_multiple_tabs(self):
        """Test getting active file among multiple tabs."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.add_file_tab("/file2.py", "content2")
        
        filepath, content = self.pane.get_active_file()
        assert filepath == "/file1.py"
        assert content == "content1"
    
    def test_next_tab_navigation(self):
        """Test navigating to next tab."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.add_file_tab("/file2.py", "content2")
        self.pane.add_file_tab("/file3.py", "content3")
        
        assert self.pane.active_tab == "/file1.py"
        
        self.pane.action_next_tab()
        assert self.pane.active_tab == "/file2.py"
        
        self.pane.action_next_tab()
        assert self.pane.active_tab == "/file3.py"
    
    def test_next_tab_wraps_around(self):
        """Test next tab wraps to beginning."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.add_file_tab("/file2.py", "content2")
        
        self.pane.action_next_tab()
        self.pane.action_next_tab()
        
        # Should wrap back to first
        assert self.pane.active_tab == "/file1.py"
    
    def test_prev_tab_navigation(self):
        """Test navigating to previous tab."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.add_file_tab("/file2.py", "content2")
        self.pane.add_file_tab("/file3.py", "content3")
        
        self.pane.action_next_tab()
        self.pane.action_next_tab()
        assert self.pane.active_tab == "/file3.py"
        
        self.pane.action_prev_tab()
        assert self.pane.active_tab == "/file2.py"
    
    def test_prev_tab_wraps_around(self):
        """Test previous tab wraps to end."""
        self.pane.add_file_tab("/file1.py", "content1")
        self.pane.add_file_tab("/file2.py", "content2")
        
        self.pane.action_prev_tab()
        
        # Should wrap to last
        assert self.pane.active_tab == "/file2.py"
    
    def test_save_all_files(self, tmp_path):
        """Test saving all files to disk."""
        file1 = tmp_path / "test1.py"
        file2 = tmp_path / "test2.js"
        
        self.pane.add_file_tab(str(file1), "content1")
        self.pane.add_file_tab(str(file2), "content2")
        
        results = self.pane.save_all_files()
        
        assert results[str(file1)] is True
        assert results[str(file2)] is True
        
        assert file1.read_text() == "content1"
        assert file2.read_text() == "content2"
    
    def test_save_all_files_creates_directories(self, tmp_path):
        """Test save creates necessary directories."""
        file_path = tmp_path / "subdir" / "nested" / "file.py"
        
        self.pane.add_file_tab(str(file_path), "content")
        results = self.pane.save_all_files()
        
        assert results[str(file_path)] is True
        assert file_path.exists()
        assert file_path.read_text() == "content"
    
    def test_save_updates_file_status(self, tmp_path):
        """Test save updates file status to saved."""
        file_path = tmp_path / "test.py"
        
        self.pane.add_file_tab(str(file_path), "content", "new")
        self.pane.save_all_files()
        
        assert self.pane.tabs[str(file_path)].status == FileStatus.SAVED
    
    def test_save_handles_permission_error(self, tmp_path):
        """Test save handles permission errors gracefully."""
        # Use a path with invalid characters or no permission
        file_path = "/proc/test.py"  # Typically no write permission
        
        self.pane.add_file_tab(file_path, "content")
        results = self.pane.save_all_files()
        
        assert results[file_path] is False
        assert self.pane.tabs[file_path].status == FileStatus.ERROR
    
    def test_tab_order_preserved(self):
        """Test that tab order is preserved during operations."""
        for i in range(5):
            self.pane.add_file_tab(f"/file{i}.py", f"content{i}")
        
        tab_list = list(self.pane.tabs.keys())
        
        # Verify order
        for i, filepath in enumerate(tab_list):
            assert filepath == f"/file{i}.py"


class TestFileContentViewer:
    """Test FileContentViewer rendering and navigation."""
    
    def test_content_viewer_creation(self):
        """Test creating a content viewer."""
        tab = FileTab(filepath="/test.py", content="line1\nline2\nline3")
        viewer = FileContentViewer(tab)
        
        assert viewer.file_tab == tab
        assert viewer.cursor_line == 0
        assert viewer.scroll_offset == 0
    
    def test_cursor_down_movement(self):
        """Test cursor down movement."""
        tab = FileTab(filepath="/test.py", content="line1\nline2\nline3")
        viewer = FileContentViewer(tab)
        
        viewer.action_cursor_down()
        assert viewer.cursor_line == 1
        
        viewer.action_cursor_down()
        assert viewer.cursor_line == 2
    
    def test_cursor_up_movement(self):
        """Test cursor up movement."""
        tab = FileTab(filepath="/test.py", content="line1\nline2\nline3")
        viewer = FileContentViewer(tab)
        viewer.cursor_line = 2
        
        viewer.action_cursor_up()
        assert viewer.cursor_line == 1
        
        viewer.action_cursor_up()
        assert viewer.cursor_line == 0
    
    def test_cursor_bounds(self):
        """Test cursor stays within bounds."""
        tab = FileTab(filepath="/test.py", content="line1\nline2")
        viewer = FileContentViewer(tab)
        
        # Try to go above beginning
        viewer.action_cursor_up()
        assert viewer.cursor_line == 0
        
        # Try to go below end
        viewer.cursor_line = 1
        viewer.action_cursor_down()
        assert viewer.cursor_line == 1
    
    def test_page_down_movement(self):
        """Test page down scrolling."""
        lines = "\n".join([f"line{i}" for i in range(50)])
        tab = FileTab(filepath="/test.py", content=lines)
        viewer = FileContentViewer(tab)
        viewer.page_size = 10
        
        viewer.action_page_down()
        assert viewer.cursor_line == 10
    
    def test_page_up_movement(self):
        """Test page up scrolling."""
        lines = "\n".join([f"line{i}" for i in range(50)])
        tab = FileTab(filepath="/test.py", content=lines)
        viewer = FileContentViewer(tab)
        viewer.cursor_line = 20
        viewer.page_size = 10
        
        viewer.action_page_up()
        assert viewer.cursor_line == 10
    
    def test_goto_line(self):
        """Test jumping to specific line."""
        lines = "\n".join([f"line{i}" for i in range(50)])
        tab = FileTab(filepath="/test.py", content=lines)
        viewer = FileContentViewer(tab)
        
        viewer.action_goto_line(25)
        assert viewer.cursor_line == 24  # 1-indexed input, 0-indexed storage
    
    def test_goto_line_bounds(self):
        """Test goto line respects bounds."""
        lines = "\n".join([f"line{i}" for i in range(10)])
        tab = FileTab(filepath="/test.py", content=lines)
        viewer = FileContentViewer(tab)
        
        viewer.action_goto_line(100)  # Beyond end
        assert viewer.cursor_line == 9
        
        viewer.action_goto_line(0)  # Before start
        assert viewer.cursor_line == 0
    
    def test_ensure_cursor_visible(self):
        """Test scroll offset adjusts to keep cursor visible."""
        lines = "\n".join([f"line{i}" for i in range(50)])
        tab = FileTab(filepath="/test.py", content=lines)
        viewer = FileContentViewer(tab)
        viewer.page_size = 10
        
        # Cursor above viewport
        viewer.cursor_line = 0
        viewer._ensure_cursor_visible()
        assert viewer.scroll_offset == 0
        
        # Cursor below viewport
        viewer.cursor_line = 20
        viewer._ensure_cursor_visible()
        assert viewer.scroll_offset > 0
        assert viewer.cursor_line >= viewer.scroll_offset


class TestStatusMessages:
    """Test status message indicators."""
    
    def test_status_enum_values(self):
        """Test FileStatus enum has correct values."""
        assert FileStatus.NEW.value == "🆕"
        assert FileStatus.MODIFIED.value == "⚡"
        assert FileStatus.SAVED.value == "💾"
        assert FileStatus.SAVING.value == "⏳"
        assert FileStatus.ERROR.value == "❌"
    
    def test_status_enum_members(self):
        """Test FileStatus has all expected members."""
        members = FileStatus.__members__
        assert "NEW" in members
        assert "MODIFIED" in members
        assert "SAVED" in members
        assert "SAVING" in members
        assert "ERROR" in members


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

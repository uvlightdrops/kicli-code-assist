"""File editor tab widget."""

from pathlib import Path
from textual.containers import Vertical, Horizontal
from textual.widgets import TextArea, Static, Button
from textual.app import ComposeResult


class EditTab(Vertical):
    """Editor tab for file editing with save/close controls."""
    
    DEFAULT_CSS = """
    EditTab {
        border: solid $primary;
        background: $surface;
        height: 100%;
        width: 100%;
    }
    
    EditTab > #editor_controls {
        height: auto;
        dock: top;
    }
    
    EditTab > #status_line {
        height: 1;
        dock: bottom;
        background: $boost;
    }
    
    EditTab > TextArea {
        height: 1fr;
        width: 1fr;
    }
    
    EditTab Button {
        margin: 0 1;
        height: 1;
    }
    """
    
    def __init__(self, file_path: Path, content: str = ""):
        super().__init__(id=f"edit_tab_{file_path.name}")
        self.file_path = file_path
        self.original_content = content
        self.is_modified = False
        self.text_area = None
        self.status_line = None
    
    def compose(self) -> ComposeResult:
        """Compose the editor tab."""
        # Control buttons
        with Horizontal(id="editor_controls"):
            yield Button("💾 Save", id="btn_save_file", variant="primary")
            yield Button("✕ Close", id="btn_close_file", variant="warning")
        
        # Main text editor
        self.text_area = TextArea(
            text=self.original_content,
            id=f"text_area_{self.file_path.name}",
            language=self._detect_language()
        )
        yield self.text_area
        
        # Status line
        self.status_line = Static(
            f"{self.file_path.name} | Line 1:1",
            id="status_line"
        )
        yield self.status_line
    
    def on_mount(self) -> None:
        """Setup after mount."""
        if self.text_area:
            self.text_area.focus()
            # Track changes
            self.text_area.changed_signal.connect(self._on_text_changed)
    
    def _detect_language(self) -> str:
        """Detect language by file extension."""
        ext = self.file_path.suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".md": "markdown",
            ".sh": "bash",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".json": "json",
            ".toml": "toml",
            ".html": "html",
            ".css": "css",
            ".go": "go",
            ".rs": "rust",
            ".c": "c",
            ".cpp": "cpp",
        }
        return language_map.get(ext, "text")
    
    def _on_text_changed(self) -> None:
        """Handle text change."""
        if self.text_area:
            current = self.text_area.text
            if current != self.original_content:
                if not self.is_modified:
                    self.is_modified = True
                    self._update_tab_title()
            else:
                if self.is_modified:
                    self.is_modified = False
                    self._update_tab_title()
            
            # Update status line with cursor position
            if self.status_line:
                cursor_row, cursor_col = self.text_area.cursor_location
                self.status_line.update(
                    f"{self.file_path.name} {'[modified]' if self.is_modified else ''} "
                    f"| Line {cursor_row + 1}:{cursor_col + 1}"
                )
    
    def _update_tab_title(self) -> None:
        """Update the tab title to reflect modification state."""
        # This will be called by parent TabbedContent
        pass
    
    def get_content(self) -> str:
        """Get current editor content."""
        return self.text_area.text if self.text_area else ""
    
    def save_to_disk(self) -> bool:
        """Save file to disk.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            content = self.get_content()
            self.file_path.write_text(content)
            self.original_content = content
            self.is_modified = False
            self._update_tab_title()
            return True
        except Exception as e:
            # Error would be shown to user elsewhere
            print(f"Error saving {self.file_path}: {e}")
            return False
    
    def has_unsaved_changes(self) -> bool:
        """Check if file has unsaved changes."""
        return self.is_modified

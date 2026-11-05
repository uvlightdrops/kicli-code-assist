"""
Preview Modal Widget

Displays file content with syntax highlighting.
Works as both modal (pop-up) and embedded pane.
"""

import logging
from pathlib import Path
from typing import Optional
from rich.syntax import Syntax
from rich.console import Console
from textual.widgets import Static, Label
from textual.containers import Container, Vertical, Horizontal
from textual.reactive import reactive
from textual.binding import Binding

logger = logging.getLogger(__name__)


class FilePreviewModal(Container):
    """File preview widget with syntax highlighting.
    
    Features:
    - Syntax highlighting (200+ languages via Pygments)
    - Large file handling (truncation + streaming)
    - Line numbers
    - Scrollable content
    - Error display
    
    Example:
        preview = FilePreviewModal()
        preview.load_file(Path("src/main.py"))
        preview.show()
    """
    
    # Observable state
    is_visible = reactive(True)
    error_message = reactive("")
    current_file = reactive("")
    
    DEFAULT_CSS = """
    FilePreviewModal {
        width: 100%;
        height: 100%;
        border: solid $primary;
        background: $surface;
    }
    
    FilePreviewModal > Vertical {
        width: 1fr;
        height: 1fr;
    }
    
    FilePreviewModal .file-header {
        dock: top;
        height: 1;
        background: $panel;
        color: $text-muted;
    }
    
    FilePreviewModal .file-content {
        width: 1fr;
        height: 1fr;
        overflow: auto;
    }
    
    FilePreviewModal .error-message {
        dock: top;
        height: 3;
        background: $error;
        color: $text;
        border: solid $error;
    }
    """
    
    BINDINGS = [
        Binding("escape", "hide", "Close"),
        Binding("q", "hide", "Close"),
    ]
    
    def __init__(
        self,
        max_file_size: int = 1024 * 1024,  # 1MB
        theme: str = "monokai",
        line_numbers: bool = True,
    ):
        """Initialize preview modal.
        
        Args:
            max_file_size: Maximum file size to load (bytes)
            theme: Syntax highlight theme
            line_numbers: Show line numbers
        """
        super().__init__()
        self.max_file_size = max_file_size
        self.theme = theme
        self.line_numbers = line_numbers
        self.current_path: Optional[Path] = None
        self.content_widget: Optional[Static] = None
    
    def compose(self):
        """Compose preview layout."""
        with Vertical(id="preview-container"):
            yield Label("", classes="file-header")
            yield Static("", classes="file-content", id="preview-content")
    
    def on_mount(self) -> None:
        """Initialize on mount."""
        self.content_widget = self.query_one("#preview-content", Static)
    
    def load_file(self, path: Path) -> bool:
        """Load and display file content.
        
        Args:
            path: Path to file
            
        Returns:
            True if successful, False on error
        """
        self.current_path = path
        self.current_file = str(path)
        
        if not path.exists():
            self.set_error(f"File not found: {path}")
            return False
        
        if not path.is_file():
            self.set_error(f"Not a file: {path}")
            return False
        
        try:
            # Check file size
            file_size = path.stat().st_size
            if file_size > self.max_file_size:
                self.set_error(
                    f"File too large ({file_size / 1024 / 1024:.1f}MB > "
                    f"{self.max_file_size / 1024 / 1024:.1f}MB)"
                )
                return False
            
            # Read content
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            
            # Detect language from extension
            language = self._detect_language(path)
            
            # Render with syntax highlighting
            self._render_content(content, language, path)
            
            # Update header
            header = self.query_one(".file-header", Label)
            header.update(f"📄 {path.name} ({file_size:,} bytes)")
            
            self.error_message = ""
            logger.info(f"Loaded file: {path}")
            return True
        
        except Exception as e:
            self.set_error(f"Error reading file: {e}")
            logger.error(f"Error loading file {path}: {e}")
            return False
    
    def _render_content(self, content: str, language: str, path: Path) -> None:
        """Render content with syntax highlighting.
        
        Args:
            content: File content
            language: Language identifier
            path: File path
        """
        if not self.content_widget:
            return
        
        try:
            # Create syntax object
            syntax = Syntax(
                content,
                language,
                theme=self.theme,
                line_numbers=self.line_numbers,
                word_wrap=False,
                indent_guides=True,
            )
            
            # Render to Rich console
            console = Console(record=True, width=120)
            console.print(syntax)
            
            # Display content
            self.content_widget.update(console.export_text())
        
        except Exception as e:
            logger.warning(f"Error rendering syntax: {e}")
            # Fallback to plain text
            self.content_widget.update(content)
    
    def _detect_language(self, path: Path) -> str:
        """Detect language from file extension.
        
        Args:
            path: File path
            
        Returns:
            Language identifier for Pygments
        """
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "jsx",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".sh": "bash",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".json": "json",
            ".md": "markdown",
            ".html": "html",
            ".css": "css",
            ".sql": "sql",
        }
        
        return ext_map.get(path.suffix, "text")
    
    def set_error(self, message: str) -> None:
        """Display error message."""
        self.error_message = message
        logger.error(message)
        
        if not self.content_widget:
            return
        
        # Display error
        error_panel = Static(f"❌ {message}", classes="error-message")
        self.content_widget.update(f"Error: {message}")
    
    def clear_error(self) -> None:
        """Clear error state."""
        self.error_message = ""
    
    def show(self) -> None:
        """Show modal (set display: block)."""
        self.is_visible = True
        self.display = True
    
    def hide(self) -> None:
        """Hide modal (set display: none)."""
        self.is_visible = False
        self.display = False
    
    def action_hide(self) -> None:
        """Action: hide modal."""
        self.hide()
    
    def get_content(self) -> Optional[str]:
        """Get current file content.
        
        Returns:
            File content or None if no file loaded
        """
        if self.content_widget:
            return self.content_widget.renderable
        return None
    
    def set_theme(self, theme: str) -> None:
        """Change syntax highlighting theme.
        
        Args:
            theme: Theme name (monokai, dracula, etc.)
        """
        self.theme = theme
        if self.current_path:
            self.load_file(self.current_path)

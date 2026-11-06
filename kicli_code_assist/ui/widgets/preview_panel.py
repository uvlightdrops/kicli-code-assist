"""Preview Panel - Display file content with syntax highlighting.

Lightweight panel for previewing selected files from the file browser.
Shows code with syntax highlighting, handles various file types.
"""

from pathlib import Path
from typing import Optional

from textual.containers import Container
from textual.widgets import Static, RichLog
from textual.reactive import reactive
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text


class PreviewPanel(Container):
    """File preview panel.
    
    Displays content of selected file with syntax highlighting.
    Handles:
    - Python, JavaScript, YAML, JSON, Markdown, and more
    - Large files (with truncation)
    - Binary file detection
    - Error handling
    """
    
    CSS = """
    PreviewPanel {
        width: 1fr;
        height: 1fr;
        border: solid $primary;
        layout: vertical;
    }
    
    PreviewPanel > Static#preview-header {
        height: 1;
        background: $panel;
        color: $text-muted;
        border-bottom: solid $border;
        content-align: left middle;
    }
    
    PreviewPanel > RichLog#preview-content {
        width: 1fr;
        height: 1fr;
        border: none;
    }
    """
    
    current_file = reactive("")
    file_size = reactive(0)
    
    def __init__(self):
        """Initialize preview panel."""
        super().__init__()
        self.current_path: Optional[Path] = None
        self.max_file_size = 1024 * 1024  # 1MB limit for display
    
    def compose(self):
        """Compose panel widgets."""
        yield Static("No file selected", id="preview-header")
        yield RichLog(markup=True, id="preview-content")
    
    def preview_file(self, file_path: str) -> None:
        """Preview a file.
        
        Args:
            file_path: Path to file to preview
        """
        path = Path(file_path)
        
        if not path.exists():
            self._show_error(f"File not found: {file_path}")
            return
        
        if not path.is_file():
            self._show_error(f"Not a file: {file_path}")
            return
        
        try:
            # Get file info
            file_size = path.stat().st_size
            self.file_size = file_size
            self.current_path = path
            self.current_file = path.name
            
            # Update header
            header = self.query_one("#preview-header", Static)
            rel_path = self._get_relative_path(path)
            size_str = self._format_size(file_size)
            header.update(f"📄 {rel_path}  ({size_str})")
            
            # Read and display file
            if file_size > self.max_file_size:
                self._show_truncated(path)
            else:
                self._show_file(path)
        
        except Exception as e:
            self._show_error(f"Error reading file: {str(e)}")
    
    def _show_file(self, path: Path) -> None:
        """Display file content with syntax highlighting."""
        content = self.query_one("#preview-content", RichLog)
        content.clear()
        
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            
            # Syntax highlighting based on extension
            lexer_name = self._get_lexer(path.suffix)
            
            if lexer_name:
                try:
                    syntax = Syntax(
                        text,
                        lexer_name,
                        theme="monokai",
                        line_numbers=True,
                        word_wrap=False,
                        background_color="default",
                    )
                    content.write(syntax)
                except Exception:
                    # Fallback: plain text if syntax highlighting fails
                    content.write(text)
            else:
                content.write(text)
        
        except UnicodeDecodeError:
            self._show_binary(path)
        except Exception as e:
            self._show_error(f"Error displaying file: {str(e)}")
    
    def _show_truncated(self, path: Path) -> None:
        """Show truncated file (for large files)."""
        content = self.query_one("#preview-content", RichLog)
        content.clear()
        
        try:
            # Read first chunk
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read(self.max_file_size)
            
            lexer_name = self._get_lexer(path.suffix)
            
            if lexer_name:
                try:
                    syntax = Syntax(
                        text,
                        lexer_name,
                        theme="monokai",
                        line_numbers=True,
                        word_wrap=False,
                        background_color="default",
                    )
                    content.write(syntax)
                except Exception:
                    content.write(text)
            else:
                content.write(text)
            
            # Add truncation notice
            notice = Text("\n\n[TRUNCATED] File is too large to display fully", style="yellow")
            content.write(notice)
        
        except Exception as e:
            self._show_error(f"Error displaying truncated file: {str(e)}")
    
    def _show_binary(self, path: Path) -> None:
        """Show message for binary files."""
        content = self.query_one("#preview-content", RichLog)
        content.clear()
        
        msg = Text(
            f"📦 Binary file: {path.name}\n\n"
            f"Cannot preview binary content.\n"
            f"Size: {self._format_size(path.stat().st_size)}",
            style="dim yellow"
        )
        content.write(msg)
    
    def _show_error(self, message: str) -> None:
        """Show error message."""
        content = self.query_one("#preview-content", RichLog)
        content.clear()
        
        msg = Text(message, style="red")
        content.write(msg)
    
    def _get_lexer(self, suffix: str) -> Optional[str]:
        """Map file extension to Pygments lexer name."""
        lexer_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "jsx",
            ".tsx": "typescript",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".sh": "bash",
            ".bash": "bash",
            ".zsh": "bash",
            ".fish": "fish",
            ".sql": "sql",
            ".html": "html",
            ".htm": "html",
            ".css": "css",
            ".scss": "scss",
            ".sass": "sass",
            ".less": "less",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".xml": "xml",
            ".toml": "toml",
            ".ini": "ini",
            ".cfg": "ini",
            ".conf": "conf",
            ".md": "markdown",
            ".rst": "rst",
            ".tex": "latex",
        }
        return lexer_map.get(suffix.lower())
    
    def _get_relative_path(self, path: Path) -> str:
        """Get relative path from current working directory."""
        try:
            return str(path.relative_to(Path.cwd()))
        except ValueError:
            return str(path)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}TB"
    
    def clear(self) -> None:
        """Clear preview panel."""
        content = self.query_one("#preview-content", RichLog)
        content.clear()
        
        header = self.query_one("#preview-header", Static)
        header.update("No file selected")
        
        self.current_file = ""
        self.current_path = None

"""Diff viewer widget for displaying file changes."""

from pathlib import Path
from textual.widgets import Static, Label
from textual.containers import Container, Vertical, Horizontal
from rich.text import Text
from rich.panel import Panel
import difflib


class DiffPane(Static):
    """Diff viewer with line-by-line display and approval controls."""
    
    DEFAULT_CSS = """
    DiffPane {
        height: 1fr;
        width: 1fr;
    }
    
    DiffPane .diff-header {
        text-style: bold;
        width: 1fr;
        height: auto;
        background: $boost;
    }
    
    DiffPane .diff-added {
        color: $success;
        background: $success 20%;
    }
    
    DiffPane .diff-removed {
        color: $error;
        background: $error 20%;
    }
    
    DiffPane .diff-modified {
        color: $warning;
        background: $warning 20%;
    }
    
    DiffPane .diff-context {
        color: $text;
    }
    
    DiffPane .diff-stats {
        text-style: dim;
        margin-top: 1;
    }
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.diffs: dict[str, str] = {}  # {file_path: unified_diff}
        self.selected_changes: set[str] = set()
    
    def set_diff(self, file_path: str, original_content: str, new_content: str) -> None:
        """Set diff for a file.
        
        Args:
            file_path: Path to file
            original_content: Original file content
            new_content: New file content (with changes)
        """
        original_lines = original_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        # Generate unified diff
        diff = list(difflib.unified_diff(
            original_lines,
            new_lines,
            fromfile=file_path,
            tofile=file_path,
            lineterm=''
        ))
        
        self.diffs[file_path] = '\n'.join(diff)
        self._render_diff(file_path)
    
    def set_diffs(self, diffs: dict[str, str]) -> None:
        """Set multiple diffs at once.
        
        Args:
            diffs: {file_path: unified_diff_string}
        """
        self.diffs = diffs
        if diffs:
            first_file = list(diffs.keys())[0]
            self._render_diff(first_file)
    
    def _render_diff(self, file_path: str) -> None:
        """Render diff for a specific file."""
        if file_path not in self.diffs:
            self.update("No diff available")
            return
        
        diff_text = self.diffs[file_path]
        lines = diff_text.split('\n')
        
        # Count statistics
        added_count = sum(1 for l in lines if l.startswith('+') and not l.startswith('+++'))
        removed_count = sum(1 for l in lines if l.startswith('-') and not l.startswith('---'))
        
        # Render with colors
        rendered = [f"📄 {file_path}", "─" * 60]
        
        for line in lines:
            if line.startswith('---') or line.startswith('+++'):
                rendered.append(f"[dim]{line}[/dim]")
            elif line.startswith('-'):
                rendered.append(f"[color(196)]✗ {line[1:]}[/color(196)]")
            elif line.startswith('+'):
                rendered.append(f"[color(46)]✓ {line[1:]}[/color(46)]")
            elif line.startswith('@@'):
                rendered.append(f"[color(33)]{line}[/color(33)]")
            else:
                rendered.append(f"  {line}")
        
        rendered.append(f"[dim]Stats: +{added_count} -{removed_count}[/dim]")
        
        self.update("\n".join(rendered))
    
    def get_all_diffs(self) -> dict[str, str]:
        """Get all diffs."""
        return self.diffs
    
    def clear(self) -> None:
        """Clear all diffs."""
        self.diffs.clear()
        self.selected_changes.clear()
        self.update("")

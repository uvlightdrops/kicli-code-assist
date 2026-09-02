"""File browser component for TUI."""
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FileItem:
    """Represents a file or directory."""
    path: Path
    is_dir: bool
    name: str
    size: int = 0
    
    def display_name(self) -> str:
        """Get display name with directory indicator."""
        if self.is_dir:
            return f"📁 {self.name}/"
        else:
            # Simple file icon based on extension
            ext = self.path.suffix.lower()
            icons = {
                '.py': '🐍',
                '.js': '📜',
                '.ts': '📘',
                '.json': '📋',
                '.yaml': '⚙️',
                '.md': '📄',
                '.txt': '📝',
                '.sh': '🔧',
                '.go': '🔵',
            }
            icon = icons.get(ext, '📄')
            return f"{icon} {self.name}"


class FileBrowser:
    """Browse files and directories in TUI."""
    
    def __init__(self, start_path: str = "."):
        """Initialize file browser.
        
        Args:
            start_path: Starting directory
        """
        self.current_path = Path(start_path).resolve()
        self.items: List[FileItem] = []
        self.selected_index = 0
        self.refresh()
    
    def refresh(self) -> None:
        """Refresh file list for current directory."""
        self.items = []
        
        # Add parent directory link
        if self.current_path.parent != self.current_path:
            self.items.append(FileItem(
                path=self.current_path.parent,
                is_dir=True,
                name=".."
            ))
        
        # Add files and directories
        try:
            entries = sorted(self.current_path.iterdir(), 
                           key=lambda p: (not p.is_dir(), p.name.lower()))
            
            for entry in entries:
                # Skip hidden files/dirs
                if entry.name.startswith('.'):
                    continue
                
                try:
                    size = entry.stat().st_size if entry.is_file() else 0
                    self.items.append(FileItem(
                        path=entry,
                        is_dir=entry.is_dir(),
                        name=entry.name,
                        size=size
                    ))
                except (OSError, PermissionError):
                    pass
        
        except PermissionError:
            pass
        
        # Reset selection if out of bounds
        if self.selected_index >= len(self.items):
            self.selected_index = max(0, len(self.items) - 1)
    
    def get_selected(self) -> Optional[FileItem]:
        """Get currently selected item."""
        if 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None
    
    def select_next(self) -> None:
        """Move selection down."""
        if self.items:
            self.selected_index = (self.selected_index + 1) % len(self.items)
    
    def select_prev(self) -> None:
        """Move selection up."""
        if self.items:
            self.selected_index = (self.selected_index - 1) % len(self.items)
    
    def enter_selected(self) -> bool:
        """Enter selected directory if it's a dir.
        
        Returns:
            True if directory changed, False otherwise
        """
        item = self.get_selected()
        if item and item.is_dir:
            self.current_path = item.path
            self.selected_index = 0
            self.refresh()
            return True
        return False
    
    def get_file_content_preview(self, max_lines: int = 20) -> str:
        """Get preview of selected file.
        
        Args:
            max_lines: Maximum lines to show
        
        Returns:
            File content preview
        """
        item = self.get_selected()
        if not item or item.is_dir:
            return ""
        
        try:
            with open(item.path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[:max_lines]
                return ''.join(lines)
        except:
            return "[Unable to read file]"
    
    def get_tree_view(self, max_items: int = 30) -> str:
        """Get tree view of files.
        
        Args:
            max_items: Maximum items to show
        
        Returns:
            Formatted file tree
        """
        lines = []
        lines.append(f"📂 {self.current_path}")
        lines.append("=" * 50)
        
        for i, item in enumerate(self.items[:max_items]):
            # Highlight selected item
            marker = "→ " if i == self.selected_index else "  "
            size_str = ""
            
            if not item.is_dir:
                size_kb = item.size / 1024
                if size_kb < 1:
                    size_str = f" ({item.size}B)"
                else:
                    size_str = f" ({size_kb:.1f}KB)"
            
            lines.append(f"{marker}{item.display_name()}{size_str}")
        
        if len(self.items) > max_items:
            lines.append(f"  ... and {len(self.items) - max_items} more")
        
        return "\n".join(lines)
    
    def go_home(self) -> None:
        """Go to home directory."""
        self.current_path = Path.home()
        self.selected_index = 0
        self.refresh()
    
    def go_to_path(self, path: str) -> bool:
        """Go to specific path.
        
        Args:
            path: Directory path
        
        Returns:
            True if successful, False otherwise
        """
        try:
            new_path = Path(path).resolve()
            if new_path.is_dir():
                self.current_path = new_path
                self.selected_index = 0
                self.refresh()
                return True
        except:
            pass
        return False

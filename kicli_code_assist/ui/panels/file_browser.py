"""File browser panel."""

from pathlib import Path
from textual.widgets import Static


class SelectableFileList(Static):
    """Navigable file list for current directory."""

    can_focus = True
    
    def __init__(self, parent_app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_app = parent_app
        self.current_dir = self.parent_app.get_allowed_base_path()
        self.entries = []  # (path, is_dir)
        self.selected_index = 0
        self.load_directory()
    
    def _is_in_allowed_root(self, path: Path) -> bool:
        """Return True when path stays within the configured workspace root."""
        return self.parent_app.is_path_allowed(path)
    
    def load_directory(self):
        """Load entries for current directory."""
        allowed_root = self.parent_app.get_allowed_base_path()
        if not self.current_dir or not self._is_in_allowed_root(self.current_dir):
            self.current_dir = allowed_root
        self.entries = []
        try:
            # Add parent directory entry only while still inside the allowed base root.
            parent_dir = self.current_dir.parent
            if self.current_dir != allowed_root and self._is_in_allowed_root(parent_dir):
                self.entries.append((parent_dir, True, ".."))
            
            # Add files and directories
            for item in sorted(self.current_dir.iterdir()):
                if item.name.startswith('.'):
                    continue
                is_dir = item.is_dir()
                icon = "📁" if is_dir else "📄"
                self.entries.append((item, is_dir, f"{icon} {item.name}"))
        except Exception as e:
            self.entries = [(None, False, f"Error: {e}")]
        
        self.selected_index = 0
        self.update_display()
    
    def update_display(self):
        """Update the file list display with coloring for loaded files."""
        lines = []
        for i, (path, is_dir, display) in enumerate(self.entries):
            marker = ">" if i == self.selected_index else " "
            
            # Check if this file is in loaded_files
            is_loaded = False
            if path and not is_dir:
                # Normalize path for comparison
                path_str = str(path.resolve())
                loaded_normalized = [str(Path(f).resolve()) for f in self.parent_app.loaded_files]
                is_loaded = path_str in loaded_normalized
            
            # Color loaded files
            if is_loaded:
                line = f"{marker} [green]{display}[/green] ✓"
            else:
                line = f"{marker} {display}"
            
            lines.append(line)
        
        self.update("\n".join(lines))
    
    def action_cursor_down(self):
        """Move cursor down."""
        if self.selected_index < len(self.entries) - 1:
            self.selected_index += 1
            self.update_display()
            self._update_preview()
    
    def action_cursor_up(self):
        """Move cursor up."""
        if self.selected_index > 0:
            self.selected_index -= 1
            self.update_display()
            self._update_preview()
    
    def action_select_cursor(self):
        """Enter directory or select file."""
        if not self.entries:
            return
        
        path, is_dir, _ = self.entries[self.selected_index]
        if is_dir:
            if path and self.parent_app.is_path_allowed(path):
                self.current_dir = path
                self.load_directory()
            elif path and path.name == "..":
                base_dir = self.parent_app.get_allowed_base_path()
                if self.current_dir != base_dir:
                    self.current_dir = self.current_dir.parent
                    if not self.parent_app.is_path_allowed(self.current_dir):
                        self.current_dir = base_dir
                    self.load_directory()
        else:
            if path and self.parent_app.is_path_allowed(path):
                self.parent_app.update_file_preview(path)
    
    def _update_preview(self):
        """Update preview for current selection."""
        if not self.entries:
            return
        path, is_dir, _ = self.entries[self.selected_index]
        if not is_dir and path and self.parent_app.is_path_allowed(path):
            self.parent_app.update_file_preview(path)
            self.parent_app.selected_file = str(path)
    
    def get_selected_file(self):
        """Get currently selected file."""
        if not self.entries:
            return None
        path, is_dir, _ = self.entries[self.selected_index]
        if not path or is_dir or not self.parent_app.is_path_allowed(path):
            return None
        return str(path)

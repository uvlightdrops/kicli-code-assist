"""Project explorer widget - displays file tree."""

from textual.widget import Widget
from textual.widgets import Tree
from textual.containers import Container
from pathlib import Path
from typing import Optional


class ProjectExplorer(Container):
    """File tree panel showing project structure."""
    
    DEFAULT_CSS = """
    ProjectExplorer {
        width: 25%;
        height: 100%;
        border: solid $primary;
    }
    
    ProjectExplorer > Tree {
        width: 100%;
        height: 100%;
    }
    """
    
    def __init__(self, project_path: str, **kwargs):
        super().__init__(**kwargs)
        self.project_path = Path(project_path)
        self.tree: Optional[Tree] = None
        self.selected_file: Optional[str] = None
    
    def compose(self):
        """Create tree widget."""
        self.tree = Tree("📁 Project")
        yield self.tree
    
    def on_mount(self) -> None:
        """Populate tree on mount."""
        if self.tree:
            self._load_tree(self.tree.root, self.project_path)
    
    def _load_tree(self, parent, path: Path, max_depth: int = 3, depth: int = 0) -> None:
        """Recursively load directory tree."""
        if depth >= max_depth:
            return
        
        try:
            items = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
            for item in items:
                if item.name.startswith("."):
                    continue
                
                icon = "📁" if item.is_dir() else "📄"
                node = parent.add(f"{icon} {item.name}", data=str(item))
                
                if item.is_dir() and depth < max_depth - 1:
                    self._load_tree(node, item, max_depth, depth + 1)
        
        except (PermissionError, OSError):
            pass
    
    def on_tree_select(self, event: Tree.Selected) -> None:
        """Handle file selection."""
        if event.node.data and Path(event.node.data).is_file():
            self.selected_file = event.node.data
            self.post_message(self.FileSelected(str(event.node.data)))
    
    class FileSelected(Widget.Post):
        """Posted when file is selected."""
        def __init__(self, file_path: str):
            self.file_path = file_path

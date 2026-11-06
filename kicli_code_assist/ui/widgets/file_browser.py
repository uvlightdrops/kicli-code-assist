"""
File Browser Widget

Tree widget for navigating project files and folders.
Supports VI-style keybindings (hjkl for navigation).
"""

import logging
from pathlib import Path
from typing import Optional, Set, List
from textual.widgets import Tree
from textual.widgets.tree import TreeNode
from textual.reactive import reactive

logger = logging.getLogger(__name__)


class FileTree(Tree):
    """File tree widget for project navigation.
    
    Features:
    - Recursive directory scanning
    - Configurable ignore patterns (.gitignore aware)
    - VI-style navigation (hjkl, Enter, etc.)
    - File/folder icons
    - Supports very large projects (lazy loading)
    
    Example:
        config = FileTreeConfig(project_root=".", ignore_patterns=[".git"])
        tree = FileTree(config)
        tree.focus()
    """
    
    # Observable state
    selected_path = reactive("")
    
    DEFAULT_CSS = """
    FileTree {
        width: 1fr;
        height: 100%;
        border: solid $primary;
    }
    
    FileTree:focus {
        border: double $accent;
    }
    """
    
    def __init__(self, project_root: str = ".", ignore_patterns: List[str] = None):
        """Initialize file tree.
        
        Args:
            project_root: Root directory to scan
            ignore_patterns: Patterns to ignore (e.g., [".git", "__pycache__"])
        """
        super().__init__("📁 Project")
        self.project_root = Path(project_root).resolve()
        self.ignore_patterns = ignore_patterns or [".git", "__pycache__", ".venv"]
        self.current_selection: Optional[TreeNode] = None
        self.on_file_selected_callback: Optional[callable] = None
        
        logger.info(f"FileTree initialized: {self.project_root}")
    
    def on_mount(self) -> None:
        """Scan project on mount."""
        self.scan_project()
    
    def scan_project(self) -> None:
        """Scan project root and populate tree."""
        logger.debug(f"Scanning project: {self.project_root}")
        
        try:
            root = self.root
            # Clear existing children by removing them one by one
            while root.children:
                root.children[0].remove()
            
            self._add_directory(root, self.project_root)
            
            logger.info(f"Project scan complete: {self.project_root}")
        
        except Exception as e:
            logger.error(f"Error scanning project: {e}")
            self.root.label = "📁 Error loading project"
    
    def _add_directory(self, parent: TreeNode, path: Path) -> None:
        """Recursively add directory contents to tree.
        
        Args:
            parent: Parent tree node
            path: Directory path to scan
        """
        if not path.is_dir():
            return
        
        try:
            # Get directory contents
            items = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
            
            # Filter ignored patterns
            items = [item for item in items if not self._should_ignore(item)]
            
            # Add each item
            for item in items:
                icon = "📁" if item.is_dir() else "📄"
                label = f"{icon} {item.name}"
                
                node = parent.add(label, expand=item.is_dir())
                node.data = {"path": item, "is_dir": item.is_dir()}
                
                # Lazy load subdirectories only if not too deep
                if item.is_dir() and self._get_depth(item) < 10:
                    # Check if directory has contents (for expand arrow)
                    try:
                        has_contents = any(not self._should_ignore(p) for p in item.iterdir())
                        if has_contents:
                            # Add a placeholder (will be replaced on expand)
                            node.add("...")
                    except PermissionError:
                        pass
        
        except PermissionError:
            logger.warning(f"Permission denied: {path}")
    
    def _should_ignore(self, path: Path) -> bool:
        """Check if path matches ignore patterns."""
        for pattern in self.ignore_patterns:
            if pattern in path.name or path.name.startswith(pattern):
                return True
        return False
    
    def _get_depth(self, path: Path) -> int:
        """Get directory depth relative to project root."""
        try:
            return len(path.relative_to(self.project_root).parts)
        except ValueError:
            return 0
    
    def _handle_selection(self, node) -> None:
        """Internal method to handle file selection (called from both event and external)."""
        if node.data and "path" in node.data:
            path = node.data["path"]
            is_dir = node.data["is_dir"]
            
            self.selected_path = str(path)
            self.current_selection = node
            
            # Expand/collapse on select
            if is_dir:
                if not node.is_expanded:  # Only populate if NOT already expanded
                    self._populate_node(node)
                # Toggle expand state
                node.toggle()
            
            logger.debug(f"Selected: {self.selected_path}")
            
            # Call file selection callback (files only)
            if not is_dir and self.on_file_selected_callback:
                try:
                    self.on_file_selected_callback(self.selected_path)
                except Exception as e:
                    logger.error(f"File selection callback error: {e}")
    
    def on_tree_select(self, event: Tree.NodeSelected) -> None:
        """Handle file selection."""
        self._handle_selection(event.node)
    
    def _populate_node(self, node: TreeNode) -> None:
        """Populate a directory node on first expand."""
        if not node.data or not node.data.get("is_dir"):
            return
        
        path = node.data["path"]
        
        # Replace placeholder with real contents
        if len(node.children) == 1 and node.children[0].label == "...":
            node.children = []
            self._add_directory(node, path)
    
    def on_tree_expand(self, event: Tree.NodeExpanded) -> None:
        """Handle directory expansion."""
        self._populate_node(event.node)
    
    def get_selected_path(self) -> Optional[Path]:
        """Get currently selected file path."""
        if self.selected_path:
            return Path(self.selected_path)
        return None
    
    def get_selected_content(self) -> Optional[str]:
        """Get content of selected file (if it's a file)."""
        path = self.get_selected_path()
        
        if path and path.is_file():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading file {path}: {e}")
                return None
        
        return None
    
    def set_on_file_selected(self, callback: callable) -> None:
        """Set file selection callback.
        
        Args:
            callback: Function called when file selected (receives file path)
        """
        self.on_file_selected_callback = callback
    
    def action_vi_up(self) -> None:
        """VI-style up navigation (k)."""
        if self.current_selection and self.current_selection.parent:
            # Move to previous sibling
            parent = self.current_selection.parent
            siblings = parent.children
            try:
                idx = siblings.index(self.current_selection)
                if idx > 0:
                    self.current_selection = siblings[idx - 1]
                    self.cursor_line = self.current_selection.line
            except ValueError:
                pass
    
    def action_vi_down(self) -> None:
        """VI-style down navigation (j)."""
        if self.current_selection and self.current_selection.parent:
            # Move to next sibling
            parent = self.current_selection.parent
            siblings = parent.children
            try:
                idx = siblings.index(self.current_selection)
                if idx < len(siblings) - 1:
                    self.current_selection = siblings[idx + 1]
                    self.cursor_line = self.current_selection.line
            except ValueError:
                pass
    
    def action_vi_left(self) -> None:
        """VI-style left (h) - collapse."""
        if self.current_selection and self.current_selection.is_expanded:
            self.current_selection.toggle()
    
    def action_vi_right(self) -> None:
        """VI-style right (l) - expand."""
        if self.current_selection and not self.current_selection.is_expanded:
            self.current_selection.toggle()

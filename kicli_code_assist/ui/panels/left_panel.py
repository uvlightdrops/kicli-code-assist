"""Left panel with tabbed file browsing and editing."""

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import TabbedContent, TabPane

from kicli_code_assist.ui.panels.file_browser import SelectableFileList
from kicli_code_assist.ui.panels.preview_pane import PreviewPane
from kicli_code_assist.ui.panels.file_editor import FileEditorPane


class LeftPanel(Container):
    """Left panel with preview and editor tabs."""
    
    DEFAULT_CSS = """
    LeftPanel {
        width: 1fr;
        height: 1fr;
    }
    
    LeftPanel TabbedContent {
        width: 1fr;
        height: 1fr;
    }
    
    LeftPanel TabPane {
        width: 1fr;
        height: 1fr;
    }
    """
    
    def __init__(self, parent_app=None, **kwargs):
        """Initialize left panel.
        
        Args:
            parent_app: Parent CodeAssistantApp instance
        """
        super().__init__(**kwargs)
        self.parent_app = parent_app
        self.tabbed_content: TabbedContent | None = None
        self._editor_counter = 0
        self._editor_tabs: dict[str, TabPane] = {}
    
    def compose(self) -> ComposeResult:
        """Create tabbed interface."""
        with TabbedContent(id="editor-tabs"):
            with TabPane("📂 Browser", id="tab-browser"):
                with Vertical():
                    file_browser = SelectableFileList(self.parent_app, id="file-browser")
                    yield file_browser
    
    def on_mount(self) -> None:
        """Setup after mount."""
        # Get reference to TabbedContent after composition
        self.tabbed_content = self.query_one(TabbedContent)
    
    def add_preview_pane(self, preview_pane: PreviewPane) -> None:
        """Add preview pane to browser tab.
        
        Args:
            preview_pane: PreviewPane widget to add
        """
        if not self.tabbed_content:
            return
        
        browser_tab = self.tabbed_content.query_one("#tab-browser", TabPane)
        # Remove old preview if exists
        for old_preview in browser_tab.query("PreviewPane"):
            old_preview.remove()
        browser_tab.mount(preview_pane)
    
    def create_editor_tab(self, file_path: str, content: str) -> FileEditorPane:
        """Create new editor tab for file.
        
        Args:
            file_path: Full path to file
            content: File content
        
        Returns:
            FileEditorPane widget
        """
        if not self.tabbed_content:
            return None
        
        filename = Path(file_path).name
        tab_id = f"editor-{self._editor_counter}"
        self._editor_counter += 1
        
        editor = FileEditorPane(
            file_path=file_path,
            content=content,
            name=filename,
            id=tab_id
        )
        
        tab = TabPane(filename, editor, id=tab_id)
        self.tabbed_content.add_pane(tab)
        self._editor_tabs[tab_id] = tab
        
        # Focus the new editor tab
        self.tabbed_content.active = tab_id
        
        return editor
    
    def close_editor_tab(self, tab_id: str) -> None:
        """Close an editor tab.
        
        Args:
            tab_id: ID of tab to close
        """
        if tab_id in self._editor_tabs:
            tab = self._editor_tabs[tab_id]
            tab.remove()
            del self._editor_tabs[tab_id]

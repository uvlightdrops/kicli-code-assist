"""Modal for creating new files."""

from pathlib import Path
from textual.app import Screen, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, Button, Label


class CreateFileModal(Screen):
    """Dialog for creating new file."""
    
    DEFAULT_CSS = """
    CreateFileModal {
        align: center middle;
    }
    
    CreateFileModal > Vertical {
        width: 60;
        height: 11;
        border: solid $primary;
        background: $surface;
    }
    
    CreateFileModal Label {
        margin: 1 0;
    }
    
    CreateFileModal Input {
        margin: 0 1 1 1;
    }
    
    CreateFileModal Horizontal {
        height: 1;
        margin: 0 1 1 1;
    }
    
    CreateFileModal Button {
        margin-right: 1;
    }
    """
    
    def __init__(self, app_ref, current_dir: Path):
        """Initialize CreateFileModal.
        
        Args:
            app_ref: Reference to parent app
            current_dir: Directory where file will be created
        """
        super().__init__()
        self.app_ref = app_ref
        self.current_dir = current_dir
    
    def compose(self) -> ComposeResult:
        """Compose the modal."""
        with Vertical():
            yield Label("📄 Create New File")
            yield Input(
                id="filename-input",
                placeholder="Enter relative path (e.g., src/main.py)"
            )
            with Horizontal():
                yield Button("Create", id="btn-create", variant="primary")
                yield Button("Cancel", id="btn-cancel")
    
    def on_mount(self) -> None:
        """Focus input on mount."""
        self.query_one("#filename-input", Input).focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-create":
            filename = self.query_one("#filename-input", Input).value.strip()
            if filename:
                self._create_file(filename)
            else:
                self.app.notify(
                    "❌ Please enter a filename",
                    severity="error",
                    timeout=5
                )
        elif event.button.id == "btn-cancel":
            self.app.pop_screen()
    
    def _create_file(self, filename: str) -> None:
        """Create file via backend.
        
        Args:
            filename: Relative path of file to create
        """
        try:
            from kicli_code_assist.ui.http_client import get_backend_client
            from kicli_code_assist.ui.panels.file_browser import SelectableFileList
            from kicli_code_assist.ui.panels.left_panel import LeftPanel
            
            # Ensure no absolute paths
            rel_path = filename.lstrip("/")
            
            # Get project root
            project_root = str(self.app_ref.get_allowed_base_path())
            
            # Call backend to create file
            client = get_backend_client()
            result = client.create_file(
                path=rel_path,
                content="",
                project_root=project_root
            )
            
            if result.get("success"):
                # Refresh file browser
                file_browser = self.app_ref.query_one(SelectableFileList)
                file_browser.load_directory()
                
                # Open in editor
                full_path = self.current_dir / rel_path
                left_panel = self.app_ref.query_one(LeftPanel)
                editor = left_panel.create_editor_tab(str(full_path), "")
                
                self.app.notify(f"✅ File created: {rel_path}", timeout=3)
                self.app.pop_screen()
            else:
                error = result.get("error", "Unknown error")
                if "already exists" in error.lower():
                    self.app.notify(
                        "❌ File already exists",
                        severity="error",
                        timeout=5
                    )
                else:
                    self.app.notify(
                        f"❌ Error: {error}",
                        severity="error",
                        timeout=5
                    )
        
        except Exception as e:
            import traceback
            self.app.notify(
                f"❌ Error creating file: {str(e)[:50]}",
                severity="error",
                timeout=10
            )
            # Also log full traceback
            from kicli_code_assist.logging_integration import get_logger
            logger = get_logger()
            logger.error(f"Create file error: {traceback.format_exc()}")

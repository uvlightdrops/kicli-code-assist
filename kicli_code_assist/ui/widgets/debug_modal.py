"""Debug modal with copyable content."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static, Button, TextArea


class DebugModal(ModalScreen):
    """Modal for displaying copyable debug information."""
    
    CSS = """
    DebugModal {
        align: center middle;
    }
    
    DebugModal > Vertical {
        width: 80;
        height: 24;
        border: solid $primary;
        background: $surface;
    }
    
    DebugModal TextArea {
        height: 1fr;
        width: 1fr;
    }
    
    DebugModal .buttons {
        dock: bottom;
        height: auto;
        border-top: solid $primary;
    }
    
    DebugModal Button {
        margin: 0 1;
    }
    """
    
    def __init__(self, title: str, content: str, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.content = content
    
    def compose(self) -> ComposeResult:
        """Create debug modal."""
        with Vertical():
            yield Static(f"🐛 {self.title}", classes="title")
            
            # TextArea for copyable content
            text_area = TextArea(
                text=self.content,
                theme="dracula",
                language="text",
            )
            text_area.read_only = True
            yield text_area
            
            # Buttons
            with Vertical(classes="buttons"):
                yield Button("📋 Copy All", id="copy-btn", variant="primary")
                yield Button("✓ Close", id="close-btn", variant="default")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "copy-btn":
            import pyperclip
            try:
                pyperclip.copy(self.content)
                self.app.notify("✅ Copied to clipboard!", title="Success", timeout=2)
            except Exception:
                # Fallback: try using xclip
                import subprocess
                try:
                    process = subprocess.Popen(
                        ['xclip', '-selection', 'clipboard'],
                        stdin=subprocess.PIPE
                    )
                    process.communicate(self.content.encode('utf-8'))
                    self.app.notify("✅ Copied to clipboard!", title="Success", timeout=2)
                except Exception as e:
                    self.app.notify(f"❌ Copy failed: {e}", title="Error", timeout=3)
            finally:
                self.dismiss()
        
        elif event.button.id == "close-btn":
            self.dismiss()

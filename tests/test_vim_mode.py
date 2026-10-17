"""Test Vi mode updates and command handling."""

import asyncio
from pathlib import Path
from textual.app import ComposeResult, App
from textual.containers import Container
from textual_vim_textarea import VimTextArea


class VimTestContainer(Container):
    """Test container to verify VimTextArea messages."""
    
    def __init__(self):
        super().__init__()
        self.test_events = []
        self.mode_changes = []
        self.save_requests = 0
        self.quit_requests = 0
    
    def compose(self) -> ComposeResult:
        self.editor = VimTextArea(text="def hello():\n    print('world')\n")
        yield self.editor
    
    def on_mount(self):
        """Setup test."""
        self.editor.focus()
        self.log("✓ Editor mounted and focused")
        # Simulate pressing ':' key
        self.log("Test: Checking for command mode support...")
    
    def on_vim_text_area_mode_changed(self, message: VimTextArea.ModeChanged) -> None:
        """Track mode changes."""
        self.mode_changes.append(f"Mode changed (event)")
        self.log(f"✓ ModeChanged event received")
    
    def on_vim_text_area_status_changed(self, message: VimTextArea.StatusChanged) -> None:
        """Track status updates."""
        self.log(f"✓ StatusChanged: {message.status}")
    
    def on_vim_text_area_save_requested(self, message: VimTextArea.SaveRequested) -> None:
        """Track save requests."""
        self.save_requests += 1
        self.log(f"✓ SaveRequested (:w command)")
    
    def on_vim_text_area_quit_requested(self, message: VimTextArea.QuitRequested) -> None:
        """Track quit requests."""
        self.quit_requests += 1
        self.log(f"✓ QuitRequested (:q command)")


class TestApp(App):
    """Simple test app."""
    
    def compose(self) -> ComposeResult:
        self.container = VimTestContainer()
        yield self.container
    
    def on_mount(self):
        """Run tests after mount."""
        self.log("\n=== Vi Mode Test ===")
        
        # Check editor state
        editor = self.container.editor
        if hasattr(editor, '_vim_state'):
            mode = editor._vim_state.mode
            self.log(f"✓ VimTextArea has _vim_state")
            self.log(f"  Current mode: {mode.name if hasattr(mode, 'name') else mode}")
        
        self.log(f"\n✓ Message handlers installed:")
        for attr in dir(self.container):
            if attr.startswith('on_vim'):
                self.log(f"  {attr}")
        
        self.exit()


if __name__ == "__main__":
    app = TestApp()
    app.run()

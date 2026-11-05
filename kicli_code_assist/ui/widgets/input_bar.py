"""
Input Bar & Status Bar Widgets

Bottom bar for user input and status display.
"""

import logging
from typing import Callable, Optional
from textual.widgets import Input, Static, Label
from textual.containers import Container, Horizontal
from textual.reactive import reactive

logger = logging.getLogger(__name__)


class InputBar(Container):
    """Input field for user requests.
    
    Features:
    - Single/multiline support
    - History tracking (Up/Down)
    - Placeholder text
    - Submit callback
    - Keyboard handling
    """
    
    # Observable state
    current_input = reactive("")
    is_focused = reactive(False)
    
    DEFAULT_CSS = """
    InputBar {
        width: 1fr;
        height: 3;
        background: $surface;
        border: solid $primary;
        padding: 0 1;
    }
    
    InputBar Input {
        width: 1fr;
        height: 1;
    }
    
    InputBar Label {
        width: 1fr;
        height: 1;
        color: $text-muted;
    }
    """
    
    def __init__(self, multiline: bool = True, max_history: int = 50):
        """Initialize input bar.
        
        Args:
            multiline: Support multiline input
            max_history: Max command history entries
        """
        super().__init__()
        self.multiline = multiline
        self.max_history = max_history
        self.history: list = []
        self.history_index: int = -1
        self.input_widget: Optional[Input] = None
        self.on_submit_callback: Optional[Callable[[str], None]] = None
    
    def compose(self):
        """Compose input layout."""
        with Horizontal(id="input-container"):
            yield Input(
                id="request-input",
                placeholder="Enter your request (Shift+Enter for newline)...",
            )
            yield Label("Ready", id="input-status")
    
    def on_mount(self) -> None:
        """Initialize on mount."""
        self.input_widget = self.query_one("#request-input", Input)
        self.input_widget.focus()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Track input changes."""
        self.current_input = event.value
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        text = event.value.strip()
        
        if not text:
            return
        
        # Add to history
        if not self.history or self.history[-1] != text:
            self.history.append(text)
            if len(self.history) > self.max_history:
                self.history.pop(0)
        
        self.history_index = -1
        
        # Clear input
        self.input_widget.value = ""
        
        # Call callback
        if self.on_submit_callback:
            try:
                self.on_submit_callback(text)
            except Exception as e:
                logger.error(f"Submit callback error: {e}")
                self.set_status(f"Error: {e}", error=True)
        
        logger.info(f"Input submitted: {text[:50]}...")
    
    def set_status(self, message: str, error: bool = False) -> None:
        """Update status display.
        
        Args:
            message: Status message
            error: True for error styling
        """
        status = self.query_one("#input-status", Label)
        status.update(message)
        
        if error:
            status.styles.color = "red"
        else:
            status.styles.color = "$text-muted"
    
    def set_on_submit(self, callback: Callable[[str], None]) -> None:
        """Set submit callback.
        
        Args:
            callback: Function called on input submission
        """
        self.on_submit_callback = callback
    
    def get_input(self) -> str:
        """Get current input value."""
        if self.input_widget:
            return self.input_widget.value
        return ""
    
    def clear_input(self) -> None:
        """Clear input field."""
        if self.input_widget:
            self.input_widget.value = ""
            self.current_input = ""
    
    def action_history_up(self) -> None:
        """Navigate history up."""
        if not self.history:
            return
        
        if self.history_index == -1:
            self.history_index = len(self.history) - 1
        elif self.history_index > 0:
            self.history_index -= 1
        
        if self.input_widget:
            self.input_widget.value = self.history[self.history_index]
    
    def action_history_down(self) -> None:
        """Navigate history down."""
        if not self.history or self.history_index == -1:
            return
        
        self.history_index += 1
        
        if self.history_index >= len(self.history):
            self.history_index = -1
            if self.input_widget:
                self.input_widget.value = ""
        else:
            if self.input_widget:
                self.input_widget.value = self.history[self.history_index]


class StatusBar(Static):
    """Status bar showing connection, metrics, time.
    
    Features:
    - Connection status
    - Processing time
    - Token count
    - Error messages
    """
    
    # Observable state
    connection_status = reactive("🔴 Offline")
    processing_time = reactive("")
    token_count = reactive("")
    error_message = reactive("")
    
    DEFAULT_CSS = """
    StatusBar {
        width: 1fr;
        height: 1;
        background: $panel;
        color: $text-muted;
        padding: 0 1;
        border-top: solid $primary;
    }
    """
    
    def __init__(self):
        """Initialize status bar."""
        super().__init__()
        self.update_status()
    
    def update_status(self) -> None:
        """Update display."""
        parts = [self.connection_status]
        
        if self.processing_time:
            parts.append(f"Time: {self.processing_time}")
        
        if self.token_count:
            parts.append(f"Tokens: {self.token_count}")
        
        if self.error_message:
            parts.append(f"⚠️  {self.error_message}")
        
        self.update(" | ".join(parts))
    
    def set_connected(self, connected: bool) -> None:
        """Set connection status.
        
        Args:
            connected: True if connected
        """
        self.connection_status = "🟢 Connected" if connected else "🔴 Offline"
        self.update_status()
    
    def set_processing_time(self, seconds: float) -> None:
        """Set processing time.
        
        Args:
            seconds: Time in seconds
        """
        self.processing_time = f"{seconds:.2f}s"
        self.update_status()
    
    def set_token_count(self, count: int) -> None:
        """Set token count.
        
        Args:
            count: Token count
        """
        self.token_count = str(count)
        self.update_status()
    
    def set_error(self, message: str) -> None:
        """Set error message.
        
        Args:
            message: Error message
        """
        self.error_message = message
        self.update_status()
    
    def clear_error(self) -> None:
        """Clear error message."""
        self.error_message = ""
        self.update_status()
    
    def watch_connection_status(self) -> None:
        """React to connection status change."""
        self.update_status()
    
    def watch_processing_time(self) -> None:
        """React to time change."""
        self.update_status()
    
    def watch_token_count(self) -> None:
        """React to token count change."""
        self.update_status()
    
    def watch_error_message(self) -> None:
        """React to error message change."""
        self.update_status()

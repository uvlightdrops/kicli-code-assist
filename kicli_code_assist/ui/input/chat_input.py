"""Chat input widget with command history and send button."""

from textual.widgets import TextArea, Button
from textual.app import ComposeResult
from textual.containers import Horizontal


class ChatInput(TextArea):
    """Chat input with command history support and visual Send button."""

    def __init__(self, parent_app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_app = parent_app
        self.command_history = []  # History of submitted commands
        self.history_index = -1  # Current position in history (-1 = new input)
        self.pending_input = ""  # Store current input while browsing history

    def send_message(self) -> None:
        """Send current message and add to history."""
        text = self.text.strip()
        if text:
            self.command_history.append(text)
            self.history_index = -1
            self.pending_input = ""
            # Submit to app
            self.parent_app.action_select_cursor()
            # Clear input after sending
            self.text = ""
    
    def on_key(self, event) -> None:
        """Handle key events: Ctrl+Enter or Shift+Enter to send, Up/Down for history."""
        if event.key == "ctrl+enter" or event.key == "shift+enter":
            # Ctrl+Enter or Shift+Enter = send
            self.send_message()
            event.prevent_default()
            event.stop()
        
        elif event.key == "up":
            # Up arrow: browse history
            cursor_row = self.cursor_location[0]
            if cursor_row == 0:  # Only if cursor is in first line
                event.prevent_default()
                event.stop()
                self._history_up()
        
        elif event.key == "down":
            # Down arrow: browse history forward
            cursor_row = self.cursor_location[0]
            if cursor_row == 0:  # Only if cursor is in first line
                event.prevent_default()
                event.stop()
                self._history_down()

    def _history_up(self) -> None:
        """Show previous command from history."""
        if not self.command_history:
            return
        
        # Save current input if we're at the end of history
        if self.history_index == -1:
            self.pending_input = self.text
        
        # Move back in history
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.text = self.command_history[-(self.history_index + 1)]

    def _history_down(self) -> None:
        """Show next command from history (or clear)."""
        if not self.command_history or self.history_index == -1:
            return
        
        # Move forward in history
        if self.history_index > 0:
            self.history_index -= 1
            self.text = self.command_history[-(self.history_index + 1)]
        else:
            # Back to current input
            self.history_index = -1
            self.text = self.pending_input

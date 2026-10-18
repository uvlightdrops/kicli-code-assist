"""Chat input widget with command history and send button."""

from textual.widgets import TextArea, Button, Static
from textual.containers import Horizontal
from textual.app import ComposeResult


class ChatInputBar(Static):
    """Chat input bar with TextArea and Send button."""
    
    DEFAULT_CSS = """
    ChatInputBar {
        height: auto;
        layout: horizontal;
        background: $surface;
        border-top: solid $primary;
    }
    
    ChatInputBar #chat-input-area {
        width: 1fr;
        height: auto;
    }
    
    ChatInputBar #chat-send-btn {
        width: auto;
        height: auto;
        margin: 0 1;
    }
    """
    
    def __init__(self, parent_app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_app = parent_app
        self.input_widget = ChatInput(parent_app, id="chat-input-area")
    
    def compose(self) -> ComposeResult:
        yield self.input_widget
        yield Button("↵ Send", id="chat-send-btn", variant="primary")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle Send button click."""
        if event.button.id == "chat-send-btn":
            self.input_widget.send_message()


class ChatInput(TextArea):
    """Chat input with command history support (like shell)."""

    def __init__(self, parent_app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_app = parent_app
        self.command_history = []  # History of submitted commands
        self.history_index = -1  # Current position in history (-1 = new input)
        self.pending_input = ""  # Store current input while browsing history

    def send_message(self) -> None:
        """Send current message."""
        text = self.text.strip()
        if text:
            self.command_history.append(text)
            self.history_index = -1
            self.pending_input = ""
            self.parent_app.action_select_cursor()
            self.text = ""  # Clear input
    
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

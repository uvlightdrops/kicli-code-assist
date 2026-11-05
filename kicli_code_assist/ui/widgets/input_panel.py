"""Input panel for agent requests."""

from textual.widgets import Static, Button, Input
from textual.containers import Container, Horizontal
from textual.binding import Binding
from typing import Optional


class InputPanel(Container):
    """Request input field and submit button."""
    
    DEFAULT_CSS = """
    InputPanel {
        height: 3;
        dock: bottom;
        border: solid $primary;
        padding: 1;
    }
    
    InputPanel > Horizontal {
        height: 1fr;
        width: 100%;
    }
    
    InputPanel Input {
        width: 1fr;
    }
    
    InputPanel Button {
        width: 12;
        margin-left: 1;
    }
    """
    
    BINDINGS = [
        Binding("enter", "submit", "Submit (Ctrl+Enter)", show=True),
        Binding("escape", "clear", "Clear", show=True),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_field: Optional[Input] = None
        self.submit_button: Optional[Button] = None
    
    def compose(self):
        """Create input field and button."""
        with Horizontal():
            self.input_field = Input(
                placeholder="Enter request (e.g., 'Analyze for performance issues')",
                id="request-input",
            )
            yield self.input_field
            
            self.submit_button = Button("Submit", id="submit-btn", variant="primary")
            yield self.submit_button
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle submit button press."""
        if event.button.id == "submit-btn":
            self.action_submit()
    
    def action_submit(self) -> None:
        """Submit request."""
        if self.input_field:
            request = self.input_field.value.strip()
            if request:
                self.post_message(self.RequestSubmitted(request))
                self.input_field.value = ""
    
    def action_clear(self) -> None:
        """Clear input."""
        if self.input_field:
            self.input_field.value = ""
    
    class RequestSubmitted:
        """Message posted when request is submitted."""
        def __init__(self, request: str):
            self.request = request

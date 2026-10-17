"""Error modal dialog for displaying error messages with recovery hints."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Header, Footer, Button, Static
from textual.binding import Binding

from ki_core.errors import KICoreError, RecoveryHint


class ErrorModal(ModalScreen):
    """Modal for displaying errors with recovery hints."""

    BINDINGS = [
        Binding("escape", "close", "Close", show=True),
        Binding("enter", "close", "OK", show=True),
    ]

    def __init__(self, error: Exception, name: str = "error_modal"):
        """Initialize error modal.
        
        Args:
            error: Exception to display
            name: Screen name
        """
        super().__init__(name=name)
        self.error = error

    def compose(self) -> ComposeResult:
        """Compose error modal."""
        with Container(id="error-modal-container"):
            yield Header(show_clock=False)
            
            with Vertical(id="error-content"):
                # Error message
                error_title = "Error"
                if isinstance(self.error, KICoreError):
                    error_title = f"Error [{self.error.error_code}]"
                
                yield Static(error_title, id="error-title", classes="error-header")
                
                # Error message
                error_msg = str(self.error)
                if isinstance(self.error, KICoreError):
                    error_msg = self.error.message
                
                yield Static(error_msg, id="error-message", classes="error-text")
                
                # Recovery hints (if available)
                if isinstance(self.error, KICoreError) and self.error.recovery_hints:
                    yield Static("Recovery suggestions:", id="hints-header", classes="error-header")
                    
                    for i, hint in enumerate(self.error.recovery_hints, 1):
                        hint_text = f"{i}. {hint.title}: {hint.description}"
                        if hint.action:
                            hint_text += f" [{hint.action}]"
                        yield Static(hint_text, id=f"hint-{i}", classes="error-hint")
                
                # Action buttons
                with Container(id="error-buttons"):
                    yield Button("Close", id="error-close-btn", variant="primary")
                    if isinstance(self.error, KICoreError) and self.error.recovery_hints:
                        yield Button("View Details", id="error-details-btn", variant="default")

            yield Footer()

    def action_close(self) -> None:
        """Close the modal."""
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "error-close-btn":
            self.action_close()
        elif event.button.id == "error-details-btn":
            # Could expand to show full traceback
            pass

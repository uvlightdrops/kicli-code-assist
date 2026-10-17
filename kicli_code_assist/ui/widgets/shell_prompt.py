"""Shell prompt styling widget."""

from textual.widgets import Static
from textual.reactive import reactive


class ShellPrompt(Static):
    """Shell command prompt indicator ($ )."""
    
    DEFAULT_CSS = """
    ShellPrompt {
        width: auto;
        height: 1;
        background: $boost;
        color: $success;
        content-align: left middle;
        padding: 0 1;
    }
    
    ShellPrompt.waiting {
        color: $warning;
    }
    
    ShellPrompt.error {
        color: $error;
    }
    """
    
    status = reactive("ready")  # ready, waiting, error
    
    def render(self) -> str:
        """Render prompt based on status."""
        if self.status == "waiting":
            return "⏳ >"
        elif self.status == "error":
            return "✗ >"
        else:
            return "$ "
    
    def set_waiting(self) -> None:
        """Set status to waiting."""
        self.status = "waiting"
    
    def set_error(self) -> None:
        """Set status to error."""
        self.status = "error"
    
    def set_ready(self) -> None:
        """Set status to ready."""
        self.status = "ready"
    
    def watch_status(self) -> None:
        """Update display when status changes."""
        self.update()

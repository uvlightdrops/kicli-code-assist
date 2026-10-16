"""Terminal output panel for shell command execution results."""

from textual.widgets import Static, RichLog
from textual.containers import Vertical
from rich.console import Console
from rich.text import Text


class TerminalPanel(Static):
    """Terminal output display for shell command results."""
    
    DEFAULT_CSS = """
    TerminalPanel {
        border: solid $primary;
        background: $surface;
    }
    
    TerminalPanel > RichLog {
        width: 100%;
        height: 100%;
    }
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_buffer: list[str] = []
        self.max_lines = 10000  # Keep last N lines in memory
    
    def compose(self):
        """Compose the terminal panel."""
        self.terminal_output = RichLog(highlight=False, markup=True)
        yield self.terminal_output
    
    def on_mount(self) -> None:
        """Setup after mount."""
        self.terminal_output.write("🖥️  Terminal Output\n")
        self.terminal_output.write("[dim]────────────────────────────────────[/]\n")
    
    def write(self, text: str) -> None:
        """Write text to terminal output."""
        self.terminal_output.write(text)
        self.output_buffer.append(text)
        
        # Trim buffer if too large
        if len(self.output_buffer) > self.max_lines:
            self.output_buffer = self.output_buffer[-self.max_lines:]
    
    def write_command(self, command: str) -> None:
        """Write a command line (bold cyan)."""
        self.write(f"[bold cyan]$ {command}[/]\n")
    
    def write_stdout(self, text: str) -> None:
        """Write stdout (dim gray)."""
        if text.strip():
            self.write(f"[dim]{text}[/]\n")
    
    def write_stderr(self, text: str) -> None:
        """Write stderr (bold red)."""
        if text.strip():
            self.write(f"[bold red]{text}[/]\n")
    
    def write_status(self, text: str) -> None:
        """Write status line (bold)."""
        self.write(f"[bold]{text}[/]\n")
    
    def write_success(self, text: str) -> None:
        """Write success message (bold green)."""
        self.write(f"[bold green]✓ {text}[/]\n")
    
    def write_error(self, text: str) -> None:
        """Write error message (bold red)."""
        self.write(f"[bold red]✗ {text}[/]\n")
    
    def clear(self) -> None:
        """Clear terminal output."""
        self.output_buffer.clear()
        self.terminal_output.clear()
        self.terminal_output.write("[dim]Terminal cleared[/]\n")
    
    def action_clear_terminal(self) -> None:
        """Action to clear terminal (accessible from key bindings)."""
        self.clear()

"""Terminal output panel for shell command execution results."""

from textual.widgets import Static, RichLog
from textual.containers import Vertical
from rich.console import Console
from rich.text import Text
from datetime import datetime


class TerminalPanel(Static):
    """Terminal output display for shell command results."""
    
    DEFAULT_CSS = """
    TerminalPanel {
        border: solid $primary;
        background: $boost;
        color: $text;
    }
    
    TerminalPanel > RichLog {
        width: 100%;
        height: 100%;
        background: $boost;
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
        self.terminal_output.write("[bold]🖥️  Terminal Output[/]\n")
        self.terminal_output.write("[dim]────────────────────────────────────────────────────────[/]\n")
    
    def write(self, text: str) -> None:
        """Write text to terminal output."""
        self.terminal_output.write(text)
        self.output_buffer.append(text)
        
        # Trim buffer if too large
        if len(self.output_buffer) > self.max_lines:
            self.output_buffer = self.output_buffer[-self.max_lines:]
    
    def write_command(self, command: str) -> None:
        """Write a command line (shell prompt style)."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write(f"[dim]{timestamp}[/] [bold cyan]$ {command}[/]\n")
    
    def write_stdout(self, text: str) -> None:
        """Write stdout (normal)."""
        if text.strip():
            self.write(f"{text}\n")
    
    def write_stderr(self, text: str) -> None:
        """Write stderr (bold red)."""
        if text.strip():
            self.write(f"[bold red]✗ {text}[/]\n")
    
    def write_status(self, text: str) -> None:
        """Write status line (bold)."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write(f"[dim]{timestamp}[/] [bold blue]→ {text}[/]\n")
    
    def write_success(self, text: str) -> None:
        """Write success message (bold green)."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write(f"[dim]{timestamp}[/] [bold green]✓ {text}[/]\n")
    
    def write_error(self, text: str) -> None:
        """Write error message (bold red)."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.write(f"[dim]{timestamp}[/] [bold red]✗ {text}[/]\n")
    
    def clear(self) -> None:
        """Clear terminal output."""
        self.output_buffer.clear()
        self.terminal_output.clear()
        self.terminal_output.write("[dim]Terminal cleared[/]\n")
    
    def action_clear_terminal(self) -> None:
        """Action to clear terminal (accessible from key bindings)."""
        self.clear()

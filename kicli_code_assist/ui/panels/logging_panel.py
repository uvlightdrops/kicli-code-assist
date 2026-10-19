"""Logging panel widget for displaying log files in the TUI."""

import os
from pathlib import Path
from textual.widgets import Static, Select
from textual.containers import Vertical, Horizontal
from textual.reactive import reactive
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax
from rich.table import Table


class LoggingPanel(Static):
    """Display log files with file selection and auto-scroll."""
    
    # Reactive properties
    selected_logfile = reactive("kicli.log")
    log_content = reactive("")
    
    LOG_DIR = Path("log")  # Relative to project root
    LOGFILES = [
        ("kicli.log", "📋 Main Log"),
        ("kicli-llm.log", "🤖 LLM Queries"),
        ("kicli-context.log", "📂 File Context"),
        ("kicli-workflow.log", "⚙️  Workflow"),
        ("kicli-errors.log", "❌ Errors"),
    ]
    
    DEFAULT_CSS = """
    LoggingPanel {
        height: 100%;
        width: 100%;
        border: solid $primary;
    }
    
    LoggingPanel > Vertical {
        height: 100%;
    }
    
    LoggingPanel #log_selector {
        height: 1;
        margin-bottom: 1;
    }
    
    LoggingPanel #log_display {
        height: 1fr;
        overflow: auto;
    }
    
    LoggingPanel #log_status {
        height: 1;
        color: $text-muted;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.console = Console(record=True)
        self._last_size = 0
        
    def compose(self):
        """Create child widgets."""
        with Vertical():
            # Logfile selector
            with Horizontal(id="log_header"):
                yield Static("📊 Logging", classes="log_title")
                
                # Dropdown to select logfile
                logfile_options = [(label, value) for value, label in self.LOGFILES]
                yield Select(logfile_options, id="log_selector", value="kicli.log")
            
            # Log content display
            yield Static("", id="log_display", classes="log_content")
            
            # Status bar
            yield Static("Ready", id="log_status", classes="log_status")
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle logfile selection."""
        if event.control.id == "log_selector":
            self.selected_logfile = str(event.value)
            self.refresh_log()
    
    def refresh_log(self) -> None:
        """Load and display the selected logfile."""
        logfile_path = self.LOG_DIR / self.selected_logfile
        
        # Get status widget
        status = self.query_one("#log_status", Static)
        display = self.query_one("#log_display", Static)
        
        # Check if log file exists
        if not logfile_path.exists():
            output = f"\n[dim]Log file not yet created:[/dim]\n[yellow]{logfile_path}[/yellow]\n\n"
            output += "[cyan]Waiting for first log entry...[/cyan]\n\n"
            output += "[dim]This logfile will be created when the first message is logged.[/dim]"
            display.update(output)
            status.update(f"⏳ Waiting for entries ({logfile_path.name})")
            return
        
        try:
            # Read last 100 lines
            with open(logfile_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Get last 100 lines (or all if fewer)
            tail_lines = lines[-100:] if len(lines) > 100 else lines
            content = "".join(tail_lines)
            
            # Display with syntax highlighting for log format
            # Log format: "2024-10-19 13:10:54 10/funcName  kicli.llm: message"
            display.update(self._render_log_content(content, logfile_path))
            
            # Update status
            file_size = logfile_path.stat().st_size
            line_count = len(lines)
            status.update(
                f"📄 {self.selected_logfile} | "
                f"{line_count} lines | "
                f"{file_size:,} bytes | "
                f"✅ Last {len(tail_lines)} lines shown"
            )
        except Exception as e:
            display.update(f"[red]Error reading logfile:[/red] {e}")
            status.update(f"❌ Error reading {logfile_path}")
    
    def _render_log_content(self, content: str, logfile_path: Path) -> str:
        """Render log content with syntax highlighting."""
        # Simple log formatting
        lines = content.strip().split('\n')
        
        output = f"\n[bold yellow]📂 {logfile_path}[/bold yellow]\n"
        output += "[dim]" + "─" * 80 + "[/dim]\n\n"
        
        for line in lines:
            if not line:
                continue
            
            # Color-code by log level
            if " ERROR " in line or " error " in line or " CRITICAL " in line:
                output += f"[red]{line}[/red]\n"
            elif " WARNING " in line or " warning " in line:
                output += f"[yellow]{line}[/yellow]\n"
            elif " DEBUG " in line or " debug " in line:
                output += f"[cyan]{line}[/cyan]\n"
            else:
                output += f"{line}\n"
        
        return output
    
    def on_mount(self):
        """Initialize on mount."""
        self.refresh_log()
        # Auto-refresh every 2 seconds
        self.set_interval(self.refresh_log, 2.0)
    
    def watch_selected_logfile(self, new_value: str) -> None:
        """Watch for logfile changes."""
        self.refresh_log()

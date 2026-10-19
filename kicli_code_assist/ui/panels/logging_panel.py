"""Modal logging viewer as a workaround for TabPane rendering issues."""

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Static, Header, Footer, Button
from textual.reactive import reactive


class LogViewerModal(Container):
    """Modal dialog to view logs."""
    
    LOG_DIR = Path("log")
    LOGFILES = [
        ("kicli.log", "📋 Main"),
        ("kicli-llm.log", "🤖 LLM"),
        ("kicli-context.log", "📂 Context"),
        ("kicli-workflow.log", "⚙️  Workflow"),
        ("kicli-errors.log", "❌ Errors"),
    ]
    
    CSS = """
    LogViewerModal {
        width: 100%;
        height: auto;
        border: double $accent;
        background: $panel;
    }
    #log_content {
        width: 100%;
        height: auto;
        border: solid $primary;
        background: $surface;
    }
    #log_buttons {
        width: 100%;
        height: auto;
        layout: horizontal;
    }
    """
    
    def __init__(self, logfile: str = "kicli.log", **kwargs):
        super().__init__(**kwargs)
        self.current_logfile = logfile
        self._current_log_idx = 0
    
    def compose(self) -> ComposeResult:
        """Create modal layout."""
        with Vertical(id="log_container"):
            yield Static(f"📋 Log Viewer - {self.current_logfile}", id="log_header")
            yield Static("", id="log_content")
            with Container(id="log_buttons"):
                yield Button("◀ Prev", id="prev_btn", variant="primary")
                yield Button("🔄 Refresh", id="refresh_btn")
                yield Button("Next ▶", id="next_btn", variant="primary")
                yield Button("Close", id="close_btn", variant="warning")
    
    def on_mount(self) -> None:
        """Load initial logs."""
        self._load_logs()
        self.set_interval(self._load_logs, 2.0)
    
    def on_button_pressed(self, event) -> None:
        """Handle button presses."""
        if event.button.id == "prev_btn":
            self.action_prev_log()
        elif event.button.id == "next_btn":
            self.action_next_log()
        elif event.button.id == "refresh_btn":
            self._load_logs()
        elif event.button.id == "close_btn":
            self.app.pop_screen()
    
    def action_next_log(self) -> None:
        """Switch to next log file."""
        self._current_log_idx = (self._current_log_idx + 1) % len(self.LOGFILES)
        self.current_logfile = self.LOGFILES[self._current_log_idx][0]
        self._update_header()
        self._load_logs()
    
    def action_prev_log(self) -> None:
        """Switch to previous log file."""
        self._current_log_idx = (self._current_log_idx - 1) % len(self.LOGFILES)
        self.current_logfile = self.LOGFILES[self._current_log_idx][0]
        self._update_header()
        self._load_logs()
    
    def _update_header(self) -> None:
        """Update header with current logfile name."""
        header = self.query_one("#log_header", Static)
        idx_display = f"[{self._current_log_idx + 1}/{len(self.LOGFILES)}]"
        header.update(f"📋 Log Viewer - {self.current_logfile} {idx_display}")
    
    def _load_logs(self) -> None:
        """Load and display the selected log file."""
        logfile = self.LOG_DIR / self.current_logfile
        content_widget = self.query_one("#log_content", Static)
        
        if not logfile.exists():
            content_widget.update(f"⏳ Waiting for {self.current_logfile}...")
            return
        
        try:
            with open(logfile, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if not lines:
                content_widget.update(f"📄 {self.current_logfile}\n(empty file)")
                return
            
            # Show last 20 lines
            tail = lines[-20:] if len(lines) > 20 else lines
            output = f"\n[{len(lines)} lines total]\n"
            output += "─" * 60 + "\n"
            output += "".join(tail)
            
            content_widget.update(output)
        
        except (OSError, IOError) as e:
            content_widget.update(f"❌ Error reading {self.current_logfile}\n{e}")



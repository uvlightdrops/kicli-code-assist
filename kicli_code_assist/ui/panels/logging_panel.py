"""Modal logging viewer as a workaround for TabPane rendering issues."""

from pathlib import Path
from textual.app import ComposeResult, Screen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Button, Select, RichLog
from textual.reactive import reactive


def get_log_dir() -> Path:
    """Get the log directory, using configured path or default."""
    from kicli_code_assist.app_config import AppConfig
    
    config = AppConfig.from_env()
    if config.kicli_log_dir:
        return Path(config.kicli_log_dir)
    
    # Default: ~/dev_data/kicli-code-assist/log
    default_data_dir = Path.home() / "dev_data" / "kicli-code-assist"
    return default_data_dir / "log"


class LogViewerModal(Screen):
    """Modal screen to view logs."""
    
    @property
    def LOG_DIR(self) -> Path:
        """Get configured log directory."""
        return get_log_dir()
    
    LOGFILES = [
        ("kicli.log", "📋 Main"),
        ("kicli-llm.log", "🤖 LLM"),
        ("kicli-context.log", "📂 Context"),
        ("kicli-workflow.log", "⚙️  Workflow"),
        ("kicli-errors.log", "❌ Errors"),
    ]
    
    CSS = """
    LogViewerModal {
        align: center middle;
    }
    #log_container {
        width: 160;
        height: 48;
        border: double $accent;
        background: $panel;
        layout: vertical;
    }
    #log_header {
        dock: top;
        height: 1;
        background: $boost;
        color: $text;
    }
    #log_selector {
        dock: top;
        height: 3;
        margin: 0 1;
    }
    #log_content {
        width: 1fr;
        height: 1fr;
        border: solid $primary;
        background: $surface;
        overflow: auto;
    }
    #log_buttons {
        dock: bottom;
        height: auto;
        layout: horizontal;
    }
    Button {
        margin: 0 1;
    }
    """
    
    def __init__(self, logfile: str = "kicli.log", **kwargs):
        super().__init__(**kwargs)
        self.current_logfile = logfile
        self._current_log_idx = 0
    
    BINDINGS = [
        ("escape", "close_modal", "Close Modal [Esc]"),
        ("n", "next_log", "Next Log [N]"),
        ("p", "prev_log", "Prev Log [P]"),
    ]
    
    def action_close_modal(self) -> None:
        """Close the modal screen."""
        self.app.pop_screen()
    
    def compose(self) -> ComposeResult:
        """Create modal layout."""
        with Container(id="log_container"):
            yield Static(f"📋 Log Viewer", id="log_header")
            
            # Select widget for logfile switching
            log_options = [(f"{name} - {label}", name) for name, label in self.LOGFILES]
            yield Select(log_options, value=self.current_logfile, id="log_selector")
            
            # Use RichLog for better scrolling and content display
            self.log_display = RichLog(id="log_content")
            yield self.log_display
            
            with Container(id="log_buttons"):
                yield Button("◀ Prev", id="prev_btn", variant="primary")
                yield Button("🔄 Refresh", id="refresh_btn")
                yield Button("Next ▶", id="next_btn", variant="primary")
                yield Button("Close [Esc]", id="close_btn", variant="warning")
    
    def on_mount(self) -> None:
        """Load initial logs."""
        self._load_logs()
        self.set_interval(self._load_logs, 2.0)
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle logfile selection from dropdown."""
        self.current_logfile = event.value
        # Find index for consistent state
        for idx, (name, _) in enumerate(self.LOGFILES):
            if name == event.value:
                self._current_log_idx = idx
                break
        self._load_logs()
    
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
        self._update_select()
        self._load_logs()
    
    def action_prev_log(self) -> None:
        """Switch to previous log file."""
        self._current_log_idx = (self._current_log_idx - 1) % len(self.LOGFILES)
        self.current_logfile = self.LOGFILES[self._current_log_idx][0]
        self._update_select()
        self._load_logs()
    
    def _update_select(self) -> None:
        """Update select widget to match current logfile."""
        try:
            select = self.query_one("#log_selector", Select)
            select.value = self.current_logfile
        except:
            pass
    
    def _load_logs(self) -> None:
        """Load and display the selected log file."""
        logfile = self.LOG_DIR / self.current_logfile
        
        if not hasattr(self, 'log_display'):
            return
        
        if not logfile.exists():
            self.log_display.write(f"⏳ Waiting for {self.current_logfile}...")
            return
        
        try:
            with open(logfile, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if not lines:
                self.log_display.write(f"📄 {self.current_logfile}\n(empty file)")
                return
            
            # Clear and reload all content
            self.log_display.clear()
            
            # Write header
            self.log_display.write(f"📄 {self.current_logfile}  [{len(lines)} lines total]")
            self.log_display.write("─" * 160)
            
            # Write all lines (RichLog will handle scrolling)
            for line in lines:
                self.log_display.write(line.rstrip('\n'))
        
        except (OSError, IOError) as e:
            self.log_display.write(f"❌ Error reading {self.current_logfile}\n{e}")




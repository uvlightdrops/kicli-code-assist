"""
Main TUI Application

Textual app that serves as the main container for all UI components.
"""

from pathlib import Path
import logging
from textual.app import ComposeResult, on
from textual.containers import Container
from textual.widgets import Header, Footer
from textual import work
from textual.app import App

from .config import ConfigLoader, TUIConfig


logger = logging.getLogger(__name__)


class KICLITUIApp(App):
    """Main KI Code Assistant TUI Application."""
    
    CSS = """
    Screen {
        background: $surface;
        color: $text;
    }
    
    Header {
        dock: top;
        height: 1;
        background: $primary;
        color: $text;
    }
    
    Footer {
        dock: bottom;
        height: 1;
        background: $panel;
        color: $text;
    }
    """
    
    TITLE = "KI Code Assistant"
    SUB_TITLE = "Intelligent Terminal IDE for Code Analysis"
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]
    
    def __init__(self, config_path: str = None):
        """Initialize TUI app with configuration."""
        super().__init__()
        self.config_loader = ConfigLoader(config_path)
        self.config = self.config_loader.config
        
        if self.config.debug:
            self.config_loader.debug_print()
    
    def compose(self) -> ComposeResult:
        """Compose main UI layout."""
        # Header
        yield Header()
        
        # Main content area (placeholder)
        # Will be filled in with individual components in future phases
        yield Container(id="main-content")
        
        # Footer
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize app on mount."""
        logger.info("KI Code Assistant TUI started")
        logger.info(f"Backend: {self.config.backend.url}")
        logger.info(f"Enabled panels: {self.config_loader.get_enabled_panels()}")
        
        if self.config.debug:
            self.title = f"{self.TITLE} [DEBUG]"
    
    def action_quit(self) -> None:
        """Handle quit action."""
        logger.info("Shutting down TUI")
        self.exit()


def run_tui(config_path: str = None) -> None:
    """Run the TUI application."""
    app = KICLITUIApp(config_path)
    app.run()


if __name__ == "__main__":
    import sys
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    run_tui(config_path)

"""TUI Configuration and styling."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class TUIConfig:
    """TUI runtime configuration."""
    
    # Backend connection
    api_base_url: str = "http://localhost:8000"
    ws_base_url: str = "ws://localhost:8000"
    
    # Display
    max_output_lines: int = 500
    refresh_rate: float = 0.1  # seconds
    
    # Formatting
    syntax_theme: str = "monokai"
    show_line_numbers: bool = True
    
    @classmethod
    def from_env(cls) -> "TUIConfig":
        """Load from environment variables."""
        import os
        return cls(
            api_base_url=os.getenv("TUI_API_URL", "http://localhost:8000"),
            ws_base_url=os.getenv("TUI_WS_URL", "ws://localhost:8000"),
            max_output_lines=int(os.getenv("TUI_MAX_LINES", "500")),
        )


# TCSS (Textual CSS) styling
TUI_CSS = """
Screen {
    layout: grid;
    grid-size: 2 3;
    grid-columns: 25% 1fr;
    grid-rows: 1fr auto auto;
}

#project-panel {
    border: solid $primary;
    width: 100%;
    height: 100%;
}

#output-panel {
    border: solid $accent;
    width: 100%;
    height: 100%;
}

#status-bar {
    dock: bottom;
    height: 1;
    background: $surface;
    color: $text;
}

#input-panel {
    dock: bottom;
    height: 3;
    border: solid $primary;
}

.metric {
    width: 1fr;
    text-align: center;
}

.loading {
    color: $accent;
}

.error {
    color: $error;
}

.success {
    color: $success;
}
"""

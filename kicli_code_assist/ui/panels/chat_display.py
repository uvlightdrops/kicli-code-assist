"""Chat display with Rich formatting and text selection support."""

from textual.widgets import RichLog


class SelectableRichLog(RichLog):
    """RichLog with text selection support.
    
    - Rich markup support for colors/formatting
    - Mouse selection (triple-click to select line)
    - Copy-to-clipboard via standard text selection
    """
    
    DEFAULT_CSS = """
    SelectableRichLog {
        height: 1fr;
        width: 100%;
        border: none;
        background: $panel;
        /* Enable text selection and copying */
        selection-background: $accent;
        selection-text: $text;
    }
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Enable keyboard focus for text selection
        self.can_focus = True

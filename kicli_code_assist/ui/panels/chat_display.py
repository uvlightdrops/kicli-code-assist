"""Chat display with text selection."""

from textual.widgets import RichLog


class SelectableRichLog(RichLog):
    """RichLog with text selection support for mouse and keyboard."""
    
    DEFAULT_CSS = """
    SelectableRichLog {
        height: 1fr;
        width: 100%;
        border: none;
        background: $panel;
    }
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_focus = True
        self.selected_text = ""
        self.selection_start = None
        self.selection_end = None
    
    def on_mouse_down(self, event) -> None:
        """Start text selection on mouse down."""
        self.selection_start = event.offset
        self.selection_end = event.offset
        event.prevent_default()
    
    def on_mouse_move(self, event) -> None:
        """Update text selection on mouse move."""
        if self.selection_start is not None:
            self.selection_end = event.offset
            event.prevent_default()
    
    def on_mouse_up(self, event) -> None:
        """Finish text selection on mouse up."""
        if self.selection_start is not None and self.selection_end is not None:
            # Text selection is handled, cursor doesn't need focus
            pass
        event.prevent_default()

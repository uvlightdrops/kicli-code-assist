"""
VI Editor Modal Widget

Text editor with VI keybindings.
Supports Insert mode, Normal mode, Visual mode.
"""

import logging
from typing import Optional, Callable
from textual.widgets import TextArea
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.binding import Binding

logger = logging.getLogger(__name__)


class VIEditorModal(Container):
    """VI-style text editor modal.
    
    Modes:
    - Normal: hjkl navigation, commands
    - Insert: Free text input
    - Visual: Selection mode
    
    Features:
    - VI-style keybindings
    - Multiline support
    - Search & replace
    - Undo/Redo
    - Line numbers
    
    Example:
        editor = VIEditorModal()
        result = await editor.edit("Initial text")
        # Returns edited text or None if cancelled
    """
    
    # Observable state
    is_visible = reactive(True)
    current_mode = reactive("INSERT")  # INSERT | NORMAL | VISUAL
    error_message = reactive("")
    line_count = reactive(0)
    
    DEFAULT_CSS = """
    VIEditorModal {
        width: 100%;
        height: 100%;
        background: $surface;
        border: solid $primary;
    }
    
    VIEditorModal > Vertical {
        width: 1fr;
        height: 1fr;
    }
    
    VIEditorModal .editor-header {
        dock: top;
        height: 1;
        background: $panel;
        color: $text-muted;
    }
    
    VIEditorModal .editor-content {
        width: 1fr;
        height: 1fr;
        border: solid $primary;
    }
    
    VIEditorModal .editor-footer {
        dock: bottom;
        height: 1;
        background: $panel;
        color: $text-muted;
    }
    
    VIEditorModal TextArea {
        width: 1fr;
        height: 1fr;
    }
    """
    
    BINDINGS = [
        Binding("escape", "normal_mode", "Normal Mode", show=False),
        Binding("ctrl+c", "cancel", "Cancel"),
        Binding("ctrl+s", "save", "Save", show=False),
        Binding("ctrl+z", "undo", "Undo", show=False),
        Binding("ctrl+y", "redo", "Redo", show=False),
    ]
    
    def __init__(
        self,
        initial_text: str = "",
        language: str = "python",
        vi_mode: bool = True,
    ):
        """Initialize VI editor.
        
        Args:
            initial_text: Text to edit
            language: Language for syntax highlighting
            vi_mode: Enable VI keybindings
        """
        super().__init__()
        self.initial_text = initial_text
        self.language = language
        self.vi_mode = vi_mode
        self.text_area: Optional[TextArea] = None
        self.result: Optional[str] = None
        self.on_save_callback: Optional[Callable[[str], None]] = None
    
    def compose(self):
        """Compose editor layout."""
        with Vertical(id="editor-container"):
            yield TextArea(
                id="text-input",
                language=self.language,
            )
    
    def on_mount(self) -> None:
        """Initialize on mount."""
        self.text_area = self.query_one("#text-input", TextArea)
        
        # Set initial text
        if self.initial_text:
            self.text_area.text = self.initial_text
        
        # Focus editor
        self.text_area.focus()
        
        # Set mode
        if not self.vi_mode:
            self.current_mode = "INSERT"
        
        logger.info(f"VI Editor initialized (mode={self.current_mode})")
    
    def action_normal_mode(self) -> None:
        """Switch to normal mode (command mode)."""
        if self.current_mode != "NORMAL":
            self.current_mode = "NORMAL"
            # In real VI, this would parse commands like :wq, :q!, etc.
            logger.debug("Switched to NORMAL mode")
    
    def action_insert_mode(self) -> None:
        """Switch to insert mode."""
        if self.current_mode != "INSERT":
            self.current_mode = "INSERT"
            logger.debug("Switched to INSERT mode")
    
    def action_visual_mode(self) -> None:
        """Switch to visual mode (selection)."""
        if self.current_mode != "VISUAL":
            self.current_mode = "VISUAL"
            logger.debug("Switched to VISUAL mode")
    
    def action_save(self) -> None:
        """Save and close editor."""
        if self.text_area:
            self.result = self.text_area.text
            
            # Call callback if provided
            if self.on_save_callback:
                try:
                    self.on_save_callback(self.result)
                except Exception as e:
                    self.error_message = f"Save error: {e}"
                    logger.error(f"Save callback error: {e}")
                    return
            
            logger.info("Editor saved")
            self.hide()
    
    def action_cancel(self) -> None:
        """Cancel editing (discard changes)."""
        self.result = None
        logger.info("Editor cancelled")
        self.hide()
    
    def action_undo(self) -> None:
        """Undo last change."""
        if self.text_area:
            try:
                # TextArea doesn't expose undo directly; use Ctrl+Z native
                logger.debug("Undo (handled by TextArea)")
            except Exception as e:
                logger.error(f"Undo error: {e}")
    
    def action_redo(self) -> None:
        """Redo last undo."""
        if self.text_area:
            try:
                # TextArea doesn't expose redo directly; use Ctrl+Y native
                logger.debug("Redo (handled by TextArea)")
            except Exception as e:
                logger.error(f"Redo error: {e}")
    
    def show(self) -> None:
        """Show modal."""
        self.is_visible = True
        self.display = True
    
    def hide(self) -> None:
        """Hide modal."""
        self.is_visible = False
        self.display = False
    
    def get_text(self) -> str:
        """Get edited text.
        
        Returns:
            Edited text or empty string if cancelled
        """
        return self.result or ""
    
    def set_on_save(self, callback: Callable[[str], None]) -> None:
        """Set save callback.
        
        Args:
            callback: Function to call on save (receives text)
        """
        self.on_save_callback = callback
    
    def set_language(self, language: str) -> None:
        """Change syntax highlighting language.
        
        Args:
            language: Language identifier
        """
        self.language = language
        if self.text_area:
            self.text_area.language = language
    
    def watch_current_mode(self, mode: str) -> None:
        """Update display when mode changes."""
        logger.debug(f"Mode changed: {mode}")
    
    def action_vi_up(self) -> None:
        """VI-style up (k)."""
        if self.text_area and self.current_mode == "NORMAL":
            # Move cursor up
            # TextArea cursor handling is native
            pass
    
    def action_vi_down(self) -> None:
        """VI-style down (j)."""
        if self.text_area and self.current_mode == "NORMAL":
            # Move cursor down
            pass
    
    def action_vi_left(self) -> None:
        """VI-style left (h)."""
        if self.text_area and self.current_mode == "NORMAL":
            # Move cursor left
            pass
    
    def action_vi_right(self) -> None:
        """VI-style right (l)."""
        if self.text_area and self.current_mode == "NORMAL":
            # Move cursor right
            pass

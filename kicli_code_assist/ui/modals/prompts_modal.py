"""Prompts management modal."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from kicli_code_assist.prompts import PromptManager
from kicli_code_assist.ui.prompts_panel import PromptsPanel


class PromptsModal(ModalScreen):
    """Modal dialog for prompt management."""
    
    CSS = """
    PromptsModal {
        align: center middle;
        background: $surface 50%;
    }
    
    PromptsModal PromptsPanel {
        width: 100;
        height: 40;
        border: solid $primary;
        background: $surface;
        padding: 1;
    }
    """
    
    BINDINGS = [
        Binding("escape", "close_modal", "Close", show=True),
    ]
    
    def __init__(self, prompt_manager: PromptManager):
        super().__init__()
        self.prompt_manager = prompt_manager
        self.prompts_panel = None
    
    def compose(self) -> ComposeResult:
        """Create modal content - direct panel without containers."""
        self.prompts_panel = PromptsPanel(self.prompt_manager)
        yield self.prompts_panel
    
    def on_mount(self) -> None:
        """Focus the prompts panel on mount after render."""
        self.call_after_refresh(self._ensure_focus)
    
    def _ensure_focus(self) -> None:
        """Ensure prompts panel has focus."""
        if self.prompts_panel:
            # Try to focus on the first child widget (RoleSelector)
            for child in self.prompts_panel.children:
                if child.can_focus:
                    child.focus()
                    return
            # Fallback to panel itself
            if self.prompts_panel.can_focus:
                self.prompts_panel.focus()
    
    def action_close_modal(self) -> None:
        """Close the modal."""
        self.app.pop_screen()

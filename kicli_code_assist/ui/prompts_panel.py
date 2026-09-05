"""Prompt management panel for TUI - role selector, template management, language learning."""

from typing import Optional, Callable, List
from dataclasses import dataclass
from textual.widgets import Static, Button, Label
from textual.containers import Vertical, Horizontal
from textual.binding import Binding
from textual.message import Message
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from kicli_code_assist.prompts import PromptManager


@dataclass
class PromptChanged(Message):
    """Message when active prompt is changed."""
    role_id: str
    prompt_text: str


@dataclass
class LanguageLearningToggled(Message):
    """Message when language learning is toggled."""
    enabled: bool
    language: Optional[str] = None


class RoleSelector(Static):
    """Display and select available prompt roles."""
    
    can_focus = True
    
    DEFAULT_CSS = """
    RoleSelector {
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    """
    
    BINDINGS = [
        Binding("up", "select_previous_role", "Previous Role", show=False),
        Binding("down", "select_next_role", "Next Role", show=False),
        Binding("enter", "set_active_role", "Activate Role", show=False),
        Binding("f", "toggle_favorite", "Toggle Favorite", show=False),
    ]
    
    def __init__(self, manager: PromptManager, on_change: Optional[Callable] = None):
        super().__init__()
        self.manager = manager
        self.on_change = on_change
        self.selected_index = 0
        self.roles_list: List[str] = []
        self.update_roles_list()
        self.render_display()
    
    def update_roles_list(self) -> None:
        """Update the list of available roles."""
        self.roles_list = sorted(self.manager.list_roles().keys())
    
    def render_display(self) -> None:
        """Render the role selector display."""
        if not self.roles_list:
            self.update("❌ No roles available")
            return
        
        # Ensure selection is valid
        if self.selected_index >= len(self.roles_list):
            self.selected_index = max(0, len(self.roles_list) - 1)
        
        # Build display
        lines = []
        active_role = self.manager.prompts_config.active_role
        
        for i, role_id in enumerate(self.roles_list):
            role = self.manager.get_role(role_id)
            if not role:
                continue
            
            # Markers
            active = "▶" if role_id == active_role else " "
            selected = "●" if i == self.selected_index else "○"
            favorite = "⭐" if self.manager.is_favorite(role_id) else "  "
            status = "✅" if role.enabled else "❌"
            
            line = f"{selected} {active} {favorite} {status} {role.name}"
            lines.append(line)
        
        header = "📚 PROMPT ROLES"
        content = "\n".join(lines)
        
        panel = Panel(
            content,
            title=header,
            expand=False,
            style="bold cyan"
        )
        
        self.update(panel)
    
    def action_select_previous_role(self) -> None:
        """Move selection up."""
        if self.selected_index > 0:
            self.selected_index -= 1
            self.render_display()
    
    def action_select_next_role(self) -> None:
        """Move selection down."""
        if self.selected_index < len(self.roles_list) - 1:
            self.selected_index += 1
            self.render_display()
    
    def action_set_active_role(self) -> None:
        """Set the selected role as active."""
        if self.selected_index < len(self.roles_list):
            role_id = self.roles_list[self.selected_index]
            self.manager.set_active_role(role_id)
            self.render_display()
            
            # Notify parent
            if self.on_change:
                prompt = self.manager.get_effective_system_prompt()
                self.post_message(PromptChanged(role_id, prompt))
    
    def action_toggle_favorite(self) -> None:
        """Toggle favorite status for selected role."""
        if self.selected_index < len(self.roles_list):
            role_id = self.roles_list[self.selected_index]
            if self.manager.is_favorite(role_id):
                self.manager.remove_favorite(role_id)
            else:
                self.manager.add_favorite(role_id)
            self.render_display()


class LanguageLearningPanel(Static):
    """Language learning configuration panel."""
    
    can_focus = True
    
    DEFAULT_CSS = """
    LanguageLearningPanel {
        height: auto;
        border: solid $accent;
        padding: 1;
    }
    """
    
    BINDINGS = [
        Binding("t", "toggle_language_learning", "Toggle LL", show=False),
    ]
    
    def __init__(self, manager: PromptManager):
        super().__init__()
        self.manager = manager
        self.render_display()
    
    def render_display(self) -> None:
        """Render language learning status."""
        ll = self.manager.prompts_config.language_learning
        
        if not ll.enabled:
            content = "Language Learning: ❌ Disabled\n(Press 'T' to enable)"
            style = "dim"
        else:
            content = (
                f"🌍 Language Learning: ✅ ENABLED\n"
                f"   Target: {ll.target_language}\n"
                f"   Level: {ll.level.value}\n"
                f"   Native: {ll.native_language}\n"
                f"(Press 'T' to disable)"
            )
            style = "bold yellow"
        
        panel = Panel(
            content,
            title="LANGUAGE LEARNING",
            expand=False,
            style=style
        )
        
        self.update(panel)
    
    def action_toggle_language_learning(self) -> None:
        """Toggle language learning mode."""
        if self.manager.is_language_learning_enabled():
            self.manager.disable_language_learning()
        else:
            # Enable with defaults
            self.manager.enable_language_learning("English", "beginner")
        
        self.render_display()
        
        # Notify parent
        enabled = self.manager.is_language_learning_enabled()
        lang = self.manager.prompts_config.language_learning.target_language if enabled else None
        self.post_message(LanguageLearningToggled(enabled, lang))


class PromptStatusBar(Static):
    """Status bar showing current active prompt and quick info."""
    
    can_focus = True
    
    DEFAULT_CSS = """
    PromptStatusBar {
        height: 3;
        background: $panel;
        border-top: solid $primary;
        padding: 0 1;
        content-align: left middle;
    }
    """
    
    def __init__(self, manager: PromptManager):
        super().__init__()
        self.manager = manager
        self.update_display()
    
    def update_display(self) -> None:
        """Update the status bar display."""
        active_role = self.manager.get_active_role()
        ll = self.manager.prompts_config.language_learning
        
        if not active_role:
            role_text = "No active role"
        else:
            role_text = f"Role: {active_role.name} ({active_role.id})"
        
        if ll.enabled:
            ll_text = f"LL: {ll.target_language} ({ll.level.value})"
        else:
            ll_text = "LL: Disabled"
        
        templates_count = len(self.manager.list_templates())
        fav_count = len(self.manager.get_favorites())
        
        status = f"  {role_text}  |  {ll_text}  |  Templates: {templates_count}  Favorites: {fav_count}"
        self.update(status)
    
    def on_prompt_changed(self, message: PromptChanged) -> None:
        """Handle prompt change."""
        self.update_display()
    
    def on_language_learning_toggled(self, message: LanguageLearningToggled) -> None:
        """Handle language learning toggle."""
        self.update_display()


class PromptsPanel(Vertical):
    """Complete prompt management panel with role selector and settings."""
    
    can_focus = True
    
    DEFAULT_CSS = """
    PromptsPanel {
        height: auto;
        width: 100%;
        background: $surface;
    }
    
    PromptsPanel > Static.title {
        height: 1;
        dock: top;
        background: $primary;
        color: $surface;
        content-align: center middle;
    }
    """
    
    def __init__(self, manager: PromptManager):
        super().__init__()
        self.manager = manager
    
    def compose(self):
        """Compose the prompt management panel."""
        # Title that doesn't block focus
        title = Static("[bold]🤖 PROMPT MANAGEMENT[/bold]", classes="title")
        yield title
        
        # Focusable components
        yield RoleSelector(self.manager)
        yield LanguageLearningPanel(self.manager)
        yield PromptStatusBar(self.manager)
    
    
    def get_effective_prompt(self) -> str:
        """Get the current effective system prompt."""
        return self.manager.get_effective_system_prompt()

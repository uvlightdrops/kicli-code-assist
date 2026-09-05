"""Prompt preview pane showing the current effective system prompt."""

from textual.widgets import Static
from rich.panel import Panel
from rich.syntax import Syntax
from kicli_code_assist.prompts import PromptManager


class PromptPreview(Static):
    """Display the current effective system prompt."""
    
    DEFAULT_CSS = """
    PromptPreview {
        height: 100%;
        width: 100%;
        border: solid $accent;
        overflow-y: auto;
    }
    """
    
    def __init__(self, manager: PromptManager):
        super().__init__()
        self.manager = manager
        self.update_display()
    
    def update_display(self) -> None:
        """Update the prompt preview."""
        prompt = self.manager.get_effective_system_prompt()
        
        # Add styling
        if not prompt:
            content = "[dim]No active prompt selected[/dim]"
        else:
            # Create syntax highlighting for the prompt
            syntax = Syntax(
                prompt,
                "markdown",
                theme="monokai",
                line_numbers=False,
                background_color="default",
            )
            content = syntax
        
        # Create panel with metadata
        active_role = self.manager.get_active_role()
        role_name = active_role.name if active_role else "None"
        
        ll = self.manager.prompts_config.language_learning
        ll_info = f"{ll.target_language} ({ll.level.value})" if ll.enabled else "Disabled"
        
        title = f"Current Prompt - Role: {role_name} | LL: {ll_info}"
        
        panel = Panel(
            content,
            title=title,
            expand=True,
            style="bold cyan",
        )
        
        self.update(panel)
    
    def on_prompt_changed(self, message) -> None:
        """Handle prompt change."""
        self.update_display()
    
    def on_language_learning_toggled(self, message) -> None:
        """Handle language learning toggle."""
        self.update_display()


class PromptInfo(Static):
    """Display detailed information about the current prompt."""
    
    DEFAULT_CSS = """
    PromptInfo {
        height: auto;
        width: 100%;
        border: solid $primary;
        padding: 1;
    }
    """
    
    def __init__(self, manager: PromptManager):
        super().__init__()
        self.manager = manager
        self.render_display()
    
    def render_display(self) -> None:
        """Render prompt information."""
        active_role = self.manager.get_active_role()
        
        if not active_role:
            content = "No active role selected"
        else:
            lines = [
                f"[bold]Role:[/bold] {active_role.name}",
                f"[bold]ID:[/bold] {active_role.id}",
                f"[bold]Version:[/bold] {active_role.version}",
                f"[bold]Enabled:[/bold] {'✅' if active_role.enabled else '❌'}",
            ]
            
            if active_role.description:
                lines.append(f"[bold]Description:[/bold] {active_role.description}")
            
            if active_role.tags:
                lines.append(f"[bold]Tags:[/bold] {', '.join(active_role.tags)}")
            
            # Language learning info
            ll = self.manager.prompts_config.language_learning
            if ll.enabled:
                lines.append("")
                lines.append(f"[bold yellow]🌍 Language Learning:[/bold yellow]")
                lines.append(f"   [yellow]Target:[/yellow] {ll.target_language}")
                lines.append(f"   [yellow]Level:[/yellow] {ll.level.value}")
                lines.append(f"   [yellow]Native:[/yellow] {ll.native_language}")
            
            content = "\n".join(lines)
        
        panel = Panel(
            content,
            title="📋 PROMPT INFO",
            expand=False,
            style="bold green",
        )
        
        self.update(panel)
    
    def on_prompt_changed(self, message) -> None:
        """Handle prompt change."""
        self.render_display()
    
    def on_language_learning_toggled(self, message) -> None:
        """Handle language learning toggle."""
        self.render_display()

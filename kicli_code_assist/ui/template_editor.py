"""Template editor modal for creating and editing custom prompts."""

from typing import Optional, Callable
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button, Input, Label, TextArea, Select
from textual.binding import Binding
from textual.message import Message
from rich.panel import Panel

from kicli_code_assist.prompts import PromptManager, CustomTemplate


class TemplateEditorMessage(Message):
    """Message when template is saved."""
    template: CustomTemplate


class TemplateEditor(Static):
    """Modal for editing custom prompt templates."""
    
    DEFAULT_CSS = """
    TemplateEditor {
        background: $boost;
        border: solid $accent;
        width: 90%;
        height: auto;
        offset: 5% 5%;
    }
    
    TemplateEditor Button {
        margin-left: 2;
        margin-right: 2;
    }
    """
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("ctrl+s", "save", "Save", show=True),
    ]
    
    def __init__(
        self,
        manager: PromptManager,
        template: Optional[CustomTemplate] = None,
        on_save: Optional[Callable] = None,
    ):
        super().__init__()
        self.manager = manager
        self.template = template
        self.on_save = on_save
        self.is_new = template is None
    
    def compose(self) -> ComposeResult:
        """Compose the template editor."""
        title = "New Template" if self.is_new else f"Edit: {self.template.name}"
        
        with Vertical():
            yield Label(f"[bold cyan]{title}[/bold cyan]")
            yield Label("")
            
            # Template ID (disabled if editing)
            yield Label("Template ID:")
            template_id = Input(
                value=self.template.id if self.template else "",
                id="template_id",
                disabled=not self.is_new,
            )
            yield template_id
            
            # Template Name
            yield Label("Name:")
            yield Input(
                value=self.template.name if self.template else "",
                id="template_name",
                placeholder="e.g., Python Debugging",
            )
            
            # Description
            yield Label("Description:")
            yield Input(
                value=self.template.description if self.template else "",
                id="template_description",
                placeholder="Short description of this template",
            )
            
            # Tags
            yield Label("Tags (comma-separated):")
            tags_str = ",".join(self.template.tags) if self.template else ""
            yield Input(
                value=tags_str,
                id="template_tags",
                placeholder="e.g., python, debugging, ai",
            )
            
            # System Prompt
            yield Label("System Prompt:")
            yield TextArea(
                text=self.template.system_prompt if self.template else "",
                id="template_prompt",
                theme="monokai",
                language="markdown",
            )
            
            yield Label("")
            
            # Buttons
            with Horizontal():
                yield Button("Save (Ctrl+S)", id="btn_save", variant="primary")
                yield Button("Cancel (Esc)", id="btn_cancel", variant="default")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn_save":
            self.action_save()
        elif event.button.id == "btn_cancel":
            self.action_cancel()
    
    def action_save(self) -> None:
        """Save the template."""
        try:
            template_id = self.query_one("#template_id", Input).value
            name = self.query_one("#template_name", Input).value
            description = self.query_one("#template_description", Input).value
            tags_str = self.query_one("#template_tags", Input).value
            prompt = self.query_one("#template_prompt", TextArea).text
            
            # Validate
            if not template_id or not name or not prompt:
                # Show error message
                return
            
            # Parse tags
            tags = [t.strip() for t in tags_str.split(",") if t.strip()]
            
            # Create or update template
            if self.is_new:
                template = CustomTemplate(
                    id=template_id,
                    name=name,
                    system_prompt=prompt,
                    description=description,
                    tags=tags,
                )
                self.manager.create_template(template)
            else:
                self.template.name = name
                self.template.system_prompt = prompt
                self.template.description = description
                self.template.tags = tags
                self.manager.update_template(self.template)
            
            # Notify parent
            if self.on_save:
                self.on_save(template if self.is_new else self.template)
            
            # Close modal
            self.remove()
        except Exception as e:
            # Show error
            pass
    
    def action_cancel(self) -> None:
        """Cancel editing."""
        self.remove()


class TemplateList(Static):
    """List of custom templates with management options."""
    
    DEFAULT_CSS = """
    TemplateList {
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    """
    
    BINDINGS = [
        Binding("n", "new_template", "New Template", show=True),
        Binding("e", "edit_template", "Edit", show=True),
        Binding("d", "delete_template", "Delete", show=True),
        Binding("up", "select_previous", "Previous", show=False),
        Binding("down", "select_next", "Next", show=False),
    ]
    
    def __init__(self, manager: PromptManager):
        super().__init__()
        self.manager = manager
        self.selected_index = 0
        self.templates_list = self.manager.list_templates()
        self.render_display()
    
    def render_display(self) -> None:
        """Render the template list."""
        self.templates_list = self.manager.list_templates()
        
        if not self.templates_list:
            content = "No custom templates (Press 'N' to create)"
        else:
            lines = []
            for i, template in enumerate(self.templates_list):
                marker = "●" if i == self.selected_index else "○"
                favorite = "⭐" if self.manager.is_favorite(template.id) else "  "
                line = f"{marker} {favorite} {template.name} ({template.id})"
                if template.description:
                    line += f"\n      {template.description}"
                lines.append(line)
            content = "\n".join(lines)
        
        panel = Panel(
            content,
            title="📦 CUSTOM TEMPLATES",
            expand=False,
            style="bold magenta",
        )
        
        self.update(panel)
    
    def action_new_template(self) -> None:
        """Create a new template."""
        # This would typically open the TemplateEditor modal
        pass
    
    def action_edit_template(self) -> None:
        """Edit the selected template."""
        if self.selected_index < len(self.templates_list):
            template = self.templates_list[self.selected_index]
            # Open TemplateEditor modal
            pass
    
    def action_delete_template(self) -> None:
        """Delete the selected template."""
        if self.selected_index < len(self.templates_list):
            template = self.templates_list[self.selected_index]
            self.manager.delete_template(template.id)
            self.render_display()
    
    def action_select_previous(self) -> None:
        """Move selection up."""
        if self.selected_index > 0:
            self.selected_index -= 1
            self.render_display()
    
    def action_select_next(self) -> None:
        """Move selection down."""
        if self.selected_index < len(self.templates_list) - 1:
            self.selected_index += 1
            self.render_display()

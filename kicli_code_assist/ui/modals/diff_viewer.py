"""Diff viewer modal for AI suggestions - shows unified diff."""

from textual.app import ComposeResult
from textual.widgets import Static, Button, Label
from textual.containers import Vertical, Horizontal
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import RichLog
import difflib


class DiffViewerModal(Screen):
    """Modal for viewing and applying AI suggestions diff."""
    
    CSS = """
    DiffViewerModal {
        align: center middle;
    }
    
    #diff_container {
        width: 95;
        height: 95%;
        border: heavy $primary;
        background: $surface;
    }
    
    #diff_header {
        width: 1fr;
        height: auto;
        padding: 1;
        background: $boost;
        border-bottom: solid $primary;
    }
    
    #diff_content {
        width: 1fr;
        height: 1fr;
    }
    
    RichLog {
        background: $panel;
    }
    
    #diff_footer {
        width: 1fr;
        height: auto;
        padding: 1;
        border-top: solid $primary;
        background: $panel;
    }
    
    #diff_footer Button {
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("enter", "apply", "Apply", show=True),
    ]
    
    def __init__(
        self,
        original_content: str,
        new_content: str,
        file_path: str,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.original_content = original_content
        self.new_content = new_content
        self.file_path = file_path
    
    def compose(self) -> ComposeResult:
        """Compose modal."""
        with Vertical(id="diff_container"):
            # Header
            with Static(id="diff_header"):
                yield Label(f"✓ Review Changes: {self.file_path}")
            
            # Diff content - RichLog directly
            self.diff_log = RichLog(highlight=False, markup=True, id="diff_content")
            yield self.diff_log
            
            # Footer with buttons
            with Horizontal(id="diff_footer"):
                yield Button("Cancel", id="btn-cancel", variant="error")
                yield Button("Apply", id="btn-apply", variant="primary")
    
    def on_mount(self) -> None:
        """Generate and display diff."""
        # Generate unified diff
        orig_lines = self.original_content.split("\n")
        new_lines = self.new_content.split("\n")
        
        diff = list(difflib.unified_diff(
            orig_lines,
            new_lines,
            fromfile=f"a/{self.file_path}",
            tofile=f"b/{self.file_path}",
            lineterm="",
            n=2,  # context lines
        ))
        
        if not diff:
            self.diff_log.write("[dim]No changes[/dim]\n")
            return
        
        # Format and color diff
        self.diff_log.write(f"[bold cyan]📄 {self.file_path}[/bold cyan]\n")
        self.diff_log.write("[dim]" + "─" * 60 + "[/dim]\n")
        
        for line in diff:
            if line.startswith("---"):
                self.diff_log.write(f"[dim]{line}[/dim]\n")
            elif line.startswith("+++"):
                self.diff_log.write(f"[dim]{line}[/dim]\n")
            elif line.startswith("@@"):
                self.diff_log.write(f"[yellow]{line}[/yellow]\n")
            elif line.startswith("+"):
                self.diff_log.write(f"[green]{line}[/green]\n")
            elif line.startswith("-"):
                self.diff_log.write(f"[red]{line}[/red]\n")
            else:
                self.diff_log.write(f"[dim]{line}[/dim]\n")
        
        self.diff_log.write(f"\n[dim]{'─' * 60}[/dim]\n")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "btn-apply":
            self.dismiss(self.new_content)
        elif event.button.id == "btn-cancel":
            self.dismiss(None)
    
    def action_apply(self) -> None:
        """Apply changes."""
        self.dismiss(self.new_content)
    
    def action_cancel(self) -> None:
        """Cancel changes."""
        self.dismiss(None)


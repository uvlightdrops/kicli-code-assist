"""Diff viewer modal for AI suggestions - shows side-by-side or unified diff."""

from textual.app import ComposeResult
from textual.widgets import Static, Button, Label, TabbedContent, TabPane
from textual.containers import Vertical, Horizontal, Container
from textual.binding import Binding
from textual.screen import Screen

from kicli_code_assist.ui.panels.chat_display import SelectableRichLog
from kicli_code_assist.approval_workflow import HunkStatus


class DiffLine(Static):
    """Single line in diff view with syntax highlighting."""
    
    def __init__(self, line_type: str, line_content: str, line_num: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.line_type = line_type  # "add", "remove", "context", "header"
        self.line_content = line_content
        self.line_num = line_num
    
    def render(self) -> str:
        """Render diff line with syntax highlighting."""
        # Add line numbers and color coding
        if self.line_type == "add":
            return f"[green]{self.line_num:4d} + {self.line_content}[/green]"
        elif self.line_type == "remove":
            return f"[red]{self.line_num:4d} - {self.line_content}[/red]"
        elif self.line_type == "header":
            return f"[bold cyan]{self.line_content}[/bold cyan]"
        else:  # context
            return f"[dim]{self.line_num:4d}   {self.line_content}[/dim]"


class DiffViewer(Static):
    """Shows unified diff for AI suggestions."""
    
    DEFAULT_CSS = """
    DiffViewer {
        width: 1fr;
        height: 1fr;
        border: solid $primary;
    }
    
    DiffViewer > SelectableRichLog {
        width: 1fr;
        height: 1fr;
        background: $panel;
    }
    """
    
    def __init__(self, original_content: str, new_content: str, file_path: str, **kwargs):
        super().__init__(**kwargs)
        self.original_content = original_content
        self.new_content = new_content
        self.file_path = file_path
    
    def compose(self) -> ComposeResult:
        """Compose diff viewer."""
        self.diff_log = SelectableRichLog(highlight=False, markup=True)
        yield self.diff_log
    
    def on_mount(self) -> None:
        """Generate and display diff."""
        import difflib
        
        # Generate unified diff
        orig_lines = self.original_content.split("\n")
        new_lines = self.new_content.split("\n")
        
        diff = difflib.unified_diff(
            orig_lines,
            new_lines,
            fromfile=f"a/{self.file_path}",
            tofile=f"b/{self.file_path}",
            lineterm="",
        )
        
        # Format and color diff
        self.diff_log.write(f"[bold cyan]📄 {self.file_path}[/bold cyan]\n")
        self.diff_log.write("[dim]" + "─" * 60 + "[/dim]\n")
        
        for i, line in enumerate(diff):
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


class DiffViewerModal(Screen):
    """Modal for viewing and applying AI suggestions diff."""
    
    CSS = """
    DiffViewerModal {
        align: center middle;
    }
    
    DiffViewerModal > Container {
        width: 95%;
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
        with Container():
            # Header
            with Static(id="diff_header"):
                yield Label(f"✓ Review Changes: {self.file_path}")
            
            # Diff content
            with Static(id="diff_content"):
                yield DiffViewer(
                    self.original_content,
                    self.new_content,
                    self.file_path,
                )
            
            # Footer with buttons
            with Horizontal(id="diff_footer"):
                yield Button("Cancel", id="btn-cancel", variant="error")
                yield Button("Apply Changes", id="btn-apply", variant="primary")
    
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

"""Shell command editor and manual entry widget for Textual TUI.

Allows users to:
1. Edit proposed commands from LLM
2. Manually enter new commands
3. Edit commands with syntax validation and risk re-classification
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Static, Button, Label, Input, RichLog, TextArea
from textual.screen import ModalScreen
from textual.binding import Binding
from textual.message import Message
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax

from kicli_code_assist.executor.shell_execution import (
    ShellCommand,
    ShellCommandBatch,
    RiskLevel,
    classify_risk,
)


@dataclass
class EditResult:
    """Result of command editing."""
    command: str
    description: str = ""
    cwd: Optional[str] = None
    timeout: Optional[int] = None
    new_risk_level: RiskLevel = field(default_factory=lambda: RiskLevel.MEDIUM)


class CommandEditor(ModalScreen):
    """Modal for editing a single shell command with risk preview.
    
    Features:
    - Text input for command
    - Description field
    - CWD field
    - Timeout field
    - Real-time risk re-classification
    - Syntax highlighting
    """
    
    CSS = """
    CommandEditor {
        align: center middle;
        background: $surface 50%;
    }
    
    CommandEditor > Vertical {
        width: 80;
        height: 30;
        border: solid $primary;
        background: $panel;
        padding: 1 2;
    }
    
    #editor-header {
        height: 2;
        border-bottom: solid $primary;
        padding: 0 0 1 0;
    }
    
    #editor-body {
        height: 1fr;
        padding: 1 0;
    }
    
    #editor-footer {
        height: 4;
        border-top: solid $primary;
        padding: 1 0 0 0;
    }
    
    #risk-preview {
        padding: 1;
        border: solid $warning;
        margin: 1 0;
    }
    
    .risk-critical {
        background: $error;
        color: white;
        text-style: bold;
    }
    
    .risk-high {
        background: $warning;
        color: black;
    }
    
    .risk-medium {
        background: $yellow;
        color: black;
    }
    
    .risk-low {
        background: $success;
        color: black;
    }
    
    Input {
        margin: 0 0 1 0;
    }
    
    Button {
        margin-right: 1;
    }
    """
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("ctrl+s", "save", "Save", show=True),
    ]
    
    def __init__(self, initial_command: ShellCommand):
        super().__init__()
        self.initial_command = initial_command
        self.current_risk = initial_command.get_risk_level()
        
        # UI widgets
        self.command_input: Optional[Input] = None
        self.description_input: Optional[Input] = None
        self.cwd_input: Optional[Input] = None
        self.timeout_input: Optional[Input] = None
        self.risk_display: Optional[RichLog] = None
    
    def compose(self) -> ComposeResult:
        """Create editor UI."""
        with Vertical():
            # Header
            with Vertical(id="editor-header"):
                yield Label("[bold]✎ Edit Shell Command[/]")
            
            # Body
            with VerticalScroll(id="editor-body"):
                yield Label("[bold cyan]Command:[/]")
                self.command_input = Input(value=self.initial_command.command)
                self.command_input.name = "command_input"
                yield self.command_input
                
                yield Label("[bold cyan]Description (optional):[/]")
                self.description_input = Input(
                    value=self.initial_command.description or ""
                )
                self.description_input.name = "description_input"
                yield self.description_input
                
                yield Label("[bold cyan]Working Directory (optional):[/]")
                self.cwd_input = Input(value=self.initial_command.cwd or "")
                self.cwd_input.name = "cwd_input"
                yield self.cwd_input
                
                yield Label("[bold cyan]Timeout in seconds (optional):[/]")
                self.timeout_input = Input(
                    value=str(self.initial_command.timeout or "30")
                )
                self.timeout_input.name = "timeout_input"
                yield self.timeout_input
                
                # Risk preview
                yield Label("[bold cyan]Risk Level (auto-updated):[/]")
                self.risk_display = RichLog(id="risk-preview", height=3)
                yield self.risk_display
                self._update_risk_preview()
            
            # Footer with buttons
            with Horizontal(id="editor-footer"):
                yield Button("Save [Ctrl+S]", id="save-btn", variant="primary")
                yield Button("Cancel [Esc]", id="cancel-btn", variant="error")
    
    def on_mount(self) -> None:
        """Set focus to command input."""
        if self.command_input:
            self.command_input.focus()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Update risk preview when command changes."""
        if event.input.name == "command_input":
            self._update_risk_preview()
    
    def _update_risk_preview(self) -> None:
        """Re-classify and display risk level."""
        if not self.command_input or not self.risk_display:
            return
        
        cmd_text = self.command_input.value.strip()
        if not cmd_text:
            self.risk_display.write("[yellow]⚠️  Enter a command[/]")
            return
        
        self.current_risk = classify_risk(cmd_text)
        
        # Color code by risk
        risk_colors = {
            RiskLevel.LOW: "🟢 LOW - Safe command",
            RiskLevel.MEDIUM: "🟡 MEDIUM - Review before execution",
            RiskLevel.HIGH: "🟠 HIGH - Risky operation, requires approval",
            RiskLevel.CRITICAL: "🔴 CRITICAL - Dangerous! Proceed with caution",
        }
        
        risk_text = risk_colors.get(self.current_risk, "Unknown")
        
        self.risk_display.clear()
        self.risk_display.write(f"[bold]{risk_text}[/]")
    
    def action_save(self) -> None:
        """Save edited command."""
        if not self.command_input or not self.command_input.value.strip():
            self.command_input.focus()
            return
        
        try:
            timeout = None
            if self.timeout_input and self.timeout_input.value.strip():
                timeout = int(self.timeout_input.value.strip())
        except ValueError:
            timeout = 30
        
        result = EditResult(
            command=self.command_input.value.strip(),
            description=self.description_input.value.strip() if self.description_input else "",
            cwd=self.cwd_input.value.strip() if self.cwd_input and self.cwd_input.value.strip() else None,
            timeout=timeout,
            new_risk_level=self.current_risk,
        )
        
        self.app.pop_screen(result)
    
    def action_cancel(self) -> None:
        """Cancel editing."""
        self.app.pop_screen(None)


class CommandManualEntryDialog(ModalScreen):
    """Modal for manually entering shell commands.
    
    Features:
    - Single or multiple command entry
    - Line-by-line or multi-line mode
    - Risk preview
    - Quick templates
    """
    
    CSS = """
    CommandManualEntryDialog {
        align: center middle;
        background: $surface 50%;
    }
    
    CommandManualEntryDialog > Vertical {
        width: 85;
        height: 32;
        border: solid $primary;
        background: $panel;
        padding: 1 2;
    }
    
    #entry-header {
        height: 2;
        border-bottom: solid $primary;
        padding: 0 0 1 0;
    }
    
    #entry-body {
        height: 1fr;
        padding: 1 0;
    }
    
    #entry-footer {
        height: 3;
        border-top: solid $primary;
        padding: 1 0 0 0;
    }
    
    TextArea {
        height: 1fr;
        border: solid $accent;
        background: $surface;
    }
    
    Button {
        margin-right: 1;
    }
    """
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("ctrl+enter", "submit", "Submit", show=True),
    ]
    
    def __init__(self):
        super().__init__()
        self.text_area: Optional[TextArea] = None
    
    def compose(self) -> ComposeResult:
        """Create manual entry UI."""
        with Vertical():
            # Header
            with Vertical(id="entry-header"):
                yield Label("[bold]➕ Enter Shell Commands Manually[/]")
                yield Label("[dim]One command per line, or paste multi-line script (Ctrl+Enter to submit)[/]")
            
            # Body
            with Vertical(id="entry-body"):
                self.text_area = TextArea(language="bash")
                self.text_area.name = "command_text_area"
                yield self.text_area
            
            # Footer
            with Horizontal(id="entry-footer"):
                yield Button("Submit [Ctrl+Enter]", id="submit-btn", variant="primary")
                yield Button("Cancel [Esc]", id="cancel-btn", variant="error")
    
    def on_mount(self) -> None:
        """Focus text area."""
        if self.text_area:
            self.text_area.focus()
    
    def action_submit(self) -> None:
        """Parse and submit commands."""
        if not self.text_area:
            return
        
        text = self.text_area.text.strip()
        if not text:
            return
        
        # Parse lines as separate commands
        commands = []
        for line in text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):  # Skip empty lines and comments
                cmd = ShellCommand(
                    command=line,
                    description="Manually entered command"
                )
                commands.append(cmd)
        
        if commands:
            batch = ShellCommandBatch(commands=commands)
            self.app.pop_screen(batch)
        else:
            self.app.pop_screen(None)
    
    def action_cancel(self) -> None:
        """Cancel entry."""
        self.app.pop_screen(None)


class CommandBatchEditorPanel(Static):
    """Panel for editing multiple commands in a batch.
    
    Allows:
    - Viewing all commands with risks
    - Clicking to edit individual commands
    - Adding new commands
    - Removing commands
    - Reordering commands
    """
    
    def __init__(self, batch: ShellCommandBatch):
        super().__init__()
        self.batch = batch
        self.selected_index = 0
    
    def render(self) -> str:
        """Render batch edit panel."""
        lines = ["[bold cyan]Commands in Batch:[/]"]
        
        for i, cmd in enumerate(self.batch.commands):
            risk_emoji = self._risk_emoji(cmd.get_risk_level())
            selected = "[inverse]" if i == self.selected_index else ""
            prefix = "[green]→[/]" if i == self.selected_index else " "
            
            lines.append(
                f"{prefix} {selected}[{i}] {risk_emoji} {cmd.command[:50]}"
            )
        
        lines.append("")
        lines.append("[dim][e]dit | [a]dd | [d]elete | [↑↓]move | [Enter]confirm[/]")
        
        return "\n".join(lines)
    
    def _risk_emoji(self, risk: RiskLevel) -> str:
        """Get emoji for risk level."""
        emojis = {
            RiskLevel.LOW: "🟢",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.HIGH: "🟠",
            RiskLevel.CRITICAL: "🔴",
        }
        return emojis.get(risk, "⚪")
    
    def on_key(self, event) -> None:
        """Handle keyboard input for batch editing."""
        if event.key == "up":
            if self.selected_index > 0:
                self.selected_index -= 1
                self.refresh()
        elif event.key == "down":
            if self.selected_index < len(self.batch.commands) - 1:
                self.selected_index += 1
                self.refresh()
        elif event.key == "e":  # Edit
            # Emit message to parent to show editor
            self.post_message(self.CommandEditRequested(self.selected_index))
        elif event.key == "a":  # Add
            self.post_message(self.CommandAddRequested())
        elif event.key == "d":  # Delete
            if len(self.batch.commands) > 1:
                self.batch.commands.pop(self.selected_index)
                if self.selected_index >= len(self.batch.commands):
                    self.selected_index -= 1
                self.refresh()
    
    class CommandEditRequested(Message):
        """Request to edit command at index."""
        def __init__(self, index: int) -> None:
            self.index = index
            super().__init__()
    
    class CommandAddRequested(Message):
        """Request to add new command."""
        pass

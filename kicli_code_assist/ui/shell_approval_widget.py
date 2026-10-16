"""Shell command approval widget for Textual TUI.

Interactive modal dialog for approving/editing/executing shell command batches
with human-in-the-loop (HITL) guardrails.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Static, Button, Label, RichLog, Switch
from textual.screen import ModalScreen
from textual.message import Message
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax

from kicli_code_assist.executor.shell_execution import (
    ShellCommandBatch,
    RiskLevel,
    SessionPermissionLevel,
)


@dataclass
class ApprovalResult:
    """Result of approval dialog."""
    
    approved: bool
    session_mode: bool = False  # User selected "auto-approve for session"
    edited_commands: Optional[list] = None


class ShellCommandApprovalModal(ModalScreen):
    """Modal dialog for approving shell command batches.
    
    Displays:
    - Batch description and command count
    - Risk level with color coding
    - List of commands with syntax highlighting
    - Buttons: Execute | Skip | Edit | Auto-Approve for Session
    - Toggle switch for session mode
    """
    
    CSS = """
    ShellCommandApprovalModal {
        align: center middle;
        background: $surface 50%;
    }
    
    ShellCommandApprovalModal > Vertical {
        width: 90;
        height: 35;
        border: solid $primary;
        background: $panel;
        padding: 1 2;
    }
    
    #approval-header {
        dock: top;
        height: 3;
        border-bottom: solid $primary;
        padding: 0 0 1 0;
    }
    
    #commands-scroll {
        height: 1fr;
        border-bottom: solid $primary;
        padding: 1 0;
    }
    
    #approval-footer {
        dock: bottom;
        height: 3;
        padding: 1 0 0 0;
    }
    
    #commands-display {
        padding: 0 1;
    }
    
    #risk-level {
        padding: 0 1;
        width: 100%;
    }
    
    #risk-critical {
        background: $error;
    }
    
    #risk-high {
        background: $warning;
    }
    
    #risk-medium {
        background: $warning;
    }
    
    #risk-low {
        background: $success;
    }
    
    #session-mode-container {
        height: 1;
        padding: 0 1;
    }
    
    #button-container {
        height: 1;
        width: 100%;
        padding: 1 0;
    }
    
    #button-container Button {
        margin-right: 1;
    }
    """
    
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]
    
    def __init__(self, command_batch: ShellCommandBatch):
        """Initialize approval modal.
        
        Args:
            command_batch: ShellCommandBatch to approve
        """
        super().__init__()
        self.command_batch = command_batch
        self.result: Optional[ApprovalResult] = None
    
    def compose(self) -> ComposeResult:
        """Compose widget tree."""
        with Vertical():
            # Header with title and batch info
            with Static(id="approval-header"):
                yield Label(f"🔐 Approve Shell Command Execution")
                yield Label(
                    f"Batch: {self.command_batch.id} | "
                    f"{len(self.command_batch.commands)} command(s)"
                )
            
            # Risk level indicator
            risk = self.command_batch.calculate_risk()
            risk_colors = {
                RiskLevel.CRITICAL: "#ff0000",
                RiskLevel.HIGH: "#ff8800",
                RiskLevel.MEDIUM: "#ffff00",
                RiskLevel.LOW: "#00ff00",
            }
            risk_labels = {
                RiskLevel.CRITICAL: "🔴 CRITICAL RISK",
                RiskLevel.HIGH: "🟠 HIGH RISK",
                RiskLevel.MEDIUM: "🟡 MEDIUM RISK",
                RiskLevel.LOW: "🟢 LOW RISK",
            }
            with Static(id=f"risk-{risk.value}", classes="risk-indicator"):
                yield Label(risk_labels[risk])
            
            # Commands display
            with VerticalScroll(id="commands-scroll"):
                with Static(id="commands-display"):
                    for i, cmd in enumerate(self.command_batch.commands, 1):
                        cmd_risk = cmd.classify_risk()
                        risk_indicator = {
                            RiskLevel.CRITICAL: "🔴",
                            RiskLevel.HIGH: "🟠",
                            RiskLevel.MEDIUM: "🟡",
                            RiskLevel.LOW: "🟢",
                        }[cmd_risk]
                        
                        # Command with description
                        yield Label(
                            f"{i}. {risk_indicator} {cmd.description or cmd.command}"
                        )
                        # Syntax-highlighted command
                        yield Static(
                            Syntax(
                                cmd.command,
                                "bash",
                                line_numbers=False,
                                theme="monokai",
                            ),
                            classes="command-syntax",
                        )
            
            # Session mode toggle
            with Horizontal(id="session-mode-container"):
                yield Label("Auto-approve for session:")
                yield Switch(
                    id="session-mode-switch",
                    value=False,
                )
            
            # Action buttons
            with Horizontal(id="button-container"):
                yield Button("Execute Batch", id="btn-execute", variant="primary")
                yield Button("Skip", id="btn-skip", variant="warning")
                yield Button("Edit Commands", id="btn-edit", variant="default")
                yield Button("Add Manual Command", id="btn-add-manual", variant="default")
                yield Button("Cancel", id="btn-cancel", variant="error")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        button_id = event.button.id
        session_mode = self.query_one("#session-mode-switch", Switch).value
        
        if button_id == "btn-execute":
            self.result = ApprovalResult(
                approved=True,
                session_mode=session_mode,
            )
            self.app.pop_screen()
        elif button_id == "btn-skip":
            self.result = ApprovalResult(
                approved=False,
                session_mode=False,
            )
            self.app.pop_screen()
        elif button_id == "btn-edit":
            # Emit message to parent to handle editing
            self.post_message(self.EditCommandsRequested(self.command_batch))
        elif button_id == "btn-add-manual":
            # Emit message to parent to handle manual entry
            self.post_message(self.AddManualCommandRequested())
        elif button_id == "btn-cancel":
            self.result = ApprovalResult(
                approved=False,
                session_mode=False,
            )
            self.app.pop_screen()
    
    def update_batch(self, batch: ShellCommandBatch) -> None:
        """Update the command batch after editing.
        
        Args:
            batch: Updated batch
        """
        self.command_batch = batch
        self.refresh()
    
    def action_cancel(self) -> None:
        """Cancel approval."""
        self.result = ApprovalResult(
            approved=False,
            session_mode=False,
        )
        self.app.pop_screen()


# For use in chat app - message when commands are approved
class CommandsApprovalRequested(Message):
    """Posted when LLM proposes commands needing approval."""
    
    def __init__(self, batch: ShellCommandBatch) -> None:
        self.batch = batch
        super().__init__()


class CommandsExecuted(Message):
    """Posted when commands have been executed."""
    
    def __init__(self, batch_id: str, results: list) -> None:
        self.batch_id = batch_id
        self.results = results
        super().__init__()


class CommandsSkipped(Message):
    """Posted when user skipped command execution."""
    
    def __init__(self, batch_id: str) -> None:
        self.batch_id = batch_id
        super().__init__()


class EditCommandsRequested(Message):
    """Posted when user clicks Edit button."""
    
    def __init__(self, batch: ShellCommandBatch) -> None:
        self.batch = batch
        super().__init__()


class AddManualCommandRequested(Message):
    """Posted when user clicks Add Manual Command button."""
    pass

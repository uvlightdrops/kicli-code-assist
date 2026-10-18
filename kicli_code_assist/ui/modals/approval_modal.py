"""Approval modal for AI suggestions in Textual UI."""

from typing import Optional, Callable
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static, Button, Label, Checkbox
from textual.screen import ModalScreen

from kicli_code_assist.approval_workflow import (
    CodeHunk,
    ApprovalSession,
    HunkStatus,
)


class HunkApprovalWidget(Static):
    """Widget for approving/rejecting a single hunk."""

    def __init__(
        self,
        hunk: CodeHunk,
        hunk_index: int,
        on_approve: Callable,
        on_reject: Callable,
    ):
        super().__init__()
        self.hunk = hunk
        self.hunk_index = hunk_index
        self.on_approve = on_approve
        self.on_reject = on_reject

    def render(self) -> str:
        """Render hunk preview."""
        status_emoji = {
            HunkStatus.APPROVED: "✓",
            HunkStatus.REJECTED: "✗",
            HunkStatus.PENDING: "?",
            HunkStatus.PARTIAL: "~",
        }.get(self.hunk.status, " ")

        approval_pct = self.hunk.get_approval_percentage()

        return f"""
{status_emoji} {self.hunk.file_path}:{self.hunk.start_line}-{self.hunk.end_line}
Status: {self.hunk.status.value} | Approval: {approval_pct:.0f}%

Changes:
"""

    def compose(self) -> ComposeResult:
        """Compose hunk approval UI."""
        # Show hunk header
        yield Label(f"{self.hunk.file_path}:{self.hunk.start_line}-{self.hunk.end_line}")

        # Show each line with checkbox
        with ScrollableContainer(id=f"hunk-{self.hunk_index}"):
            for line in self.hunk.lines:
                status_marker = "✓" if line.status == HunkStatus.APPROVED else "✗" if line.status == HunkStatus.REJECTED else "○"
                yield Label(f"{status_marker} {line.line_number}: {line.modified_line[:60]}")

        # Buttons for hunk approval
        with Horizontal():
            yield Button("Approve Hunk", id=f"approve-{self.hunk_index}", variant="success")
            yield Button("Reject Hunk", id=f"reject-{self.hunk_index}", variant="error")
            yield Button("Details", id=f"details-{self.hunk_index}", variant="default")


class ApprovalModal(ModalScreen[Optional[ApprovalSession]]):
    """Modal for approving AI-generated code changes.

    This modal displays hunks of code changes and allows line-by-line
    or hunk-level approval/rejection.
    """

    BINDINGS = [
        ("escape", "dismiss", "Cancel"),
        ("enter", "approve_all", "Approve All"),
        ("ctrl+r", "reject_all", "Reject All"),
    ]

    DEFAULT_CSS = """
    ApprovalModal {
        align: center middle;
        layer: modals;
    }

    ApprovalModal > Vertical {
        width: 120;
        height: 35;
        border: solid $accent;
        background: $surface;
        layout: vertical;
    }

    ApprovalModal #title {
        width: 1fr;
        height: auto;
        text-align: center;
        text-style: bold;
    }

    ApprovalModal #summary {
        width: 1fr;
        height: auto;
        padding: 0 2;
        text-align: center;
    }

    ApprovalModal #hunks-container {
        width: 1fr;
        height: 1fr;
        border: dashed $primary;
        overflow-y: auto;
    }

    ApprovalModal #hunk-widget {
        width: 1fr;
        height: auto;
        border: dashed $secondary;
        margin: 1 1;
    }

    ApprovalModal #button-panel {
        width: 1fr;
        height: auto;
        border-top: solid $accent;
        padding: 1 2;
        layout: horizontal;
    }

    ApprovalModal #approval-stats {
        width: 1fr;
        text-align: center;
    }
    
    ApprovalModal [id*="hunk-content"] {
        width: 1fr;
        height: auto;
        max-height: 8;
        overflow-y: auto;
        border: solid $panel;
        margin: 1 0;
    }
    
    ApprovalModal [id*="hunk-text"] {
        width: 1fr;
        height: auto;
    }
    """

    def __init__(self, session: ApprovalSession):
        super().__init__()
        self.session = session

    def compose(self) -> ComposeResult:
        """Compose approval modal."""
        with Vertical():
            yield Label("AI Suggestions Approval", id="title")

            # Summary stats
            summary = self.session.get_summary()
            yield Label(
                f"Hunks: {summary['approved']}/{summary['total_hunks']} approved | "
                f"Overall: {summary['overall_approval']}",
                id="summary",
            )

            # Hunks container
            with ScrollableContainer(id="hunks-container"):
                for idx, hunk in enumerate(self.session.hunks):
                    with Vertical(id=f"hunk-widget"):
                        # Hunk header
                        status_emoji = {
                            HunkStatus.APPROVED: "✓",
                            HunkStatus.REJECTED: "✗",
                            HunkStatus.PENDING: "?",
                            HunkStatus.PARTIAL: "~",
                        }.get(hunk.status, " ")

                        header_text = f"{status_emoji} {hunk.file_path}:{hunk.start_line}-{hunk.end_line}"
                        yield Label(header_text)

                        # Show preview of changes in a scrollable container
                        preview_lines = []
                        for line in hunk.lines:
                            preview_lines.append(f"  {line.modified_line[:70]}")

                        preview_text = "\n".join(preview_lines)
                        
                        from textual.widgets import Static
                        with ScrollableContainer(id=f"hunk-content-{idx}"):
                            yield Static(preview_text, id=f"hunk-text-{idx}")

                        # Approval buttons for this hunk
                        with Horizontal():
                            yield Button(
                                "✓ Approve",
                                id=f"approve-{idx}",
                                variant="success",
                            )
                            yield Button(
                                "✗ Reject",
                                id=f"reject-{idx}",
                                variant="error",
                            )
                            yield Button(
                                "Details",
                                id=f"details-{idx}",
                                variant="default",
                            )

            # Bottom panel
            with Horizontal(id="button-panel"):
                yield Label(id="approval-stats")
                yield Button("✓ Apply Approved", id="apply", variant="success")
                yield Button("✗ Discard All", id="discard", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "apply":
            self.dismiss(self.session)
        elif button_id == "discard":
            self.dismiss(None)
        elif button_id and button_id.startswith("approve-"):
            idx = int(button_id.split("-")[1])
            self.session.approve_hunk(idx)
            self._update_summary()
            self.refresh()
        elif button_id and button_id.startswith("reject-"):
            idx = int(button_id.split("-")[1])
            self.session.reject_hunk(idx)
            self._update_summary()
            self.refresh()
        elif button_id and button_id.startswith("details-"):
            idx = int(button_id.split("-")[1])
            self._show_hunk_details(idx)

    def action_approve_all(self) -> None:
        """Approve all hunks."""
        for hunk in self.session.hunks:
            hunk.approve_all()
        self._update_summary()
        self.refresh()

    def action_reject_all(self) -> None:
        """Reject all hunks."""
        for hunk in self.session.hunks:
            hunk.reject_all()
        self._update_summary()
        self.refresh()

    def _update_summary(self) -> None:
        """Update summary label."""
        summary = self.session.get_summary()
        summary_widget = self.query_one("#approval-stats", Label)
        summary_widget.update(
            f"Hunks: {summary['approved']}/{summary['total_hunks']} approved | "
            f"Overall: {summary['overall_approval']}"
        )

    def _show_hunk_details(self, hunk_index: int) -> None:
        """Show detailed view of single hunk (could open another modal)."""
        # TODO: Implement detail modal with line-by-line approval
        pass

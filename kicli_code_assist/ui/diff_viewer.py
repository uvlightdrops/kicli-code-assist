"""Diff viewer widgets for reviewing code changes."""

from typing import List, Optional, Tuple
from dataclasses import dataclass
from textual.app import ComposeResult
from textual.widgets import Static, Button
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from kicli_code_assist.context.diff_engine import FileDiff


@dataclass
class DiffViewerState:
    """State of diff viewer."""
    diffs: List[FileDiff]
    current_index: int = 0
    applied_indices: set = None
    rejected_indices: set = None

    def __post_init__(self):
        """Initialize sets."""
        if self.applied_indices is None:
            self.applied_indices = set()
        if self.rejected_indices is None:
            self.rejected_indices = set()


class DiffDisplay(Static):
    """Display a single diff with syntax highlighting."""

    DEFAULT_CSS = """
    DiffDisplay {
        width: 100%;
        height: auto;
        border: solid $accent;
        overflow: auto;
    }
    """

    def __init__(self, diff: FileDiff, config):
        """Initialize diff display.

        Args:
            diff: FileDiff to display
            config: Configuration object
        """
        super().__init__()
        self.diff = diff
        self.config = config

    def render(self) -> str:
        """Render diff with color coding."""
        output = []
        unified = self.diff.to_unified_diff(
            context_lines=self.config.diff_context_lines
        )

        for line in unified.split("\n"):
            if line.startswith("+++") or line.startswith("---"):
                # File headers in cyan
                output.append(f"[cyan]{line}[/cyan]")
            elif line.startswith("+"):
                # Added lines in green
                output.append(f"[green]{line}[/green]")
            elif line.startswith("-"):
                # Removed lines in red
                output.append(f"[red]{line}[/red]")
            elif line.startswith("@@"):
                # Hunk headers in yellow
                output.append(f"[yellow]{line}[/yellow]")
            else:
                # Context lines normal
                output.append(line)

        return "\n".join(output)


class DiffViewerHeader(Static):
    """Header showing diff metadata."""

    DEFAULT_CSS = """
    DiffViewerHeader {
        width: 100%;
        height: 3;
        border: solid $accent;
        background: $panel;
    }
    """

    def __init__(self, state: DiffViewerState, config):
        """Initialize header.

        Args:
            state: DiffViewerState
            config: Configuration object
        """
        super().__init__()
        self.state = state
        self.config = config

    def render(self) -> str:
        """Render header with diff info."""
        if not self.state.diffs:
            return "No diffs"

        diff = self.state.diffs[self.state.current_index]
        idx = self.state.current_index + 1
        total = len(self.state.diffs)

        # Confidence indicator
        confidence = diff.similarity
        confidence_status = "✅ Auto-apply" if confidence > 0.75 else "⚠️ Review"

        # Status indicator
        if self.state.current_index in self.state.applied_indices:
            status = "[green]✅ APPLIED[/green]"
        elif self.state.current_index in self.state.rejected_indices:
            status = "[red]❌ REJECTED[/red]"
        else:
            status = "[yellow]⏳ PENDING[/yellow]"

        return (
            f"📝 Diff {idx}/{total} | {diff.file_path}\n"
            f"Confidence: {confidence:.0%} | {confidence_status} | Status: {status}\n"
            f"Changes: +{len([c for c in diff.get_changes() if c.type == 'added'])} "
            f"-{len([c for c in diff.get_changes() if c.type == 'removed'])}"
        )


class DiffViewerFooter(Static):
    """Footer showing keybindings."""

    DEFAULT_CSS = """
    DiffViewerFooter {
        width: 100%;
        height: 2;
        border: solid $accent;
        background: $panel;
    }
    """

    def render(self) -> str:
        """Render footer with keybindings."""
        return (
            "[b]j[/b]=Next  [b]k[/b]=Prev  [b]a[/b]=Apply  [b]r[/b]=Reject  "
            "[b]A[/b]=Apply All  [b]q[/b]=Close"
        )


class DiffPanel(Container):
    """Full diff review panel with navigation and actions."""

    DEFAULT_CSS = """
    DiffPanel {
        width: 100%;
        height: 100%;
        border: solid $accent;
        background: $panel;
    }
    """

    def __init__(self, diffs: List[FileDiff], config):
        """Initialize diff panel.

        Args:
            diffs: List of FileDiff objects
            config: Configuration object
        """
        super().__init__()
        self.config = config
        self.state = DiffViewerState(diffs=diffs)
        self.on_diff_applied = None
        self.on_diff_rejected = None

    def compose(self) -> ComposeResult:
        """Compose diff panel."""
        yield DiffViewerHeader(self.state, self.config)
        if self.state.diffs:
            yield DiffDisplay(
                self.state.diffs[self.state.current_index],
                self.config,
                id="diff-display",
            )
        yield DiffViewerFooter()

    def on_mount(self) -> None:
        """Handle mount."""
        self.focus()

    def on_key(self, event) -> None:
        """Handle key press.

        Args:
            event: Key event
        """
        if not self.state.diffs:
            return

        if event.key == "j":
            self.navigate_next()
        elif event.key == "k":
            self.navigate_prev()
        elif event.key == "a":
            self.apply_current()
        elif event.key == "r":
            self.reject_current()
        elif event.key == "A":
            self.apply_all()
        elif event.key == "q":
            self.remove()

    def navigate_next(self) -> None:
        """Navigate to next diff."""
        if self.state.current_index < len(self.state.diffs) - 1:
            self.state.current_index += 1
            self.refresh_view()

    def navigate_prev(self) -> None:
        """Navigate to previous diff."""
        if self.state.current_index > 0:
            self.state.current_index -= 1
            self.refresh_view()

    def apply_current(self) -> None:
        """Apply current diff."""
        if self.state.current_index not in self.state.rejected_indices:
            self.state.applied_indices.add(self.state.current_index)
            if self.on_diff_applied:
                diff = self.state.diffs[self.state.current_index]
                self.on_diff_applied(self.state.current_index, diff)
            self.refresh_view()

    def reject_current(self) -> None:
        """Reject current diff."""
        if self.state.current_index not in self.state.applied_indices:
            self.state.rejected_indices.add(self.state.current_index)
            if self.on_diff_rejected:
                diff = self.state.diffs[self.state.current_index]
                self.on_diff_rejected(self.state.current_index, diff)
            self.refresh_view()

    def apply_all(self) -> None:
        """Apply all diffs."""
        for i, diff in enumerate(self.state.diffs):
            if i not in self.state.rejected_indices:
                self.state.applied_indices.add(i)
                if self.on_diff_applied:
                    self.on_diff_applied(i, diff)
        self.refresh_view()

    def reject_all(self) -> None:
        """Reject all diffs."""
        for i, diff in enumerate(self.state.diffs):
            if i not in self.state.applied_indices:
                self.state.rejected_indices.add(i)
                if self.on_diff_rejected:
                    self.on_diff_rejected(i, diff)
        self.refresh_view()

    def refresh_view(self) -> None:
        """Refresh display with current diff."""
        if not self.state.diffs:
            return

        # Update header
        try:
            header = self.query_one(DiffViewerHeader)
            header.refresh()
        except Exception:
            pass

        # Update display
        try:
            display = self.query_one("#diff-display", expect_type=DiffDisplay)
            display.diff = self.state.diffs[self.state.current_index]
            display.refresh()
        except Exception:
            pass

    def get_applied_diffs(self) -> List[Tuple[int, FileDiff]]:
        """Get list of applied diffs.

        Returns:
            List of (index, FileDiff) tuples
        """
        return [
            (i, self.state.diffs[i]) for i in self.state.applied_indices
        ]

    def get_rejected_diffs(self) -> List[Tuple[int, FileDiff]]:
        """Get list of rejected diffs.

        Returns:
            List of (index, FileDiff) tuples
        """
        return [
            (i, self.state.diffs[i]) for i in self.state.rejected_indices
        ]

    def get_summary(self) -> dict:
        """Get summary of diff results.

        Returns:
            Summary dict with counts
        """
        return {
            "total": len(self.state.diffs),
            "applied": len(self.state.applied_indices),
            "rejected": len(self.state.rejected_indices),
            "pending": (
                len(self.state.diffs)
                - len(self.state.applied_indices)
                - len(self.state.rejected_indices)
            ),
        }

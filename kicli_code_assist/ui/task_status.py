"""Task status display widgets."""

from typing import Optional
from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Container, Vertical
from kicli_code_assist.executor.task_tracker import TaskTracker, TaskStatus


class TaskStatusCompact(Static):
    """Compact task status for status bar."""

    DEFAULT_CSS = """
    TaskStatusCompact {
        width: 100%;
        height: 1;
        background: $panel;
    }
    """

    def __init__(self, tracker: TaskTracker):
        """Initialize compact status.

        Args:
            tracker: TaskTracker instance
        """
        super().__init__()
        self.tracker = tracker

    def on_mount(self) -> None:
        """Set up auto-refresh when mounted."""
        self.set_interval(0.2, self.refresh)

    def render(self) -> str:
        """Render compact status."""
        summary = self.tracker.get_summary()
        
        return (
            f"📊 Tasks: {summary['active']} active | "
            f"{summary['completed']} done | "
            f"{summary['completion_rate']:.0f}%"
        )


class TaskDetailLine(Static):
    """Single line in task detail panel."""

    def __init__(self, task_id: str, task):
        """Initialize detail line.

        Args:
            task_id: Task identifier
            task: Task object
        """
        super().__init__()
        self.task_id = task_id
        self._task = task

    @property
    def task(self):
        """Get task."""
        return self._task

    def render(self) -> str:
        """Render task detail line."""
        # Status icon
        status_icons = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.IN_PROGRESS: "🔄",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.CANCELLED: "⚠️",
        }
        icon = status_icons.get(self.task.status, "?")

        # Elapsed time
        elapsed = f"({self.task.metrics.elapsed_ms():.0f}ms)"

        return f"{icon} {self.task.description} {elapsed}"


class TaskDetailPanel(Static):
    """Detailed task hierarchy view."""

    DEFAULT_CSS = """
    TaskDetailPanel {
        width: 100%;
        height: auto;
        border: solid $accent;
        background: $panel;
        overflow: auto;
    }
    """

    def __init__(self, tracker: TaskTracker):
        """Initialize detail panel.

        Args:
            tracker: TaskTracker instance
        """
        super().__init__()
        self.tracker = tracker

    def on_mount(self) -> None:
        """Set up auto-refresh when mounted."""
        self.set_interval(0.3, self.refresh)

    def render(self) -> str:
        """Render task hierarchy."""
        output = []
        tree = self.tracker.get_task_tree()

        if not tree:
            return "No tasks"

        for parent_id, parent_task in tree.items():
            # Parent task
            status_icons = {
                TaskStatus.PENDING: "⏳",
                TaskStatus.IN_PROGRESS: "🔄",
                TaskStatus.COMPLETED: "✅",
                TaskStatus.FAILED: "❌",
                TaskStatus.CANCELLED: "⚠️",
            }
            icon = status_icons.get(parent_task.status, "?")
            parent_line = f"[bold]{icon} {parent_task.description}[/bold]"
            output.append(parent_line)

            # Subtasks
            for sub_id in parent_task.subtasks:
                sub = self.tracker.get_task(sub_id)
                if sub:
                    sub_icon = status_icons.get(sub.status, "?")
                    elapsed = f"({sub.metrics.elapsed_ms():.0f}ms)"
                    sub_line = f"  {sub_icon} {sub.description} {elapsed}"
                    output.append(sub_line)

        # Summary bar
        summary = self.tracker.get_summary()
        total = summary["total_tasks"]
        completed = summary["completed"]
        pct = summary["completion_rate"]
        
        progress_bar = self._make_progress_bar(pct)
        summary_line = f"\nCompletion: {progress_bar} {pct:.0f}%"
        output.append(summary_line)

        return "\n".join(output)

    def _make_progress_bar(self, percentage: float) -> str:
        """Create visual progress bar.

        Args:
            percentage: Percentage (0-100)

        Returns:
            Progress bar string
        """
        filled = int(percentage / 5)  # 20 chars = 100%
        empty = 20 - filled
        return "█" * filled + "░" * empty


class TaskStatusWidget(Container):
    """Main task status widget with compact + detail views."""

    DEFAULT_CSS = """
    TaskStatusWidget {
        width: 100%;
        height: auto;
    }
    """

    def __init__(self, tracker: TaskTracker, show_detail: bool = False):
        """Initialize task status widget.

        Args:
            tracker: TaskTracker instance
            show_detail: Show detailed view or compact
        """
        super().__init__()
        self.tracker = tracker
        self.show_detail = show_detail

    def compose(self) -> ComposeResult:
        """Compose task status widgets."""
        # Always show compact status
        yield TaskStatusCompact(self.tracker)

        # Optional detailed view
        if self.show_detail:
            yield TaskDetailPanel(self.tracker)

    def toggle_detail(self) -> None:
        """Toggle between compact and detailed view."""
        self.show_detail = not self.show_detail
        self.remove_children()
        self.mount(*self.compose())

    def show_detail_view(self) -> None:
        """Show detailed task view."""
        if not self.show_detail:
            self.toggle_detail()

    def hide_detail_view(self) -> None:
        """Hide detailed task view."""
        if self.show_detail:
            self.toggle_detail()

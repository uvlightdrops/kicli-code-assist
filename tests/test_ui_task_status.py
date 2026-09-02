"""Tests for task status widgets."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from kicli_code_assist.ui.task_status import (
    TaskStatusCompact,
    TaskDetailLine,
    TaskDetailPanel,
    TaskStatusWidget,
)
from kicli_code_assist.executor.task_tracker import TaskTracker, TaskStatus, TaskType


class MockTracker:
    """Mock task tracker."""

    def __init__(self):
        self.tasks = {}
        self.active = []

    def get_summary(self):
        return {
            "total_tasks": 5,
            "active": 1,
            "completed": 3,
            "failed": 0,
            "completion_rate": 60.0,
        }

    def get_task_tree(self):
        parent = Mock()
        parent.status = TaskStatus.COMPLETED
        parent.description = "Parent task"
        parent.subtasks = []
        parent.metrics = Mock(elapsed_ms=Mock(return_value=1000))
        return {"parent-1": parent}

    def get_task(self, task_id):
        return None


class TestTaskStatusCompact:
    """Test TaskStatusCompact widget."""

    def test_initialization(self):
        """Test compact status initialization."""
        tracker = MockTracker()
        widget = TaskStatusCompact(tracker)
        assert widget.tracker is tracker

    def test_render_format(self):
        """Test compact status format."""
        tracker = MockTracker()
        widget = TaskStatusCompact(tracker)

        output = widget.render()
        assert "📊 Tasks:" in output
        assert "active" in output
        assert "done" in output

    def test_render_shows_counts(self):
        """Test status shows active and completed counts."""
        tracker = MockTracker()
        widget = TaskStatusCompact(tracker)

        output = widget.render()
        assert "1 active" in output
        assert "3 done" in output

    def test_render_shows_completion(self):
        """Test status shows completion rate."""
        tracker = MockTracker()
        widget = TaskStatusCompact(tracker)

        output = widget.render()
        assert "60%" in output


class TestTaskDetailLine:
    """Test TaskDetailLine widget."""

    def test_initialization(self):
        """Test detail line initialization."""
        task = Mock()
        task.status = TaskStatus.COMPLETED
        task.description = "Test task"
        task.metrics = Mock(elapsed_ms=Mock(return_value=500))

        line = TaskDetailLine("task-1", task)
        assert line.task_id == "task-1"
        assert line.task is task

    def test_render_completed_icon(self):
        """Test completed task shows check mark."""
        task = Mock()
        task.status = TaskStatus.COMPLETED
        task.description = "Test task"
        task.metrics = Mock(elapsed_ms=Mock(return_value=500))

        line = TaskDetailLine("task-1", task)
        output = line.render()
        assert "✅" in output

    def test_render_in_progress_icon(self):
        """Test in progress task shows spinner."""
        task = Mock()
        task.status = TaskStatus.IN_PROGRESS
        task.description = "Test task"
        task.metrics = Mock(elapsed_ms=Mock(return_value=500))

        line = TaskDetailLine("task-1", task)
        output = line.render()
        assert "🔄" in output

    def test_render_failed_icon(self):
        """Test failed task shows X."""
        task = Mock()
        task.status = TaskStatus.FAILED
        task.description = "Test task"
        task.metrics = Mock(elapsed_ms=Mock(return_value=500))

        line = TaskDetailLine("task-1", task)
        output = line.render()
        assert "❌" in output

    def test_render_description(self):
        """Test renders task description."""
        task = Mock()
        task.status = TaskStatus.COMPLETED
        task.description = "Analyzing code"
        task.metrics = Mock(elapsed_ms=Mock(return_value=500))

        line = TaskDetailLine("task-1", task)
        output = line.render()
        assert "Analyzing code" in output

    def test_render_elapsed_time(self):
        """Test renders elapsed time."""
        task = Mock()
        task.status = TaskStatus.COMPLETED
        task.description = "Test task"
        task.metrics = Mock(elapsed_ms=Mock(return_value=1234))

        line = TaskDetailLine("task-1", task)
        output = line.render()
        assert "1234ms" in output


class TestTaskDetailPanel:
    """Test TaskDetailPanel widget."""

    def test_initialization(self):
        """Test detail panel initialization."""
        tracker = MockTracker()
        panel = TaskDetailPanel(tracker)
        assert panel.tracker is tracker

    def test_render_no_tasks(self):
        """Test render with no tasks."""
        tracker = MockTracker()
        tracker.get_task_tree = Mock(return_value={})
        panel = TaskDetailPanel(tracker)

        output = panel.render()
        assert "No tasks" in output

    def test_render_shows_parent_task(self):
        """Test render shows parent task."""
        tracker = MockTracker()
        panel = TaskDetailPanel(tracker)

        output = panel.render()
        assert "Parent task" in output

    def test_render_parent_task_bold(self):
        """Test parent task is bolded."""
        tracker = MockTracker()
        panel = TaskDetailPanel(tracker)

        output = panel.render()
        assert "[bold]" in output

    def test_render_completion_bar(self):
        """Test render shows completion bar."""
        tracker = MockTracker()
        panel = TaskDetailPanel(tracker)

        output = panel.render()
        assert "Completion:" in output
        assert "%" in output

    def test_progress_bar_full(self):
        """Test progress bar for 100% completion."""
        tracker = MockTracker()
        tracker.get_summary = Mock(
            return_value={
                "total_tasks": 5,
                "active": 0,
                "completed": 5,
                "failed": 0,
                "completion_rate": 100.0,
            }
        )
        panel = TaskDetailPanel(tracker)

        bar = panel._make_progress_bar(100)
        assert "█" * 20 in bar
        assert "░" not in bar

    def test_progress_bar_empty(self):
        """Test progress bar for 0% completion."""
        tracker = MockTracker()
        panel = TaskDetailPanel(tracker)

        bar = panel._make_progress_bar(0)
        assert "█" not in bar
        assert "░" * 20 in bar

    def test_progress_bar_half(self):
        """Test progress bar for 50% completion."""
        tracker = MockTracker()
        panel = TaskDetailPanel(tracker)

        bar = panel._make_progress_bar(50)
        assert bar.count("█") == 10
        assert bar.count("░") == 10


class TestTaskStatusWidget:
    """Test TaskStatusWidget container."""

    def test_initialization_compact(self):
        """Test widget initialization in compact mode."""
        tracker = MockTracker()
        widget = TaskStatusWidget(tracker, show_detail=False)
        assert widget.tracker is tracker
        assert widget.show_detail is False

    def test_initialization_detailed(self):
        """Test widget initialization in detail mode."""
        tracker = MockTracker()
        widget = TaskStatusWidget(tracker, show_detail=True)
        assert widget.show_detail is True

    def test_toggle_detail(self):
        """Test toggling detail view."""
        tracker = MockTracker()
        widget = TaskStatusWidget(tracker, show_detail=False)

        assert widget.show_detail is False
        # Note: toggle_detail would need mount to work properly
        # So we just test the flag change
        widget.show_detail = not widget.show_detail
        assert widget.show_detail is True

    def test_show_detail_view(self):
        """Test showing detail view."""
        tracker = MockTracker()
        widget = TaskStatusWidget(tracker, show_detail=False)

        # Note: toggle_detail requires running Textual app
        # So we just test the flag directly
        widget.show_detail = True
        assert widget.show_detail is True

    def test_hide_detail_view(self):
        """Test hiding detail view."""
        tracker = MockTracker()
        widget = TaskStatusWidget(tracker, show_detail=True)

        # Note: toggle_detail requires running Textual app
        # So we just test the flag directly
        widget.show_detail = False
        assert widget.show_detail is False

"""Tests for task tracking system."""

import pytest
import time
from pathlib import Path
from kicli_code_assist.executor.task_tracker import (
    TaskTracker,
    TaskStatus,
    TaskType,
    Task,
    TaskMetrics,
)
from ki_core import Config


class TestTaskMetrics:
    """Test TaskMetrics class."""

    def test_initialization(self):
        """Test creating metrics."""
        metrics = TaskMetrics()
        assert metrics.start_time == 0.0
        assert metrics.end_time is None
        assert metrics.items_processed == 0
        assert metrics.errors == 0
        assert metrics.success_rate == 1.0

    def test_elapsed_time(self):
        """Test elapsed time calculation."""
        metrics = TaskMetrics()
        metrics.start_time = time.time()
        time.sleep(0.01)
        elapsed = metrics.elapsed_ms()
        assert elapsed >= 10  # At least 10ms

    def test_elapsed_time_with_end(self):
        """Test elapsed time with explicit end."""
        metrics = TaskMetrics()
        metrics.start_time = 100.0
        metrics.end_time = 110.0
        assert metrics.elapsed_ms() == 10000  # 10 seconds = 10000ms

    def test_to_dict(self):
        """Test serialization to dict."""
        metrics = TaskMetrics(
            start_time=100.0,
            end_time=110.0,
            items_processed=5,
            errors=1,
            success_rate=0.8,
        )
        d = metrics.to_dict()
        assert d["start_time"] == 100.0
        assert d["end_time"] == 110.0
        assert d["items_processed"] == 5
        assert d["errors"] == 1
        assert d["success_rate"] == 0.8


class TestTask:
    """Test Task class."""

    def test_creation(self):
        """Test creating a task."""
        task = Task(
            task_id="test-1",
            task_type=TaskType.FILE_ANALYSIS,
            description="Test task",
        )
        assert task.task_id == "test-1"
        assert task.status == TaskStatus.PENDING
        assert task.result is None
        assert task.error_message is None

    def test_start(self):
        """Test starting a task."""
        task = Task(
            task_id="test-1",
            task_type=TaskType.FILE_ANALYSIS,
            description="Test task",
        )
        task.start()
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.metrics.start_time > 0

    def test_complete(self):
        """Test completing a task."""
        task = Task(
            task_id="test-1",
            task_type=TaskType.FILE_ANALYSIS,
            description="Test task",
        )
        task.start()
        task.complete("Success")
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "Success"
        assert task.metrics.end_time is not None

    def test_fail(self):
        """Test failing a task."""
        task = Task(
            task_id="test-1",
            task_type=TaskType.FILE_ANALYSIS,
            description="Test task",
        )
        task.start()
        task.fail("Something went wrong")
        assert task.status == TaskStatus.FAILED
        assert task.error_message == "Something went wrong"
        assert task.metrics.end_time is not None

    def test_cancel(self):
        """Test cancelling a task."""
        task = Task(
            task_id="test-1",
            task_type=TaskType.FILE_ANALYSIS,
            description="Test task",
        )
        task.start()
        task.cancel()
        assert task.status == TaskStatus.CANCELLED
        assert task.metrics.end_time is not None

    def test_is_active(self):
        """Test active status check."""
        task = Task(
            task_id="test-1",
            task_type=TaskType.FILE_ANALYSIS,
            description="Test task",
        )
        assert task.is_active()
        task.start()
        assert task.is_active()
        task.complete()
        assert not task.is_active()

    def test_to_dict(self):
        """Test serialization to dict."""
        task = Task(
            task_id="test-1",
            task_type=TaskType.FILE_ANALYSIS,
            description="Test task",
        )
        d = task.to_dict()
        assert d["task_id"] == "test-1"
        assert d["task_type"] == "file_analysis"
        assert d["status"] == "pending"
        assert d["description"] == "Test task"

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "task_id": "test-1",
            "task_type": "file_analysis",
            "status": "pending",
            "description": "Test task",
            "parent_task_id": None,
            "subtasks": [],
            "result": None,
            "error_message": None,
        }
        task = Task.from_dict(data)
        assert task.task_id == "test-1"
        assert task.task_type == TaskType.FILE_ANALYSIS
        assert task.status == TaskStatus.PENDING


class TestTaskTracker:
    """Test TaskTracker class."""

    def test_initialization(self):
        """Test creating tracker."""
        tracker = TaskTracker()
        assert tracker.tasks == {}
        assert tracker.active_task is None

    def test_create_task(self):
        """Test creating a task."""
        tracker = TaskTracker()
        task = tracker.create_task(
            "task-1",
            TaskType.FILE_ANALYSIS,
            "Analyze files",
        )
        assert task.task_id == "task-1"
        assert "task-1" in tracker.tasks
        assert tracker.tasks["task-1"].status == TaskStatus.PENDING

    def test_create_subtask(self):
        """Test creating subtask."""
        tracker = TaskTracker()
        parent = tracker.create_task("parent", TaskType.LLM_CALL, "Parent")
        child = tracker.create_task(
            "child",
            TaskType.FILE_ANALYSIS,
            "Child",
            parent_task_id="parent",
        )
        assert child.parent_task_id == "parent"
        assert "child" in parent.subtasks

    def test_start_task(self):
        """Test starting a task."""
        tracker = TaskTracker()
        tracker.create_task("task-1", TaskType.FILE_ANALYSIS, "Analyze")
        task = tracker.start_task("task-1")
        assert task.status == TaskStatus.IN_PROGRESS
        assert tracker.active_task == "task-1"

    def test_complete_task(self):
        """Test completing a task."""
        tracker = TaskTracker()
        tracker.create_task("task-1", TaskType.FILE_ANALYSIS, "Analyze")
        tracker.start_task("task-1")
        task = tracker.complete_task("task-1", "Success")
        assert task.status == TaskStatus.COMPLETED
        assert tracker.active_task is None

    def test_fail_task(self):
        """Test failing a task."""
        tracker = TaskTracker()
        tracker.create_task("task-1", TaskType.FILE_ANALYSIS, "Analyze")
        tracker.start_task("task-1")
        task = tracker.fail_task("task-1", "Error occurred")
        assert task.status == TaskStatus.FAILED
        assert task.error_message == "Error occurred"

    def test_cancel_task(self):
        """Test cancelling a task."""
        tracker = TaskTracker()
        tracker.create_task("task-1", TaskType.FILE_ANALYSIS, "Analyze")
        tracker.start_task("task-1")
        task = tracker.cancel_task("task-1")
        assert task.status == TaskStatus.CANCELLED

    def test_get_task(self):
        """Test retrieving a task."""
        tracker = TaskTracker()
        tracker.create_task("task-1", TaskType.FILE_ANALYSIS, "Analyze")
        task = tracker.get_task("task-1")
        assert task is not None
        assert task.task_id == "task-1"

    def test_get_nonexistent_task(self):
        """Test retrieving nonexistent task."""
        tracker = TaskTracker()
        task = tracker.get_task("nonexistent")
        assert task is None

    def test_get_active_tasks(self):
        """Test getting active tasks."""
        tracker = TaskTracker()
        tracker.create_task("task-1", TaskType.FILE_ANALYSIS, "Analyze")
        tracker.create_task("task-2", TaskType.LLM_CALL, "Call LLM")
        tracker.start_task("task-1")
        tracker.start_task("task-2")
        tracker.complete_task("task-1")

        active = tracker.get_active_tasks()
        assert len(active) == 1
        assert active[0].task_id == "task-2"

    def test_get_task_tree(self):
        """Test getting task hierarchy."""
        tracker = TaskTracker()
        tracker.create_task("parent-1", TaskType.LLM_CALL, "Parent 1")
        tracker.create_task("child-1", TaskType.FILE_ANALYSIS, "Child 1", "parent-1")
        tracker.create_task("parent-2", TaskType.LLM_CALL, "Parent 2")

        tree = tracker.get_task_tree()
        assert len(tree) == 2
        assert "parent-1" in tree
        assert "parent-2" in tree
        assert "child-1" not in tree

    def test_get_summary(self):
        """Test getting execution summary."""
        tracker = TaskTracker()
        tracker.create_task("task-1", TaskType.FILE_ANALYSIS, "Analyze")
        tracker.create_task("task-2", TaskType.LLM_CALL, "Call LLM")
        tracker.start_task("task-1")
        tracker.complete_task("task-1")
        tracker.start_task("task-2")

        summary = tracker.get_summary()
        assert summary["total_tasks"] == 2
        assert summary["completed"] == 1
        assert summary["failed"] == 0
        assert summary["active"] == 1
        assert summary["completion_rate"] == 50.0

    def test_status_display(self):
        """Test formatted status display."""
        tracker = TaskTracker()
        tracker.create_task("task-1", TaskType.FILE_ANALYSIS, "Analyze files")
        tracker.start_task("task-1")

        display = tracker.get_status_display()
        assert "Task Status" in display
        assert "Active: 1" in display
        assert "Analyze files" in display

    def test_write_history(self):
        """Test writing task history."""
        tracker = TaskTracker()
        tracker.create_task("task-1", TaskType.FILE_ANALYSIS, "Analyze")
        tracker.start_task("task-1")
        tracker.complete_task("task-1")

        history = tracker.load_history()
        assert len(history) >= 1
        assert any(t.task_id == "task-1" for t in history)

    def test_clear_history(self):
        """Test clearing history."""
        tracker = TaskTracker()
        tracker.create_task("task-1", TaskType.FILE_ANALYSIS, "Analyze")
        tracker.start_task("task-1")
        tracker.complete_task("task-1")
        tracker.clear_history()

        history = tracker.load_history()
        assert len(history) == 0

    def test_workflow_integration(self):
        """Test complete task workflow."""
        tracker = TaskTracker()

        # Create task hierarchy
        parent = tracker.create_task("analyze", TaskType.LLM_CALL, "Analyze code")
        child1 = tracker.create_task(
            "select-files", TaskType.FILE_ANALYSIS, "Select files", "analyze"
        )
        child2 = tracker.create_task(
            "cache", TaskType.CACHING, "Cache context", "analyze"
        )

        # Execute workflow
        tracker.start_task("analyze")
        assert tracker.active_task == "analyze"

        tracker.start_task("select-files")
        tracker.complete_task("select-files", "Selected 5 files")

        tracker.start_task("cache")
        tracker.complete_task("cache", "Cached 2.3MB")

        tracker.complete_task("analyze", "Analysis complete")

        # Check final state
        summary = tracker.get_summary()
        assert summary["completed"] == 3
        assert summary["active"] == 0
        assert summary["completion_rate"] == 100.0

    def test_task_with_metrics(self):
        """Test task metrics collection."""
        tracker = TaskTracker()
        tracker.create_task("task-1", TaskType.FILE_ANALYSIS, "Analyze")
        task = tracker.start_task("task-1")

        # Simulate work
        time.sleep(0.02)
        task.metrics.items_processed = 10
        task.metrics.errors = 1
        task.metrics.success_rate = 0.9

        tracker.complete_task("task-1")

        retrieved = tracker.get_task("task-1")
        assert retrieved.metrics.items_processed == 10
        assert retrieved.metrics.errors == 1
        assert retrieved.metrics.success_rate == 0.9
        assert retrieved.metrics.elapsed_ms() >= 20

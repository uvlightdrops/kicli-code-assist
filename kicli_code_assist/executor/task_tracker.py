"""Task tracking and status management for LLM workflows."""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum
import json
from pathlib import Path

from ki_core import Config


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """Type of task being tracked."""
    FILE_ANALYSIS = "file_analysis"
    LLM_CALL = "llm_call"
    DIFF_GENERATION = "diff_generation"
    CODE_REVIEW = "code_review"
    CACHING = "caching"
    OTHER = "other"


@dataclass
class TaskMetrics:
    """Metrics for a task."""
    start_time: float = 0.0
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    items_processed: int = 0
    errors: int = 0
    success_rate: float = 1.0

    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return (time.time() - self.start_time) * 1000

    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.elapsed_ms(),
            "items_processed": self.items_processed,
            "errors": self.errors,
            "success_rate": self.success_rate,
        }


@dataclass
class Task:
    """Single task being tracked."""
    task_id: str
    task_type: TaskType
    description: str
    status: TaskStatus = TaskStatus.PENDING
    metrics: TaskMetrics = field(default_factory=TaskMetrics)
    parent_task_id: Optional[str] = None
    subtasks: List[str] = field(default_factory=list)
    result: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def start(self) -> None:
        """Mark task as started."""
        self.status = TaskStatus.IN_PROGRESS
        self.metrics.start_time = time.time()

    def complete(self, result: Optional[str] = None) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.metrics.end_time = time.time()
        self.result = result

    def fail(self, error: str) -> None:
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.metrics.end_time = time.time()
        self.error_message = error

    def cancel(self) -> None:
        """Cancel task."""
        self.status = TaskStatus.CANCELLED
        self.metrics.end_time = time.time()

    def is_active(self) -> bool:
        """Check if task is currently active."""
        return self.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS)

    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "description": self.description,
            "status": self.status.value,
            "metrics": self.metrics.to_dict(),
            "parent_task_id": self.parent_task_id,
            "subtasks": self.subtasks,
            "result": self.result,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create from dict."""
        task = cls(
            task_id=data["task_id"],
            task_type=TaskType(data["task_type"]),
            description=data["description"],
            status=TaskStatus(data["status"]),
            parent_task_id=data.get("parent_task_id"),
            subtasks=data.get("subtasks", []),
            result=data.get("result"),
            error_message=data.get("error_message"),
        )
        return task


class TaskTracker:
    """Track and manage tasks during LLM workflows."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize task tracker.

        Args:
            config: Configuration object
        """
        self.config = config or Config.from_env()
        self.tasks: Dict[str, Task] = {}
        self.active_task: Optional[str] = None
        self.history_file = (
            Path(self.config.kicli_session_dir) / "task_history.jsonl"
        )
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

    def create_task(
        self,
        task_id: str,
        task_type: TaskType,
        description: str,
        parent_task_id: Optional[str] = None,
    ) -> Task:
        """Create a new task.

        Args:
            task_id: Unique task identifier
            task_type: Type of task
            description: Task description
            parent_task_id: Parent task if subtask

        Returns:
            Created Task object
        """
        task = Task(
            task_id=task_id,
            task_type=task_type,
            description=description,
            parent_task_id=parent_task_id,
        )
        self.tasks[task_id] = task

        # Register as subtask if has parent
        if parent_task_id and parent_task_id in self.tasks:
            self.tasks[parent_task_id].subtasks.append(task_id)

        return task

    def start_task(self, task_id: str) -> Optional[Task]:
        """Start a task.

        Args:
            task_id: Task identifier

        Returns:
            Task object or None if not found
        """
        if task_id not in self.tasks:
            return None

        task = self.tasks[task_id]
        task.start()
        self.active_task = task_id
        self._write_history(task)
        return task

    def complete_task(self, task_id: str, result: Optional[str] = None) -> Optional[Task]:
        """Complete a task.

        Args:
            task_id: Task identifier
            result: Task result

        Returns:
            Task object or None if not found
        """
        if task_id not in self.tasks:
            return None

        task = self.tasks[task_id]
        task.complete(result)
        if self.active_task == task_id:
            self.active_task = None
        self._write_history(task)
        return task

    def fail_task(self, task_id: str, error: str) -> Optional[Task]:
        """Mark task as failed.

        Args:
            task_id: Task identifier
            error: Error message

        Returns:
            Task object or None if not found
        """
        if task_id not in self.tasks:
            return None

        task = self.tasks[task_id]
        task.fail(error)
        if self.active_task == task_id:
            self.active_task = None
        self._write_history(task)
        return task

    def cancel_task(self, task_id: str) -> Optional[Task]:
        """Cancel a task.

        Args:
            task_id: Task identifier

        Returns:
            Task object or None if not found
        """
        if task_id not in self.tasks:
            return None

        task = self.tasks[task_id]
        task.cancel()
        if self.active_task == task_id:
            self.active_task = None
        self._write_history(task)
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task object or None if not found
        """
        return self.tasks.get(task_id)

    def get_active_tasks(self) -> List[Task]:
        """Get all active tasks.

        Returns:
            List of active Task objects
        """
        return [t for t in self.tasks.values() if t.is_active()]

    def get_task_tree(self) -> Dict[str, Task]:
        """Get task hierarchy (parent tasks only).

        Returns:
            Dict of parent_task_id -> Task
        """
        return {
            task_id: task
            for task_id, task in self.tasks.items()
            if task.parent_task_id is None
        }

    def get_summary(self) -> dict:
        """Get task execution summary.

        Returns:
            Summary stats
        """
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
        active = len(self.get_active_tasks())

        total_time = sum(t.metrics.elapsed_ms() for t in self.tasks.values())
        avg_time = total_time / total if total > 0 else 0

        return {
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "active": active,
            "completion_rate": (completed / total * 100) if total > 0 else 0,
            "total_duration_ms": total_time,
            "average_duration_ms": avg_time,
            "active_task_id": self.active_task,
        }

    def _write_history(self, task: Task) -> None:
        """Write task to history log.

        Args:
            task: Task to log
        """
        try:
            with open(self.history_file, "a") as f:
                f.write(json.dumps(task.to_dict()) + "\n")
        except (OSError, IOError):
            pass

    def load_history(self) -> List[Task]:
        """Load task history from file.

        Returns:
            List of tasks from history
        """
        if not self.history_file.exists():
            return []

        tasks = []
        try:
            with open(self.history_file, "r") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        task = Task.from_dict(data)
                        tasks.append(task)
        except (OSError, IOError, json.JSONDecodeError):
            pass

        return tasks

    def clear_history(self) -> None:
        """Clear task history."""
        try:
            self.history_file.unlink()
        except OSError:
            pass

    def get_status_display(self) -> str:
        """Get formatted status display.

        Returns:
            Formatted status string for UI
        """
        summary = self.get_summary()

        lines = []
        lines.append("📊 Task Status")
        lines.append(f"  Active: {summary['active']} | Completed: {summary['completed']} | Failed: {summary['failed']}")
        lines.append(f"  Completion: {summary['completion_rate']:.0f}%")

        if self.active_task and self.active_task in self.tasks:
            task = self.tasks[self.active_task]
            elapsed = task.metrics.elapsed_ms()
            lines.append(f"  🔄 {task.description} ({elapsed:.0f}ms)")

        return "\n".join(lines)

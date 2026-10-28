"""Agent execution state model and snapshots.

Provides dataclasses for tracking agent state, thinking steps, and execution progress.
Used by AgentController for state broadcasting and persistence.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pathlib import Path
import json


class AgentStatus(str, Enum):
    """Agent execution status."""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    ROLLING_BACK = "rolling_back"


class AgentPhase(str, Enum):
    """Agent execution phases (Phase 5.4 sub-phases)."""
    INIT = "init"
    ANALYSIS = "analysis"
    GIT_WORKFLOW = "git_workflow"        # Phase 5.4.1
    TEST_AUTOMATION = "test_automation"  # Phase 5.4.2
    STATE_TRACKING = "state_tracking"    # Phase 5.4.3
    CODE_QUALITY = "code_quality"        # Phase 5.4.4
    ROLLBACK = "rollback"                # Phase 5.4.5
    COMPLETE = "complete"


class ThinkingType(str, Enum):
    """Type of thinking step."""
    DECISION = "decision"
    ANALYSIS = "analysis"
    PLANNING = "planning"
    REASONING = "reasoning"
    ERROR = "error"


@dataclass
class ThinkingStep:
    """A single thinking step in agent reasoning."""
    timestamp: datetime
    thinking_type: ThinkingType
    content: str
    reasoning: Optional[str] = None
    confidence: float = 1.0  # 0.0-1.0 confidence in this step
    alternatives: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "thinking_type": self.thinking_type.value,
            "content": self.content,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "alternatives": self.alternatives,
        }


@dataclass
class ActionLog:
    """A completed action."""
    timestamp: datetime
    action_type: str  # "file_created", "test_run", "commit", etc.
    description: str
    status: str = "success"  # "success", "warning", "error"
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "action_type": self.action_type,
            "description": self.description,
            "status": self.status,
            "details": self.details,
        }


@dataclass
class ErrorInfo:
    """Error information."""
    error_type: str
    message: str
    traceback: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    recovery_hint: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {
            "error_type": self.error_type,
            "message": self.message,
            "traceback": self.traceback,
            "timestamp": self.timestamp.isoformat(),
            "recovery_hint": self.recovery_hint,
        }


@dataclass
class AgentStateSnapshot:
    """Snapshot of current agent execution state.
    
    Complete state representation sent to all listeners (WebUI, CLI supervisor, etc.)
    Used for broadcasting state updates and persistence.
    """
    agent_id: str
    task_id: str
    status: AgentStatus
    current_phase: AgentPhase
    progress: int  # 0-100
    started_at: datetime
    updated_at: datetime
    
    # Thinking and reasoning
    thinking_steps: List[ThinkingStep] = field(default_factory=list)
    
    # Actions taken
    action_log: List[ActionLog] = field(default_factory=list)
    
    # Current operation
    current_operation: Optional[str] = None
    next_action: Optional[str] = None
    
    # Error state
    error: Optional[ErrorInfo] = None
    
    # Git context
    git_branch: Optional[str] = None
    git_commit: Optional[str] = None
    
    # Test results
    test_results: Optional[Dict[str, Any]] = None
    
    # Quality metrics
    quality_checks: Optional[Dict[str, Any]] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "status": self.status.value,
            "current_phase": self.current_phase.value,
            "progress": self.progress,
            "started_at": self.started_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "thinking_steps": [step.to_dict() for step in self.thinking_steps],
            "action_log": [action.to_dict() for action in self.action_log],
            "current_operation": self.current_operation,
            "next_action": self.next_action,
            "error": self.error.to_dict() if self.error else None,
            "git_branch": self.git_branch,
            "git_commit": self.git_commit,
            "test_results": self.test_results,
            "quality_checks": self.quality_checks,
            "metadata": self.metadata,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AgentStateSnapshot:
        """Create from dict."""
        thinking_steps = [
            ThinkingStep(
                timestamp=datetime.fromisoformat(step["timestamp"]),
                thinking_type=ThinkingType(step["thinking_type"]),
                content=step["content"],
                reasoning=step.get("reasoning"),
                confidence=step.get("confidence", 1.0),
                alternatives=step.get("alternatives", []),
            )
            for step in data.get("thinking_steps", [])
        ]
        
        action_log = [
            ActionLog(
                timestamp=datetime.fromisoformat(action["timestamp"]),
                action_type=action["action_type"],
                description=action["description"],
                status=action.get("status", "success"),
                details=action.get("details"),
            )
            for action in data.get("action_log", [])
        ]
        
        error = None
        if data.get("error"):
            error = ErrorInfo(
                error_type=data["error"]["error_type"],
                message=data["error"]["message"],
                traceback=data["error"].get("traceback"),
                timestamp=datetime.fromisoformat(data["error"]["timestamp"]),
                recovery_hint=data["error"].get("recovery_hint"),
            )
        
        return cls(
            agent_id=data["agent_id"],
            task_id=data["task_id"],
            status=AgentStatus(data["status"]),
            current_phase=AgentPhase(data["current_phase"]),
            progress=data["progress"],
            started_at=datetime.fromisoformat(data["started_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            thinking_steps=thinking_steps,
            action_log=action_log,
            current_operation=data.get("current_operation"),
            next_action=data.get("next_action"),
            error=error,
            git_branch=data.get("git_branch"),
            git_commit=data.get("git_commit"),
            test_results=data.get("test_results"),
            quality_checks=data.get("quality_checks"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ExecutionResult:
    """Result of agent execution."""
    agent_id: str
    task_id: str
    success: bool
    status: AgentStatus
    final_state: AgentStateSnapshot
    duration_seconds: float
    error: Optional[ErrorInfo] = None
    rollback_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "success": self.success,
            "status": self.status.value,
            "final_state": self.final_state.to_dict(),
            "duration_seconds": self.duration_seconds,
            "error": self.error.to_dict() if self.error else None,
            "rollback_info": self.rollback_info,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str, indent=2)

"""
Phase 5.5.2: Transparency & Observability - Core Tracing Module

ReasoningTracer records agent decision-making steps with full context
for human visibility and audit trails.
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pathlib import Path
import threading
from queue import Queue


class EventType(str, Enum):
    """Types of reasoning events."""
    ANALYSIS_START = "analysis_start"
    ANALYSIS_STEP = "analysis_step"
    ANALYSIS_COMPLETE = "analysis_complete"
    DECISION_POINT = "decision_point"
    DECISION_MADE = "decision_made"
    EXECUTION_START = "execution_start"
    EXECUTION_STEP = "execution_step"
    EXECUTION_COMPLETE = "execution_complete"
    ERROR_OCCURRED = "error_occurred"
    WARNING_ISSUED = "warning_issued"
    METADATA_RECORDED = "metadata_recorded"


class SeverityLevel(str, Enum):
    """Severity of events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ReasoningEvent:
    """Atomic reasoning event."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.ANALYSIS_STEP
    timestamp: datetime = field(default_factory=datetime.utcnow)
    severity: SeverityLevel = SeverityLevel.INFO
    
    # Context
    agent_id: str = ""
    goal_id: str = ""
    phase: str = ""  # e.g., "analyze", "decide", "execute"
    
    # Event details
    message: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Decision information
    decision_point: Optional[str] = None
    options_considered: List[str] = field(default_factory=list)
    option_selected: Optional[str] = None
    reasoning_brief: str = ""
    confidence_score: Optional[float] = None  # 0.0-1.0
    
    # Execution information
    action_performed: Optional[str] = None
    action_result: Optional[str] = None
    duration_ms: Optional[int] = None
    
    # Error information
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    recovery_suggestion: Optional[str] = None


@dataclass
class ReasoningSession:
    """Container for all reasoning events in one execution."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    goal_id: str = ""
    goal_title: str = ""
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: str = "in_progress"  # in_progress, completed, failed
    
    events: List[ReasoningEvent] = field(default_factory=list)
    
    # Aggregate metrics
    total_events: int = 0
    analysis_events: int = 0
    decision_events: int = 0
    execution_events: int = 0
    error_count: int = 0
    warning_count: int = 0
    total_duration_ms: int = 0
    
    # Top-level results
    success: bool = False
    result_summary: str = ""
    final_action_taken: Optional[str] = None


class ReasoningTracer:
    """
    Records agent reasoning steps with full context.
    
    Usage:
    ```python
    tracer = ReasoningTracer(agent_id="agent-1")
    
    with tracer.trace_session("goal-1", "Refactor UserService") as session:
        tracer.record_event(
            event_type=EventType.ANALYSIS_START,
            message="Beginning impact analysis"
        )
        
        tracer.record_decision(
            decision_point="Change order",
            options=["top-down", "bottom-up"],
            selected="bottom-up",
            reasoning="Minimize import conflicts",
            confidence=0.92
        )
        
        tracer.record_execution(
            action="update_imports",
            result="3 files updated",
            duration_ms=250
        )
    ```
    """
    
    def __init__(
        self,
        agent_id: str,
        output_dir: Optional[Path] = None,
        enable_async: bool = False
    ):
        """
        Initialize tracer.
        
        Args:
            agent_id: ID of the agent being traced
            output_dir: Where to save reasoning sessions (default: ./sessions)
            enable_async: If True, events queued and written async
        """
        self.agent_id = agent_id
        self.output_dir = Path(output_dir or "./reasoning_sessions")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.enable_async = enable_async
        self.event_queue: Optional[Queue] = Queue() if enable_async else None
        
        self._current_session: Optional[ReasoningSession] = None
        self._lock = threading.RLock()
    
    def start_session(
        self,
        goal_id: str,
        goal_title: str
    ) -> ReasoningSession:
        """Start a new reasoning session."""
        with self._lock:
            self._current_session = ReasoningSession(
                agent_id=self.agent_id,
                goal_id=goal_id,
                goal_title=goal_title
            )
            return self._current_session
    
    def end_session(
        self,
        success: bool,
        result_summary: str = "",
        final_action: Optional[str] = None
    ) -> ReasoningSession:
        """End current session and save to disk."""
        with self._lock:
            if not self._current_session:
                raise RuntimeError("No active session")
            
            session = self._current_session
            session.completed_at = datetime.utcnow()
            session.status = "completed" if success else "failed"
            session.success = success
            session.result_summary = result_summary
            session.final_action_taken = final_action
            
            # Calculate aggregate metrics
            session.total_events = len(session.events)
            session.analysis_events = sum(
                1 for e in session.events
                if e.event_type == EventType.ANALYSIS_START or
                   e.event_type == EventType.ANALYSIS_STEP or
                   e.event_type == EventType.ANALYSIS_COMPLETE
            )
            session.decision_events = sum(
                1 for e in session.events
                if EventType.DECISION_MADE in e.event_type
            )
            session.execution_events = sum(
                1 for e in session.events
                if e.event_type == EventType.EXECUTION_START or
                   e.event_type == EventType.EXECUTION_STEP or
                   e.event_type == EventType.EXECUTION_COMPLETE
            )
            session.error_count = sum(
                1 for e in session.events
                if e.severity == SeverityLevel.ERROR or
                   e.severity == SeverityLevel.CRITICAL
            )
            session.warning_count = sum(
                1 for e in session.events
                if e.severity == SeverityLevel.WARNING
            )
            
            if session.completed_at and session.started_at:
                delta = session.completed_at - session.started_at
                session.total_duration_ms = int(delta.total_seconds() * 1000)
            
            self._save_session(session)
            self._current_session = None
            
            return session
    
    def record_event(
        self,
        event_type: EventType,
        message: str = "",
        context: Optional[Dict[str, Any]] = None,
        severity: SeverityLevel = SeverityLevel.INFO,
        phase: str = "",
    ) -> ReasoningEvent:
        """Record a generic reasoning event."""
        if not self._current_session:
            raise RuntimeError("No active session. Call start_session() first.")
        
        event = ReasoningEvent(
            event_type=event_type,
            message=message,
            context=context or {},
            severity=severity,
            agent_id=self.agent_id,
            goal_id=self._current_session.goal_id,
            phase=phase
        )
        
        with self._lock:
            self._current_session.events.append(event)
        
        if self.enable_async:
            self.event_queue.put(("record", event))
        
        return event
    
    def record_decision(
        self,
        decision_point: str,
        options: List[str],
        selected: str,
        reasoning: str,
        confidence: float = 1.0,
        context: Optional[Dict[str, Any]] = None
    ) -> ReasoningEvent:
        """Record a decision point."""
        if not self._current_session:
            raise RuntimeError("No active session. Call start_session() first.")
        
        event = ReasoningEvent(
            event_type=EventType.DECISION_MADE,
            message=f"Decided: {decision_point} -> {selected}",
            decision_point=decision_point,
            options_considered=options,
            option_selected=selected,
            reasoning_brief=reasoning,
            confidence_score=confidence,
            context=context or {},
            agent_id=self.agent_id,
            goal_id=self._current_session.goal_id,
            phase="decide"
        )
        
        with self._lock:
            self._current_session.events.append(event)
        
        if self.enable_async:
            self.event_queue.put(("record", event))
        
        return event
    
    def record_execution(
        self,
        action: str,
        result: str = "",
        duration_ms: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        success: bool = True
    ) -> ReasoningEvent:
        """Record execution of an action."""
        if not self._current_session:
            raise RuntimeError("No active session. Call start_session() first.")
        
        event = ReasoningEvent(
            event_type=EventType.EXECUTION_COMPLETE,
            message=f"Executed: {action}",
            action_performed=action,
            action_result=result,
            duration_ms=duration_ms,
            severity=SeverityLevel.INFO if success else SeverityLevel.ERROR,
            context=context or {},
            agent_id=self.agent_id,
            goal_id=self._current_session.goal_id,
            phase="execute"
        )
        
        with self._lock:
            self._current_session.events.append(event)
        
        if self.enable_async:
            self.event_queue.put(("record", event))
        
        return event
    
    def record_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        recovery_suggestion: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ReasoningEvent:
        """Record an error."""
        if not self._current_session:
            raise RuntimeError("No active session. Call start_session() first.")
        
        event = ReasoningEvent(
            event_type=EventType.ERROR_OCCURRED,
            message=error_message,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            recovery_suggestion=recovery_suggestion,
            severity=SeverityLevel.ERROR,
            context=context or {},
            agent_id=self.agent_id,
            goal_id=self._current_session.goal_id,
            phase="error"
        )
        
        with self._lock:
            self._current_session.events.append(event)
        
        if self.enable_async:
            self.event_queue.put(("record", event))
        
        return event
    
    def record_warning(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ReasoningEvent:
        """Record a warning."""
        return self.record_event(
            event_type=EventType.WARNING_ISSUED,
            message=message,
            context=context,
            severity=SeverityLevel.WARNING
        )
    
    def get_current_session(self) -> Optional[ReasoningSession]:
        """Get current session."""
        return self._current_session
    
    def _save_session(self, session: ReasoningSession) -> Path:
        """Save session to JSON file."""
        session_file = self.output_dir / f"{session.session_id}.json"
        
        # Convert dataclasses to dicts
        session_dict = asdict(session)
        session_dict["events"] = [asdict(e) for e in session.events]
        
        # Convert datetime to ISO string
        session_dict["started_at"] = session.started_at.isoformat()
        if session.completed_at:
            session_dict["completed_at"] = session.completed_at.isoformat()
        
        for event in session_dict["events"]:
            event["timestamp"] = event["timestamp"].isoformat()
        
        with open(session_file, "w") as f:
            json.dump(session_dict, f, indent=2, default=str)
        
        return session_file
    
    def load_session(self, session_id: str) -> Optional[ReasoningSession]:
        """Load a saved session from disk."""
        session_file = self.output_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return None
        
        with open(session_file, "r") as f:
            data = json.load(f)
        
        # Reconstruct dataclasses
        session = ReasoningSession(
            session_id=data["session_id"],
            agent_id=data["agent_id"],
            goal_id=data["goal_id"],
            goal_title=data["goal_title"],
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=(
                datetime.fromisoformat(data["completed_at"])
                if data.get("completed_at")
                else None
            ),
            status=data["status"],
            total_events=data["total_events"],
            analysis_events=data["analysis_events"],
            decision_events=data["decision_events"],
            execution_events=data["execution_events"],
            error_count=data["error_count"],
            warning_count=data["warning_count"],
            total_duration_ms=data["total_duration_ms"],
            success=data["success"],
            result_summary=data["result_summary"],
            final_action_taken=data.get("final_action_taken")
        )
        
        for event_dict in data["events"]:
            event = ReasoningEvent(
                event_id=event_dict["event_id"],
                event_type=EventType(event_dict["event_type"]),
                timestamp=datetime.fromisoformat(event_dict["timestamp"]),
                severity=SeverityLevel(event_dict["severity"]),
                agent_id=event_dict["agent_id"],
                goal_id=event_dict["goal_id"],
                phase=event_dict["phase"],
                message=event_dict["message"],
                context=event_dict["context"],
                decision_point=event_dict.get("decision_point"),
                options_considered=event_dict.get("options_considered", []),
                option_selected=event_dict.get("option_selected"),
                reasoning_brief=event_dict.get("reasoning_brief", ""),
                confidence_score=event_dict.get("confidence_score"),
                action_performed=event_dict.get("action_performed"),
                action_result=event_dict.get("action_result"),
                duration_ms=event_dict.get("duration_ms"),
                error_type=event_dict.get("error_type"),
                error_message=event_dict.get("error_message"),
                stack_trace=event_dict.get("stack_trace"),
                recovery_suggestion=event_dict.get("recovery_suggestion")
            )
            session.events.append(event)
        
        return session
    
    def list_sessions(self) -> List[ReasoningSession]:
        """List all saved sessions."""
        sessions = []
        for session_file in self.output_dir.glob("*.json"):
            session_id = session_file.stem
            session = self.load_session(session_id)
            if session:
                sessions.append(session)
        
        return sorted(
            sessions,
            key=lambda s: s.started_at,
            reverse=True
        )


# Context manager for convenience
from contextlib import contextmanager

@contextmanager
def trace_execution(tracer: ReasoningTracer, goal_id: str, goal_title: str):
    """Context manager for tracing a complete execution."""
    session = tracer.start_session(goal_id, goal_title)
    try:
        yield session
        tracer.end_session(True, "Execution completed successfully")
    except Exception as e:
        tracer.record_error(
            error_type=type(e).__name__,
            error_message=str(e),
            stack_trace=str(e.__traceback__)
        )
        tracer.end_session(False, f"Execution failed: {str(e)}")
        raise

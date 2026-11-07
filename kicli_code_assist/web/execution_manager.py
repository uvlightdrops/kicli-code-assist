"""
Phase 5.5.2.I2: WebSocket Streaming Execution Manager

Manages agent execution lifecycle with WebSocket streaming:
- Creates execution sessions
- Handles transparency module integration
- Manages event emission and cleanup
- Tracks active executions
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Optional, Callable, Any
from pathlib import Path
from threading import Lock

logger = logging.getLogger("kicli-web")


class ExecutionSession:
    """Represents a single agent execution session."""
    
    def __init__(self, execution_id: str, goal_title: str, socketio, namespace: str = "/agent/execution"):
        self.execution_id = execution_id
        self.goal_title = goal_title
        self.socketio = socketio
        self.namespace = namespace
        self.room = f"execution:{execution_id}"
        
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.status = "initialized"  # initialized → running → completed → failed
        self.event_count = 0
        self.error: Optional[str] = None
        
        # Import event emitter (avoid circular import)
        from kicli_code_assist.agent.transparency_event_emitter import TransparencyEventEmitter
        self.emitter = TransparencyEventEmitter(socketio, execution_id)
    
    def start(self) -> None:
        """Mark session as running and emit start event."""
        self.status = "running"
        self.emitter.start_execution(self.execution_id, self.goal_title)
    
    def complete(self, success: bool, duration_ms: int = 0, summary: str = "") -> None:
        """Mark session as complete and emit end event."""
        self.completed_at = datetime.now()
        self.status = "completed" if success else "failed"
        self.emitter.finish_execution(success, summary, duration_ms)
    
    def error_occurred(self, error: str) -> None:
        """Record error and update status."""
        self.error = error
        self.status = "failed"
        self.emitter.emit_error("execution_error", error)
    
    def get_duration_ms(self) -> int:
        """Get execution duration in milliseconds."""
        if self.completed_at:
            delta = self.completed_at - self.created_at
        else:
            delta = datetime.now() - self.created_at
        return int(delta.total_seconds() * 1000)
    
    def cleanup(self) -> None:
        """Clean up session resources."""
        logger.info(f"Cleaning up execution {self.execution_id}: "
                   f"{self.event_count} events, {self.get_duration_ms()}ms")


class ExecutionManager:
    """Manages WebSocket execution lifecycle for agent operations.
    
    Handles:
    - Session creation and lifecycle
    - Event streaming via transparency modules
    - Cleanup and resource management
    """
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.sessions: Dict[str, ExecutionSession] = {}
        self.lock = Lock()
    
    def create_session(self, goal_title: str) -> ExecutionSession:
        """Create new execution session.
        
        Args:
            goal_title: Title/description of goal
        
        Returns:
            ExecutionSession with unique execution_id
        """
        execution_id = str(uuid.uuid4())
        
        with self.lock:
            session = ExecutionSession(execution_id, goal_title, self.socketio)
            self.sessions[execution_id] = session
        
        logger.info(f"Created execution session: {execution_id}")
        return session
    
    def get_session(self, execution_id: str) -> Optional[ExecutionSession]:
        """Get session by ID.
        
        Args:
            execution_id: Unique execution identifier
        
        Returns:
            ExecutionSession or None if not found
        """
        return self.sessions.get(execution_id)
    
    def end_session(self, execution_id: str, success: bool = True, summary: str = "") -> None:
        """End and cleanup execution session.
        
        Args:
            execution_id: Unique execution identifier
            success: Whether execution succeeded
            summary: Execution summary/result
        """
        with self.lock:
            session = self.sessions.get(execution_id)
            if session:
                duration = session.get_duration_ms()
                session.complete(success, duration, summary)
                session.cleanup()
    
    def list_active_sessions(self) -> list[str]:
        """Get list of active execution IDs.
        
        Returns:
            List of execution IDs in 'running' or 'initialized' state
        """
        with self.lock:
            return [
                eid for eid, session in self.sessions.items()
                if session.status in ("initialized", "running")
            ]
    
    def cleanup_expired_sessions(self, max_age_seconds: int = 3600) -> int:
        """Clean up expired sessions.
        
        Args:
            max_age_seconds: Maximum session age (default 1 hour)
        
        Returns:
            Number of sessions cleaned up
        """
        now = datetime.now()
        expired = []
        
        with self.lock:
            for eid, session in list(self.sessions.items()):
                age_seconds = (now - session.created_at).total_seconds()
                if age_seconds > max_age_seconds and session.status != "running":
                    session.cleanup()
                    del self.sessions[eid]
                    expired.append(eid)
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
        
        return len(expired)


# Global execution manager (singleton)
_execution_manager: Optional[ExecutionManager] = None

def init_execution_manager(socketio) -> ExecutionManager:
    """Initialize global execution manager."""
    global _execution_manager
    _execution_manager = ExecutionManager(socketio)
    return _execution_manager

def get_execution_manager() -> ExecutionManager:
    """Get global execution manager."""
    if _execution_manager is None:
        raise RuntimeError("ExecutionManager not initialized. Call init_execution_manager() first.")
    return _execution_manager

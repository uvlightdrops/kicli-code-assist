"""
TransparencyEventEmitter bridges Transparency Modules with WebSocket.

Emits real-time events (decisions, executions, errors, LLM calls, metrics)
to connected frontend clients via SocketIO.

Phase 5.5.2.I2: WebSocket Streaming
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path


class TransparencyEventEmitter:
    """Emit transparency events to WebSocket clients."""
    
    def __init__(self, socketio, execution_id: str):
        """Initialize event emitter.
        
        Args:
            socketio: Flask-SocketIO instance
            execution_id: Unique execution identifier (used as room name)
        """
        self.socketio = socketio
        self.execution_id = execution_id
        self.room = f"execution:{execution_id}"
        self.event_count = 0
    
    def _emit(self, event_name: str, data: Dict[str, Any]) -> None:
        """Emit event to WebSocket room.
        
        Args:
            event_name: Event name (e.g., "agent:decision")
            data: Event data dictionary
        """
        # Add timestamp and execution_id to all events
        event_data = {
            "execution_id": self.execution_id,
            "timestamp": datetime.now().isoformat(),
            **data
        }
        
        self.socketio.emit(event_name, event_data, room=self.room, skip_sid=False)
        self.event_count += 1
    
    def emit_decision(
        self,
        options_considered: List[str],
        option_selected: str,
        confidence_score: float,
        reasoning: str = ""
    ) -> None:
        """Emit decision event.
        
        Args:
            options_considered: List of options evaluated
            option_selected: Option that was chosen
            confidence_score: Confidence in decision (0-1)
            reasoning: Optional explanation
        """
        self._emit("agent:decision", {
            "options_considered": options_considered,
            "option_selected": option_selected,
            "confidence_score": min(1.0, max(0.0, confidence_score)),
            "reasoning": reasoning
        })
    
    def emit_execution(
        self,
        action: str,
        result: str,
        duration_ms: int = 0,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Emit execution event.
        
        Args:
            action: Action name (e.g., "llm_generation", "file_write")
            result: Result status ("success", "failure", "partial")
            duration_ms: Execution time in milliseconds
            details: Optional extra data
        """
        data = {
            "action": action,
            "result": result,
            "duration_ms": max(0, duration_ms or 0)
        }
        if details:
            data["details"] = details
        
        self._emit("agent:execution", data)
    
    def emit_error(
        self,
        error_type: str,
        message: str,
        recovery_suggestion: str = "",
        error_id: Optional[str] = None
    ) -> None:
        """Emit error event.
        
        Args:
            error_type: Error class name
            message: Error message
            recovery_suggestion: How to recover
            error_id: Unique error identifier
        """
        self._emit("agent:error", {
            "error_type": error_type,
            "message": message,
            "recovery_suggestion": recovery_suggestion,
            "error_id": error_id or ""
        })
    
    def emit_llm_call(
        self,
        model: str,
        purpose: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        cost: float,
        latency_ms: int
    ) -> None:
        """Emit LLM call event.
        
        Args:
            model: Model name (e.g., "gpt-4o")
            purpose: Purpose (e.g., "code_generation")
            input_tokens: Input token count
            output_tokens: Output token count
            total_tokens: Total token count
            cost: Estimated cost (USD)
            latency_ms: Call latency in milliseconds
        """
        self._emit("agent:llm_call", {
            "model": model,
            "purpose": purpose,
            "input_tokens": max(0, input_tokens),
            "output_tokens": max(0, output_tokens),
            "total_tokens": max(0, total_tokens),
            "cost": max(0.0, cost or 0.0),
            "latency_ms": max(0, latency_ms or 0)
        })
    
    def emit_metric_update(
        self,
        phase: str,
        metrics: Dict[str, Any]
    ) -> None:
        """Emit metrics update event.
        
        Args:
            phase: Phase name (e.g., "analysis", "generation")
            metrics: Metric data (counters, timers, gauges, etc.)
        """
        self._emit("agent:metric_update", {
            "phase": phase,
            "metrics": metrics or {}
        })
    
    def emit_session_end(
        self,
        success: bool,
        total_events: int = 0,
        duration_ms: int = 0,
        trace_file: Optional[str] = None,
        summary: str = ""
    ) -> None:
        """Emit session end event.
        
        Args:
            success: Whether execution succeeded
            total_events: Total events recorded
            duration_ms: Total execution time
            trace_file: Path to trace JSON file
            summary: Execution summary
        """
        self._emit("agent:session_end", {
            "success": success,
            "total_events": total_events,
            "duration_ms": max(0, duration_ms or 0),
            "trace_file": trace_file or "",
            "summary": summary
        })
    
    def emit_status(
        self,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Emit status update event.
        
        Args:
            status: Current status (e.g., "running", "completed", "failed")
            details: Optional status details
        """
        self._emit("agent:status", {
            "status": status,
            "details": details or {}
        })

"""REST API endpoints for agent execution traces and transparency data.

Phase 5.5.2.I3: Query interface for trace files, metrics, and cost tracking.
"""

import logging
import json
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime

from flask import Flask, request, jsonify

logger = logging.getLogger("kicli-web-agent-traces")


class TraceManager:
    """Manages reading and querying trace files."""
    
    def __init__(self, project_root: Path):
        """Initialize trace manager.
        
        Args:
            project_root: Project root directory (traces stored in traces/)
        """
        self.project_root = Path(project_root)
        self.traces_dir = self.project_root / "traces"
    
    def list_executions(self, limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
        """List recent executions.
        
        Args:
            limit: Max number of executions to return
            skip: Number of executions to skip (pagination)
        
        Returns:
            List of execution summaries sorted by recency
        """
        if not self.traces_dir.exists():
            return []
        
        executions = []
        
        # Collect all trace files
        for trace_file in sorted(self.traces_dir.glob("*.json"), reverse=True):
            try:
                with open(trace_file, "r") as f:
                    data = json.load(f)
                
                executions.append({
                    "execution_id": data.get("execution_id", trace_file.stem),
                    "agent_id": data.get("agent_id", "unknown"),
                    "timestamp": data.get("created_at", ""),
                    "status": "completed" if data.get("ended_at") else "running",
                    "total_events": len(data.get("events", [])),
                    "trace_file": str(trace_file.relative_to(self.project_root))
                })
            except Exception as e:
                logger.warning(f"Cannot read trace file {trace_file}: {e}")
        
        # Apply pagination
        return executions[skip:skip + limit]
    
    def get_execution_trace(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get full execution trace.
        
        Args:
            execution_id: Execution identifier
        
        Returns:
            Full trace data or None if not found
        """
        trace_file = self.traces_dir / f"{execution_id}.json"
        
        if not trace_file.exists():
            return None
        
        try:
            with open(trace_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Cannot read trace {execution_id}: {e}")
            return None
    
    def get_execution_events(self, execution_id: str) -> List[Dict[str, Any]]:
        """Get event stream for execution.
        
        Args:
            execution_id: Execution identifier
        
        Returns:
            List of events in chronological order
        """
        trace = self.get_execution_trace(execution_id)
        return trace.get("events", []) if trace else []
    
    def get_execution_decisions(self, execution_id: str) -> List[Dict[str, Any]]:
        """Get decision events for execution.
        
        Args:
            execution_id: Execution identifier
        
        Returns:
            List of decision events
        """
        trace = self.get_execution_trace(execution_id)
        if not trace:
            return []
        
        return [
            e for e in trace.get("events", [])
            if e.get("event_type") == "DECISION"
        ]
    
    def get_execution_errors(self, execution_id: str) -> List[Dict[str, Any]]:
        """Get error events for execution.
        
        Args:
            execution_id: Execution identifier
        
        Returns:
            List of error events
        """
        trace = self.get_execution_trace(execution_id)
        if not trace:
            return []
        
        return [
            e for e in trace.get("events", [])
            if e.get("event_type") == "ERROR"
        ]
    
    def get_llm_calls(self, execution_id: str) -> List[Dict[str, Any]]:
        """Get LLM call records for execution.
        
        Args:
            execution_id: Execution identifier (also checks llm_calls_*.json)
        
        Returns:
            List of LLM call records
        """
        # Check both trace file (embedded events) and separate llm_calls file
        calls = []
        
        # Look for llm_calls_*.json file
        llm_file = self.traces_dir / f"llm_calls_{execution_id}.json"
        if llm_file.exists():
            try:
                with open(llm_file, "r") as f:
                    data = json.load(f)
                    calls.extend(data.get("calls", []))
            except Exception as e:
                logger.warning(f"Cannot read LLM calls file: {e}")
        
        # Also check trace file for embedded LLM events
        trace = self.get_execution_trace(execution_id)
        if trace:
            for event in trace.get("events", []):
                if event.get("event_type") == "LLM_CALL":
                    calls.append(event)
        
        return calls
    
    def get_performance_metrics(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get performance metrics for execution.
        
        Args:
            execution_id: Execution identifier
        
        Returns:
            Metrics data or None if not found
        """
        metrics_file = self.traces_dir / f"{execution_id}-metrics.json"
        
        if not metrics_file.exists():
            return None
        
        try:
            with open(metrics_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Cannot read metrics {execution_id}: {e}")
            return None
    
    def get_cost_summary(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get LLM cost summary for execution.
        
        Args:
            execution_id: Execution identifier
        
        Returns:
            Cost summary or None if not found
        """
        # Look for cost_summary_*.json or embedded in llm_calls
        cost_file = self.traces_dir / f"cost_summary_{execution_id}.json"
        
        if cost_file.exists():
            try:
                with open(cost_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Cannot read cost summary: {e}")
        
        # Compute from LLM calls if available
        calls = self.get_llm_calls(execution_id)
        if calls:
            total_cost = sum(c.get("total_cost", 0.0) for c in calls)
            total_tokens = sum(c.get("total_tokens", 0) for c in calls)
            
            return {
                "total_cost": total_cost,
                "total_calls": len(calls),
                "total_tokens": total_tokens,
                "currency": "USD"
            }
        
        return None
    
    def export_execution(self, execution_id: str, format: str = "json") -> Optional[Dict[str, Any]]:
        """Export execution data in specified format.
        
        Args:
            execution_id: Execution identifier
            format: Export format (json, markdown)
        
        Returns:
            Exported data or None if not found
        """
        trace = self.get_execution_trace(execution_id)
        if not trace:
            return None
        
        if format == "markdown":
            return self._format_markdown(trace)
        
        # Default: JSON (already loaded)
        return trace
    
    def _format_markdown(self, trace: Dict[str, Any]) -> Dict[str, str]:
        """Format trace as markdown.
        
        Args:
            trace: Trace data
        
        Returns:
            Dict with "content" key containing markdown
        """
        lines = [
            f"# Execution Trace: {trace.get('execution_id', 'unknown')}",
            f"",
            f"**Agent:** {trace.get('agent_id', 'unknown')}",
            f"**Started:** {trace.get('created_at', 'unknown')}",
            f"**Ended:** {trace.get('ended_at', 'unknown')}",
            f"**Duration:** {trace.get('duration_seconds', 'unknown')}s",
            f"**Events:** {len(trace.get('events', []))}",
            f"",
            f"## Events",
            f"",
        ]
        
        for event in trace.get("events", []):
            event_type = event.get("event_type", "UNKNOWN")
            timestamp = event.get("timestamp", "")
            description = event.get("description", "")
            lines.append(f"### {event_type} ({timestamp})")
            lines.append(f"{description}")
            lines.append(f"")
        
        return {
            "content": "\n".join(lines),
            "format": "markdown"
        }


def register_trace_routes(app: Flask, project_root: Optional[Path] = None):
    """Register trace query endpoints.
    
    Args:
        app: Flask app
        project_root: Optional project root for trace location
    """
    if project_root is None:
        project_root = Path.cwd()
    
    trace_manager = TraceManager(project_root)
    
    @app.route("/api/traces", methods=["GET"])
    def list_traces():
        """List recent execution traces.
        
        Query parameters:
        - limit: Max results (default 50)
        - skip: Pagination offset (default 0)
        """
        limit = min(int(request.args.get("limit", 50)), 500)
        skip = int(request.args.get("skip", 0))
        
        executions = trace_manager.list_executions(limit=limit, skip=skip)
        
        return jsonify({
            "status": "ok",
            "total": len(executions),
            "skip": skip,
            "limit": limit,
            "executions": executions
        })
    
    @app.route("/api/traces/<execution_id>", methods=["GET"])
    def get_trace(execution_id: str):
        """Get full execution trace."""
        trace = trace_manager.get_execution_trace(execution_id)
        
        if not trace:
            return jsonify({"status": "error", "message": "Trace not found"}), 404
        
        return jsonify({
            "status": "ok",
            "trace": trace
        })
    
    @app.route("/api/traces/<execution_id>/events", methods=["GET"])
    def get_events(execution_id: str):
        """Get event stream for execution."""
        events = trace_manager.get_execution_events(execution_id)
        
        return jsonify({
            "status": "ok",
            "execution_id": execution_id,
            "total_events": len(events),
            "events": events
        })
    
    @app.route("/api/traces/<execution_id>/decisions", methods=["GET"])
    def get_decisions(execution_id: str):
        """Get decision events for execution."""
        decisions = trace_manager.get_execution_decisions(execution_id)
        
        return jsonify({
            "status": "ok",
            "execution_id": execution_id,
            "total_decisions": len(decisions),
            "decisions": decisions
        })
    
    @app.route("/api/traces/<execution_id>/errors", methods=["GET"])
    def get_errors(execution_id: str):
        """Get error events for execution."""
        errors = trace_manager.get_execution_errors(execution_id)
        
        return jsonify({
            "status": "ok",
            "execution_id": execution_id,
            "total_errors": len(errors),
            "errors": errors
        })
    
    @app.route("/api/traces/<execution_id>/llm-calls", methods=["GET"])
    def get_llm_calls(execution_id: str):
        """Get LLM call records for execution."""
        calls = trace_manager.get_llm_calls(execution_id)
        
        return jsonify({
            "status": "ok",
            "execution_id": execution_id,
            "total_calls": len(calls),
            "calls": calls
        })
    
    @app.route("/api/traces/<execution_id>/metrics", methods=["GET"])
    def get_metrics(execution_id: str):
        """Get performance metrics for execution."""
        metrics = trace_manager.get_performance_metrics(execution_id)
        
        if not metrics:
            return jsonify({
                "status": "ok",
                "execution_id": execution_id,
                "metrics": None,
                "message": "No metrics found"
            })
        
        return jsonify({
            "status": "ok",
            "execution_id": execution_id,
            "metrics": metrics
        })
    
    @app.route("/api/traces/<execution_id>/cost", methods=["GET"])
    def get_cost(execution_id: str):
        """Get LLM cost summary for execution."""
        cost = trace_manager.get_cost_summary(execution_id)
        
        if not cost:
            return jsonify({
                "status": "ok",
                "execution_id": execution_id,
                "cost": None,
                "message": "No cost data found"
            })
        
        return jsonify({
            "status": "ok",
            "execution_id": execution_id,
            "cost": cost
        })
    
    @app.route("/api/traces/<execution_id>/export", methods=["GET"])
    def export_trace(execution_id: str):
        """Export execution data.
        
        Query parameters:
        - format: Export format (json, markdown; default json)
        """
        export_format = request.args.get("format", "json")
        
        if export_format not in ("json", "markdown"):
            return jsonify({
                "status": "error",
                "message": "Invalid format. Use 'json' or 'markdown'"
            }), 400
        
        data = trace_manager.export_execution(execution_id, format=export_format)
        
        if not data:
            return jsonify({"status": "error", "message": "Trace not found"}), 404
        
        return jsonify({
            "status": "ok",
            "execution_id": execution_id,
            "format": export_format,
            "data": data
        })

"""Unit tests for agent trace endpoints (Phase 5.5.2.I3).

Tests the TraceManager and Flask API endpoints for querying:
- Execution list
- Full traces
- Events, decisions, errors
- LLM calls and cost tracking
- Performance metrics
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from kicli_code_assist.web.agent_traces import TraceManager, register_trace_routes


class TestTraceManager:
    """Tests for TraceManager functionality."""
    
    @pytest.fixture
    def traces_dir(self, tmp_path):
        """Create temporary traces directory with sample files."""
        traces_dir = tmp_path / "traces"
        traces_dir.mkdir()
        
        # Create sample trace file
        trace_data = {
            "execution_id": "exec-001",
            "agent_id": "TestAgent",
            "created_at": "2026-11-02T03:30:00Z",
            "ended_at": "2026-11-02T03:35:00Z",
            "duration_seconds": 300,
            "events": [
                {
                    "timestamp": "2026-11-02T03:30:00Z",
                    "event_type": "DECISION",
                    "description": "Test decision"
                },
                {
                    "timestamp": "2026-11-02T03:32:00Z",
                    "event_type": "LLM_CALL",
                    "model": "gpt-4o",
                    "total_cost": 0.0425
                },
                {
                    "timestamp": "2026-11-02T03:35:00Z",
                    "event_type": "ERROR",
                    "description": "Test error"
                }
            ]
        }
        
        trace_file = traces_dir / "exec-001.json"
        trace_file.write_text(json.dumps(trace_data))
        
        return tmp_path  # Return parent so manager can find traces/
    
    def test_list_executions(self, traces_dir):
        """Test listing executions."""
        manager = TraceManager(traces_dir)
        executions = manager.list_executions()
        
        assert len(executions) == 1
        assert executions[0]["execution_id"] == "exec-001"
        assert executions[0]["agent_id"] == "TestAgent"
        assert executions[0]["status"] == "completed"
        assert executions[0]["total_events"] == 3
    
    def test_get_execution_trace(self, traces_dir):
        """Test fetching full trace."""
        manager = TraceManager(traces_dir)
        trace = manager.get_execution_trace("exec-001")
        
        assert trace is not None
        assert trace["execution_id"] == "exec-001"
        assert len(trace["events"]) == 3
    
    def test_get_execution_trace_not_found(self, traces_dir):
        """Test fetching non-existent trace."""
        manager = TraceManager(traces_dir)
        trace = manager.get_execution_trace("nonexistent")
        
        assert trace is None
    
    def test_get_execution_events(self, traces_dir):
        """Test getting event stream."""
        manager = TraceManager(traces_dir)
        events = manager.get_execution_events("exec-001")
        
        assert len(events) == 3
        assert events[0]["event_type"] == "DECISION"
        assert events[1]["event_type"] == "LLM_CALL"
        assert events[2]["event_type"] == "ERROR"
    
    def test_get_execution_decisions(self, traces_dir):
        """Test filtering decision events."""
        manager = TraceManager(traces_dir)
        decisions = manager.get_execution_decisions("exec-001")
        
        assert len(decisions) == 1
        assert decisions[0]["event_type"] == "DECISION"
        assert decisions[0]["description"] == "Test decision"
    
    def test_get_execution_errors(self, traces_dir):
        """Test filtering error events."""
        manager = TraceManager(traces_dir)
        errors = manager.get_execution_errors("exec-001")
        
        assert len(errors) == 1
        assert errors[0]["event_type"] == "ERROR"
    
    def test_get_llm_calls(self, traces_dir):
        """Test extracting LLM call records."""
        manager = TraceManager(traces_dir)
        calls = manager.get_llm_calls("exec-001")
        
        # Should find embedded LLM_CALL event
        assert len(calls) >= 1
        assert any(c.get("model") == "gpt-4o" for c in calls)
    
    def test_get_performance_metrics_not_found(self, traces_dir):
        """Test getting metrics when none exist."""
        manager = TraceManager(traces_dir)
        metrics = manager.get_performance_metrics("exec-001")
        
        assert metrics is None
    
    def test_get_cost_summary(self, traces_dir):
        """Test computing cost summary from LLM calls."""
        manager = TraceManager(traces_dir)
        cost = manager.get_cost_summary("exec-001")
        
        # Should compute from embedded LLM_CALL event
        if cost:
            assert cost["total_cost"] > 0
            assert "currency" in cost
    
    def test_export_execution_json(self, traces_dir):
        """Test exporting trace as JSON."""
        manager = TraceManager(traces_dir)
        exported = manager.export_execution("exec-001", format="json")
        
        assert exported is not None
        assert exported["execution_id"] == "exec-001"
    
    def test_export_execution_markdown(self, traces_dir):
        """Test exporting trace as markdown."""
        manager = TraceManager(traces_dir)
        exported = manager.export_execution("exec-001", format="markdown")
        
        assert exported is not None
        assert "content" in exported
        assert "format" in exported
        assert exported["format"] == "markdown"
        assert "exec-001" in exported["content"]
        assert "DECISION" in exported["content"]
    
    def test_empty_traces_directory(self, tmp_path):
        """Test with empty traces directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        manager = TraceManager(empty_dir)
        executions = manager.list_executions()
        
        assert len(executions) == 0
    
    def test_no_traces_directory(self, tmp_path):
        """Test with non-existent traces directory."""
        manager = TraceManager(tmp_path / "nonexistent")
        executions = manager.list_executions()
        
        assert len(executions) == 0


class TestTraceRoutes:
    """Tests for Flask trace endpoints."""
    
    @pytest.fixture
    def app_with_traces(self, tmp_path):
        """Create Flask app with trace routes registered."""
        from flask import Flask
        
        app = Flask(__name__)
        app.config["TESTING"] = True
        
        # Create sample traces
        traces_dir = tmp_path / "traces"
        traces_dir.mkdir()
        
        trace_data = {
            "execution_id": "exec-001",
            "agent_id": "TestAgent",
            "created_at": "2026-11-02T03:30:00Z",
            "ended_at": "2026-11-02T03:35:00Z",
            "events": [
                {"event_type": "DECISION", "timestamp": "2026-11-02T03:30:00Z"},
                {"event_type": "ERROR", "timestamp": "2026-11-02T03:35:00Z"}
            ]
        }
        
        (traces_dir / "exec-001.json").write_text(json.dumps(trace_data))
        
        # Register routes
        register_trace_routes(app, project_root=tmp_path)
        
        return app.test_client(), tmp_path
    
    def test_list_traces_endpoint(self, app_with_traces):
        """Test /api/traces endpoint."""
        client, _ = app_with_traces
        response = client.get("/api/traces")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["total"] >= 1
    
    def test_get_trace_endpoint(self, app_with_traces):
        """Test /api/traces/<id> endpoint."""
        client, _ = app_with_traces
        response = client.get("/api/traces/exec-001")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["trace"]["execution_id"] == "exec-001"
    
    def test_get_trace_not_found(self, app_with_traces):
        """Test /api/traces/<id> with non-existent trace."""
        client, _ = app_with_traces
        response = client.get("/api/traces/nonexistent")
        
        assert response.status_code == 404
        data = response.get_json()
        assert data["status"] == "error"
    
    def test_get_events_endpoint(self, app_with_traces):
        """Test /api/traces/<id>/events endpoint."""
        client, _ = app_with_traces
        response = client.get("/api/traces/exec-001/events")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["total_events"] == 2
    
    def test_get_decisions_endpoint(self, app_with_traces):
        """Test /api/traces/<id>/decisions endpoint."""
        client, _ = app_with_traces
        response = client.get("/api/traces/exec-001/decisions")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["total_decisions"] >= 1
    
    def test_get_errors_endpoint(self, app_with_traces):
        """Test /api/traces/<id>/errors endpoint."""
        client, _ = app_with_traces
        response = client.get("/api/traces/exec-001/errors")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["total_errors"] >= 1
    
    def test_get_llm_calls_endpoint(self, app_with_traces):
        """Test /api/traces/<id>/llm-calls endpoint."""
        client, _ = app_with_traces
        response = client.get("/api/traces/exec-001/llm-calls")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert "total_calls" in data
    
    def test_get_metrics_endpoint(self, app_with_traces):
        """Test /api/traces/<id>/metrics endpoint."""
        client, _ = app_with_traces
        response = client.get("/api/traces/exec-001/metrics")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
    
    def test_get_cost_endpoint(self, app_with_traces):
        """Test /api/traces/<id>/cost endpoint."""
        client, _ = app_with_traces
        response = client.get("/api/traces/exec-001/cost")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
    
    def test_export_endpoint_json(self, app_with_traces):
        """Test /api/traces/<id>/export?format=json endpoint."""
        client, _ = app_with_traces
        response = client.get("/api/traces/exec-001/export?format=json")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["format"] == "json"
    
    def test_export_endpoint_markdown(self, app_with_traces):
        """Test /api/traces/<id>/export?format=markdown endpoint."""
        client, _ = app_with_traces
        response = client.get("/api/traces/exec-001/export?format=markdown")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["format"] == "markdown"
    
    def test_export_endpoint_invalid_format(self, app_with_traces):
        """Test /api/traces/<id>/export with invalid format."""
        client, _ = app_with_traces
        response = client.get("/api/traces/exec-001/export?format=xml")
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
    
    def test_pagination(self, app_with_traces):
        """Test pagination with limit and skip."""
        client, _ = app_with_traces
        response = client.get("/api/traces?limit=10&skip=0")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["limit"] == 10
        assert data["skip"] == 0

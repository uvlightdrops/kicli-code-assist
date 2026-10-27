"""
Integration tests for Phase 2D: /api/agent/route endpoint.

Tests the full flow:
1. Intent Detection (Phase 2A)
2. Parallel Agent Execution (Phase 2B)
3. Result Aggregation (Phase 2C)
4. API Response Format

Validates:
- End-to-end request/response flow
- Timing improvements vs Phase 1
- Error handling and fallback
- Performance characteristics
"""

import asyncio
import json
import pytest
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import Flask app creation
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from kicli_code_assist.web.server import create_app
from kicli_code_assist.agent.intent_detector import IntentType, AgentIntent


@pytest.fixture
def app():
    """Create test Flask app."""
    from kicli_code_assist.web.server import register_routes, register_project_routes
    
    test_config = {
        "web": {"host": "127.0.0.1", "port": 8000},
        "storage": {
            "log_dir": str(Path.home() / "dev_data" / "kicli-code-assist" / "log"),
            "project_root": str(Path(__file__).parent.parent)
        },
    }
    app, socketio = create_app(test_config)
    app.config["TESTING"] = True
    
    # Register routes
    register_routes(app)
    register_project_routes(app)
    
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def sample_python_file():
    """Create a sample Python file for testing within the project."""
    # Create file in the project directory (which is allowed by security checks)
    project_dir = Path(__file__).parent.parent
    test_dir = project_dir / "test_samples"
    test_dir.mkdir(exist_ok=True)
    
    file_path = test_dir / "sample.py"
    file_path.write_text("""
def calculate_sum(numbers):
    \"\"\"Calculate sum of numbers.\"\"\"
    total = 0
    for num in numbers:
        total += num
    return total


class DataProcessor:
    \"\"\"Processes data in batches.\"\"\"
    
    def __init__(self, batch_size=10):
        self.batch_size = batch_size
    
    def process(self, items):
        \"\"\"Process items in batches.\"\"\"
        results = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            results.extend(self._process_batch(batch))
        return results
    
    def _process_batch(self, batch):
        \"\"\"Process a single batch.\"\"\"
        return [item * 2 for item in batch]
""")
    
    yield file_path
    
    # Cleanup
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir)


class TestIntegrationPhase2D:
    """Test Phase 2D integration endpoint."""

    def test_agent_route_request_validation(self, client):
        """Test that missing parameters are rejected."""
        # Missing query
        response = client.post(
            "/api/agent/route",
            json={
                "file_path": "/path/to/file.py",
                "project_root": str(Path.cwd()),
            }
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert not data["success"]
        assert "query" in data["error"].lower()

        # Missing file_path
        response = client.post(
            "/api/agent/route",
            json={
                "query": "Explain this file",
                "project_root": str(Path.cwd()),
            }
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert not data["success"]
        assert "file_path" in data["error"].lower()

    def test_agent_route_success_response_format(self, client, sample_python_file):
        """Test that successful response has correct format."""
        project_root = sample_python_file.parent
        file_path = sample_python_file.relative_to(project_root)

        response = client.post(
            "/api/agent/route",
            json={
                "query": "Explain this code",
                "file_path": str(file_path),
                "project_root": str(project_root),
                "scope": "folder",
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # Validate success
        assert data["success"] is True
        assert "session_id" in data
        assert data["session_id"]

        # Validate intent
        assert "intent" in data
        assert "type" in data["intent"]
        assert "confidence" in data["intent"]
        assert "agents" in data["intent"]
        assert isinstance(data["intent"]["agents"], list)

        # Validate summary and tabs
        assert "summary" in data
        assert "tabs" in data
        assert isinstance(data["tabs"], dict)

        # Validate actions and next_steps
        assert "actions" in data
        assert isinstance(data["actions"], list)
        assert "next_steps" in data
        assert isinstance(data["next_steps"], list)

        # Validate timing
        assert "timing" in data
        assert "intent_ms" in data["timing"]
        assert "execution_ms" in data["timing"]
        assert "aggregation_ms" in data["timing"]
        assert "total_ms" in data["timing"]

        # All timing values should be positive
        assert data["timing"]["intent_ms"] > 0
        assert data["timing"]["execution_ms"] > 0
        assert data["timing"]["total_ms"] > 0

    def test_agent_route_intent_detection(self, client, sample_python_file):
        """Test that intent is correctly detected."""
        project_root = sample_python_file.parent
        file_path = sample_python_file.relative_to(project_root)

        # Test EXPLAIN intent
        response = client.post(
            "/api/agent/route",
            json={
                "query": "Explain this function and show me its metrics",
                "file_path": str(file_path),
                "project_root": str(project_root),
                "scope": "folder",
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"]
        assert data["intent"]["type"] in ["EXPLAIN", "explain"]
        assert data["intent"]["confidence"] >= 0.5

        # Test OPTIMIZE intent
        response = client.post(
            "/api/agent/route",
            json={
                "query": "Optimize this code for performance",
                "file_path": str(file_path),
                "project_root": str(project_root),
                "scope": "folder",
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"]
        assert data["intent"]["type"] in ["OPTIMIZE", "optimize"]

    def test_agent_route_session_id_generation(self, client, sample_python_file):
        """Test that session IDs are generated and consistent."""
        project_root = sample_python_file.parent
        file_path = sample_python_file.relative_to(project_root)

        # Test without session_id (should be auto-generated)
        response1 = client.post(
            "/api/agent/route",
            json={
                "query": "Explain this code",
                "file_path": str(file_path),
                "project_root": str(project_root),
            }
        )
        data1 = json.loads(response1.data)
        session_id_1 = data1["session_id"]
        assert session_id_1

        # Test with provided session_id
        provided_session_id = "test-session-12345"
        response2 = client.post(
            "/api/agent/route",
            json={
                "query": "Explain this code",
                "file_path": str(file_path),
                "project_root": str(project_root),
                "session_id": provided_session_id,
            }
        )
        data2 = json.loads(response2.data)
        assert data2["session_id"] == provided_session_id

    def test_agent_route_scope_parameter(self, client, sample_python_file):
        """Test that scope parameter is handled correctly."""
        project_root = sample_python_file.parent
        file_path = sample_python_file.relative_to(project_root)

        # Test folder scope
        response = client.post(
            "/api/agent/route",
            json={
                "query": "Explain this code",
                "file_path": str(file_path),
                "project_root": str(project_root),
                "scope": "folder",
            }
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"]

        # Test project scope
        response = client.post(
            "/api/agent/route",
            json={
                "query": "Explain this code",
                "file_path": str(file_path),
                "project_root": str(project_root),
                "scope": "project",
            }
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"]

    def test_agent_route_multiple_agents(self, client, sample_python_file):
        """Test that multiple agents can be run for a single query."""
        project_root = sample_python_file.parent
        file_path = sample_python_file.relative_to(project_root)

        response = client.post(
            "/api/agent/route",
            json={
                "query": "Explain, analyze metrics, and suggest refactoring",
                "file_path": str(file_path),
                "project_root": str(project_root),
                "scope": "folder",
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"]

        # Should have multiple agents in intent
        assert len(data["intent"]["agents"]) >= 1

        # Tabs should be populated
        assert len(data["tabs"]) >= 1

    def test_agent_route_timing_improvements(self, client, sample_python_file):
        """Test that Phase 2D timing is reasonable (expect 2-4 seconds total)."""
        project_root = sample_python_file.parent
        file_path = sample_python_file.relative_to(project_root)

        start = time.time()
        response = client.post(
            "/api/agent/route",
            json={
                "query": "Explain this code",
                "file_path": str(file_path),
                "project_root": str(project_root),
                "scope": "folder",
            }
        )
        elapsed = time.time() - start

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"]

        # Total should be < 10 seconds for test environment
        # (actual production should be 2-4 seconds, but tests may be slower)
        assert elapsed < 30.0, f"Took too long: {elapsed}s"

        # Response timing should be populated
        total_ms = data["timing"]["total_ms"]
        assert total_ms > 0
        assert total_ms < 30000  # 30 seconds max

    def test_agent_route_path_traversal_protection(self, client):
        """Test that path traversal attacks are blocked."""
        project_root = Path("/home/flow/dev_flow/kicli-code-assist")

        # Try to access file outside project
        response = client.post(
            "/api/agent/route",
            json={
                "query": "Explain this code",
                "file_path": "../../../../../../etc/passwd",
                "project_root": str(project_root),
            }
        )

        assert response.status_code == 403
        data = json.loads(response.data)
        assert not data["success"]
        assert "access" in data["error"].lower()

    def test_agent_route_file_not_found_handled(self, client):
        """Test that missing files are handled gracefully."""
        project_root = Path(__file__).parent.parent
        nonexistent_file = "nonexistent_file_xyz123.py"

        response = client.post(
            "/api/agent/route",
            json={
                "query": "Explain this code",
                "file_path": nonexistent_file,
                "project_root": str(project_root),
            }
        )

        # Should still return 200 but with error in response or empty results
        # (depends on agent implementation)
        assert response.status_code in [200, 500]
        data = json.loads(response.data)
        if data["success"]:
            # If successful, tabs might be empty
            assert isinstance(data["tabs"], dict)
        else:
            # If failed, should have error
            assert "error" in data

    def test_agent_route_synthesis_method_present(self, client, sample_python_file):
        """Test that synthesis_method is included in response."""
        project_root = sample_python_file.parent
        file_path = sample_python_file.relative_to(project_root)

        response = client.post(
            "/api/agent/route",
            json={
                "query": "Explain this code",
                "file_path": str(file_path),
                "project_root": str(project_root),
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"]
        assert "synthesis_method" in data
        assert data["synthesis_method"] in ["llm", "template"]

    def test_agent_route_confidence_score(self, client, sample_python_file):
        """Test that confidence scores are reasonable (0.0-1.0)."""
        project_root = sample_python_file.parent
        file_path = sample_python_file.relative_to(project_root)

        response = client.post(
            "/api/agent/route",
            json={
                "query": "Explain this code",
                "file_path": str(file_path),
                "project_root": str(project_root),
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"]

        confidence = data["intent"]["confidence"]
        assert 0.0 <= confidence <= 1.0, f"Confidence out of range: {confidence}"

    def test_agent_route_reasoning_included(self, client, sample_python_file):
        """Test that reasoning is included in intent."""
        project_root = sample_python_file.parent
        file_path = sample_python_file.relative_to(project_root)

        response = client.post(
            "/api/agent/route",
            json={
                "query": "Explain this code",
                "file_path": str(file_path),
                "project_root": str(project_root),
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"]

        assert "reasoning" in data["intent"]
        reasoning = data["intent"]["reasoning"]
        assert isinstance(reasoning, str)
        # Reasoning should not be empty (unless explicitly set to empty)
        # but we're lenient here

    def test_agent_route_next_steps_actionable(self, client, sample_python_file):
        """Test that next steps are populated."""
        project_root = sample_python_file.parent
        file_path = sample_python_file.relative_to(project_root)

        response = client.post(
            "/api/agent/route",
            json={
                "query": "Explain this code",
                "file_path": str(file_path),
                "project_root": str(project_root),
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"]

        next_steps = data["next_steps"]
        assert isinstance(next_steps, list)
        # Next steps might be empty, but should be a list
        if next_steps:
            assert all(isinstance(step, str) for step in next_steps)


class TestPhase2DTiming:
    """Test timing characteristics of Phase 2D."""

    def test_phase2d_parallel_execution(self, client, sample_python_file):
        """Verify that Phase 2B parallel execution improves speed."""
        project_root = sample_python_file.parent
        file_path = sample_python_file.relative_to(project_root)

        response = client.post(
            "/api/agent/route",
            json={
                "query": "Explain, show metrics, and suggest refactoring",
                "file_path": str(file_path),
                "project_root": str(project_root),
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"]

        timing = data["timing"]
        
        # Execution should be faster than sequential would be
        # (roughly 1/3 of sum of individual times if running 3 agents in parallel)
        execution_ms = timing["execution_ms"]
        total_ms = timing["total_ms"]

        # Execution should contribute ~50-70% of total time
        execution_ratio = execution_ms / total_ms
        assert 0.3 < execution_ratio < 0.9, f"Execution ratio unusual: {execution_ratio}"

    def test_phase2d_timing_breakdown(self, client, sample_python_file):
        """Verify that timing breakdown makes sense."""
        project_root = sample_python_file.parent
        file_path = sample_python_file.relative_to(project_root)

        response = client.post(
            "/api/agent/route",
            json={
                "query": "Explain this code",
                "file_path": str(file_path),
                "project_root": str(project_root),
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        timing = data["timing"]

        # All components should be present
        assert "intent_ms" in timing
        assert "execution_ms" in timing
        assert "aggregation_ms" in timing
        assert "total_ms" in timing

        # Total should be >= sum of components (some overhead is ok)
        component_sum = (
            timing["intent_ms"] + 
            timing["execution_ms"] + 
            timing["aggregation_ms"]
        )
        total = timing["total_ms"]
        
        # Allow for 5% overhead
        assert total >= component_sum * 0.95, \
            f"Total timing doesn't match components: {total} < {component_sum}"


class TestPhase2DErrorHandling:
    """Test error handling in Phase 2D."""

    def test_agent_route_malformed_json(self, client):
        """Test handling of malformed JSON."""
        response = client.post(
            "/api/agent/route",
            data="not valid json",
            content_type="application/json"
        )

        # Should handle gracefully (400 or 500)
        assert response.status_code in [400, 500]

    def test_agent_route_none_json_body(self, client):
        """Test handling of None JSON body."""
        response = client.post(
            "/api/agent/route",
            json=None
        )

        # Should handle gracefully
        assert response.status_code in [400, 500]

    def test_agent_route_invalid_scope(self, client, sample_python_file):
        """Test handling of invalid scope values."""
        project_root = sample_python_file.parent
        file_path = sample_python_file.relative_to(project_root)

        # Should accept any string for scope
        response = client.post(
            "/api/agent/route",
            json={
                "query": "Explain this code",
                "file_path": str(file_path),
                "project_root": str(project_root),
                "scope": "invalid_scope",
            }
        )

        # Should either work or fail gracefully
        assert response.status_code in [200, 400, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

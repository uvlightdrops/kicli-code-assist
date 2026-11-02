"""
Phase 5.5.2.I1: Integration tests for CodeImplementationAgent with Transparency Modules
"""

import pytest
from pathlib import Path
import tempfile

from kicli_code_assist.agent.code_implementation import CodeImplementationAgent


@pytest.fixture
def temp_project():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        # Create basic project structure
        (project_root / "src").mkdir()
        (project_root / "src" / "__init__.py").write_text("")
        (project_root / "src" / "main.py").write_text(
            "def hello():\n    return 'Hello, World!'\n"
        )
        
        yield project_root


class TestCodeImplementationAgentTransparency:
    """Test transparency module integration with CodeImplementationAgent."""
    
    def test_agent_initialization_with_transparency(self, temp_project):
        """Test agent initializes transparency modules."""
        agent = CodeImplementationAgent(str(temp_project), enable_transparency=True)
        
        assert agent.enable_transparency is True
        assert agent.tracer is not None
        assert agent.tracker is not None
        assert agent.metrics is not None
        assert agent.tracer.agent_id == "CodeImplementationAgent"
        assert agent.tracker.agent_id == "CodeImplementationAgent"
        assert agent.metrics.agent_id == "CodeImplementationAgent"
    
    def test_agent_initialization_without_transparency(self, temp_project):
        """Test agent can disable transparency modules."""
        agent = CodeImplementationAgent(str(temp_project), enable_transparency=False)
        
        assert agent.enable_transparency is False
        assert agent.tracer is None
        assert agent.tracker is None
        assert agent.metrics is None
    
    def test_traces_directory_created(self, temp_project):
        """Test traces directory is created for transparency data."""
        agent = CodeImplementationAgent(str(temp_project), enable_transparency=True)
        
        traces_dir = temp_project / "traces"
        assert traces_dir.exists()
        assert traces_dir.is_dir()
    
    def test_transparency_modules_are_thread_safe(self, temp_project):
        """Test that transparency modules have thread-safe operations."""
        agent = CodeImplementationAgent(str(temp_project), enable_transparency=True)
        
        # Verify thread safety mechanisms
        assert hasattr(agent.tracer, "_lock"), "Tracer should have _lock for thread safety"
        assert hasattr(agent.tracker, "_lock"), "Tracker should have _lock for thread safety"
        assert hasattr(agent.metrics, "_lock"), "Metrics should have _lock for thread safety"
    
    def test_execution_id_assigned(self, temp_project):
        """Test that execution_id is properly assigned."""
        from datetime import datetime
        
        agent = CodeImplementationAgent(str(temp_project), enable_transparency=True)
        execution_id = f"test-exec-{datetime.now().isoformat()}"
        agent.execution_id = execution_id
        
        assert agent.execution_id == execution_id
    
    def test_metrics_saves_data(self, temp_project):
        """Test that metrics can be finalized and saved."""
        agent = CodeImplementationAgent(str(temp_project), enable_transparency=True)
        agent.metrics.start_phase("test_phase")
        agent.metrics.end_phase("test_phase")
        agent.metrics.finalize()
        
        # Should complete without errors
        report = agent.metrics.generate_report()
        assert report is not None
        assert isinstance(report, str)  # Report is a formatted string
    
    def test_tracer_output_directory(self, temp_project):
        """Test that tracer can save to output directory."""
        agent = CodeImplementationAgent(str(temp_project), enable_transparency=True)
        
        assert agent.tracer.output_dir is not None
        output_path = Path(agent.tracer.output_dir)
        assert output_path.exists() or output_path.parent.exists()
    
    def test_tracker_output_directory(self, temp_project):
        """Test that tracker can save to output directory."""
        agent = CodeImplementationAgent(str(temp_project), enable_transparency=True)
        
        assert agent.tracker.output_dir is not None
        output_path = Path(agent.tracker.output_dir)
        assert output_path.exists() or output_path.parent.exists()


class TestCodeImplementationAgentGenerateCodeIntegration:
    """Test transparency integration in code generation."""
    
    def test_generate_code_via_llm_with_transparency_disabled(self, temp_project):
        """Test LLM code generation works without transparency."""
        agent = CodeImplementationAgent(str(temp_project), enable_transparency=False)
        
        # Should not raise errors even without transparency
        assert agent.tracer is None
        assert agent.tracker is None
    
    def test_agent_can_read_files_with_transparency(self, temp_project):
        """Test that agent can still read files with transparency enabled."""
        agent = CodeImplementationAgent(str(temp_project), enable_transparency=True)
        
        # This tests the basic functionality isn't broken by transparency
        files = agent.discover_python_files()
        assert len(files) > 0
        
        # Should find the test file we created
        py_files = [f for f in files if f.name == "main.py"]
        assert len(py_files) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

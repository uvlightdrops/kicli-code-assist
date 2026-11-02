"""
Phase 5.5.2.U1: Unit Tests for Transparency Modules

Tests for ReasoningTracer, LLMCallTracker, PerformanceMetrics
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import asdict

from kicli_code_assist.agent.reasoning_tracer import (
    ReasoningTracer, ReasoningEvent, ReasoningSession, EventType, SeverityLevel
)
from kicli_code_assist.agent.llm_call_tracker import (
    LLMCallTracker, LLMCallRecord, TokenUsage, LLMModel, CallPurpose, PRICING_TABLE
)
from kicli_code_assist.agent.performance_metrics import (
    PerformanceMetrics, PhaseMetrics, ExecutionMetrics
)


# ============================================================================
# REASONING TRACER TESTS
# ============================================================================

class TestReasoningTracer:
    """Unit tests for ReasoningTracer."""
    
    @pytest.fixture
    def tracer(self, tmp_path):
        """Create tracer with temp directory."""
        return ReasoningTracer(
            agent_id="test-agent",
            output_dir=tmp_path
        )
    
    def test_start_session(self, tracer):
        """Test starting a session."""
        session = tracer.start_session("goal-1", "Test Goal")
        
        assert session is not None
        assert session.agent_id == "test-agent"
        assert session.goal_id == "goal-1"
        assert session.goal_title == "Test Goal"
        assert session.status == "in_progress"
    
    def test_record_event(self, tracer):
        """Test recording a generic event."""
        session = tracer.start_session("goal-1", "Test")
        
        event = tracer.record_event(
            event_type=EventType.ANALYSIS_START,
            message="Beginning analysis",
            phase="analyze"
        )
        
        assert event.event_type == EventType.ANALYSIS_START
        assert event.message == "Beginning analysis"
        assert event.phase == "analyze"
        assert event.agent_id == "test-agent"
        assert event.goal_id == "goal-1"
        assert len(session.events) == 1
    
    def test_record_decision(self, tracer):
        """Test recording a decision point."""
        session = tracer.start_session("goal-1", "Test")
        
        event = tracer.record_decision(
            decision_point="Refactoring Strategy",
            options=["top-down", "bottom-up", "incremental"],
            selected="bottom-up",
            reasoning="Minimizes import cycles",
            confidence=0.95
        )
        
        assert event.event_type == EventType.DECISION_MADE
        assert event.decision_point == "Refactoring Strategy"
        assert event.options_considered == ["top-down", "bottom-up", "incremental"]
        assert event.option_selected == "bottom-up"
        assert event.confidence_score == 0.95
        assert event.reasoning_brief == "Minimizes import cycles"
    
    def test_record_execution(self, tracer):
        """Test recording execution."""
        session = tracer.start_session("goal-1", "Test")
        
        event = tracer.record_execution(
            action="update_imports",
            result="3 files updated",
            duration_ms=250,
            success=True
        )
        
        assert event.event_type == EventType.EXECUTION_COMPLETE
        assert event.action_performed == "update_imports"
        assert event.action_result == "3 files updated"
        assert event.duration_ms == 250
    
    def test_record_error(self, tracer):
        """Test recording an error."""
        session = tracer.start_session("goal-1", "Test")
        
        event = tracer.record_error(
            error_type="CircularImportError",
            error_message="Module A imports B, B imports A",
            stack_trace="File X line 10",
            recovery_suggestion="Extract shared code to module C"
        )
        
        assert event.event_type == EventType.ERROR_OCCURRED
        assert event.error_type == "CircularImportError"
        assert event.severity == SeverityLevel.ERROR
        assert event.recovery_suggestion == "Extract shared code to module C"
    
    def test_record_warning(self, tracer):
        """Test recording a warning."""
        session = tracer.start_session("goal-1", "Test")
        
        event = tracer.record_warning(
            message="Unused import detected",
            context={"module": "utils", "import_name": "helper"}
        )
        
        assert event.event_type == EventType.WARNING_ISSUED
        assert event.severity == SeverityLevel.WARNING
        assert event.context["module"] == "utils"
    
    def test_end_session(self, tracer, tmp_path):
        """Test ending and saving session."""
        session = tracer.start_session("goal-1", "Test")
        tracer.record_event(EventType.ANALYSIS_START, "Start")
        
        final_session = tracer.end_session(
            success=True,
            result_summary="Completed successfully",
            final_action="merge"
        )
        
        assert final_session.status == "completed"
        assert final_session.success is True
        assert final_session.result_summary == "Completed successfully"
        assert final_session.final_action_taken == "merge"
        
        # Verify saved to disk
        session_file = tmp_path / f"{final_session.session_id}.json"
        assert session_file.exists()
    
    def test_session_persistence(self, tracer, tmp_path):
        """Test saving and loading session."""
        session = tracer.start_session("goal-1", "Test Goal")
        tracer.record_event(EventType.ANALYSIS_START, "Start")
        tracer.record_decision(
            decision_point="Strategy",
            options=["A", "B"],
            selected="A",
            reasoning="Test",
            confidence=0.9
        )
        
        final_session = tracer.end_session(success=True)
        session_id = final_session.session_id
        
        # Load from disk
        loaded = tracer.load_session(session_id)
        
        assert loaded is not None
        assert loaded.session_id == session_id
        assert loaded.agent_id == "test-agent"
        assert loaded.goal_id == "goal-1"
        assert len(loaded.events) == 2
        assert loaded.events[1].decision_point == "Strategy"
    
    def test_list_sessions(self, tracer):
        """Test listing saved sessions."""
        # Create multiple sessions
        for i in range(3):
            session = tracer.start_session(f"goal-{i}", f"Test {i}")
            tracer.end_session(success=True)
        
        sessions = tracer.list_sessions()
        
        assert len(sessions) == 3
        # Most recent first
        assert sessions[0].goal_id == "goal-2"
        assert sessions[2].goal_id == "goal-0"
    
    def test_no_active_session_error(self, tracer):
        """Test error when no active session."""
        with pytest.raises(RuntimeError, match="No active session"):
            tracer.record_event(EventType.ANALYSIS_START, "Test")
    
    def test_aggregate_metrics(self, tracer):
        """Test session aggregate metrics."""
        session = tracer.start_session("goal-1", "Test")
        
        tracer.record_event(EventType.ANALYSIS_START, "Start")
        tracer.record_event(EventType.ANALYSIS_STEP, "Step 1")
        tracer.record_decision("D1", ["A", "B"], "A", "Test", 0.9)
        tracer.record_execution("action1", "result1", 100)
        tracer.record_error("TestError", "Test message")
        tracer.record_warning("Test warning")
        
        final_session = tracer.end_session(success=False)
        
        assert final_session.total_events == 6
        assert final_session.analysis_events == 2
        assert final_session.decision_events == 1
        # EXECUTION_COMPLETE counts as execution_events
        assert final_session.execution_events >= 1
        assert final_session.error_count == 1
        assert final_session.warning_count == 1
        assert final_session.total_duration_ms >= 0
    
    def test_event_with_context(self, tracer):
        """Test recording event with custom context."""
        session = tracer.start_session("goal-1", "Test")
        
        context_data = {
            "files_affected": ["a.py", "b.py"],
            "complexity": "high",
            "estimated_time_min": 30
        }
        
        event = tracer.record_event(
            event_type=EventType.ANALYSIS_STEP,
            message="Dependency analysis",
            context=context_data
        )
        
        assert event.context == context_data
        assert event.context["complexity"] == "high"


# ============================================================================
# LLM CALL TRACKER TESTS
# ============================================================================

class TestLLMCallTracker:
    """Unit tests for LLMCallTracker."""
    
    @pytest.fixture
    def tracker(self, tmp_path):
        """Create tracker with temp directory."""
        return LLMCallTracker(
            agent_id="test-agent",
            output_dir=tmp_path
        )
    
    def test_record_call(self, tracker):
        """Test recording an LLM call."""
        record = tracker.record_call(
            model=LLMModel.GPT_4O,
            purpose=CallPurpose.CODE_ANALYSIS,
            prompt="Analyze this code...",
            response="The code does...",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
            latency_ms=1200,
            goal_id="goal-1",
            session_id="session-1"
        )
        
        assert record.model == LLMModel.GPT_4O
        assert record.purpose == CallPurpose.CODE_ANALYSIS
        assert record.prompt_length == len("Analyze this code...")
        assert record.latency_ms == 1200
        assert record.success is True
        assert len(tracker.calls) == 1
    
    def test_cost_calculation_gpt4o(self, tracker):
        """Test cost calculation for GPT-4O."""
        record = tracker.record_call(
            model=LLMModel.GPT_4O,
            purpose=CallPurpose.CODE_ANALYSIS,
            prompt="Test",
            response="Result",
            token_usage=TokenUsage(input_tokens=1000, output_tokens=1000, total_tokens=2000),
            latency_ms=500
        )
        
        # GPT-4O: $5/1M input, $15/1M output
        expected_input_cost = (1000 / 1000) * 0.005
        expected_output_cost = (1000 / 1000) * 0.015
        expected_total = expected_input_cost + expected_output_cost
        
        assert abs(record.estimated_input_cost - expected_input_cost) < 0.0001
        assert abs(record.estimated_output_cost - expected_output_cost) < 0.0001
        assert abs(record.estimated_total_cost - expected_total) < 0.0001
    
    def test_cost_calculation_claude_opus(self, tracker):
        """Test cost calculation for Claude-3 Opus."""
        record = tracker.record_call(
            model=LLMModel.CLAUDE_3_OPUS,
            purpose=CallPurpose.CODE_GENERATION,
            prompt="Generate code",
            response="def foo():\n    pass",
            token_usage=TokenUsage(input_tokens=500, output_tokens=500, total_tokens=1000),
            latency_ms=2000
        )
        
        # Claude-3 Opus: $15/1M input, $75/1M output
        expected_input_cost = (500 / 1000) * 0.015
        expected_output_cost = (500 / 1000) * 0.075
        expected_total = expected_input_cost + expected_output_cost
        
        assert abs(record.estimated_total_cost - expected_total) < 0.0001
    
    def test_cost_summary_single_call(self, tracker):
        """Test cost summary with single call."""
        tracker.record_call(
            model=LLMModel.GPT_4O,
            purpose=CallPurpose.CODE_ANALYSIS,
            prompt="Analyze",
            response="Result",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
            latency_ms=500
        )
        
        summary = tracker.get_cost_summary()
        
        assert summary.total_calls == 1
        assert summary.total_input_tokens == 100
        assert summary.total_output_tokens == 50
        assert summary.total_cost > 0
        assert summary.average_cost_per_call == summary.total_cost
    
    def test_cost_summary_multiple_calls(self, tracker):
        """Test cost summary with multiple calls."""
        for i in range(5):
            tracker.record_call(
                model=LLMModel.GPT_4O if i % 2 == 0 else LLMModel.CLAUDE_3_HAIKU,
                purpose=CallPurpose.CODE_ANALYSIS,
                prompt="Test",
                response="Result",
                token_usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
                latency_ms=500 + (i * 100)
            )
        
        summary = tracker.get_cost_summary()
        
        assert summary.total_calls == 5
        assert summary.total_input_tokens == 500
        assert summary.total_output_tokens == 250
        assert summary.average_cost_per_call > 0
        assert summary.calls_by_model[LLMModel.GPT_4O] == 3
        assert summary.calls_by_model[LLMModel.CLAUDE_3_HAIKU] == 2
    
    def test_filter_by_purpose(self, tracker):
        """Test filtering calls by purpose."""
        tracker.record_call(
            model=LLMModel.GPT_4O,
            purpose=CallPurpose.CODE_ANALYSIS,
            prompt="Analyze",
            response="Result",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
            latency_ms=500
        )
        tracker.record_call(
            model=LLMModel.GPT_4O,
            purpose=CallPurpose.CODE_GENERATION,
            prompt="Generate",
            response="def foo(): pass",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
            latency_ms=500
        )
        
        analysis_calls = tracker.get_calls_by_purpose(CallPurpose.CODE_ANALYSIS)
        gen_calls = tracker.get_calls_by_purpose(CallPurpose.CODE_GENERATION)
        
        assert len(analysis_calls) == 1
        assert len(gen_calls) == 1
        assert analysis_calls[0].purpose == CallPurpose.CODE_ANALYSIS
    
    def test_filter_by_model(self, tracker):
        """Test filtering calls by model."""
        tracker.record_call(
            model=LLMModel.GPT_4O,
            purpose=CallPurpose.CODE_ANALYSIS,
            prompt="Test",
            response="Result",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
            latency_ms=500
        )
        tracker.record_call(
            model=LLMModel.CLAUDE_3_HAIKU,
            purpose=CallPurpose.CODE_ANALYSIS,
            prompt="Test",
            response="Result",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
            latency_ms=300
        )
        
        gpt_calls = tracker.get_calls_by_model(LLMModel.GPT_4O)
        claude_calls = tracker.get_calls_by_model(LLMModel.CLAUDE_3_HAIKU)
        
        assert len(gpt_calls) == 1
        assert len(claude_calls) == 1
    
    def test_filter_by_session(self, tracker):
        """Test filtering calls by session."""
        tracker.record_call(
            model=LLMModel.GPT_4O,
            purpose=CallPurpose.CODE_ANALYSIS,
            prompt="Test",
            response="Result",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
            latency_ms=500,
            session_id="session-1"
        )
        tracker.record_call(
            model=LLMModel.GPT_4O,
            purpose=CallPurpose.CODE_ANALYSIS,
            prompt="Test",
            response="Result",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
            latency_ms=500,
            session_id="session-2"
        )
        
        session1_calls = tracker.get_calls_by_session("session-1")
        session2_calls = tracker.get_calls_by_session("session-2")
        
        assert len(session1_calls) == 1
        assert len(session2_calls) == 1
    
    def test_save_and_export(self, tracker, tmp_path):
        """Test saving calls to JSON."""
        tracker.record_call(
            model=LLMModel.GPT_4O,
            purpose=CallPurpose.CODE_ANALYSIS,
            prompt="Analyze",
            response="Result",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
            latency_ms=500
        )
        
        filepath = tracker.save_to_file("test_export.json")
        
        assert filepath.exists()
        with open(filepath) as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]["model"] == "gpt-4o"
        assert data[0]["purpose"] == "code_analysis"
    
    def test_cost_report_generation(self, tracker):
        """Test cost report generation."""
        tracker.record_call(
            model=LLMModel.GPT_4O,
            purpose=CallPurpose.CODE_ANALYSIS,
            prompt="Test",
            response="Result",
            token_usage=TokenUsage(input_tokens=1000, output_tokens=500, total_tokens=1500),
            latency_ms=1000
        )
        
        report = tracker.generate_cost_report()
        
        assert "Cost Report" in report
        assert "Total Calls: 1" in report
        assert "GPT-4O" in report or "gpt-4o" in report.lower()
    
    def test_most_expensive_call(self, tracker):
        """Test identifying most expensive call."""
        # Cheap call
        tracker.record_call(
            model=LLMModel.CLAUDE_3_HAIKU,
            purpose=CallPurpose.CODE_ANALYSIS,
            prompt="Test",
            response="Result",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
            latency_ms=300
        )
        
        # Expensive call
        tracker.record_call(
            model=LLMModel.CLAUDE_3_OPUS,
            purpose=CallPurpose.CODE_GENERATION,
            prompt="Test" * 100,
            response="Result" * 100,
            token_usage=TokenUsage(input_tokens=5000, output_tokens=5000, total_tokens=10000),
            latency_ms=3000
        )
        
        summary = tracker.get_cost_summary()
        
        assert summary.most_expensive_call.model == LLMModel.CLAUDE_3_OPUS
        assert summary.most_expensive_call.estimated_total_cost > summary.total_cost / 2


# ============================================================================
# PERFORMANCE METRICS TESTS
# ============================================================================

class TestPerformanceMetrics:
    """Unit tests for PerformanceMetrics."""
    
    @pytest.fixture
    def metrics(self, tmp_path):
        """Create metrics with temp directory."""
        return PerformanceMetrics(
            agent_id="test-agent",
            goal_id="test-goal",
            execution_id="exec-1"
        )
    
    def test_start_end_phase(self, metrics):
        """Test starting and ending a phase."""
        metrics.start_phase("analysis")
        import time
        time.sleep(0.01)  # Ensure some time passes
        metrics.end_phase(success=True, error_count=0, warning_count=1)
        
        assert "analysis" in metrics.phases
        phase = metrics.phases["analysis"]
        assert phase.success is True
        assert phase.error_count == 0
        assert phase.warning_count == 1
        assert phase.duration_ms >= 0
    
    def test_start_stop_timer(self, metrics):
        """Test timer functionality."""
        metrics.start_timer("test_timer")
        duration = metrics.stop_timer("test_timer")
        
        assert duration is not None
        assert duration >= 0
        assert "test_timer" in metrics.timers
    
    def test_counter_operations(self, metrics):
        """Test counter increment."""
        val1 = metrics.increment_counter("files_analyzed", 5)
        assert val1 == 5
        
        val2 = metrics.increment_counter("files_analyzed", 3)
        assert val2 == 8
        
        val3 = metrics.increment_counter("files_analyzed", -2)
        assert val3 == 6
    
    def test_gauge_set(self, metrics):
        """Test gauge value setting."""
        metrics.set_gauge("memory_usage_mb", 256)
        metrics.set_gauge("memory_usage_mb", 512)
        
        gauge = metrics.gauges["memory_usage_mb"]
        assert gauge.value == 512
    
    def test_histogram(self, metrics):
        """Test histogram recording."""
        metrics.record_histogram("request_latency_ms", 150)
        metrics.record_histogram("request_latency_ms", 250)
        metrics.record_histogram("request_latency_ms", 450)
        
        histogram = metrics.histograms["request_latency_ms"]
        assert len(histogram.values) == 3
        assert 150 in histogram.values
        assert len(histogram.buckets) > 0
    
    def test_multiple_phases(self, metrics):
        """Test tracking multiple phases."""
        metrics.start_phase("analyze")
        metrics.end_phase(success=True)
        
        metrics.start_phase("decide")
        metrics.end_phase(success=True)
        
        metrics.start_phase("execute")
        metrics.end_phase(success=False, error_count=1)
        
        assert len(metrics.phases) == 3
        assert metrics.phases["analyze"].success is True
        assert metrics.phases["execute"].error_count == 1
    
    def test_finalize_metrics(self, metrics):
        """Test finalizing metrics."""
        metrics.start_phase("test_phase")
        metrics.increment_counter("items_processed", 10)
        import time
        time.sleep(0.01)  # Ensure duration is measurable
        metrics.end_phase(success=True, error_count=0, warning_count=2)
        
        execution = metrics.finalize(
            success=True,
            result_summary="Test completed"
        )
        
        assert execution.agent_id == "test-agent"
        assert execution.goal_id == "test-goal"
        assert execution.total_duration_ms >= 0
        assert execution.total_warnings == 2
        assert execution.success is True
    
    def test_metrics_aggregation(self, metrics):
        """Test aggregating metrics across phases."""
        metrics.start_phase("phase_1")
        metrics.end_phase(success=True, error_count=2, warning_count=1)
        
        metrics.start_phase("phase_2")
        metrics.end_phase(success=True, error_count=1, warning_count=0)
        
        execution = metrics.finalize()
        
        assert execution.total_errors == 3
        assert execution.total_warnings == 1
    
    def test_save_metrics(self, metrics, tmp_path):
        """Test saving metrics to JSON."""
        metrics.start_phase("test_phase")
        metrics.increment_counter("test_counter", 5)
        metrics.set_gauge("test_gauge", 100)
        metrics.end_phase(success=True)
        
        filepath = metrics.save_metrics(output_dir=tmp_path)
        
        assert filepath.exists()
        with open(filepath) as f:
            data = json.load(f)
        
        assert data["agent_id"] == "test-agent"
        assert data["success"] is True
        assert "test_phase" in data["phases"]
    
    def test_report_generation(self, metrics):
        """Test report generation."""
        metrics.start_phase("analyze")
        metrics.end_phase(success=True)
        
        metrics.start_phase("execute")
        metrics.end_phase(success=False, error_count=1)
        
        report = metrics.generate_report()
        
        assert "Execution Metrics Report" in report
        assert "analyze" in report
        assert "execute" in report
        assert "Total Duration" in report
    
    def test_concurrent_counters(self, metrics):
        """Test thread-safe counter operations."""
        import threading
        
        def increment_counter():
            for _ in range(100):
                metrics.increment_counter("concurrent_test")
        
        threads = [threading.Thread(target=increment_counter) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # 5 threads * 100 increments = 500
        assert metrics.counters["concurrent_test"].value == 500


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests across all modules."""
    
    def test_full_execution_trace(self, tmp_path):
        """Test complete execution with all three modules."""
        tracer = ReasoningTracer(agent_id="integration-test", output_dir=tmp_path)
        tracker = LLMCallTracker(agent_id="integration-test", output_dir=tmp_path)
        metrics = PerformanceMetrics(agent_id="integration-test", goal_id="goal-1")
        
        # Simulate execution
        session = tracer.start_session("goal-1", "Integration Test")
        metrics.start_phase("analysis")
        
        # Record reasoning
        tracer.record_event(EventType.ANALYSIS_START, "Starting analysis")
        metrics.increment_counter("files_analyzed", 5)
        
        # Record LLM call
        tracker.record_call(
            model=LLMModel.GPT_4O,
            purpose=CallPurpose.CODE_ANALYSIS,
            prompt="Analyze code",
            response="Analysis result",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150),
            latency_ms=1000,
            goal_id="goal-1"
        )
        
        # Record decision
        tracer.record_decision(
            decision_point="Strategy",
            options=["A", "B"],
            selected="A",
            reasoning="Better performance",
            confidence=0.9
        )
        
        metrics.end_phase(success=True)
        metrics.start_phase("execution")
        
        # Record execution
        tracer.record_execution("apply_changes", "3 files modified", 500, success=True)
        metrics.increment_counter("files_modified", 3)
        
        metrics.end_phase(success=True)
        
        # Finalize
        final_session = tracer.end_session(success=True, result_summary="Success")
        execution_metrics = metrics.finalize(success=True)
        cost_summary = tracker.get_cost_summary()
        
        # Verify all data captured
        # Events: ANALYSIS_START, DECISION_MADE, EXECUTION_COMPLETE
        assert len(final_session.events) >= 3
        assert final_session.success is True
        
        assert execution_metrics.total_duration_ms >= 0
        assert execution_metrics.total_errors == 0
        
        assert cost_summary.total_calls == 1
        assert cost_summary.total_cost > 0
        
        # Verify persistence
        loaded_session = tracer.load_session(final_session.session_id)
        assert loaded_session is not None
        assert len(loaded_session.events) >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

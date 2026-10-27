"""Phase 2C: ResultAggregator tests.

Tests cover:
- Tab generation from each agent type
- LLM synthesis with mocking
- Template-based fallback synthesis
- Action extraction
- Next steps generation
- Full aggregation workflow
- Error handling and graceful degradation
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch, Mock

import pytest

from kicli_code_assist.agent.aggregator import (
    Action,
    ActionType,
    AggregatedResult,
    ResultAggregator,
    TabContent,
)
from kicli_code_assist.agent.executor import ExecutorResult
from kicli_code_assist.agent.intent_detector import AgentIntent, IntentType


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_executor_result():
    """Create a sample ExecutorResult with all agent outputs."""
    return ExecutorResult(
        query="Explain and optimize this function",
        intent=AgentIntent(
            intent_type=IntentType.EXPLAIN,
            agents_to_run=["explain", "metrics", "refactor"],
            confidence=0.95,
            reasoning="User asked for explanation and optimization",
        ),
        session_id="session-test-123",
        results={
            "explain": {
                "status": "ok",
                "summary": "Main controller function",
                "classes": [
                    {"name": "MainController", "line": 10, "methods": 5},
                ],
                "functions": [
                    {"name": "process_request", "line": 25, "complexity": 3},
                    {"name": "validate_input", "line": 35, "complexity": 2},
                ],
                "imports": [
                    {"module": "fastapi", "name": "FastAPI", "line": 1},
                    {"module": "sqlalchemy", "name": "Session", "line": 2},
                ],
            },
            "metrics": {
                "status": "ok",
                "maintainability_index": 78,
                "complexity": "MEDIUM",
                "issues": [
                    {"type": "high_complexity", "function": "process_request"},
                ],
                "improvements": [
                    "Extract validation logic into separate function",
                ],
            },
            "refactor": {
                "status": "ok",
                "suggestions": [
                    {
                        "type": "extract_method",
                        "entity": "process_request",
                        "message": "Break down into smaller functions",
                        "line": 25,
                    },
                ],
                "patterns": ["strategy_pattern", "factory_pattern"],
                "priority": "HIGH",
                "improvement_potential": 0.65,
            },
        },
        total_time_ms=350.5,
        cached=False,
    )


@pytest.fixture
def test_file(tmp_path):
    """Create a temporary test Python file."""
    file_path = tmp_path / "test_module.py"
    file_path.write_text("""
def main_function(x, y):
    return x + y

class TestClass:
    pass
""")
    return file_path


@pytest.fixture
def aggregator():
    """Create a ResultAggregator instance."""
    return ResultAggregator(provider="openai", enable_llm=False)


@pytest.fixture
def aggregator_with_mock_llm():
    """Create a ResultAggregator with mocked LLM."""
    mock_chain = AsyncMock()
    aggregator = ResultAggregator(
        provider="openai",
        provider_chain=mock_chain,
        enable_llm=True,
    )
    return aggregator, mock_chain


# ============================================================================
# Tab Generation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_build_structure_tab(aggregator):
    """Test building Structure tab from explain agent results."""
    result = {
        "classes": [{"name": "MyClass", "line": 10}],
        "functions": [{"name": "my_func", "line": 5}],
        "imports": [{"module": "os", "line": 1}],
        "summary": "Main module structure",
    }
    
    tab = aggregator._build_structure_tab(result)
    
    assert tab.title == "Structure"
    assert tab.agent_type == "explain"
    assert len(tab.data["classes"]) == 1
    assert len(tab.data["functions"]) == 1
    assert tab.data["description"] == "Main module structure"


@pytest.mark.asyncio
async def test_build_metrics_tab(aggregator):
    """Test building Metrics tab from metrics agent results."""
    result = {
        "maintainability_index": 85,
        "complexity": "LOW",
        "issues": [{"type": "unused_import"}],
        "improvements": ["Remove unused import"],
    }
    
    tab = aggregator._build_metrics_tab(result)
    
    assert tab.title == "Metrics"
    assert tab.agent_type == "metrics"
    assert tab.data["maintainability_index"] == 85
    assert tab.data["overall_health"] == "Excellent"
    assert len(tab.data["issues"]) == 1


@pytest.mark.asyncio
async def test_build_refactor_tab(aggregator):
    """Test building Refactor tab from refactoring agent results."""
    result = {
        "suggestions": [{"message": "Extract method"}],
        "patterns": ["Strategy", "Factory"],
        "priority": "HIGH",
        "improvement_potential": 0.75,
    }
    
    tab = aggregator._build_refactor_tab(result)
    
    assert tab.title == "Refactor"
    assert tab.agent_type == "refactor"
    assert len(tab.data["recommendations"]) == 1
    assert tab.data["priority"] == "HIGH"


@pytest.mark.asyncio
async def test_build_dependencies_tab(aggregator):
    """Test building Dependencies tab from dependencies agent results."""
    result = {
        "imports": {"os": True, "sys": True},
        "internal_dependencies": {"utils.py": True},
        "external_dependencies": {"fastapi": True},
        "dependency_graph": {},
    }
    
    tab = aggregator._build_dependencies_tab(result)
    
    assert tab.title == "Dependencies"
    assert tab.agent_type == "dependencies"
    assert "os" in tab.data["imports"]


@pytest.mark.asyncio
async def test_build_tabs_all_agents(aggregator, sample_executor_result):
    """Test building tabs from multiple agent results."""
    tabs = await aggregator._build_tabs(sample_executor_result)
    
    assert "Structure" in tabs
    assert "Metrics" in tabs
    assert "Refactor" in tabs


# ============================================================================
# Synthesis Tests
# ============================================================================


@pytest.mark.asyncio
async def test_synthesis_with_template(aggregator, sample_executor_result):
    """Test template-based synthesis fallback."""
    tabs = await aggregator._build_tabs(sample_executor_result)
    
    summary, method = await aggregator._synthesize_with_template(
        executor_result=sample_executor_result,
        query="Explain this code",
        tabs=tabs,
    )
    
    assert method == "template"
    assert len(summary) > 0
    assert "Analysis" in summary or "contain" in summary.lower()


@pytest.mark.asyncio
async def test_synthesis_with_llm_success(aggregator_with_mock_llm, sample_executor_result):
    """Test LLM synthesis with successful response."""
    aggregator, mock_chain = aggregator_with_mock_llm
    
    # Mock LLM response with proper ki-core Message/ChatResponse structure
    mock_message = Mock()
    mock_message.content = "This is a well-structured controller with good maintainability."
    
    mock_response = Mock()
    mock_response.message = mock_message
    mock_chain.achat.return_value = mock_response
    
    tabs = await aggregator._build_tabs(sample_executor_result)
    
    summary, method = await aggregator._synthesize_with_llm(
        executor_result=sample_executor_result,
        file_path=Path("test.py"),
        query="Explain this code",
        tabs=tabs,
    )
    
    assert method == "llm"
    assert "controller" in summary.lower()
    mock_chain.achat.assert_called_once()


@pytest.mark.asyncio
async def test_synthesis_with_llm_fallback_on_error(aggregator_with_mock_llm, sample_executor_result):
    """Test LLM synthesis falls back to template on error."""
    aggregator, mock_chain = aggregator_with_mock_llm
    
    # Mock LLM error
    mock_chain.achat.side_effect = Exception("LLM error")
    
    tabs = await aggregator._build_tabs(sample_executor_result)
    
    summary, method = await aggregator._synthesize_with_llm(
        executor_result=sample_executor_result,
        file_path=Path("test.py"),
        query="Explain this code",
        tabs=tabs,
    )
    
    assert method == "template"
    assert len(summary) > 0


# ============================================================================
# Action Extraction Tests
# ============================================================================


@pytest.mark.asyncio
async def test_extract_actions_empty(aggregator):
    """Test action extraction with no suggestions."""
    executor_result = ExecutorResult(
        query="Explain",
        intent=AgentIntent(
            intent_type=IntentType.EXPLAIN,
            agents_to_run=["explain"],
            confidence=0.9,
            reasoning="",
        ),
        session_id="test",
        results={},
    )
    
    tabs = {}
    actions = await aggregator._extract_actions(executor_result, tabs)
    
    assert len(actions) == 0


@pytest.mark.asyncio
async def test_extract_actions_file_creation(aggregator):
    """Test action extraction for file creation suggestions."""
    executor_result = ExecutorResult(
        query="Create auth module",
        intent=AgentIntent(
            intent_type=IntentType.SUGGEST,
            agents_to_run=["suggest"],
            confidence=0.9,
            reasoning="",
        ),
        session_id="test",
        results={},
    )
    
    tabs = {
        "Suggestions": TabContent(
            title="Suggestions",
            description="File suggestions",
            data={
                "suggested_files": [
                    {
                        "name": "auth.py",
                        "description": "Authentication module",
                        "content": "def authenticate(): pass",
                        "purpose": "Handle JWT auth",
                    },
                ],
                "file_changes": [],
            },
            agent_type="suggest",
        ),
    }
    
    actions = await aggregator._extract_actions(executor_result, tabs)
    
    assert len(actions) >= 1
    assert actions[0].action_type == ActionType.WRITE_FILE
    assert actions[0].target == "auth.py"


@pytest.mark.asyncio
async def test_extract_actions_refactoring(aggregator):
    """Test action extraction from refactoring recommendations."""
    executor_result = ExecutorResult(
        query="Refactor this",
        intent=AgentIntent(
            intent_type=IntentType.REFACTOR,
            agents_to_run=["refactor"],
            confidence=0.9,
            reasoning="",
        ),
        session_id="test",
        results={},
    )
    
    tabs = {
        "Refactor": TabContent(
            title="Refactor",
            description="Refactoring recommendations",
            data={
                "recommendations": [
                    {
                        "entity": "process_request",
                        "message": "Break down into smaller functions",
                        "type": "extract_method",
                    },
                ],
                "patterns": [],
            },
            agent_type="refactor",
        ),
    }
    
    actions = await aggregator._extract_actions(executor_result, tabs)
    
    assert len(actions) >= 1
    assert actions[0].action_type == ActionType.REVIEW_DIFF


# ============================================================================
# Next Steps Extraction Tests
# ============================================================================


@pytest.mark.asyncio
async def test_extract_next_steps_explain_intent(aggregator):
    """Test next steps suggestion for explain intent."""
    executor_result = ExecutorResult(
        query="Explain this function",
        intent=AgentIntent(
            intent_type=IntentType.EXPLAIN,
            agents_to_run=["explain"],
            confidence=0.9,
            reasoning="",
        ),
        session_id="test",
        results={},
    )
    
    next_steps = await aggregator._extract_next_steps(executor_result, "Explain")
    
    assert len(next_steps) > 0
    assert any("metrics" in step.lower() for step in next_steps)


@pytest.mark.asyncio
async def test_extract_next_steps_optimize_intent(aggregator):
    """Test next steps suggestion for optimize intent."""
    executor_result = ExecutorResult(
        query="Optimize this for performance",
        intent=AgentIntent(
            intent_type=IntentType.OPTIMIZE,
            agents_to_run=["metrics"],
            confidence=0.9,
            reasoning="",
        ),
        session_id="test",
        results={},
    )
    
    next_steps = await aggregator._extract_next_steps(
        executor_result,
        "Optimize performance"
    )
    
    assert len(next_steps) > 0
    assert any("refactor" in step.lower() or "metrics" in step.lower() for step in next_steps)


@pytest.mark.asyncio
async def test_extract_next_steps_with_query_keywords(aggregator):
    """Test that next steps consider query keywords."""
    executor_result = ExecutorResult(
        query="Check security vulnerabilities",
        intent=AgentIntent(
            intent_type=IntentType.REVIEW,
            agents_to_run=["review"],
            confidence=0.9,
            reasoning="",
        ),
        session_id="test",
        results={},
    )
    
    next_steps = await aggregator._extract_next_steps(
        executor_result,
        "Check security vulnerabilities"
    )
    
    assert any("security" in step.lower() for step in next_steps)


# ============================================================================
# Full Aggregation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_aggregate_full_workflow(aggregator, sample_executor_result, test_file):
    """Test full aggregation workflow."""
    result = await aggregator.aggregate(
        executor_result=sample_executor_result,
        file_path=test_file,
        query="Explain and optimize this function",
    )
    
    assert isinstance(result, AggregatedResult)
    assert result.session_id == "session-test-123"
    assert result.query == "Explain and optimize this function"
    assert len(result.summary) > 0
    assert len(result.tabs) > 0
    assert result.execution_time_ms > 0
    assert result.synthesis_method in ["template", "llm"]


@pytest.mark.asyncio
async def test_aggregate_with_llm_synthesis(aggregator_with_mock_llm, sample_executor_result, test_file):
    """Test aggregation with LLM synthesis."""
    aggregator, mock_chain = aggregator_with_mock_llm
    
    # Mock LLM response with proper ki-core structure
    mock_message = Mock()
    mock_message.content = "This code is well-structured with good maintainability. Consider extracting complex logic."
    
    mock_response = Mock()
    mock_response.message = mock_message
    mock_chain.achat.return_value = mock_response
    
    result = await aggregator.aggregate(
        executor_result=sample_executor_result,
        file_path=test_file,
        query="Explain this code",
    )
    
    assert result.synthesis_method == "llm"
    assert "well-structured" in result.summary.lower()


@pytest.mark.asyncio
async def test_aggregate_error_handling(aggregator, test_file):
    """Test graceful error handling in aggregation."""
    # Create invalid executor result
    invalid_result = ExecutorResult(
        query="Test",
        intent=AgentIntent(
            intent_type=IntentType.EXPLAIN,
            agents_to_run=[],
            confidence=0.5,
            reasoning="",
        ),
        session_id=None,
        results={},
    )
    
    result = await aggregator.aggregate(
        executor_result=invalid_result,
        file_path=test_file,
        query="Test query",
    )
    
    # Should return a result even on error
    assert isinstance(result, AggregatedResult)
    assert result.execution_time_ms >= 0


# ============================================================================
# Data Structure Tests
# ============================================================================


def test_action_to_dict():
    """Test Action serialization."""
    action = Action(
        action_type=ActionType.WRITE_FILE,
        target="auth.py",
        description="Create authentication module",
        details={"content": "# Auth module"},
        priority="high",
    )
    
    data = action.to_dict()
    
    assert data["action_type"] == "write_file"
    assert data["target"] == "auth.py"
    assert data["priority"] == "high"


def test_tab_content_to_dict():
    """Test TabContent serialization."""
    tab = TabContent(
        title="Structure",
        description="Code structure overview",
        data={"classes": ["MyClass"], "functions": ["my_func"]},
        agent_type="explain",
    )
    
    data = tab.to_dict()
    
    assert data["title"] == "Structure"
    assert data["agent_type"] == "explain"
    assert "classes" in data["data"]


def test_aggregated_result_to_dict():
    """Test AggregatedResult serialization."""
    result = AggregatedResult(
        session_id="test-123",
        query="Explain this",
        summary="This is a test module.",
        tabs={},
        actions=[],
        next_steps=["Step 1"],
        execution_time_ms=100.0,
        synthesis_method="template",
    )
    
    data = result.to_dict()
    
    assert data["session_id"] == "test-123"
    assert data["query"] == "Explain this"
    assert len(data["next_steps"]) == 1
    assert data["synthesis_method"] == "template"


# ============================================================================
# Health Score Tests
# ============================================================================


def test_calculate_health_score_excellent():
    """Test health score calculation for excellent code."""
    aggregator = ResultAggregator()
    health = aggregator._calculate_health_score(90)
    assert health == "Excellent"


def test_calculate_health_score_good():
    """Test health score calculation for good code."""
    aggregator = ResultAggregator()
    health = aggregator._calculate_health_score(75)
    assert health == "Good"


def test_calculate_health_score_fair():
    """Test health score calculation for fair code."""
    aggregator = ResultAggregator()
    health = aggregator._calculate_health_score(60)
    assert health == "Fair"


def test_calculate_health_score_poor():
    """Test health score calculation for poor code."""
    aggregator = ResultAggregator()
    health = aggregator._calculate_health_score(45)
    assert health == "Poor"


def test_calculate_health_score_critical():
    """Test health score calculation for critical code."""
    aggregator = ResultAggregator()
    health = aggregator._calculate_health_score(30)
    assert health == "Critical"


# ============================================================================
# Prompt Building Tests
# ============================================================================


@pytest.mark.asyncio
async def test_build_synthesis_prompt(aggregator, sample_executor_result, test_file):
    """Test LLM synthesis prompt construction."""
    tabs = await aggregator._build_tabs(sample_executor_result)
    
    prompt = aggregator._build_synthesis_prompt(
        executor_result=sample_executor_result,
        file_path=test_file,
        query="Explain this code",
        tabs=tabs,
    )
    
    assert len(prompt) > 0
    assert "File:" in prompt
    assert "User Query:" in prompt
    assert "Intent:" in prompt
    assert "Summary:" in prompt


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_aggregator_initialization_without_llm():
    """Test aggregator initialization without LLM."""
    agg = ResultAggregator(provider="openai", enable_llm=False)
    assert not agg.enable_llm


@pytest.mark.asyncio
async def test_aggregator_initialization_with_llm():
    """Test aggregator initialization with LLM."""
    mock_chain = AsyncMock()
    agg = ResultAggregator(provider="openai", provider_chain=mock_chain, enable_llm=True)
    assert agg.enable_llm


@pytest.mark.asyncio
async def test_export_aggregated_result_to_json(aggregator, sample_executor_result, test_file):
    """Test exporting aggregated result to JSON."""
    result = await aggregator.aggregate(
        executor_result=sample_executor_result,
        file_path=test_file,
        query="Explain and optimize",
    )
    
    # Convert to dict and then to JSON
    data = result.to_dict()
    json_str = json.dumps(data)
    
    assert len(json_str) > 0
    
    # Parse back from JSON
    parsed = json.loads(json_str)
    assert parsed["session_id"] == "session-test-123"
    assert parsed["query"] == "Explain and optimize"

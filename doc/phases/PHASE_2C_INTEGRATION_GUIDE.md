# Phase 2C: ResultAggregator Integration Guide

**Purpose**: Connect Phase 2C ResultAggregator with Phase 2B ExecutorResult and Phase 2D UI  
**Audience**: Developers building the full agent system  
**Last Updated**: 2026-10-27  

---

## Integration Overview

```
Phase 2A (Intent Detection)
        ↓
Phase 2B (Parallel Execution) → ExecutorResult
        ↓
Phase 2C (Result Synthesis) → AggregatedResult  ← YOU ARE HERE
        ↓
Phase 2D (UI Rendering)
        ↓
User Interface Display
```

---

## How to Use ResultAggregator

### 1. Import the Classes

```python
from kicli_code_assist.agent import (
    AgentExecutor,
    ExecutorResult,
    ResultAggregator,
    AggregatedResult,
    Action,
    ActionType,
    TabContent,
)
from pathlib import Path
```

### 2. Create Executor and Aggregator

```python
# Phase 2B: Execute agents in parallel
executor = AgentExecutor(project_root=Path("/home/user/project"))

# Phase 2C: Create aggregator for synthesis
aggregator = ResultAggregator(provider="openai", enable_llm=True)
```

### 3. Execute and Aggregate

```python
# Run agents
executor_result = await executor.execute(
    query="Explain and optimize this function",
    file_path=Path("utils.py"),
    scope="folder",
    session_id="session-123"
)

# Synthesize results
aggregated_result = await aggregator.aggregate(
    executor_result=executor_result,
    file_path=Path("utils.py"),
    query="Explain and optimize this function"
)
```

### 4. Access Results

```python
# Summary
print(f"Summary: {aggregated_result.summary}")

# Tabs
for tab_name, tab in aggregated_result.tabs.items():
    print(f"\n{tab.title}:")
    print(f"  Description: {tab.description}")
    print(f"  Data: {tab.data}")

# Actions
for action in aggregated_result.actions:
    print(f"\nAction: {action.target}")
    print(f"  Type: {action.action_type.value}")
    print(f"  Priority: {action.priority}")

# Next steps
print(f"\nNext Steps:")
for step in aggregated_result.next_steps:
    print(f"  - {step}")
```

---

## Data Flow Through Phases

### ExecutorResult (Phase 2B Output)

```python
executor_result = ExecutorResult(
    query="Explain and optimize this function",
    intent=AgentIntent(
        intent_type=IntentType.EXPLAIN,
        agents_to_run=["explain", "metrics", "refactor"],
        confidence=0.95,
        reasoning="User asked for explanation and optimization"
    ),
    session_id="session-123",
    results={
        "explain": {
            "status": "ok",
            "classes": [...],
            "functions": [...],
            "imports": [...]
        },
        "metrics": {
            "status": "ok",
            "maintainability_index": 78,
            "complexity": "MEDIUM",
            "issues": [...]
        },
        "refactor": {
            "status": "ok",
            "suggestions": [...],
            "patterns": [...],
            "priority": "HIGH"
        }
    },
    total_time_ms=350.5,
    cached=False
)
```

### AggregatedResult (Phase 2C Output)

```python
aggregated_result = AggregatedResult(
    session_id="session-123",
    query="Explain and optimize this function",
    summary="This utility module is well-structured with good maintainability (78/100). Extract complex logic to improve code organization.",
    
    tabs={
        "Structure": TabContent(
            title="Structure",
            description="Code structure overview",
            data={
                "classes": [...],
                "functions": [...],
                "imports": [...]
            },
            agent_type="explain"
        ),
        "Metrics": TabContent(
            title="Metrics",
            description="Code quality and complexity analysis",
            data={
                "maintainability_index": 78,
                "complexity": "MEDIUM",
                "overall_health": "Good",
                "issues": [...]
            },
            agent_type="metrics"
        ),
        "Refactor": TabContent(
            title="Refactor",
            description="Refactoring recommendations and patterns",
            data={
                "recommendations": [...],
                "patterns": [...],
                "priority": "HIGH",
                "improvement_potential": 0.65
            },
            agent_type="refactor"
        )
    },
    
    actions=[
        Action(
            action_type=ActionType.REVIEW_DIFF,
            target="process_request",
            description="Extract complex validation logic",
            details={"line": 25, "complexity": 5},
            priority="high"
        )
    ],
    
    next_steps=[
        "Run metrics analysis to check code quality",
        "Review dependencies to understand interactions",
        "Consider extracting validation into separate module"
    ],
    
    execution_time_ms=15.3,
    synthesis_method="llm"
)
```

---

## Integration Points

### 1. With Phase 2B (ExecutorResult)

**Input Format**:
- ExecutorResult with results from multiple agents
- Each agent has a result dict with status and data

**Transformation**:
- Reads agent-specific output formats
- Builds tabs organized by agent type
- Extracts actions and next steps

**Output Format**:
- AggregatedResult with organized, synthesized data
- Ready for UI rendering

### 2. With Phase 2D (UI Rendering)

**From ResultAggregator**:
```python
# Summary for main chat message
chat_message = aggregated_result.summary

# Tabs for Analysis panel
analysis_tabs = aggregated_result.tabs

# Actions for action buttons
action_buttons = [
    {
        "label": action.description,
        "icon": "check" if action.action_type == ActionType.ACCEPT_CHANGES else "edit",
        "onClick": f"performAction('{action.target}')"
    }
    for action in aggregated_result.actions
]

# Next steps for suggestions panel
suggestions = aggregated_result.next_steps
```

**UI Component Integration**:
```tsx
// React component example
function ResultsPanel({ aggregatedResult }) {
    return (
        <div>
            {/* Chat message with summary */}
            <ChatMessage content={aggregatedResult.summary} />
            
            {/* Tab interface */}
            <TabInterface>
                {Object.entries(aggregatedResult.tabs).map(([name, tab]) => (
                    <Tab key={name} title={tab.title} content={tab.data} />
                ))}
            </TabInterface>
            
            {/* Action buttons */}
            <ActionPanel>
                {aggregatedResult.actions.map(action => (
                    <ActionButton key={action.target} action={action} />
                ))}
            </ActionPanel>
            
            {/* Suggestions */}
            <SuggestionsPanel>
                {aggregatedResult.next_steps.map(step => (
                    <Suggestion key={step}>{step}</Suggestion>
                ))}
            </SuggestionsPanel>
        </div>
    );
}
```

---

## LLM Provider Configuration

### Option 1: Default OpenAI Provider

```python
# Uses default OpenAI ProviderChain
aggregator = ResultAggregator(provider="openai", enable_llm=True)
```

Requires `.env`:
```
OPENAI_API_KEY=sk-...
```

### Option 2: Custom Provider Chain

```python
from ki_core.adapters import ProviderChain
from ki_core.adapters import OpenAIClient, AnthropicClient

providers = [
    OpenAIClient(),      # Primary
    AnthropicClient(),   # Fallback
]
chain = ProviderChain(providers, max_retries=3)

aggregator = ResultAggregator(provider_chain=chain, enable_llm=True)
```

### Option 3: Template-Only (No LLM)

```python
# No LLM, always uses template synthesis
aggregator = ResultAggregator(enable_llm=False)

# Works without any API keys
```

### Option 4: Graceful Degradation

```python
# Attempts LLM, falls back to template if unavailable
aggregator = ResultAggregator(provider="openai")

# Will work even if:
# - OpenAI API key missing
# - ki-core not installed
# - Network unavailable
# - LLM timeout
```

---

## Error Handling Patterns

### Handling Failed Agents

When an agent fails, ResultAggregator skips that tab:

```python
executor_result = ExecutorResult(
    results={
        "explain": {"status": "ok", ...},
        "metrics": {"status": "error", "error": "Timeout"},  # Failed
        "refactor": {"status": "ok", ...},
    }
)

aggregated_result = await aggregator.aggregate(executor_result, ...)

# result.tabs contains:
# - "Structure" (from explain) ✓
# - "Refactor" (from refactor) ✓
# - NOT "Metrics" (skipped due to error) ✗

# But aggregation still succeeds!
```

### Handling LLM Failures

LLM failures don't block synthesis:

```python
# LLM is down
aggregator = ResultAggregator(provider="openai")

aggregated_result = await aggregator.aggregate(executor_result, ...)

# result.synthesis_method == "template" (automatic fallback)
# result.summary is still populated (from template)
# User gets results without LLM enhancement
```

### Handling Malformed Agent Data

Missing fields are handled gracefully:

```python
executor_result = ExecutorResult(
    results={
        "explain": {
            "status": "ok"
            # Missing: classes, functions, imports
        }
    }
)

aggregated_result = await aggregator.aggregate(executor_result, ...)

# result.tabs["Structure"] still created
# Defensive defaults: empty lists for missing fields
```

---

## API Endpoint Example

How Phase 2C integrates in a REST API:

```python
from fastapi import FastAPI, HTTPException
from pathlib import Path

app = FastAPI()

executor = AgentExecutor(project_root=Path("."))
aggregator = ResultAggregator(provider="openai")


@app.post("/api/analyze")
async def analyze_code(
    query: str,
    file_path: str,
    session_id: str = None
):
    """Analyze code file and return aggregated results."""
    
    try:
        # Phase 2B: Execute agents
        executor_result = await executor.execute(
            query=query,
            file_path=Path(file_path),
            session_id=session_id
        )
        
        # Phase 2C: Aggregate results
        aggregated_result = await aggregator.aggregate(
            executor_result=executor_result,
            file_path=Path(file_path),
            query=query
        )
        
        # Return as JSON
        return aggregated_result.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Example Request

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain and optimize this function",
    "file_path": "utils.py",
    "session_id": "session-123"
  }'
```

### Example Response

```json
{
  "session_id": "session-123",
  "query": "Explain and optimize this function",
  "summary": "This utility module is well-structured...",
  "tabs": {
    "Structure": {
      "title": "Structure",
      "description": "Code structure overview",
      "data": {
        "classes": [...],
        "functions": [...]
      },
      "agent_type": "explain"
    },
    "Metrics": {
      "title": "Metrics",
      "data": {
        "maintainability_index": 78,
        "complexity": "MEDIUM",
        "overall_health": "Good"
      },
      "agent_type": "metrics"
    }
  },
  "actions": [
    {
      "action_type": "review_diff",
      "target": "process_request",
      "description": "Extract complex validation logic",
      "priority": "high"
    }
  ],
  "next_steps": [
    "Run metrics analysis to check code quality",
    "Review dependencies to understand interactions"
  ],
  "execution_time_ms": 15.3,
  "synthesis_method": "llm"
}
```

---

## Testing Integration

### Unit Test Example

```python
import pytest
from pathlib import Path

@pytest.mark.asyncio
async def test_full_workflow(tmp_path):
    """Test Phase 2B → 2C integration."""
    
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text("def hello(): pass")
    
    # Phase 2B
    executor = AgentExecutor(project_root=tmp_path)
    executor_result = await executor.execute(
        query="Explain this code",
        file_path=test_file
    )
    
    # Phase 2C
    aggregator = ResultAggregator(enable_llm=False)
    aggregated_result = await aggregator.aggregate(
        executor_result=executor_result,
        file_path=test_file,
        query="Explain this code"
    )
    
    # Verify results
    assert aggregated_result.session_id is not None
    assert aggregated_result.summary is not None
    assert len(aggregated_result.tabs) > 0
```

### Integration Test Example

```python
@pytest.mark.asyncio
async def test_api_endpoint(client):
    """Test full API flow."""
    
    response = await client.post(
        "/api/analyze",
        json={
            "query": "Explain this code",
            "file_path": "utils.py",
            "session_id": "test-123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify AggregatedResult structure
    assert "summary" in data
    assert "tabs" in data
    assert "actions" in data
    assert "next_steps" in data
    assert "synthesis_method" in data
```

---

## Performance Considerations

### Latency Budget

Total analysis latency:
- Intent detection (Phase 2A): ~150ms
- AST parsing: ~50ms
- Parallel agent execution: ~200-300ms (max of all agents)
- Result aggregation (Phase 2C): ~10-20ms
- LLM synthesis: ~300-500ms
- **Total: ~700-1000ms** (user-acceptable for analysis)

### Optimization Strategies

1. **Cache AST contexts** (Phase 2B already does this)
   - First query: ~800ms
   - Repeated queries: ~50ms (8x faster)

2. **Template-only mode** for faster responses
   - No LLM: ~350ms (2x faster)
   - Use when latency is critical

3. **Streaming results** (Phase 2E)
   - Send summary immediately (~20ms)
   - Stream tabs as generated (~200-300ms)
   - Show next steps early (~50ms)

4. **Parallel aggregation** (already in Phase 2C)
   - Tab generation runs in parallel
   - No sequential processing

---

## Debugging Tips

### Enable Debug Logging

```python
import logging

# Set aggregator logger to DEBUG
logging.getLogger("kicli_code_assist.agent.aggregator").setLevel(logging.DEBUG)

# Set executor logger to DEBUG too
logging.getLogger("kicli_code_assist.agent.executor").setLevel(logging.DEBUG)

# Now see detailed logs
aggregated_result = await aggregator.aggregate(...)
```

### Inspect Intermediate Results

```python
# Check ExecutorResult
print(f"Intent: {executor_result.intent.intent_type}")
print(f"Agents run: {executor_result.intent.agents_to_run}")
print(f"Results: {list(executor_result.results.keys())}")

# Check AggregatedResult
print(f"Synthesis method: {aggregated_result.synthesis_method}")
print(f"Tabs: {list(aggregated_result.tabs.keys())}")
print(f"Actions: {len(aggregated_result.actions)}")
print(f"Next steps: {len(aggregated_result.next_steps)}")
```

### Mock LLM for Testing

```python
from unittest.mock import AsyncMock, Mock

# Mock the ProviderChain
mock_chain = AsyncMock()
mock_message = Mock()
mock_message.content = "Mocked LLM response"
mock_response = Mock()
mock_response.message = mock_message
mock_chain.achat.return_value = mock_response

# Use in tests
aggregator = ResultAggregator(provider_chain=mock_chain)
result = await aggregator.aggregate(...)
# result.synthesis_method == "llm"
```

---

## Common Issues & Solutions

### Issue: LLM Synthesis Always Falls Back to Template

**Cause**: ProviderChain not initialized or API key missing

**Solution**:
```python
# Option 1: Check API key
import os
assert os.getenv("OPENAI_API_KEY"), "OPENAI_API_KEY not set"

# Option 2: Explicitly pass ProviderChain
from ki_core.adapters import ProviderChain, OpenAIClient
chain = ProviderChain([OpenAIClient()])
aggregator = ResultAggregator(provider_chain=chain)

# Option 3: Accept template synthesis
aggregator = ResultAggregator(enable_llm=False)
```

### Issue: Missing Tabs in Results

**Cause**: Agent failed or executor didn't run that agent

**Solution**:
```python
# Check which agents ran
print(executor_result.intent.agents_to_run)

# Check agent results
for agent_name, result in executor_result.results.items():
    if result.get("status") == "error":
        print(f"Agent {agent_name} failed: {result.get('error')}")

# Verify tabs match agents
print(aggregated_result.tabs.keys())
```

### Issue: Actions Not Generated

**Cause**: Suggest agent didn't run or generated no suggestions

**Solution**:
```python
# Check if suggest agent ran
if "suggest" not in executor_result.intent.agents_to_run:
    print("Suggest agent not included in intent")

# Check suggestions tab
if "Suggestions" in aggregated_result.tabs:
    suggestions = aggregated_result.tabs["Suggestions"].data
    print(f"Suggested files: {len(suggestions.get('suggested_files', []))}")
    print(f"File changes: {len(suggestions.get('file_changes', []))}")
```

---

## Next Phase: 2D UI Integration

Phase 2D will:
1. Render AggregatedResult summary as chat message
2. Display tabs in Analysis panel
3. Show action buttons for recommendations
4. Display next steps as suggestions

Expected output:
```
[Chat Message] "This utility module is well-structured..."

[Analysis Tabs]
├─ Structure (6 functions, 2 classes)
├─ Metrics (Maintainability: 78/100)
├─ Refactor (3 recommendations)
└─ Dependencies (8 imports)

[Action Buttons]
├─ Review process_request refactoring
├─ Extract validation logic
└─ Check performance metrics

[Next Steps]
- Run metrics analysis to check code quality
- Review dependencies to understand interactions
```

---

## Summary

**Phase 2C Integration provides**:
- ✅ Seamless connection from Phase 2B ExecutorResult
- ✅ Graceful degradation on failures
- ✅ Multiple synthesis methods (LLM + template)
- ✅ Organized output ready for Phase 2D UI
- ✅ Comprehensive error handling
- ✅ Full type safety and documentation

**Ready for**: Phase 2D UI implementation and Phase 2E streaming enhancements

---

**Last Updated**: 2026-10-27  
**Version**: Phase 2C (ResultAggregator)  
**Status**: Production Ready ✅

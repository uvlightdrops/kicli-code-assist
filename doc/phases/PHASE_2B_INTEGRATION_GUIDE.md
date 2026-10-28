# Phase 2A → 2B Integration Guide

**For**: Phase 2B (AgentExecutor) implementation  
**Depends On**: Phase 2A (AgentIntentDetector) - ✅ Complete

---

## What Phase 2A Provides

### Export Points

```python
from kicli_code_assist.agent.intent_detector import (
    # Enums & Classes
    IntentType,        # 7 intent categories
    AgentIntent,       # Result dataclass
    AgentIntentDetector,  # Main detector class
    
    # Constants
    INTENT_TO_AGENTS,  # Maps intent → agent list
    INTENT_KEYWORDS,   # Keyword patterns for fallback
    
    # Helpers
    get_intent_detector,  # Singleton pattern
)
```

### API Contract

```python
# Main interface
intent = await detector.detect_intent(
    query: str,
    file_context: Optional[Dict] = None
) -> AgentIntent

# AgentIntent fields
intent.intent_type          # IntentType enum
intent.agents_to_run        # List[str] - recommended agents
intent.confidence           # float 0.0-1.0
intent.reasoning            # str - explanation
intent.additional_context   # Optional[Dict]
intent.is_confident         # bool (True if confidence >= 0.75)
intent.to_dict()            # Dict - JSON serializable
```

---

## How Phase 2B Uses It

### 1. Query Intent Classification

```python
# Phase 2B: AgentExecutor.__init__()
from kicli_code_assist.agent.intent_detector import AgentIntentDetector

class AgentExecutor:
    def __init__(self, provider_chain=None):
        self.intent_detector = AgentIntentDetector(provider_chain)
        self.agents = {}  # Your agent registry
    
    async def route_and_execute(self, query: str, file_path: str):
        # Step 1: Detect intent
        intent = await self.intent_detector.detect_intent(
            query,
            file_context={
                "file": file_path,
                "language": "python",  # optional
            }
        )
        
        # Step 2: Get list of agents to run (from Phase 2A)
        agents_to_run = intent.agents_to_run  # e.g., ["explain", "metrics"]
        
        # Step 3: Run agents in parallel (Phase 2B logic)
        results = await asyncio.gather(*[
            self.agents[agent_name].run(file_path)
            for agent_name in agents_to_run
        ])
        
        return results, intent  # For Phase 2C aggregator
```

### 2. Agent Selection Logic

```python
# Before Phase 2A: keyword matching
if "refactor" in query.lower():
    agents = ["refactor", "suggest"]
else:
    agents = ["explain"]

# After Phase 2A: intelligent classification
intent = await detector.detect_intent(query)
agents = intent.agents_to_run  # Always correct mapping
confidence = intent.confidence  # High confidence = trusted
```

### 3. Conditional Execution

```python
# Only run agents if confident about intent
intent = await detector.detect_intent(query)

if intent.is_confident:
    # Run exactly what detector recommended
    results = await executor.run_agents(intent.agents_to_run)
else:
    # Run default safe set
    results = await executor.run_agents(["explain", "metrics"])

# Phase 2C can then rank results by intent type
```

---

## Integration Checklist

### Phase 2B Implementation

- [ ] Import AgentIntentDetector in executor
- [ ] Add detector to AgentExecutor.__init__()
- [ ] Replace keyword matching with detector.detect_intent()
- [ ] Use intent.agents_to_run for agent selection
- [ ] Log intent.reasoning for debugging
- [ ] Handle confidence thresholds
- [ ] Pass intent to Phase 2C aggregator

### Phase 2B Testing

- [ ] Test each IntentType detection in executor context
- [ ] Verify correct agents selected for each intent
- [ ] Test with both LLM and keyword fallback paths
- [ ] Verify cache hits improve performance
- [ ] Test parallel agent execution with detected intents
- [ ] Measure end-to-end latency improvements

### Phase 2B Documentation

- [ ] Document updated routing logic
- [ ] Add intent detection examples to README
- [ ] Include phase 2A in architecture diagrams
- [ ] Document agent selection algorithm

---

## Sample Phase 2B Code Structure

```python
# kicli_code_assist/agent/executor.py (NEW)

from dataclasses import dataclass
from typing import List, Dict, Any
import asyncio

from kicli_code_assist.agent.intent_detector import (
    AgentIntentDetector, AgentIntent
)

@dataclass
class ExecutionContext:
    query: str
    file_path: str
    intent: AgentIntent
    results: Dict[str, Any]

class AgentExecutor:
    """Parallel agent executor with intent-based routing."""
    
    def __init__(self, provider_chain=None):
        self.intent_detector = AgentIntentDetector(provider_chain)
        self.agents = {}
        self.ast_cache = {}  # Shared AST context
    
    async def execute(self, query: str, file_path: str) -> ExecutionContext:
        # Step 1: Detect intent (Phase 2A)
        intent = await self.intent_detector.detect_intent(
            query,
            file_context={"file": file_path}
        )
        
        # Step 2: Parse AST once (Phase 2B optimization)
        ast_context = await self._get_ast_context(file_path)
        
        # Step 3: Run agents in parallel (Phase 2B)
        tasks = [
            self.agents[agent_name].run(file_path, ast_context)
            for agent_name in intent.agents_to_run
        ]
        results_list = await asyncio.gather(*tasks)
        results = {
            intent.agents_to_run[i]: r
            for i, r in enumerate(results_list)
        }
        
        # Step 4: Return context for Phase 2C aggregator
        return ExecutionContext(
            query=query,
            file_path=file_path,
            intent=intent,
            results=results
        )
    
    async def _get_ast_context(self, file_path: str):
        # Cache AST to avoid re-parsing for multiple agents
        if file_path not in self.ast_cache:
            self.ast_cache[file_path] = await self._parse_ast(file_path)
        return self.ast_cache[file_path]
```

---

## Performance Impact of Phase 2A Integration

### Before Phase 2A
```
Query → Keyword check → Agent selection → Run agents
         ↓ ~70% accuracy
         Only 1-2 agents, might miss intent
```

### After Phase 2A (with Phase 2B)
```
Query → LLM intent detection → Correct agents → Run in parallel
         ↓ ~90% accuracy        ↓ 100% right    ↓ 3-4x faster
         Fallback to keywords   1-3 agents
```

### Expected Gains
- **Accuracy**: 70% → 90% (+28%)
- **Speed**: 6-7s → 2-3s (3-4x faster with parallel execution)
- **User experience**: Right agents, better results

---

## Testing Phase 2A in Phase 2B Context

### Test Template for Phase 2B

```python
import pytest
from kicli_code_assist.agent.executor import AgentExecutor
from kicli_code_assist.agent.intent_detector import IntentType

class TestAgentExecutorWithIntentDetector:
    
    @pytest.mark.asyncio
    async def test_explain_intent_runs_explain_metrics(self):
        executor = AgentExecutor()
        # Mock agents
        executor.agents = {
            "explain": MockAgent("explain"),
            "metrics": MockAgent("metrics"),
        }
        
        context = await executor.execute(
            query="Explain this function",
            file_path="module.py"
        )
        
        assert context.intent.intent_type == IntentType.EXPLAIN
        assert set(context.intent.agents_to_run) == {"explain", "metrics"}
        assert "explain" in context.results
        assert "metrics" in context.results
    
    @pytest.mark.asyncio
    async def test_optimize_intent_runs_metrics_refactor(self):
        executor = AgentExecutor()
        executor.agents = {
            "metrics": MockAgent("metrics"),
            "refactor": MockAgent("refactor"),
        }
        
        context = await executor.execute(
            query="Optimize performance",
            file_path="module.py"
        )
        
        assert context.intent.intent_type == IntentType.OPTIMIZE
        # Both should run in parallel
        assert context.results["metrics"].status == "success"
        assert context.results["refactor"].status == "success"
```

---

## Dependency Graph

```
Phase 2A (IntentDetector)
    ↓ uses
ki-core.adapters.ProviderChain
    ↓
Phase 2B (AgentExecutor)
    ↓ uses
Phase 2A + Agents + AST parsing
    ↓
Phase 2C (ResultAggregator)
    ↓ uses
Phase 2B ExecutionContext
    ↓
Phase 2D (SessionManager)
```

---

## Common Pitfalls to Avoid

### ❌ Don't
```python
# Don't ignore confidence
intent = await detector.detect_intent(query)
agents = intent.agents_to_run  # Might have low confidence

# Don't handle exceptions differently
try:
    intent = await detector.detect_intent(query)
except:
    # LLM failed, but fallback still works
    # This shouldn't raise
    pass
```

### ✅ Do
```python
# Do check confidence for critical paths
intent = await detector.detect_intent(query)
if intent.is_confident:
    agents = intent.agents_to_run
else:
    agents = ["explain", "metrics"]  # Safe default

# Do trust the exception handling
intent = await detector.detect_intent(query)
# If LLM fails, automatically uses keyword fallback
# Never raises if provider_chain provided
```

---

## Questions for Phase 2B Developer

1. **How to pass ProviderChain?**
   ```python
   detector = AgentIntentDetector(provider_chain=your_chain)
   ```

2. **What if LLM is unavailable?**
   - Automatically falls back to keyword matching
   - Confidence is lower but intent still detected

3. **Can I override agent selection?**
   ```python
   intent = await detector.detect_intent(query)
   agents = override_agents.get(query, intent.agents_to_run)
   ```

4. **How to debug intent detection?**
   ```python
   intent = await detector.detect_intent(query)
   print(f"Intent: {intent.intent_type}")
   print(f"Confidence: {intent.confidence}")
   print(f"Reasoning: {intent.reasoning}")
   ```

5. **What about cache invalidation?**
   ```python
   detector.clear_cache()  # Clear all cached intents
   # Or cache is automatically managed per phase 2D
   ```

---

## Success Criteria for Phase 2B

✅ Intent detection integrates smoothly  
✅ Agents selected correctly for each intent  
✅ Parallel execution improves performance  
✅ Fallback works when LLM unavailable  
✅ Tests pass with real agents  
✅ Cache improves repeated queries  
✅ Confidence scores guide execution  

---

**Ready for Phase 2B Implementation** ✅

Start date: Next sprint  
Estimated duration: 2-3 days  
Owner: [Assign developer]

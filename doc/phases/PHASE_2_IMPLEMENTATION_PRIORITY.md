# Phase 2 Implementation Priority & Quick Start

**Document**: Implementation execution guide  
**Audience**: Developers building Phase 2  
**Updated**: 2026-10-27

---

## Quick Summary: What's Wrong Now?

### Current `/api/agent/route` (Phase 1)

```python
# BAD: Keyword-based routing
query_lower = query.lower()
if any(w in query_lower for w in ["refactor", "improve", "optimize"]):
    agents_to_run.append("refactor")

# BAD: Sequential execution
if "explain" in agents_to_run:
    result = agent.explain_code(...)  # ~2s
if "metrics" in agents_to_run:
    result = analyzer.analyze(...)    # ~2s, but could run in parallel

# BAD: Wasted computation - AST parsed twice!
# explain_code() parses AST
# metrics.analyze() parses same file again
```

**Impact**:
- ❌ User query "Create JWT module" → No agents run (no keywords match)
- ❌ Even when agents match, sequential execution is slow (2s + 2s + 2s = 6s)
- ❌ Same file parsed multiple times (AST compute wasted)

---

## Phase 2 Implementation Order

### ✅ STEP 1: Intent Detection (1-2 days)

**Why First**: Foundation for everything else. Other components depend on correct intent classification.

**Files to Create**:
```
kicli_code_assist/agent/intent_detector.py (150 lines)
tests/test_intent_detector.py (100 lines)
```

**Deliverable**: `AgentIntentDetector.detect_intent(query) → AgentIntent`

**Example**:
```python
detector = AgentIntentDetector(provider="openai")

# Input: User query
intent = detector.detect_intent("Create JWT auth module")

# Output:
# AgentIntent(
#   intent_type=IntentType.SUGGEST,
#   agents_to_run=["suggest", "explain"],
#   confidence=0.92,
#   reasoning="User wants architecture suggestion"
# )
```

**Implementation Tips**:
1. Start with GPT-4 via OpenAI API (you likely have credits)
2. Design LLM prompt to output structured JSON
3. Add fallback to keyword matching if LLM fails
4. Cache classifications (same query → same intent)

**Test Cases to Add**:
```python
test_cases = [
    ("Explain this module", IntentType.EXPLAIN, ≥0.8),
    ("Why is this slow?", IntentType.DIAGNOSE, ≥0.75),
    ("Optimize this code", IntentType.OPTIMIZE, ≥0.8),
    ("Is this secure?", IntentType.REVIEW, ≥0.75),
    ("Create JWT auth", IntentType.SUGGEST, ≥0.75),
]
```

**Checkpoint**: Can manually call detector and get reasonable intents

---

### ✅ STEP 2: Shared AST Context (1 day)

**Why Next**: Required for parallel execution. Prevents double-parsing.

**Files to Create/Modify**:
```
kicli_code_assist/agent/analysis/ast_context.py (new, 50 lines)
kicli_code_assist/agent/__init__.py (add ASTContext export)
```

**Modification**:
```python
# In ProgrammingAgent
def explain_code(self, file_path: Path, ast_context: ASTContext = None):
    """Reuse AST if provided, else parse."""
    if ast_context:
        functions = ast_context.functions
        classes = ast_context.classes
    else:
        functions, classes, _ = self.ast_analyzer.analyze_file(file_path)
```

**Same for**:
- `CodeMetricsAnalyzer.analyze_with_ast()`
- `RefactoringAnalyzer.analyze_with_ast()`

**Checkpoint**: Old code still works (no AST provided), but new code path exists

---

### ✅ STEP 3: Parallel Agent Executor (2 days)

**Why Now**: Core performance improvement. Serial → Parallel.

**Files to Create**:
```
kicli_code_assist/agent/executor.py (200 lines)
tests/test_executor.py (150 lines)
```

**Deliverable**: `AgentExecutor.run_parallel(intent, file_path) → List[AgentResult]`

**Key Implementation**:
```python
import asyncio

class AgentExecutor:
    async def run_parallel(self, intent, file_path):
        # Parse AST ONCE
        ast_context = ASTContext.from_file(file_path)
        
        # Build concurrent tasks
        tasks = []
        for agent_type in intent.agents_to_run:
            if agent_type == "explain":
                tasks.append(self._run_explain(file_path, ast_context))
            elif agent_type == "metrics":
                tasks.append(self._run_metrics(file_path, ast_context))
            # ... etc
        
        # Run all in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [
            AgentResult(agent_type, status="success", result=r)
            for agent_type, r in zip(intent.agents_to_run, results)
        ]
```

**Performance Target**:
- 3 agents serial: ~6-7 seconds
- 3 agents parallel: ~3-4 seconds
- **Goal: >30% speedup**

**Checkpoint**: Executor can run agents concurrently, single AST parse, all agents get results

---

### ✅ STEP 4: Update Backend Route Handler (1 day)

**Why Now**: Wire up intent detection + executor to `/api/agent/route`

**File to Modify**:
```
kicli_code_assist/web/server.py (lines 287-450)
```

**Change**:
```python
@app.route("/api/agent/route", methods=["POST"])
def agent_route():
    # ... existing validation ...
    
    # STEP 1: Detect intent (was: keyword matching)
    detector = AgentIntentDetector()
    intent = detector.detect_intent(query)
    
    # STEP 2: Run agents in parallel (was: sequential)
    executor = AgentExecutor(project_root)
    results = asyncio.run(executor.run_parallel(intent, file_path))
    
    # STEP 3: Return aggregated results (next step)
    return jsonify({
        "intent": intent.to_dict(),
        "agents": [r.to_dict() for r in results],
        "session_id": uuid.uuid4(),
    })
```

**Checkpoint**: `/api/agent/route` now uses intent detection + parallel execution

---

### ✅ STEP 5: Result Aggregation (2 days)

**Why Now**: Add intelligence to response. Summary + recommended actions.

**Files to Create**:
```
kicli_code_assist/agent/aggregator.py (200 lines)
tests/test_aggregator.py (100 lines)
```

**Deliverable**: `ResultAggregator.aggregate(results, intent) → AggregatedResults`

**Key**:
```python
class ResultAggregator:
    def aggregate(self, results, intent):
        # Extract insights (highest complexity functions, etc)
        insights = self._extract_insights(results)
        
        # Generate summary using LLM
        summary = self._generate_summary(insights, intent)
        
        # Determine which UI tabs to show
        tabs = self._determine_tabs(results)
        
        # Suggest top actions
        actions = self._rank_actions(insights)
        
        return AggregatedResults(
            summary=summary,
            tabs_to_show=tabs,
            recommended_actions=actions,
            # ... etc
        )
```

**Update Response Schema**:
```json
{
  "intent": {...},
  "results": [{...}],
  "summary": "NEW: Natural language overview",
  "tabs_to_show": ["NEW: Analysis", "Metrics"],
  "recommended_actions": ["NEW: Extract validation"]
}
```

**Checkpoint**: Response includes summary + tabs + actions, frontend can display them

---

### ✅ STEP 6: Session Context (2 days)

**Why Last**: Optimization layer. Caching + follow-ups.

**Files to Create**:
```
kicli_code_assist/agent/session.py (250 lines)
tests/test_session.py (100 lines)
```

**Deliverable**: `SessionManager` for caching + follow-up queries

**New Endpoints**:
- `POST /api/session/create` → creates session, returns session_id
- `GET /api/session/{session_id}` → session metadata
- Update `POST /api/agent/route` to accept `session_id`

**Usage**:
```
Query #1: "Explain this"
  → New session
  → Run all agents
  → Cache results
  
Query #2: "Now optimize" + session_id
  → Check cache: explain results already cached
  → Only run refactor agent
  → Return combined cached + fresh results
  → Response shows {"from_cache": true} for explain
```

**Checkpoint**: Sessions work, caching prevents redundant analysis

---

## Implementation Reality Check

### Time Estimates (Best Case)
- Step 1 (Intent): 8-12 hours
- Step 2 (AST Context): 4-6 hours
- Step 3 (Executor): 12-16 hours
- Step 4 (Backend Update): 4-6 hours
- Step 5 (Aggregation): 12-16 hours
- Step 6 (Sessions): 12-16 hours

**Total: 52-72 hours (~1-1.5 weeks)**

### Risk Factors
1. **LLM Integration** - First time? Add +2 days to Step 1
2. **Async/Await** - Not familiar with asyncio? Add +1 day to Step 3
3. **Testing** - No test infrastructure? Add +1 day per step
4. **Integration Issues** - Components not playing nice? Budget +1 day

### Recommended Approach

**Option A: Phased (Recommended)**
- Build all 6 steps completely
- Each step has working tests
- Deploy as single PR
- Timeline: 1.5 weeks

**Option B: MVP (Faster, Less Complete)**
- Skip Step 6 (Sessions) for now
- Deploy Steps 1-5 as MVP
- Add Sessions later
- Timeline: 1 week
- Trade-off: No caching/follow-ups yet

**Option C: Minimal (Fastest)**
- Just do Steps 1-3 + Step 4
- Skip aggregation, skip sessions
- Fast LLM routing + parallel execution
- Timeline: 3-4 days
- Trade-off: UI gets raw results, no smart summary

---

## Testing Strategy

### Unit Tests (Per Step)

**Step 1**: Intent Detector
```python
def test_common_queries():
    detector = AgentIntentDetector()
    
    assert detector.detect_intent("Explain this").intent_type == IntentType.EXPLAIN
    assert detector.detect_intent("Optimize this").intent_type == IntentType.OPTIMIZE
    
    intent = detector.detect_intent("Security review please")
    assert "review" in intent.agents_to_run or intent.confidence < 0.7
```

**Step 3**: Executor
```python
async def test_parallel_execution():
    executor = AgentExecutor(project_root)
    intent = AgentIntent(agents_to_run=["explain", "metrics"])
    
    results = await executor.run_parallel(intent, "src/app.py")
    
    assert len(results) == 2
    assert all(r.status == "success" for r in results)
    
    # Verify shared AST (should parse only once)
    # Check executor internals to confirm
```

### Integration Tests (Cross-Step)

```python
def test_full_flow():
    # Intent detection
    detector = AgentIntentDetector()
    intent = detector.detect_intent("Optimize this module")
    
    # Parallel execution
    executor = AgentExecutor(project_root)
    results = asyncio.run(executor.run_parallel(intent, "src/app.py"))
    
    # Aggregation
    aggregator = ResultAggregator()
    final = aggregator.aggregate(results, intent)
    
    assert final.summary  # Has summary
    assert len(final.tabs_to_show) > 0  # Knows what to show
    assert len(final.recommended_actions) > 0  # Suggests actions
```

### E2E Tests (Full API)

```python
def test_api_flow():
    # Call actual endpoint
    response = client.post("/api/agent/route", {
        "query": "Explain this and find optimizations",
        "file_path": "src/app.py",
        "scope": "folder",
        "project": "/path"
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify new Phase 2 fields
    assert "intent" in data
    assert "summary" in data
    assert "tabs_to_show" in data
    assert "recommended_actions" in data
    
    # Verify Phase 1 backward compat
    assert "agents" in data
    assert "session_id" in data
```

---

## Git Workflow

### Branch Strategy
```bash
git checkout -b phase2-intelligent-routing
git checkout -b phase2-step1-intent-detection

# After Step 1 complete
git commit -m "Phase 2 Step 1: LLM-based intent detection

- AgentIntentDetector with GPT-4 backend
- Keyword fallback for resilience
- Unit tests covering 20+ query types
- Confidence scores for each detection"

git push origin phase2-step1-intent-detection
# Create PR for review

# After review approved
git checkout phase2-intelligent-routing
git merge phase2-step1-intent-detection
git branch -d phase2-step1-intent-detection
```

### Key Commits
1. `[Phase 2.1] Intent Detection` - AgentIntentDetector
2. `[Phase 2.2] AST Context Sharing` - Update analyzers
3. `[Phase 2.3] Parallel Executor` - AgentExecutor
4. `[Phase 2.4] Backend Integration` - Update /api/agent/route
5. `[Phase 2.5] Result Aggregation` - ResultAggregator
6. `[Phase 2.6] Session Context` - SessionManager + endpoints

---

## Quality Checklist (Each Step)

Before marking a step complete:

- [ ] Code written (primary files)
- [ ] Tests written (>80% coverage)
- [ ] Tests passing (`pytest tests/test_*.py`)
- [ ] No type errors (`mypy src/`)
- [ ] No lint issues (`ruff check`)
- [ ] Docstrings complete
- [ ] Backward compatibility verified
- [ ] Git commit with clear message
- [ ] PR created with test results

---

## Common Pitfalls to Avoid

### Pitfall 1: Not Testing Incrementally
❌ Build all 6 steps, then test  
✅ Test each step before moving to next

### Pitfall 2: Async/Await Complexity
❌ Use `asyncio.run()` everywhere  
✅ Understand event loop, use `await` properly

### Pitfall 3: AST Context Not Shared
❌ Pass ASTContext but agents still parse file  
✅ Verify parsers check if AST provided before re-parsing

### Pitfall 4: No Fallback for LLM
❌ Intent detection breaks if LLM fails  
✅ Always fall back to keyword matching

### Pitfall 5: Forgetting Backward Compat
❌ Change response schema, break Phase 1 clients  
✅ Keep old fields, add new ones, verify old clients work

---

## Success Criteria per Step

| Step | Done When... |
|------|--------------|
| 1 | Intent detection works for 20+ test queries with confidence |
| 2 | AST only parsed once (verify in executor logs) |
| 3 | Parallel execution >30% faster than sequential |
| 4 | `/api/agent/route` returns new response schema |
| 5 | Summary + tabs + actions included in response |
| 6 | Session caching prevents redundant analysis |

---

## Next: Implementation

→ See `PHASE_2_TECHNICAL_SPEC.md` for API contracts and detailed interfaces  
→ Start with Step 1: `AgentIntentDetector`  
→ Use `test_intent_detector.py` as template

# Agent Routing Intelligence Plan: From Keyword Matching to Real Agentic Behavior

**Status**: Architecture Design Phase  
**Priority**: Critical Path for Hybrid Agent UI  
**Timeline**: Phase 2 Implementation  
**Owner**: Copilot Agent Development

---

## Executive Summary

The current `/api/agent/route` endpoint uses **dumb keyword-based intent detection**. We need to build **real agent intelligence** with:

1. **LLM-based Intent Detection** - Understand semantic intent, not just keywords
2. **Parallel Agent Execution** - Run multiple agents concurrently via `asyncio.gather()`
3. **Smart Result Aggregation** - Combine results contextually, auto-generate summaries
4. **Session Context Tracking** - Avoid redundant analysis, enable follow-up conversations

---

## Current State Analysis

### Keyword-Based Routing (Phase 1)
**File**: `kicli_code_assist/web/server.py`, lines 340-350

```python
# Current approach - fragile and limited
query_lower = query.lower()
if any(w in query_lower for w in ["refactor", "improve", "optimize"]):
    agents_to_run.append("refactor")
```

**Problems**:
- ❌ "Simplify this complex module" → Not detected (no "refactor" keyword)
- ❌ "What patterns does this use?" → Detected as nothing (no keyword match)
- ❌ "Show me security issues" → Detected as nothing (no security agent exists yet)
- ❌ No understanding of user intent: explain ≠ refactor ≠ review
- ❌ Cannot combine intent with confidence levels (this is definitely explain-focused)

### Sequential Agent Execution (Phase 1)
**File**: `kicli_code_assist/web/server.py`, lines 360-405

```python
# Current approach - runs agents one by one
if "explain" in agents_to_run:
    agent = ProgrammingAgent(project_root)
    result = agent.explain_code(...)  # Blocks until complete
    results.append(...)

if "metrics" in agents_to_run:
    analyzer = CodeMetricsAnalyzer(...)
    result = analyzer.analyze(...)    # Blocks until complete
    results.append(...)
```

**Problems**:
- ❌ Even though explain + metrics share AST, we parse twice (compute waste)
- ❌ Analysis time = T1 + T2 + T3... instead of max(T1, T2, T3)
- ❌ No way to track progress or cancel if user interrupts
- ❌ UI blocks waiting for full serial execution

### Existing Analysis Components (Shared Infrastructure)

✅ **Already exists**:
- `ASTAnalyzer` - Parses Python AST, extracts functions/classes/imports
- `DependencyResolver` - Quick impact analysis (what depends on this file)
- `ProjectAnalysisService` - Metadata for entire project
- `SemanticIndexer` - (Minimal) keyword/semantic search placeholder
- `SmartSelector` - Context window management for LLM input

✅ **Analyzers available**:
- `CodeMetricsAnalyzer` - Complexity, maintainability, function metrics
- `RefactoringAnalyzer` - Refactor suggestions based on metrics
- `DependencyAnalyzer` - Dependency structure and coupling
- `ProgrammingAgent.explain_code()` - AST-based explanation
- `ProgrammingAgent.suggest_refactoring()` - Heuristic suggestions

**All share common AST context** - Opportunity to pass AST as shared parameter instead of re-parsing.

---

## Proposed Architecture

### 1. LLM-Based Intent Detection

**Component**: `AgentIntentDetector` (New)

```
User Query
    ↓
┌─────────────────────────────┐
│   AgentIntentDetector       │
│  (LLM-based classifier)     │
└─────────────────────────────┘
    ↓
Intent Classification:
- intent_type: str (explain | refactor | review | optimize | diagnose)
- agents_to_run: List[str]
- confidence: float (0.0-1.0)
- reasoning: str (why these agents)
```

**Implementation**:
```python
class AgentIntentDetector:
    """Classify user intent using LLM, not keywords."""
    
    def __init__(self, llm_provider: str = "openai"):
        # Use GPT-4, Claude, or local Ollama
        self.llm = self._init_llm(llm_provider)
    
    def detect_intent(self, query: str) -> AgentIntent:
        """
        Analyze query to determine:
        1. What the user is trying to accomplish
        2. Which agents can help
        3. How confident we are
        
        Examples:
        - Query: "Create a user authentication module with JWT"
          Intent: AgentIntent(
              type="suggest",
              agents=["suggest", "explain"],  # Explain best practices
              confidence=0.92,
              reasoning="User wants architecture suggestions"
          )
        
        - Query: "Why does this take so long?"
          Intent: AgentIntent(
              type="diagnose",
              agents=["metrics", "dependencies", "refactor"],
              confidence=0.85,
              reasoning="Performance diagnosis required"
          )
        
        - Query: "Simplify this"
          Intent: AgentIntent(
              type="refactor",
              agents=["metrics", "refactor"],
              confidence=0.78,
              reasoning="Simplification implies complexity issue"
          )
        """
        prompt = self._build_classification_prompt(query)
        response = self.llm.classify(prompt)
        return self._parse_intent_response(response)
```

**Advantages**:
- ✅ Understands semantic meaning, not just keywords
- ✅ Detects compound intents (explain + optimize)
- ✅ Confidence scores → Can show user "I'm 92% sure you want refactor"
- ✅ Reasoning explanations → User understands why agents were chosen
- ✅ Graceful fallback to keyword detection if LLM unavailable

### 2. Parallel Agent Execution with Shared Context

**Component**: `AgentExecutor` (Refactored)

**Architecture**:
```
Query → Intent Detection → Parallel Agent Pool

                ┌─────────────────────────────┐
                │  Shared AST Context         │
                │  (parsed once, used by all) │
                └─────────────────────────────┘
                           ↓
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
      Explain Agent  Metrics Agent  Refactor Agent
      (2.1s)         (1.8s)         (3.4s)
          ↓                ↓                ↓
          └────────────────┼────────────────┘
                           ↓
                  Results Aggregated (3.4s total)
                  Instead of serial (7.3s)
```

**Implementation**:
```python
class AgentExecutor:
    """Execute multiple agents in parallel with shared context."""
    
    async def run_parallel(
        self, 
        intent: AgentIntent,
        file_path: Path,
        project_root: Path,
        scope: str = "folder"
    ) -> AgentResults:
        """
        Run all agents in intent.agents_to_run concurrently.
        
        Key insight: Pass shared AST context to all agents
        to avoid re-parsing the file multiple times.
        """
        # Parse AST ONCE
        ast_context = self._parse_ast(file_path)
        
        # Build concurrent tasks
        tasks = []
        for agent_type in intent.agents_to_run:
            if agent_type == "explain":
                task = self._run_explain(file_path, ast_context)
            elif agent_type == "metrics":
                task = self._run_metrics(file_path, ast_context)
            elif agent_type == "refactor":
                task = self._run_refactor(file_path, ast_context)
            elif agent_type == "dependencies":
                task = self._run_dependencies(file_path, ast_context)
            else:
                continue
            
            tasks.append(task)
        
        # Run all concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate and handle errors
        return self._aggregate_results(results, intent)
    
    async def _run_explain(self, file_path: Path, ast_context: AST):
        """Run explain agent (now receives shared AST)."""
        agent = ProgrammingAgent(self.project_root)
        # Pass AST context to avoid re-parsing
        return agent.explain_code(file_path, ast_context=ast_context)
    
    async def _run_metrics(self, file_path: Path, ast_context: AST):
        """Run metrics agent."""
        analyzer = CodeMetricsAnalyzer(self.project_root)
        # Metrics can use pre-parsed AST
        return analyzer.analyze_with_ast(file_path, ast_context)
```

**Benefits**:
- ✅ Parallel execution: 3 seconds instead of 7 seconds
- ✅ Shared AST context: parse once, use everywhere
- ✅ No wasted I/O: dependency graph computed once
- ✅ Can add progress reporting: "Analyzing... 67%"
- ✅ Can handle per-agent timeouts: If metrics takes >5s, show partial results

### 3. Smart Result Aggregation

**Component**: `ResultAggregator` (New)

**Current behavior**: Return flat list of agent results
```json
{
  "agents": [
    {"type": "explain", "result": {...}},
    {"type": "metrics", "result": {...}}
  ]
}
```

**Improved behavior**: Aggregate + synthesize
```json
{
  "intent": "explain_with_refactor",
  "confidence": 0.92,
  
  "summary": "Module has high cyclomatic complexity (avg 7.2) and could be simplified by breaking into 3 smaller functions. Consider extracting validation logic.",
  
  "results": {
    "explain": {
      "structure": {...},
      "functions": [...]
    },
    "metrics": {
      "complexity_issues": [...],
      "maintainability_index": 62
    },
    "refactor": {
      "suggestions": [...],
      "estimated_effort": "medium"
    }
  },
  
  "tabs_to_show": ["Analysis", "Metrics", "Refactor"],
  "recommended_actions": [
    {
      "action": "Extract validation",
      "file": "user.py",
      "line": 42
    }
  ]
}
```

**Implementation**:
```python
class ResultAggregator:
    """Combine individual agent results into coherent summary."""
    
    def aggregate(
        self,
        results: Dict[str, Any],
        intent: AgentIntent,
        file_path: Path
    ) -> AggregatedResults:
        """
        1. Combine structure + metrics (they share AST)
        2. Auto-generate summary from agent outputs
        3. Determine which UI tabs to show
        4. Suggest recommended actions
        """
        
        # Extract key insights from each agent
        insights = self._extract_insights(results)
        
        # Generate coherent summary
        summary = self._generate_summary(insights, intent)
        
        # Determine UI tabs based on results
        tabs = self._determine_tabs(results)
        
        # Suggest top actions
        actions = self._rank_actions(insights)
        
        return AggregatedResults(
            summary=summary,
            results=results,
            tabs_to_show=tabs,
            actions=actions,
            confidence=intent.confidence
        )
```

**Benefits**:
- ✅ Frontend gets actionable summary, not just raw data
- ✅ Knows which tabs to show (no empty panels)
- ✅ Suggested actions prioritized
- ✅ Explains combined findings in natural language

### 4. Session Context Tracking

**Component**: `AgentSession` (Database-backed)

**Purpose**: Track analysis history within a conversation, avoid re-running same analysis

**Schema**:
```python
@dataclass
class AgentSession:
    session_id: str
    project_path: str
    created_at: datetime
    last_activity: datetime
    
    # Current state
    current_file: str
    current_scope: str  # "folder" or "project"
    
    # Analysis cache (don't re-run if unchanged)
    analyses: Dict[str, AnalysisResult]  # key: "{file}:{scope}:{intent}"
    file_hashes: Dict[str, str]  # track if file changed since last analysis

class AnalysisResult:
    file_path: str
    intent_type: str
    agents_run: List[str]
    results: Dict
    timestamp: datetime
    file_hash: str  # MD5 of analyzed file
```

**Usage**:
```
User Query #1: "Explain this"
  → New session created, file hash stored
  → Analysis run, results cached
  
User Query #2: "Now optimize it"
  → Same file hash
  → Reuse explain results from cache
  → Only run refactor agent
  
User modifies file
  → Session detects file hash changed
  → Clear cached results for that file
  → Next query triggers fresh analysis
```

**Benefits**:
- ✅ Follow-up conversations don't re-analyze
- ✅ User can ask "based on the explain above, what should I refactor?" → uses cached explain
- ✅ Cross-tab state: if user switches files and back, remembers prior analysis
- ✅ Foundation for "pinning" results or generating reports

---

## Implementation Roadmap

### Phase 2A: LLM Intent Detection (1-2 days)
```
1. Create AgentIntentDetector class
   - Support OpenAI, Claude, Ollama backends
   - Build classification prompt
   - Parse LLM response into AgentIntent
   
2. Update /api/agent/route
   - Call detector instead of keyword matching
   - Fall back to keyword matching if LLM unavailable
   - Return intent + confidence in response
   
3. Test with example queries
   - "Create JWT auth module"
   - "Why is this slow?"
   - "Simplify this code"
```

### Phase 2B: Parallel Agent Execution (2-3 days)
```
1. Refactor analyzers to accept shared AST context
   - Update CodeMetricsAnalyzer.analyze_with_ast()
   - Update RefactoringAnalyzer.analyze_with_ast()
   - Update ProgrammingAgent to use pre-parsed AST
   
2. Build AgentExecutor
   - Implement asyncio.gather() for parallel runs
   - Add progress callback (for UI progress bar)
   - Add per-agent timeout handling
   
3. Rewrite /api/agent/route to use executor
   - Parse AST once
   - Pass to executor.run_parallel()
   - Return aggregated results
   
4. Performance testing
   - Measure time: serial vs parallel
   - Target: >30% speed improvement
```

### Phase 2C: Smart Result Aggregation (2-3 days)
```
1. Build ResultAggregator
   - Extract key insights per agent
   - Generate LLM-powered summary
   - Auto-determine tabs to show
   
2. Update response schema
   - Include summary field
   - Include tabs_to_show field
   - Include recommended_actions field
   
3. Frontend integration
   - Display summary in Analysis tab header
   - Only render tabs in tabs_to_show
   - Show recommended actions as buttons
   
4. Test with real code samples
```

### Phase 2D: Session Context (2-3 days)
```
1. Add session database layer
   - SQLite or small Redis-backed store
   - Track session_id lifecycle
   
2. Implement session manager
   - Create session on first query
   - Check cache on subsequent queries
   - Invalidate on file changes
   
3. Update /api/agent/route
   - Accept session_id in request
   - Check cache before running analysis
   - Return which results are cached vs fresh
   
4. Frontend integration
   - Show "From prior analysis" badge on cached results
   - Allow user to force refresh
```

---

## Code Changes Required

### Backend Files to Modify

**New files**:
```
kicli_code_assist/agent/intent_detector.py (150 lines)
kicli_code_assist/agent/executor.py (200 lines)
kicli_code_assist/agent/aggregator.py (150 lines)
kicli_code_assist/agent/session.py (200 lines)
```

**Modified files**:
```
kicli_code_assist/web/server.py
  - Replace /api/agent/route logic
  - Add new endpoints: /api/session/*, /api/intent/test
  - ~150 lines changed

kicli_code_assist/agent/metrics.py
  - Add analyze_with_ast(ast_context) method
  - Avoid re-parsing if AST provided
  
kicli_code_assist/agent/refactoring.py
  - Add analyze_with_ast(ast_context) method
  
kicli_code_assist/agent/__init__.py
  - Update ProgrammingAgent to accept ast_context parameter
```

### Frontend Files to Modify

**Modified files**:
```
web/frontend/src/components/UnifiedAgentChat.tsx
  - Handle confidence scores
  - Display intent classification reasoning
  - Show "From prior analysis" badges for cached results

web/frontend/src/components/AnalysisPanel.tsx
  - Render tabs from tabs_to_show
  - Display recommended_actions
  - Show summary header
  - Add "Force Refresh" button
```

---

## Testing Strategy

### Unit Tests
```python
# test_intent_detector.py
def test_intent_detection_examples():
    detector = AgentIntentDetector()
    
    # Test various queries
    intent = detector.detect_intent("Create JWT auth")
    assert "suggest" in intent.agents_to_run
    
    intent = detector.detect_intent("Why is this slow?")
    assert "metrics" in intent.agents_to_run
    assert "dependencies" in intent.agents_to_run
```

### Integration Tests
```python
# test_agent_routing.py
async def test_parallel_execution():
    executor = AgentExecutor(project_root)
    intent = AgentIntent(agents_to_run=["explain", "metrics", "refactor"])
    
    start = time.time()
    results = await executor.run_parallel(intent, file_path)
    elapsed = time.time() - start
    
    # Should be faster than serial
    assert elapsed < 7.0  # Was ~7s serial, should be ~3-4s parallel
```

### E2E Tests
```python
# test_user_flows.py
def test_explain_and_optimize_flow():
    # User asks to explain
    resp1 = client.post("/api/agent/route", {
        "query": "Explain this module",
        "file_path": "src/auth.py"
    })
    assert "explain" in [r["type"] for r in resp1["agents"]]
    session_id = resp1["session_id"]
    
    # User asks to optimize (should reuse explain results)
    resp2 = client.post("/api/agent/route", {
        "query": "Now optimize it",
        "file_path": "src/auth.py",
        "session_id": session_id
    })
    assert any(r["cached"] for r in resp2["agents"] if r["type"] == "explain")
```

---

## Success Criteria

✅ **LLM Intent Detection**
- Correctly classify 90%+ of test queries
- Graceful fallback to keyword matching
- Confidence scores ≥ 0.8 for confident predictions

✅ **Parallel Execution**
- >30% speed improvement (3 agents: 7s → <5s)
- Shared AST context working (no duplicate parses)
- Proper error handling per agent

✅ **Result Aggregation**
- Summary generated for 100% of analyses
- Tabs correctly determined (no empty panels)
- Recommended actions ranked by impact

✅ **Session Context**
- Cache hit rate >50% for follow-up queries
- File change detection working
- Session persistence across page reloads

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| LLM API cost | $$ | Implement local Ollama option, cache classifications |
| LLM latency | Slow UX | Classify while agents run in background |
| Shared AST bugs | Wrong results | Comprehensive unit tests, gradual rollout |
| Cache invalidation | Stale results | Strong file hashing, manual refresh option |

---

## Questions for Review

1. **LLM Provider**: Use OpenAI GPT-4, Claude 3.5, or local Ollama?
2. **Cache Backend**: SQLite, Redis, or just in-memory?
3. **Timeout Strategy**: How long to wait for slow agents before showing partial results?
4. **Agent Weighting**: Should "metrics" have higher weight than "dependencies" in results summary?
5. **UI Feedback**: Show progress bar for parallel execution, or just wait until complete?

---

## Related Documentation

- `HYBRID_AGENT_IMPLEMENTATION_PLAN.md` - Phase 1-2 roadmap
- `PROGRAMMING_AGENT_UI_ARCHITECTURE.md` - UI design rationale
- `PHASE_1_HYBRID_IMPLEMENTATION.md` - Current Phase 1 status

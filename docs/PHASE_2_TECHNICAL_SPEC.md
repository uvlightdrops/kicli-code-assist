# Phase 2 Technical Specification: Agent Intelligence System

**Document Purpose**: Detailed API contracts, data structures, and implementation checklist  
**Audience**: Developers implementing Phase 2  
**Last Updated**: 2026-10-27

---

## Table of Contents

1. [Data Structures](#data-structures)
2. [API Contracts](#api-contracts)
3. [Component Responsibilities](#component-responsibilities)
4. [Integration Points](#integration-points)
5. [Backward Compatibility](#backward-compatibility)
6. [Implementation Checklist](#implementation-checklist)

---

## Data Structures

### Intent Classification

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class IntentType(Enum):
    """User intent categories."""
    EXPLAIN = "explain"
    REFACTOR = "refactor"
    REVIEW = "review"
    OPTIMIZE = "optimize"
    DIAGNOSE = "diagnose"
    SUGGEST = "suggest"
    VALIDATE = "validate"

@dataclass
class AgentIntent:
    """Result of LLM-based intent classification."""
    
    # Core classification
    intent_type: IntentType
    agents_to_run: List[str]  # ["explain", "metrics", "refactor"]
    confidence: float  # 0.0 to 1.0
    
    # Explanation for user/debugging
    reasoning: str  # "User asked about performance → metrics + dependencies"
    
    # Optional metadata
    additional_context: Optional[Dict[str, str]] = None
    
    @property
    def is_confident(self) -> bool:
        """Returns True if confidence >= 0.75."""
        return self.confidence >= 0.75
    
    def to_dict(self) -> Dict:
        return {
            "intent_type": self.intent_type.value,
            "agents_to_run": self.agents_to_run,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "additional_context": self.additional_context,
        }
```

### Shared AST Context

```python
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class ASTContext:
    """Shared AST analysis result, passed to all agents."""
    
    file_path: str
    
    # Core AST data (from ASTAnalyzer)
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    imports: List[ImportInfo]
    
    # Dependency graph
    dependencies: Dict[str, List[str]]  # This file depends on...
    dependents: List[str]  # Files that depend on this
    
    # Caching
    parsed_at: str  # ISO timestamp
    file_hash: str  # MD5 of file contents
    
    @staticmethod
    def from_file(file_path: Path) -> "ASTContext":
        """Parse file and build context."""
        analyzer = ASTAnalyzer()
        resolver = DependencyResolver(file_path.parent)
        
        functions, classes, imports = analyzer.analyze_file(file_path)
        dependents = resolver.get_file_dependents(file_path)
        
        return ASTContext(
            file_path=str(file_path),
            functions=functions,
            classes=classes,
            imports=imports,
            dependencies={},  # TODO: populate from imports
            dependents=[str(f) for f in dependents],
            parsed_at=datetime.now().isoformat(),
            file_hash=hashlib.md5(file_path.read_bytes()).hexdigest(),
        )
```

### Agent Results

```python
from typing import Any, Optional

@dataclass
class AgentResult:
    """Result from a single agent execution."""
    
    agent_type: str  # "explain", "metrics", "refactor", etc.
    status: str  # "success", "error", "timeout"
    
    # Result data
    result: Dict[str, Any]
    
    # Metadata
    error: Optional[str] = None
    execution_time_ms: float = 0
    from_cache: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "agent_type": self.agent_type,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "from_cache": self.from_cache,
        }
```

### Aggregated Results

```python
@dataclass
class AggregatedResults:
    """Combined results from all agents, with synthesis."""
    
    # Intent that led to these results
    intent: AgentIntent
    
    # Individual agent results
    results: Dict[str, AgentResult]  # {agent_type: result}
    
    # Synthesis
    summary: str  # Natural language summary of findings
    recommended_actions: List[Dict[str, Any]]  # [{"action": "...", "file": "...", "line": ...}]
    tabs_to_show: List[str]  # ["Analysis", "Metrics", "Refactor"]
    
    # Metadata
    total_execution_time_ms: float
    session_id: str
    
    def to_dict(self) -> Dict:
        return {
            "intent": self.intent.to_dict(),
            "results": {k: v.to_dict() for k, v in self.results.items()},
            "summary": self.summary,
            "recommended_actions": self.recommended_actions,
            "tabs_to_show": self.tabs_to_show,
            "total_execution_time_ms": self.total_execution_time_ms,
            "session_id": self.session_id,
        }
```

### Session Tracking

```python
from datetime import datetime

@dataclass
class SessionAnalysis:
    """Cached analysis result within a session."""
    
    file_path: str
    intent_type: str
    agents_run: List[str]
    results: Dict[str, Any]
    timestamp: str  # ISO format
    file_hash: str
    execution_time_ms: float

@dataclass
class AgentSession:
    """User session tracking for context and caching."""
    
    session_id: str
    project_path: str
    created_at: str  # ISO timestamp
    last_activity: str
    
    # Current context
    current_file: Optional[str] = None
    current_scope: str = "folder"  # "folder" or "project"
    
    # Analysis cache
    analyses: Dict[str, SessionAnalysis] = field(default_factory=dict)
    
    @property
    def cache_key(self, file_path: str, intent_type: str) -> str:
        """Generate cache key for analysis lookup."""
        return f"{file_path}:{intent_type}"
    
    def get_cached_analysis(self, file_path: str, intent_type: str, file_hash: str) -> Optional[SessionAnalysis]:
        """Get cached analysis if file hasn't changed."""
        key = self.cache_key(file_path, intent_type)
        analysis = self.analyses.get(key)
        
        if analysis and analysis.file_hash == file_hash:
            return analysis
        return None
    
    def store_analysis(self, file_path: str, analysis: SessionAnalysis):
        """Cache analysis result."""
        key = self.cache_key(file_path, analysis.intent_type)
        self.analyses[key] = analysis
        self.last_activity = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "project_path": self.project_path,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "current_file": self.current_file,
            "current_scope": self.current_scope,
        }
```

---

## API Contracts

### POST /api/agent/route (Updated)

**Request**:
```json
{
  "query": "Explain this module and show optimization opportunities",
  "file_path": "src/authentication/jwt_handler.py",
  "scope": "folder",
  "project": "/path/to/project",
  "session_id": "optional-for-follow-ups"
}
```

**Response** (New structure):
```json
{
  "intent": {
    "intent_type": "explain",
    "agents_to_run": ["explain", "metrics", "refactor"],
    "confidence": 0.92,
    "reasoning": "Query contains 'explain' (high signal), 'optimization' (refactor signal). Metrics always paired with explain."
  },
  
  "results": {
    "explain": {
      "agent_type": "explain",
      "status": "success",
      "result": { ... },
      "execution_time_ms": 2100,
      "from_cache": false
    },
    "metrics": {
      "agent_type": "metrics",
      "status": "success",
      "result": { ... },
      "execution_time_ms": 1800,
      "from_cache": false
    },
    "refactor": {
      "agent_type": "refactor",
      "status": "success",
      "result": { ... },
      "execution_time_ms": 3200,
      "from_cache": false
    }
  },
  
  "summary": "The JWT handler has 5 functions with average cyclomatic complexity of 6.2. Consider extracting token validation into a separate validator class. High coupling to auth service (imported by 8 files) suggests extracting reusable utilities.",
  
  "recommended_actions": [
    {
      "action": "Extract token validation",
      "priority": "high",
      "file": "src/authentication/jwt_handler.py",
      "line": 42,
      "justification": "Complexity 7, only called from 1 function"
    }
  ],
  
  "tabs_to_show": ["Analysis", "Metrics", "Refactor"],
  "total_execution_time_ms": 3200,
  "session_id": "uuid-abc123..."
}
```

**HTTP Status**:
- `200 OK` - Analysis completed
- `400 Bad Request` - Missing required fields
- `403 Forbidden` - Path outside allowed root
- `500 Internal Server Error` - Agent execution failed

### POST /api/session/create (New)

**Request**:
```json
{
  "project_path": "/path/to/project"
}
```

**Response**:
```json
{
  "session_id": "uuid-abc123...",
  "created_at": "2026-10-27T13:57:27Z"
}
```

### GET /api/session/{session_id} (New)

**Response**:
```json
{
  "session_id": "uuid-abc123...",
  "project_path": "/path/to/project",
  "created_at": "2026-10-27T13:57:27Z",
  "last_activity": "2026-10-27T14:02:15Z",
  "current_file": "src/auth.py",
  "current_scope": "folder",
  "cached_analyses": 3
}
```

### POST /api/intent/test (Debug endpoint, optional)

**Purpose**: Test LLM intent detection without running agents

**Request**:
```json
{
  "query": "Fix this performance bottleneck"
}
```

**Response**:
```json
{
  "intent_type": "diagnose",
  "agents_to_run": ["metrics", "dependencies", "profiler"],
  "confidence": 0.88,
  "reasoning": "Query contains 'performance' + 'bottleneck' → diagnostic intent",
  "prompt_used": "..."
}
```

---

## Component Responsibilities

### AgentIntentDetector

**File**: `kicli_code_assist/agent/intent_detector.py`

**Responsibilities**:
1. Accept user query as input
2. Classify intent using LLM (with keyword fallback)
3. Determine which agents to run
4. Return AgentIntent with confidence

**Public Interface**:
```python
class AgentIntentDetector:
    def __init__(self, llm_provider: str = "openai"):
        """Initialize detector with LLM backend."""
        
    def detect_intent(self, query: str) -> AgentIntent:
        """Classify user intent and determine agents to run."""
    
    def test_classify(self, query: str) -> Dict:
        """Debug endpoint: show classification reasoning."""
```

**Testing**:
```python
def test_all_example_queries():
    detector = AgentIntentDetector()
    
    test_cases = [
        ("Explain this module", ["explain", "metrics"]),
        ("Why is this slow?", ["metrics", "dependencies", "refactor"]),
        ("Fix security issues", ["review", "suggest"]),
        ("Simplify this code", ["metrics", "refactor"]),
    ]
    
    for query, expected_agents in test_cases:
        intent = detector.detect_intent(query)
        assert all(a in intent.agents_to_run for a in expected_agents)
```

### AgentExecutor

**File**: `kicli_code_assist/agent/executor.py`

**Responsibilities**:
1. Parse file AST once (shared context)
2. Run all agents in intent.agents_to_run concurrently
3. Handle per-agent timeouts and errors
4. Return list of AgentResult

**Public Interface**:
```python
class AgentExecutor:
    def __init__(self, project_root: Path, timeout_per_agent: float = 10.0):
        """Initialize executor."""
    
    async def run_parallel(
        self,
        intent: AgentIntent,
        file_path: Path,
        scope: str = "folder"
    ) -> List[AgentResult]:
        """Execute all agents concurrently."""
    
    async def run_single(
        self,
        agent_type: str,
        file_path: Path,
        ast_context: ASTContext
    ) -> AgentResult:
        """Execute single agent (internal use)."""
```

**Testing**:
```python
async def test_parallel_speed():
    executor = AgentExecutor(project_root)
    intent = AgentIntent(agents_to_run=["explain", "metrics", "refactor"])
    
    start = time.time()
    results = await executor.run_parallel(intent, file_path="src/app.py")
    elapsed = time.time() - start
    
    # Parallel should be much faster than serial
    assert elapsed < 5.0
    assert len(results) == 3
    assert all(r.status == "success" for r in results)
```

### ResultAggregator

**File**: `kicli_code_assist/agent/aggregator.py`

**Responsibilities**:
1. Extract key insights from agent results
2. Generate natural language summary
3. Determine which tabs to show UI
4. Rank and suggest recommended actions

**Public Interface**:
```python
class ResultAggregator:
    def aggregate(
        self,
        results: List[AgentResult],
        intent: AgentIntent,
        file_path: Path
    ) -> AggregatedResults:
        """Combine and synthesize agent results."""
    
    def _extract_insights(self, results: List[AgentResult]) -> Dict[str, Any]:
        """Pull out key findings from each agent."""
    
    def _generate_summary(self, insights: Dict, intent: AgentIntent) -> str:
        """Create coherent summary using LLM."""
    
    def _determine_tabs(self, results: List[AgentResult]) -> List[str]:
        """Decide which UI tabs to show."""
    
    def _rank_actions(self, insights: Dict) -> List[Dict]:
        """Suggest top actionable changes."""
```

**Testing**:
```python
def test_aggregation():
    results = [
        AgentResult("explain", "success", {...}),
        AgentResult("metrics", "success", {...}),
    ]
    intent = AgentIntent(...)
    
    aggregator = ResultAggregator()
    agg_results = aggregator.aggregate(results, intent, Path("src/app.py"))
    
    assert agg_results.summary  # Non-empty summary
    assert "Metrics" in agg_results.tabs_to_show
    assert len(agg_results.recommended_actions) > 0
```

### SessionManager

**File**: `kicli_code_assist/agent/session.py`

**Responsibilities**:
1. Create and manage user sessions
2. Track cached analyses
3. Detect file changes (via hash)
4. Invalidate cache when files change

**Public Interface**:
```python
class SessionManager:
    def __init__(self, storage_path: Path = None):
        """Initialize session manager with optional persistent storage."""
    
    def create_session(self, project_path: str) -> AgentSession:
        """Create new session."""
    
    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Retrieve existing session."""
    
    def store_analysis(
        self,
        session_id: str,
        file_path: str,
        analysis: SessionAnalysis
    ):
        """Cache analysis result."""
    
    def get_cached_analysis(
        self,
        session_id: str,
        file_path: str,
        intent_type: str,
        current_file_hash: str
    ) -> Optional[SessionAnalysis]:
        """Retrieve cached analysis if file unchanged."""
```

**Testing**:
```python
def test_session_caching():
    manager = SessionManager()
    session = manager.create_session("/path/to/project")
    
    # Cache an analysis
    analysis = SessionAnalysis(
        file_path="src/app.py",
        intent_type="explain",
        ...
    )
    manager.store_analysis(session.session_id, analysis)
    
    # Retrieve it
    cached = manager.get_cached_analysis(
        session.session_id,
        "src/app.py",
        "explain",
        analysis.file_hash
    )
    assert cached is not None
    
    # File changed, cache invalidates
    cached = manager.get_cached_analysis(
        session.session_id,
        "src/app.py",
        "explain",
        "different_hash"
    )
    assert cached is None
```

---

## Integration Points

### Backend Flow

```
POST /api/agent/route
  ↓
[1] Validate request (file exists, scope valid)
  ↓
[2] Create or resume session
  ↓
[3] LLM-based intent detection
      AgentIntentDetector.detect_intent(query)
  ↓
[4] Check session cache
      SessionManager.get_cached_analysis(...)
  ↓
[5] If cache miss, run agents in parallel
      executor = AgentExecutor(project_root)
      await executor.run_parallel(intent, file_path)
  ↓
[6] Aggregate results
      aggregator = ResultAggregator()
      aggregated = aggregator.aggregate(results, intent, file_path)
  ↓
[7] Store in session cache
      SessionManager.store_analysis(session_id, aggregated)
  ↓
[8] Return aggregated results with session_id
      response = aggregated.to_dict()
      return jsonify(response)
```

### Modified Agent Interfaces

**ProgrammingAgent**:
```python
# CURRENT (Phase 1)
def explain_code(self, file_path: Path, line_no: Optional[int] = None) -> Dict:
    """Explain a file."""

# UPDATED (Phase 2)
def explain_code(
    self, 
    file_path: Path, 
    line_no: Optional[int] = None,
    ast_context: Optional[ASTContext] = None
) -> Dict:
    """Explain a file, optionally using pre-parsed AST."""
    if ast_context:
        # Use provided context, skip parsing
        functions = ast_context.functions
        classes = ast_context.classes
    else:
        # Parse file (legacy behavior)
        functions, classes, imports = self.ast_analyzer.analyze_file(file_path)
```

**CodeMetricsAnalyzer**:
```python
# CURRENT (Phase 1)
def analyze(self, file_path: str | Path) -> dict:
    """Analyze metrics for single file."""

# NEW (Phase 2)
def analyze_with_ast(
    self, 
    file_path: Path,
    ast_context: ASTContext
) -> dict:
    """Analyze metrics using pre-parsed AST."""
```

### Frontend Changes (UnifiedAgentChat)

**Current**:
```typescript
const response = await axios.post('/api/agent/route', {
  query: inputValue,
  file_path: currentFile,
  scope: scope,
  project: projectPath,
});

// Gets back: {intent, agents: [...]}
```

**Updated**:
```typescript
const response = await axios.post('/api/agent/route', {
  query: inputValue,
  file_path: currentFile,
  scope: scope,
  project: projectPath,
  session_id: sessionId,  // NEW: for follow-up context
});

// Gets back: {intent, results: {...}, summary, tabs_to_show, recommended_actions}

// Display summary
setText(response.data.summary);

// Show recommended actions as buttons
response.data.recommended_actions.forEach(action => {
  addButton(action.action, () => applyAction(action));
});

// Only render tabs in tabs_to_show
const tabs = response.data.tabs_to_show;  // ["Analysis", "Metrics"]
```

---

## Backward Compatibility

### Phase 1 → Phase 2 Migration

**No breaking changes** to existing code:

1. ✅ `/api/agent/route` endpoint still accepts Phase 1 requests
2. ✅ Response includes all Phase 1 fields (`agents` array still present)
3. ✅ Optional `session_id` field (client can omit it)
4. ✅ Analyzers accept optional AST context (default to parsing if not provided)
5. ✅ Existing tests continue to work

**Graceful Degradation**:
- If LLM unavailable → Fall back to keyword intent detection
- If session storage unavailable → No caching, but analysis still works
- If aggregator fails → Return raw agent results (previous behavior)

### Testing Backward Compatibility

```python
def test_phase1_request_still_works():
    """Ensure old /api/agent/route requests still work."""
    response = client.post("/api/agent/route", {
        "query": "Explain this",
        "file_path": "src/app.py",
        "scope": "folder",
        "project": "/path/to/project"
        # NO session_id
    })
    
    assert response.status_code == 200
    # Phase 1 clients expect this structure
    assert "agents" in response.json()
    assert "session_id" in response.json()
    
    # New structure also present
    assert "intent" in response.json()
    assert "summary" in response.json()
```

---

## Implementation Checklist

### Phase 2A: Intent Detection

- [ ] Create `kicli_code_assist/agent/intent_detector.py`
  - [ ] `AgentIntentDetector` class
  - [ ] LLM integration (GPT-4 / Claude / Ollama)
  - [ ] Keyword fallback logic
  - [ ] Unit tests (test_intent_detector.py)

- [ ] Update `/api/agent/route`
  - [ ] Call `AgentIntentDetector.detect_intent(query)`
  - [ ] Include intent + confidence in response
  - [ ] Debug endpoint `/api/intent/test`

- [ ] Integration testing
  - [ ] Test with real queries
  - [ ] Verify fallback behavior
  - [ ] Measure LLM latency

### Phase 2B: Parallel Execution

- [ ] Create `kicli_code_assist/agent/executor.py`
  - [ ] `AgentExecutor` class
  - [ ] Async task management
  - [ ] Per-agent timeout handling
  - [ ] Error aggregation

- [ ] Refactor analyzers to accept AST context
  - [ ] Update `ProgrammingAgent.explain_code(ast_context=...)`
  - [ ] Update `CodeMetricsAnalyzer.analyze_with_ast(...)`
  - [ ] Update `RefactoringAnalyzer.analyze_with_ast(...)`

- [ ] Performance testing
  - [ ] Measure serial vs parallel time
  - [ ] Target >30% speedup
  - [ ] Profile memory usage

### Phase 2C: Result Aggregation

- [ ] Create `kicli_code_assist/agent/aggregator.py`
  - [ ] `ResultAggregator` class
  - [ ] Summary generation using LLM
  - [ ] Tab determination logic
  - [ ] Action ranking

- [ ] Update response schema
  - [ ] Include `summary` field
  - [ ] Include `tabs_to_show` list
  - [ ] Include `recommended_actions`

- [ ] Frontend integration
  - [ ] Display summary in Analysis tab
  - [ ] Render only tabs in `tabs_to_show`
  - [ ] Show recommended actions

### Phase 2D: Session Context

- [ ] Create `kicli_code_assist/agent/session.py`
  - [ ] `AgentSession` dataclass
  - [ ] `SessionManager` class
  - [ ] Storage backend (SQLite or in-memory)

- [ ] New API endpoints
  - [ ] `POST /api/session/create`
  - [ ] `GET /api/session/{session_id}`
  - [ ] `DELETE /api/session/{session_id}` (optional)

- [ ] Integration with `/api/agent/route`
  - [ ] Accept `session_id` in request
  - [ ] Check cache before running analysis
  - [ ] Store results in session cache

- [ ] Session cleanup
  - [ ] Expire old sessions (>24 hours)
  - [ ] Limit session storage per project

### Cross-Phase Testing

- [ ] Full e2e: Query → Intent → Parallel Execution → Aggregation → Cache
- [ ] Error scenarios: LLM down, agent timeout, file not found, etc.
- [ ] Performance: Measure end-to-end latency
- [ ] UI integration: Frontend displays results correctly
- [ ] Backward compatibility: Phase 1 clients still work

### Documentation

- [ ] API documentation (swagger/OpenAPI)
- [ ] LLM prompt examples
- [ ] Configuration guide (LLM provider selection)
- [ ] Troubleshooting guide
- [ ] Performance tuning guide

---

## Success Metrics

| Metric | Target | Phase |
|--------|--------|-------|
| Intent detection accuracy | ≥90% | 2A |
| Parallel speedup | ≥30% | 2B |
| Cache hit rate | ≥50% | 2D |
| LLM latency | <2s | 2A |
| Summary generation | <1s | 2C |
| **Total request latency** | **<6s** | 2B+C+D |

---

## Related Documents

- `AGENT_ROUTING_INTELLIGENCE_PLAN.md` - Strategic overview
- `HYBRID_AGENT_IMPLEMENTATION_PLAN.md` - Phase 1-2 roadmap
- Current endpoint: `kicli_code_assist/web/server.py` lines 287-423

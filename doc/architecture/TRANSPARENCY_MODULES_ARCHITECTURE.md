---
title: "Phase 5.5.2: Transparency & Observability - Architecture"
project: "kicli-code-assist"
scope: "architecture"
created: 2026-11-02T00:18:00+01:00
updated: 2026-11-02T00:18:00+01:00
update_reason: "Concept for real-time agent reasoning and cost tracking"
status: "active"
author: "Copilot"
---

# Phase 5.5.2: Transparency & Observability - Architecture

## Problem Statement

When agent executes a complex task, users have **zero visibility** into:
- **Why** did agent choose this workflow?
- **What** LLM calls were made?
- **How much** did it cost (tokens)?
- **Which** decisions were automatic vs. human-chosen?

Current state:
- Logs buried in `log/kicli-llm.log` (not accessible in UI)
- No cost tracking
- No decision audit trail
- No real-time progress updates

---

## Vision

**Goal:** Agents expose their complete reasoning in **real-time, at zero cost**.

```
User submits refactoring task
  ↓
Agent starts execution
  ├─ Reasoning Event: "Intent detected: multi_file_refactoring"
  ├─ Decision Event: "Selected WorkflowType.REFACTORING (confidence: 0.94)"
  ├─ Analysis Event: "Analyzing impact... found 7 files"
  ├─ LLM Event: "Calling Claude 3.5 Sonnet"
  │  ├─ Tokens: 450 input, 200 output
  │  ├─ Cost: $0.002
  │  └─ Time: 1.2s
  ├─ Verification Event: "Syntax check: ✓ OK"
  ├─ Test Event: "Running pytest... 45 passed, 0 failed (3.2s)"
  └─ Completion Event: "Success! Branch: refactor/user-account, Commit: abc123..."
  
  → ALL events streamed to WebSocket in real-time
  → Displayed in Frontend debug panel
  → Downloadable audit file JSON
```

---

## Architecture

### 1. ReasoningTracer (Core)

```python
class ReasoningTracer:
    """Capture all agent decisions and reasoning."""
    
    def log_decision(
        self,
        decision_type: str,          # "intent", "workflow", "strategy"
        decision: str,               # What was decided
        alternatives: List[str],     # Other options considered
        confidence: float,           # 0.0-1.0
        reasoning: str              # Why this decision
    ) → Event:
        """Log a decision point."""
    
    def log_analysis(
        self,
        analysis_type: str,          # "impact", "dependencies", "risks"
        findings: Dict
    ) → Event:
        """Log analysis results."""
    
    def log_error(
        self,
        error_type: str,
        error: Exception,
        recovery_strategy: Optional[str]
    ) → Event:
        """Log errors and recovery attempts."""
    
    def export_trace(self) → Dict:
        """Export complete trace as structured data."""
```

**Data Structure:**

```python
@dataclass
class ReasoningEvent:
    timestamp: datetime
    event_type: str          # "decision", "analysis", "error", "success"
    category: str            # "intent", "workflow", "code", "test", etc.
    message: str
    details: Dict = field(default_factory=dict)
    confidence: Optional[float] = None
    alternatives: List[str] = field(default_factory=list)
    elapsed_ms: int = 0
```

### 2. LLMCallTracker (Middleware)

```python
class LLMCallTracker:
    """Track all LLM calls with cost & performance."""
    
    async def track_call(
        self,
        model: str,
        prompt: str,
        response: str,
        tokens_input: int,
        tokens_output: int
    ) → LLMCallRecord:
        """Record LLM call."""
    
    def calculate_cost(
        self,
        model: str,
        tokens_input: int,
        tokens_output: int
    ) → float:
        """Calculate USD cost based on model pricing."""
    
    def get_session_stats(self) → LLMStats:
        """Get aggregate stats: total calls, cost, tokens."""
```

**Data Structure:**

```python
@dataclass
class LLMCallRecord:
    timestamp: datetime
    model: str                 # "gpt-4", "claude-3.5-sonnet", etc.
    tokens_input: int
    tokens_output: int
    tokens_total: int
    cost_usd: float
    latency_ms: int
    purpose: str              # "intent_detection", "code_generation"
    prompt_preview: str       # First 100 chars
    response_preview: str
    success: bool
    error: Optional[str] = None

@dataclass
class LLMStats:
    total_calls: int
    total_tokens: int
    total_cost_usd: float
    average_latency_ms: float
    calls_by_model: Dict[str, int]
    errors: int
```

### 3. PerformanceMetrics (Timeline)

```python
class PerformanceMetrics:
    """Track timing and performance of each phase."""
    
    def start_phase(self, phase_name: str) → PhaseTimer:
        """Start timing a phase."""
    
    def end_phase(self, phase_name: str) → PhaseMetrics:
        """End timing, record metrics."""
    
    def get_timeline(self) → List[PhaseMetrics]:
        """Get all phases with timing."""
    
    def identify_bottlenecks(self) → List[Bottleneck]:
        """Which phases took longest?"""
```

**Data Structure:**

```python
@dataclass
class PhaseMetrics:
    phase_name: str
    start_time: datetime
    end_time: datetime
    duration_ms: int
    success: bool
    sub_phases: List[PhaseMetrics] = field(default_factory=list)

@dataclass
class Bottleneck:
    phase: str
    duration_ms: int
    percentage_of_total: float
    recommendation: str
```

### 4. AuditExporter (Output)

```python
class AuditExporter:
    """Export reasoning trace for compliance/debugging."""
    
    def export_json(self, trace: ReasoningTrace) → str:
        """Export as JSON."""
    
    def export_yaml(self, trace: ReasoningTrace) → str:
        """Export as YAML."""
    
    def export_markdown(self, trace: ReasoningTrace) → str:
        """Export as human-readable Markdown."""
    
    def export_for_compliance(self) → ComplianceReport:
        """Export with: timestamp, actor, decisions, costs, actions."""
```

---

## Integration Points

### 1. Extend CoordinationResult

```python
@dataclass
class CoordinationResult:
    # Existing fields
    success: bool
    query: str
    intent: AgentIntent
    workflow: str
    agents_used: List[str]
    answer: str
    tabs: Dict[str, Any]
    actions: List[Dict]
    timing_ms: Dict[str, int]
    error: Optional[str]
    
    # NEW: Transparency
    reasoning_trace: ReasoningTrace  # Full trace
    llm_stats: LLMStats             # Cost + token summary
    performance_timeline: List[PhaseMetrics]  # Timing breakdown
    audit_trail_url: Optional[str]  # URL to download audit file
```

### 2. WebSocket Streaming (Real-time)

```python
@app.websocket("/ws/agent/reasoning")
async def websocket_reasoning(websocket: WebSocket, session_id: str):
    """Stream reasoning events in real-time."""
    await websocket.accept()
    
    # Connect to session's reasoning tracer
    tracer = reasoning_tracer_registry.get(session_id)
    
    # Stream events as they occur
    async for event in tracer.stream_events():
        await websocket.send_json(event.to_dict())
```

### 3. REST Endpoint for Audit Export

```python
@app.get("/api/agent/audit/{session_id}")
async def get_audit_trail(session_id: str, format: str = "json"):
    """Download audit trail."""
    trace = reasoning_tracer_registry.get(session_id).export_trace()
    exporter = AuditExporter()
    
    if format == "json":
        return JSONResponse(exporter.export_json(trace))
    elif format == "yaml":
        return StreamingResponse(exporter.export_yaml(trace))
    elif format == "markdown":
        return StreamingResponse(exporter.export_markdown(trace))
    else:
        raise HTTPException(status_code=400)
```

---

## Frontend Components

### ReasoningPanel

Real-time display of agent reasoning:

```typescript
// Components/ReasoningPanel.tsx

interface ReasoningEvent {
  timestamp: ISO8601;
  event_type: "decision" | "analysis" | "llm" | "test" | "success";
  message: string;
  confidence?: number;
  details: Record<string, any>;
}

export const ReasoningPanel = () => {
  const [events, setEvents] = useState<ReasoningEvent[]>([]);
  const ws = useWebSocket("/ws/agent/reasoning");
  
  useEffect(() => {
    ws.onMessage = (event) => {
      setEvents(prev => [...prev, JSON.parse(event.data)]);
      // Auto-scroll to bottom
    };
  }, [ws]);
  
  return (
    <div className="reasoning-panel">
      <h2>Agent Reasoning</h2>
      <div className="event-timeline">
        {events.map((e, i) => (
          <ReasoningEventCard key={i} event={e} />
        ))}
      </div>
      <CostSummary />
      <DownloadAuditButton />
    </div>
  );
};
```

### CostSummary

Display cost breakdown:

```typescript
<div className="cost-summary">
  <div className="stat">
    <span>Total LLM Calls:</span>
    <strong>{stats.total_calls}</strong>
  </div>
  <div className="stat">
    <span>Tokens:</span>
    <strong>{stats.total_tokens.toLocaleString()}</strong>
  </div>
  <div className="stat">
    <span>Estimated Cost:</span>
    <strong>${stats.total_cost_usd.toFixed(4)}</strong>
  </div>
  <div className="stat">
    <span>Avg Latency:</span>
    <strong>{stats.average_latency_ms}ms</strong>
  </div>
</div>
```

---

## Data Flow Example

**User:** "Refactor UserAccount class across project"

**Timeline:**

```
00:00ms   ReasoningTracer.start()
00:05ms   log_decision("intent", "multi_file_refactoring", confidence=0.92)
00:10ms   → WebSocket: Decision event (real-time)
00:15ms   log_decision("workflow", "REFACTORING", confidence=0.89)
00:20ms   → WebSocket: Workflow event
00:100ms  log_analysis("impact", {files: 7, imports: 12, usages: 45})
00:110ms  → WebSocket: Analysis event
00:200ms  LLMCallTracker.track_call("claude-3.5-sonnet", ...)
00:800ms  → LLM response received
01:000ms  log_analysis("code_generated", {lines: 120, methods: 3})
02:000ms  PerformanceMetrics.end_phase("code_generation")
         → WebSocket: Timing event
02:500ms  log_analysis("tests", {passed: 45, failed: 0})
02:510ms  → WebSocket: Test success event
02:600ms  log_decision("commit", "auto_commit", confidence=1.0)
02:610ms  → WebSocket: Completion event
         
Result:
  → CoordinationResult includes:
    - reasoning_trace: All 15 events
    - llm_stats: {calls: 2, cost: $0.004, tokens: 1250}
    - performance_timeline: 7 phases
    - audit_trail_url: /api/agent/audit/session-123
```

---

## Success Criteria

- ✅ Every decision traced + alternatives shown
- ✅ Every LLM call logged + cost calculated
- ✅ Real-time WebSocket stream (<100ms latency)
- ✅ Audit trail exportable as JSON/YAML/Markdown
- ✅ Cost accurate to ±1% vs. OpenAI invoice
- ✅ Zero overhead (<50ms per decision)
- ✅ Works with existing agents (no breaking changes)

---

## Files to Create

```
kicli_code_assist/agent/
├── reasoning_tracer.py      # Core tracing
├── llm_call_tracker.py      # LLM cost tracking
├── performance_metrics.py   # Timing analysis
├── audit_exporter.py        # Output formats
└── transparency_middleware.py # Integration
```

---

## Next Steps

1. Implement core modules (tracing, tracking, metrics)
2. Integrate into existing agents (no breaking changes)
3. Add WebSocket streaming endpoint
4. Build frontend components
5. Test with real workflows
6. Measure overhead + optimize

---


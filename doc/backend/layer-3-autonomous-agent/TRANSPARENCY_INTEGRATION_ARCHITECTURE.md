---
title: Phase 5.5.2 Transparency Integration Architecture
project: kicli-code-assist
agent_project: kicli-code-assist
scope: Backend Architecture / Layer 3 Autonomous Agents / Phase 5.5.2
purpose: Design transparency module integration for Phase 5.5.2
created: 2026-11-02T03:05:37+01:00
updated: 2026-11-07T12:38:00+01:00
update_reason: Upgraded to semantic schema, shortened title
status: stable

semantic_blocks:
  - id: transparency-modules
    type: implementation
    status: stable
    version: 1.0

relations:
  - target: README
    type: part-of
    reason: "Phase 5.5.2 transparency & observability capability"
    
  - target: AGENT_COORDINATION_ARCHITECTURE
    type: extends
    reason: "Adds observability to the 6-stage orchestration pipeline"
    
  - target: MULTIFILE_REFACTORING_ARCHITECTURE
    type: extends
    reason: "Provides transparency for multi-file refactoring operations"
---

# Phase 5.5.2 Transparency Integration

**Phase:** 5.5.2 Transparency Implementation
**Subphase:** Integration with CodeImplementationAgent
**Status:** In Progress
**Start Time:** 2026-11-02T03:05:37+01:00

---

## Overview

Integrate 3 transparency modules (ReasoningTracer, LLMCallTracker, PerformanceMetrics) into CodeImplementationAgent to provide:

1. **Real-time decision tracking** - Every decision point logged with confidence
2. **Cost visibility** - Every LLM call tracked with actual pricing
3. **Performance metrics** - Phase timing, token usage, error rates

Result: Agent execution becomes fully transparent + auditable.

---

## Architecture

```
CodeImplementationAgent (existing)
  ↓
  ├─→ ReasoningTracer (new): Track all decisions + errors
  ├─→ LLMCallTracker (new): Track LLM cost + tokens
  └─→ PerformanceMetrics (new): Track phase timing + custom metrics
  
  Results exported to:
  ├─→ JSON files (persistence)
  ├─→ WebSocket stream (real-time)
  └─→ HTTP API (queries)
```

### Integration Points

| Agent Method | Tracer Call | Tracker Call | Metrics Call |
|--------------|-------------|--------------|--------------|
| `__init__` | `start_session()` | — | `start_phase("initialization")` |
| `analyze_project()` | `record_event(ANALYSIS_START)` | — | `start_phase("analysis")` |
| `_make_llm_decision()` | `record_decision()` | — | — |
| `_call_llm()` | — | `record_call()` | `start_timer("llm_call")` |
| `_apply_changes()` | `record_execution()` | — | `start_phase("apply_changes")` |
| `_verify_changes()` | `record_event(VERIFICATION)` | — | — |
| Error handler | `record_error()` | — | `increment_counter("errors")` |
| `execute()` finalize | `end_session()` | — | `end_phase()`, `finalize()` |

---

## Implementation Steps

### Step 1: Modify CodeImplementationAgent Constructor
- Create ReasoningTracer instance
- Create LLMCallTracker instance
- Create PerformanceMetrics instance
- Store references as `self.tracer`, `self.tracker`, `self.metrics`

### Step 2: Add Session/Phase Lifecycle Hooks
- `execute()` start: Create session, start phase
- `execute()` end: End session, finalize metrics, export

### Step 3: Instrument Decision Points
- `_make_llm_decision()`: Call `tracer.record_decision()`
- `_call_llm()`: 
  - Call `tracker.record_call()` with actual LLM call data
  - Call `metrics.start_timer()` before call
  - Call `metrics.stop_timer()` after call

### Step 4: Instrument Execution Points
- `_apply_changes()`: Call `tracer.record_execution()`
- Error handlers: Call `tracer.record_error()`

### Step 5: Export Results
- `execute()` completion:
  - `tracer.end_session()` → saves JSON
  - `metrics.save_metrics()` → saves JSON
  - Generate report in agent response

---

## File Changes Required

### 1. CodeImplementationAgent

**File:** `/home/flow/dev_flow/kicli-code-assist/kicli_code_assist/agent/code_implementation.py`

**Changes:**
- Import: `from .reasoning_tracer import ReasoningTracer, EventType`
- Import: `from .llm_call_tracker import LLMCallTracker, CallPurpose`
- Import: `from .performance_metrics import PerformanceMetrics`
- Constructor: Initialize 3 modules
- `execute()`: Wrap with session/phase management
- Decision/LLM/Execution points: Add tracer/tracker/metrics calls
- Finalize: Export results to JSON

**Estimated Lines:** +150-200 LOC

### 2. WebSocket Streaming Handler (NEW)

**File:** `/home/flow/dev_flow/kicli-code-assist/kicli_code_assist/web/server_websocket.py` (modify)

**Changes:**
- New namespace: `/agent/execution`
- Event types: `decision`, `execution`, `error`, `llm_call`, `metric_update`
- Stream reasoning events in real-time as they occur

**Estimated Lines:** +100-150 LOC

### 3. HTTP API Endpoint (NEW)

**File:** `/home/flow/dev_flow/kicli-code-assist/kicli_code_assist/web/server.py` (modify)

**Changes:**
- `GET /api/agent/execution/{id}/events` - Get all events from session
- `GET /api/agent/execution/{id}/metrics` - Get performance metrics
- `GET /api/agent/execution/{id}/cost` - Get LLM cost breakdown
- `GET /api/agent/execution/{id}/report` - Get full HTML report

**Estimated Lines:** +100-150 LOC

### 4. Frontend: ReasoningPanel (NEW)

**File:** `/home/flow/dev_flow/kicli-code-assist/web/frontend/src/components/ReasoningPanel.tsx`

**Changes:**
- Display events in real-time via WebSocket
- Event types with color coding:
  - 🟢 DECISION (cyan)
  - 🔵 EXECUTION (blue)
  - 🟠 ERROR (orange)
  - 💰 LLM_CALL (yellow)
- Collapsible event details (decision options, LLM response, etc.)
- Cost summary badge
- Metrics chart (phase timing, token usage)

**Estimated Lines:** +300-400 LOC (TSX + hooks)

---

## Data Flow

```
CodeImplementationAgent.execute()
  ↓
  1. tracer.start_session() → session_id
  2. metrics.start_phase("analyze")
  3. _analyze_project()
     → tracer.record_event(ANALYSIS_START)
  4. _make_llm_decision()
     → tracer.record_decision(options, selected, confidence)
  5. _call_llm()
     → tracer.record_decision("llm_call", ...)
     → tracker.record_call(model, tokens, cost)
     → metrics.start_timer("llm_call") / stop_timer()
  6. _apply_changes()
     → tracer.record_execution(action, result)
     → metrics.start_phase("apply")
  7. [Events streamed via WebSocket to frontend in real-time]
  8. tracer.end_session() → save JSON + emit SESSION_END event
  9. metrics.finalize() → aggregate results
  10. metrics.save_metrics() → save JSON
  11. Return response with session_id + report
  
  Frontend displays:
  - Real-time events stream
  - Cost breakdown
  - Phase timings
  - Error recovery suggestions
```

---

## Timeline

| Phase | Task | Est. Time | Dependencies |
|-------|------|-----------|--------------|
| I1 | CodeImplementationAgent integration | 60 min | ✅ Modules ready |
| I2 | WebSocket streaming handler | 40 min | I1 |
| I3 | HTTP API endpoints | 40 min | I1 |
| I4 | Frontend ReasoningPanel component | 60 min | I2 |
| I5 | End-to-end testing + debugging | 40 min | I1-I4 |

**Total Estimated Time:** ~240 minutes (~4 hours)

---

## Testing Strategy

### Unit Tests
- CodeImplementationAgent initialization with modules
- Tracer/tracker/metrics calls at key points
- Session lifecycle management

### Integration Tests
- Full execution with all transparency modules
- WebSocket event streaming
- HTTP API queries
- Frontend event display

### E2E Tests
- Code generation request
- Watch events in real-time on frontend
- Verify cost calculation
- Verify phase timing
- Verify metrics aggregation

---

## Success Criteria

✅ CodeImplementationAgent integrates all 3 modules  
✅ Session created/ended properly  
✅ Events recorded at all decision/execution points  
✅ LLM calls tracked with cost calculation  
✅ WebSocket streams events in real-time  
✅ HTTP API returns correct data  
✅ Frontend displays events + metrics  
✅ All existing tests still pass  
✅ No performance regression (<5% slowdown)

---

## Rollback Plan

If integration fails:
1. Keep modules as separate optional imports
2. Add `enable_transparency=False` flag to CodeImplementationAgent
3. Can disable transparency without affecting core functionality

---

## Next Actions

1. ✅ Create this concept document
2. → Modify CodeImplementationAgent (I1)
3. → Add WebSocket handler (I2)
4. → Add HTTP endpoints (I3)
5. → Create ReasoningPanel component (I4)
6. → End-to-end testing (I5)

**Start:** Phase 5.5.2.I1 - CodeImplementationAgent Integration

---

**Document Created:** 2026-11-02T03:05:37+01:00  
**Status:** Ready for Implementation
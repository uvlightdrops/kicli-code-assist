# Phase 2: Agent Routing Intelligence - Executive Summary

**Status**: Architecture & Design Complete, Ready for Implementation  
**Timeline**: 1-1.5 weeks (52-72 developer-hours)  
**Complexity**: Medium-High (async programming, LLM integration)  
**Impact**: 3x+ performance improvement, semantic understanding, session awareness

---

## The Problem

Current `/api/agent/route` endpoint has three critical limitations:

### 1. Dumb Keyword Matching (Not Real Intent)
```
User: "Create JWT authentication module"
System: No keywords match → No agents run
Result: ❌ User gets nothing

User: "Why is this slow?"
System: Finds no "refactor" keyword → Doesn't run metrics
Result: ❌ Wrong agents chosen
```

### 2. Sequential Execution (Wasteful)
```
Agent A runs: 2 seconds
Agent B runs: 2 seconds (could run in parallel)
Agent C runs: 2 seconds (could run in parallel)

Total: 6 seconds when it could be 2 seconds
```

### 3. Redundant AST Parsing
```
File: src/app.py

Explain Agent: Parse AST → 800ms
Metrics Agent: Parse AST again → 800ms (same file!)

Wasted: 800ms compute
```

---

## The Solution

Build **Real Agent Intelligence** with 4 capabilities:

### 1. LLM-Based Intent Detection ✅
Instead of keyword matching, use Claude/GPT-4 to understand intent:
```
User: "Create JWT auth module"
LLM: "User wants architecture suggestions" 
→ Run: [suggest, explain]  ✅

User: "Why is this slow?"
LLM: "Performance diagnosis"
→ Run: [metrics, dependencies, refactor]  ✅
```

### 2. Parallel Agent Execution ✅
Run multiple agents concurrently instead of sequentially:
```
Timeline: 6 seconds → 2-3 seconds (3x faster)

Agent A: [====2s====]
Agent B:      [====2s====]
Agent C:           [====2s====]
Total:       [====~3s====]
```

### 3. Smart Result Aggregation ✅
Combine results into actionable insight:
```
Individual Results:
- explain: {structure: {...}}
- metrics: {complexity: 7.2, functions: [...]}
- refactor: {suggestions: [...]}

Aggregated:
"Module has high complexity (7.2 avg). 
Consider extracting validation (line 42).
3 functions exceed recommended length."

Plus: tabs_to_show = ["Analysis", "Metrics"]
Plus: recommended_actions = [{extract_validation, high_priority}]
```

### 4. Session Context Tracking ✅
Avoid redundant analysis in conversations:
```
Query 1: "Explain this" 
→ Analyze all agents, cache results

Query 2: "Now optimize it" (same file)
→ Reuse explain from cache
→ Only run refactor agent
→ 50% less computation
```

---

## Architecture Overview

```
┌─────────────────────────────────────────┐
│ User Query: "Explain and optimize"      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ 1. Intent Detector (LLM)                │
│ "explain" + "optimize" intent           │
│ confidence: 0.92                        │
└─────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────┐
│ 2. Parse AST (ONCE)              │
│ Shared context for all agents    │
└──────────────────────────────────┘
                    ↓
    ┌───────────────┼───────────────┐
    ↓               ↓               ↓
┌────────┐     ┌────────┐     ┌────────┐
│Explain │     │Metrics │     │Refactor│
│(2s)    │     │(2s)    │     │(2s)    │
└────────┘     └────────┘     └────────┘
    │               │               │
    └───────────────┼───────────────┘
                    ↓ (Total: 2s, not 6s)
┌─────────────────────────────────────────┐
│ 3. Result Aggregation                   │
│ - Summary: "High complexity, refactor"  │
│ - tabs_to_show: ["Analysis", "Metrics"] │
│ - actions: ["Extract validation"]       │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ 4. Session Cache                        │
│ Store results for follow-up queries     │
└─────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 2A: Intent Detection (1-2 days)
- LLM-based query classification
- Fallback to keyword matching
- Confidence scores

### Phase 2B: Parallel Execution (2-3 days)
- Shared AST context
- `asyncio.gather()` for concurrent agents
- Per-agent timeout handling

### Phase 2C: Result Aggregation (2-3 days)
- Natural language summary generation
- Smart tab determination
- Action ranking and suggestions

### Phase 2D: Session Context (2-3 days)
- Session management with caching
- File change detection
- Follow-up conversation support

---

## Expected Improvements

| Metric | Phase 1 | Phase 2 | Improvement |
|--------|---------|---------|------------|
| Query Understanding | Keyword-based | LLM-based | Semantic |
| Execution Time (3 agents) | 6-7 seconds | 2-3 seconds | **3-4x faster** |
| AST Parses | 3 (wasteful) | 1 (shared) | **-2 parses** |
| Follow-up Queries | Full re-analysis | Cache hit | **50% faster** |
| False Negatives | ~30% of queries | <5% of queries | **Better coverage** |

---

## New Files to Create

```
kicli_code_assist/agent/
  intent_detector.py        (150 lines)
  executor.py               (200 lines)
  aggregator.py             (150 lines)
  session.py                (250 lines)
  
tests/
  test_intent_detector.py   (100 lines)
  test_executor.py          (150 lines)
  test_aggregator.py        (100 lines)
  test_session.py           (100 lines)

docs/
  AGENT_ROUTING_INTELLIGENCE_PLAN.md          ✅ DONE
  PHASE_2_TECHNICAL_SPEC.md                   ✅ DONE
  PHASE_2_IMPLEMENTATION_PRIORITY.md          ✅ DONE
  PHASE_2_EXECUTIVE_SUMMARY.md                ✅ DONE (this file)
```

---

## New API Endpoints

### Updated: POST /api/agent/route
```json
Request:
{
  "query": "Explain and optimize",
  "file_path": "src/app.py",
  "scope": "folder",
  "project": "/path",
  "session_id": "optional"
}

Response:
{
  "intent": {
    "intent_type": "explain",
    "agents_to_run": ["explain", "metrics", "refactor"],
    "confidence": 0.92,
    "reasoning": "Query contains 'explain' + 'optimize'"
  },
  "results": {
    "explain": {...},
    "metrics": {...},
    "refactor": {...}
  },
  "summary": "Module has high complexity. Consider extraction.",
  "tabs_to_show": ["Analysis", "Metrics"],
  "recommended_actions": [
    {"action": "Extract validation", "priority": "high"}
  ],
  "total_execution_time_ms": 2300,
  "session_id": "uuid-xxx"
}
```

### New: POST /api/session/create
```json
Request: { "project_path": "/path" }
Response: { "session_id": "uuid-xxx" }
```

### New: GET /api/session/{session_id}
```json
Response: {
  "session_id": "uuid-xxx",
  "created_at": "2026-10-27T...",
  "cached_analyses": 3,
  "current_file": "src/app.py"
}
```

---

## Key Design Decisions

### 1. LLM Provider
- **Option A**: OpenAI GPT-4 (recommended)
  - Pros: Best accuracy, proven for classification
  - Cons: API costs
  
- **Option B**: Claude 3.5
  - Pros: Good quality, structured output
  - Cons: Another API to manage

- **Option C**: Local Ollama (free)
  - Pros: No costs, runs locally
  - Cons: Lower accuracy than GPT-4
  
**Recommendation**: Start with GPT-4 (you have credits), add Ollama fallback

### 2. Caching Backend
- **Option A**: In-memory dict (simple, for MVP)
- **Option B**: SQLite (persistent across restarts)
- **Option C**: Redis (distributed, fast)

**Recommendation**: SQLite for Phase 2 (persistent, simple)

### 3. Async Framework
- Use Python's built-in `asyncio` + `asyncio.gather()`
- No additional dependencies needed
- Proven pattern in production

### 4. Backward Compatibility
- Keep Phase 1 response structure
- Add new fields (`summary`, `tabs_to_show`, etc)
- All Phase 1 clients continue to work

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| LLM API unavailable | Medium | High | Fallback to keyword matching |
| Async bugs causing crashes | Medium | High | Comprehensive testing, gradual rollout |
| AST sharing breaks agents | Low | Critical | Unit tests, verify each agent |
| Performance regression | Low | Medium | Benchmarking before/after each step |
| Cache invalidation bugs | Medium | Medium | Strong file hashing, manual refresh |

---

## Success Criteria

✅ LLM Intent Detection
- Correctly classify 90%+ of test queries
- Confidence scores help users understand routing
- Graceful fallback when LLM unavailable

✅ Parallel Execution
- >30% speed improvement measured
- No duplicate AST parses
- All agents get results correctly

✅ Result Aggregation
- Summary generated for 100% of analyses
- UI tabs match result types
- Recommended actions are actionable

✅ Session Context
- Cache prevents redundant analysis
- Follow-up queries faster (50%+ improvement)
- File changes properly invalidate cache

---

## Timeline

| Phase | Tasks | Duration | Cumulative |
|-------|-------|----------|-----------|
| 2A | Intent Detection + tests | 1-2 days | 1-2 days |
| 2B | AST sharing + Executor | 2-3 days | 3-5 days |
| 2C | Backend update + Aggregation | 2-3 days | 5-8 days |
| 2D | Session manager + integration | 2-3 days | 7-11 days |
| — | Testing + refinement | 2-3 days | 9-14 days |

**Total: 1-1.5 weeks** (depends on parallelization)

---

## Comparison to Competition

| Feature | Copilot (VS Code) | JetBrains AI | Kicli Phase 2 |
|---------|-------------------|--------------|---------------|
| Semantic intent | ✅ | ✅ | ✅ NEW |
| Parallel analysis | ✅ | ✅ | ✅ NEW |
| Session persistence | ✅ | ✅ | ✅ NEW |
| Code context awareness | ✅ | ✅ | ✅ EXISTING |
| Smart recommendations | ✅ | ✅ | ✅ NEW |

---

## Getting Started

### For Project Managers
1. Allocate 1-1.5 weeks
2. Ensure LLM API access (OpenAI)
3. Review success criteria

### For Developers
1. Read: `PHASE_2_TECHNICAL_SPEC.md` (detailed API)
2. Read: `PHASE_2_IMPLEMENTATION_PRIORITY.md` (execution order)
3. Start: Step 1 - `AgentIntentDetector`
4. Review: Test templates in priority guide

### For Code Reviewers
- Verify each step has >80% test coverage
- Check backward compatibility maintained
- Benchmark performance improvements
- Validate error handling for LLM failures

---

## Related Documents

- **Strategic Overview**: `AGENT_ROUTING_INTELLIGENCE_PLAN.md`
- **Technical Spec**: `PHASE_2_TECHNICAL_SPEC.md`
- **Implementation Order**: `PHASE_2_IMPLEMENTATION_PRIORITY.md`
- **Phase 1 Status**: `HYBRID_AGENT_IMPLEMENTATION_PLAN.md`

---

## Questions?

Key decisions before starting:
1. Which LLM provider? (GPT-4, Claude, Ollama)
2. Caching backend? (in-memory, SQLite, Redis)
3. Timeline flexibility? (1 week vs 1.5 weeks)
4. Deploy all 4 phases together or incrementally?

---

**Next Step**: Review with stakeholders, approve timeline, begin implementation

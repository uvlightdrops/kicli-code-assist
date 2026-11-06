---
title: Code Analysis Architecture & Integration
project: kicli-code-assist
scope: Development Guide
purpose: Comprehensive overview of code analysis pipeline from UI to backend
created: 2026-11-06T07:55:00+01:00
updated: 2026-11-06T07:55:00+01:00
status: active
---

# Code Analysis Architecture

## Overview

Code analysis in kicli-code-assist is a multi-layered pipeline:

```
User selects file in TUI
     ↓
TUI sends request to /api/agent/route
     ↓
MetaCoordinationAgent (intent detection)
     ↓
Route to specialized agents (Explain, Metrics, Dependencies, etc.)
     ↓
Streaming response via WebSocket
     ↓
TUI displays in Agent Tabs with chunked feedback
```

---

## Layer 1: TUI Integration (UI → Backend)

**Current Status:** Ready, but not fully wired to analysis yet

**Location:** `kicli_code_assist/ui/tui_client.py`, `kicli_code_assist/ui/widgets/agent_tabs.py`

**What happens:**
- User selects file in FileTree → `on_file_selected()` fires
- TUI has `BackendClient` that sends requests to `/api/agent/route`
- Response rendered in AgentTabPanel (Explain, Metrics, Dependencies tabs)

**Current Issue:** AgentTabPanel shows static data; needs to call `/api/agent/route` and stream results

**What we need to fix:**
- [ ] Wire file selection → backend request
- [ ] Parse chunked JSON responses (streaming)
- [ ] Update tabs in real-time as chunks arrive
- [ ] Show loading states during analysis

---

## Layer 2: Backend Orchestration

**Location:** `kicli_code_assist/web/server_routes.py` (lines 39-150)

**Endpoint:** `POST /api/agent/route`

**Flow:**
```
1. MetaCoordinationAgent receives query + file_path
2. Intent Detection: "explain code" → type = "explain"
3. Workflow Selection: type → agents to run
4. Agent Execution: Run Explain, Metrics, Dependencies in parallel
5. Aggregation: Combine results
6. Answer Generation: Format response
7. Stream back to UI
```

**Key Components:**
- `MetaCoordinationAgent` (kicli_code_assist/agent/meta_coordinator.py)
  - 6-stage orchestration pipeline
  - Intent → Workflow → Agents → Aggregation → Generation
  
- `CoordinationRequest` (meta_coordinator.py)
  - Input: query, file_path, project_root, scope
  - Output: answer, tabs, timing, agents_used

**Current Capabilities:**
- ✅ Intent detection (explain, suggest, refactor)
- ✅ Parallel agent execution
- ✅ Response aggregation
- ✅ Timing metrics per stage

---

## Layer 3: Analysis Engines

### 3.1 Project Analysis (Foundation)

**Location:** `kicli_code_assist/agent/analysis/`

**Modules:**
- `project_analyzer.py` - Detect project type, find entry points
- `ast_analyzer.py` - Parse Python syntax, extract functions/classes
- `dependency_resolver.py` - Track imports, build dependency graph
- `semantic_indexer.py` - In-memory search index
- `smart_selector.py` - Select code within token budget

**Status:** Phase 1 Complete (bare-bones, ~500 LOC)

**Capabilities:**
- Parse Python files → extract functions, classes, imports
- Detect frameworks (Flask, Django, FastAPI)
- Find dependencies (what imports this file?)
- Search functions by name/docstring
- Select code snippets within token budget

**Limitations (by design):**
- String-matching for dependencies (not perfect AST)
- In-memory indexing (not persistent)
- Simple greedy selection (no ranking)

### 3.2 Specialized Analyzers

**Explain Agent** - What does this code do?
- Location: `kicli_code_assist/agent/reasoning.py` or `/api/agent/explain`
- Input: file_path, selection (optional)
- Output: Summary, key functions, data flow

**Metrics Agent** - Code quality metrics
- Location: `kicli_code_assist/agent/metrics.py` or `/api/agent/metrics`
- Input: file_path
- Output: Complexity, maintainability, LOC, coverage

**Dependencies Agent** - What uses this?
- Location: `kicli_code_assist/agent/dependencies.py` or `/api/agent/dependencies`
- Input: file_path
- Output: Files that import this, impact analysis

**Refactoring Agent** - How to improve?
- Location: `kicli_code_assist/agent/refactoring.py` or `/api/agent/refactor`
- Input: file_path, metrics
- Output: Refactoring suggestions with code examples

---

## Layer 4: Response Streaming & Chunks

**Location:** `kicli_code_assist/web/server_routes.py` (agent_stream_reason)

**How it works:**
1. Backend collects results from multiple agents
2. Streams JSON chunks via WebSocket or HTTP streaming
3. Each chunk is a "feedback piece" (observation, issue, solution, impact)

**Chunk Format (Proposed):**
```json
{
  "type": "observation",
  "agent": "metrics",
  "content": "Cyclomatic complexity is 8 (high)",
  "severity": "medium",
  "context": {"lines": [42, 65], "metric": "complexity"}
}
```

**Current Status:** Streaming works for reasoning; needs generalization for all agents

---

## Layer 5: TUI Display

**Location:** `kicli_code_assist/ui/widgets/agent_tabs.py`

**Layout Schema:**
```
FileTree (1fr) │ Preview (2fr, tabs) │ Agent (2fr, tabs)
               │                     │
               │ File Content        │ Active Agent Tab:
               │                     │  ├─ Response/Chat (50%)
               │                     │  └─ Chunks (50%, streaming)
```

Each **Agent Tab** (Explain, Metrics, Refactor, Suggest) contains:
- **Top Half:** Agent's conversational response / analysis result
- **Bottom Half:** Real-time streaming chunks (thinking, observations, issues, solutions)

**Tabs:**
1. **Explain** - What this code does (reasoning + structure)
2. **Metrics** - Code quality analysis
3. **Dependencies** - Impact analysis (what uses this)
4. **Refactor** - Improvement suggestions
5. **Suggest** - General enhancements

**How to Display Chunks:**
- Stream arrives as JSON objects
- Parse agent + type (observation, issue, solution)
- Accumulate in tab content
- Render with appropriate styling (colors, icons)

**Example Rendering:**
```
📊 METRICS
━━━━━━━━━━━━━━━━━━
🔍 Observation: Cyclomatic complexity is 8 (high)
  Context: functions at lines 42-65

⚠️  Issue: High complexity reduces maintainability
  Confidence: 9/10

💡 Solution: Extract helper functions
  Example: def _validate_input() {...}

✅ Impact: Reduces complexity to 4, improves testability
```

---

## Blockers & Next Steps

### Current Blockers:
1. **TUI ↔ Backend Connection** - File selection doesn't trigger `/api/agent/route` yet
2. **Streaming Format** - Chunks not standardized across all agents
3. **Tab Rendering** - AgentTabPanel doesn't parse/display chunks
4. **Error Handling** - No graceful fallback if analysis fails

### To Unblock Code Analysis:

**Phase I1 (Minimal):**
- [ ] Wire FileTree selection → Backend request (10 min)
- [ ] Standardize chunk format across agents (30 min)
- [ ] Parse + render chunks in tabs (60 min)
- [ ] Test end-to-end (30 min)

**Phase I2 (Enhanced):**
- [ ] Real-time streaming (WebSocket)
- [ ] Caching results (avoid re-analysis)
- [ ] Error recovery (retry, fallback)

---

## Testing Strategy

**Unit Tests (Existing):**
```bash
pytest tests/test_agent_endpoints.py  # Endpoint tests
pytest tests/test_ai_agents_chat.py   # Agent logic
```

**Integration Test (NEW):**
1. Start server: `python -m kicli_code_assist.web.server`
2. Start TUI: `kicli-assist tui --project .`
3. Select file in FileTree
4. Observe tabs update with analysis
5. Check logs for timing/errors

**Manual Testing:**
```bash
# Direct API call
curl -X POST http://localhost:3000/api/agent/route \
  -H "Content-Type: application/json" \
  -d '{"query": "explain this code", "file_path": "src/main.py", "project_root": "."}'
```

---

## Checklist: Ready for Phase I1?

- [ ] **API Endpoints** - `/api/agent/route` and specialized agents working
  - Check: `curl -X POST http://localhost:3000/api/agent/route` returns 200
  
- [ ] **MetaCoordinationAgent** - Orchestrates intents → agents
  - Check: Response includes `intent`, `workflow`, `agents_used`, `tabs`
  
- [ ] **BackendClient in TUI** - Can send requests (WIP)
  - Check: `BackendClient(url).post("/agent/route", data)` works
  
- [ ] **Chunk Format** - Standardized across all agents
  - Check: All agent responses follow `{type, agent, content, severity, context}` format
  
- [ ] **AgentTabPanel** - Can render chunks
  - Check: Parsing JSON, displaying in tabs, colors/icons work
  
- [ ] **Error Handling** - Graceful failures
  - Check: Backend unreachable → shows message, not crash

**Status:** Endpoints & orchestration ready; TUI integration needs 2-3 hours work.

---

## References

- [Meta Coordinator Docs](../agent/meta_coordinator.py) - 6-stage pipeline
- [Project Analyzer Docs](../agent/analysis/PHASE_1_README.md) - AST, dependencies, metrics
- [Server Routes](../web/server_routes.py) - All endpoints (lines 39-1100)
- [Textual HowTo](./TEXTUAL_HOWTO.md) - UI patterns for streaming/tabs

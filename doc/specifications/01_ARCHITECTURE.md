---
title: System Architecture Overview
project: kicli-code-assist
scope: architecture
status: active
created: 2026-11-05T21:42+01:00
updated: 2026-11-05T21:42+01:00
update_reason: Refactor for TUI 2.0 (agentische intelligent IDE, nicht chat)
agent_project: kicli-code-assist
cross_references:
  - doc/architecture/FRONTEND_SPECIFICATION.md (abstract multi-frontend interface)
  - doc/architecture/TUI_INTELLIGENT_TERMINAL_IDE.md (TUI 2.0 vision & roadmap)
  - doc/architecture/TUI_TEXTUAL_ARCHITECTURE.md (Textual implementation details)
  - doc/architecture/AGENT_ORCHESTRATION_ARCHITECTURE.md (backend agent routing)
semantic_blocks:
  - id: executive-summary
    title: Executive Summary
  - id: architecture-diagram
    title: Architecture Diagram
  - id: core-concepts
    title: Core Concepts
  - id: data-flow-request-response
    title: Data Flow: Request → Response
  - id: backend-routes-summary
    title: Backend Routes Summary
  - id: configuration-deployment
    title: Configuration & Deployment
  - id: phase-roadmap
    title: Phase Roadmap
  - id: success-criteria
    title: Success Criteria
  - doc/architecture/TRANSPARENCY_MODULES_ARCHITECTURE.md (reasoning traces & observability)
---

# System Architecture Overview

## Executive Summary [executive-summary]

**KI Code Assist** is a **server-client system** for intelligent code analysis via terminal or web UI. The architecture separates concerns into three layers:

1. **Backend** (Flask/FastAPI) — Agent orchestration, LLM routing, transparency
2. **Frontend Specification** (abstract) — Multi-frontend interface contract
3. **Frontend Implementations** — TUI (Textual), WebUI (React), future (GTK, Web)

**Goal:** Ship agentische intelligent terminal IDE that leverages Phase 5.5.2 backend capabilities (reasoning traces, multi-agent orchestration, code understanding).

---

## Architecture Diagram [architecture-diagram]

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERACTION                        │
├──────────────────────────┬──────────────────────────────────┤
│  TUI 2.0 (Textual)       │  WebUI (React)                   │
│  Terminal IDE            │  Browser IDE                     │
│  Project Tree + Tabs     │  Split-pane + Chat              │
└──────────────────────────┴──────────────────────────────────┘
                           │
           ┌───────────────┴───────────────┐
           │                               │
     ┌─────▼──────────────┐        ┌──────▼──────────────┐
     │  HTTP Streaming    │        │  WebSocket Stream  │
     │  /api/agent/route  │        │  /agent/execution  │
     └─────┬──────────────┘        └──────┬──────────────┘
           │                              │
           └───────────────┬──────────────┘
                           │
     ┌─────────────────────▼──────────────────────┐
     │         Backend (Flask)                    │
     ├─────────────────────────────────────────────┤
     │  MetaCoordinationAgent (routing)           │
     │  + CodeImplementationAgent                 │
     │  + DependencyAnalyzer                      │
     │  + RefactoringAnalyzer                     │
     │  + CodeMetricsAnalyzer                     │
     │  + StreamingReasoningAgent                 │
     │                                             │
     │  ReasoningTracer (transparency)            │
     │  LLMCallTracker (observability)            │
     │  PerformanceMetrics (timing)               │
     └─────────────────────┬──────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
         ┌────▼────┐          ┌────────▼────┐
         │  ki-core │          │ OpenAI API  │
         │ (config) │          │ Ollama API  │
         └──────────┘          └─────────────┘
```

---

## Core Concepts [core-concepts]

### 1. Backend (Server Layer)

**Responsibility:** Orchestrate agents, process requests, stream responses

**Key Modules:**
- `MetaCoordinationAgent` — Routes requests to appropriate agent
- `CodeImplementationAgent` — Generates code via LLM
- `DependencyAnalyzer` — Finds circular deps, imports
- `RefactoringAnalyzer` — Detects 5 refactoring patterns
- `CodeMetricsAnalyzer` — Computes complexity, maintainability
- `StreamingReasoningAgent` — Streams reasoning steps

**Transparency Stack (Phase 5.5.2):**
- `ReasoningTracer` — Captures reasoning decisions
- `LLMCallTracker` — Logs all LLM API calls
- `PerformanceMetrics` — Measures execution time

**Configuration:** `ki.yaml` (local), `config/stages/` (deployment)

**Deployment:** `python -m stackctl start`

### 2. Frontend Specification (Interface Contract)

**Responsibility:** Define abstract interface that multiple frontends implement

**What It Specifies:**
- Layout & components (Project Tree, Tabs, Input, Status Bar)
- Backend routes required (`GET /api/project/scan`, `POST /api/agent/route`, etc.)
- Data flows (request → response → display)
- Event format (JSON-L streaming)
- Error handling (backend unavailable, timeout, LLM error)
- Keyboard shortcuts (common across all frontends)

**File:** `doc/architecture/FRONTEND_SPECIFICATION.md`

**Why Separate?** So that Textual TUI, React WebUI, and future GTK/Web frontends can all be built against this spec without backend changes.

### 3. Frontend Implementations

#### A. TUI 2.0 (Textual) — Terminal IDE for host-2

**Status:** Phase 1 (foundation) — starting now

**Key Features (by phase):**
- Phase 1: Project tree, tabbed output, input field, status bar
- Phase 2: Agent streaming, rich formatting (code blocks, diffs, metrics)
- Phase 3: Real-time reasoning events, keyboard macros
- Phase 4: Performance optimization for large projects
- Phase 5+: Session persistence, split panes, themes

**Architecture:** `doc/architecture/TUI_INTELLIGENT_TERMINAL_IDE.md`

**Implementation:** `doc/architecture/TUI_TEXTUAL_ARCHITECTURE.md`

#### B. WebUI (React) — Web IDE for host-1

**Status:** Deployed (Phase 1-3 complete)

**Features:**
- Split-pane editor + agent chat
- Real-time reasoning panel (WebSocket)
- Diff viewer, metrics dashboard
- Session history

**Code:** `web/frontend/` (React/TypeScript)

---

## Data Flow: Request → Response [data-flow-request-response]

### User Request (TUI Example)

```
1. User selects file: src/main.py
2. User types: "Analyze this for performance issues"
3. Presses Enter

4. TUI sends HTTP request:
   POST /api/agent/route
   {
     "project_path": "/home/user/project",
     "selected_file": "src/main.py",
     "user_request": "Analyze this for performance issues",
     "agent_modes": ["explain", "metrics", "suggest"]
   }

5. Backend:
   - MetaCoordinator routes to appropriate agents
   - CodeMetricsAnalyzer: complexity, maintainability
   - CodeImplementationAgent: analysis + suggestions
   - ReasoningTracer: captures reasoning steps
   - LLMCallTracker: logs LLM calls
   - PerformanceMetrics: measures time

6. Backend streams response (JSON-L):
   {"event_type": "explain", "content": "This function..."}
   {"event_type": "metrics", "complexity": 3}
   {"event_type": "suggest", "suggestions": [...]}
   {"event_type": "complete", "duration_ms": 2341}

7. TUI:
   - Renders each event to appropriate tab (Explain, Metrics, Suggest)
   - Updates status bar (elapsed time, cost)
   - User can switch tabs while processing

8. User interacts:
   - Presses Ctrl+1 → Jump to Explain tab
   - Presses Ctrl+2 → Jump to Metrics tab
   - Presses Up/Down → Previous requests from history
   - Presses Ctrl+C → Cancel running request
```

---

## Backend Routes Summary [backend-routes-summary]

See `doc/architecture/FRONTEND_SPECIFICATION.md` for full contract.

**Key Routes:**

```
Project Operations:
  GET /api/project/scan       → List files in project
  GET /api/project/file       → Get file contents

Agent Operations (Streaming):
  POST /api/agent/route       → Main entry point (all agents)
  POST /api/agent/explain     → Explain code
  POST /api/agent/suggest     → Generate suggestions
  POST /api/agent/reason      → Stream reasoning
  POST /api/agent/metrics     → Compute metrics
  POST /api/agent/refactor    → Refactoring ideas
  POST /api/agent/dependencies → Dependency analysis

WebSocket (Real-time):
  WS /socket.io/agent/execution
    Events: reasoning_step, llm_call, performance_metric

Historical Queries:
  GET /api/traces/{trace_id}  → Full trace object
  GET /api/logs/tail          → Recent logs
```

---

## Configuration & Deployment [configuration-deployment]

### Local Development

```bash
# Terminal 1: Start backend
cd /home/flow/dev_flow/kicli-code-assist
python -m stackctl start

# Terminal 2: Start TUI
kicli-assist tui --project /path/to/project

# Terminal 3: Check logs
tail -f log/kicli.log
```

### Environment Variables

```bash
KI_STAGE=development          # Local config loading
OPENAI_API_KEY=sk-...        # LLM provider
KI_OLLAMA_URL=http://...     # Ollama endpoint (if using)
```

### Configuration Files

- **Local:** `ki.yaml` (project root)
- **Staging:** `config/stages/staging.yaml`
- **Production:** `config/stages/production.yaml`

---

## Phase Roadmap [phase-roadmap]

### Phase 1: Foundation (This Week - Nov 5-8)
- [x] Documentation: FRONTEND_SPECIFICATION + TUI_INTELLIGENT_TERMINAL_IDE
- [ ] TUI scaffold: Project Tree + Tabs + Input + Status Bar
- [ ] Backend connectivity: Health check + basic request/response
- [ ] Keyboard shortcuts: Basic navigation + tab switching

**Goal:** TUI renders, can submit requests, displays responses

### Phase 2: Agent Integration (Week 1)
- Streaming all agent modes (Explain, Suggest, Metrics, Reason, Refactor, Deps)
- Rich formatting (code blocks, diffs, metrics visualization)
- Input history + completion
- Error recovery (timeout, backend unavailable)

**Goal:** Full agent capabilities visible in TUI

### Phase 3: Intelligence Features (Week 2)
- Real-time reasoning events (WebSocket)
- Advanced keyboard shortcuts (macros)
- Search + filtering
- Session context tracking

**Goal:** TUI becomes powerful IDE tool

### Phase 4: Performance (Week 3)
- Large project optimization (lazy-load trees)
- Caching + session state
- Memory optimization

### Phase 5+: Extended Features (Future)
- Session persistence
- Split panes / themes
- Offline mode
- Multi-file editing

---

## Related Documentation

**Start Here:**
- `doc/architecture/FRONTEND_SPECIFICATION.md` — Interface contract
- `doc/architecture/TUI_INTELLIGENT_TERMINAL_IDE.md` — TUI vision & phases

**Deep Dives:**
- `doc/architecture/AGENT_ORCHESTRATION_ARCHITECTURE.md` — Backend routing
- `doc/architecture/TRANSPARENCY_MODULES_ARCHITECTURE.md` — Observability
- `doc/architecture/TUI_TEXTUAL_ARCHITECTURE.md` — Textual specifics

**Reference:**
- `doc/architecture/WEBSOCKET_STREAMING_ARCHITECTURE.md` — Real-time events
- `doc/architecture/ASYNC_LLM_SECURITY_ARCHITECTURE.md` — Security considerations

**Deprecated (Archive):**
- `doc/archive/tui_attempt_oct2026/02_TUI_SPECIFICATION_LEGACY.md` — Old chat-based design

---

## Success Criteria [success-criteria]

**By End of Phase 1:**
- TUI compiles and runs without errors
- Can connect to backend (`/api/project/scan` works)
- Can submit request and receive response
- File tree navigation works (Up/Down/Enter)
- Tab switching works (Ctrl+1-6)
- Status bar shows connection + timing
- Keyboard shortcuts functional

**By End of Phase 2:**
- All 6 agent modes stream correctly
- Rich formatting visible (code blocks, metrics)
- Input history works
- Error handling graceful

**By End of Phase 3:**
- Real-time reasoning visible
- Advanced keyboard features working
- TUI is genuinely useful IDE tool

---

**Status:** Foundation complete  
**Next Step:** Phase 1 implementation (TUI scaffold)
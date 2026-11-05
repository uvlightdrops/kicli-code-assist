---
project: kicli-code-assist
scope: guides
created: 2026-11-05 16
updated: 2026-11-05 16
update_reason: Initial TUI client design for K8s jump host environments
status: in_progress
agent_project: kicli-code-assist
---

# TUI Client Implementation Plan

## Objective
Build a Terminal User Interface (TUI) client using Textual that provides **identical functionality** to the WebUI, enabling agent-driven code analysis and implementation on jump hosts without GUI access.

## Architecture: Analog to WebUI

### API Surface (Shared with WebUI)
All endpoints remain **identical** — TUI is a different frontend to the same backend:

| Endpoint | Purpose | TUI Widget |
|----------|---------|-----------|
| `/api/agent/route` | Main agent orchestration | UnifiedAgentPanel |
| `/api/agent/explain` | Code explanation | ExplainPanel |
| `/api/agent/suggest` | Code suggestions | SuggestPanel |
| `/api/agent/reason` | Reasoning trace | ReasoningPanel |
| `/api/agent/ensemble` | Multi-agent synthesis | EnsemblePanel |
| `/api/agent/dependencies` | Dependency analysis | DependencyPanel |
| `/api/agent/refactor` | Refactoring suggestions | RefactorPanel |
| `/api/agent/metrics` | Code metrics | MetricsPanel |
| `/api/traces/*` | Historical queries | TraceHistoryPanel |
| WebSocket: `/socket.io/` | Event streaming | Real-time updates |

### TUI Layout Strategy

```
┌─────────────────────────────────────────────────────────┐
│ Code Assistant TUI  (q=quit, h=help)                    │
├─────────────────────┬───────────────────────────────────┤
│ Project Files (F1)  │ Agent Reasoning / Output (F2-F6)  │
│                     │                                   │
│ ┌─────────────────┐ │ ┌─────────────────────────────┐   │
│ │ src/            │ │ │ Explain / Suggest / Reason  │   │
│ │ ├─ main.py ◄───╬─┤ │ metrics: 2.3s, $0.04        │   │
│ │ ├─ utils.py     │ │ │                             │   │
│ │ └─ lib/         │ │ │ [Real-time trace stream]    │   │
│ │                 │ │ │                             │   │
│ └─────────────────┘ │ └─────────────────────────────┘   │
├─────────────────────┼───────────────────────────────────┤
│ Input (F7: New Request)                                 │
│ > analyze src/main.py for performance issues           │
│ [Sending... ▓▓▓▓▓░░░░]                                  │
└─────────────────────────────────────────────────────────┘
```

## Implementation Phases (87 min budget)

### Phase 1: Core Scaffolding (25 min)
- [ ] `tui_client.py`: Main TUI app class extending `textual.app.App`
- [ ] `tui_agent_client.py`: HTTP + WebSocket client wrapper
- [ ] `tui_config.py`: TUI-specific config (colors, layout, API base URL)
- **Tests**: `test_tui_client_structure.py` (3 tests)

### Phase 2: Core Widgets (35 min)
- [ ] `widgets/project_explorer.py`: File tree panel
- [ ] `widgets/agent_output_panel.py`: Result display (unified for all agent modes)
- [ ] `widgets/input_panel.py`: Request input + submit
- [ ] `widgets/status_bar.py`: Real-time metrics (time, cost, tokens)
- [ ] `widgets/trace_viewer.py`: Streaming reasoning trace
- **Tests**: `test_tui_widgets.py` (8 tests)

### Phase 3: Agent Integration (20 min)
- [ ] Connect TUI to `/api/agent/route` endpoint
- [ ] WebSocket event streaming (ReasoningTracer events)
- [ ] Display formatting: Diffs, code blocks, tables (via Rich)
- [ ] Error handling + loading states
- **Tests**: `test_tui_agent_integration.py` (5 tests)

### Phase 4: CLI Entry & Polish (7 min)
- [ ] `cli.py` update: Add `tui` command
- [ ] Test startup: `python -m kicli_code_assist.ui.textual_app`
- [ ] Documentation + quick-start

## Technical Details

### Client Architecture
```python
# tui_agent_client.py
class TUIAgentClient:
    """Adapter layer: TUI → Backend API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.session = httpx.AsyncClient(base_url=base_url)
        self.ws = None  # WebSocket connection
        
    async def call_agent(self, mode: str, context: dict) -> AsyncGenerator:
        """Stream agent response (Explain/Suggest/Reason/etc)"""
        # POST /api/agent/route with mode + files
        # Connect WebSocket for trace events
        # Yield: (event_type, data) tuples
```

### Key Widget: Agent Output Panel
```python
# widgets/agent_output_panel.py
class AgentOutputPanel(Static):
    """Unified display for all agent modes"""
    
    def render_explain(self, data: ExplainResult):
        # Rich.Console for formatted output
        
    def render_refactor(self, data: RefactorResult):
        # Syntax-highlighted diffs
        
    def render_reasoning(self, data: ReasoningEvent):
        # Real-time trace stream
```

## Success Criteria
- ✅ TUI starts on `python -m kicli_code_assist.ui.textual_app`
- ✅ Can select file from project tree
- ✅ Can submit agent request (Explain mode)
- ✅ Sees streaming reasoning trace in real-time
- ✅ Displays results with proper formatting
- ✅ All 16 tests pass

## Files to Create/Modify

### New Files
```
kicli_code_assist/ui/
├── tui_client.py              (main app)
├── tui_agent_client.py        (API wrapper)
├── tui_config.py              (config)
├── widgets/
│   ├── project_explorer.py
│   ├── agent_output_panel.py
│   ├── input_panel.py
│   ├── status_bar.py
│   └── trace_viewer.py
└── tests/
    ├── test_tui_client_structure.py
    ├── test_tui_widgets.py
    └── test_tui_agent_integration.py
```

### Modified Files
```
kicli_code_assist/cli.py        (add 'tui' command)
doc/guides/README.md            (update with TUI reference)
```

## Assumptions
- Backend API running on `localhost:8000` (configurable)
- httpx + aiohttp available (install if needed)
- Terminal supports 256-color + mouse (Textual requirement)
- Textual 8.2.8+ installed

## Dependencies Check
- textual ✅ (already in pyproject.toml)
- httpx, aiohttp → need to verify in pyproject.toml
- rich ✅ (included with textual)

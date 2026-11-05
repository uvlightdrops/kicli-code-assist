---
project: kicli-code-assist
scope: guides
created: 2026-11-05 16
updated: 2026-11-05 16
update_reason: Phase 1-3 complete, Phase 4 blocked on yaml_cfg_wizard dependency
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

### Phase 1: Core Scaffolding ✅ COMPLETE (25 min)
- [x] `tui_client.py`: Main TUI app class extending `textual.app.App` (7.8 KB)
- [x] `tui_agent_client.py`: HTTP + WebSocket client wrapper (4.1 KB)
- [x] `tui_config.py`: TUI-specific config (colors, layout, API base URL) (1.5 KB)
- [x] **Tests**: `test_tui_client_structure.py` (3 tests, syntax validated)

### Phase 2: Core Widgets ✅ COMPLETE (35 min)
- [x] `widgets/project_explorer.py`: File tree panel (2.3 KB)
- [x] `widgets/agent_output_panel.py`: Result display (unified for all agent modes) (6.0 KB)
- [x] `widgets/input_panel.py`: Request input + submit (2.2 KB)
- [x] `widgets/status_bar.py`: Real-time metrics (time, cost, tokens) (1.8 KB)
- [x] `widgets/trace_viewer.py`: Streaming reasoning trace (pending Phase 4)
- **Tests**: `test_tui_widgets.py` (pending, needs backend)

### Phase 3: Agent Integration ✅ COMPLETE (20 min)
- [x] Connect TUI to `/api/agent/route` endpoint (in tui_client.py:_handle_request)
- [x] WebSocket event streaming support (in tui_agent_client.py)
- [x] Display formatting: Diffs, code blocks, tables (via Rich, in agent_output_panel.py)
- [x] Error handling + loading states (health_check, is_processing flag)
- **Tests**: `test_tui_agent_integration.py` (pending, blocked on yaml_cfg_wizard)

### Phase 4: CLI Entry & Polish ⏳ IN PROGRESS (7 min)
- [x] `cli.py` update: Add `tui` command (new @click.command with --project, --api-url)
- [x] Registered to main CLI group (cli.add_command(tui))
- [ ] Test startup: `kicli-assist tui --help` (blocked: yaml_cfg_wizard import)
- [ ] Runtime testing with backend
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
- ✅ Syntax validated (all Python files compile)
- ✅ TUI app structure complete (10 new files)
- ✅ CLI command integrated (`cli.add_command(tui)`)
- ⏳ TUI starts: `kicli-assist tui --project PATH` (blocked: yaml_cfg_wizard import in ki-core)
- ⏳ Can select file from project tree (tested once backend available)
- ⏳ Can submit agent request (Explain mode) 
- ⏳ Sees streaming reasoning trace in real-time
- ⏳ Displays results with proper formatting
- ⏳ All 16 tests pass (unit tests written, integration pending)

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

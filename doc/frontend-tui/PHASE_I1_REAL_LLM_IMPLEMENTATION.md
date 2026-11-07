---
title: "Phase I1: Real LLM Integration Implementation"
project: kicli-code-assist
scope: frontend-tui
type: implementation
status: in_progress
created: 2026-11-06T10:28:00+01:00
updated: 2026-11-06T10:45:00+01:00
update_reason: Document Phase I1 real LLM backend integration for TUI
cross_references:
  - ../../doc/backend/layer-2-workflow-orchestration/AGENT_ROUTE_SPEC.md
  - ../../doc/backend/README.md
  - ./TUI_TEXTUAL_ARCHITECTURE.md
---

# Phase I1: Real LLM Integration Implementation

Status: **In Progress** — HTTP client complete, integration wired, ready to test

## What Changed

### New Components

#### 1. **TUI HTTP Client** (`kicli_code_assist/ui/http_client.py`)

Handles all TUI-to-backend communication.

**Class: `TUIBackendClient`**
- Constructor: Takes `base_url` (default: `http://localhost:3000`)
- Main method: `analyze_file(query, file_path, project_root, scope)`
- Returns: `AnalysisResponse` with `(success, answer, chunks, intent, agents_used, error)`

**Response Parsing**
- Converts backend response JSON into UI-ready format
- Extracts chunks from tabs (each tab can have `chunks` array)
- Falls back to tab summaries if no chunks found
- Error responses return `AnalysisResponse(success=False, error=message)`

**Error Handling**
- Connection error (backend unreachable)
- HTTP error (400, 403, 500)
- Timeout (32 seconds per AGENT_ROUTE_SPEC)
- JSON parse error

#### 2. **Test Script** (`scripts/test_phase_i1_integration.py`)

End-to-end integration test.

**Tests**
1. Backend health (`GET /api/health`)
2. File analysis (`POST /api/agent/route`)
3. Response parsing validation
4. Pretty-print results

**Usage**
```bash
cd kicli-code-assist
python3 scripts/test_phase_i1_integration.py
```

### Updated Components

#### 1. **Agent Tabs Widget** (`kicli_code_assist/ui/widgets/agent_tabs.py`)

Replaced mock data with real LLM integration.

**Key Changes**
- Added `http_client` import
- Constructor now takes: `file_path`, `project_root`, `backend_url`
- New method: `set_file_context(file_path, project_root)` — update file before analyze
- New method: `_perform_analysis()` — async worker that calls backend
- New method: `_build_query(agent_type)` — context-aware queries

**Query Generation**
Per agent type:
- `explain`: "Analyze and explain {file}. What does it do?"
- `metrics`: "Show code quality metrics for {file}..."
- `refactor`: "What refactoring opportunities exist..."
- `dependencies`: "Show dependencies and imports..."
- `suggest`: "Suggest improvements..."
- `reason`: "Provide detailed reasoning..."

**Error Display**
- Backend errors shown in active tab
- User-friendly messages (not raw HTTP errors)
- Chunks display includes error type/message

**Async Handling**
- Uses Textual `@work` decorator for background processing
- Prevents UI blocking during LLM request
- Status: `is_analyzing` flag prevents double-click

## Architecture: TUI → Backend Flow

```
TUI File Selection
  ↓
User clicks "Analyze" button
  ↓
AgentTabPanel.on_button_pressed()
  ↓
AgentTabPanel.action_analyze()
  ↓
AgentTabPanel._perform_analysis() [@work async]
  ├─ Get active tab (Explain, Metrics, etc)
  ├─ Build query: _build_query(agent_type)
  ├─ HTTP request: client.analyze_file(...)
  │  ├─ POST /api/agent/route
  │  ├─ Payload: {query, file_path, project_root, scope}
  │  └─ Response: {success, answer, tabs, intent, agents_used}
  ├─ Parse response: _parse_response(data)
  │  └─ Convert tabs/chunks to UI format
  └─ Update UI: tab_content.set_response() + set_chunks()
  ↓
User sees: Real agent analysis + chunks in split panels
```

## API Contract

**Endpoint**: `POST /api/agent/route` (Backend Layer 2)

**Request**
```json
{
  "query": "Analyze this file and show metrics",
  "file_path": "/absolute/path/to/file.py",
  "project_root": "/absolute/path/to/project",
  "scope": "file"
}
```

**Response (Success)**
```json
{
  "success": true,
  "session_id": "uuid-here",
  "query": "...",
  "answer": "Detailed conversational response...",
  "intent": {"type": "explain", "confidence": 0.92},
  "workflow": "analysis",
  "agents_used": ["explain", "metrics"],
  "tabs": {
    "Explain": {
      "summary": "...",
      "chunks": [
        {"type": "observation", "content": "..."},
        {"type": "issue", "content": "..."}
      ]
    }
  },
  "actions": [],
  "timing": {"intent_ms": 100, "execution_ms": 1500, ...}
}
```

**Response (Error)**
```json
{
  "success": false,
  "error": "File not found: ...",
  "session_id": "uuid-here"
}
```

See: [AGENT_ROUTE_SPEC.md](../../doc/backend/layer-2-workflow-orchestration/AGENT_ROUTE_SPEC.md)

## Testing

### Prerequisites
```bash
# Start backend
cd /home/flow/dev_flow/kicli-code-assist
KI_STAGE=development python -m stackenv start

# In another terminal
cd kicli-code-assist
```

### Quick Test
```bash
python3 scripts/test_phase_i1_integration.py
```

Expected output:
```
[1/2] Testing Backend Health...
✓ Backend healthy: {'status': 'ok', 'service': 'kicli-web'}

[2/2] Testing File Analysis...
Response success: True
Intent: explain
Agents used: ['metrics', 'refactoring']
Answer length: 2850 chars
Chunks: 5

=== Analysis Response ===
This Python file implements a..."
```

### TUI Integration Test (Manual)
```bash
# 1. Start TUI
python3 -m kicli_code_assist.ui.tui_client

# 2. Open a Python file from the file tree
# 3. Select file (e.g., src/main.py)
# 4. Navigate to "Analyze" tab
# 5. Press "Analyze" button
# 6. Watch panels populate with real LLM response
```

## Known Limitations & Gaps

| Item | Status | Notes |
|------|--------|-------|
| HTTP client | ✅ Complete | urllib (no external deps) |
| Backend integration | ✅ Complete | Calls real `/api/agent/route` |
| Error handling | ✅ Complete | Connection, validation, timeout |
| Async UI updates | ✅ Complete | Uses Textual @work |
| Streaming responses | ⚠️ Partial | Currently waits for full response; streaming chunks TODO |
| File selection binding | 🔴 Missing | TUI needs to pass selected file to AgentTabPanel |
| Query optimization | 🔴 Missing | Context could include file type, size, imports |
| Caching | 🔴 Missing | Same query = repeated requests (Layer 2 does cache) |
| Large response handling | ⚠️ Partial | May need truncation/pagination for 10KB+ responses |

## Next Steps (Priority Order)

1. **Wire file selection → AgentTabPanel** (TUI Integration)
   - When user selects file in FileTree, update AgentTabPanel context
   - Could be done in `tui_client.py` or FileTree widget

2. **Test end-to-end TUI flow**
   - Start backend, TUI, select file, click Analyze
   - Verify response appears in right panels

3. **Implement response streaming** (UX Polish)
   - Show chunks as they arrive (not wait for full response)
   - Use chunked transfer encoding or WebSocket

4. **Add loading indicator** (UX Polish)
   - Show "🔄 Analyzing..." while request in progress
   - Disable button during analysis (prevent double-click)

5. **Handle large responses** (Robustness)
   - Truncate responses > 10KB with "..." + scroll indicator
   - Show preview + expandable sections

6. **Add cache layer** (Performance)
   - Cache file content + analysis results
   - Reuse if query/file unchanged

## Code Structure

```
kicli_code_assist/ui/
├── http_client.py              [NEW] TUI ↔ Backend communication
├── widgets/
│  └── agent_tabs.py            [UPDATED] Real LLM integration
└── tui_client.py               [TODO] Wire file selection to AgentTabPanel

doc/frontend-tui/
└── PHASE_I1_REAL_LLM_IMPL.md   [THIS FILE]

scripts/
└── test_phase_i1_integration.py [NEW] Integration test
```

## Files Changed (Commit b20980e)

- ✅ Created: `kicli_code_assist/ui/http_client.py` (210 lines, TUIBackendClient)
- ✅ Created: `scripts/test_phase_i1_integration.py` (198 lines, integration test)
- ✅ Updated: `kicli_code_assist/ui/widgets/agent_tabs.py` (+180 lines, async analysis)

## Performance Characteristics

**Latency** (from AGENT_ROUTE_SPEC)
- First request: 2-5 seconds (model load, analysis)
- Subsequent: 1-3 seconds (caching)
- Timeout: 32 seconds

**Network**
- Request: ~1KB JSON
- Response: 2-10KB (answer + chunks + metadata)
- Timeout: 32s (Textual async safe)

**UI Responsiveness**
- Analyze button press: Immediate (async worker launched)
- Response display: Updates when response received (~2-5s)
- No UI blocking

## Debugging

**Enable debug logging**
```python
import logging
logging.getLogger("kicli_code_assist.ui.http_client").setLevel(logging.DEBUG)
logging.getLogger("kicli_code_assist.ui.widgets.agent_tabs").setLevel(logging.DEBUG)
```

**Check backend logs**
```bash
tail -f /home/flow/dev_flow/kicli-code-assist/log/kicli.log
```

**Test client directly**
```python
from kicli_code_assist.ui.http_client import TUIBackendClient
client = TUIBackendClient("http://localhost:3000")
response = client.analyze_file(
    query="Test analysis",
    file_path="/path/to/file.py",
    project_root="/path/to/project"
)
print(response)
```

## Integration Checkpoint

**Date**: 2026-11-06 10:45  
**Branch**: devel  
**Commit**: b20980e  

**Status Summary**
- ✅ HTTP client complete and tested
- ✅ Agent tabs wired to real backend
- ✅ Async integration ready
- ⚠️ File selection binding TODO
- ⚠️ Streaming responses TODO

**Ready for**: Manual TUI testing with file selection wired
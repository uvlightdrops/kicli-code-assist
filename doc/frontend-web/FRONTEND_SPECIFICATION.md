---
title: Frontend Specification - Abstract Interface Design
scope: architecture
project: kicli-code-assist
status: active
created: 2026-11-05T21:23+01:00
updated: 2026-11-05T21:23+01:00
update_reason: Initial abstract specification for multi-frontend architecture
agent_project: kicli-code-assist
cross_references:
  - doc/architecture/TUI_INTELLIGENT_TERMINAL_IDE.md (TUI implementation)
  - doc/features/UI_TABS.md (Tab system reference)
semantic_blocks:
  - id: core-principles
    title: Core Principles
  - id: layout-components
    title: Layout & Components
  - id: data-flow-user-request
    title: Data Flow: User Request
  - id: backend-routes-required
    title: Backend Routes Required
  - id: component-states-transitions
    title: Component States & Transitions
  - id: input-handling
    title: Input Handling
  - id: visual-formatting
    title: Visual Formatting
  - id: error-handling
    title: Error Handling
  - id: keyboard-shortcuts-frontend-agnostic
    title: Keyboard Shortcuts (Frontend-Agnostic)
  - id: frontend-implementation-checklist
    title: Frontend Implementation Checklist
  - doc/phases/archive/PHASE5_UI_INTEGRATION.md (Earlier UI thinking)
---

# Frontend Specification

**Purpose:** Define a frontend interface that can be implemented in multiple technologies (Textual TUI, GTK, Web, etc.) without changing the backend.

## Core Principles [core-principles]

1. **Backend Agnostic**: All layout/component decisions map to backend API calls
2. **Stateless UI**: No UI-side logic beyond formatting and interaction
3. **Streaming Ready**: Support async/streaming responses from backend
4. **Multi-Frontend**: Mockup + routing can be implemented in Textual, GTK, Next.js, etc.

---

## Layout & Components [layout-components]

### Screen Structure (Abstract)

```
┌─────────────────────────────────────────────────────────────┐
│ 🤖 KI Code Assistant  v1.0              Mode: [Active]      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ ┌──────────────────┐  ┌────────────────────────────────────┐ │
│ │ 📁 Project Tree  │  │ 📊 Main Panel (Tabbed)             │ │
│ │                  │  │ ╔════════════════════════════════╗ │ │
│ │ • src/           │  │ ║ [Explain] [Suggest] [Reason]   ║ │ │
│ │ • tests/         │  │ ║ [Metrics] [Refactor] [Deps]    ║ │ │
│ │ • config.yaml    │  │ ╠════════════════════════════════╣ │ │
│ │ • README.md      │  │ ║                                ║ │ │
│ │                  │  │ ║ [Agent Response Output]        ║ │ │
│ │ Logs | Chat      │  │ ║ (Rich formatted, scrollable)   ║ │ │
│ │ ─────────────    │  │ ║                                ║ │ │
│ │ [Log stream]     │  │ ║ 🔄 Processing... (4.2s)        ║ │ │
│ │ [Info/Warn/Err]  │  │ ╚════════════════════════════════╝ │ │
│ └──────────────────┘  └────────────────────────────────────┘ │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│ Input: [Analyze this function for performance issues]      │ │
├─────────────────────────────────────────────────────────────┤
│ Status: ✅ Ready | Backend: http://localhost:8000 | Time: 2s│
└─────────────────────────────────────────────────────────────┘
```

### Components

| Component | Type | Purpose | Backend Interaction |
|-----------|------|---------|---------------------|
| **Project Tree** | Sidebar | Navigate project files | `GET /api/project/scan` |
| **Main Panel** | Tabbed Container | Agent response display | Varies per tab |
| **Tab: Explain** | Panel | Code explanation | `POST /api/agent/explain` |
| **Tab: Suggest** | Panel | Improvement suggestions | `POST /api/agent/suggest` |
| **Tab: Reason** | Panel | Reasoning trace (streaming) | `WS /socket.io + /api/traces` |
| **Tab: Metrics** | Panel | Code metrics & quality | `POST /api/agent/metrics` |
| **Tab: Refactor** | Panel | Refactoring recommendations | `POST /api/agent/refactor` |
| **Tab: Dependencies** | Panel | Dependency analysis | `POST /api/agent/dependencies` |
| **Logs Panel** | Sidebar Tab | Real-time logs | `GET /api/logs/tail?lines=100` |
| **Chat Panel** | Sidebar Tab | Chat history | `GET /api/chat/history` |
| **Input Field** | Bottom Bar | User request submission | `POST /api/agent/route` |
| **Status Bar** | Bottom | Connection + metrics | Real-time updates via WS |

---

## Data Flow: User Request [data-flow-user-request]

```
1. User selects file in Project Tree
   └─→ [Frontend] Highlight file
   └─→ [Backend] GET /api/project/file?path=...
       └─ Returns: File content, metadata

2. User types request in Input Field
   └─→ [Frontend] Display request in chat/log

3. User presses Enter/Submit
   └─→ [Frontend] Set processing=true, show spinner
   └─→ [Backend] POST /api/agent/route
       {
         "project_path": ".",
         "selected_file": "src/main.py",
         "user_request": "Analyze this function for performance issues",
         "agent_modes": ["explain", "metrics", "suggest"]
       }

4. Backend streams response (JSON-L format)
   └─ For each event:
   
   {"event_type": "explain", "content": "This function..."}
   {"event_type": "metrics", "complexity": 3, "maintainability_index": 75}
   {"event_type": "suggest", "suggestions": [...]}


5. Frontend renders each event to appropriate Tab
   - [Explain Tab] Renders explanation text
   - [Metrics Tab] Renders metric values
   - [Suggest Tab] Renders suggestions with diffs

6. Status Bar updates with timing + cost
   - "✅ Complete | Time: 2.3s | Cost: $0.04 | Tokens: 234"

```

---

## Backend Routes Required [backend-routes-required]

### Project Operations

```
GET /api/project/scan
  Query: path=., depth=3
  Returns: {files: [...], count: 42, languages: [...]}

GET /api/project/file
  Query: path=src/main.py
  Returns: {path, content, size, language, lines}
```

### Agent Operations

```
POST /api/agent/route
  Body: {project_path, selected_file, user_request, agent_modes=[]}
  Returns: Streaming JSON-L
    {"event_type": "explain", "content": "..."}
    {"event_type": "metrics", "complexity": 3}
    ...

POST /api/agent/explain
POST /api/agent/suggest
POST /api/agent/reason
POST /api/agent/metrics
POST /api/agent/refactor
POST /api/agent/dependencies
  All accept: {project_path, selected_file, user_request}
  All return: Streaming JSON-L event objects

WebSocket /socket.io
  Namespace: /agent/execution
  Subscribe to: reasoning_step_started, reasoning_step_complete, 
               llm_call_started, llm_call_complete, performance_metric
```

### Logging & Tracing

```
GET /api/logs/tail
  Query: lines=100, level=INFO
  Returns: [{timestamp, level, message}, ...]

GET /api/traces/{trace_id}
  Returns: Full trace object with reasoning steps, LLM calls, metrics

WebSocket /socket.io
  Namespace: /logs
  Subscribe to: log_entry events in real-time
```

---

## Component States & Transitions [component-states-transitions]

### Processing State

```
┌─────────────┐
│   Ready     │ (waiting for input)
└──────┬──────┘
       │ (user submits request)
       ↓
┌─────────────────────────┐
│  Processing             │ (spinner animating)
│  "⏳ Analyzing..." (2.1s)│
└──────┬──────────────────┘
       │ (events stream in)
       ↓
┌─────────────────────────┐
│  Displaying Results     │ (tabs populating)
│  [Explain] [Metrics]    │
└──────┬──────────────────┘
       │ (all events received)
       ↓
┌──────────────────────────┐
│  Ready (Complete)        │
│  "✅ Complete (2.3s)"    │
└──────────────────────────┘
```

### Tab Selection State

**At any time:**
- Only one Tab active (highlighted)
- User can switch tabs while processing
- Backend continues streaming all events
- Inactive tabs buffer their content, show on switch

---

## Input Handling [input-handling]

### Input Field Behavior

**State:**
- Focused: Shows cursor, accepts typing
- Unfocused: Grayed out, shows last request
- Processing: Disabled, shows spinner

**Submission:**
- User types request
- Presses Enter (or Ctrl+Enter for multi-line)
- Input field clears
- Request echoed to Logs/Chat panel
- Processing begins

**History:**
- Up/Down arrows cycle through history
- Each request stored with timestamp
- Optional: Search history (Ctrl+F)

---

## Visual Formatting [visual-formatting]

### Code Blocks

**In Explain/Suggest Tabs:**
```
[cyan]Code:[/]
[code_block]
def process_data(items):
    return [item * 2 for item in items]
[/code_block]
```

### Metrics Display

**In Metrics Tab:**
```
Complexity:        ████░░░░ 4/10
Maintainability:   ██████░░ 7/10
Test Coverage:     ██░░░░░░ 2/10

Lines of Code:     42
Cyclomatic:        3
```

### Reasoning Trace

**In Reason Tab (streaming):**
```
🤔 Thinking...

[1] Analyzing AST
    └─ Found function: process_data
    └─ Found 3 variables
    └─ Found 1 loop

[2] Checking complexity
    └─ Cyclomatic: 1 + 1 (loop) = 2
    └─ Depth: 1 level
    └─ Result: Simple ✅

[3] Suggestions
    └─ Could add type hints
    └─ Could add docstring
```

### Diff/Suggestion Display

**In Suggest Tab:**
```
[green]+ def process_data(items: List[int]) -> List[int]:[/]
[red]- def process_data(items):[/]

  """Process items by doubling each value."""
  return [item * 2 for item in items]
```

---

## Error Handling [error-handling]

### Backend Unavailable

```
┌─────────────────────────────────────────────┐
│ ❌ Backend unreachable                      │
├─────────────────────────────────────────────┤
│ http://localhost:8000                       │
│                                             │
│ Make sure backend is running:               │
│   python -m stackctl start                  │
│                                             │
│ [Retry] [Configure]                         │
└─────────────────────────────────────────────┘
```

### Request Timeout

```
❌ Request timed out (>60s)
   Last response: Metrics completed (2.1s ago)

   Waiting for: Reasoning trace...

   [Cancel] [Retry] [View Partial]
```

### LLM Error

```
⚠️  LLM Error from backend

   Provider: OpenAI
   Error: Invalid API key

   Solution: Configure OpenAI key in ki.yaml
```

---

## Keyboard Shortcuts (Frontend-Agnostic) [keyboard-shortcuts-frontend-agnostic]

| Shortcut | Action |
|----------|--------|
| `q` / `Esc` | Quit application |
| `Tab` / `Shift+Tab` | Switch focus (Tree ↔ Panel ↔ Input) |
| `Ctrl+1` thru `Ctrl+6` | Jump to Tab (Explain, Suggest, Reason, Metrics, Refactor, Deps) |
| `Ctrl+L` | Clear current tab |
| `Ctrl+C` | Cancel running request |
| `Up/Down` (in Input) | Previous/next from history |
| `Ctrl+F` | Search (in logs/output) |
| `Ctrl+S` | Save session (TODO) |

---

## Frontend Implementation Checklist [frontend-implementation-checklist]

For each frontend (Textual TUI, GTK, Web):

- [ ] Project Tree component (file browser, highlight selection)
- [ ] Tabbed Panel system (Explain, Suggest, Reason, Metrics, Refactor, Deps)
- [ ] Input Field (text entry, history, submit button)
- [ ] Status Bar (connection, metrics, spinner)
- [ ] Log Panel (sidebar, real-time updates)
- [ ] Chat Panel (sidebar, message history)
- [ ] Async streaming from backend
- [ ] Error handling + retry logic
- [ ] Keyboard shortcuts
- [ ] Rich formatting (code blocks, syntax highlighting, diffs)

---

## API Contract Examples

### Request

```json
POST /api/agent/route

{
  "project_path": "/home/user/my_project",
  "selected_file": "src/main.py",
  "user_request": "Analyze this function for performance issues",
  "agent_modes": ["explain", "metrics", "suggest"]
}
```

### Response (Streaming, JSON-L)

```json
{"event_type": "explain", "content": "This function iterates..."}
{"event_type": "metrics", "complexity": 3, "maintainability_index": 75}
{"event_type": "suggest", "suggestions": [{"type": "type_hint", "description": "Add type hints"}]}
{"event_type": "complete", "duration_ms": 2341, "cost": 0.04}
```

---

**Status:** Foundation complete  
**Next Step:** Implement in Textual TUI (doc/architecture/TUI_INTELLIGENT_TERMINAL_IDE.md)
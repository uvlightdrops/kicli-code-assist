---
title: "Roadmap: AI Terminal IDE Vision"
project: "kicli-code-assist"
scope: "roadmap-tui-vision"
type: "roadmap"
status: "active-roadmap"
created: 2026-11-05T21:25+01:00
updated: 2026-11-06T10:11:02+01:00
update_reason: "Moved to roadmap-todo/ for clarity - active TUI feature list"
cross_references:
  - doc/frontend-tui/README.md (current TUI docs)
  - doc/backend/README.md (API available)
  - doc/phases/PHASE_1_TUI_IMPLEMENTATION_COMPLETE.md (current status)
note: "This is the TUI feature roadmap. For current implementation status, see Phase 1 docs."
---

# TUI Intelligent Terminal IDE - Vision & Roadmap

## The Vision

**Not a "primitive chat interface"** — but an **intelligent terminal IDE** that leverages a powerful agent backend to enable sophisticated code analysis, transformation, and reasoning.

### What Makes This Different

| Aspect | TUI Attempt 1 (Oct 2026) | TUI 2.0 (Nov 2026+) |
|--------|--------------------------|-------------------|
| **Backend** | Basic LLM chat | Advanced agent orchestration (Phase 5.5.2+) |
| **Capabilities** | File browse + chat | Reasoning traces, multi-agent, transparency, metrics |
| **UI** | Simple file list + chat | Tabbed agent modes, streaming display, intelligent layout |
| **Use Case** | Exploratory conversation | Professional code analysis on jump hosts |
| **Future** | Limited by simple architecture | Grows with backend capabilities (no UI redesign needed) |

---

## Architecture Layers

```
┌─────────────────────────────────────────┐
│   Frontend (TUI/GTK/Web)                │ ← User interacts here
│   - Textual UI components               │
│   - Keyboard input, display             │
│   - Rich formatting                     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│   Frontend Specification (Abstract)     │ ← Routes + Components
│   - Layout: Project Tree + Panels       │
│   - Tabs: Explain, Suggest, Reason, etc │
│   - API: Which backend routes to call   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│   Backend API (Flask/ki-core)           │ ← Logic lives here
│   - /api/agent/route (orchestration)    │
│   - /api/agent/* (individual modes)     │
│   - WebSocket /socket.io (streaming)    │
│   - /api/traces/* (historical queries)  │
└─────────────────────────────────────────┘
```

This separation means:
- **GTK frontend** can be added later without touching backend
- **Web frontend** can be added later without touching backend
- **TUI improvements** don't require backend changes
- **Backend upgrades** automatically available to all frontends

---

## Phase Roadmap

### Phase 1: Foundation (This session - Nov 5)

**Goals:**
- ✅ Abstract Frontend Specification (FRONTEND_SPECIFICATION.md)
- ⏳ TUI Implementation scaffold (basic app structure)
- ⏳ Project Tree widget (file navigation)
- ⏳ Tab system (Explain, Suggest, Reason, Metrics, Refactor, Deps)
- ⏳ Input field + submission

**By end of Phase 1:**
- TUI renders correctly
- Can select files from tree
- Can submit requests to backend
- Backend responses display in tabs

---

### Phase 2: Agent Integration & Streaming (Week 1)

**Goals:**
- Real-time streaming from `/api/agent/route`
- Each event type (explain, suggest, reason, etc.) renders to correct tab
- Rich formatting: code blocks, diffs, metrics
- Error handling: timeout, backend unavailable, invalid response
- Status bar: time, cost, tokens, connection status

**By end of Phase 2:**
- Full request → response cycle working
- Multi-mode responses streaming
- All output formatted correctly

---

### Phase 3: Intelligence Features (Week 2)

**Goals:**
- Reasoning trace display (WebSocket real-time events)
- Metrics visualization (charts, scores)
- Dependency graph (clickable nodes)
- Smart input suggestions (context-aware prompts)
- Keyboard shortcuts + help modal

**By end of Phase 3:**
- TUI feels "intelligent" - shows reasoning process
- Professional metrics display
- Keyboard-driven workflow

---

### Phase 4: Polish & Optimization (Week 3)

**Goals:**
- Performance: large file trees (1000+ files)
- Responsiveness: smooth scrolling, quick tab switches
- Visual polish: colors, spacing, animations (spinners, progress)
- Error recovery: graceful degradation
- Testing: comprehensive coverage

**By end of Phase 4:**
- Production-ready TUI
- Fast on typical hardware
- Handles edge cases gracefully

---

### Phase 5: Extended Features (Month 2+)

**Optional enhancements (prioritize based on feedback):**
- Session persistence (save/load conversations)
- Advanced search (find in tree, search output)
- Split-pane view (compare two files side-by-side)
- Theming (dark/light/custom colors)
- Keyboard macros (record/replay sequences)
- Offline mode (cache responses, work without backend)
- Integration with external tools (git, linters, formatters)

---

## Core Components

### 1. Project Tree

**Purpose:** Navigate project files and select for analysis

**Features:**
- Recursive directory tree
- Lazy loading (expand on click/arrow)
- File icons (📁 📄 📝)
- Highlight current selection
- Max depth to prevent huge trees

**Backend Integration:**
- `GET /api/project/scan` → load tree
- `GET /api/project/file?path=...` → get file content

**Later Enhancement:**
- Search/filter by filename
- Git status indicators (modified, untracked)
- File metadata (size, lines, language)

---

### 2. Tabbed Agent Output

**Purpose:** Display responses from different agent modes

**Tabs:**
- **Explain**: Code explanation in natural language
- **Suggest**: Improvement suggestions with diffs
- **Reason**: Reasoning trace (streaming, step-by-step thinking)
- **Metrics**: Code quality metrics (complexity, maintainability, etc.)
- **Refactor**: Refactoring recommendations with code changes
- **Dependencies**: Dependency analysis and graph

**Behavior:**
- Only one tab active at a time
- Can switch tabs while processing (events buffer)
- Scroll independently per tab
- Clear button per tab

**Backend Integration:**
- `POST /api/agent/route` → streams all events
- `WS /socket.io/agent/execution` → real-time reasoning events

---

### 3. Input Field

**Purpose:** Accept user requests

**Features:**
- Multi-line support (grows as user types)
- History: Up/Down arrows cycle through previous requests
- Auto-submit: Enter = send (or Ctrl+Enter for multi-line)
- Placeholder: "Ask me to analyze, suggest, explain..."
- Status: Disabled during processing, enabled when ready

**Backend Integration:**
- `POST /api/agent/route` with user_request parameter

---

### 4. Status Bar

**Purpose:** Real-time metrics and connection status

**Display:**
```
✅ Ready | Backend: http://localhost:8000 | Time: 2.3s | Cost: $0.04 | Tokens: 234
```

**Updating:**
- Backend connection: ✅ / ❌ / ⏳ (checking)
- Processing state: ✅ Ready / 🔄 Processing (X.Xs)
- Metrics: Time (ms), Cost ($), Tokens (#)

**Backend Integration:**
- `GET /api/project/scan` → check backend health at startup
- Stream events → update metrics per event

---

### 5. Logs & Chat Sidebar (Future)

**Purpose:** Debug and history

**Logs Tab:**
- Real-time log tail
- Filters: ERROR, WARN, INFO, DEBUG
- Show what's sent to LLM and what's returned

**Chat Tab:**
- Full conversation history
- Searchable
- Can re-submit previous requests

**Backend Integration:**
- `GET /api/logs/tail?lines=100`
- `WS /socket.io/logs` for real-time updates

---

## Data Flow Examples

### Example 1: User Analyzes Function

```
1. User navigates tree: src/ → utils.py → select
2. Tree highlights utils.py
3. Input field: "Explain this function and suggest improvements"
4. User presses Enter

5. Frontend:
   - Disables input, shows spinner
   - Status bar: "🔄 Processing (0.2s)..."
   - Clears previous tab contents

6. Backend POST /api/agent/route:
   {
     "project_path": ".",
     "selected_file": "src/utils.py",
     "user_request": "Explain...",
     "agent_modes": ["explain", "suggest", "metrics"]
   }

7. Backend streams (JSON-L):
   - Event 1: explain → Display in [Explain] tab
   - Event 2: suggest → Display in [Suggest] tab  
   - Event 3: metrics → Display in [Metrics] tab
   - Event 4: complete → Stop spinner, show time/cost

8. Status bar updates:
   ✅ Complete | Time: 2.3s | Cost: $0.04 | Tokens: 234

9. User clicks tabs to read responses
```

### Example 2: Real-time Reasoning (Phase 3)

```
1. User submits request with agent_modes=["reason", "suggest"]
2. Backend starts streaming

3. Reasoning Tab gets live events:
   WebSocket: "reasoning_step_started" {step: "Analyze AST"}
   → Display: "[1] Analyzing AST..."
   
   WebSocket: "reasoning_step_complete" {findings: [...]}
   → Update: "[1] ✅ Found 3 functions"
   
   WebSocket: "reasoning_step_started" {step: "Check complexity"}
   → Display: "[2] Checking complexity..."
   
   (etc.)

4. Suggest Tab still receives events independently
5. User watches both tabs update in real-time
```

---

## Design Decisions

### Why Tabs, Not Multiple Panels?

**Chosen:** Tabs (one mode at a time)
**Alternative:** Split panes (multiple modes side-by-side)

**Rationale:**
- Terminal space is limited (80-200 chars wide)
- Tabs keep each response readable (no cramped columns)
- Easy to focus on one mode without distraction
- Can add split view later (Phase 5 enhancement)

---

### Why Fixed Project Tree Width?

**Chosen:** 60 chars fixed width for tree
**Alternative:** Percentage-based (40% of terminal)

**Rationale:**
- Percentage fails with dynamic content in Textual
- 60 chars fits most file paths comfortably
- Leaves ample space for output panel
- User can scroll tree horizontally if needed

---

### Why JSON-L Response Format?

**Chosen:** JSON-L (one JSON object per line)
**Alternative:** Single JSON response, streaming text

**Rationale:**
- Each event is independent and parseable
- Can display partial results (don't wait for full response)
- Easy to buffer and re-render on tab switch
- Works well with WebSocket + REST mixed (some events via stream, some via WS)

---

## Testing Strategy

### Manual Testing (Phase 1-2)

```
✓ Project tree renders and scrolls
✓ File selection highlights correctly
✓ Input field accepts text and submits
✓ Backend request sent with correct parameters
✓ Response events display in correct tabs
✓ Tab switching doesn't lose content
✓ Status bar updates with timing/cost
✓ Error messages display gracefully
✓ Backend unavailable shown clearly
✓ Timeout handled (60s default)
```

### Automated Testing (Phase 2+)

- Mock backend responses (JSON-L fixtures)
- Unit tests for event rendering
- Integration tests for request → display flow
- Performance tests (1000 files in tree, 10K line output)

---

## Known Challenges & Solutions

### Challenge 1: Terminal Size Variability

**Problem:** TUI must work on 80-char small terminals and 200+ char wide terminals

**Solution:**
- Fixed tree width (60 chars) + scrollable output
- Responsive layout: stack vertically on very small terminals
- Test on multiple sizes during Phase 1

### Challenge 2: Streaming Large Responses

**Problem:** Reasoning traces can be thousands of lines; don't want to buffer all

**Solution:**
- Use RichLog with `max_lines` buffer (e.g., last 500 lines)
- Older lines auto-removed
- Optional: "Load more" button to fetch history

### Challenge 3: WebSocket vs REST Mixed

**Problem:** Some events come via `POST /api/agent/route` stream, some via WebSocket

**Solution:**
- Client handles both simultaneously
- Events ordered by timestamp
- Duplicates detected and ignored
- Coordinator pattern in tui_client.py

---

## Success Criteria (Phase 1 Complete)

- [ ] FRONTEND_SPECIFICATION.md complete (abstract, multi-frontend ready)
- [ ] TUI renders with all components (tree, tabs, input, status)
- [ ] File selection works (can click/arrow through tree)
- [ ] Backend connectivity verified (health check passes)
- [ ] Request submission works (can type + press Enter)
- [ ] Response events display in tabs (at least one mode)
- [ ] Status bar shows metrics
- [ ] Error handling works (backend unavailable, timeout, etc.)
- [ ] No crashes on edge cases
- [ ] Keyboard shortcuts working (Tab, Ctrl+1-6, q)

---

**Status:** Vision & roadmap complete  
**Next:** Phase 1 implementation begins  
**Timeline:** Phases 1-2 this week, Phase 3+ next week
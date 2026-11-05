---
title: Phase 1 TUI Checklist - Foundation & Scaffold
project: kicli-code-assist
scope: specification
status: active
created: 2026-11-05T22:01+01:00
updated: 2026-11-05T22:01+01:00
update_reason: Extract from old 04_FEATURE_CHECKLIST, redesigned for TUI 2.0 (agent-backend)
agent_project: kicli-code-assist
cross_references:
  - doc/architecture/01_ARCHITECTURE.md (Phase 1 overview)
  - doc/architecture/FRONTEND_SPECIFICATION.md (what to implement)
  - doc/architecture/TUI_INTELLIGENT_TERMINAL_IDE.md (vision & phases)
  - doc/architecture/TUI_TEXTUAL_ARCHITECTURE.md (implementation guide)
---

# Phase 1 TUI Checklist — Foundation & Scaffold

**Timeline:** Week of Nov 5-8, 2026  
**Goal:** TUI renders, connects to backend, can submit requests and display responses  
**Success Criteria:** All items checked ✅

---

## Component Implementation

### Project Tree Widget
- [ ] File browser component (read-only tree of project files)
- [ ] Recursive directory scanning with depth limit (3-5 levels)
- [ ] File/folder icons (📄 📁)
- [ ] Highlight currently selected file
- [ ] Keyboard navigation (Up/Down/Enter to expand folders)
- [ ] Display current path in header
- [ ] Handle edge cases (empty dir, permission denied, cycles)
- [ ] Responsive width (60-80 chars fixed width, not percentage)

**Implementation File:** `kicli_code_assist/ui/widgets/project_tree.py`  
**Test Coverage:** File list rendering, navigation, edge cases

### Tabbed Agent Output Panel
- [ ] Tab system (6 tabs: Explain, Suggest, Reason, Metrics, Refactor, Deps)
- [ ] Only one tab active at a time
- [ ] Tab switching via Ctrl+1-6 keyboard shortcuts
- [ ] Content buffer for each tab (store events while not active)
- [ ] Display buffer when tab becomes active
- [ ] Tab labels show completion status (✅ or ⏳)
- [ ] Clear tab content (Ctrl+L)

**Implementation File:** `kicli_code_assist/ui/widgets/agent_output_panel.py`  
**Test Coverage:** Tab switching, buffering, keyboard shortcuts

### Input Field Widget
- [ ] Text input field with cursor
- [ ] Focus/unfocus states (grayed out when unfocused)
- [ ] Submit on Enter (or Ctrl+Enter for multi-line)
- [ ] Clear field after submission
- [ ] History tracking (Up/Down arrows cycle through history)
- [ ] Display placeholder text
- [ ] Disabled state during processing

**Implementation File:** `kicli_code_assist/ui/widgets/input_field.py`  
**Test Coverage:** Input validation, history, state transitions

### Status Bar
- [ ] Backend connection status (✅ Connected | ❌ Unreachable)
- [ ] Processing indicator (⏳ Analyzing... | ✅ Complete)
- [ ] Response timing (ms)
- [ ] Cost indicator ($0.04)
- [ ] Token count
- [ ] Keyboard shortcut hint (q=quit, Ctrl+C=cancel)

**Implementation File:** `kicli_code_assist/ui/widgets/status_bar.py`  
**Test Coverage:** Status updates, formatting

### Main TUI App
- [ ] Assemble all widgets into layout
- [ ] Vertical/horizontal layout manager
- [ ] Project Tree (left, 60 chars)
- [ ] Agent Output (center, flexible)
- [ ] Input Field (bottom, full width)
- [ ] Status Bar (bottom, full width)
- [ ] CSS/styling for layout
- [ ] App initialization and mount

**Implementation File:** `kicli_code_assist/ui/tui_client.py` (refactor)  
**Test Coverage:** Layout rendering, widget assembly

---

## Backend Connectivity

### Health Check
- [ ] Check backend health on startup
- [ ] Use root endpoint `/` (not `/health`)
- [ ] Timeout after 5s
- [ ] Show error modal if unreachable
- [ ] Provide retry button

**Implementation:** `kicli_code_assist/ui/tui_agent_client.py:health_check()`

### Project Scanning
- [ ] Implement `scan_project(path, depth=3)`
- [ ] Call `GET /api/project/scan?path=.&depth=3`
- [ ] Parse response (files, count, languages)
- [ ] Populate Project Tree widget
- [ ] Handle errors (timeout, 404, etc.)

**Implementation:** `kicli_code_assist/ui/tui_agent_client.py:scan_project()`

### Request/Response Streaming
- [ ] Implement `call_agent_route(project_path, selected_file, user_request, agent_modes)`
- [ ] POST to `/api/agent/route`
- [ ] Parse JSON-L response stream
- [ ] Route each event to appropriate tab
- [ ] Handle stream errors (partial response, timeout)
- [ ] Cancel button support

**Implementation:** `kicli_code_assist/ui/tui_agent_client.py:call_agent_route()`

### Event Routing
- [ ] Map event_type → tab widget
  - `explain` → Explain tab
  - `suggest` → Suggest tab
  - `reason` → Reason tab
  - `metrics` → Metrics tab
  - `refactor` → Refactor tab
  - `dependencies` → Deps tab
  - `complete` → Status bar (timing, cost)
- [ ] Buffer events for inactive tabs
- [ ] Display on tab switch

**Implementation:** `kicli_code_assist/ui/tui_agent_client.py:route_event()`

---

## User Interaction

### Keyboard Shortcuts

| Key | Action | Mode |
|-----|--------|------|
| `q` | Quit | Always |
| `Esc` | Cancel request | Processing |
| `Ctrl+C` | Cancel request | Processing |
| `Tab` | Next focus (Tree → Output → Input) | Always |
| `Shift+Tab` | Previous focus | Always |
| `Ctrl+1` | Jump to Explain tab | Always |
| `Ctrl+2` | Jump to Suggest tab | Always |
| `Ctrl+3` | Jump to Reason tab | Always |
| `Ctrl+4` | Jump to Metrics tab | Always |
| `Ctrl+5` | Jump to Refactor tab | Always |
| `Ctrl+6` | Jump to Deps tab | Always |
| `Ctrl+L` | Clear current tab | Output focused |
| `Up/Down` | Previous/next from history | Input focused |
| `Enter` | Submit request | Input focused |
| `Ctrl+Enter` | New line (in multi-line mode) | Input focused |

**Implementation:** Textual bindings in `tui_client.py`

### File Selection Workflow
1. User navigates Project Tree (Up/Down/Enter)
2. Selects a Python file
3. File path highlighted
4. File path available for request

**Implementation:** `widgets/project_tree.py:on_tree_select()`

### Request Submission Workflow
1. User focuses Input Field (Tab)
2. Types request (e.g., "Analyze this function")
3. Presses Enter
4. Request sent to `/api/agent/route`
5. Status bar shows "⏳ Analyzing..."
6. Events stream in, populate tabs
7. Tab headers show ✅ when complete
8. Status bar shows timing + cost
9. Input field cleared, ready for next request

**Implementation:** Across all widgets + `tui_agent_client.py`

---

## Error Handling

### Backend Unavailable
- [ ] Detect on health check (timeout or status ≠ 200)
- [ ] Show modal: "❌ Backend unreachable (http://localhost:8000)"
- [ ] Show suggestion: "Start backend: python -m stackctl start"
- [ ] Provide [Retry] button
- [ ] Disable input field until connected

**Implementation:** `tui_agent_client.py:health_check()` + error modal

### Request Timeout
- [ ] Timeout after 60s of no response
- [ ] Show warning in status bar: "⚠️ Request timed out (>60s)"
- [ ] [Cancel] and [Retry] buttons in modal
- [ ] Allow user to view partial results

**Implementation:** Streaming handler with timeout

### LLM Error
- [ ] Catch error events from backend
- [ ] Display in Explain/Suggest tab: "⚠️ LLM Error: {error_message}"
- [ ] Show in red text
- [ ] Provide [Retry] button

**Implementation:** Error event routing + display

### Invalid File Path
- [ ] Check if selected file exists before submitting
- [ ] Show error: "❌ File not found: {path}"
- [ ] Suggest re-scanning project (Ctrl+R)

**Implementation:** Validation in input submission

---

## Testing

### Manual Testing Checklist
- [ ] Start TUI: `kicli-assist tui --project /path/to/project`
- [ ] Backend connected (status bar shows ✅)
- [ ] Project Tree displays files
- [ ] Navigate tree (Up/Down/Enter)
- [ ] Select file (highlight changes)
- [ ] Focus Input (Tab key)
- [ ] Type request + Enter
- [ ] Status bar shows "⏳ Analyzing..."
- [ ] First tab shows response
- [ ] Tab switch works (Ctrl+1-6)
- [ ] Status bar shows timing after complete
- [ ] Input cleared, ready for next request
- [ ] Ctrl+C cancels processing
- [ ] Q quits application
- [ ] Test with backend stopped (error handling)

### Edge Cases
- [ ] Empty project (no files)
- [ ] Large project (1000+ files)
- [ ] No selected file (submit anyway)
- [ ] Network timeout
- [ ] LLM error
- [ ] Terminal resize (layout adapts)
- [ ] Very long response (tab scrolls)
- [ ] Rapid requests (one after another)

### Automated Tests
- [ ] Unit: Project Tree file scanning
- [ ] Unit: Tab widget switching
- [ ] Unit: Event routing logic
- [ ] Integration: Backend connectivity
- [ ] Integration: Request/response flow
- [ ] Snapshot: Status bar rendering

**Files:** `tests/test_tui_widgets.py`, `tests/test_tui_integration.py`

---

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| File tree render | <100ms | For 1000+ files |
| Project scan | <2s | Initial load |
| Tab switch | <50ms | No lag |
| Request to first event | <3s | Includes API latency |
| Memory usage | <150MB | Session idle |
| Terminal resize | <100ms | Responsive layout |

---

## Success Criteria (Definition of Done)

**Functional:**
- ✅ TUI starts without errors
- ✅ Backend health check works (shows connection status)
- ✅ Project Tree populates from filesystem
- ✅ File selection works (navigation + highlight)
- ✅ Can submit request with selected file
- ✅ Backend response displays in tabs
- ✅ All 6 tabs functional
- ✅ Status bar updates correctly
- ✅ Keyboard shortcuts work

**Non-Functional:**
- ✅ No crashes on edge cases
- ✅ UI responsive during processing
- ✅ Memory usage reasonable
- ✅ Layout correct on terminal resize
- ✅ Error messages clear and actionable

**Code Quality:**
- ✅ No type errors (mypy clean)
- ✅ Linting passes (pylint/flake8)
- ✅ Tests passing (>80% coverage)
- ✅ No hardcoded values (all config)
- ✅ Comments on non-obvious logic
- ✅ Git history clean (semantic commits)

---

## Related Documentation

**Read First:**
- `doc/architecture/01_ARCHITECTURE.md` (Phase 1 section)
- `doc/architecture/FRONTEND_SPECIFICATION.md` (components to implement)

**Implementation Guide:**
- `doc/architecture/TUI_INTELLIGENT_TERMINAL_IDE.md` (Phase 1 breakdown)
- `doc/architecture/TUI_TEXTUAL_ARCHITECTURE.md` (widget patterns)

**Reference:**
- `doc/archive/tui_attempt_oct2026/04_FEATURE_CHECKLIST.md` (old lessons learned)
- `doc/archive/tui_attempt_oct2026/02_TUI_SPECIFICATION_LEGACY.md` (old design)

---

## Notes & Learnings from Attempt 1 (Oct 2026)

**What Worked:**
- Textual framework solid for TUI
- File tree navigation intuitive
- Async operations with `run_worker(thread=True)` work well
- RichLog good for streaming output

**What Didn't Work:**
- Chat-based interface too limited for code analysis
- Trying to do too much in Phase 1 (file preview, context injection)
- Complexity exploded without clear agent backend

**This Time (Nov 2026):**
- Start with minimal Phase 1 (just scaffold + streaming)
- Leverage advanced backend (agents, reasoning, transparency)
- Clear phase boundaries
- Focus on agent capabilities, not chat chat

---

**Status:** Ready to implement  
**Next Step:** Begin Phase 1 TUI scaffold (kicli_code_assist/ui/ refactor)  
**Timeline:** Nov 5-8, 2026

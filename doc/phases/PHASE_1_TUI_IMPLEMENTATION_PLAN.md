---
title: Phase 1 - TUI Implementation Plan (Nov 5-8, 2026)
scope: implementation
project: kicli-code-assist
status: active
created: 2026-11-05T23:57+01:00
updated: 2026-11-05T23:57+01:00
update_reason: Comprehensive implementation roadmap - inside-out modular approach
agent_project: kicli-code-assist
cross_references:
  - doc/architecture/FRONTEND_SPECIFICATION.md (abstract interface)
  - doc/architecture/TUI_INTELLIGENT_TERMINAL_IDE.md (vision & phases)
  - doc/architecture/TUI_TEXTUAL_ARCHITECTURE.md (implementation patterns)
  - doc/specifications/02_PHASE_1_CHECKLIST.md (acceptance criteria)
---

# Phase 1 - TUI Implementation Plan

## Strategy: Inside-Out Modular Approach

Build **independent, self-contained modules first**, then compose them into the final TUI.

This approach enables:
- ✅ Early testing (each module works standalone)
- ✅ Easy layout experimentation (swap/reorder modules)
- ✅ Parallel development (modules are independent)
- ✅ Clean configuration (disable modules via config)
- ✅ Future improvements (replace modules without breaking TUI)

---

## Phase 1 Breakdown (5 Sub-Phases)

### 1.1: Core Infrastructure & Config
**Duration:** 1-2 hours  
**Deliverable:** Base TUI app + configuration system

**Tasks:**
- [ ] Create `kicli_code_assist/ui/tui_client.py` (main Textual app)
- [ ] Create config: `kicli_code_assist/config/tui_config.yaml`
- [ ] Configuration loader: `kicli_code_assist/ui/config.py`
- [ ] Enable/disable modules via config (e.g., `enabled_panels: [tree, tabs, logs, chat]`)

**Tech Stack:**
- Textual App class
- YAML configuration
- pydantic for validation

**Acceptance Criteria:**
- [ ] App starts without errors
- [ ] Config loads from YAML
- [ ] Logging shows module status

---

### 1.2: Preview Modal (Standalone)
**Duration:** 2-3 hours  
**Deliverable:** Reusable file preview widget

**What it does:**
- Read file from filesystem
- Display with syntax highlighting (Rich)
- Handle large files (streaming, truncation)
- Modal pop-up or embedded pane

**Implementation:**
- File: `kicli_code_assist/ui/widgets/preview_modal.py`
- Class: `FilePreviewModal(Container)`
- Methods: `load_file()`, `show()`, `close()`
- Config: `max_preview_size`, `highlight_language`

**Acceptance Criteria:**
- [ ] Preview renders any file type
- [ ] Scrollable, searchable
- [ ] Syntax highlighting works
- [ ] Works as standalone widget

---

### 1.3: VI Editor Modal (Standalone)
**Duration:** 2-3 hours  
**Deliverable:** VI-style editor for input/command editing

**What it does:**
- Modal text editor (like vim)
- VI keybindings (hjkl, insert mode, etc.)
- Multiline support
- Return to main TUI when done (ESC or :wq)

**Implementation:**
- File: `kicli_code_assist/ui/widgets/vi_editor_modal.py`
- Class: `VIEditorModal(Container)`
- Modes: Insert, Normal, Visual
- Config: `vi_mode_enabled`, `vi_keybindings`

**Note:** May use Textual's TextArea or build custom (TBD)

**Acceptance Criteria:**
- [ ] Modal opens on hotkey (e.g., Ctrl+E)
- [ ] VI keybindings work (hjkl, i, ESC, etc.)
- [ ] Returns text to TUI on exit
- [ ] Works standalone

---

### 1.4: File Browser Widget (Standalone)
**Duration:** 2-3 hours  
**Deliverable:** Project tree navigation widget

**What it does:**
- Scan project root (configurable)
- Display tree with folders/files
- Expand/collapse folders
- Select file → load preview + context

**Implementation:**
- File: `kicli_code_assist/ui/widgets/file_browser.py`
- Class: `FileTree(Tree)` or custom tree widget
- Methods: `scan_project()`, `select_file()`, `get_selected_path()`
- Config: `project_root`, `ignore_patterns` (.gitignore aware)

**Acceptance Criteria:**
- [ ] Tree renders correctly
- [ ] Vi-style navigation (hjkl)
- [ ] Expand/collapse works
- [ ] Selection persists
- [ ] Works standalone in a test app

---

### 1.5: AI Panel System (Modular Tabs)
**Duration:** 3-4 hours  
**Deliverable:** Tabbed agent output display

**What it does:**
- Container with multiple tabs
- Each tab = one agent mode (Explain, Suggest, Reason, Metrics, etc.)
- Display rich formatted output (code blocks, diffs, etc.)
- Loading state (spinner)

**Implementation:**
- File: `kicli_code_assist/ui/widgets/agent_tabs.py`
- Classes:
  - `AgentTabPanel(TabbedContent)` (main container)
  - `ExplainTab(Vertical)` (content)
  - `SuggestTab(Vertical)`
  - etc.
- Methods: `display_response()`, `clear_tab()`, `append_output()`
- Config: `enabled_tabs`, `tab_order`

**Acceptance Criteria:**
- [ ] Tabs render correctly
- [ ] Can switch tabs with Ctrl+1-6
- [ ] Content scrolls
- [ ] Rich formatting works
- [ ] Loading spinner animates

---

### 1.6: Input Bar & Status (Simple)
**Duration:** 1-2 hours  
**Deliverable:** Bottom input + status display

**What it does:**
- Text input field at bottom
- Accept multi-line input (Shift+Enter for newline)
- Submit on Enter
- Show status: connected, processing, error, ready

**Implementation:**
- File: `kicli_code_assist/ui/widgets/input_bar.py`
- Class: `InputBar(Container)`
- Config: `multiline_support`, `submit_hotkey`

**Acceptance Criteria:**
- [ ] Input renders
- [ ] Accepts text
- [ ] Status updates
- [ ] Visible feedback

---

### 1.7: Composition & Layout (Main TUI App)
**Duration:** 2-3 hours  
**Deliverable:** Complete TUI with all components

**What it does:**
- Assemble all widgets from 1.2-1.6
- Grid layout:
  ```
  ┌─────────────┬──────────────────┐
  │ File Tree   │ Agent Tabs       │
  │ (1.4)       │ (1.5)            │
  ├─────────────┼──────────────────┤
  │ Input Bar (1.6) + Status       │
  └─────────────┴──────────────────┘
  ```
- Connect file selection → preview modal
- Connect input submit → backend API
- Optional: Logs panel (sidebar tab)

**Implementation:**
- File: `kicli_code_assist/ui/tui_client.py` (Textual App)
- Methods: `compose()`, `on_mount()`, `handle_submit()`
- Config: `enable_logs`, `enable_chat`, `layout_mode`

**Acceptance Criteria:**
- [ ] All widgets render in correct positions
- [ ] File selection works
- [ ] Input submission works
- [ ] Tab switching works
- [ ] Resizing works

---

### 1.8: Backend Connectivity (HTTP/WS)
**Duration:** 2-3 hours  
**Deliverable:** API client for TUI

**What it does:**
- HTTP client for `/api/agent/route`
- WebSocket client for streaming responses
- Error handling + timeouts
- Queue responses to UI thread safely

**Implementation:**
- File: `kicli_code_assist/ui/api_client.py`
- Classes:
  - `HTTPClient` (async requests)
  - `WebSocketClient` (streaming)
- Methods: `send_request()`, `stream_response()`
- Config: `backend_url`, `timeout`, `retry_count`

**Acceptance Criteria:**
- [ ] Can connect to backend
- [ ] Sends requests correctly
- [ ] Receives responses
- [ ] Handles errors gracefully
- [ ] Timeout works

---

### 1.9: Integration Testing & Polish
**Duration:** 2-3 hours  
**Deliverable:** E2E test + minor fixes

**What it does:**
- Test full workflow: select file → submit → display response
- Keyboard shortcuts work
- Configuration disabling works
- Error handling (backend down, invalid response, etc.)

**Implementation:**
- File: `tests/test_tui_integration.py`
- Test scenarios:
  - App starts
  - File selection works
  - Backend communication works
  - Tabs display correctly
  - Disabling modules via config works

**Acceptance Criteria:**
- [ ] E2E workflow passes
- [ ] No crashes on bad input
- [ ] Config disabling works
- [ ] Keyboard shortcuts work

---

## Configuration System

All UI modules should be configurable. Example `tui_config.yaml`:

```yaml
# TUI Configuration
tui:
  # Enabled panels (comment out to disable)
  panels:
    file_tree:
      enabled: true
      project_root: "."
      ignore_patterns: [".git", "__pycache__", ".venv"]
    
    agent_tabs:
      enabled: true
      enabled_tabs: [explain, suggest, reason, metrics]
      tab_order: [explain, suggest, reason, metrics, refactor, dependencies]
    
    logs:
      enabled: true
      max_lines: 100
    
    chat:
      enabled: false  # Disable for now
  
  # Editor modes
  vi_mode: true
  preview_modal: true
  
  # Backend
  backend_url: "http://localhost:8000"
  timeout: 30
  
  # UI
  theme: "dark"
  layout: "split"  # split | focused
```

---

## Implementation Order

**Recommended sequence** (not strictly sequential - can parallelize):

1. **1.1 Core Infrastructure** — Blocks everything
2. **1.4 File Browser** — Simple, visualize early
3. **1.2 Preview Modal** — Useful independently
4. **1.3 VI Editor** — Optional, can add later
5. **1.5 AI Tabs** — Core feature
6. **1.6 Input Bar** — Simple
7. **1.7 Composition** — Brings it together
8. **1.8 Backend** — Integrates with real API
9. **1.9 Testing** — Verify it all works

---

## Commit Strategy

After each sub-phase (1.1, 1.2, etc.):
1. Commit working code
2. Update this document with status
3. Note any issues/learnings

Format:
```
feat: Phase 1.X — [Component Name]

- Implemented [what was done]
- Added config support for [features]
- Tests: [N passing]

Learnings:
- [Any insights, gotchas, design decisions]

Remaining:
- [What's left in this component]
```

---

## Risk Mitigation

**Risk:** Textual library learning curve  
**Mitigation:** Start with simple widgets (1.4), progressively complex

**Risk:** Backend API not available  
**Mitigation:** Mock API responses in 1.8, real backend optional

**Risk:** Complex layout causes UI bugs  
**Mitigation:** Test composition (1.7) early with simple content

**Risk:** Configuration system too complex  
**Mitigation:** Start with basic YAML, add validation gradually

---

## Success Criteria for Phase 1

By end of Phase 1:

- [ ] TUI app starts without errors
- [ ] File tree navigable
- [ ] Can select a file
- [ ] Preview shows file content
- [ ] Can submit a request to backend
- [ ] Response displays in correct tab
- [ ] All components work independently
- [ ] Configuration system working
- [ ] No crashes on bad input
- [ ] Keyboard navigation smooth
- [ ] Documentation complete

---

## Next Steps After Phase 1

- **Phase 2:** Streaming responses, WebSocket integration
- **Phase 3:** Reasoning traces, metrics visualization
- **Phase 4:** Polish, keyboard shortcuts, help system

---

**Created:** 2026-11-05T23:57+01:00  
**Status:** READY FOR IMPLEMENTATION  
**Responsible:** Copilot

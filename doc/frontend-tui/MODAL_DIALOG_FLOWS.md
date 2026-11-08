---
title: Modal & Dialog Flow Diagrams
project: kicli-code-assist
scope: frontend-tui
purpose: Document all modal/dialog interactions, keybindings, state transitions, and data flow in TUI application
created: 2026-11-08 03
updated: 2026-11-08 03
update_reason: Initial creation - comprehensive UI flow documentation
status: active
semantic_blocks: true
relations:
  - type: depends-on
    target: ../ARCHITECTURE_OVERVIEW.md
    reason: Foundation for all TUI interactions
  - type: related-to
    target: PROJECT_UNDERSTANDING_USAGE.md
    reason: Project understanding modal workflow
  - type: reference
    target: ../../backend/system-apis/README.md
    reason: Backend endpoint contracts for modal workflows
---

# Modal & Dialog Flow Diagrams

## Overview

This document maps all modal/dialog interactions in kicli-code-assist TUI, including:
- Entry points (keybindings, button clicks)
- State transitions
- Data flow (user input → backend → display)
- User decision points
- Error handling

---

## Section 1: Keybindings Map [keybindings-map]

| Key | Action | Dialog | Trigger | Handler |
|-----|--------|--------|---------|---------|
| `q` / `ctrl+c` | Quit | None | App-level | `action_quit()` |
| `ctrl+1` – `ctrl+6` | Tab Switch | None | Tab navigation | `action_tab_*()` |
| `n` | New File | CreateFileDialog | File browser focus | `action_new_file()` |
| `ctrl+s` | Save Current | None (direct save) | Editor focus | `action_save_current_file()` |
| `ctrl+u` | Analyze Project | UnderstandProjectDialog | Any panel focus | `action_understand_project()` |
| `ctrl+b` | Toggle Browser | None | UI state | (file browser toggle) |
| `ctrl+f` | Preview/Find | None | UI state | (preview pane toggle) |

**Note:** Some keybindings not yet fully working (N, Ctrl+S in progress)

---

## Section 2: Project Understanding Flow [project-understanding-flow]

### Trigger: `Ctrl+U` → Analyze Project

```
User presses Ctrl+U
    ↓
action_understand_project() in KICLITUIApp
    ↓
Is project path selected? 
    → NO: Show error notification → return
    → YES: continue
    ↓
UnderstandProjectDialog appears
    ├─ "Overview" (fast, ~2s)
    ├─ "Detailed" (medium, ~5s) [default]
    └─ "Deep" (slow, ~10s)
    ↓
User selects depth level
    ↓
HTTP POST /api/projects/understand
    {
      "project_path": "/path/to/project",
      "depth": "detailed"
    }
    ↓
Backend processes (3-10 seconds)
    ├─ Stage 1: Discovery (docs scan)
    ├─ Stage 2: Code Analysis (AST extraction)
    ├─ Stage 3: Aggregation (context building)
    ├─ Stage 4: LLM Prep (prompt generation)
    └─ Stage 5: Synthesis (report generation)
    ↓
Response received:
    {
      "success": true,
      "project_name": "...",
      "synthesis_report": "...",
      "aggregated_context": "...",
      "llm_insights": "...",
      "metrics": {...}
    }
    ↓
ProjectUnderstandingPanel updates
    ├─ Displays synthesis_report (truncated for TUI)
    ├─ Shows project metrics (modules, LOC, patterns)
    └─ Panel switches to "📊 Project" tab
    ↓
User reads report
    ├─ Can scroll through synthesis
    ├─ Can view full report with external viewer
    └─ Can copy results
    ↓
End (user closes panel or switches tab)
```

**State Management:**
```
[IDLE] → [DIALOG_SHOWN] → [PROCESSING] → [RESULTS_SHOWN] → [IDLE]
         (await input)      (backend)       (display)
```

**Error Cases:**
1. **Project not found:** Show error, return to IDLE
2. **Backend timeout:** Show timeout error, return to IDLE
3. **No project selected:** Show "Select a project first", return to IDLE
4. **Malformed response:** Log error, show generic error message

---

## Section 3: File Operations Flow [file-operations-flow]

### 3.1 New File Dialog (`N` key)

```
User presses N (in file browser)
    ↓
action_new_file() triggered
    ↓
CreateFileDialog appears
    ├─ Filename input field
    ├─ Optional: Folder selector
    └─ [Create] [Cancel] buttons
    ↓
User enters filename
    ↓
User clicks [Create] or presses Enter
    ↓
HTTP POST /api/files/create
    {
      "project_root": "/path/to/project",
      "file_path": "src/new_file.py"
    }
    ↓
Backend response:
    {
      "success": true,
      "created_file": "/path/to/project/src/new_file.py",
      "content": ""
    }
    ↓
File appears in browser
    ↓
Auto-select new file in FileTree
    ↓
Optionally: Open in editor
    ↓
End
```

**Status:** Currently broken - keybinding not working properly

---

### 3.2 Save File Dialog (`Ctrl+S` key)

```
User presses Ctrl+S (in editor)
    ↓
action_save_current_file() triggered
    ↓
Get active editor content
    ↓
HTTP POST /api/files/save
    {
      "file_path": "/path/to/project/src/file.py",
      "content": "..."
    }
    ↓
Backend response:
    {
      "success": true,
      "file_path": "...",
      "message": "File saved"
    }
    ↓
Show success notification
    ↓
Update file modified indicator (remove *)
    ↓
End
```

**Status:** Currently broken - keybinding not working properly

---

## Section 4: Analysis Dialog (Ctrl+A alternative)

```
User triggers analysis (planned feature)
    ↓
Show dialog:
    ├─ Code analysis depth
    ├─ Pattern detection
    ├─ Metrics level
    └─ Export options
    ↓
User configures
    ↓
HTTP POST /api/projects/analyze
    ↓
Backend processes file structure
    ↓
Results show in "📈 Metrics" tab
    ├─ Module hierarchy
    ├─ Function/class list
    ├─ Dependency graph
    └─ Complexity metrics
    ↓
End
```

**Status:** Partially implemented (ProjectAnalysisPanel exists)

---

## Section 5: Shell Command Approval Dialog

```
Backend suggests shell command
    ↓
App receives command via WebSocket or API
    ↓
ShellCommandApprovalModal appears
    ├─ Displays: command, description
    ├─ Shows: [Approve] [Reject] [Edit] buttons
    └─ Context: why this command is needed
    ↓
User decision:
    
    → [Approve]:
        HTTP POST /api/execute/shell
        {
          "command": "...",
          "approved": true
        }
        → Backend executes
        → Results streamed to UI
        ↓
        
    → [Reject]:
        Show notification "Command rejected"
        ↓
        
    → [Edit]:
        CommandManualEntryDialog appears
        User edits command
        Goto: User decision (Approve/Reject)
        ↓
        
End
```

**Components:**
- `ShellCommandApprovalModal` in `ui/modals/approval_modal.py`
- `CommandManualEntryDialog` in `ui/shell_command_editor.py`

---

## Section 6: Error Modal [error-modal]

```
Any operation produces error
    ↓
Backend returns error response
    OR
Exception occurs in TUI
    ↓
ErrorModal appears
    ├─ Title: Error type (ValidationError, TimeoutError, etc.)
    ├─ Message: User-friendly description
    ├─ Details: Technical details (collapsed)
    └─ [Dismiss] [View Details] [Report] buttons
    ↓
User action:
    
    → [Dismiss]:
        Modal closes
        Previous screen restored
        ↓
        
    → [View Details]:
        Expand technical details
        Show stack trace (if available)
        ↓
        
    → [Report]:
        Send error to logging backend
        Show "Error reported" message
        ↓
        
End
```

**Components:**
- `ErrorModal` in `ui/modals/error_modal.py`
- `error_modal.tcss` styling

---

## Section 7: VI Editor Modal [vi-editor-modal]

```
User wants to edit code block
    OR
Agent suggests multi-line edit
    ↓
VIEditorModal appears
    ├─ Full screen editor
    ├─ Vi keybindings enabled
    ├─ Syntax highlighting
    └─ File type detection
    ↓
User edits (Vi mode)
    ├─ Press ESC to command mode
    ├─ `:wq` to save & exit
    ├─ `:q!` to discard
    ↓
Backend receives edited content
    ↓
Content returned to calling dialog
    ↓
Modal closes
    ↓
Editor updates with changes
    ↓
End
```

**Components:**
- `VIEditorModal` in `ui/widgets/vi_editor_modal.py`

---

## Section 8: Prompts/Templates Modal [prompts-modal]

```
User opens Prompts (Ctrl+P or menu)
    ↓
PromptsModal appears
    ├─ List of saved prompts
    ├─ Search/filter
    ├─ [Create New] [Edit] [Delete] buttons
    └─ Preview pane
    ↓
User actions:
    
    → [Select prompt]:
        Prompt content loads
        Preview shows result
        User can execute
        ↓
        
    → [Create New]:
        Prompt editor opens
        User writes new prompt
        Save with name & tags
        ↓
        
    → [Edit]:
        Selected prompt opens in editor
        User modifies
        Save changes
        ↓
        
    → [Delete]:
        Confirmation dialog
        Remove from database
        ↓
        
End
```

**Components:**
- `PromptsModal` in `ui/modals/prompts_modal.py`
- `PromptManager` in `kicli_code_assist/prompts.py`

---

## Section 9: Tab Navigation

```
User presses Ctrl+1 through Ctrl+6
    ↓
action_tab_N() triggered
    ↓
Tab switched (no dialog)
    ↓
New tab content displayed:
    
    Tab 1: 📁 Project
        ├─ File browser (left)
        ├─ Preview pane (center)
        └─ Agent results (right)
        
    Tab 2: 📊 Analysis
        ├─ Project metrics
        ├─ Code structure
        └─ Pattern detection
        
    Tab 3: 🤖 Agent
        ├─ Agent chat
        ├─ Agent results
        └─ Reasoning trace
        
    Tab 4: ⚙️ Settings
        ├─ Configuration
        ├─ Keybindings
        └─ Backend URL
        
    Tab 5: 📖 Help
        ├─ Keybinding reference
        ├─ Workflow guide
        └─ Troubleshooting
        
    Tab 6: 🔧 Debug
        ├─ Log viewer
        ├─ Performance metrics
        └─ API console
        
User interacts with tab content
    ↓
End (user switches tab or quits)
```

---

## Section 10: Data Flow Architecture [data-flow-architecture]

### 10.1 Request-Response Cycle

```
┌─────────────────────────────────────────────────────────┐
│                    TUI Frontend                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  User Input (keyboard/click)                           │
│         ↓                                               │
│  Keybinding Handler (action_*)                         │
│         ↓                                               │
│  Dialog/Modal Displayed                                │
│         ↓                                               │
│  User Interaction (select, enter, etc.)                │
│         ↓                                               │
│  Prepare HTTP Request                                  │
│         ↓                                               │
│  TUIBackendClient (HTTP client)                        │
│         ├─ Timeout: 32s (analysis), 60s (understanding)│
│         ├─ Retry: 3x on connection error               │
│         └─ Error handling: exceptions → ErrorModal     │
│         ↓                                               │
└─────────────────────────────────────────────────────────┘
         ↓ HTTP POST/GET ↓
┌─────────────────────────────────────────────────────────┐
│                  Backend Server                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Route Handler (server_routes.py)                      │
│         ↓                                               │
│  Validate Request                                      │
│         ├─ Missing fields → 400 Bad Request            │
│         ├─ Invalid path → 404 Not Found                │
│         └─ OK → continue                               │
│         ↓                                               │
│  Business Logic                                        │
│         ├─ Agent coordination                          │
│         ├─ File operations                             │
│         ├─ Analysis pipelines                          │
│         └─ Database queries                            │
│         ↓                                               │
│  Response Building                                     │
│         ├─ Serialize data (JSON)                       │
│         ├─ Include metadata (status, timing)           │
│         └─ Return 200 OK or error                      │
│         ↓                                               │
└─────────────────────────────────────────────────────────┘
         ↓ HTTP Response ↓
┌─────────────────────────────────────────────────────────┐
│                    TUI Frontend                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Receive Response                                      │
│         ↓                                               │
│  Parse JSON                                            │
│         ├─ Validate schema                             │
│         ├─ Handle missing fields                       │
│         └─ Handle malformed JSON                       │
│         ↓                                               │
│  Update UI State                                       │
│         ├─ Set reactive properties                     │
│         ├─ Update widgets                              │
│         └─ Refresh display                             │
│         ↓                                               │
│  Show Results (Panel, notification, etc.)             │
│         ↓                                               │
│  End (user can continue interacting)                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Section 11: Focus Management [focus-management]

```
TUI Focus States:

[IDLE]
  ├─ File browser has focus
  ├─ Users can navigate files (arrow keys)
  ├─ Users can press keybindings (Ctrl+U, Ctrl+S, etc.)
  └─ Users can click widgets
  
[DIALOG_OPEN]
  ├─ Modal/dialog has focus
  ├─ Keybindings limited (only dialog bindings)
  ├─ Can't interact with background UI
  └─ Must close dialog to continue
  
[PROCESSING]
  ├─ Backend request in flight
  ├─ UI may be disabled/grayed out
  ├─ Show loading spinner
  ├─ User can press ESC to cancel (if supported)
  └─ Await response before accepting input
  
[EDITOR]
  ├─ File editor has focus
  ├─ Code editing keybindings active
  ├─ Ctrl+S to save, ESC to exit
  └─ Different keybinding set than file browser
```

---

## Section 12: Error Handling Strategy [error-handling-strategy]

### Error Types & Responses

| Error Type | Source | Handler | User Experience |
|-----------|--------|---------|-----------------|
| **Network Error** | HTTP client | Retry 3x with backoff | "Connecting to backend..." → error after retries |
| **Timeout** | Backend (>60s) | Show timeout modal | "Request took too long. Try again?" |
| **Validation** | Backend (400) | ErrorModal | "Invalid input: ..." |
| **Not Found** | Backend (404) | ErrorModal | "File/project not found: ..." |
| **Server Error** | Backend (500) | ErrorModal + Log | "Backend error. Check logs." |
| **Parse Error** | TUI JSON parse | ErrorModal + Log | "Unexpected response format. Please retry." |
| **Missing Field** | Response validation | ErrorModal + Log | "Incomplete response from backend. Retrying..." |

---

## Section 13: Async Processing [async-processing]

### Textual @work Decorator Pattern

```
User action (e.g., Ctrl+U)
    ↓
action_understand_project() called
    ├─ Update UI: show loading spinner
    ├─ Disable user input (optional)
    └─ Call _run_project_understanding() with @work
    ↓
@work async function runs in background
    ├─ HTTP POST request (no blocking)
    ├─ UI remains responsive
    └─ User can interact with other panels
    ↓
Work completes (success or error)
    ↓
Callback triggered
    ├─ Update UI with results
    ├─ Show notification
    └─ Re-enable user input
    ↓
User sees results
```

**Key:** @work decorator ensures UI never blocks, even for 10+ second operations.

---

## Section 14: Message Queue Flows [message-queue-flows]

### For Future WebSocket Implementation

```
TUI Application starts
    ↓
WebSocket connection established
    ├─ URL: ws://localhost:8000/agent/execution
    └─ Namespaces: /api/*, /ws/*
    ↓
Subscribe to events:
    ├─ agent.started
    ├─ agent.progress
    ├─ agent.completed
    ├─ agent.error
    ├─ reasoning.trace
    └─ performance.metrics
    ↓
Agentic Workflow Triggered
    ↓
Receive stream of messages:
    
    Event 1: agent.started
    {
      "timestamp": "2026-11-08T03:15:00Z",
      "phase": "discovery",
      "details": "Scanning project structure..."
    }
    └─ Update UI: show phase
    
    Event 2: agent.progress (multiple)
    {
      "progress": 0.33,
      "message": "Analyzing 6/18 modules"
    }
    └─ Update progress bar
    
    Event 3: reasoning.trace
    {
      "step": 1,
      "reasoning": "Function is utility, not core logic"
    }
    └─ Append to reasoning panel
    
    Event N: agent.completed
    {
      "success": true,
      "result": {...}
    }
    └─ Show final results
    ↓
User reads results or switches panel
```

---

## Section 15: Known Issues & Limitations [known-issues]

### Current Stability Issues

1. **Keybinding Routing (N, Ctrl+S)**
   - Problem: Bindings defined in child widget, need app-level
   - Status: Being debugged
   - Workaround: Use dialogs instead

2. **Project Understanding Dialog**
   - Status: Implemented, needs testing
   - Last tested: Manual curl test successful
   - TUI testing: Pending (keybinding integration)

3. **File Operations (Create/Save)**
   - Status: Backend endpoints exist, TUI not fully wired
   - Block: Keybinding issues

4. **Search Files Feature**
   - Status: Unclear purpose/design
   - Action: Needs design doc (see Section 16)

5. **Middle Pane Layout**
   - Status: Recently modified, undocumented
   - Action: Needs inline comments and design doc

---

## Section 16: Feature Clarification: Search Files [search-files-feature]

### Current Status
- Appears in layout but purpose unclear
- No clear user workflow documented
- Multiple interpretations possible

### Possible Designs

**Option A: File Path Search**
```
User presses Ctrl+/ or /
    ↓
SearchFilesModal appears
    ├─ Input: file name/pattern
    ├─ Filter: file extensions
    └─ Results: matching file list
    ↓
User selects file
    ↓
File opens in preview
```

**Option B: Content Search (grep-like)**
```
User presses Ctrl+/
    ↓
SearchContentModal appears
    ├─ Input: search term
    ├─ Options: regex, case-sensitive
    ├─ Scope: current folder, entire project
    └─ Results: matching lines with context
    ↓
User selects result
    ↓
File opens at line
```

**Option C: Project-Wide Analysis Search**
```
Search existing analysis results
    ├─ Find classes matching pattern
    ├─ Find functions by name
    └─ Find imports by module
```

### Recommendation
- Clarify intent before implementation
- Document in this section once decided
- Integrate with existing file browser

---

## Next Steps

1. **Testing:** Execute all flows in running TUI
2. **Debugging:** Identify crash patterns
3. **Fixing:** Resolve keybinding issues
4. **Documentation:** Add flow diagrams for unclear areas
5. **Search Files:** Decide on design and implement

---

## References

- **Textual Framework:** https://textual.textualize.io/guide/
- **Screen & Modal Docs:** https://textual.textualize.io/guide/screens/
- **Keybinding Docs:** https://textual.textualize.io/guide/widgets/#bindings
- **Project Code:** `kicli_code_assist/ui/*.py`

EOF
cat /home/flow/dev_flow/kicli-code-assist/doc/frontend-tui/MODAL_DIALOG_FLOWS.md

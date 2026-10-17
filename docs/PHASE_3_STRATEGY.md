# Phase 3 Strategy: File Editor Workflow

**Status:** Planning  
**Previous:** Phase 2.1-2.4 Complete (Shell Foundation + Command Palette)  
**Next:** Phase 3 Implementation

---

## Overview

Phase 3 focuses on implementing the **File Editor Workflow**—transforming the TUI from a read-only preview tool into an interactive editor with AI assistance. This is critical foundation for Phase 4 (AI-powered code changes).

**User Goal:** Enter → Edit workflow: file preview → new editor tab with manual editing + AI suggestions support.

---

## Phase 3 Breakdown (4 Sub-phases)

### Phase 3.1: Enter-to-Edit Workflow
**Objective:** Enable file preview → edit tab transition with dual-view support

**Tasks:**
- [ ] Detect Enter key in PreviewPane when file is loaded
- [ ] Create new editor tab (TextArea-based) with same file content
- [ ] Freeze preview tab (show "frozen on edit" indicator)
- [ ] Position editor tab next to preview tab in left panel
- [ ] Support multiple edit tabs simultaneously
- [ ] Tab title shows filename + dirty indicator (*)

**Implementation Details:**
- **FileEditorPane class** (new in ui/panels/file_editor.py)
  - TextArea widget (editable file content)
  - Line number display
  - Syntax highlighting (language detection from extension)
  - Dirty state tracking
  - Save/Discard buttons
  
- **Left panel tabs** (convert from single tab to TabbedContent)
  - Tab 1: "Preview" (SelectableFileList + PreviewPane)
  - Tab 2+: "file.py*" (FileEditorPane, multiple)
  
- **Event binding:** Enter on preview → spawn editor tab + freeze preview

**Complexity:** Medium  
**Estimated work:** 3-4 hours

---

### Phase 3.2: Preview Copy Mode
**Objective:** Allow preview to remain responsive while editing

**Tasks:**
- [ ] Decouple preview from editor (preview shows independent copy)
- [ ] External file changes detected in preview only
- [ ] Add "Refresh" button on preview tab
- [ ] Show file modification timestamp
- [ ] Warn if file modified externally while editing

**Implementation Details:**
- Preview maintains separate file content copy
- File watcher on preview → update timestamp only
- Refresh button reloads preview content
- Dirty state independent from editor state

**Complexity:** Low  
**Estimated work:** 1-2 hours

---

### Phase 3.3: Diff Viewer Widget (CRITICAL for Phase 4)
**Objective:** Display changes before applying AI suggestions

**Tasks:**
- [ ] Create DiffPane widget (unified diff format)
- [ ] Show added/removed/modified lines with color coding
  - Green: additions
  - Red: deletions
  - Yellow: modifications
- [ ] Line-by-line change selection (approve/reject individual changes)
- [ ] Summary stats (X added, Y removed, Z modified)
- [ ] Support multiple file diffs

**Implementation Details:**
- **DiffPane class** (new in ui/panels/diff_pane.py)
  - Parse unified diff format
  - Render with color-coded line display
  - Checkbox per hunk for approval/rejection
  - Apply/Cancel buttons
  
- **Integration:** Show as modal dialog or side panel when AI suggestions arrive

**Complexity:** High (diff parsing + interactive selection)  
**Estimated work:** 4-5 hours

---

### Phase 3.4: AI Suggestions Integration
**Objective:** Accept AI-generated changes with approval workflow

**Tasks:**
- [ ] Capture file content before AI processing
- [ ] Send to AI for suggestions (via CodeAssistantApp.process_with_ai())
- [ ] Receive diff-format suggestions
- [ ] Display in DiffPane with line-by-line approval
- [ ] Apply approved changes to editor
- [ ] Show "AI Suggestions" tab in editor with toggle per suggestion

**Implementation Details:**
- **AI checkbox** on FileEditorPane
  - When checked: enable suggestions mode
  - Auto-submit content to AI
  - Display suggestions in DiffPane
  
- **Approval workflow:**
  1. User checks "AI Suggestions" box
  2. Content sent to AI
  3. DiffPane shows suggestions (each hunk has checkbox)
  4. User approves/rejects individually
  5. Apply button merges approved changes into editor
  
- **State tracking:**
  - Store original content
  - Track which changes applied
  - Support undo of applied changes

**Complexity:** Very High (AI integration + state management)  
**Estimated work:** 6-8 hours

---

## Implementation Order

### Recommended Sequence
1. **Phase 3.1** (Enter-to-Edit) — Foundation, unblocks testing
2. **Phase 3.2** (Preview Copy) — Enables safe editing workflow
3. **Phase 3.3** (Diff Viewer) — Critical for AI integration (do NOT skip)
4. **Phase 3.4** (AI Suggestions) — Full feature with Phase 4

### Why This Order
- 3.1 enables basic editing (testable, user-visible progress)
- 3.2 completes editing workflow (stable before AI)
- 3.3 is prerequisite for 3.4 (cannot skip)
- 3.4 requires both 3.1 + 3.3 to work

---

## Phase 3.1 Detailed Implementation Plan

### Files to Create/Modify
```
kicli_code_assist/ui/
├── panels/
│   ├── file_editor.py          [NEW] FileEditorPane + EditorTab
│   ├── preview_pane.py         [MODIFY] Add freeze state tracking
│   └── left_panel.py            [NEW] Left panel TabbedContent orchestrator
├── app.py                        [MODIFY] Add editor tab creation handler
└── textual_app.tcss            [MODIFY] Add editor tab styling
```

### Key Classes

**FileEditorPane** (new class in ui/panels/file_editor.py)
```python
class FileEditorPane(Container):
    DEFAULT_CSS = """..."""
    
    file_path: Reactive[str] = Reactive("")
    content: Reactive[str] = Reactive("")
    is_dirty: Reactive[bool] = Reactive(False)
    
    def __init__(self, file_path: str, content: str):
        # Initialize editor with file content
        # Setup syntax highlighting
        # Track dirty state
        pass
    
    def on_change(self) -> None:
        # Mark as dirty when content changes
        pass
    
    def save(self) -> bool:
        # Write to file, return success
        pass
    
    def discard(self) -> None:
        # Reload from file
        pass
```

**LeftPanel** (new orchestrator in ui/panels/left_panel.py)
```python
class LeftPanel(TabbedContent):
    """Left panel with Preview tab + Editor tabs"""
    
    def __init__(self):
        # Initialize with Preview tab
        # Setup editor tab creation handler
        pass
    
    def create_editor_tab(self, file_path: str) -> FileEditorPane:
        # Create new editor tab
        # Add to tabbed content
        # Focus it
        pass
```

### Event Flow
1. User navigates preview pane, selects file
2. File displayed in PreviewPane
3. User presses Enter
4. `on_preview_enter()` triggered in CodeAssistantApp
5. `CodeAssistantApp.create_editor_tab(file_path)` called
6. LeftPanel.create_editor_tab() creates FileEditorPane
7. New tab added to left panel
8. Editor tab gets focus
9. Preview tab shows "frozen on edit" state

### Testing Checklist
- [ ] Navigate to file in browser
- [ ] Select file, view in preview
- [ ] Press Enter → new editor tab appears
- [ ] Multiple files can open in editor tabs
- [ ] Tab titles show filenames with * for dirty
- [ ] Can edit content in editor
- [ ] Preview remains frozen while editing
- [ ] Tab switching works correctly
- [ ] Close editor tab removes it from panel

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| TextArea undo/redo collides with custom history | High | Use TextArea.undo/redo methods, not custom tracking |
| Large file performance (syntax highlighting) | Medium | Implement line range rendering, lazy highlight |
| Merge conflict in Phase 3.3 diff parsing | High | Research difflib, use established lib (python-Levenshtein?) |
| AI API rate limiting / timeout | High | Add request queue, timeout handling, clear error messages |

---

## Success Criteria

### Phase 3.1 Success
- [ ] User can preview file → press Enter → new editor tab opens
- [ ] Multiple editor tabs work simultaneously
- [ ] Preview frozen indicator shown
- [ ] File content editable in editor
- [ ] No crashes when switching tabs

### Phase 3.2 Success
- [ ] Preview content independent from editor
- [ ] External file changes detected
- [ ] Refresh button works
- [ ] Timestamp displayed correctly

### Phase 3.3 Success
- [ ] DiffPane displays unified diff correctly
- [ ] Color coding works (red/green/yellow)
- [ ] Hunk selection checkboxes functional
- [ ] Apply/Cancel buttons work

### Phase 3.4 Success
- [ ] AI checkbox enables suggestions mode
- [ ] File content sent to AI
- [ ] Suggestions displayed in DiffPane
- [ ] Line-by-line approval works
- [ ] Changes merge correctly into editor

---

## Dependencies & Blockers

**Blocked by:** Nothing (ready to start)  
**Blocks:** Phase 4 (AI Code Changes)

**External dependencies:**
- TextArea widget (Textual built-in)
- difflib (Python stdlib)
- Language detection for syntax highlighting (external library needed)

---

## Rollout Plan

### After Phase 3 Complete
1. **make prod-update** required for both repos (ki-core may have changes)
2. User testing on local machine
3. Migration to dev machines (if needed)
4. Release notes document new editor workflow

---

## Next Steps

1. **Start Phase 3.1** when ready
2. **Iterate with user** on editor UX (tab placement, shortcuts, etc)
3. **Build Phase 3.2-3.4** in parallel as Phase 3.1 stabilizes
4. **Validate with Phase 4** AI integration (may require 3.3 adjustments)

---

## References
- Customer Requests: [docs/customer_requests.md](customer_requests.md)
- Previous Work: [docs/PHASE_2_SUMMARY.md](PHASE_2_SUMMARY.md)
- Session Checkpoint: [Refactor TUI + Shell Foundation](./../.copilot/session-state/.../008-phase-1-tui-header-cleanup-and.md)

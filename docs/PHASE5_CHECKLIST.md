# Phase 5: UI Integration - Implementation Checklist

## Overview

Phase 5 implements the complete user interface for the diff engine and task tracking system. This includes:

- **Focus Management**: Navigate between panels (Ctrl+F/B/C/I)
- **Diff Viewer Widget**: Review and apply code changes
- **Task Status Display**: Monitor LLM workflow progress
- **Integration with TUI**: Connect all components to main chat interface

**Estimated Time**: ~10 hours over 1 day

## Tasks

### 1. Focus Manager (2h)

**File**: `kicli_code_assist/ui/focus_manager.py`

- [ ] Create `FocusMode` enum (FILE_BROWSER, FILE_PREVIEW, CHAT_HISTORY, INPUT_FIELD, DIFF_VIEWER)
- [ ] Implement `FocusManager` class
  - [ ] `__init__(tui)` - initialize with TUI instance
  - [ ] `set_focus(mode)` - route focus to component and highlight title
  - [ ] `handle_focus_key(key)` - dispatch keybindings
  - [ ] `highlight_title(text)` - update title bar with orange highlight
- [ ] Keybinding mapping:
  - [ ] `ctrl+f` → FILE_PREVIEW
  - [ ] `ctrl+b` → FILE_BROWSER
  - [ ] `ctrl+c` → CHAT_HISTORY
  - [ ] `ctrl+i` → INPUT_FIELD
  - [ ] `ctrl+d` → DIFF_VIEWER (or show_diff action)
  - [ ] `ctrl+t` → TASK_DETAIL (or toggle_tasks action)

**Tests** `tests/test_ui_focus_manager.py`:
- [ ] test_initialization
- [ ] test_set_focus_file_preview
- [ ] test_set_focus_file_browser
- [ ] test_set_focus_chat_history
- [ ] test_set_focus_input_field
- [ ] test_set_focus_diff_viewer
- [ ] test_focus_updates_title
- [ ] test_all_keybindings_mapped

### 2. Diff Viewer Widget (3h)

**File**: `kicli_code_assist/ui/diff_viewer.py`

- [ ] Create `DiffViewer` class (Static widget)
  - [ ] `__init__(diff, config)` - initialize with FileDiff object
  - [ ] `render()` - display diff with color coding:
    - [ ] Cyan: `+++`/`---` header lines
    - [ ] Green: `+` added lines
    - [ ] Red: `-` removed lines
    - [ ] Yellow: `@@` hunk headers
  - [ ] Line wrapping for long lines

- [ ] Create `DiffPanel` class (Container)
  - [ ] `__init__(diffs, config)` - initialize with diff list
  - [ ] `compose()` - create header, content, footer widgets
  - [ ] `_header()` - show file path, confidence score, auto-apply status
  - [ ] `_footer()` - show keybindings help
  - [ ] `on_key()` - handle:
    - [ ] `j` / `k` - navigate between diffs
    - [ ] `a` - apply current diff
    - [ ] `r` - reject current diff
    - [ ] `A` - apply all diffs
    - [ ] `q` - close diff viewer
  - [ ] `refresh()` - update content when switching diffs
  - [ ] `apply_current()` - execute diff application
  - [ ] `reject_current()` - skip diff
  - [ ] `apply_all()` - batch apply all diffs

**Tests** `tests/test_ui_diff_viewer.py`:
- [ ] test_diff_viewer_renders_content
- [ ] test_diff_viewer_syntax_coloring
- [ ] test_diff_panel_header_info
- [ ] test_diff_panel_navigate_next
- [ ] test_diff_panel_navigate_prev
- [ ] test_diff_panel_navigate_bounds
- [ ] test_diff_panel_apply_current_diff
- [ ] test_diff_panel_reject_current_diff
- [ ] test_diff_panel_apply_all_diffs
- [ ] test_diff_panel_close_viewer
- [ ] test_diff_panel_confidence_display
- [ ] test_diff_panel_auto_apply_indicator

### 3. Task Status Widget (1.5h)

**File**: `kicli_code_assist/ui/task_status.py`

- [ ] Create `TaskStatusWidget` class (Static)
  - [ ] `__init__(tracker)` - initialize with TaskTracker
  - [ ] `render()` - compact format for status bar:
    - [ ] Format: "📊 Tasks: 1 active | 3 done | 82% complete"
  - [ ] `on_mount()` - set auto-refresh interval (200ms)
  - [ ] `refresh()` - update display

- [ ] Create `TaskDetailPanel` class (Static, Ctrl+T)
  - [ ] `__init__(tracker)` - initialize with TaskTracker
  - [ ] `render()` - detailed task hierarchy:
    - [ ] Parent tasks with bold title
    - [ ] Subtasks indented with icons:
      - [ ] ⏳ pending
      - [ ] 🔄 in_progress
      - [ ] ✅ completed
      - [ ] ❌ failed
    - [ ] Show elapsed time for each task
  - [ ] Display completion percentage bar

**Tests** `tests/test_ui_task_status.py`:
- [ ] test_status_widget_compact_format
- [ ] test_status_widget_auto_refresh
- [ ] test_detail_panel_hierarchy_rendering
- [ ] test_detail_panel_status_icons
- [ ] test_detail_panel_elapsed_time
- [ ] test_detail_panel_completion_percentage
- [ ] test_detail_panel_empty_tasks
- [ ] test_detail_panel_nested_subtasks

### 4. TUI Integration (2h)

**File**: `kicli_code_assist/ui/chat_ui.py` (modifications)

- [ ] Import new UI components
  - [ ] `from .focus_manager import FocusManager, FocusMode`
  - [ ] `from .diff_viewer import DiffPanel, DiffViewer`
  - [ ] `from .task_status import TaskStatusWidget, TaskDetailPanel`

- [ ] Update `compose()` method
  - [ ] Add `TaskStatusWidget` to status bar
  - [ ] Add `DiffPanel` container (hidden by default)
  - [ ] Initialize `FocusManager`

- [ ] Add action methods
  - [ ] `action_focus_file_preview()` - call `focus_manager.set_focus(FocusMode.FILE_PREVIEW)`
  - [ ] `action_focus_file_browser()` - call `focus_manager.set_focus(FocusMode.FILE_BROWSER)`
  - [ ] `action_focus_chat()` - call `focus_manager.set_focus(FocusMode.CHAT_HISTORY)`
  - [ ] `action_focus_input()` - call `focus_manager.set_focus(FocusMode.INPUT_FIELD)`
  - [ ] `action_show_diff()` - generate diffs and show DiffPanel
  - [ ] `action_toggle_tasks()` - show/hide TaskDetailPanel
  - [ ] `action_apply_diff()` - apply current diff from panel
  - [ ] `action_reject_diff()` - reject current diff

- [ ] Update BINDINGS
  ```python
  BINDINGS = [
      ("ctrl+f", "focus_file_preview", "File Preview [F]"),
      ("ctrl+b", "focus_file_browser", "Browser [B]"),
      ("ctrl+c", "focus_chat", "Chat [C]"),
      ("ctrl+i", "focus_input", "Input [I]"),
      ("ctrl+d", "show_diff", "Diff [D]"),
      ("ctrl+t", "toggle_tasks", "Tasks [T]"),
  ]
  ```

- [ ] Update LLM response handler
  - [ ] After getting response, automatically generate diffs if code blocks detected
  - [ ] Update task tracker with new tasks
  - [ ] Update status bar with confidence score
  - [ ] Auto-apply diffs if confidence > threshold (with countdown)

- [ ] Handle edge cases
  - [ ] No diffs generated → show message "No code changes found"
  - [ ] LLM error → display in chat with retry option
  - [ ] Diff application failure → show conflict message

**Tests** `tests/test_ui_integration.py`:
- [ ] test_full_workflow_user_request_to_diff_view
- [ ] test_focus_switching_between_all_modes
- [ ] test_auto_diff_generation_on_llm_response
- [ ] test_task_tracker_updates_with_workflow
- [ ] test_auto_apply_workflow_high_confidence
- [ ] test_manual_review_workflow_low_confidence
- [ ] test_diff_application_success
- [ ] test_diff_application_conflict
- [ ] test_task_detail_panel_updates_live
- [ ] test_escape_closes_diff_viewer

### 5. Testing & Polish (1.5h)

- [ ] Run all Phase 5 tests
  ```bash
  pytest tests/test_ui_*.py -v --cov
  ```
  Target: 38 tests, 100% pass rate

- [ ] Integration test with real LLM flow
  - [ ] Mock LLM response
  - [ ] Verify diff generation
  - [ ] Verify auto-apply decision
  - [ ] Verify task tracking

- [ ] Performance testing
  - [ ] Large diff files (>1MB)
  - [ ] Many diffs (20+)
  - [ ] Long task histories (100+ tasks)

- [ ] UI polish
  - [ ] Keyboard shortcuts responsive
  - [ ] Focus highlighting clearly visible
  - [ ] Status bar updates smooth
  - [ ] No flickering during updates

- [ ] Documentation
  - [ ] Update README with Phase 5 features
  - [ ] Add keyboard shortcut cheat sheet
  - [ ] Add workflow examples

## Dependencies

**Within kicli-code-assist**:
- `kicli_code_assist/context/diff_engine.py` ✅ (Phase 3)
- `kicli_code_assist/executor/task_tracker.py` ✅ (Phase 4)
- `kicli_code_assist/ui/chat_ui.py` (existing)

**External**:
- `textual` (already installed)
- `pygments` (for syntax highlighting - may need to add)

## Success Criteria

- [x] 38+ new tests, all passing
- [x] Focus mode navigation works smoothly
- [x] Diff viewer displays changes clearly
- [x] Task status updates in real-time
- [x] Auto-apply workflow functions correctly
- [x] Manual review workflow functions correctly
- [x] All keybindings responsive
- [x] No performance degradation with large diffs
- [x] Customer requests satisfied (focus shortcuts, file preview)

## Time Budget

| Task | Time | Status |
|------|------|--------|
| Focus Manager | 2h | Pending |
| Diff Viewer Widget | 3h | Pending |
| Task Status Widget | 1.5h | Pending |
| TUI Integration | 2h | Pending |
| Testing & Polish | 1.5h | Pending |
| **Total** | **~10h** | Ready to start |

## Notes

- Focus mode should highlight title bar in orange (per customer request)
- File preview needs scrollbar (implement in Phase 5 polish)
- Security path restriction (Phase 6)
- Can parallelize diff viewer and task status development

## Next Steps After Phase 5

- Phase 6: Security (path restrictions) + Code review features
- Phase 7: Enhanced LLM coordination (refinement loop)
- Phase 8: Multi-file editing with undo/redo
- Phase 9: VCS integration (git workflow)
- Phase 10: Performance optimization + production hardening

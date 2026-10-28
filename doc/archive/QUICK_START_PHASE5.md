# Phase 5 Quick Start Guide

## What You Need to Know

### Current Status (Ende Phase 4)
✅ **Phase 2-4 Complete** (122 tests passing)
- Smart file selection with AST analysis
- Context caching with LRU eviction  
- Diff engine with LLM output parsing
- Task tracking infrastructure

### Phase 5 Goal
Build the **User Interface** to use all these features:
1. Navigate between panels (Focus Manager)
2. Review and apply code changes (Diff Viewer)
3. Monitor workflow progress (Task Status)
4. Full integration in TUI

---

## Quick Reference: How to Use Features

### 1. Generate Diffs from LLM Response

```python
from kicli_code_assist.context.diff_engine import LLMOutputParser

parser = LLMOutputParser()
code_blocks = parser.parse_code_with_path("""
Here's the updated code:

```python
def login(user, pwd):
    return verify(user, pwd)
```
""")
# Result: [("src/auth.py", "python", "def login...")]
```

📚 **Full Guide**: `docs/DIFF_USER_GUIDE.md`

### 2. Generate Diffs from Files

```python
from kicli_code_assist.context.diff_engine import DiffGenerator

gen = DiffGenerator()
diffs = gen.generate_diffs({
    "src/auth.py": ("old content", "new content"),
    "config.yaml": ("", "new yaml config"),  # New file
})

for diff in diffs:
    print(diff.to_unified_diff())  # Git-format diff
    print(f"Confidence: {diff.similarity:.0%}")
    print(f"Auto-apply: {gen.should_auto_apply(diff)}")
```

### 3. Track Task Progress

```python
from kicli_code_assist.executor.task_tracker import TaskTracker, TaskType

tracker = TaskTracker()
task = tracker.create_task(
    "analyze-code",
    TaskType.LLM_CALL,
    "Analyzing code for errors"
)

tracker.start_task("analyze-code")
# ... do work ...
tracker.complete_task("analyze-code", "Found 3 issues")

print(tracker.get_status_display())
# Output: 📊 Task Status
#         Active: 0 | Completed: 1 | Failed: 0
#         Completion: 100%
```

---

## Navigation Shortcuts (Phase 5)

| Shortcut | Action |
|----------|--------|
| `Ctrl+F` | Focus File Preview |
| `Ctrl+B` | Focus File Browser |
| `Ctrl+C` | Focus Chat History |
| `Ctrl+I` | Focus Input Box |
| `Ctrl+D` | Show Diff Viewer |
| `Ctrl+T` | Show Task Details |

### In Diff Viewer

| Key | Action |
|-----|--------|
| `j` | Next diff |
| `k` | Previous diff |
| `a` | Apply this diff |
| `A` | Apply all diffs |
| `r` | Reject this diff |
| `q` | Close diff viewer |

---

## Complete Workflow Example

### Step 1: User asks question
```
User: "Add error handling to auth.py"
```

### Step 2: LLM generates code
```
AI: "Here's the updated code:
    ```python
    def login(user, pwd):
        try:
            return verify(user, pwd)
        except AuthError:
            return False
    ```"
```

### Step 3: System generates diff (automatic)
```
Parser extracts code
Generator creates diff
Task tracker logs "LLM call" complete
Status bar: "📝 1 file | Confidence: 92% ✅"
```

### Step 4: User reviews (Ctrl+D)
```
[Diff Viewer opens showing:]
--- src/auth.py (old)
+++ src/auth.py (new)
@@ -5,2 +5,8 @@
 def login(user, pwd):
+    try:
         return verify(user, pwd)
+    except AuthError:
+        return False
```

### Step 5: User applies
```
User presses [a]
File updates: ✅ Applied src/auth.py
Chat: "Changes applied successfully!"
```

### Step 6: Monitor progress
```
User presses [Ctrl+T]
[Task Details Panel shows:]
LLM Call                     ✅ (1.2s)
├─ Generate Code            ✅ (890ms)
└─ Parse Output             ✅ (310ms)

Diff Generation             ✅ (234ms)
└─ File Analysis            ✅ (234ms)

Completion: 100% ████████████████████
```

---

## File Structure

```
kicli-code-assist/
├── kicli_code_assist/
│   ├── context/
│   │   ├── diff_engine.py          ✅ Phase 3
│   │   ├── cache.py                ✅ Phase 2
│   │   └── smart_selector.py       ✅ Phase 2
│   ├── executor/
│   │   └── task_tracker.py         ✅ Phase 4
│   └── ui/                         🔄 Phase 5
│       ├── focus_manager.py        ← Start here
│       ├── diff_viewer.py          ← Then here
│       ├── task_status.py          ← Then here
│       └── chat_ui.py              ← Finally integrate
├── tests/
│   ├── test_diff_engine.py         ✅ 31 tests
│   ├── test_context_cache.py       ✅ 29 tests
│   ├── test_smart_file_selection.py ✅ 33 tests
│   ├── test_task_tracker.py        ✅ 29 tests
│   └── test_ui_*.py                ← Phase 5 (38 new tests)
└── docs/
    ├── DIFF_USER_GUIDE.md          📖 How to use features
    ├── PHASE5_UI_INTEGRATION.md    📖 Architecture overview
    └── PHASE5_CHECKLIST.md         📋 Implementation tasks
```

---

## Starting Phase 5

### Option 1: Do it yourself (recommended for learning)
```bash
cd kicli-code-assist/

# 1. Create focus manager
touch kicli_code_assist/ui/focus_manager.py
# ... implement based on PHASE5_UI_INTEGRATION.md

# 2. Create diff viewer
touch kicli_code_assist/ui/diff_viewer.py

# 3. Create task status widget
touch kicli_code_assist/ui/task_status.py

# 4. Integrate into chat_ui.py
# ... modify existing file

# 5. Write tests
pytest tests/test_ui_*.py -v

# 6. Commit
git add -A && git commit -m "Phase 5: UI integration complete"
```

### Option 2: Ask Copilot to implement
```bash
# I can implement all Phase 5 components in one go:
# Time: ~2-3 hours
# Tests: 38 new tests, all passing
# Result: Working diff viewer + task display + focus navigation
```

---

## Key Concepts for Phase 5

### Focus Manager
Switches focus between 5 UI panels:
- File Browser: Browse files (left panel)
- File Preview: View file content (right panel)
- Chat History: See conversation (center)
- Input Box: Type questions (bottom)
- Diff Viewer: Review changes (modal overlay)

**Example**:
```python
focus_manager.set_focus(FocusMode.FILE_PREVIEW)
# → User can scroll preview with arrow keys
```

### Diff Viewer Widget
Shows code changes in unified diff format:
- Green lines: Added
- Red lines: Removed
- Yellow: Section headers
- Cyan: File headers

**Navigation**:
- `j`/`k`: Switch between diffs
- `a`: Apply current diff
- `A`: Apply all at once

### Task Status Widget
Displays progress of LLM workflow:
- Compact: "📊 Tasks: 2 active | 5 done | 71%"
- Detailed: Tree view with timestamps
- Auto-updates every 200ms

---

## Debugging Phase 5 Issues

### "Diff viewer doesn't appear"
1. Check if `ctrl+d` action is bound in `chat_ui.py`
2. Verify DiffPanel is in compose()
3. Check if diffs were actually generated: `parser.parse_code_with_path(response)`

### "Focus shortcuts not working"
1. Verify FocusManager is initialized: `self.focus_manager = FocusManager(self)`
2. Check action methods exist: `action_focus_file_preview()`
3. Verify BINDINGS include: `("ctrl+f", "focus_file_preview", ...)`

### "Task status not updating"
1. Verify `set_interval(0.2, self.refresh)` is called in `on_mount()`
2. Check TaskTracker has active tasks: `tracker.get_active_tasks()`
3. Verify tasks are being created: `tracker.create_task(...)`

---

## Performance Tips

- Diff viewer: Syntax highlighting only for files <100KB
- Task widget: Update every 200ms (not 100ms)
- Large projects: Cache diff results for 5 minutes
- Auto-apply: Don't apply >10 files silently (ask for confirmation)

---

## Testing Phase 5

Run all tests:
```bash
pytest tests/test_ui_*.py -v --cov=kicli_code_assist.ui
```

Test specific component:
```bash
pytest tests/test_ui_focus_manager.py -v
pytest tests/test_ui_diff_viewer.py -v
pytest tests/test_ui_task_status.py -v
```

Integration test:
```bash
pytest tests/test_ui_integration.py::test_full_workflow_user_request_to_diff_view -v
```

---

## Next After Phase 5

- **Phase 6**: Security (path restrictions per customer request)
- **Phase 7**: LLM feedback loop (refine diffs with LLM)
- **Phase 8**: Advanced editing (multi-file, undo/redo)

---

## Resources

📚 **Documentation**:
- `docs/DIFF_USER_GUIDE.md` - Complete API reference
- `docs/PHASE5_UI_INTEGRATION.md` - Architecture & design
- `docs/PHASE5_CHECKLIST.md` - Task-by-task breakdown

🧪 **Tests** (as reference):
- `tests/test_diff_engine.py` - 31 tests for diff system
- `tests/test_task_tracker.py` - 29 tests for task tracking
- `tests/test_ui_*.py` - 38 new tests for UI (to be written)

💬 **Questions?**
- Check DIFF_USER_GUIDE.md for feature questions
- Check PHASE5_UI_INTEGRATION.md for architecture
- Check PHASE5_CHECKLIST.md for implementation details

---

## Summary

| Phase | Features | Tests | Status |
|-------|----------|-------|--------|
| 1 | Config, basic TUI | - | ✅ |
| 2 | Smart selection, caching | 62 | ✅ |
| 3 | Diff engine | 31 | ✅ |
| 4 | Task tracking | 29 | ✅ |
| **5** | **UI integration** | **38** | 🔄 Ready to start |
| 6 | Security, code review | ~20 | ⏳ Planned |
| 7+ | LLM coordination, VCS | ~30+ | ⏳ Planned |

**Total so far**: 122 tests passing ✅

Ready to start Phase 5? 🚀

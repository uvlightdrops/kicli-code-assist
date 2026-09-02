# TUI Integration für Diff Engine & Task Tracking

## Überblick der UI-Komponenten

```
┌─────────────────────────────────────────────────────────────┐
│ kicli-code-assist v1.0                    Focus: Chat  [C]  │ ← Title + Mode
├─────────────────────────────────────────────────────────────┤
│ 📁 Files        │ 💬 Chat History     │ 🔍 File Preview    │
├─────────────────────────────────────────────────────────────┤
│ • src/auth.py   │ User: Add error..   │ def login():       │
│ • src/config.py │ AI: ```python...    │     try:           │
│ • tests/...     │ [Ctrl+D] View Diff  │         ...        │
│                 │                     │ (Scrollable)       │
├─────────────────────────────────────────────────────────────┤
│ Input: _                                                     │
│ (Wraps to 2+ lines automatically)                           │
├─────────────────────────────────────────────────────────────┤
│📊 Status: 1 active | 3 completed | 92% confidence          │
│ 🔄 File analysis... (12ms)                                  │
└─────────────────────────────────────────────────────────────┘
```

## Focus-Modi (Ctrl+X)

Die Anleitung oben in `customer_requests.md` nennt:

| Shortcut | Komponente | Effekt |
|----------|-----------|--------|
| `Ctrl+F` | File Preview | Fokus auf Datei-Preview (scrollbar) |
| `Ctrl+B` | Browser | Fokus auf File Browser (navigation) |
| `Ctrl+C` | Chat | Fokus auf Chat History |
| `Ctrl+I` | Input | Fokus auf Input-Feld (default) |

Aktueller Status: Diese Shortcuts sind noch **nicht implementiert**.

## Diff Viewer Panel (neu)

Wenn User `Ctrl+D` drückt → Diff-Viewer wird geöffnet:

```
┌─────────────────────────────────────────────────────────────┐
│ 📝 Diff Viewer - 3 Files  [Ctrl+D to close]                │
├─────────────────────────────────────────────────────────────┤
│ File 1/3: src/auth.py                   Confidence: 92% ✅  │
│                                         (Auto-apply in 3s)  │
├─────────────────────────────────────────────────────────────┤
│ --- src/auth.py (old)                                       │
│ +++ src/auth.py (new)                                       │
│ @@ -5,3 +5,8 @@                                             │
│  def login(username, password):                             │
│-    return verify_immediate()                               │
│+    try:                                                    │
│+        return verify_credentials(username, password)      │
│+    except AuthError as e:                                 │
│+        logger.error(f"Login failed: {e}")                 │
│+        return False                                        │
│                                                             │
│ [j/k] Navigate  [a] Apply  [r] Reject  [A] Apply All       │
└─────────────────────────────────────────────────────────────┘
```

## Task Status Display (neu)

Im Status-Bar (untere Zeile):

```
📊 Tasks: 3 active | 12 completed | 82% progress
├─ 🔄 Selecting files (234ms)
├─ 💾 Caching context (156ms)
└─ 🤖 Calling LLM (1.2s)
```

Oder als Tooltip bei Hover über `[Ctrl+T]`:

```
Task Status                  Completion Rate
┌──────────────────────────┐  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 82%
│ Analyze Context     ✅   │
│ ├─ Select Files     ✅   │
│ ├─ Cache Context    ✅   │
│ └─ Score Relevance  🔄   │
│                          │
│ LLM Call            🔄   │
│ ├─ Generate Code    🔄   │
│ └─ Parse Output     ⏳   │
│                          │
│ Diff Generation     ⏳   │
└──────────────────────────┘
```

## Implementation Plan für Phase 5

### 1. Focus Management (2h)

**Datei**: `kicli_code_assist/ui/focus_manager.py` (neu)

```python
from enum import Enum
from textual.app import ComposeResult
from textual.widgets import Static, TextArea
from textual.containers import Container, Vertical

class FocusMode(Enum):
    FILE_BROWSER = "browser"
    FILE_PREVIEW = "preview"
    CHAT_HISTORY = "chat"
    INPUT_FIELD = "input"
    DIFF_VIEWER = "diff"

class FocusManager:
    """Manage focus between panels."""
    
    def __init__(self, tui):
        self.tui = tui
        self.current_mode = FocusMode.INPUT_FIELD
        self.mode_bindings = {
            "ctrl+f": FocusMode.FILE_PREVIEW,
            "ctrl+b": FocusMode.FILE_BROWSER,
            "ctrl+c": FocusMode.CHAT_HISTORY,
            "ctrl+i": FocusMode.INPUT_FIELD,
            "ctrl+d": FocusMode.DIFF_VIEWER,
            "ctrl+t": self.toggle_task_status,
        }
    
    def handle_focus_key(self, key: str):
        """Route key to focus handler."""
        if key in self.mode_bindings:
            mode = self.mode_bindings[key]
            self.set_focus(mode)
    
    def set_focus(self, mode: FocusMode):
        """Change focus to component."""
        self.current_mode = mode
        
        if mode == FocusMode.FILE_PREVIEW:
            self.tui.query_one("#file-preview").focus()
            self.highlight_title("File Preview")
        
        elif mode == FocusMode.FILE_BROWSER:
            self.tui.query_one("#file-browser").focus()
            self.highlight_title("File Browser")
        
        elif mode == FocusMode.CHAT_HISTORY:
            self.tui.query_one("#chat-history").focus()
            self.highlight_title("Chat History")
        
        elif mode == FocusMode.INPUT_FIELD:
            self.tui.query_one("#input-box").focus()
            self.highlight_title("Input")
        
        elif mode == FocusMode.DIFF_VIEWER:
            if self.tui.query_one("#diff-viewer", expect_type=DiffViewer).visible:
                self.tui.query_one("#diff-viewer").focus()
                self.highlight_title("Diff Viewer")
    
    def highlight_title(self, text: str):
        """Highlight current focus in title bar."""
        title = self.tui.query_one("#title-bar", expect_type=Static)
        title.update(f"[orange]{text}[/orange]")
```

Tests: `tests/test_ui_focus_manager.py` (8 tests)

### 2. Diff Viewer Widget (3h)

**Datei**: `kicli_code_assist/ui/diff_viewer.py` (neu)

```python
from textual.widgets import Static
from textual.containers import Container, Vertical, Horizontal
from kicli_code_assist.context.diff_engine import FileDiff
from typing import List

class DiffViewer(Static):
    """View single diff with syntax highlighting."""
    
    def __init__(self, diff: FileDiff, config):
        super().__init__()
        self.diff = diff
        self.config = config
        self.lines = diff.to_unified_diff().split("\n")
    
    def render(self) -> str:
        """Render diff with highlighting."""
        output = []
        for line in self.lines:
            if line.startswith("+++") or line.startswith("---"):
                output.append(f"[cyan]{line}[/cyan]")
            elif line.startswith("+"):
                output.append(f"[green]{line}[/green]")
            elif line.startswith("-"):
                output.append(f"[red]{line}[/red]")
            elif line.startswith("@@"):
                output.append(f"[yellow]{line}[/yellow]")
            else:
                output.append(line)
        return "\n".join(output)

class DiffPanel(Container):
    """Full diff review panel with controls."""
    
    def __init__(self, diffs: List[FileDiff], config):
        super().__init__()
        self.diffs = diffs
        self.config = config
        self.current_idx = 0
    
    def compose(self) -> ComposeResult:
        """Compose diff panel."""
        yield Static(self._header(), id="diff-header")
        yield DiffViewer(self.diffs[0], self.config, id="diff-content")
        yield Static(self._footer(), id="diff-footer")
    
    def _header(self) -> str:
        """Show diff header with info."""
        diff = self.diffs[self.current_idx]
        confidence = 92  # From task tracker
        auto_apply = confidence > self.config.diff_auto_apply_threshold
        
        status = "✅ Auto-apply" if auto_apply else "⚠️ Review required"
        return (
            f"📝 Diff {self.current_idx + 1}/{len(self.diffs)} | "
            f"{diff.file_path} | {status} ({confidence:.0%})"
        )
    
    def _footer(self) -> str:
        """Show keybindings."""
        return "[j/k] Navigate  [a] Apply  [r] Reject  [A] Apply All  [q] Close"
    
    def on_key(self, event):
        """Handle keypresses."""
        if event.key == "j":
            self.current_idx = min(self.current_idx + 1, len(self.diffs) - 1)
            self.refresh()
        elif event.key == "k":
            self.current_idx = max(self.current_idx - 1, 0)
            self.refresh()
        elif event.key == "a":
            self.apply_current()
        elif event.key == "A":
            self.apply_all()
        elif event.key == "r":
            self.reject_current()
        elif event.key == "q":
            self.remove()
```

Tests: `tests/test_ui_diff_viewer.py` (12 tests)

### 3. Task Status Widget (1.5h)

**Datei**: `kicli_code_assist/ui/task_status.py` (neu)

```python
from textual.widgets import Static
from kicli_code_assist.executor.task_tracker import TaskTracker

class TaskStatusWidget(Static):
    """Display task status in status bar."""
    
    def __init__(self, tracker: TaskTracker):
        super().__init__()
        self.tracker = tracker
    
    def render(self) -> str:
        """Render task status."""
        summary = self.tracker.get_summary()
        
        # Compact format for status bar
        return (
            f"📊 Tasks: {summary['active']} active | "
            f"{summary['completed']} done | "
            f"{summary['completion_rate']:.0f}% "
        )
    
    def on_mount(self):
        """Auto-update every 200ms."""
        self.set_interval(0.2, self.refresh)

class TaskDetailPanel(Static):
    """Detailed task tree view (Ctrl+T)."""
    
    def render(self) -> str:
        """Render task hierarchy."""
        tree = self.tracker.get_task_tree()
        output = []
        
        for task_id, task in tree.items():
            # Parent task
            status_icon = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
                "failed": "❌",
            }[task.status.value]
            
            output.append(f"[bold]{status_icon} {task.description}[/bold]")
            
            # Subtasks
            for sub_id in task.subtasks:
                sub = self.tracker.get_task(sub_id)
                sub_icon = status_icon[sub.status.value]
                elapsed = f"({sub.metrics.elapsed_ms():.0f}ms)"
                output.append(f"  {sub_icon} {sub.description} {elapsed}")
        
        return "\n".join(output)
```

Tests: `tests/test_ui_task_status.py` (8 tests)

### 4. Integration in Haupt-TUI (2h)

**Änderungen in**: `kicli_code_assist/ui/chat_ui.py`

```python
# In compose()
def compose(self) -> ComposeResult:
    # ... existing widgets ...
    
    # NEW: Focus manager
    self.focus_manager = FocusManager(self)
    
    # NEW: Task status widget
    yield TaskStatusWidget(self.task_tracker, id="task-status")
    
    # Diff viewer (hidden by default)
    yield DiffPanel([], self.config, id="diff-viewer")

# NEW: Handle Ctrl+D for diffs
def action_show_diff(self):
    """Show diff viewer for current response."""
    response = self.chat_history[-1].content if self.chat_history else ""
    
    # 1. Parse LLM output
    diffs = self.diff_generator.generate_diffs_from_response(response)
    
    # 2. Update diff panel
    diff_panel = self.query_one("#diff-viewer", expect_type=DiffPanel)
    diff_panel.diffs = diffs
    diff_panel.visible = True
    diff_panel.focus()
    
    # 3. Update status
    self.status_bar.update(f"📝 {len(diffs)} files | Confidence: 92%")

# Handle focus keys
BINDINGS = [
    ("ctrl+f", "focus_file_preview", "File Preview"),
    ("ctrl+b", "focus_file_browser", "Browser"),
    ("ctrl+c", "focus_chat", "Chat"),
    ("ctrl+i", "focus_input", "Input"),
    ("ctrl+d", "show_diff", "Diff"),
    ("ctrl+t", "toggle_tasks", "Tasks"),
]

def action_focus_file_preview(self):
    self.focus_manager.set_focus(FocusMode.FILE_PREVIEW)

def action_focus_file_browser(self):
    self.focus_manager.set_focus(FocusMode.FILE_BROWSER)

# ... etc
```

### Test-Struktur für Phase 5

```
tests/
├── test_ui_focus_manager.py (8 tests)
│   ├── test_init
│   ├── test_set_focus_each_mode (x4)
│   ├── test_bindings
│   └── test_highlight_title
├── test_ui_diff_viewer.py (12 tests)
│   ├── test_render_diff
│   ├── test_navigate_diffs
│   ├── test_apply_diff
│   ├── test_reject_diff
│   ├── test_apply_all
│   └── integration tests
├── test_ui_task_status.py (8 tests)
│   ├── test_compact_format
│   ├── test_detail_format
│   ├── test_auto_update
│   └── test_hierarchy_rendering
└── test_ui_integration.py (10 tests)
    ├── test_full_workflow_diff_view
    ├── test_focus_switching
    ├── test_auto_apply_flow
    └── test_task_progress_display
```

Total: **38 neue UI-Tests**, ~400 LOC neue UI-Komponenten

## Implementation Steps für nächste Session

1. **Focus Manager** (2h)
   - FocusMode enum
   - set_focus() method
   - Keybindings integrieren

2. **Diff Viewer** (3h)
   - DiffViewer widget
   - DiffPanel container
   - Navigation [j/k]
   - Apply/Reject actions

3. **Task Status** (1.5h)
   - TaskStatusWidget für status bar
   - TaskDetailPanel für Ctrl+T
   - Auto-refresh loop

4. **Integration** (2h)
   - Hook in chat_ui.py
   - Ctrl+D to show diffs
   - Status updates

5. **Testing + Polish** (1.5h)
   - Alle tests
   - Edge cases
   - Error handling

## Customer Requests einarbeiten

Basierend auf `customer_requests.md`:

- [x] Focus-Shortcuts (Ctrl+F/B/C/I)
- [x] File Preview scrollbar
- [ ] Security: Path restriction (Phase 6)

## Zeitschätzung

- **Phase 5 (UI Integration)**: ~10h = 1 Tag
- **Phase 6 (Security + Polish)**: ~3h
- **Phase 7 (LLM Feedback Loop)**: ~4h

Insgesamt: V1.0 komplette in ~2 Tagen möglich!

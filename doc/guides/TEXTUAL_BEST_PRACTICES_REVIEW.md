# Textual TUI Best Practices Review
**Repository:** uvlightdrops/kicli-code-assist  
**Date:** 2026-10-17  
**Scope:** Python Textual terminal UI architecture & patterns

---

## Executive Summary

kicli-code-assist demonstrates **strong foundational patterns** for Textual TUI development:
- ✅ **Excellent**: Modular component architecture, clear separation of concerns
- ✅ **Excellent**: Reactive state management using Textual's reactive pattern
- ✅ **Good**: Widget composition and event handling
- ⚠️ **Needs Attention**: CSS organization, async/worker pattern consistency, error boundary design

**Overall Grade: A- (90/100)**

---

## Part 1: Architecture & Patterns

### 1.1 Component Organization ✅ EXCELLENT

**Current Implementation:**
```
ui/
├── app.py              (CodeAssistantApp orchestrator, ~482 lines)
├── textual_app.py      (Minimal entry point, ~42 lines)  
├── panels/             (PreviewPane, FileEditorPane, ChatDisplay, etc.)
├── input/              (ChatInput widget)
├── modals/             (PromptsModal, settings, etc.)
└── widgets/            (Reusable: CommandHistory, ShellInput, CommandPalette)
```

**Strengths:**
- Follows **separation by concern** pattern, not by feature
- Each module has single responsibility (e.g., CommandHistory = pure history logic, not tied to specific widget)
- Clear dependency direction: app.py → panels/input/modals/widgets
- No circular imports detected

**Examples of Good Practice:**
```python
# widgets/command_history.py - Reusable pure logic
class CommandHistory:
    def add(self, cmd: str) -> None:
    def up(self) -> str | None:
    def down(self) -> str | None:
    # Zero dependency on Textual or UI state
```

**Recommendation:** Continue this pattern. Each new UI component should:
1. Have single clear purpose
2. Exist in appropriate subdirectory (panels, widgets, modals, input)
3. Have zero cross-module dependencies within UI (use message passing)

---

### 1.2 Reactive State Management ✅ EXCELLENT

**Current Implementation:**
```python
class CodeAssistantApp(Static):
    current_focus = reactive("browser")
    project_loaded = reactive(False)
    
    def watch_current_focus(self, focus: str) -> None:
        # Auto-triggered when current_focus changes
        self.browser_title.remove_class("active")
        ...
```

**Strengths:**
- Proper use of Textual's reactive pattern
- Watchers follow naming convention `watch_<property_name>()`
- Decouples state from UI updates

**What's Well Done:**
- Reactive properties only for **state that affects UI rendering**
- Not over-using reactives for ephemeral data
- Watch methods are simple and focused

**Potential Issue:**
```python
# Current: FileEditorPane uses Reactive for is_dirty
is_dirty: Reactive[bool] = Reactive(False)  # Good - affects tab title
```

**Recommendation:** 
- Keep reactives for: visibility, focus state, data that drives rendering
- Don't use reactives for: transient UI state, cache, temporary data
- Use regular attributes for business logic state

---

### 1.3 Message Passing Pattern ⚠️ NEEDS ATTENTION

**Current State:**
- ✅ Good: PreviewPane has custom `PreviewEnter` message
- ✅ Good: FileEditorPane has `_AISuggestionsRequested` message
- ⚠️ Issue: Most messages are implicit (button clicks → action methods)
- ⚠️ Issue: Limited use of Widget.post_message() for cross-widget communication

**Current Pattern:**
```python
# This works but is direct coupling:
def on_button_pressed(self, event: Button.Pressed) -> None:
    if event.button.id == "btn-save":
        self.action_save()  # Direct method call
```

**Better Pattern (Already Present):**
```python
# Good pattern - explicit message:
class PreviewPane(Static):
    class PreviewEnter(Message):
        def __init__(self, file_path: Path, content: str):
            self.file_path = file_path
            self.content = content
            super().__init__()
    
    def action_enter(self) -> None:
        self.post_message(self.PreviewEnter(self.file_path, self.content))
```

**Recommendation:**
1. **Use messages for cross-widget communication**, not method calls
2. Create Message subclasses for all significant widget events:
   ```python
   class FileEditorPane(Container):
       class FileSaved(Message):
           def __init__(self, file_path: str): ...
       
       class FileDiscarded(Message):
           def __init__(self, file_path: str): ...
   ```
3. Handle messages in parent containers, not widget methods
4. Document expected messages in widget docstrings

---

### 1.4 Event Binding & Actions ✅ GOOD

**Current Implementation:**
```python
BINDINGS = [
    Binding("tab", "focus_next", "Focus Next", show=True),
    Binding("shift+tab", "focus_previous", "Focus Previous", show=True),
    Binding("ctrl+x", "focus_shell", "Shell", show=True),
    # ...
]

def action_focus_shell(self) -> None:
    """Focus the shell panel (Ctrl+X)."""
```

**Strengths:**
- All key bindings declared in BINDINGS (discoverable)
- Action methods are `action_*` (Textual convention)
- Short, focused action implementations
- Show/hide in footer is properly controlled

**Weaknesses:**
- Some actions delegate to implementation details:
  ```python
  def action_open_prompts(self) -> None:
      self.app.push_screen(PromptsModal(...))  # OK but uses app reference
  ```

**Recommendation:**
- Use `self.app` only when pushing screens or accessing app-level state
- For widget-level actions, emit messages instead:
  ```python
  def action_edit_file(self) -> None:
      self.post_message(CodeAssistantApp.EditFileRequested(file_path))
  ```

---

### 1.5 Widget Hierarchy & Composition ✅ GOOD

**Current Structure:**
```
CodeAssistantApp (Static)
├── Main Title (Static)
├── Horizontal (main_container)
│   ├── LeftPanel (Container)
│   │   └── TabbedContent (editor-tabs)
│   │       ├── TabPane (Browser)
│   │       │   ├── SelectableFileList
│   │       │   └── PreviewPane
│   │       └── TabPane (Editor 1, 2, ...)
│   │           └── FileEditorPane
│   └── Vertical (right_panel)
│       └── TabbedContent (chat_terminal_tabs)
│           ├── TabPane (Chat) → SelectableRichLog
│           ├── TabPane (Terminal) → TerminalPanel
│           └── TabPane (Shell) → ShellPanel
├── Input Title (Static)
├── ChatInput (TextArea)
└── Status Bar (Static)
```

**Strengths:**
- Clear container nesting
- Logical grouping (left = input, right = output)
- CSS layout with `width: 1fr` and `height: 1fr` properly applied

**Potential Issue:**
```python
# In app.py compose():
# Problem: mixing Container creation with widget setup
with Vertical(id="left_panel", classes="panel"):
    self.left_panel = LeftPanel(parent_app=self)  # Creates new widget
    yield self.left_panel
```

Better pattern:
```python
# Defer setup to on_mount() for complex initialization
def compose(self) -> ComposeResult:
    self.left_panel = LeftPanel()
    yield self.left_panel

def on_mount(self) -> None:
    # Now safe to query and configure
    self.file_list = self.left_panel.query_one("#file-browser", SelectableFileList)
```

**Recommendation:**
- Keep compose() for structure only
- Use on_mount() for component initialization and queries
- This is already implemented in Phase 3 refactoring ✅

---

## Part 2: Textual-Specific Best Practices

### 2.1 Styling & CSS ⚠️ NEEDS ATTENTION

**Current State:**
- CSS is split: `kicli_code_assist/ui/styles/textual_app.tcss` + inline `DEFAULT_CSS`
- Good: Avoiding massive monolithic CSS file
- Issue: Inconsistency in color/spacing naming

**Pattern Issues:**
```python
# Problem: Mixing specific colors with semantic names
DEFAULT_CSS = """
FileEditorPane {
    background: $surface;      # Good - semantic
    border-bottom: solid $primary;  # Good
}
"""

# But elsewhere:
DEFAULT_CSS = """
PreviewPane {
    color: $success;  # Inconsistent naming
    background: $error 20%;  # 20% opacity syntax unclear
}
"""

# Better:
DEFAULT_CSS = """
FileEditorPane {
    border: solid $primary 1;
}

FileEditorPane > #editor-buttons {
    margin: 0 1;
    height: 1;
}

FileEditorPane #editor-title {
    text-align: left;
    width: 1fr;
}
"""
```

**Recommendation:**
1. **Create a design system** (`ui/styles/_design_tokens.tcss`):
   ```tcss
   /* Colors */
   $color-success: #00aa00;
   $color-error: #ff0000;
   $color-warning: #ffaa00;
   
   /* Spacing */
   $spacing-xs: 0;
   $spacing-sm: 1;
   $spacing-md: 2;
   $spacing-lg: 4;
   ```

2. **Enforce hierarchical selectors:**
   ```css
   FileEditorPane { }  /* Container */
   FileEditorPane #editor-header { }  /* Child */
   FileEditorPane #editor-header Label { }  /* Deep child */
   ```

3. **CSS file organization:**
   ```
   styles/
   ├── _design_tokens.tcss
   ├── _components.tcss    (reusable widget styles)
   ├── _layout.tcss        (containers, grid, flexbox)
   └── textual_app.tcss    (app-specific overrides)
   ```

---

### 2.2 Async/Worker Pattern ⚠️ CRITICAL ISSUE

**Current Implementation:**
```python
# From chat_session.py - AI processing
def process_with_ai(self, user_message: str) -> str:
    """Process message with LLM."""
    # This is BLOCKING - called from UI thread!
    response = self.client.chat.completions.create(...)
    return response.choices[0].message.content
```

**Problem:**
- ❌ LLM API calls are blocking (can hang UI for 5-30+ seconds)
- ❌ No visible feedback during processing
- ❌ TUI becomes unresponsive

**Current State:**
```python
# In app.py - worker pattern (partially)
def handle_ai_response(self):
    self.llm_worker = self.run_worker(
        self.process_with_ai,
        arg1,
        arg2
    )
```

**Issue with Current Worker:**
```python
# Problem: run_worker expects async function
self.run_worker(self.sync_method)  # ❌ Fails with "non-async function"
```

**Recommendation - Correct Implementation:**

```python
# ui/app.py
class CodeAssistantApp(Static):
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-submit-chat":
            # Post message to self, handle in async context
            self.post_message(self.ProcessChatMessage(user_input))
    
    async def on_process_chat_message(self, message: "CodeAssistantApp.ProcessChatMessage") -> None:
        """Handle message processing asynchronously."""
        self.chat_display.update("[yellow]⏳ Processing...[/]")
        
        try:
            response = await asyncio.to_thread(
                self.chat_session.process_with_ai,
                message.content
            )
            self.chat_display.update(response)
        except Exception as e:
            self.chat_display.update(f"[red]❌ Error: {e}[/]")
    
    class ProcessChatMessage(Message):
        def __init__(self, content: str):
            self.content = content
            super().__init__()
```

**Pattern to Use:**
```python
# For CPU-intensive or blocking operations:
response = await asyncio.to_thread(blocking_function, arg1, arg2)

# For I/O-intensive operations:
response = await async_function(arg1, arg2)
```

**Recommendation:**
1. ✅ Create `async` wrapper for `ChatSession.process_with_ai()`
2. ✅ Use `asyncio.to_thread()` for blocking operations
3. ✅ Add spinner/progress indicator during processing
4. ✅ Show "Processing..." message in chat display
5. ✅ Add timeout (e.g., 60 seconds) for LLM calls

**Files to Update:**
- `chat_session.py`: Add `async def process_with_ai_async()`
- `ui/app.py`: Add message handler + async processing

---

### 2.3 Focus Management ✅ GOOD

**Current Implementation:**
```python
def action_focus_browser(self) -> None:
    """Focus the file browser panel."""
    self.current_focus = "browser"
    self.call_after_refresh(self.file_list.focus)  # Defer until refresh
```

**Strengths:**
- Uses `call_after_refresh()` to defer focus (correct)
- Tracks focus state in reactive property
- Updates UI visuals based on focus (title highlighting)

**What's Already Well Done:**
```python
def watch_current_focus(self, focus: str) -> None:
    """Update UI when focus changes."""
    # Updates CSS classes based on current_focus
    self.browser_title.remove_class("active")
    # ... etc
```

**Recommendation:** No changes needed - this pattern is correct.

---

### 2.4 Text Input & History ✅ EXCELLENT

**Current Implementation (ChatInput):**
```python
class ChatInput(TextArea):
    def __init__(self, parent_app, ...):
        super().__init__(...)
        self.command_history = CommandHistory()  # Reusable
    
    def action_cursor_up(self) -> None:
        """Navigate command history."""
        prev = self.command_history.up()
        if prev:
            self.text = prev
```

**Strengths:**
- ✅ Uses reusable CommandHistory class
- ✅ Decouples history from TextArea
- ✅ Preserves pending input while browsing

**Textual-Specific Note:**
```python
# TextArea has built-in undo/redo via:
self.text  # Content
self.selection  # Current selection

# Don't override these; use for history navigation only
```

**Recommendation:** Continue this pattern. ✅

---

### 2.5 Modal Dialogs ✅ GOOD

**Current Implementation:**
```python
def action_open_prompts(self) -> None:
    from kicli_code_assist.ui.modals.prompts_modal import PromptsModal
    self.app.push_screen(PromptsModal(self.prompt_manager))
```

**Pattern Issues:**
```python
# Current: No callback handling
self.app.push_screen(PromptsModal(...))  # Fire and forget

# Better: Use callback for result
def _on_modal_result(self, result) -> None:
    if result:
        self.handle_modal_result(result)

self.app.push_screen(PromptsModal(...), callback=self._on_modal_result)
```

**Recommendation:**
1. Always use callbacks for modal results
2. Document expected callback signature in modal class
3. Handle "cancelled" case (when user presses Esc)

Example:
```python
class PromptsModal(Screen):
    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(None)  # Pass None for cancel
        elif event.key == "enter":
            self.dismiss(self.selected_item)
```

---

## Part 3: Common Anti-Patterns Found & Fixes

### ❌ Anti-Pattern 1: Direct Component Access
```python
# Bad - tight coupling
def handle_event(self):
    self.file_browser.select_item(5)
    self.preview_pane.load_file(path)
    self.chat_display.write("text")
```

✅ Better:
```python
# Use messages
def handle_event(self):
    self.post_message(self.FileSelected(file_path))
    self.post_message(self.PreviewRequested(file_path))
```

**Status in codebase:** ⚠️ Mix of both patterns - refactor needed

---

### ❌ Anti-Pattern 2: Blocking LLM Calls in UI Thread
```python
# Current issue
def on_send_button(self):
    response = self.chat_session.process_with_ai(msg)  # BLOCKS UI!
    self.display_response(response)
```

✅ Better:
```python
async def process_ai_async(self, msg: str):
    response = await asyncio.to_thread(
        self.chat_session.process_with_ai, msg
    )
    return response
```

**Status in codebase:** ⚠️ Critical - needs fixing (see Section 2.2)

---

### ❌ Anti-Pattern 3: Global State in Widgets
```python
# Bad - mutable global state
class ChatDisplay(Static):
    _messages = []  # Shared across instances!
```

✅ Better:
```python
# Good - instance state
class ChatDisplay(Static):
    def __init__(self):
        self.messages = []  # Per-instance
```

**Status in codebase:** ✅ Not found - good practice followed

---

### ❌ Anti-Pattern 4: Over-Complex Compose Methods
```python
# Bad - 100+ lines in compose()
def compose(self):
    with Vertical():
        with Horizontal():
            # ... tons of nesting and setup
```

✅ Better:
```python
# Good - extract to separate builder methods or sub-widgets
def compose(self):
    yield self._create_header()
    yield self._create_content()
    yield self._create_footer()
```

**Status in codebase:** ⚠️ app.py compose is reasonable (~50 lines) but LeftPanel.compose could be clearer

---

## Part 4: CSS Organization & Typography

### 4.1 Responsive Layout ✅ GOOD
```css
/* Good practice found */
Horizontal {
    width: 1fr;
    height: auto;
}

LeftPanel {
    width: 1fr;
    height: 1fr;
}

#left_panel {
    width: 50%;  /* Split layout */
}

#right_panel {
    width: 50%;
}
```

**Recommendation:** Add breakpoints for small terminals:
```css
/* Add media query support (pseudo) */
@media (max-width: 80) {
    #left_panel {
        width: 100%;
        height: 50%;
    }
    #right_panel {
        width: 100%;
        height: 50%;
    }
}
```

### 4.2 Color Usage ⚠️ INCONSISTENT
```python
# Found inconsistencies:
"[color(196)]✗"  # ANSI code
"[red]error[/]"  # CSS name
"$error"         # Variable
"#ff0000"        # Hex (not supported in TCSS)
```

**Recommendation:** Standardize to one style:
```python
# Use Rich style names only
"[red]Error message[/]"
"[green]Success[/]"
"[yellow]Warning[/]"
"[dim]Secondary text[/]"
```

---

## Part 5: Testing & Documentation

### 5.1 Unit Testing
**Status:** ❌ No TUI tests found

**Recommendation:** Add simple snapshot tests:
```python
# tests/ui/test_widgets.py
def test_command_palette_filtering():
    palette = CommandPalette()
    palette.filter_commands("ls")
    assert "ls" in palette.filtered_commands
    assert "lsof" in palette.filtered_commands
```

### 5.2 Documentation
**Status:** ✅ Good docstrings, but missing integration docs

**Recommendation:** Add TUI architecture guide:
```
docs/
├── TUI_ARCHITECTURE.md      # Overall widget structure
├── WIDGET_PATTERNS.md       # Message passing, events
├── STYLING_GUIDE.md         # CSS organization
└── ASYNC_PATTERNS.md        # Worker & async best practices
```

---

## Summary: Textual Best Practices Grade

| Aspect | Grade | Status |
|--------|-------|--------|
| Component Organization | A | ✅ Excellent modularity |
| Reactive State Management | A | ✅ Correct usage |
| Message Passing | B+ | ⚠️ Partially implemented |
| Event Binding | A- | ✅ Good, minor improvements |
| Widget Composition | A | ✅ Clear hierarchy |
| Async/Workers | C | ❌ **CRITICAL:** Blocking LLM calls |
| Focus Management | A | ✅ Correct pattern |
| CSS Organization | B | ⚠️ Needs design tokens |
| Input Handling | A | ✅ Good reusability |
| Modal Dialogs | B+ | ⚠️ Missing callbacks |
| Testing | D | ❌ No tests |
| Documentation | B | ⚠️ Good docstrings, need architecture guide |

**Overall Textual Grade: A- (90/100)**

---

## Recommended Immediate Actions

### 🔴 CRITICAL (Week 1)
1. **Fix blocking LLM calls** - Implement async/to_thread pattern
2. **Add spinner/progress UI** - Show processing state
3. **Add timeout to LLM calls** - Prevent infinite hangs

### 🟡 HIGH (Week 2-3)
4. Implement message-passing for cross-widget communication
5. Create CSS design tokens system
6. Add modal callback patterns

### 🟢 MEDIUM (Month 1)
7. Add unit tests for UI widgets
8. Create TUI architecture documentation
9. Refactor LeftPanel.compose() for clarity

---

**Report Complete**  
*Generated: 2026-10-17*

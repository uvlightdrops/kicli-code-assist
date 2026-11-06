---
title: Textual UI Patterns & Recipes
project: kicli-code-assist
scope: Development Guide
purpose: Quick reference for common Textual patterns, gotchas, and recipes used in this project
created: 2026-11-06T07:50:00+01:00
updated: 2026-11-06T07:50:00+01:00
status: active
---

# Textual HowTo: Patterns & Recipes

Quick reference for Textual patterns in kicli-code-assist. Each section: brief intro + how-to stichpunkte + common gotchas.

---

## Event Handlers & Message Dispatch

Textual posts messages when user interacts (clicks, keys, state changes). You handle them via event handlers.

**Method Naming Syntax** works, BUT with gotchas:
- Handler name: `on_<widget_type>_<event_name>()` → `on_tree_node_selected()`
- **Problem**: Case conversion rules are tricky. `Tree.NodeSelected` → `on_tree_node_selected()` ✓, but sometimes it doesn't fire
- **Workaround**: Override `action_*()` methods instead (more reliable for user input)

**How to do it:**
- For **user input events** (keys, clicks): Override `action_select_cursor()`, `action_toggle_node()`, etc.
- For **state events** (node expanded, value changed): Use method naming `on_*()` or decorator `@on(Tree.NodeExpanded)`
- **Reliable fallback**: Always override the action method, then call parent `super().action_toggle_node()`

**Gotchas:**
- ❌ `on_tree_node_selected()` may not fire even if Tree posts the message (version/widget combo)
- ❌ Don't rely on event handler alone for user interactions; override actions instead
- ❌ Parent class action may post different message than you expect; test with logs
- ✅ Decorator syntax `@on(Tree.NodeSelected)` is more reliable than method naming for complex widgets

**Example (from FileTree):**
```python
def action_select_cursor(self) -> None:
    """ENTER key - select node, then lazy-load if directory."""
    super().action_select_cursor()  # Parent posts NodeSelected
    if self.cursor_node and self.cursor_node.data.get("is_dir"):
        self._populate_node(self.cursor_node)
```

---

## TreeNode Gotchas

TreeNodes look like simple objects, but have quirks:

**Data Storage & Comparison:**
- `node.label` returns `rich.text.Text`, NOT a string → comparison fails silently
- ❌ `if node.label == "..."` → **False**, even if label is "..."
- ✅ `if str(node.label) == "..."` → **True**

**Children Management:**
- `node.children` is read-only property, NOT assignable
- ❌ `node.children = []` → TypeError
- ✅ `node.remove_children()` then `node.add(label)`
- ✅ Placeholder pattern: create with `node.add("...")`, check `len(node.children) == 1 and str(node.children[0].label) == "..."`

**Lazy Loading Pattern:**
- Create node with `expand=False` (collapsed by default)
- Add placeholder `node.add("...")` so expand arrow shows
- Override `action_toggle_node()` or `action_select_cursor()` to replace placeholder on expand
- Use `node.toggle()` to programmatically expand/collapse

**Example (from FileTree):**
```python
node = parent.add("📁 folder", expand=False)  # Collapsed
node.add("...")  # Placeholder so arrow shows
# Later, in action_toggle_node():
if len(node.children) == 1 and str(node.children[0].label) == "...":
    node.remove_children()
    add_real_children(node)  # Replace placeholder
```

---

## CSS & Layout

Textual uses CSS-like syntax for styling and layout. Fractional units (`1fr`, `2fr`) divide space proportionally.

**Horizontal 3-Panel Layout** (FileTree | Preview | Agent):
```python
CSS = """
content-area {
    layout: horizontal;
    width: 1fr;
    height: 1fr;
}
FileTree {
    width: 1fr;
    height: 1fr;
    border: solid $primary;
}
PreviewPanel {
    width: 2fr;
    height: 1fr;
    border: solid $secondary;
}
AgentTabPanel {
    width: 2fr;
    height: 1fr;
    border: solid $secondary;
}
"""
```

**How to layout:**
- `layout: horizontal` (default) or `layout: vertical` for container
- Widths/heights: `1fr` (1 part), `2fr` (2 parts), `100%` (full), `10` (lines/chars)
- Borders: `solid $primary`, `double $accent`, `rounded $panel`
- Focus: `border: double $accent` when widget has focus

**Gotchas:**
- ❌ Nested containers fight for space; use explicit widths
- ❌ `width: auto` doesn't work; always specify `1fr` or pixels
- ❌ `height: auto` for text widgets will overflow; use `height: 1fr`
- ✅ Use `max-height` to prevent overflow
- ✅ Test layout in different terminal sizes

---

## Widget Composition & Containers

Textual widgets must be composed inside `compose()` method. Containers group children.

**How to compose:**
- Override `compose()` in your App/Container
- Yield widgets in order (top-to-bottom or left-to-right depending on layout)
- Use `Container` for grouping with layout control
- Set `id` for later querying with `self.query_one(MyWidget, id="...")`

**Widget Lifecycle:**
1. `__init__()` - Create widget
2. `on_mount()` - Called when added to tree, safe to query siblings
3. User interaction - Posts messages
4. Event handlers fire
5. Reactive attributes update → `_watch_*()` methods fire

**Example (3-panel layout):**
```python
def compose(self) -> ComposeResult:
    yield Container(
        FileTree(...),
        PreviewPanel(...),
        AgentTabPanel(...),
        id="content-area"
    )
```

**Gotchas:**
- ❌ Don't query widgets in `__init__()`; use `on_mount()`
- ❌ Don't modify compose() after app starts
- ✅ Use `try/except` in `on_mount()` when querying optional widgets
- ✅ Set `id` attributes for reliable querying

---

## Reactive State & Watchers

Textual widgets can have reactive attributes that trigger watchers.

**How to use:**
```python
from textual.reactive import reactive

class MyWidget(Widget):
    selected_path = reactive("")
    
    def _watch_selected_path(self, old_value: str, new_value: str) -> None:
        """Called when selected_path changes."""
        logger.debug(f"Selection changed: {old_value} → {new_value}")
```

**How it works:**
- Declare attribute with `= reactive("")`
- Textual watches for changes
- Auto-calls `_watch_<name>()` when value changes
- Useful for triggering UI updates

**Gotchas:**
- ❌ `_watch_*()` fires even on first mount (old_value may be uninitialized)
- ❌ Too many watchers = performance issues
- ✅ Use `recompose=True` to redraw on change
- ✅ Keep watcher logic fast; use `@work` for heavy lifting

---

## Keybindings & Actions

Textual maps keys to actions. Override `action_*()` methods to customize behavior.

**How to bind keys:**
```python
BINDINGS = [
    ("q", "quit", "Quit"),
    ("ctrl+s", "save", "Save"),
]

def action_quit(self) -> None:
    self.app.exit()

def action_save(self) -> None:
    logger.info("Saving...")
```

**How to override built-in actions:**
```python
class MyTree(Tree):
    def action_toggle_node(self) -> None:
        """Override SPACE key behavior."""
        # Custom logic here
        super().action_toggle_node()  # Call parent if needed
```

**Gotchas:**
- ❌ Key names are case-sensitive: `"enter"` not `"ENTER"`
- ❌ `ctrl+c` is reserved for interrupt; use `ctrl+x` instead
- ❌ `action_*()` methods MUST exist or keybind fails silently
- ✅ Test keybinds by pressing keys; check logs for action calls
- ✅ Use `action_focus_next()` / `action_focus_previous()` for navigation

---

## Debugging & Logging

Textual is hard to debug interactively. Use logging + stderr.

**How to debug:**
- Set up logger early: `logger = logging.getLogger(__name__)`
- Log lifecycle events: `on_mount()`, `action_*()`, event handlers
- Use `stderr` for quick debugging: `print(f"DEBUG: {value}", file=sys.stderr)`
- Check logs after TUI closes: `tail -f log/kicli.log`

**Gotchas:**
- ❌ `print()` to stdout gets eaten by TUI
- ❌ Don't use `pdb` in TUI; it breaks the terminal
- ✅ Redirect stderr with `2>&1` to capture debug output
- ✅ Add `logger.debug()` calls before uncertain operations
- ✅ Test logic outside TUI first (unit tests, standalone scripts)

---

## kicli-code-assist TUI Layout Schema

**Canonical 3-panel horizontal layout (Phase 1.3+):**

```
┌───────────────┬──────────────────────┬──────────────────────┐
│   FileTree    │   Preview Pane       │   Agent Pane         │
│   (1fr)       │   (2fr, tabs)        │   (2fr, tabs)        │
│               │                      │                      │
│ - Project     │ File Content         │ Explain Tab:         │
│ - Folders     │ (Syntax highlight)   │  ├─ Response (top)   │
│ - Files       │                      │  └─ Chunks (bottom)  │
│               │                      │                      │
│               │ Or other tabs later  │ Metrics Tab:         │
│               │                      │  ├─ Response (top)   │
│               │                      │  └─ Chunks (bottom)  │
│               │                      │                      │
│               │                      │ Refactor Tab:        │
│               │                      │  ├─ Response (top)   │
│               │                      │  └─ Chunks (bottom)  │
└───────────────┴──────────────────────┴──────────────────────┘
```

**Key Constraints:**
- Left pane (FileTree): Always showing file browser, user selects files here
- Middle pane (Preview): Always shows file preview (top-level tabs possible later)
- Right pane (Agent): Shows analysis results (tabs: Explain, Metrics, Refactor, Suggest)
- Each Agent tab splits vertically: **Response/Chat (50%) + Thinking/Chunks (50%)**
- Widths fixed: `1fr : 2fr : 2fr` (FileTree narrow, Panels balanced)

**Interaction Flow:**
1. User selects file in FileTree
2. Preview pane updates with file content
3. User triggers analysis (manual button, not auto-select)
4. Agent tab opens with Response top, Chunks streaming bottom
5. Chunks scroll in real-time as agent thinks

**See:** kicli_code_assist/ui/tui_client.py:compose(), CODE_ANALYSIS_STRUCTURE.md

---

## Common Patterns

### Modal / Dialog
```python
def show_modal(self, title: str, content: str) -> None:
    """Show a modal dialog."""
    dialog = Static(content, id="dialog")
    self.app.push_screen(dialog)  # Push new screen
```

### Search / Filter in Tree
```python
def filter_tree(self, query: str) -> None:
    """Hide nodes that don't match query."""
    for node in self.root.children:
        if query.lower() not in str(node.label).lower():
            node.display = False
        else:
            node.display = True
```

### Scrollable Panel
```python
class ScrollablePanel(Container):
    CSS = """
    ScrollablePanel {
        width: 1fr;
        height: 1fr;
        overflow: auto;
        border: solid $primary;
    }
    """
```

### Real-time Status Updates (WebSocket)
```python
async def stream_status(self) -> None:
    """Periodically update status."""
    while True:
        status = await fetch_status()
        self.query_one(StatusBar).update(status)
        await asyncio.sleep(1)
```

---

## Checklist for New Features

- [ ] **Layout**: Specify `width`/`height` explicitly (no `auto`)
- [ ] **Events**: Test if `on_*()` fires; fallback to `action_*()` override
- [ ] **Data**: Use `.data` dict on TreeNode for custom fields, not properties
- [ ] **Strings**: Remember `node.label` is `Text`; convert with `str()`
- [ ] **Focus**: Call `.focus()` on widget to make it interactive
- [ ] **Logging**: Add `logger.debug()` at entry points for debugging
- [ ] **CSS**: Test in different terminal sizes
- [ ] **Performance**: Profile if tree has 1000+ nodes

---

**See also:** kicli_code_assist/ui/widgets/, kicli_code_assist/ui/tui_client.py for working examples.

---
title: TUI Textual Architecture - Widget Design & Event Flow
scope: architecture
project: kicli-code-assist
status: in_progress
created: 2026-11-05T19:52+01:00
updated: 2026-11-05T19:52+01:00
update_reason: Document widget hierarchy, async patterns, CSS layout after Phase 3 completion
agent_project: kicli-code-assist
cross_references:
  - /home/flow/dev_doc/TUI_STRATEGY_CLARIFICATION.md
  - doc/guides/TUI_CLIENT_IMPLEMENTATION_PLAN.md
  - doc/guides/TEXTUAL_BEST_PRACTICES_REVIEW.md
---

# TUI Textual Architecture

## Widget Hierarchy

```
CodeAssistantTUIApp (App)
├── Header (Textual built-in)
├── Horizontal #main-content
│   ├── ProjectExplorer (Container)
│   │   └── Tree (file system browser)
│   │       └── Events: on_tree_node_selected
│   │
│   └── AgentOutputPanel (Container)
│       ├── RichLog (scrollable output display)
│       └── Handles all output formatting
│
├── StatusBar (Container)
│   └── Static widgets for metrics display
│       ├── Backend status
│       ├── Processing indicator
│       └── Agent metrics (time, cost, tokens)
│
├── InputPanel (Container)
│   ├── Static (title)
│   └── TextArea (user request input)
│       └── Events: on_key
│
└── Footer (Textual built-in)
    └── Help text + key bindings
```

## CSS Layout Strategy

### Rationale

**Vertical Main Layout:**
```css
Screen {
    layout: vertical;
}
```
- Simplest Textual layout mode
- Works well on variable terminal sizes
- Scales naturally on small jump-host terminals

**Horizontal Content Split:**
```css
#main-content {
    layout: horizontal;
    height: 1fr;
}
```
- Side-by-side project tree + output
- Matches WebUI left/right split
- Easy to toggle full-width if needed

**Fixed Tree Width (60 chars):**
```css
#project-panel {
    width: 60;
    height: 100%;
}
```

**Why 60 chars (not percentage)?**
- Percentage often fails in Textual with dynamic content
- Fixed width = predictable behavior across terminals
- 60 chars ≈ typical filename length (allows full path reading)
- Right panel gets `width: 1fr` (fill remaining space)

**Example on 120-char terminal:**
- Left panel: 60 chars
- Right panel: 60 chars (perfect balance)

**Example on 80-char terminal:**
- Left panel: 60 chars
- Right panel: 20 chars (scrollable, less ideal but functional)

**Example on 200-char terminal:**
- Left panel: 60 chars
- Right panel: 140 chars (excellent for large output)

### CSS Details

```tcss
Screen {
    layout: vertical;
}

#main-content {
    layout: horizontal;
    height: 1fr;
}

#project-panel {
    border: solid $primary;
    width: 60;          /* Fixed 60 characters */
    height: 100%;
}

#output-panel {
    border: solid $accent;
    width: 1fr;         /* Fill remaining space */
    height: 100%;
}

#status-bar {
    height: 1;
    background: $surface;
    color: $text;
}

#input-panel {
    height: 3;          /* 3 lines for input */
    border: solid $primary;
}
```

### Responsive Behavior

| Terminal Width | Left Panel | Right Panel | Usability |
|---|---|---|---|
| 60 chars | 60 (100%) | 0 | Tree only, input below |
| 80 chars | 60 | 20 | Tight but functional |
| 120 chars | 60 | 60 | Balanced, good |
| 200+ chars | 60 | 140+ | Excellent |

**Note:** On very small terminals (<80 chars), user can horizontally scroll each panel independently.

## Widget Implementation Details

### ProjectExplorer

**Purpose:** Display file system tree for project navigation

**Code Location:** `kicli_code_assist/ui/widgets/project_explorer.py`

**Key Attributes:**
```python
class ProjectExplorer(Container):
    file_tree: Tree      # Renamed from 'tree' to avoid property conflict
    project_path: Path   # Root directory
    max_depth: int       # Limit tree depth (default 3)
```

**Methods:**
```python
def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
    """Handle file selection."""
    # Get selected file path
    node = event.node
    file_path = self._extract_path_from_node(node)
    
    # Post message to parent
    self.post_message(self.FileSelected(file_path))

def _load_tree(self, path: Path, parent: TreeNode, depth: int) -> None:
    """Recursively load directory tree."""
    if depth > self.max_depth:
        return
    
    for item in sorted(path.iterdir()):
        if item.is_dir():
            subtree = parent.add(f"📁 {item.name}", data=item)
            self._load_tree(item, subtree, depth + 1)
        else:
            parent.add(f"📄 {item.name}", data=item)
```

**Message:**
```python
class FileSelected(Message):
    def __init__(self, file_path: str):
        self.file_path = file_path
        super().__init__()
```

### AgentOutputPanel

**Purpose:** Display agent responses (Explain, Suggest, Reason, Metrics, Refactor, Dependencies)

**Code Location:** `kicli_code_assist/ui/widgets/agent_output_panel.py`

**Key Attributes:**
```python
class AgentOutputPanel(Container):
    output_log: RichLog   # Rich formatted output
    max_lines: int        # Buffer size (default 500)
```

**Rendering Events:**
```python
def render_event(self, event: Dict[str, Any]) -> None:
    """Handle agent event and update display."""
    event_type = event.get("event_type")
    
    if event_type == "explain":
        self._render_explain(event)
    elif event_type == "suggest":
        self._render_suggest(event)
    elif event_type == "reason":
        self._render_reason(event)
    elif event_type == "metrics":
        self._render_metrics(event)
    # ... etc
```

**Example: Explain Rendering**
```python
def _render_explain(self, event: Dict) -> None:
    """Render explanation with syntax highlighting."""
    content = event.get("content", "")
    language = event.get("language", "python")
    
    # Use Syntax for code blocks
    from rich.syntax import Syntax
    syntax = Syntax(content, language, theme="monokai")
    
    self.output_log.write(syntax)
```

### InputPanel

**Purpose:** Capture user request and submit to backend

**Code Location:** `kicli_code_assist/ui/widgets/input_panel.py`

**Key Attributes:**
```python
class InputPanel(Container):
    text_input: TextArea
    
    @property
    def value(self) -> str:
        """Get current input text."""
        return self.text_input.text
    
    def clear(self) -> None:
        """Clear input field."""
        self.text_input.text = ""
```

**Event Handling:**
```python
def on_key(self, event: events.Key) -> None:
    """Handle Enter key to submit."""
    if event.key == "ctrl+enter":
        self.post_message(self.RequestSubmitted(self.value))
        self.clear()
```

### StatusBar

**Purpose:** Display processing state, metrics, backend connection status

**Code Location:** `kicli_code_assist/ui/widgets/status_bar.py`

**Example Display:**
```
Backend: http://localhost:8000 | Status: ✅ Ready | Time: 2.3s | Cost: $0.04
```

**Update Method:**
```python
def update_metrics(self, status: str = None, time_ms: float = None, 
                   cost: float = None, tokens: int = None) -> None:
    """Update status bar display."""
    parts = []
    
    if status:
        parts.append(status)
    if time_ms:
        parts.append(f"Time: {time_ms/1000:.1f}s")
    if cost:
        parts.append(f"Cost: ${cost:.4f}")
    if tokens:
        parts.append(f"Tokens: {tokens}")
    
    self.update(" | ".join(parts))
```

## Event Flow

### User Selects File

```
1. ProjectExplorer.on_tree_node_selected()
   ↓
2. Posts FileSelected message to CodeAssistantTUIApp
   ↓
3. CodeAssistantTUIApp.on_file_selected()
   ↓
4. Loads file content, updates InputPanel placeholder text
   ↓
5. User sees "Context loaded: src/main.py (245 lines)"
```

### User Submits Request

```
1. User types in InputPanel + presses Ctrl+Enter
   ↓
2. InputPanel.on_key() → posts RequestSubmitted message
   ↓
3. CodeAssistantTUIApp.on_request_submitted()
   ↓
4. Set is_processing=True, show spinner in StatusBar
   ↓
5. Call TUIAgentClient.call_agent_route() (async)
   ↓
6. Streaming JSON-L response from /api/agent/route
   ↓
7. For each event: AgentOutputPanel.render_event()
   ↓
8. Update StatusBar with metrics (time, cost, tokens)
   ↓
9. Set is_processing=False, show ready status
```

### WebSocket Streaming (Phase 5)

```
CodeAssistantTUIApp.on_mount()
   ↓
Open WebSocket: ws://localhost:8000/socket.io
   ↓
Subscribe to /agent/execution namespace
   ↓
Receive real-time events:
   - reasoning_step_started
   - reasoning_step_complete
   - llm_call_started
   - llm_call_complete
   - performance_metric
   - trace_event
   ↓
ReasoningPanel.handle_event() updates display in real-time
```

## Async Pattern: HTTP to TUI

### Problem
- LLM API calls can take 5-30+ seconds
- Textual's `on_mount()` is synchronous but we need async operations
- UI must stay responsive during blocking operations

### Solution: Message Handlers as Async Entry Points

**Pattern:**
```python
class CodeAssistantTUIApp(App):
    def on_mount(self) -> None:
        """Synchronous mount handler."""
        # Check health synchronously
        is_healthy = self.client.health_check()  # async but we block briefly
        
    async def on_request_submitted(self, message: "InputPanel.RequestSubmitted") -> None:
        """Asynchronous message handler.
        
        Textual automatically runs message handlers as async if defined async.
        """
        self.is_processing = True
        self.status_bar.update_metrics(status="⏳ Processing...")
        
        try:
            # Stream events from backend
            async for event in self.client.call_agent_route(
                project_path=str(self.project_path),
                selected_file=self.current_file,
                user_request=message.content
            ):
                # Update UI per event
                self.output_panel.render_event(event)
                self.status_bar.update_metrics(
                    time_ms=event.get("duration_ms", 0),
                    cost=event.get("cost", 0),
                    tokens=event.get("tokens", 0)
                )
        except Exception as e:
            self.output_panel.render_event({
                "event_type": "error",
                "message": str(e)
            })
        finally:
            self.is_processing = False
            self.status_bar.update_metrics(status="✅ Ready")
```

**Why This Works:**
1. Textual detects `async def on_request_submitted()` signature
2. Automatically runs handler in async context
3. `async for event in call_agent_route()` streams responses
4. UI updates happen in event loop (reactive)
5. Other UI events (keypresses) continue to work during processing

## Error Handling

### Health Check at Startup

```python
async def on_mount(self) -> None:
    is_healthy = await self.client.health_check()
    
    if not is_healthy:
        self.status_bar.update_metrics(
            status=f"❌ Cannot reach backend at {self.config.api_base_url}"
        )
        self.output_panel.render_event({
            "event_type": "error",
            "message": "Backend unreachable. Make sure stackctl is running."
        })
```

### Request Timeout

```python
async def on_request_submitted(self, message) -> None:
    try:
        async with asyncio.timeout(300):  # 5 minute timeout
            async for event in self.client.call_agent_route(...):
                self.output_panel.render_event(event)
    except asyncio.TimeoutError:
        self.output_panel.render_event({
            "event_type": "error",
            "message": "❌ Request timed out (>5 minutes)"
        })
```

### Graceful Degradation

If output becomes unresponsive:
- Press `Ctrl+C` to interrupt current operation
- Press `q` to quit TUI
- No data loss (stateless API)

## Performance Considerations

### Tree Rendering

- **Problem:** Loading entire codebase into Tree can be slow (1000+ files)
- **Solution:** 
  - Limit tree depth (default 3)
  - Lazy load subtrees on expand (TODO: Phase 6)
  - Show loading indicator while scanning

### Output Buffering

- **Problem:** Very large agent responses can fill memory
- **Solution:**
  - `AgentOutputPanel.max_output_lines = 500` (default)
  - Older lines auto-removed when buffer full
  - User can always see recent output

### Streaming Optimization

- **Problem:** Network overhead if WebSocket sends too many events
- **Solution:**
  - Backend batches events (Phase 5.5.2)
  - TUI processes events as they arrive
  - No buffering on client side

## Future Enhancements (Phase 5+)

1. **Keyboard Macros:** Record/replay sequences (e.g., "analyze all Python files")
2. **Split Panes:** Optional vertical split for side-by-side comparison
3. **Search/Filter:** Ctrl+F to search file tree or output
4. **Theming:** Switch color schemes (dark/light/high-contrast)
5. **Session Persistence:** Save current state, restore on next run
6. **Offline Mode:** Cache previous responses, work without backend
7. **Performance Profiling:** Built-in metrics for TUI responsiveness

---

**Status:** Phase 3 complete, Phase 4 in progress  
**Next:** Phase 5 testing & WebSocket integration  
**Last Updated:** 2026-11-05T19:52+01:00
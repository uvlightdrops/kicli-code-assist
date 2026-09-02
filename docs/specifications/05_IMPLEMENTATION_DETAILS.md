# Implementation Details & Code Walkthrough

## File Locations

### Main Application

```
kicli-code-assist/
├── kicli_code_assist/
│   ├── ui/
│   │   └── textual_app.py          # Main TUI application
│   ├── chat_session.py             # Chat history & context management
│   ├── cli.py                      # Entry point (kicli-assist tui)
│   ├── context/
│   │   └── project_context.py      # Project scanning
│   └── examples/
│       └── simple_chat.py          # LLM client creation
└── docs/
    └── specifications/             # THIS DOCUMENTATION
```

### Dependencies

```
ki-core/
├── src/ki_core/
│   ├── config.py                   # Config loading & provider selection
│   └── core/
│       └── models.py               # Message, Role, ChatRequest
```

---

## Component Details

### 1. SelectableFileList (textual_app.py:23-95)

**Purpose**: Custom Textual Static widget for vi-style file browsing

**Key Methods**:

#### `__init__(parent_app, *args, **kwargs)`
- Stores reference to parent app
- Sets initial directory to os.getcwd()
- Initializes empty entries list
- Calls load_directory()

#### `load_directory()`
- Scans self.current_dir for entries
- Builds list of tuples: (Path, is_dir: bool, display_text: str)
- Adds parent directory (..) if not at root
- Filters out dot files
- Sorts alphabetically
- Resets selected_index to 0
- Calls update_display()

**Example entries**:
```python
[
  (Path('/home/user/dev_flow'), True, '..'),
  (Path('/home/user/dev_flow/docs'), True, '📁 docs'),
  (Path('/home/user/dev_flow/README.md'), False, '📄 README.md'),
]
```

#### `update_display()`
- Iterates through self.entries
- For each entry, checks if index == selected_index
- Adds ">" marker if selected
- Renders with icons and names
- Updates widget display via `self.update(text)`

**Output**:
```
> ..
  📄 file.py
  📁 src
```

#### `action_cursor_up()`
- Decreases self.selected_index
- Bounds checks: `max(0, selected_index - 1)`
- Calls update_display()

#### `action_cursor_down()`
- Increases self.selected_index
- Bounds checks: `min(len(entries) - 1, selected_index + 1)`
- Calls update_display()

#### `action_select_cursor()`
- Gets current entry: `entries[selected_index]`
- If directory: calls load_directory() with new path
- If file: calls parent_app.update_file_preview() (no-op)

#### `get_selected_file() -> str | None`
- Returns full path of selected entry
- Returns None if index out of bounds
- Used by L-key handler

---

### 2. FocusAwareInput (textual_app.py:15-22)

**Purpose**: Custom Input widget that submits on ENTER when in INPUT mode

**Implementation**:

```python
class FocusAwareInput(Input):
    def __init__(self, parent_app=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_app = parent_app
    
    def on_key(self, event):
        if event.key == "enter":
            if self.parent_app.current_focus == "input":
                self.parent_app.action_select_cursor()
                event.prevent_default()
        else:
            # Let Input handle other keys
            super()._on_key(event)
```

**Behavior**:
- Intercepts ENTER key
- Checks if current_focus == "input"
- If yes: calls action_select_cursor() → on_input_submitted_manual()
- If no: ignores (prevents accidental submission in browser mode)
- All other keys: delegated to parent Input class

---

### 3. CodeAssistantApp (textual_app.py:98-330)

**Main Application Class**

#### Initialization (`__init__`)

```python
def __init__(self):
    super().__init__()
    self.chat_session = ChatSession(os.getcwd())  # Chat history
    
    # Widget references (set in compose())
    self.file_list = None
    self.preview_display = None
    self.chat_display = None
    self.input_field = None
    self.status_bar = None
    self.selected_file = None
    
    # Load LLM client
    from ki_core import Config
    self.config = Config.from_env()
    
    from kicli_code_assist.cli import _detect_best_provider
    provider = _detect_best_provider()
    
    from kicli_code_assist.examples.simple_chat import create_client
    self.client = create_client(self.config, provider)
```

#### Layout (`compose()`)

Creates widget hierarchy:
1. Title (Static)
2. Main container (Horizontal)
   - Left panel (Vertical)
     - File list title
     - SelectableFileList widget
     - Preview title
     - Preview display (Static)
   - Right panel (Vertical)
     - Chat title
     - Chat display (RichLog)
3. Input title (Static)
4. FocusAwareInput widget
5. Status bar (Static)

#### Mount (`on_mount()`)

- Sets initial focus to file_list (BROWSER mode)
- Schedules _init_preview_async() with call_later()

**Why call_later?**: RichLog needs to know widget size before write() works

#### Preview Initialization (`_init_preview_async()`)

```python
def _init_preview_async(self) -> None:
    self.chat_display.write("Welcome to KI Code Assistant!\n")
    self.chat_display.write("Use UP/DOWN to navigate files, ENTER to select, TAB to switch focus.\n")
```

#### Focus Management

**Action Methods**:

```python
def action_focus_next(self):
    """TAB key handler"""
    if self.current_focus == "browser":
        self.current_focus = "input"
        self.input_field.focus()
    else:
        self.current_focus = "browser"
        self.file_list.focus()

def action_focus_previous(self):
    """Shift+TAB key handler"""
    # Same logic as action_focus_next (toggles)
```

**Watch Method**:

```python
def watch_current_focus(self, focus: str) -> None:
    """Called automatically when current_focus changes (reactive)"""
    focus_char = "B" if focus == "browser" else "I"
    ctx_status = self.chat_session.get_context_status()
    self.status_bar.update(f"Curr-focus: {focus_char}  |  {ctx_status}")
```

#### File Navigation

```python
def action_cursor_up(self):
    """UP arrow key"""
    if self.current_focus == "browser" and self.file_list:
        self.file_list.action_cursor_up()

def action_cursor_down(self):
    """DOWN arrow key"""
    if self.current_focus == "browser" and self.file_list:
        self.file_list.action_cursor_down()

def action_select_cursor(self):
    """ENTER key"""
    if self.current_focus == "browser" and self.file_list:
        self.file_list.action_select_cursor()
    elif self.current_focus == "input":
        msg = self.input_field.value.strip()
        if msg:
            self.on_input_submitted_manual(msg)
```

#### File Loading

```python
def action_load_file(self):
    """L key - Load file to context"""
    if not self.file_list:
        return
    
    file_path = self.file_list.get_selected_file()
    if file_path:
        self.chat_display.write(f"\n[bold cyan]📄 Added to context:[/] {file_path}")
        self.selected_file = file_path
    else:
        self.chat_display.write("\n[bold yellow]⚠️  No file selected[/]")
```

#### Context Loading

```python
def action_load_context(self):
    """CTRL+L - Load project context"""
    self.chat_display.write("[bold cyan]📊 Scanning project...[/]")
    try:
        self.chat_session.load_project_context()
        status = self.chat_session.get_context_status()
        self.chat_display.write(f"[bold green]✅ {status}[/]")
        self.project_loaded = True
    except Exception as e:
        self.chat_display.write(f"[bold red]❌ Error: {str(e)}[/]")
```

#### Message Submission

```python
def on_input_submitted_manual(self, msg: str) -> None:
    """Handle message submission (from Input or action)"""
    self.input_field.value = ""
    
    # Add to display and history
    self.chat_display.write(f"\n[bold cyan]You:[/] {msg}")
    self.chat_session.add_message("user", msg)
    
    # Show loading state
    self.chat_display.write("\n[bold yellow]⏳ Waiting for LLM response...[/]")
    
    # Send async (non-blocking)
    self.app.call_later(self._send_to_llm_async, msg)
```

#### LLM Integration

```python
async def _send_to_llm_async(self, msg: str) -> None:
    """Stream response from LLM"""
    try:
        # Get messages with context
        api_messages = self.chat_session.get_messages_for_api()
        
        # Convert to ki-core format
        from ki_core.core.models import Message, Role, ChatRequest
        messages = [
            Message(
                role=Role.SYSTEM if m["role"] == "system" else
                      Role.ASSISTANT if m["role"] == "assistant" else
                      Role.USER,
                content=m["content"]
            )
            for m in api_messages
        ]
        
        # Create request and stream
        request = ChatRequest(messages=messages)
        response_text = ""
        
        self.chat_display.write("\n[bold green]Assistant:[/]\n")
        
        for event in self.client.chat_stream(request):
            if event.text:
                response_text += event.text
        
        # Write full response
        self.chat_display.write(response_text)
        self.chat_display.write("\n")
        
        # Add to history
        self.chat_session.add_message("assistant", response_text)
    
    except Exception as e:
        self.chat_display.write(f"[bold red]Error: {str(e)}[/]")
```

---

### 4. ChatSession (chat_session.py)

**Class Overview**:

```python
class ChatSession:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.messages = []                      # History
        self.project_context = None             # ProjectInfo
        self.project_context_manager = None
```

**Message Storage**:

```python
self.messages = [
    {"role": "system", "content": "You are a helpful..."},
    {"role": "user", "content": "Tell me about X"},
    {"role": "assistant", "content": "X is..."},
]
```

**add_message(role, content)**:
```python
def add_message(self, role: str, content: str) -> None:
    self.messages.append({"role": role, "content": content})
```

**load_project_context()**:
```python
def load_project_context(self) -> None:
    self.project_context_manager = ProjectContextManager(self.root_dir)
    self.project_context = self.project_context_manager.scan_project()
```

**get_context_status()**:
```python
def get_context_status(self) -> str:
    if not self.project_context:
        return "❌ No context"
    
    file_count = len(self.project_context.get("files", []))
    languages = self.project_context.get("languages", {})
    lang_count = len(languages)
    
    return f"✅ Project context: {file_count} files, {lang_count} languages"
```

**get_messages_for_api()**:
```python
def get_messages_for_api(self) -> list[dict]:
    messages = []
    
    # Build system message with context
    system_text = "You are a helpful AI code assistant..."
    if self.project_context:
        system_text += f"\n\nProject Info:\n"
        system_text += f"Root: {self.project_context['root']}\n"
        system_text += f"Files: {len(self.project_context['files'])}\n"
        # ... more context details
    
    messages.append({"role": "system", "content": system_text})
    
    # Add conversation history
    messages.extend(self.messages)
    
    return messages
```

---

### 5. ProjectContextManager (context/project_context.py)

**Class Overview**:

```python
class ProjectContextManager:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
```

**scan_project()**:

```python
def scan_project(self) -> ProjectInfo:
    all_files = []
    languages = {}
    
    for root, dirs, files in os.walk(self.root_dir):
        # Filter excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        
        for file in files:
            if file.startswith('.'):
                continue
            
            path = Path(root) / file
            ext = path.suffix.lower()
            
            # Detect language
            lang = self._detect_language(ext)
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
            
            all_files.append({
                "path": str(path.relative_to(self.root_dir)),
                "ext": ext,
                "language": lang
            })
    
    # Find key files
    key_files = self._find_key_files(all_files)
    
    return ProjectInfo(
        root=str(self.root_dir),
        files=all_files,
        languages=languages,
        key_files=key_files,
        summary=self._generate_summary(all_files, languages)
    )
```

**Language Detection**:

```python
LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    # ... more extensions
}

def _detect_language(self, ext: str) -> str | None:
    return LANGUAGE_MAP.get(ext)
```

**Excluded Directories**:

```python
EXCLUDED_DIRS = {
    '.git', '__pycache__', 'node_modules',
    'venv', '.venv', 'dist', 'build',
    # ... more
}
```

---

## Data Flow Examples

### Example 1: Navigate File and Load Context

```
User presses DOWN arrow
  ↓
Textual key event captured
  ↓
action_cursor_down() called
  ↓
current_focus == "browser" → file_list.action_cursor_down()
  ↓
selected_index += 1, update_display()
  ↓
File list re-rendered with new cursor position
```

### Example 2: Send Message to LLM

```
User types message and presses ENTER
  ↓
FocusAwareInput.on_key(enter_event)
  ↓
current_focus == "input" → action_select_cursor()
  ↓
on_input_submitted_manual("user message")
  ↓
chat_session.add_message("user", "user message")
  ↓
app.call_later(_send_to_llm_async)
  ↓
(async) get_messages_for_api() [injects project context]
  ↓
(async) client.chat_stream(request)
  ↓
(async) response streamed back, written to chat_display
  ↓
(async) chat_session.add_message("assistant", response)
```

### Example 3: Load Project Context

```
User presses CTRL+L
  ↓
action_load_context() called
  ↓
chat_display shows "📊 Scanning project..."
  ↓
ProjectContextManager.scan_project() runs
  ↓
os.walk() traverses directory tree
  ↓
Files categorized by language
  ↓
ProjectInfo returned
  ↓
chat_session.project_context = ProjectInfo
  ↓
chat_display shows "✅ Project context: 47 files, 3 languages"
  ↓
Status bar updates with context info
```

---

## Common Patterns

### Pattern 1: Action Handler

```python
def action_something(self):
    """Handle key binding"""
    if self.current_focus == "relevant_mode":
        # Do something
        self.widget.update()  # Update display
        self.status_bar.update(status)  # Update status
```

### Pattern 2: Async Operation

```python
def action_something_async(self):
    """Trigger async operation"""
    self.chat_display.write("Processing...")
    self.app.call_later(self._do_async_work)

async def _do_async_work(self):
    """Non-blocking work"""
    try:
        result = await expensive_operation()
        self.chat_display.write(f"Done: {result}")
    except Exception as e:
        self.chat_display.write(f"Error: {e}")
```

### Pattern 3: Reactive State Update

```python
current_focus = reactive("browser")  # Reactive state

def watch_current_focus(self, focus: str) -> None:
    """Called when current_focus changes"""
    self.status_bar.update(f"Focus: {focus}")
```

---

## Debugging Tips

### Check Current State

```python
# In action handler, add:
print(f"Focus: {self.current_focus}")
print(f"Selected: {self.file_list.selected_index}")
print(f"Entries: {len(self.file_list.entries)}")
```

### Log Key Events

```python
def _on_key(self, event):
    print(f"Key: {event.key}")
    super()._on_key(event)
```

### Check LLM Response

```python
# In _send_to_llm_async, add:
for event in self.client.chat_stream(request):
    print(f"Got event: {event.text}")
```

### Inspect Message History

```python
print(self.chat_session.messages)
```

---

## Testing Scenarios

### Test 1: File Navigation

1. Start app: `kicli-assist tui`
2. Press DOWN → file selection moves down
3. Press UP → file selection moves up
4. Press ENTER on directory → navigate into it
5. Press UP/DOWN again → verify in new directory

### Test 2: Focus Switching

1. Start app (focus on browser)
2. Press TAB → focus shifts to input (visible cursor in input field)
3. Type text → verify text appears
4. Press TAB → focus back to browser
5. Press UP/DOWN → file list navigates

### Test 3: Message Submission

1. Press TAB to enter INPUT mode
2. Type: "What is Python?"
3. Press ENTER
4. Verify message appears in chat
5. Wait for LLM response
6. Verify response appears

### Test 4: Project Context

1. Set up test project with .py and .js files
2. Press CTRL+L
3. Verify status bar shows file count
4. Type message → verify context injected (check in response)

### Test 5: Error Handling

1. Set `export KI_PROVIDER=mock` (no-op provider)
2. Send message → verify response
3. Set invalid LLM config → verify error message

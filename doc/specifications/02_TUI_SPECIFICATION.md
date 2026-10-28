# TUI Specification - User Interface & Interaction

## Layout

### Screen Structure

```
┌─────────────────────────────────────────────────────────────┐
│            🤖 KI Code Assistant (Title)                     │
├─────────────────────────┬───────────────────────────────────┤
│                         │                                   │
│   📂 File List          │   💬 Chat                         │
│   ────────────          │   ─────                           │
│   > ..                  │   Welcome message                 │
│     📄 file1.py         │   Project context info            │
│     📁 subdir           │                                   │
│     📄 file2.py         │   [User messages and]             │
│                         │   [AI responses]                  │
│   ────────────          │                                   │
│   👁️ File Preview       │                                   │
│   ────────────          │                                   │
│   (No file selected)    │                                   │
│                         │                                   │
├─────────────────────────┴───────────────────────────────────┤
│ ⌨️  Input                                                    │
│ ┌───────────────────────────────────────────────────────────┐
│ │ [User input field here]                                   │
│ └───────────────────────────────────────────────────────────┘
├─────────────────────────────────────────────────────────────┤
│ Curr-focus: B  |  ❌ No context                             │
└─────────────────────────────────────────────────────────────┘
```

### Sections

| Section | Component | Purpose |
|---------|-----------|---------|
| Title | Static | App name and branding |
| Left Panel | Vertical | File browser + preview |
| - File List | SelectableFileList | Current directory navigation |
| - Preview Title | Static | Section header |
| - File Preview | Static | File content preview (ready for impl.) |
| Right Panel | Vertical | Chat area |
| - Chat Title | Static | Section header |
| - Chat Display | RichLog | Conversation history with auto-scroll |
| Input Area | Vertical | Message input (multi-line support) |
| - Input Title | Static | Section header |
| - Input Field | MultilineInput | User message composition with wrapping |
| Status Bar | Static | Focus indicator + context status |

## File List Widget (`SelectableFileList`)

### Display Format

```
> ..                        ← Current directory marker (>)
  📄 file1.py              ← File with icon
  📁 src                   ← Directory with icon
  📄 README.md
  📁 tests
  📄 pyproject.toml
```

### Features

**Navigation**:
- UP/DOWN arrows move cursor
- ">" marker shows selected entry
- Parent directory (..) always first entry
- Files and directories sorted alphabetically
- Dot files filtered out (ignored)

**Selection**:
- ENTER on directory: navigate into it
- ENTER on file: select (for L key loading)
- Current directory tracked in `SelectableFileList.current_dir`

**Data Structure**:
- `entries`: List of tuples: `(path: Path, is_dir: bool, display: str)`
- `selected_index`: Current cursor position
- `current_dir`: Current working directory (Path object)

### Methods

```python
load_directory()           # Scan current_dir, populate entries
update_display()           # Render widget with cursor marker
action_cursor_up()         # Decrease selected_index
action_cursor_down()       # Increase selected_index
action_select_cursor()     # Handle ENTER key
get_selected_file()        # Return path of selected item
```

## Focus Management

### Three-Mode System

| Mode | Focus | Active Actions | Key Features |
|------|-------|---|---|
| **BROWSER** (B) | File List | UP/DOWN/ENTER/L/CTRL+L/Q/TAB | Navigate & select files |
| **CHAT** (C) | Chat Display | Scroll UP/DOWN/L/CTRL+L/Q/TAB | Read conversation, load files |
| **INPUT** (I) | Input Field | Text entry/ENTER/Ctrl+Enter/TAB | Type & send messages |

### Focus Switching

```
START (Browser Mode)
  ↓
TAB → CHAT Mode (can scroll chat history)
  ↓
TAB → INPUT Mode (cursor in input field)
  ↓
TAB → BROWSER Mode (back to file list)
  ↓
(cycle continues)
```

**Implementation**:
- Reactive state: `current_focus: reactive("browser")`
- Watch method: `watch_current_focus()` manages focus and CSS classes
- Action: `action_focus_next()` / `action_focus_previous()`
- Visual indicator: Title bars highlighted in orange when focused
- Widget focus: `.focus()` called on relevant widget

### Status Bar Display

```
Curr-focus: B  |  ❌ No context loaded
       ↑                   ↑
  [B/C/I indicator]   [Project context status]
```

## Keyboard Shortcuts

### Browser Mode

| Key | Action | Result |
|-----|--------|--------|
| UP | `action_cursor_up()` | Move cursor up in file list |
| DOWN | `action_cursor_down()` | Move cursor down in file list |
| ENTER | `action_select_cursor()` | Open directory or select file |
| L | `action_load_file()` | Add file to context, show in chat |
| TAB | `action_focus_next()` | Switch to CHAT mode (→ INPUT mode) |
| Shift+TAB | `action_focus_previous()` | Switch to previous mode |
| CTRL+L | `action_load_context()` | Scan entire project, load context |
| Q | `action_app_quit()` | Exit application |

### Chat Mode

| Key | Action | Result |
|-----|--------|--------|
| UP | Scroll up | Read earlier messages |
| DOWN | Scroll down | Read later messages |
| L | `action_load_file()` | Add currently selected file to context |
| TAB | `action_focus_next()` | Switch to INPUT mode |
| Shift+TAB | `action_focus_previous()` | Switch to BROWSER mode |
| CTRL+L | `action_load_context()` | Scan entire project, load context |
| Q | `action_app_quit()` | Exit application |

### Input Mode

| Key | Action | Result |
|-----|--------|--------|
| (any char) | Text input | Type message (multi-line with wrapping) |
| ENTER | New line | Add new line to input text |
| Ctrl+ENTER | Submit (future) | Send message to LLM |
| TAB | `action_focus_next()` | Switch to BROWSER mode |
| Shift+TAB | `action_focus_previous()` | Switch to CHAT mode |
| CTRL+L | `action_load_context()` | Scan entire project, load context |
| Q | `action_app_quit()` | Exit application |
| HOME/END/CTRL+A | Text edit | Standard text editing shortcuts |

**Note**: Text editing shortcuts (HOME, END, CTRL+A, etc.) work normally in INPUT mode via TextArea widget.

## Chat Display (`RichLog`)

### Features

- **Rich Text Markup**: Supports Textual/Rich syntax
- **Auto-scroll**: New messages appear at bottom
- **Highlighting**: Off (plain text rendering)
- **Markup**: Enabled for colored output

### Message Format

**System Message** (on startup):
```
Welcome to KI Code Assistant!
Use UP/DOWN to navigate files, ENTER to select, TAB to switch focus.
```

**File Loaded**:
```
[bold cyan]📄 Added to context:[/] /path/to/file.py
```

**Context Status**:
```
[bold green]✅ Project context loaded: 42 files, 3 languages[/]
```

**User Message**:
```
[bold cyan]You:[/] Tell me about this function
```

**LLM Response**:
```
[bold green]Assistant:[/]
This function does X, Y, and Z...
```

**Error Message**:
```
[bold red]❌ Error: Connection failed[/]
```

**Loading State**:
```
[bold yellow]⏳ Waiting for LLM response...[/]
```

## Input Field (`MultilineInput`)

### Features

- **Custom Widget**: Wraps Textual `TextArea` for multi-line editing
- **Text Wrapping**: Automatic wrapping at terminal width
- **Dynamic Height**: Grows from 2 to 5 lines as content increases
- **Focus-aware**: Integrates with 3-mode focus system
- **Keyboard Support**: ENTER for new line, Ctrl+ENTER for submit

### Behavior

**In BROWSER/CHAT mode**:
- Input field receives no events
- Focus is on file list or chat display
- Input field appears empty/inactive

**In INPUT mode**:
- Input field has focus (visual cursor visible)
- Typing populates the field
- Text automatically wraps to new lines
- ENTER key creates new line in text
- Ctrl+ENTER (future) will trigger submission

**Visible Features**:
- Multi-line text visible at once
- No scrolling needed to see input
- Clear visual boundary showing input extent
- Input title highlighted in orange when focused

**Implementation**:
```python
class MultilineInput(Static):
    """Multi-line input widget with text wrapping."""
    
    def get_value() -> str       # Get current input text
    def set_value(value: str)    # Set input text
    def clear()                  # Clear all text
    def focus()                  # Give focus to text area
    def blur()                   # Remove focus
```

## File Preview Section

### Current State

- **Display**: Static widget showing "No file selected"
- **Purpose**: Ready for implementation
- **Planned Feature**: Show file content when selected

### Planned Implementation

When file selected (via L key):
1. Read file content (with size limit)
2. Detect language/syntax
3. Render in Static widget with syntax highlighting
4. Auto-scroll to relevant section (if context-aware)

## State Indicators

### Status Bar Components

```
Curr-focus: B              ← Focus indicator (B or I)
            └─ Browser (B) or Input (I) mode

❌ No context              ← Context status
✅ Project context loaded: 42 files, 3 languages
```

### Visual Cues

| Element | Visual | Meaning |
|---------|--------|---------|
| ">" in file list | Cursor position | Currently selected entry |
| Title bar color | Orange highlight | Mode has focus (orange background) |
| Chat display | Scrollable | Can read history when in CHAT mode |
| Input field | Multi-line visible | Can see all typed text at once |
| Status bar | "B", "C", or "I" | Current focus mode indicator |

## Error Handling UI

### Error Display Locations

1. **Chat Display**: LLM errors, context load errors
   - Format: `[bold red]❌ Error: {message}[/]`
   - Example: `❌ Error: OpenAI API key not found`

2. **File Loading**: File not found, permission denied
   - Format: `⚠️  No file selected` (if L pressed with no selection)

3. **Project Context**: Directory access errors
   - Caught during scan, reported in chat

## Planned Enhancements

1. **File Preview Auto-Update**: Show content when navigating
2. **Syntax Highlighting**: In file preview
3. **Search/Filter**: Filter file list by name
4. **Multiple File Selection**: Load multiple files to context
5. **File Metadata**: Show size, last modified
6. **Context Visualization**: Display loaded files in chat header
7. **Role Switching**: Change LLM role (Ctrl+R) mid-conversation
8. **Session Management**: Resume previous chat sessions on startup
9. **Export Sessions**: Save conversations as JSON/Markdown
10. **Chat Persistence**: Auto-save chat history between sessions

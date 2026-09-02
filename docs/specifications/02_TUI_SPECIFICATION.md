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
| - Chat Display | RichLog | Conversation history |
| Input Area | Horizontal | Message input |
| - Input Title | Static | Section header |
| - Input Field | FocusAwareInput | User message composition |
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

### Two-Mode System

| Mode | Focus | Active Actions | Disabled Actions |
|------|-------|---|---|
| **BROWSER** (B) | File List | UP/DOWN/ENTER/L/CTRL+L/Q/TAB | Text input |
| **INPUT** (I) | Input Field | Text entry/ENTER/CTRL+L/Q/TAB | UP/DOWN/L |

### Focus Switching

```
START (Browser Mode)
  ↓
TAB → INPUT Mode (cursor in input field)
  ↓
TAB → BROWSER Mode (cursor in file list)
  ↓
(cycle continues)
```

**Implementation**:
- Reactive state: `current_focus: reactive("browser")`
- Watch method: `watch_current_focus()` updates status bar
- Action: `action_focus_next()` / `action_focus_previous()`
- Widget focus: `.focus()` called on relevant widget

### Status Bar Display

```
Curr-focus: B  |  ❌ No context loaded
       ↑                    ↑
    [B=Browser/I=Input]   [Project context status]
```

## Keyboard Shortcuts

### Browser Mode

| Key | Action | Result |
|-----|--------|--------|
| UP | `action_cursor_up()` | Move cursor up in file list |
| DOWN | `action_cursor_down()` | Move cursor down in file list |
| ENTER | `action_select_cursor()` | Open directory or select file |
| L | `action_load_file()` | Add file to context, show in chat |
| TAB | `action_focus_next()` | Switch to INPUT mode |
| Shift+TAB | `action_focus_previous()` | Switch to INPUT mode |
| CTRL+L | `action_load_context()` | Scan entire project, load context |
| Q | `action_app_quit()` | Exit application |

### Input Mode

| Key | Action | Result |
|-----|--------|--------|
| (any char) | Text input | Type message |
| ENTER | `on_key()` in FocusAwareInput | Submit message to LLM |
| TAB | `action_focus_next()` | Switch to BROWSER mode |
| Shift+TAB | `action_focus_previous()` | Switch to BROWSER mode |
| CTRL+L | `action_load_context()` | Scan entire project, load context |
| Q | `action_app_quit()` | Exit application |
| UP/DOWN | (ignored) | No file navigation in input mode |

**Note**: In INPUT mode, text editing shortcuts (HOME, END, CTRL+A, etc.) work normally via Input widget.

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

## Input Field (`FocusAwareInput`)

### Features

- **Custom Widget**: Extends Textual `Input`
- **ENTER Handling**: Custom `on_key()` method
- **Focus-aware**: Only submits when `current_focus == "input"`
- **Placeholder**: (None - empty field)

### Behavior

**In BROWSER mode**:
- Input field receives no events
- Focus is on file list

**In INPUT mode**:
- Input field has focus (visual cursor)
- Typing populates the field
- ENTER key triggers `action_select_cursor()`

**Implementation**:
```python
class FocusAwareInput(Input):
    def on_key(self, event):
        if event.key == "enter" and parent_app.current_focus == "input":
            parent_app.action_select_cursor()
            event.prevent_default()
        else:
            super()._on_key(event)
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
| Input field border | Highlighted | Input has focus |
| File list background | Normal | File list is focused |
| Status "B" | Bold | Browser mode active |
| Status "I" | Bold | Input mode active |

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

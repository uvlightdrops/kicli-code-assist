# Feature Checklist & Implementation Status

## Core Features

### ✅ [DONE] Focus Management

- [x] Browser mode (file list focus)
- [x] Input mode (chat input focus)
- [x] TAB/Shift+TAB to toggle between modes
- [x] Status bar shows current focus (B/I)
- [x] Only one mode active at a time
- [x] Clear visual separation between modes

### ✅ [DONE] File Browser Navigation

- [x] Display current directory entries only (not recursive)
- [x] Show parent directory (..)
- [x] UP/DOWN arrow keys to navigate
- [x] ">" cursor marker for selected file
- [x] File/directory icons (📄 and 📁)
- [x] ENTER to open directories or select files
- [x] Sorted alphabetically
- [x] Filter out dot files (hidden files)
- [x] Handle directory traversal
- [x] Current directory in path tracking

### ✅ [DONE] Chat Input & Submission

- [x] Input field in INPUT mode
- [x] ENTER submits message
- [x] Custom FocusAwareInput widget
- [x] Focus checks before submission
- [x] Clear input field after sending
- [x] Message added to history

### ✅ [DONE] Chat Display

- [x] RichLog widget for message display
- [x] Rich text markup support
- [x] System messages on startup
- [x] User message formatting: `[bold cyan]You:[/] message`
- [x] AI response formatting: `[bold green]Assistant:[/] response`
- [x] Error message formatting: `[bold red]❌ Error:[/]`
- [x] Loading state: `[bold yellow]⏳ Waiting for LLM response...[/]`
- [x] Auto-scroll to latest messages
- [x] Streaming response support

### ✅ [DONE] LLM Integration

- [x] OpenAI provider support (via ki-core)
- [x] Ollama provider support (via ki-core)
- [x] Mock provider for testing
- [x] Provider auto-detection
- [x] Environment variable configuration
- [x] YAML configuration support
- [x] Chat request/response models
- [x] Message streaming
- [x] Error handling for LLM failures

### ✅ [DONE] Project Context

- [x] ProjectContextManager class
- [x] Directory scanning
- [x] File categorization by language
- [x] Language detection by extension
- [x] Key file identification
- [x] Excluded directory filtering
- [x] Context status display
- [x] Integration with ChatSession

### ✅ [DONE] Session Management

- [x] ChatSession class
- [x] Message history tracking
- [x] add_message() method
- [x] get_messages_for_api() with context injection
- [x] get_context_status() summary
- [x] Context loading (CTRL+L)
- [x] System message initialization

### ✅ [DONE] Keyboard Shortcuts

Browser Mode:
- [x] UP - Move cursor up
- [x] DOWN - Move cursor down
- [x] ENTER - Select/open
- [x] L - Load file to context
- [x] TAB - Switch to INPUT
- [x] Shift+TAB - Switch to INPUT
- [x] CTRL+L - Load project context
- [x] Q - Quit

Input Mode:
- [x] ENTER - Submit message
- [x] TAB - Switch to BROWSER
- [x] Shift+TAB - Switch to BROWSER
- [x] CTRL+L - Load project context
- [x] Q - Quit
- [x] Text editing (Home, End, Ctrl+A, etc.)

### ✅ [DONE] UI Layout

- [x] Title bar with app name
- [x] Split-screen layout (left/right)
- [x] File list panel (left)
- [x] Chat display panel (right)
- [x] Input area (bottom)
- [x] Status bar with focus/context info
- [x] Panel titles and headers
- [x] File preview section (placeholder)

### ✅ [DONE] Async Operations

- [x] Non-blocking LLM calls
- [x] app.call_later() for async execution
- [x] Status updates during waiting
- [x] User can navigate while waiting for response
- [x] Exception handling in async context

### ✅ [DONE] Python 3.10 Compatibility

- [x] Removed StrEnum (3.11+ only)
- [x] Used str+Enum pattern instead
- [x] Updated all pyproject.toml files
- [x] Tested with Python 3.10

---

## Pending Features

### 🔄 [PARTIAL] File Preview

**Status**: Widget ready, feature incomplete

- [ ] Auto-update when navigating file list
- [ ] Display file content
- [ ] Syntax highlighting
- [ ] File size limits
- [ ] Language detection for highlighting

**Implementation Plan**:
1. Add method to read file content (with 10KB limit)
2. Detect language from extension
3. Update Static preview widget
4. Call on cursor movement in file list

### 🔄 [PARTIAL] Context Integration

**Status**: Context scanning works, integration partial

- [x] Scan project files
- [x] Categorize by language
- [x] Identify key files
- [ ] Prioritize which files to include in context
- [ ] Limit context size for API
- [ ] Show loaded files in UI

**Implementation Plan**:
1. Add size tracking to ProjectInfo
2. Implement file selection logic (key files first)
3. Display loaded file list in chat
4. Add file count badge in header

### ⏳ [NOT STARTED] Persistent Storage

- [ ] SQLite database for sessions
- [ ] Save/load conversation history
- [ ] Store project context snapshots
- [ ] Session list UI
- [ ] Export conversations

### ⏳ [NOT STARTED] Advanced File Filtering

- [ ] Search/filter file list by name
- [ ] Regex pattern matching
- [ ] Language-specific file selection
- [ ] Gitignore pattern support

### ⏳ [NOT STARTED] Multi-File Selection

- [ ] Mark multiple files (SPACE key)
- [ ] Bulk load to context
- [ ] Display selected file count
- [ ] Clear selection (ESC key)

### ⏳ [NOT STARTED] File Metadata

- [ ] Show file size in list
- [ ] Show last modified date
- [ ] Show line count
- [ ] Show permissions

### ⏳ [NOT STARTED] UI Enhancements

- [ ] Syntax highlighting in code blocks
- [ ] Theme support (dark/light)
- [ ] Configurable colors
- [ ] Font size adjustment
- [ ] Window split ratio adjustment

### ⏳ [NOT STARTED] Context Features

- [ ] @file syntax to reference specific files
- [ ] @function to reference specific functions
- [ ] Selection highlighting in preview
- [ ] Jump to error location

### ⏳ [NOT STARTED] Performance

- [ ] Incremental file scanning
- [ ] Lazy loading for large projects
- [ ] Caching of project structure
- [ ] Background indexing

---

## Known Issues & Limitations

### Current Limitations

1. **File Preview**: Placeholder only, no actual file viewing
2. **Context Size**: No limit checking (could exceed API limits)
3. **Async Model**: Uses `app.call_later()`, not true async/await
4. **No History Persistence**: Sessions lost on exit
5. **File Content**: Never loaded into memory (only path used)
6. **Large Projects**: Scans everything (could be slow for huge projects)

### Potential Improvements

1. Add file size limits to context injection
2. Implement conversation persistence
3. Add incremental project scanning
4. Support .gitignore for filtering
5. Add @file reference syntax
6. Implement file preview with syntax highlighting
7. Add multi-file selection
8. Performance optimization for large codebases

---

## Integration Points

### User → TUI

```
Keyboard Input
  ↓ (Textual key event)
Binding or Widget.on_key()
  ↓
Action Method (e.g., action_cursor_down)
  ↓
State Update (selected_index, current_focus)
  ↓
Display Update (render new UI)
```

### TUI → Chat Session

```
on_input_submitted_manual(msg)
  ↓
chat_session.add_message("user", msg)
  ↓
app.call_later(_send_to_llm_async)
  ↓
get_messages_for_api() [injects context]
  ↓
LLM Request
```

### LLM → TUI

```
LLM Response Stream
  ↓
event.text chunks
  ↓
chat_display.write(text)
  ↓
chat_session.add_message("assistant", full_response)
```

### File Browser → Context

```
L key pressed
  ↓
action_load_file()
  ↓
chat_session.add_message() [optional]
  ↓
(next message includes file in context)
```

### Project Scan → Context

```
CTRL+L pressed
  ↓
action_load_context()
  ↓
ProjectContextManager.scan_project()
  ↓
chat_session.load_project_context()
  ↓
Status bar updated
```

---

## Configuration & Setup

### Entry Point

```
$ kicli-assist tui
```

Defined in: `kicli_code_assist/cli.py`

### Config Files

**Location**: `~/.ki/config.yaml`

**Example**:
```yaml
provider: openai
openai:
  api_key: sk-...
  model: gpt-3.5-turbo
ollama:
  url: http://localhost:11434
  model: llama2
```

### Environment Variables

```bash
export KI_PROVIDER=openai
export KI_OPENAI_KEY=sk-...
export KI_OLLAMA_URL=http://localhost:11434
export KI_OLLAMA_MODEL=llama2
```

---

## Testing Strategy

### Manual Testing Checklist

- [ ] Start TUI: `kicli-assist tui`
- [ ] Navigate files: UP/DOWN arrow keys
- [ ] Change directory: ENTER on directory
- [ ] Switch focus: TAB key
- [ ] Send message: Type text + ENTER in INPUT mode
- [ ] Load file: Select file + L key
- [ ] Load context: CTRL+L
- [ ] Quit: Q key
- [ ] Test with Mock provider: `export KI_PROVIDER=mock`
- [ ] Test with Ollama: Start Ollama, `export KI_PROVIDER=ollama`
- [ ] Test with OpenAI: Set API key, `export KI_PROVIDER=openai`

### Automated Tests

Currently: None (TUI testing is complex)

**Recommendations**:
- Unit tests for ChatSession
- Unit tests for ProjectContextManager
- Unit tests for Config loading
- Integration tests for LLM providers
- Snapshot tests for context formatting

---

## Performance Benchmarks

(To be measured)

- File list rendering: < 100ms for 1000 files
- Message submission to display: < 5s for GPT response
- Project scan time: < 2s for typical project
- Memory usage: < 100MB for chat history + context

---

## Security Considerations

1. **API Keys**: Loaded from env vars, not in code
2. **File Access**: Only reads accessible files (no privilege escalation)
3. **Context Injection**: No code injection (content is text-only)
4. **Input Validation**: None currently (TODO)
5. **Secrets Protection**: .env files scanned but content not exposed

**Recommendations**:
- Add input sanitization for prompt injection
- Mask API keys in logs
- Add rate limiting for API calls
- Validate file paths to prevent directory traversal

# KI Code Assistant - Specification Documentation

This directory contains complete specifications for the KI Code Assistant TUI application. Use this documentation to understand the system architecture, user interface, backend logic, and implementation details.

## Document Guide

### 1. **01_ARCHITECTURE.md** - System Overview
**Start here** if you're new to the project.

- Project overview and goals
- Tech stack and dependencies
- Component breakdown (TUI, ChatSession, Project Context, ki-core)
- Integration points and data flow
- Configuration system
- Error handling and performance considerations

**Who should read**: Architects, project leads, new team members

---

### 2. **02_TUI_SPECIFICATION.md** - User Interface & Interaction
**Reference this** for UI behavior and keyboard shortcuts.

- Screen layout and widget structure
- File browser (`SelectableFileList`) capabilities
- Focus management system (Browser vs Input mode)
- Keyboard shortcuts (complete list)
- Chat display formatting and markup
- Input field behavior
- Status indicators and visual cues

**Who should read**: UI developers, UX designers, QA

---

### 3. **03_BACKEND_SPECIFICATION.md** - Chat & Context Logic
**Reference this** for implementation details of the backend.

- ChatSession class and message management
- ProjectContextManager and file scanning
- Context injection into LLM requests
- LLM provider integration (OpenAI, Ollama, Mock)
- Configuration system and provider detection
- Async execution model
- Error handling strategies

**Who should read**: Backend developers, LLM integration specialists

---

### 4. **04_FEATURE_CHECKLIST.md** - Features & Status
**Use this** to track implementation progress and understand what's done vs. pending.

- ✅ Completed features (with implementation notes)
- 🔄 Partially implemented features
- ⏳ Planned features (not started)
- Known issues and limitations
- Integration points summary
- Configuration requirements
- Performance benchmarks and security considerations

**Who should read**: Project managers, developers planning new features, QA

---

### 5. **05_IMPLEMENTATION_DETAILS.md** - Code Walkthrough
**Deep dive here** when implementing or debugging specific components.

- File locations and structure
- Component-by-component code walkthrough
  - SelectableFileList widget
  - FocusAwareInput widget
  - CodeAssistantApp main application
  - ChatSession
  - ProjectContextManager
- Data flow examples and common patterns
- Debugging tips
- Testing scenarios

**Who should read**: Backend developers, debuggers, code reviewers

---

## Quick Reference

### Key Files

| File | Purpose |
|------|---------|
| `kicli_code_assist/ui/textual_app.py` | TUI application, widgets, and key handlers |
| `kicli_code_assist/chat_session.py` | Chat history and message management |
| `kicli_code_assist/context/project_context.py` | Project scanning and context extraction |
| `ki-core/src/ki_core/config.py` | Configuration loading and LLM provider selection |

### Key Classes

| Class | Location | Purpose |
|-------|----------|---------|
| `CodeAssistantApp` | textual_app.py | Main TUI application container |
| `SelectableFileList` | textual_app.py | File browser widget |
| `FocusAwareInput` | textual_app.py | Message input widget |
| `ChatSession` | chat_session.py | Chat history and context |
| `ProjectContextManager` | project_context.py | Project scanning and indexing |
| `Config` | ki-core config.py | Configuration and provider detection |

### Keyboard Shortcuts (Quick Ref)

**Browser Mode** (file list has focus):
- `UP/DOWN` - Navigate
- `ENTER` - Select/open
- `L` - Load file to context
- `TAB` - Switch to input mode
- `CTRL+L` - Scan project
- `Q` - Quit

**Input Mode** (chat input has focus):
- `ENTER` - Submit message
- `TAB` - Back to browser
- `CTRL+L` - Scan project
- `Q` - Quit

### Configuration

**Environment Variables**:
```bash
export KI_PROVIDER=openai      # or ollama, mock
export KI_OPENAI_KEY=sk-...
export KI_OLLAMA_URL=http://localhost:11434
```

**Config File** (`~/.ki/config.yaml`):
```yaml
provider: openai
openai:
  api_key: sk-...
  model: gpt-3.5-turbo
ollama:
  url: http://localhost:11434
  model: llama2
```

### Running the App

```bash
# Development
cd kicli-code-assist
python -m venv venv
source venv/bin/activate
pip install -e .
kicli-assist tui

# With specific provider
export KI_PROVIDER=mock
kicli-assist tui
```

---

## Feature Status Summary

### ✅ Complete (20 features)

- Focus management (Browser/Input modes)
- File browser navigation (vi-style)
- Chat input and message submission
- Chat display with rich formatting
- LLM integration (OpenAI, Ollama, Mock)
- Project context scanning
- Session management
- All keyboard shortcuts
- UI layout and split-screen design
- Async LLM operations

### 🔄 In Progress (2 features)

- File preview display
- Context size management

### ⏳ Not Started (9 features)

- Persistent storage
- Advanced file filtering
- Multi-file selection
- File metadata display
- Syntax highlighting
- Theme support
- Performance optimization
- Context features (@file, @function syntax)
- UI enhancements

---

## Common Tasks

### Adding a New Keyboard Shortcut

1. Add Binding to `BINDINGS` list in `CodeAssistantApp`
2. Implement `action_*` method in `CodeAssistantApp`
3. Check focus mode if needed (use `if self.current_focus == "browser"`)
4. Update 02_TUI_SPECIFICATION.md with new shortcut

**Example**:
```python
BINDINGS = [
    # ... existing
    Binding("x", "do_something", "Do Something", show=True),
]

def action_do_something(self) -> None:
    """X key handler"""
    self.chat_display.write("Did something!")
```

### Adding Context to LLM Messages

Context is injected in `ChatSession.get_messages_for_api()`. To modify:

1. Edit the system message template in that method
2. Format context info (from `self.project_context`)
3. Append to system text
4. Test with a message

### Implementing File Preview

1. Add display logic to `SelectableFileList.action_select_cursor()`
2. Read file content with size limits (~10KB)
3. Detect language from extension
4. Call `parent_app.update_file_preview(path, content, language)`
5. Update preview widget via `self.preview_display.update(formatted_content)`

### Adding a New LLM Provider

1. Create provider class in ki-core
2. Implement `chat_stream(request: ChatRequest) -> Iterator[ChatEvent]`
3. Update `_detect_best_provider()` in cli.py
4. Add config parsing to ki-core Config class
5. Test with: `export KI_PROVIDER=my_provider`

### Debugging Message Flow

Add logging to trace messages through the system:

```python
# In on_input_submitted_manual
print(f"[INPUT] User message: {msg}")

# In get_messages_for_api
print(f"[API] Total messages: {len(messages)}")

# In _send_to_llm_async
print(f"[LLM] Sending request with {len(api_messages)} messages")
```

---

## Architecture Diagrams

### Message Flow

```
User Input
  ↓
Textual Event
  ↓
Action Handler
  ↓
ChatSession.add_message()
  ↓
app.call_later(async task)
  ↓
get_messages_for_api()  ← injects project context
  ↓
LLM Provider (OpenAI/Ollama/Mock)
  ↓
Response Stream
  ↓
RichLog Widget
  ↓
ChatSession.add_message("assistant", response)
```

### Focus Management

```
START: BROWSER MODE
  ↓
User presses TAB
  ↓
current_focus = "input"
  ↓
input_field.focus()
  ↓
Status bar updates
  ↓
Input Mode Active
  ↓
User presses TAB
  ↓
current_focus = "browser"
  ↓
file_list.focus()
  ↓
Status bar updates
  ↓
Browser Mode Active (loop continues)
```

### File Navigation

```
User in BROWSER mode
  ↓
Presses UP/DOWN
  ↓
SelectableFileList.action_cursor_up/down()
  ↓
selected_index += 1/-1
  ↓
update_display()
  ↓
File list re-rendered
  ↓
">" marker shows new position
```

---

## Testing Approach

### Manual Testing Checklist

- [ ] Navigation works (UP/DOWN)
- [ ] Focus switching works (TAB)
- [ ] Message submission works (ENTER)
- [ ] File selection works (L key)
- [ ] Project context loads (CTRL+L)
- [ ] LLM responses appear (with different providers)
- [ ] Error messages display properly
- [ ] No crashes on invalid inputs

### Automated Testing (Recommended)

- Unit tests for `ChatSession` methods
- Unit tests for `ProjectContextManager` scanning
- Unit tests for config loading
- Integration tests for LLM providers
- Snapshot tests for context formatting

---

## Performance Targets

- File list rendering: < 100ms for 1000 files
- Message submission to response: < 5s (depending on LLM)
- Project scan: < 2s for typical project
- Memory usage: < 100MB for chat + context

---

## Security Notes

1. API keys loaded from environment (not in code)
2. File access respects system permissions
3. No code execution (text-only context)
4. Input validation: **TODO** (add prompt injection protection)
5. Secrets protection: **.env files scanned but not exposed

---

## Future Enhancement Ideas

1. **Database**: Persistent conversation storage
2. **Search**: File list filtering by name/pattern
3. **Multi-select**: Load multiple files at once
4. **Syntax highlighting**: In file preview and chat
5. **Theme system**: Dark/light/custom colors
6. **Code execution**: Run code snippets (sandboxed)
7. **Integration**: Git history, issue tracking, API docs
8. **Performance**: Incremental scanning, lazy loading

---

## Contact & Questions

For questions about specifications:
1. Check the relevant document in this folder
2. See **05_IMPLEMENTATION_DETAILS.md** for code examples
3. Review **04_FEATURE_CHECKLIST.md** for known issues
4. Check git commit history for context on changes

---

## Document Maintenance

**Last Updated**: 2024 (current session)

**Maintenance Guidelines**:
- Update documentation when adding features
- Keep checklist in 04_FEATURE_CHECKLIST.md synchronized
- Update keyboard shortcuts when adding bindings
- Document breaking changes in implementation details
- Keep code examples current with actual code

**When to update**:
- New feature implemented
- UI layout changed
- Backend logic refactored
- New configuration options added
- Bug fixes that affect behavior

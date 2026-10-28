# KI Code Assistant - System Architecture

## Project Overview

KI Code Assistant is an interactive terminal UI (TUI) for project-aware AI-driven code assistance. It enables developers to:
- Browse project files in a vi/netrw-style interface
- Load files into AI context for analysis
- Chat with an LLM (via OpenAI, Ollama, or Mock provider)
- Maintain conversation history with project context

## Tech Stack

- **Language**: Python 3.10+
- **TUI Framework**: Textual 0.20.0+
- **LLM Providers**: 
  - OpenAI GPT API (via ki-core)
  - Ollama local (via ki-core)
  - Mock provider for testing
- **Configuration**: YAML-based (via ki-core)
- **Project Context**: Static file scanning

## System Components

### 1. Core Module (ki-core)

**Responsibility**: Unified LLM provider abstraction and configuration

**Components**:
- `Config` class: YAML + environment variable loading
- Provider adapters: OpenAI, Ollama, Mock
- Message/ChatRequest models for API contracts

**Key File**: `ki-core/src/ki_core/config.py`

**Configuration Sources** (in priority order):
1. Environment variables (e.g., `KI_PROVIDER`, `KI_OPENAI_KEY`)
2. YAML file at `~/.ki/config.yaml`
3. Defaults (Ollama localhost:11434)

**Auto-Detection Logic**:
1. If `KI_PROVIDER` env var set → use that provider
2. Else if OpenAI key available → use OpenAI
3. Else if Ollama reachable → use Ollama
4. Else → use Mock provider

### 2. KI Code Assistant (kicli-code-assist)

**Responsibility**: Interactive TUI for code assistance

**Main Components**:

#### A. TUI Application (`textual_app.py`)
- `CodeAssistantApp`: Main Textual app container
- `SelectableFileList`: Custom widget for vi-style file browsing
- `FocusAwareInput`: Custom Input widget for message submission
- Layout: Split-screen (file browser left, chat right) + input area

#### B. Chat Session (`chat_session.py`)
- Maintains conversation history
- Integrates project context into messages
- Formats messages for LLM API

#### C. Project Context (`context/project_context.py`)
- Scans project directory for relevant files
- Categorizes by language/type
- Provides context status summary

### 3. Integration Points

```
User Input (TUI)
  ↓
Textual Event Handlers
  ↓
Action Methods (focus, navigation, submission)
  ↓
ChatSession.add_message()
  ↓
Project Context Manager
  ↓
ki-core.Config.from_env() → get LLM client
  ↓
LLM Provider (OpenAI/Ollama/Mock)
  ↓
Response Stream → ChatDisplay (RichLog)
  ↓
ChatSession.add_message("assistant", response)
```

## Data Flow

### Message Flow
1. User types in Input field (INPUT mode)
2. Presses ENTER
3. `FocusAwareInput.on_key()` triggers `action_select_cursor()`
4. `on_input_submitted_manual()` called
5. Message added to ChatSession
6. Project context injected via `get_messages_for_api()`
7. Request sent to LLM asynchronously (`_send_to_llm_async()`)
8. Response streamed back to `chat_display` (RichLog)
9. Response added to ChatSession history

### File Navigation Flow
1. User navigates file list (UP/DOWN in BROWSER mode)
2. `SelectableFileList.action_cursor_up/down()` updates cursor
3. `update_display()` re-renders file list with ">" marker
4. User presses ENTER to open directory or select file
5. `action_select_cursor()` in SelectableFileList
6. If directory: `load_directory()` updates current_dir
7. If file: `parent_app.update_file_preview()` (currently no-op)

## State Management

### Current Focus
- **Reactive State**: `current_focus` ("browser" or "input")
- **Watch Method**: `watch_current_focus()` updates status bar
- **Control**: TAB/Shift+TAB toggle between modes

### File Selection
- **Stored In**: `SelectableFileList.selected_index`
- **File List**: `SelectableFileList.entries` (list of tuples)
- **Current Directory**: `SelectableFileList.current_dir`

### Chat State
- **History**: `ChatSession.messages` (list of dicts)
- **Project Context**: `ChatSession.project_context` (dict)
- **Display**: `RichLog` widget (text rendering)

## Configuration Files

### Entry Points
- **TUI Command**: `kicli-assist tui` (defined in `cli.py`)
- **Config Loading**: `ki-core/src/ki_core/config.py`

### Environment Variables
```
KI_PROVIDER=openai|ollama|mock
KI_OPENAI_KEY=sk-...
KI_OLLAMA_URL=http://localhost:11434
KI_OLLAMA_MODEL=llama2
```

### YAML Config (`~/.ki/config.yaml`)
```yaml
provider: openai|ollama
openai:
  api_key: sk-...
ollama:
  url: http://localhost:11434
  model: llama2
```

## Error Handling

- **Missing Provider**: Falls back to Mock provider
- **LLM Errors**: Displayed in chat via RichLog (red error text)
- **File I/O**: Try/except in SelectableFileList.load_directory()
- **Async Failures**: Caught in `_send_to_llm_async()`, shown in chat

## Performance Considerations

- **File Scanning**: Only current directory (not recursive)
- **Async LLM**: Non-blocking with `app.call_later()`
- **Chat Display**: RichLog streams response (no line-buffering)
- **Memory**: No persistent storage (session-only)

## Future Architecture Decisions

1. **Database**: Plan to store conversation sessions
2. **Event Bus**: NATS for multi-service communication
3. **Persistence**: SQLite or PostgreSQL for context/history
4. **Real-time Sync**: WebSocket for multi-user sessions

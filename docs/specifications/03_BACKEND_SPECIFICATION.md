# Backend Specification - Chat & Context

## Chat Session Management (`chat_session.py`)

### Purpose

Manages conversation history and integrates project context into LLM requests.

### Class: `ChatSession`

```python
class ChatSession:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.messages = []                 # Conversation history
        self.project_context = None        # Scanned project info
        self.project_context_manager = None
```

### Message Format

**Internal Storage** (in `self.messages`):
```python
{
    "role": "user" | "assistant" | "system",
    "content": str
}
```

**System Message** (auto-added on init):
```python
{
    "role": "system",
    "content": "You are a helpful AI code assistant..."
}
```

### Key Methods

#### `add_message(role: str, content: str)`

Adds message to history.

```python
def add_message(self, role: str, content: str) -> None:
    self.messages.append({
        "role": role,
        "content": content
    })
```

**Usage**:
- User input: `chat_session.add_message("user", user_text)`
- AI response: `chat_session.add_message("assistant", llm_response)`

#### `load_project_context()`

Scans project directory and extracts context.

```python
def load_project_context(self) -> None:
    self.project_context_manager = ProjectContextManager(self.root_dir)
    self.project_context = self.project_context_manager.scan_project()
```

**Raises**: Exception if scan fails (file I/O errors, etc.)

#### `get_context_status() -> str`

Returns human-readable context summary.

```python
def get_context_status(self) -> str:
    if not self.project_context:
        return "❌ No context"
    
    file_count = len(self.project_context.get("files", []))
    languages = self.project_context.get("languages", {})
    lang_count = len(languages)
    
    return f"✅ Project context: {file_count} files, {lang_count} languages"
```

**Example Output**:
```
✅ Project context: 47 files, 4 languages
```

#### `get_messages_for_api() -> list[dict]`

Formats messages for LLM API call, injecting project context.

```python
def get_messages_for_api(self) -> list[dict]:
    messages = []
    
    # Add system message with context
    system_text = "You are a helpful AI code assistant..."
    if self.project_context:
        system_text += f"\n\nProject context:\n{self._format_context()}"
    
    messages.append({"role": "system", "content": system_text})
    
    # Add conversation history
    messages.extend(self.messages)
    
    return messages
```

**Injected Context Format**:
```
Project context:
- Root: /home/user/myproject
- Files: 47 total
- Languages: Python (28), JavaScript (12), YAML (7)
- Key files: pyproject.toml, package.json, README.md

[Detailed file listing by category]
```

### Planned Features

1. **Persistent Storage**: Save sessions to DB
2. **Context Prioritization**: Load only relevant files
3. **File Versioning**: Track file changes during session
4. **Multi-turn Context**: Maintain context across turns

---

## Project Context Manager (`context/project_context.py`)

### Purpose

Scans project directory and categorizes files for context inclusion.

### Class: `ProjectContextManager`

```python
class ProjectContextManager:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.project_info = None
```

### Class: `ProjectInfo`

```python
@dataclass
class ProjectInfo:
    root: str
    files: list[dict]           # Full file list
    languages: dict[str, int]   # Language counts
    key_files: list[str]        # Important files
    summary: str                # Text summary
```

### Key Methods

#### `scan_project() -> ProjectInfo`

Walks directory tree and categorizes files.

```python
def scan_project(self) -> ProjectInfo:
    all_files = []
    languages = {}
    
    for root, dirs, files in os.walk(self.root_dir):
        # Filter out: .git, __pycache__, node_modules, venv, .env files
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
    
    # Identify key files
    key_files = self._find_key_files(all_files)
    
    return ProjectInfo(
        root=str(self.root_dir),
        files=all_files,
        languages=languages,
        key_files=key_files,
        summary=self._generate_summary(all_files, languages)
    )
```

#### `_detect_language(ext: str) -> str | None`

Maps file extension to language.

```python
LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".jsx": "JavaScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C Header",
    ".cs": "C#",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".xml": "XML",
    ".html": "HTML",
    ".css": "CSS",
    ".md": "Markdown",
    ".txt": "Text",
}
```

#### `_find_key_files(files: list) -> list[str]`

Identifies important files for context.

**Priority Order**:
1. Config files: `pyproject.toml`, `package.json`, `setup.py`, `Makefile`
2. Documentation: `README.md`, `CONTRIBUTING.md`, `API.md`
3. Entry points: `main.py`, `index.js`, `app.py`, `server.go`
4. Environment: `.env.example`, `docker-compose.yml`

**Example**:
```python
KEY_FILE_PATTERNS = [
    "pyproject.toml",
    "package.json",
    "setup.py",
    "requirements.txt",
    "README.md",
    "main.py",
    "app.py",
    "index.js",
]

def _find_key_files(self, files: list) -> list[str]:
    key = []
    for pattern in KEY_FILE_PATTERNS:
        matches = [f["path"] for f in files if f["path"].endswith(pattern)]
        key.extend(matches)
    return list(set(key))  # Remove duplicates
```

### Excluded Directories

```python
EXCLUDED_DIRS = {
    '.git',
    '.github',
    '__pycache__',
    '.pytest_cache',
    '.mypy_cache',
    'node_modules',
    '.venv',
    'venv',
    'env',
    '.env',
    'dist',
    'build',
    '.egg-info',
    '.tox',
    'htmlcov',
    '.coverage',
}
```

### Output Example

```json
{
  "root": "/home/user/myproject",
  "files": [
    {"path": "src/main.py", "ext": ".py", "language": "Python"},
    {"path": "src/utils.py", "ext": ".py", "language": "Python"},
    {"path": "tests/test_main.py", "ext": ".py", "language": "Python"},
    {"path": "README.md", "ext": ".md", "language": "Markdown"},
    {"path": "pyproject.toml", "ext": ".toml", "language": "TOML"}
  ],
  "languages": {
    "Python": 47,
    "JavaScript": 12,
    "YAML": 5,
    "Markdown": 3
  },
  "key_files": [
    "pyproject.toml",
    "README.md",
    "src/main.py"
  ],
  "summary": "Python project (47 files) with JavaScript tooling (12 files)"
}
```

---

## LLM Integration (`cli.py`)

### Provider Detection

```python
def _detect_best_provider() -> str:
    """Auto-detect best available LLM provider."""
    
    # 1. Check environment override
    if os.getenv("KI_PROVIDER"):
        return os.getenv("KI_PROVIDER")
    
    # 2. Check OpenAI availability
    from ki_core import Config
    config = Config.from_env()
    if config.openai_key:
        return "openai"
    
    # 3. Check Ollama availability
    try:
        import requests
        requests.get("http://localhost:11434/api/tags", timeout=2)
        return "ollama"
    except:
        pass
    
    # 4. Default to mock
    return "mock"
```

### Chat Client Creation

```python
def create_client(config: Config, provider: str):
    """Create LLM client for provider."""
    
    if provider == "openai":
        from ki_core.providers.openai_provider import OpenAIProvider
        return OpenAIProvider(config.openai_key)
    elif provider == "ollama":
        from ki_core.providers.ollama_provider import OllamaProvider
        return OllamaProvider(config.ollama_url, config.ollama_model)
    else:
        from ki_core.providers.mock_provider import MockProvider
        return MockProvider()
```

### Message Streaming

All providers implement `chat_stream(request: ChatRequest) -> Iterator[ChatEvent]`

```python
def chat_stream(self, request: ChatRequest):
    """Stream response from LLM."""
    for event in self.provider.stream(request.messages):
        yield ChatEvent(
            text=event.text,
            finish_reason=event.finish_reason
        )
```

**Usage in TUI**:
```python
response_text = ""
for event in self.client.chat_stream(request):
    if event.text:
        response_text += event.text

# Write full response as single piece to avoid line fragmentation
self.chat_display.write(response_text)
```

---

## Configuration System (via ki-core)

### Loading Priority

1. **Environment Variables** (highest)
   - `KI_PROVIDER` → which provider
   - `KI_OPENAI_KEY` → OpenAI API key
   - `KI_OPENAI_MODEL` → OpenAI model (default: gpt-3.5-turbo)
   - `KI_OLLAMA_URL` → Ollama endpoint
   - `KI_OLLAMA_MODEL` → Ollama model

2. **YAML File** (`~/.ki/config.yaml`)
   ```yaml
   provider: openai
   openai:
     api_key: sk-...
     model: gpt-3.5-turbo
   ollama:
     url: http://localhost:11434
     model: llama2
   ```

3. **Defaults** (lowest)
   - Provider: Ollama
   - Ollama URL: http://localhost:11434
   - Ollama Model: llama2

### Config Class

```python
@dataclass
class Config:
    provider: str  # "openai", "ollama", "mock"
    openai_key: str | None
    openai_model: str
    ollama_url: str
    ollama_model: str
    
    @classmethod
    def from_env(cls) -> Config:
        """Load config from env + YAML + defaults."""
        # Implementation in ki-core
```

---

## Error Handling Strategy

### Categories

| Category | Example | Handling |
|----------|---------|----------|
| Config | Missing API key | Fall back to Mock provider |
| Network | LLM unreachable | Show error in chat, don't crash |
| File I/O | Can't read project files | Continue with partial context |
| API | Rate limited | Show message to user |

### User-Facing Messages

All errors displayed in chat with formatting:
```
[bold red]❌ Error: {error_message}[/]
```

No exceptions propagate to crash the TUI.

---

## Async Execution

### Message Submission Flow

1. User types + presses ENTER
2. `on_input_submitted_manual()` called
3. Message added to ChatSession
4. `self.app.call_later(self._send_to_llm_async, msg)` scheduled
5. Control returns immediately (non-blocking)
6. User can continue navigating/typing
7. LLM response streams back into chat

### Implementation

```python
async def _send_to_llm_async(self, msg: str) -> None:
    """Send message to LLM asynchronously (non-blocking)."""
    try:
        api_messages = self.chat_session.get_messages_for_api()
        request = ChatRequest(messages=api_messages)
        response_text = ""
        
        self.chat_display.write("\n[bold green]Assistant:[/]\n")
        for event in self.client.chat_stream(request):
            if event.text:
                response_text += event.text
        
        self.chat_display.write(response_text)
        self.chat_session.add_message("assistant", response_text)
    
    except Exception as e:
        self.chat_display.write(f"[bold red]Error: {str(e)}[/]")
```

**Note**: Uses `app.call_later()`, not true async/await (Textual compatibility).

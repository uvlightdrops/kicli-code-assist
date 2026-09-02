# Project Context for Chat

## Overview

The **ProjectContextManager** enables kicli-assist to understand your entire project and answer questions about it intelligently.

When you ask a question in the chat, the LLM receives:
- Complete project structure
- Dependencies and configuration
- Key file contents (README, config, main files)
- Code statistics

## How It Works

### 1. Project Scanning
```
ProjectContextManager scans the entire project directory:
✓ Finds all source files
✓ Identifies configuration files
✓ Extracts dependencies
✓ Builds project structure tree
```

### 2. Smart File Selection
```
Priority Order:
1. README.md (documentation)
2. setup.py / pyproject.toml (config)
3. Main entry points (main.py, index.js)
4. Source code (*.py, *.js, etc.)
5. Tests and utils
```

### 3. Context Building
```python
from kicli_code_assist.context import ProjectContextManager

manager = ProjectContextManager()
project_info = manager.build_context()

# Get LLM-ready context
context = project_info.to_context_string(max_tokens=4000)
```

### 4. Chat Integration
```
User: "How does the authentication work?"
         ↓
ProjectContextManager adds context:
  "Here's your project:
   - Language: Python
   - Files: 23
   - Structure: [...]
   - Key files: [README, setup.py, auth.py]"
         ↓
LLM responds with full project understanding
```

## Features

### ✅ Project Detection
- Automatically detects primary language (Python, JavaScript, Go, etc.)
- Recognizes mixed-language projects
- Extracts dependencies from multiple package managers

### ✅ Smart File Inclusion
- Ignores: `.git`, `__pycache__`, `node_modules`, `.venv`, etc.
- Prioritizes: README, config files, main entry points
- Limits: Files > 10MB are skipped
- Lines: Counts code lines for file prioritization

### ✅ Dependency Extraction
- Python: requirements.txt, pyproject.toml
- Node: package.json
- Organized by language and type

### ✅ Structure Analysis
- Directory tree (up to depth 3)
- File sizes and line counts
- File type detection (code, config, docs)

### ✅ Context String Generation
- LLM-friendly format
- Respects token limits (default 4000)
- Includes key file contents
- Adds project summary

## API Reference

### ProjectContextManager

```python
manager = ProjectContextManager("/path/to/project")

# Build complete context
info = manager.build_context()

# Get summary
summary = manager.get_summary()

# Add specific file
manager.add_file_to_context("src/models.py")
```

### ProjectInfo

```python
info = manager.build_context()

# Properties
info.name              # Project name
info.language          # Primary language
info.total_files       # Number of files
info.total_size        # Total size in bytes
info.dependencies      # List of deps
info.structure         # Tree view string
info.files             # List of FileInfo objects

# Convert to LLM context
context = info.to_context_string(max_tokens=4000)
```

### FileInfo

```python
for file_info in info.files:
    file_info.path             # Full path
    file_info.relative_path    # Path relative to project
    file_info.size             # File size in bytes
    file_info.lines            # Line count
    file_info.language         # Programming language
    file_info.is_config        # Is it a config file?
    file_info.is_doc           # Is it documentation?
    file_info.priority         # Priority score (higher = include first)
```

## Usage Examples

### Example 1: Simple Project Analysis

```python
from kicli_code_assist.context import ProjectContextManager

manager = ProjectContextManager()
info = manager.build_context()

print(f"Project: {info.name}")
print(f"Language: {info.language}")
print(f"Files: {info.total_files}")
print(f"Size: {info.total_size / 1024:.1f} KB")
```

**Output:**
```
Project: kicli-code-assist
Language: python
Files: 23
Size: 83.1 KB
```

### Example 2: Get Project Context for LLM

```python
manager = ProjectContextManager()
info = manager.build_context()

# Generate context (respects 4000 token limit)
context = info.to_context_string(max_tokens=4000)

# Use in LLM request
response = llm_client.chat(
    messages=[
        {"role": "system", "content": context},
        {"role": "user", "content": "How does the auth work?"}
    ]
)
```

### Example 3: Analyze Project Structure

```python
manager = ProjectContextManager()
info = manager.build_context()

print(info.structure)  # Beautiful tree view
```

**Output:**
```
kicli-code-assist/
  README.md (4.8KB)
  pyproject.toml
  kicli_code_assist/
    __init__.py
    cli.py
    ui/
      tui_app.py (8.2KB)
      file_browser.py (5.9KB)
    context/
      project_context.py (13.3KB)
```

### Example 4: Get Top Files

```python
manager = ProjectContextManager()
info = manager.build_context()

# Top 5 files by priority
for file_info in info.files[:5]:
    lang = f"({file_info.language})" if file_info.language else ""
    print(f"{file_info.relative_path} {lang} - {file_info.priority}")
```

**Output:**
```
README.md  - 100
pyproject.toml  - 90
kicli_code_assist/context/project_context.py (python) - 0
kicli_code_assist/ui/tui_app.py (python) - 0
kicli_code_assist/ui/file_browser.py (python) - 0
```

## Integration with TUI Chat

### Current Flow
```
User types question in TUI
         ↓
Chat sends to LLM (without project context)
```

### Future Flow (Coming in Next Phase)
```
User types question in TUI
         ↓
ProjectContextManager loads project context
         ↓
Chat combines context + user question
         ↓
Sends to LLM with full project understanding
         ↓
LLM provides informed answer
```

## Language Detection

Automatically detects:
- **Python** - .py, .pyx, .pyi files
- **JavaScript** - .js, .jsx files
- **TypeScript** - .ts, .tsx files
- **Go** - .go files
- **Rust** - .rs files
- **Java** - .java files
- **C#** - .cs files
- **Ruby** - .rb files
- **PHP** - .php files

If multiple languages found, returns "mixed"

## Dependency Detection

### Python
- `requirements.txt`
- `pyproject.toml`
- Format: `python:package_name`

### Node.js
- `package.json`
- Format: `node:package_name`

## Configuration Ignored

Files matching these patterns are automatically ignored:
- `.git`, `.gitignore`
- `__pycache__`, `.pyc`, `.pyo`
- `node_modules`
- `.venv`, `venv`
- `.egg-info`, `dist`, `build`
- `.pytest_cache`, `coverage`
- `.vscode`, `.idea`

## Performance

- **Scan time:** ~100ms for typical project (< 1000 files)
- **Memory:** ~1 KB per file entry
- **Context size:** 7-10 KB average (configurable)

## Token Limits

Different models have different token limits:

| Model | Limit | Recommended Context |
|-------|-------|-------------------|
| GPT-4 | 8000 | 4000 tokens |
| GPT-3.5 | 4000 | 2000 tokens |
| Ollama | Variable | 2000-4000 tokens |

Default: `to_context_string(max_tokens=4000)` is safe for most models

## Example Context Output

```markdown
# Project: kicli-code-assist
**Language:** python
**Files:** 23
**Size:** 83.1 KB

## Dependencies
- python:pyproject.toml

## Structure
```
kicli-code-assist/
  README.md (4.8KB)
  pyproject.toml
  kicli_code_assist/
    cli.py (3.2KB)
    ui/
      tui_app.py (8.2KB)
      file_browser.py (5.9KB)
    context/
      project_context.py (13.3KB)
```
```

## Key Files Content
### README.md
# KI Code Assistant
Headless code generation and review tool with interactive TUI...
```

## Customization

### Add Files Dynamically
```python
manager = ProjectContextManager()
info = manager.build_context()

# Add additional files
manager.add_file_to_context("src/critical_module.py")
```

### Custom Project Root
```python
manager = ProjectContextManager("/path/to/my/project")
```

### Token Budget Control
```python
# Use only 2000 tokens
context = info.to_context_string(max_tokens=2000)
```

## Troubleshooting

**Q: Project not detected**
- A: Ensure project root has common files (README, setup.py, package.json, etc.)

**Q: Some files missing from context**
- A: Check token limit - increase `max_tokens` parameter

**Q: Context too large**
- A: Reduce `max_tokens` or call `add_file_to_context()` selectively

**Q: Wrong language detected**
- A: Language detection is heuristic; verify your project language

## Future Enhancements

- [ ] Git history analysis
- [ ] Test coverage information
- [ ] Architecture diagram generation
- [ ] API documentation extraction
- [ ] Type annotation analysis
- [ ] Code complexity metrics
- [ ] Dependency graph visualization

---

**Version:** 1.0  
**Status:** Production Ready ✅

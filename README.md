# KI Code Assistant

Headless code generation and review tool with interactive TUI and Tmux support.

## Features

- 🤖 **Code Generation** - Ask KI to generate/refactor code
- 👁️ **Diff Preview** - Review changes before applying
- 🎮 **Interactive TUI** - Terminal UI with prompt_toolkit
- 🪟 **Tmux Support** - Split-pane layout for remote development
- 🔒 **Safe Execution** - Command whitelisting and audit logging
- 🖥️ **Remote Ready** - Works over SSH with minimal dependencies

## Installation

```bash
# Clone the repo and ensure ki-core is present in the sibling directory
cd ~/dev_flow
git clone <ki-core-repo-url> ki-core
git clone <kicli-code-assist-repo-url> kicli-code-assist

cd ~/dev_flow/kicli-code-assist
python3.10 -m venv venv
source venv/bin/activate

# Install the shared base first, then the assistant
pip install -e ~/dev_flow/ki-core
pip install -e .
```

## Configuration

**See [`docs/KI_CORE_INTEGRATION.md`](docs/KI_CORE_INTEGRATION.md) for setup with ki-core!**

kicli-code-assist uses ki-core for LLM access. To get started:

1. Copy config: `cp /path/to/ki-core/ki.yaml.example ki.yaml`
2. Edit with your LLM provider (OpenAI, Ollama, or company KI server)
3. Create `creds.yaml` for sensitive data (api keys)
4. Run the tool!

## Quick Start

### 1. Simple Chat (TUI)

```bash
kicli-assist tui
```

**Keyboard Shortcuts:**
- `Tab` / `Shift+Tab` - Navigate changes
- `Y` - Accept change
- `N` - Reject change
- `E` - Edit change
- `Ctrl+C` - Quit

### 2. Tmux Layout (Recommended for Remote)

```bash
# Complex layout (code + chat + input)
kicli-assist tmux

# Or simple 2-pane layout
kicli-assist tmux --simple
```

Layouts:

**Complex (3 panes):**
```
┌─────────────────────────────────────┐
│  Code Editor (40%)                  │
├─────────────────────────────────────┤
│  Chat (30%)     │  Diff (30%)       │
└─────────────────────────────────────┘
```

**Simple (2 panes):**
```
┌─────────────────────────────────────┐
│  Code View (40%)                    │
├─────────────────────────────────────┤
│  Chat (60%)                         │
└─────────────────────────────────────┘
```

### 3. Simple Chat (No TUI)

```bash
kicli-assist chat --model gpt-4o-mini
```

## Architecture

```
kicli_code_assist/
├── ui/                     # Terminal UI components
│   ├── tui_app.py         # Main TUI application
│   ├── diff_viewer.py     # Diff display
│   └── chat_ui.py         # Chat component (future)
├── executor/              # Code execution
│   └── safe_executor.py   # Safe command runner with whitelist
├── utils/                 # Utilities
├── examples/              # Examples
├── cli.py                 # CLI entry point
└── tmux_launcher.py       # Tmux session launcher
```

## Safe Code Execution

The executor enforces:

- **Whitelist**: Only approved commands (python, bash, git, grep, etc.)
- **Restrictions**: Blocks dangerous patterns (rm -rf /, dd, fork bombs)
- **Sandbox**: All execution in `/srv/aiagent`
- **Audit Log**: All commands logged to JSON

```python
from kicli_code_assist.executor import SafeCodeExecutor

executor = SafeCodeExecutor(max_timeout=30)
result = executor.execute("python my_script.py", dry_run=False)

print(result.stdout)
print(result.stderr)
print(result.returncode)
```

## Diff Viewer

```python
from kicli_code_assist.ui.diff_viewer import CodeChange, DiffViewer

change = CodeChange(
    filepath="src/main.py",
    original="def old(): pass",
    modified="def new(): return 42"
)

viewer = DiffViewer()
viewer.show_diff(change)
viewer.show_side_by_side(change)
```

## Tmux Keybindings

In Tmux session:

- `Ctrl+B %` - Split vertically
- `Ctrl+B "` - Split horizontally
- `Ctrl+B [Arrow]` - Navigate panes
- `Ctrl+B Z` - Zoom pane
- `Ctrl+B :` - Command prompt

## Supported Platforms

- Ubuntu 24 LTS
- SUSE SLES 15
- Python 3.10+

## Dependencies

- `prompt-toolkit` >= 3.0 - TUI framework
- `rich` >= 13.0 - Rich terminal formatting
- `pygments` - Syntax highlighting
- `pyyaml` - Config files
- `ki-core` - Shared AI client abstraction (integrated) ✅

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run linter
ruff check .
```

## Future Features

- [ ] Code execution with output preview
- [ ] File explorer integration
- [ ] Git diff integration
- [ ] Syntax-aware editing
- [ ] Multi-file diffs
- [ ] Chat history persistence

## License

MIT

## Author

KI Development Team

# KI Code Assistant

**Interactive AI-powered code generation and review tool** with Terminal UI and Tmux support.

[![Tests Passing](https://img.shields.io/badge/tests-passing-brightgreen)](#)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](#)
[![License](https://img.shields.io/badge/license-proprietary-red)](#)

---

## ✨ Features

- 🤖 **Code Generation** - Ask AI to generate, refactor, or document code
- 👁️ **Diff Preview** - Review changes before applying to files
- 💬 **Chat Interface** - Interactive TUI and Tmux layouts
- 📁 **File Browser** - Browse and load project files in context
- 🔒 **Safe Execution** - Command whitelisting and audit logging
- 🌐 **Remote Ready** - Full SSH support for remote development
- ⚙️ **Layered Config** - Environment-specific settings via ki-core
- 🧠 **Project Context** - Automatic file discovery and context loading

---

## 🚀 Quick Start

### Installation

```bash
# Setup directory structure
cd ~/dev_flow
git clone <ki-core-repo> ki-core
git clone <kicli-repo> kicli-code-assist

# Install
cd kicli-code-assist
python3 -m venv .venv
source .venv/bin/activate
pip install -e ../ki-core
pip install -e .
```

### Generate Initial Config

```bash
# Auto-generate config skeleton with all defaults
kicli-assist config init -o ki.yaml

# Edit with your settings
vim ki.yaml
```

### Run

```bash
# Terminal UI (recommended)
kicli-assist tui

# Tmux layout
kicli-assist tmux

# Simple chat
kicli-assist chat
```

---

## 📚 Documentation

### User Guides
- **[Installation Guide](INSTALLATION.md)** - Detailed setup instructions
- **[Chat Workflow Guide](docs/CHAT_WITH_FILES_WORKFLOW.md)** - Using chat with files
- **[Diff User Guide](docs/DIFF_USER_GUIDE.md)** - Reviewing and applying diffs
- **[File Browser Guide](docs/FILE_BROWSER.md)** - Browsing project files
- **[Chat History Guide](docs/CHAT_HISTORY_AND_PROMPTS.md)** - Session management

### Technical Reference
- **[Configuration System](docs/KI_CORE_INTEGRATION.md)** - Layered config setup
- **[Project Context](docs/PROJECT_CONTEXT.md)** - Context detection and management
- **[Integration Status](INTEGRATION_STATUS.md)** - Current feature status

### Feature Status
- **[Customer Requests](docs/customer_requests.md)** - Tracked customer features
- **[Centralized Tracking](../../yaml_cfg_wizard/docs/FEATURE_STATUS.md)** - Full ecosystem status

### Legacy Documentation
- **[Archive](docs/archive/)** - Historical development phases (Phases 2-5)

---

## 🛠️ Commands

### TUI
```bash
kicli-assist tui               # Terminal UI
kicli-assist tui --provider openai  # Override provider
```

### Chat
```bash
kicli-assist chat              # Interactive chat
kicli-assist chat --model gpt-4     # Specific model
```

### Config Management
```bash
kicli-assist config init              # Generate skeleton
kicli-assist config init -o config.yaml  # Custom path

# Config inspection (via yaml-cfg-wizard)
yaml-cfg config show key
yaml-cfg config list
yaml-cfg config verify config.yaml schema.yaml
```

### System
```bash
kicli-assist doctor            # Environment diagnostics
kicli-assist openinterpreter   # Execute code with AI
kicli-assist tmux              # Tmux multi-pane layout
```

---

## ⚙️ Configuration

### Schema-Based System

All configuration is **schema-driven** via `yaml-cfg-wizard`:

1. **Base Schema** (ki-core)
   ```yaml
   ki-core/src/ki_core/schema/config.schema.yaml
   ```

2. **App Schema** (kicli-code-assist)
   ```yaml
   kicli-code-assist/schema/kicli.schema.yaml
   ```

3. **Resolution Order** (highest to lowest priority)
   - Environment variables (`KI_CFG_*`)
   - Runtime files (`config/runtime/`)
   - Stage overrides (`config/stages/`)
   - Profile overrides (`config/profiles/`)
   - Default values (`config/defaults/`)
   - Config file (`ki.yaml`)
   - Schema defaults

### Generate Skeleton

```bash
kicli-assist config init -o ki.yaml
```

This generates a complete config file with:
- All LLM providers (OpenAI, Ollama, KI)
- Knowledge base settings
- Storage paths
- App-specific settings (context, diff, etc.)
- All defaults from merged schemas

### Edit Config

```yaml
# ki.yaml
llm:
  default_provider: openai
  providers:
    openai:
      api_key: sk-...
      model: gpt-4

apps:
  kicli:
    context:
      max_files: 10
      cache_enabled: true
```

### Override with Environment

```bash
# Export to override config values
export KI_CFG_LLM__DEFAULT_PROVIDER=openai
export KI_CFG_APPS__KICLI__CONTEXT__MAX_FILES=20

kicli-assist tui  # Uses env overrides
```

---

## 🧠 How It Works

### Chat Workflow

1. **Load Context** - Browse and select files to include
2. **Ask Question** - Chat with AI about your code
3. **Review Diff** - AI suggests changes (diff preview)
4. **Apply Changes** - Accept/reject modifications
5. **Iterate** - Continue conversation with updated context

### File Discovery

- Auto-discovers Python/JS/TS projects
- Respects `.gitignore` exclusions
- Intelligent relevance ranking
- Configurable context limits

### Safe Execution

- Command whitelisting (git, python, npm, etc.)
- Audit logging of all operations
- Dry-run capability
- User confirmation prompts

---

## 🔧 Development

### Project Structure

```
kicli-code-assist/
├── kicli_code_assist/
│   ├── cli.py              # CLI entrypoint
│   ├── ui/
│   │   ├── textual_app.py  # TUI implementation
│   │   └── components/     # UI components
│   ├── executor/           # Code execution
│   ├── diff/               # Diff engine
│   └── context/            # Project context
├── schema/
│   └── kicli.schema.yaml   # App-specific schema
├── config/
│   ├── defaults.yaml       # Generated defaults
│   ├── profiles/           # Profile overrides
│   └── stages/             # Stage overrides
├── docs/
│   ├── archive/            # Legacy phase docs
│   └── *.md                # Current guides
└── tests/                  # Test suite
```

### Running Tests

```bash
pytest tests/
pytest tests/ -v            # Verbose
pytest tests/test_diff.py   # Specific test
```

### Configuration for Development

```bash
# Create local dev config
kicli-assist config init

# Use local Ollama
export KI_CFG_LLM__DEFAULT_PROVIDER=ollama
export KI_CFG_OLLAMA__BASE_URL=http://localhost:11434

kicli-assist tui
```

---

## 📊 Current Status

**2 of 5 customer features complete:**
- ✅ Schema-based configuration system
- ✅ Chat history export
- 🚧 TUI focus management (partial)
- ⏳ Path security restrictions (pending)
- ⏳ Prompt templates (pending)

See [docs/customer_requests.md](docs/customer_requests.md) for details.

---

## 🔗 Related Projects

- **[ki-core](../../ki-core/)** - Configuration and LLM provider management
- **[yaml-cfg-wizard](../../yaml_cfg_wizard/)** - Config utilities and CLI
- **[ki-knowledge](../../ki-knowledge/)** - Knowledge base integration (optional)

---

## 📝 License

Proprietary - All rights reserved

---

## 🤝 Support

- **Issues:** Report via GitHub issues
- **Documentation:** See [docs/](docs/)
- **Config Help:** `kicli-assist doctor`
- **CLI Help:** `kicli-assist --help`

---

**Last Updated:** 2026-09-05  
**Version:** 0.1 (Foundation Complete)

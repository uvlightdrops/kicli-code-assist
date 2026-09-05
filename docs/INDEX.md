# Documentation Index

Welcome to kicli-code-assist documentation. This guide will help you navigate all available resources.

---

## 📖 Start Here

- **[README.md](../README.md)** - Project overview and quick start
- **[INSTALLATION.md](../INSTALLATION.md)** - Detailed setup instructions
- **[customer_requests.md](customer_requests.md)** - Feature status and tracking

---

## 🎯 User Guides

### Getting Started
- **[KI_CORE_INTEGRATION.md](KI_CORE_INTEGRATION.md)** - How config system works
- **[INSTALLATION.md](../INSTALLATION.md)** - Step-by-step setup

### Using the Tool
- **[CHAT_WITH_FILES_WORKFLOW.md](CHAT_WITH_FILES_WORKFLOW.md)** - Chat workflow with files
- **[FILE_BROWSER.md](FILE_BROWSER.md)** - Using the file browser
- **[DIFF_USER_GUIDE.md](DIFF_USER_GUIDE.md)** - Reviewing and applying diffs
- **[CHAT_HISTORY_AND_PROMPTS.md](CHAT_HISTORY_AND_PROMPTS.md)** - Chat sessions and history

### Configuration
- **[KI_CORE_INTEGRATION.md](KI_CORE_INTEGRATION.md)** - Layered config system
- **[CONFIG_INTEGRATION.md](CONFIG_INTEGRATION.md)** - Config resolution order

---

## 🔧 Technical Reference

### Architecture & Design
- **[PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)** - Context detection and management
- **[INTEGRATION_STATUS.md](../INTEGRATION_STATUS.md)** - Current feature implementation status

### Project Structure
```
kicli-code-assist/
├── kicli_code_assist/      # Main package
│   ├── cli.py              # CLI entrypoint
│   ├── ui/                 # Terminal UI
│   ├── executor/           # Code execution
│   ├── diff/               # Diff engine
│   └── context/            # Project context
├── schema/                 # JSON schemas
├── config/                 # Config templates
├── docs/                   # Documentation
│   ├── archive/            # Legacy phases
│   └── *.md                # Current guides
├── tests/                  # Test suite
└── README.md               # Main readme
```

---

## 📊 Feature Status

### Current Implementation
- ✅ Schema-based configuration (complete)
- ✅ Chat history export (complete)
- 🚧 TUI focus management (partial)
- ⏳ Path security (pending)
- ⏳ Prompt templates (pending)

**See [customer_requests.md](customer_requests.md) for full details.**

### Centralized Tracking
Full ecosystem status (ki-core, yaml-cfg-wizard, kicli) tracked in:
- **[yaml-cfg-wizard FEATURE_STATUS.md](../../yaml_cfg_wizard/docs/FEATURE_STATUS.md)**

---

## 📚 Related Projects

- **[ki-core](../../ki-core/)** - LLM providers and configuration
- **[yaml-cfg-wizard](../../yaml_cfg_wizard/)** - Configuration utilities
- **[ki-knowledge](../../ki-knowledge/)** - Knowledge base (optional)

---

## 💾 Legacy Documentation

All historical development phases are archived in:
- **[docs/archive/](archive/)** - Phases 2-5 documentation

---

## 🚀 Quick Links

### Commands
```bash
# Start using the tool
kicli-assist tui               # Terminal UI
kicli-assist chat              # Simple chat
kicli-assist tmux              # Tmux layout
kicli-assist config init       # Generate config

# Get help
kicli-assist --help
kicli-assist doctor            # Environment check
```

### Config
```bash
# View configuration
yaml-cfg-wizard config show [KEY]
yaml-cfg-wizard config list
yaml-cfg-wizard config paths

# Validate
yaml-cfg-wizard config verify config.yaml schema.yaml
```

### Development
```bash
pytest tests/                  # Run tests
ruff check .                   # Lint
ruff format .                  # Format
```

---

## 🤝 Support

- **Documentation:** This folder
- **Config Help:** `kicli-assist doctor`
- **CLI Help:** `kicli-assist --help`
- **Issues:** GitHub issues

---

**Last Updated:** 2026-09-05

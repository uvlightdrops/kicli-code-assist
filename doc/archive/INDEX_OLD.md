# Documentation Index

Welcome to kicli-code-assist documentation. This guide will help you navigate all available resources.

---

## 📖 Start Here

- **[README.md](../README.md)** - Project overview and quick start
- **[PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)** - Ecosystem context and project scope

### Current Status & Requests
- **[tracking/customer_requests.md](tracking/customer_requests.md)** - 📝 Feature backlog & priorities
- **[tracking/PHASE_2_SUMMARY.md](tracking/PHASE_2_SUMMARY.md)** - Latest phase summary
- **[features/FEATURES_IMPLEMENTED.md](features/FEATURES_IMPLEMENTED.md)** - ✅ Completed features

---

## 🎯 User & Admin Guides

### Getting Started
- **[guides/INSTALLATION.md](guides/INSTALLATION.md)** - Step-by-step setup
- **[guides/YAML_CONFIG_SYSADMIN.md](guides/YAML_CONFIG_SYSADMIN.md)** - Configuration administration

### Using the Tool
- **[features/CHAT_WITH_FILES_WORKFLOW.md](features/CHAT_WITH_FILES_WORKFLOW.md)** - Complete usage workflow
- **[features/FILE_BROWSER.md](features/FILE_BROWSER.md)** - Navigating and selecting files
- **[features/DIFF_USER_GUIDE.md](features/DIFF_USER_GUIDE.md)** - Reviewing and applying diffs
- **[features/UI_TABS.md](features/UI_TABS.md)** - Terminal UI navigation

### Security & Configuration
- **[guides/SECURITY.md](guides/SECURITY.md)** - Path restrictions and security settings
- **[guides/SECRETS_MANAGEMENT.md](guides/SECRETS_MANAGEMENT.md)** - Secret handling
- **[guides/CONFIG_VALIDATION_GUIDE.md](guides/CONFIG_VALIDATION_GUIDE.md)** - Config validation
- **[guides/PRODUCTION_DEPLOYMENT.md](guides/PRODUCTION_DEPLOYMENT.md)** - Production deployment guide
- **[guides/TEXTUAL_BEST_PRACTICES_REVIEW.md](guides/TEXTUAL_BEST_PRACTICES_REVIEW.md)** - UI development practices

---

## 🏗️ Architecture & Design

### System Design
- **[architecture/PROJECT_STRUCTURE.md](architecture/PROJECT_STRUCTURE.md)** - Project codebase organization
- **[architecture/CODEBASE_ASSESSMENT.md](architecture/CODEBASE_ASSESSMENT.md)** - Architecture assessment
- **[architecture/CLI_ARCHITECTURE_ROADMAP.md](architecture/CLI_ARCHITECTURE_ROADMAP.md)** - CLI design
- **[architecture/SHELL_EXECUTION_ARCHITECTURE_REVIEW.md](architecture/SHELL_EXECUTION_ARCHITECTURE_REVIEW.md)** - Shell integration
- **[architecture/CONFIG_INTEGRATION.md](architecture/CONFIG_INTEGRATION.md)** - Config resolution layers
- **[architecture/PHASE_4_ARCHITECTURE.md](architecture/PHASE_4_ARCHITECTURE.md)** - Latest architecture

### Features & Workflows
- **[features/AI_WORKFLOW.md](features/AI_WORKFLOW.md)** - AI integration workflow
- **[features/CHAT_HISTORY_AND_PROMPTS.md](features/CHAT_HISTORY_AND_PROMPTS.md)** - Chat session management
- **[features/PROMPT_MANAGEMENT_DESIGN.md](features/PROMPT_MANAGEMENT_DESIGN.md)** - Prompt template system
- **[features/SHELL_COMMAND_EDITING.md](features/SHELL_COMMAND_EDITING.md)** - Shell command feature
- **[features/SHELL_EXECUTION_IMPLEMENTATION.md](features/SHELL_EXECUTION_IMPLEMENTATION.md)** - Execution implementation

---

## 📊 Development & Tracking

### Project Phases & Status
- **[tracking/PHASE1_COMPLETE.md](tracking/PHASE1_COMPLETE.md)** - Phase 1: Prompt Management
- **[tracking/PHASE_2_SUMMARY.md](tracking/PHASE_2_SUMMARY.md)** - Phase 2: Config System
- **[tracking/PHASE3_COMPLETE.md](tracking/PHASE3_COMPLETE.md)** - Phase 3: Error Handling & Validation
- **[tracking/PHASE_3_STRATEGY.md](tracking/PHASE_3_STRATEGY.md)** - Phase 3 strategy
- **[tracking/PHASE_4_COMPLETION_REPORT.md](tracking/PHASE_4_COMPLETION_REPORT.md)** - Phase 4: Async LLM & Integration
- **[tracking/PHASE_4_ROADMAP.md](tracking/PHASE_4_ROADMAP.md)** - Phase 4 roadmap
- **[tracking/PHASE_A_LOGGING_SUMMARY.md](tracking/PHASE_A_LOGGING_SUMMARY.md)** - Logging implementation
- **[tracking/PHASE_B_TUI_LOGGING_SUMMARY.md](tracking/PHASE_B_TUI_LOGGING_SUMMARY.md)** - TUI logging progress

### Feature & Integration Tracking
- **[tracking/customer_requests.md](tracking/customer_requests.md)** - Feature backlog & priorities
- **[tracking/IMPLEMENTATION_STATUS.md](tracking/IMPLEMENTATION_STATUS.md)** - Implementation checklist
- **[tracking/INTEGRATION_STATUS.md](tracking/INTEGRATION_STATUS.md)** - Integration status
- **[tracking/PROJECT_STATUS.md](tracking/PROJECT_STATUS.md)** - Current project status
- **[tracking/DEPLOYMENT_READINESS.md](tracking/DEPLOYMENT_READINESS.md)** - Deployment readiness

### Bug Fixes & Improvements
- **[tracking/SHELL_EXECUTION_FIX.md](tracking/SHELL_EXECUTION_FIX.md)** - Shell execution bug fixes
- **[tracking/SHELL_EXECUTION_RESEARCH.md](tracking/SHELL_EXECUTION_RESEARCH.md)** - Shell execution research

---

## 🚀 Quick Links

### Commands
```bash
# Start using the tool
kicli-assist tui               # Terminal UI
kicli-assist chat              # Simple chat
kicli-assist config skeleton   # Generate config

# Get help
kicli-assist --help
kicli-assist doctor            # Environment check
```

### Development
```bash
pytest tests/                  # Run tests
ruff check .                   # Lint
ruff format .                  # Format
```

---

## 📚 Related Projects

- **[ki-core](../../ki-core/)** - LLM providers and configuration
- **[yaml-cfg-wizard](../../yaml_cfg_wizard/)** - Configuration utilities
- **[ki-ecosystem](../../ki-ecosystem/)** - Ecosystem management

---

## 📁 Folder Organization

```
docs/
├── architecture/           # System design & architecture patterns
├── features/              # Feature documentation & workflows
├── guides/                # Admin guides, how-tos, best practices
├── tracking/              # Project phases, status, bug fixes, PRs
├── integration/           # Cross-system integration (optional)
├── specifications/        # Technical specifications
├── archive/               # Legacy documentation (Phase 2, 5, old roadmaps)
├── INDEX.md              # This file
└── PROJECT_CONTEXT.md    # Project overview
```

---

**Last Updated:** 2026-10-19

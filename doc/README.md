# KI Code Assistant Documentation

Complete documentation for the KI Code Assistant project, organized by topic and purpose.

## 📖 Quick Navigation

### 🚀 Getting Started
- **[Installation Guide](guides/INSTALLATION.md)** - Setup and installation instructions
- **[Quick Start](guides/)** - Essential guides for new users

### 📚 User Guides
- **[Chat Workflow Guide](features/CHAT_WITH_FILES_WORKFLOW.md)** - Using chat with files
- **[Diff User Guide](features/DIFF_USER_GUIDE.md)** - Reviewing and applying diffs
- **[File Browser Guide](features/FILE_BROWSER.md)** - Browsing project files
- **[Chat History Guide](features/CHAT_HISTORY_AND_PROMPTS.md)** - Session management
- **[Configuration System](guides/YAML_CONFIG_SYSADMIN.md)** - Layered config setup
- **[Shell Command Editing](features/SHELL_COMMAND_EDITING.md)** - Safe command execution
- **[VI Editor Guide](guides/VI_EDITOR_GUIDE.md)** - VI mode editing

### 🏗️ Architecture & Design
- **[Architecture Guides](architecture/)** - System architecture and design decisions
- **[Agent Architecture](architecture/AGENT_COORDINATION_ARCHITECTURE.md)** - Agent coordination
- **[AI Architecture Best Practices](architecture/AI_ARCHITECTURE_BEST_PRACTICES_REVIEW.md)** - Design patterns
- **[Agent UI Architecture](architecture/PROGRAMMING_AGENT_UI_ARCHITECTURE.md)** - UI design
- **[Web Frontend Design](architecture/WEB_FRONTEND_DESIGN.md)** - Frontend architecture

### ⚙️ Technical Reference
- **[Specifications](specifications/)** - Detailed technical specifications
- **[Features Implemented](features/FEATURES_IMPLEMENTED.md)** - Feature status
- **[Project Context](guides/PROJECT_CONTEXT.md)** - Context detection and management
- **[Security Guide](guides/SECURITY.md)** - Security best practices

### 🚀 Deployment
- **[Production Deployment](guides/PRODUCTION_DEPLOYMENT.md)** - Production setup
- **[Web Deployment Guide](guides/WEB_DEPLOYMENT_GUIDE.md)** - Web UI deployment
- **[Secrets Management](guides/SECRETS_MANAGEMENT.md)** - Handling credentials
- **[Semi-Production Deployment](deployment/SEMI_PROD_DEPLOYMENT.md)** - Staging setup

### 💾 Server Management
- **[Server Management Overview](server/SERVER_MANAGEMENT_README.md)** - Overview and quick start
- **[Server Management Design](server/SERVER_MANAGEMENT_DESIGN.md)** - Architecture and design
- **[Server Management Flows](server/SERVER_MANAGEMENT_FLOWS.md)** - Workflow diagrams
- **[Server Management Implementation](server/SERVER_MANAGEMENT_IMPLEMENTATION.md)** - Implementation details
- **[Server Management Decisions](server/SERVER_MANAGEMENT_DECISIONS.md)** - Decision log

### 📈 Development Phases
- **[Phase Documentation](phases/)** - Phase-specific documentation and reports
- **[Phase 5 Reports](phases/PHASE_5_*.md)** - Latest phase updates
- **[Hybrid Agent Implementation](architecture/HYBRID_AGENT_IMPLEMENTATION_PLAN.md)** - Phase 1 hybrid approach

### 📑 Tracking & Status
- **[Implementation Status](tracking/IMPLEMENTATION_STATUS.md)** - Current implementation status
- **[Project Status](tracking/PROJECT_STATUS.md)** - Overall project status
- **[Customer Requests](tracking/customer_requests.md)** - Tracked customer features
- **[Deployment Readiness](tracking/DEPLOYMENT_READINESS.md)** - Deployment checklist

### 📦 Features & Integration
- **[Features Overview](features/)** - All feature documentation
- **[Integration Guide](integration/OPTION_C_INTEGRATION_GUIDE.md)** - Integration patterns
- **[AI Workflow](features/AI_WORKFLOW.md)** - AI integration workflow

### 📚 Archive & Legacy
- **[Archive](archive/)** - Historical development phases and decision documents
- **[Phase Reports](archive/phase-reports/)** - Phase completion reports

---

## 📂 Directory Structure

```
doc/
├── guides/              # User guides and tutorials
├── architecture/        # System architecture and design docs
├── features/            # Feature documentation
├── deployment/          # Deployment configurations and guides
├── specifications/      # Technical specifications
├── tracking/            # Project tracking and status
├── phases/              # Phase-specific documentation
├── server/              # Server management documentation
├── archive/             # Historical documentation
└── README.md            # This file
```

---

## 🔍 Finding What You Need

| I want to... | Start here |
|---|---|
| Get the project running | [Installation Guide](guides/INSTALLATION.md) |
| Understand the system | [Architecture Guides](architecture/) |
| Deploy to production | [Production Deployment](guides/PRODUCTION_DEPLOYMENT.md) |
| Check feature status | [Features Implemented](features/FEATURES_IMPLEMENTED.md) |
| Review recent changes | [Phase Documentation](phases/) |
| Manage a running server | [Server Management](server/) |
| See what was built before | [Archive](archive/) |

---

## 📋 Document Index

### Guides
- CONFIG_VALIDATION_GUIDE.md
- HOT_RELOAD_DEV.md
- INSTALLATION.md
- PRODUCTION_DEPLOYMENT.md
- SECRETS_MANAGEMENT.md
- SECURITY.md
- TEXTUAL_BEST_PRACTICES_REVIEW.md
- VI_EDITOR_GUIDE.md
- WEB_DEPLOYMENT_GUIDE.md
- YAML_CONFIG_SYSADMIN.md

### Architecture
- AI_ARCHITECTURE_BEST_PRACTICES_REVIEW.md
- CLI_ARCHITECTURE_ROADMAP.md
- CODEBASE_ASSESSMENT.md
- CONFIG_INTEGRATION.md
- PHASE_4_ARCHITECTURE.md
- PROJECT_STRUCTURE.md
- SHELL_EXECUTION_ARCHITECTURE_REVIEW.md
- WEB_EDITOR_EDIT_CAPABILITIES.md
- WEB_EDITOR_FRAMEWORKS_COMPARISON.md
- WEB_FRONTEND_DESIGN.md
- WEB_IMPLEMENTATION_PLAYBOOK.md

### Features
- AI_WORKFLOW.md
- CHAT_HISTORY_AND_PROMPTS.md
- CHAT_WITH_FILES_WORKFLOW.md
- DIFF_USER_GUIDE.md
- FEATURES_IMPLEMENTED.md
- FILE_BROWSER.md
- PROMPT_MANAGEMENT_DESIGN.md
- SHELL_COMMAND_EDITING.md
- SHELL_EXECUTION_IMPLEMENTATION.md
- UI_TABS.md

### Specifications
- 01_ARCHITECTURE.md
- 02_TUI_SPECIFICATION.md
- 03_BACKEND_SPECIFICATION.md
- 04_FEATURE_CHECKLIST.md
- 05_IMPLEMENTATION_DETAILS.md
- README.md

### Server Management
- SERVER_MANAGEMENT_README.md
- SERVER_MANAGEMENT_DESIGN.md
- SERVER_MANAGEMENT_FLOWS.md
- SERVER_MANAGEMENT_IMPLEMENTATION.md
- SERVER_MANAGEMENT_DECISIONS.md

### Phases
- PHASE_1_HYBRID_IMPLEMENTATION.md
- PHASE_1_SUMMARY.md
- PHASE_2_EXECUTIVE_SUMMARY.md
- PHASE_2A_INTENT_DETECTOR_COMPLETE.md
- PHASE_2_ARCHITECTURE_COMPARISON.md
- PHASE_2B_IMPLEMENTATION_COMPLETE.md
- PHASE_2C_IMPLEMENTATION_COMPLETE.md
- PHASE_2_TECHNICAL_SPEC.md
- PHASE_5_1_SUMMARY.md
- PHASE_5_4_SUMMARY.md
- PHASE_5_4_PLAN.md

### Deployment
- kicli-web-option1.conf
- kicli-web-option2.conf
- SEMI_PROD_DEPLOYMENT.md

### Tracking
- IMPLEMENTATION_STATUS.md
- PROJECT_STATUS.md
- customer_requests.md
- DEPLOYMENT_READINESS.md

### Integration
- OPTION_C_INTEGRATION_GUIDE.md

---

## 🔗 Related Resources

- **[KI Core Documentation](../../ki-core/doc/)** - Core framework docs
- **[YAML Configuration Wizard](../../yaml_cfg_wizard/doc/)** - Config management tool
- **[FlowPy](../../flowpy/)** - Python automation library

---

**Last Updated:** October 28, 2026
**Total Documents:** 100+
**Sections:** 12

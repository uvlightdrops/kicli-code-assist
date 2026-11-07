---
title: Guides & How-To Documentation
project: kicli-code-assist
scope: guides
purpose: Index and navigation for operational guides, tutorials, and setup instructions
created: 2026-11-02T13:00:00+01:00
updated: 2026-11-07T17:30:00+01:00
update_reason: Added comprehensive navigation table, added semantic relations, PHASE 2 guides cleanup
status: active
---

# Guides & How-To Documentation

**Purpose:** Operational guides, tutorials, and setup instructions for kicli-code-assist.

---

## 📋 Guide Index

| Category | Document | Purpose | Audience | Status |
|----------|----------|---------|----------|--------|
| **Installation/Setup** | [INSTALLATION.md](INSTALLATION.md) | Development environment setup | Developers | ✅ Complete |
| | [TUI_QUICK_START.md](TUI_QUICK_START.md) | Quick start for TUI client | End Users | ✅ Complete |
| **Configuration** | [CONFIG_VALIDATION_GUIDE.md](CONFIG_VALIDATION_GUIDE.md) | Config file validation & ConfigManager | Developers | ✅ Complete |
| | [HOT_RELOAD_DEV.md](HOT_RELOAD_DEV.md) | Hot-reload during development | Developers | ✅ Complete |
| | [YAML_CONFIG_SYSADMIN.md](YAML_CONFIG_SYSADMIN.md) | YAML config reference for admins | DevOps/Admins | ✅ Complete |
| **Deployment** | [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) | Production deployment guide | DevOps/Admins | ✅ Complete |
| | [WEB_DEPLOYMENT_GUIDE.md](WEB_DEPLOYMENT_GUIDE.md) | Web frontend & service deployment | DevOps/Admins | ✅ Complete |
| **Security** | [SECRETS_MANAGEMENT.md](SECRETS_MANAGEMENT.md) | Managing secrets & env vars | Developers/DevOps | ✅ Complete |
| | [SECURITY.md](SECURITY.md) | Security best practices | All Roles | ✅ Complete |
| **Project Context** | [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) | Architecture & project overview | Developers | ✅ Complete |
| | [PROJECT_MANAGEMENT.md](PROJECT_MANAGEMENT.md) | Phase tracking & project status | PMs/Leads | ✅ Complete |
| **Best Practices** | [TEXTUAL_BEST_PRACTICES_REVIEW.md](TEXTUAL_BEST_PRACTICES_REVIEW.md) | TUI/Textual framework best practices | Developers | ✅ Complete |
| | [VI_EDITOR_GUIDE.md](VI_EDITOR_GUIDE.md) | Vi/vim integration guide | Developers | ✅ Complete |

**Legend:** ✅ Complete | 🚧 In Progress | ⚠️ Needs Review | 📝 Planned

---

## Related Documentation Folders

| Folder | Purpose | Link |
|--------|---------|------|
| **backend/** | REST API specs, workflow orchestration, data layer | [→ Backend Docs](../backend/) |
| **features/** | Feature specifications and implementation details | [→ Features](../features/) |
| **architecture/** | System design, patterns, and technical decisions | [→ Architecture](../architecture/) |
| **refactorings/** | Code refactoring history and patterns | [→ Refactorings](../refactorings/) |
| **phases/** | Phase summaries and completion reports | [→ Phases](../phases/) |
| **tracking/** | Session progress and checkpoints | [→ Tracking](../tracking/) |

---

### ✅ DO Include

- **Setup Guides** (`INSTALLATION.md`, `SETUP.md`)
  - How to install/initialize the project
  - Prerequisites and dependencies
  - Step-by-step setup instructions

- **Configuration Guides** (`CONFIGURATION.md`, `CONFIG_*.md`)
  - Configuration options
  - Environment variables
  - Settings and parameters

- **How-To Tutorials** (`HOWTO_*.md`)
  - How to use specific features
  - Common workflows
  - Step-by-step procedures

- **Troubleshooting Guides** (`TROUBLESHOOTING.md`, `TROUBLESHOOT_*.md`)
  - Common issues and solutions
  - Debugging tips
  - Error messages and fixes

- **Admin Guides** (`ADMIN_*.md`)
  - Operational procedures for non-experts
  - Maintenance tasks
  - Deployment procedures

- **Quick Start** (`QUICKSTART.md`)
  - Get up and running in 5-10 minutes
  - Minimal setup
  - Basic usage examples

- **CLI Reference** (`CLI_REFERENCE.md`)
  - Available commands
  - Command syntax and options
  - Examples

### ❌ DO NOT Include

- Architecture details → `/architecture/`
- Test code or test results → `/testing/`
- Phase summaries → `/phases/`
- Feature-specific docs → `/features/`
- Session progress → `/tracking/`

---

## File Naming Convention

```
QUICKSTART.md                    # 5-10 minute getting started
INSTALLATION.md                  # Detailed setup instructions
CONFIGURATION.md                 # Configuration reference
CLI_REFERENCE.md                 # Command-line interface reference
HOWTO_*.md                       # How-to tutorials
TROUBLESHOOTING.md               # Common issues & solutions
ADMIN_*.md                       # Admin/operational procedures
DEPLOYMENT_*.md                  # Deployment procedures
```

---

## YAML Header Template

```yaml
---
project: kicli-code-assist
scope: guides
created: 2026-MM-DD HH
updated: 2026-MM-DD HH
update_reason: "Created guide, updated instructions, etc"
status: current
agent_project: kicli-code-assist
cross_references:
  - /home/flow/dev_flow/kicli-code-assist/doc/features/FEATURE_X.md
---
```

---

## Example: QUICKSTART.md

**What it includes:**
1. Install dependencies
2. Run initial setup
3. Start the server
4. Open browser to http://localhost:3000
5. Try basic operations

**Target audience:** New developers, just want to get it running  
**Length:** ~1-2 pages max

---

## Example: CONFIGURATION.md

**What it includes:**
- Configuration files overview
- Environment variables (with descriptions)
- Config file format
- Common configuration scenarios
- Where to set each option

---

## Audience

- **Developers** → QUICKSTART, INSTALLATION, CLI_REFERENCE, HOWTO_*
- **Operators/DevOps** → DEPLOYMENT, CONFIGURATION, TROUBLESHOOTING
- **Admins** → ADMIN_*, MAINTENANCE
- **New Users** → QUICKSTART, HOWTO_*

---

## Related Documentation

- **Features**: `/features/` (what can you do)
- **Architecture**: `/architecture/` (how it works internally)
- **Troubleshooting**: Cross-reference `/architecture/` for root cause analysis
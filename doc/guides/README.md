---
project: kicli-code-assist
scope: guides
created: 2026-11-02 13
updated: 2026-11-02 13
update_reason: Created folder README with guidelines
status: current
agent_project: kicli-code-assist
cross_references:
  - /home/flow/dev_doc/DOCUMENTATION_ORGANIZATION_GUIDE.md
---

# Guides & How-To Documentation

**Purpose:** Operational guides, tutorials, and setup instructions for kicli-code-assist.

---

## What Goes Here

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
---
title: Specifications Directory Guide
scope: reference
project: kicli-code-assist
status: active
created: 2026-11-05T19:55+01:00
updated: 2026-11-05T19:55+01:00
update_reason: Updated to reflect current agent-backend TUI architecture
agent_project: kicli-code-assist
cross_references:
  - /home/flow/dev_doc/TUI_STRATEGY_CLARIFICATION.md
  - doc/guides/TUI_CLIENT_IMPLEMENTATION_PLAN.md
  - doc/architecture/TUI_TEXTUAL_ARCHITECTURE.md
---

# Specifications Directory Guide

This directory contains **complete specifications** for kicli-code-assist components. Specifications define *what* to build and success criteria, not *how* to implement (see guides/ and architecture/ for implementation details).

## Current Specifications

### 02_TUI_SPECIFICATION.md
**Status:** `archived` — Legacy design, superseded

**Describes:** Earlier chat-based terminal interface design (October 2026)
- File browser + Chat + Input layout
- Interactive file selection model
- Session persistence

**Why Archived:** 
- Project shifted to agent-backend interface approach (Nov 2026)
- New approach leverages Phase 5.5.2 features (transparency, reasoning traces)
- Better for operational use case (K8s jump hosts)

**See Also:**
- `/home/flow/dev_doc/TUI_STRATEGY_CLARIFICATION.md` — Decision context
- `doc/guides/TUI_CLIENT_IMPLEMENTATION_PLAN.md` — Current active specification
- `doc/architecture/TUI_TEXTUAL_ARCHITECTURE.md` — Implementation deep dive

## Implementation References

### For TUI Developers

**Start here:**
1. Read `doc/guides/TUI_CLIENT_IMPLEMENTATION_PLAN.md` (what we're building)
2. Read `doc/architecture/TUI_TEXTUAL_ARCHITECTURE.md` (how it's designed)
3. Read `doc/guides/TEXTUAL_BEST_PRACTICES_REVIEW.md` (patterns & anti-patterns)

**Key Code Files:**
- `kicli_code_assist/ui/tui_client.py` (main app, 285 LOC)
- `kicli_code_assist/ui/widgets/project_explorer.py` (file tree)
- `kicli_code_assist/ui/widgets/agent_output_panel.py` (unified output display)
- `kicli_code_assist/ui/widgets/input_panel.py` (request input)

**Backend API (same as WebUI):**
- `POST /api/agent/route` — Main orchestration endpoint
- `GET /api/agent/explain`, `/suggest`, `/reason`, etc. — Individual modes
- `WebSocket /socket.io` — Real-time streaming events

### For Backend Developers

- `kicli_code_assist/web/server.py` — Flask app, all agent routes
- `kicli_code_assist/agent/` — Agent logic (meta_coordinator, code_implementation, etc.)
- Specs documented in server.py docstrings and route comments

### For Configuration/Operations

- `doc/deployment/CONSOLIDATION_STRATEGY.md` — Deployment configuration
- `doc/deployment/PHASE_1_REPORT.md` — Current deployment docs status
- `ki.yaml` — Project configuration file

## Directory Organization

```
doc/specifications/
├── README.md (this file)
├── 02_TUI_SPECIFICATION.md (archived - legacy chat design)
└── [Future specs for CLI, Config, Plugins, etc.]

doc/guides/
├── TUI_CLIENT_IMPLEMENTATION_PLAN.md ← Active TUI spec
├── TUI_QUICK_START.md ← User guide for TUI
├── TEXTUAL_BEST_PRACTICES_REVIEW.md ← Best practices reference

doc/architecture/
├── TUI_TEXTUAL_ARCHITECTURE.md ← Deep dive into widget design
├── PROJECT_STRUCTURE.md ← File organization
└── [Other architecture docs]
```

## How to Use This Directory

### I'm implementing a feature
1. Find the spec in `guides/` that describes it
2. Check `architecture/` for implementation patterns
3. Verify against acceptance criteria in spec
4. Write tests matching spec examples

### I'm reviewing a PR
1. Read the relevant spec
2. Verify implementation matches spec requirements
3. Check architecture docs for pattern compliance
4. Use spec as acceptance criteria

### I'm debugging something
1. Check `architecture/` for component interaction diagrams
2. Search `doc/guides/` for similar issues
3. Review code walkthrough in architecture docs
4. Look at git history for related changes

### I'm writing documentation
1. Link to specs as source of truth (don't duplicate)
2. Implementation docs reference specs, not vice versa
3. Archive old docs when superseded
4. Use YAML headers for organization

## Adding New Specifications

**When to create a spec:**
- New major component or feature
- Significant architectural change
- API contract or public interface
- Non-obvious design decisions

**Template:**
```markdown
---
title: Feature Name Specification
scope: specification
project: kicli-code-assist
status: draft | active | archived
created: YYYY-MM-DDThh:mm+01:00
updated: YYYY-MM-DDThh:mm+01:00
update_reason: Initial draft | Bug fixes | Superseded by new approach
agent_project: kicli-code-assist
cross_references: [links to related docs]
---

# Feature Name Specification

## Overview
[What is this? Who uses it? Why does it exist?]

## Requirements
[Functional and non-functional requirements]

## API/Interface
[How to use it - with examples]

## Examples
[Real usage scenarios]

## Error Cases
[What can go wrong and how to handle it]

## Performance Requirements
[Speed, memory, scalability targets]

## Future Enhancements
[Out of scope but worth noting]
```

## Archival Policy

Old specs are **archived, never deleted**, so we can:
- Understand historical decisions
- See what approaches were considered
- Learn what didn't work
- Preserve institutional memory

**How to archive a spec:**
1. Add `status: archived` to YAML header
2. Add `superseded_by: [link to new spec]` if applicable
3. Add `update_reason: Archived because...`
4. Keep file in `doc/specifications/` (don't move)
5. Add note at top of document:
   ```markdown
   **STATUS: ARCHIVED** — See [TUI_STRATEGY_CLARIFICATION.md] for decision context.
   ```

---

**Last Updated:** 2026-11-05T19:55+01:00  
**Scope:** Project-level documentation  
**Related:** `/home/flow/dev_doc/DOCUMENTATION_ORGANIZATION_GUIDE.md` (cross-project standards)

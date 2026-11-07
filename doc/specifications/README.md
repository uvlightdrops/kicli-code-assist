---
title: Specifications Directory Guide
scope: reference
project: kicli-code-assist
status: active
created: 2026-11-05T19:55+01:00
updated: 2026-11-05T21:45+01:00
update_reason: Update for TUI 2.0 foundation (FRONTEND_SPECIFICATION + architecture links)
agent_project: kicli-code-assist
cross_references:
  - doc/architecture/01_ARCHITECTURE.md (system overview & phase roadmap)
  - doc/architecture/FRONTEND_SPECIFICATION.md (abstract multi-frontend contract)
  - doc/architecture/TUI_INTELLIGENT_TERMINAL_IDE.md (TUI vision & 5-phase roadmap)
  - doc/architecture/TUI_TEXTUAL_ARCHITECTURE.md (Textual implementation details)
---

# Specifications Directory Guide

This directory contains **foundational specifications** for kicli-code-assist. Specifications define *what* to build and success criteria.

**For implementation details and patterns:** See `doc/architecture/` and `doc/guides/`

## Current Specifications

### 01_ARCHITECTURE.md ✅ ACTIVE
**Status:** `active` — System overview for Phase 1+ TUI development

**Describes:**
- 3-layer architecture (Backend + Frontend Spec + Frontend Implementations)
- Data flow (Request → Response → Display)
- Phase roadmap (1: Foundation, 2: Integration, 3-5: Advanced)
- Backend routes summary
- Configuration & deployment

**When to read:**
- Before starting implementation (understand the big picture)
- When making architectural decisions
- To understand phase boundaries and success criteria

**Related:**
- `doc/architecture/FRONTEND_SPECIFICATION.md` — Interface contract
- `doc/architecture/TUI_INTELLIGENT_TERMINAL_IDE.md` — TUI vision
- `doc/architecture/AGENT_ORCHESTRATION_ARCHITECTURE.md` — Backend details

---

### 02_PHASE_1_CHECKLIST.md ✅ NEW
**Status:** `active` — Phase 1 implementation checklist

**Describes:**
- Component implementation tasks (Project Tree, Tabs, Input, Status Bar)
- Backend connectivity requirements
- User interaction workflow
- Keyboard shortcuts
- Error handling strategies
- Testing checklist
- Success criteria
- Learnings from Oct 2026 attempt

**When to use:**
- Developer: Track implementation progress
- QA: Validate against checklist
- Reviewer: Acceptance criteria

**Read together with:**
- `doc/architecture/FRONTEND_SPECIFICATION.md` (what each component does)
- `doc/architecture/TUI_TEXTUAL_ARCHITECTURE.md` (how to implement)

---

### Archived Specifications

**See:** `doc/archive/tui_attempt_oct2026/` for:
- `02_TUI_SPECIFICATION.md` — Legacy chat-based design (Oct 2026)
- `03_BACKEND_SPECIFICATION.md` — Old chat backend routes
- `04_FEATURE_CHECKLIST.md` — Old feature checklist (chat phase)
- `05_IMPLEMENTATION_DETAILS.md` — Old code walkthrough

**Why archived:** 
- Oct 2026 chat-based approach superseded by agent-backend design
- Preserved for historical reference and lessons learned
- See archive README for insights extracted

---

## Quick Navigation

### "I want to understand the system"
1. Start: `01_ARCHITECTURE.md` (5 min overview)
2. Deep dive: `doc/architecture/FRONTEND_SPECIFICATION.md` (component details)
3. Backend: `doc/architecture/AGENT_ORCHESTRATION_ARCHITECTURE.md`

### "I want to implement Phase 1 TUI"
1. Read: `01_ARCHITECTURE.md` (Phases 1-3)
2. Read: `doc/architecture/TUI_INTELLIGENT_TERMINAL_IDE.md` (Phase 1 breakdown)
3. Read: `doc/architecture/FRONTEND_SPECIFICATION.md` (what to implement)
4. Start coding: `kicli_code_assist/ui/tui_client.py`

### "I want to understand the frontend spec"
1. `doc/architecture/FRONTEND_SPECIFICATION.md` — Abstract interface
2. `doc/architecture/TUI_TEXTUAL_ARCHITECTURE.md` — Textual specifics
3. Code: `kicli_code_assist/ui/` (widgets, client)

### "I want to understand the backend"
1. `01_ARCHITECTURE.md` (Backend section)
2. `doc/architecture/AGENT_ORCHESTRATION_ARCHITECTURE.md` (agent routing)
3. `doc/architecture/TRANSPARENCY_MODULES_ARCHITECTURE.md` (reasoning traces)
4. Code: `kicli_code_assist/agent/`, `kicli_code_assist/web/server.py`

### "I want to understand WebUI (host-1)"
1. Skip TUI docs
2. Read: `doc/architecture/WEB_FRONTEND_DESIGN.md`
3. Code: `web/frontend/src/components/`

---

## Document Organization Philosophy

**This directory (`doc/specifications/`):**
- High-level "what to build"
- Interface contracts
- Success criteria
- Stable reference documents

**Related directory (`doc/architecture/`):**
- HOW to build it
- Design decisions & rationale
- Component interaction
- Phase-specific architecture

**Related directory (`doc/guides/`):**
- Step-by-step implementation walkthroughs
- Best practices & patterns
- Troubleshooting guides
- Quick references

**Related directory (`doc/archive/`):**
- Old attempts & learnings
- Historical context
- What didn't work & why

---

## Archival Policy

Old specs are **archived, never deleted**:
- Understand historical decisions
- See what approaches were considered
- Learn from past attempts
- Preserve institutional memory

**How to archive:**
1. Add `status: archived` to YAML header
2. Add note: `**STATUS: ARCHIVED** — See [reason doc] for context`
3. Keep in `doc/specifications/` (don't move)

---

## Cross-Project Standards

This project follows cross-project standards documented in:
- `/home/flow/dev_doc/DOCUMENTATION_ORGANIZATION_GUIDE.md` (folder structure)
- `/home/flow/dev_doc/DEPLOYMENT_STANDARDS.md` (YAML headers, formatting)

**For new docs:** Use template from `DEPLOYMENT_STANDARDS.md`

---

**Last Updated:** 2026-11-05T21:45+01:00  
**Next Review:** After Phase 1 completion (Nov 8)
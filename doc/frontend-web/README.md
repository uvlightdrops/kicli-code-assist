---
title: WebUI Frontend Documentation
project: kicli-code-assist
scope: frontend-web
status: active
created: 2026-11-05T22:14:00+01:00
updated: 2026-11-03T15:00:00+01:00
update_reason: Reorganized after archiving outdated Oct 2026 docs; updated cross-references
agent_project: CodeImplementationAgent
cross_references:
  - "doc/specifications/01_ARCHITECTURE.md"
  - "doc/architecture/FRONTEND_SPECIFICATION.md"
  - "doc/PHASE_5_5_2_SUMMARY.md"
  - "doc/archive/webui_phase1_v1/README.md"
---

# WebUI Frontend Documentation

**Current Phase:** Phase 5.5.2 (Transparency & Observability) | Phase 5.5.3+ (Performance & Extensions)  
**Framework:** React + TypeScript  
**Key Features:** Agent-driven dashboard, real-time reasoning visualization, diff viewer, streaming events

---

## Quick Navigation

### 📋 For New Developers
1. Start: `doc/specifications/01_ARCHITECTURE.md` — TUI 2.0 system overview
2. WebUI specific: This README → architecture docs below
3. Implement: `doc/architecture/FRONTEND_SPECIFICATION.md` — Interface contract
4. Real-time: `doc/architecture/PHASE_5_5_2_I2_WEBSOCKET_ARCHITECTURE.md` — Event streaming

### 🎯 For Phase 5.5.2+ Implementation
- `REASONING_PANEL_FRONTEND_DESIGN.md` — Transparency visualization (active)
- `DIFF_USER_GUIDE.md` — Diff viewer usage (active)
- `WEB_EDITOR_FRAMEWORKS_COMPARISON.md` — Framework reference (active)
- `WEB_EDITOR_EDIT_CAPABILITIES.md` — Current editor status (reference)

### 📚 For Historical Context
- `PHASE_1_SUMMARY.md` — Phase 1 snapshot (archived status)
- `UI_TABS.md` — Tab system (temporary location; will move to frontend-tui/)
- Older docs: See `doc/archive/webui_phase1_v1/README.md`

---

## Current Documentation (6 Active Docs)

### Architecture & Design

| Doc | Purpose | Status |
|-----|---------|--------|
| **REASONING_PANEL_FRONTEND_DESIGN.md** | Real-time agent transparency visualization for Phase 5.5.2 | ✅ Active (Nov 2) |
| **WEB_EDITOR_FRAMEWORKS_COMPARISON.md** | Detailed analysis of Monaco, CodeMirror, Ace, Vim-mode options | ✅ Reference (Oct 28) |
| **WEB_EDITOR_EDIT_CAPABILITIES.md** | Current editor status & roadmap for edit mode implementation | ✅ Reference (Oct 28) |

### Features & Usage Guides

| Doc | Purpose | Status |
|-----|---------|--------|
| **DIFF_USER_GUIDE.md** | How to use the diff engine and code editing features | ✅ Active (Sept 2026) |
| **UI_TABS.md** | Tab system guide (⚠️ Note: describes TUI; temporary location) | ⏳ TUI Feature (will move) |

### Implementation History (Archived Status)

| Doc | Purpose | Status |
|-----|---------|--------|
| **PHASE_1_SUMMARY.md** | Phase 1 completion snapshot (Sept 2026) | 📦 Archived (historical) |

---

## Related Documentation

**System-wide:**
- `doc/specifications/01_ARCHITECTURE.md` — TUI 2.0 system overview (3-layer, phase roadmap)
- `doc/architecture/FRONTEND_SPECIFICATION.md` — Abstract interface (shared by TUI + WebUI)

**Phase 5.5.2 Implementation:**
- `doc/PHASE_5_5_2_SUMMARY.md` — Complete Phase 5.5.2 overview
- `doc/architecture/PHASE_5_5_2_I2_WEBSOCKET_ARCHITECTURE.md` — WebSocket event design
- `doc/architecture/PHASE_5_5_2_I4_FRONTEND_CONCEPT.md` — ReasoningPanel concept

**Backend APIs:**
- `doc/architecture/AGENT_ORCHESTRATION_ARCHITECTURE.md` — Agent routing
- `doc/architecture/TRANSPARENCY_MODULES_ARCHITECTURE.md` — Reasoning traces
- `doc/backend/` (when created) — Backend implementation guides

**Alternative Frontend:**
- `doc/frontend-tui/` — TUI documentation (Phase 2+)

**Archive:**
- `doc/archive/webui_phase1_v1/README.md` — Old Oct 2026 approach (chat-based)

---

## Development Workflow

### Local Development (Phase 5.5.2+)
```bash
# Start backend (includes transparency modules)
python -m stackctl start
# Runs: agent services, WebSocket streaming, transparency traces

# Start WebUI (from web/frontend/)
npm run dev
# Opens http://localhost:3000
# Connects to backend via /api/* and /agent/* routes
```

### Implementation Checklist
- [ ] Understanding Phase 5.5.2 architecture (read PHASE_5_5_2_SUMMARY.md)
- [ ] WebSocket event format (read WEBSOCKET_ARCHITECTURE.md)
- [ ] ReasoningPanel component design (read this doc's REASONING_PANEL_FRONTEND_DESIGN.md)
- [ ] Backend REST/WS routes (read /api/agent/*, /agent/execution namespace)
- [ ] Test with dummy data before connecting to real agents

---

## Current State

| Phase | Status | Components |
|-------|--------|------------|
| Phase 1 (Sept 2026) | ✅ Complete | UnifiedAgentChat, DiffViewer, SettingsPanel |
| Phase 2-3 (Oct-Nov 2026) | ✅ Complete | WebSocket streaming, transparency modules, ReasoningPanel concept |
| Phase 4+ | 🔮 Future | Performance optimization, extended features |

---

## Notes

- **UI_TABS.md:** Describes Terminal UI, stored here temporarily; will move to `doc/frontend-tui/` in Phase 2
- **Old WebUI docs:** See `doc/archive/webui_phase1_v1/` for Oct 2026 approach (chat-based, superseded)
- **Coordination:** TUI and WebUI share the same backend (agents, config, API) but have different frontend implementations

---

**Last Updated:** 2026-11-03  
**Scope:** WebUI-specific architecture, design, and implementation  
**Related:** `doc/specifications/` (common specs), `doc/backend/` (backend APIs when created)

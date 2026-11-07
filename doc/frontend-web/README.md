---
title: WebUI Frontend Documentation
project: kicli-code-assist
agent_project: kicli-code-assist
scope: User Interface / Web Frontend Implementation
purpose: Documentation hub for React/TypeScript WebUI architecture, design, and implementation
created: 2026-11-05T22:14:29+01:00
updated: 2026-11-07T14:00:00+01:00
update_reason: Upgraded to semantic schema with semantic blocks and relations
status: stable

semantic_blocks:
  - id: webui-documentation-hub
    type: reference
    status: stable
    version: 1.0
  - id: phase-5-5-2-transparency
    type: implementation
    status: stable
    version: 1.0
  - id: editor-framework-comparison
    type: architecture
    status: stable
    version: 1.0
  - id: diff-viewer-system
    type: implementation
    status: stable
    version: 1.0

relations:
  - target: REASONING_PANEL_FRONTEND_DESIGN.md
    type: composed-of
    reason: "Phase 5.5.2 transparency visualization component"
  - target: DIFF_USER_GUIDE.md
    type: composed-of
    reason: "Diff viewer and code editing features"
  - target: WEB_EDITOR_FRAMEWORKS_COMPARISON.md
    type: composed-of
    reason: "Editor framework analysis and selection"
  - target: FRONTEND_SPECIFICATION.md
    type: references
    reason: "Abstract interface shared with TUI"
  - target: PHASE_1_SUMMARY.md
    type: references
    reason: "Historical Phase 1 completion data"
  - target: ../backend/layer-2-workflow-orchestration/AGENT_ROUTE_SPEC.md
    type: depends-on
    reason: "Calls backend agent routing and streaming APIs"
  - target: ../specifications/01_ARCHITECTURE.md
    type: references
    reason: "Follows TUI 2.0 system architecture"
  - target: ../backend/layer-3-autonomous-agent/AGENT_COORDINATION.md
    type: depends-on
    reason: "Displays agent coordination visualization"
---

# WebUI Frontend Documentation [webui-documentation-hub]

**Current Phase:** Phase 5.5.2 (Transparency & Observability)  
**Framework:** React + TypeScript  
**Key Features:** Agent-driven dashboard, real-time reasoning visualization, diff viewer, streaming events

## Purpose

**WebUI frontend for kicli-code-assist:** Browser-based user interface providing code analysis, visualization of agent reasoning, and real-time collaboration with AI agents.

## Documentation Index

| Document | Blocks | Purpose | S |
|----------|--------|---------|---|
| **REASONING_PANEL_FRONTEND_DESIGN.md** | – | Real-time agent transparency visualization | ✅ |
| **DIFF_USER_GUIDE.md** | – | Diff viewer and code editing workflows | ✅ |
| **WEB_EDITOR_FRAMEWORKS_COMPARISON.md** | – | Editor framework analysis (Monaco, CodeMirror, Ace) | ✅ |
| **WEB_EDITOR_EDIT_CAPABILITIES.md** | – | Current editor status and roadmap | ✅ |
| **FRONTEND_SPECIFICATION.md** | – | Abstract interface contract (shared TUI/WebUI) | ✅ |
| **UI_TABS.md** | – | Tab system design and usage | ✅ |
| **PHASE_1_SUMMARY.md** | – | Phase 1 completion snapshot (historical) | 📦 |

## Quick Navigation

### 📋 For New Developers
1. Start: `../specifications/01_ARCHITECTURE.md` — TUI 2.0 system overview
2. WebUI: This README → documentation index below
3. Implementation: `FRONTEND_SPECIFICATION.md` — interface contract
4. Real-time: `REASONING_PANEL_FRONTEND_DESIGN.md` — Phase 5.5.2 visualization

### 🎯 For Active Development (Phase 5.5.2+)
- `REASONING_PANEL_FRONTEND_DESIGN.md` — Transparency visualization (active)
- `DIFF_USER_GUIDE.md` — Diff viewer features (active)
- `WEB_EDITOR_FRAMEWORKS_COMPARISON.md` — Framework reference (active)
- Backend coordination: `../backend/layer-3-autonomous-agent/AGENT_COORDINATION.md`

### 📚 For Historical Context
- `PHASE_1_SUMMARY.md` — Phase 1 snapshot (archived)
- Archive: `../archive/webui_phase1_v1/` — Oct 2026 approach (superseded)

## Related Documentation

**System Architecture:**
- `../specifications/01_ARCHITECTURE.md` — TUI 2.0 system overview
- `FRONTEND_SPECIFICATION.md` — Abstract interface (shared by TUI + WebUI)

**Phase 5.5.2 Implementation:**
- `../PHASE_5_5_2_SUMMARY.md` — Complete Phase 5.5.2 overview
- `../architecture/PHASE_5_5_2_I2_WEBSOCKET_ARCHITECTURE.md` — WebSocket design
- `../architecture/PHASE_5_5_2_I4_FRONTEND_CONCEPT.md` — ReasoningPanel concept

**Backend APIs:**
- `../backend/layer-2-workflow-orchestration/AGENT_ROUTE_SPEC.md` — Agent routing
- `../backend/layer-3-autonomous-agent/AGENT_COORDINATION.md` — Coordination logic
- `../architecture/TRANSPARENCY_MODULES_ARCHITECTURE.md` — Reasoning traces

**Alternative Frontend:**
- `../frontend-tui/` — Terminal UI documentation

---

## Development Workflow

### Local Development
```bash
# Start backend (includes transparency modules + WebSocket streaming)
python -m stackctl start

# Start WebUI (from web/frontend/)
npm run dev
# Opens http://localhost:3000
# Connects to backend via /api/* and /agent/* routes
```

### Implementation Path
1. Read `PHASE_5_5_2_SUMMARY.md` (Phase 5.5.2 overview)
2. Study `REASONING_PANEL_FRONTEND_DESIGN.md` (transparency visualization)
3. Review `FRONTEND_SPECIFICATION.md` (component interface)
4. Check `../backend/` docs (API contracts)
5. Implement components (in `kicli_code_assist/web/frontend/src/`)

---

## Current State

| Phase | Status | Components |
|-------|--------|------------|
| Phase 1 | ✅ Complete | UnifiedAgentChat, DiffViewer, SettingsPanel |
| Phase 5.5.2 | ✅ Complete | ReasoningPanel (concept ready for Phase I4) |
| Phase I4+ | 🔮 Future | Performance, extended features |

---

**Scope:** WebUI-specific architecture, design, and implementation  
**Related:** `../specifications/` (system-wide), `../backend/` (backend APIs), `../frontend-tui/` (TUI implementation)
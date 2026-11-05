---
title: WebUI Frontend Documentation
project: kicli-code-assist
scope: frontend
status: active
created: 2026-11-05T22:14+01:00
updated: 2026-11-05T22:14+01:00
update_reason: Organize WebUI-specific docs in dedicated folder
agent_project: kicli-code-assist
cross_references:
  - doc/specifications/01_ARCHITECTURE.md (system overview)
  - doc/architecture/FRONTEND_SPECIFICATION.md (shared interface)
  - doc/frontend-tui/README.md (TUI alternative)
---

# WebUI Frontend Documentation

**Status:** Phase 1-3 Complete | Deployed on host-1  
**Framework:** React + TypeScript  
**Key Features:** Split-pane editor, agent chat, reasoning panel, diff viewer

---

## Quick Start

1. **Read First:** `WEB_FRONTEND_DESIGN.md` — Architecture overview
2. **Understand:** `WEB_IMPLEMENTATION_PLAYBOOK.md` — Implementation guide
3. **Reference:** `REASONING_PANEL_FRONTEND_DESIGN.md` — Reasoning visualization

---

## Documentation Structure

### Architecture & Design

- **WEB_FRONTEND_DESIGN.md** — Overall architecture and design principles
- **WEB_EDITOR_EDIT_CAPABILITIES.md** — Code editing features
- **WEB_EDITOR_FRAMEWORKS_COMPARISON.md** — Framework analysis (Monaco vs alternatives)
- **WEB_IMPLEMENTATION_PLAYBOOK.md** — Step-by-step implementation guide
- **REASONING_PANEL_FRONTEND_DESIGN.md** — Real-time reasoning visualization

### Features & UX

- **UI_TABS.md** — Tab system (Logging, Chat, Terminal, Shell)
- **DIFF_USER_GUIDE.md** — How to use diff viewer

### Implementation Status

- **PHASE_1_HYBRID_IMPLEMENTATION.md** — Phase 1 implementation details
- **PHASE_1_SUMMARY.md** — Phase 1 completion summary

---

## Key Files in Codebase

```
web/frontend/
├── src/
│   ├── components/           # React components
│   │   ├── UnifiedAgentChat.tsx
│   │   ├── DiffViewer.tsx
│   │   ├── ReasoningPanel.tsx
│   │   └── [others]
│   ├── hooks/               # Custom React hooks
│   │   ├── useAnalysisSettings.ts
│   │   └── [others]
│   └── App.tsx
├── Dockerfile
└── package.json
```

---

## Related Documentation

**Shared (TUI + WebUI):**
- `doc/architecture/FRONTEND_SPECIFICATION.md` — Abstract interface
- `doc/architecture/WEBSOCKET_STREAMING_ARCHITECTURE.md` — Real-time events

**Backend (supports both frontends):**
- `doc/architecture/AGENT_ORCHESTRATION_ARCHITECTURE.md` — Agent routing
- `doc/architecture/TRANSPARENCY_MODULES_ARCHITECTURE.md` — Reasoning traces

**Alternative Frontend:**
- `doc/frontend-tui/README.md` — TUI documentation

---

## Development Workflow

### Local Development
```bash
# Start backend
python -m stackctl start

# Start WebUI (from web/frontend/)
npm run dev
# Opens http://localhost:3000
```

### Build for Production
```bash
npm run build
# Creates optimized build in dist/
```

---

## Current State

✅ **Phase 1:** Foundation (Split-pane, Chat, Agent routing)  
✅ **Phase 2:** WebSocket streaming (Real-time events, reasoning)  
✅ **Phase 3:** Transparency (Reasoning panel, call traces)  
⏳ **Phase 4:** Performance optimization (Caching, session persistence)  
🔮 **Phase 5+:** Extended features (Themes, split modes, offline)

---

## Deployment

- **Host-1:** WebUI accessible via browser
- **Kubernetes:** Deployed via Helm + Docker
- **Environment:** Uses ki.yaml config + environment variables

See `doc/deployment/` for detailed deployment guides.

---

**Last Updated:** 2026-11-05  
**Scope:** WebUI-specific architecture and implementation  
**Related:** `doc/frontend-tui/` (TUI alternative), `doc/backend/` (backend APIs)

---
title: "Backend Documentation Hub"
project: "kicli-code-assist"
scope: "backend"
created: 2026-11-06T09:20:00+01:00
updated: 2026-11-06T09:20:00+01:00
update_reason: "Created backend doc hub for API + orchestration clarity"
status: "active"
cross_references:
  - doc/CODE_ANALYSIS_STRUCTURE.md (5-layer overview)
  - doc/architecture/AGENT_ORCHESTRATION_ARCHITECTURE.md (deep dive)
  - doc/architecture/AGENT_COORDINATION_ARCHITECTURE.md (agent pipeline)
---

# Backend Documentation Hub

Quick navigation for clients (TUI, WebUI, ki-knowledge, etc) integrating with kicli backend.

## 🎯 Start Here

**First time?** → Read `AGENT_ROUTE_SPEC.md` (5-min overview)
**Implementing?** → Follow `INTEGRATION_GUIDE.md` (step-by-step)
**Debugging?** → Check `doc/CODE_ANALYSIS_STRUCTURE.md` (5-layer flow)

## 📚 Organization

### API Level (What you call)
- **`AGENT_ROUTE_SPEC.md`** — `/api/agent/route` endpoint
  - Request/Response schema
  - Query patterns (Explain, Metrics, Refactor, etc)
  - Error responses
  - Real examples from TUI

### Architecture Level (How it works)
- **`doc/architecture/AGENT_ORCHESTRATION_ARCHITECTURE.md`**
  - 6-stage pipeline (intent → routing → agent selection → execution → aggregation → generation)
  - MetaCoordinationAgent + specialized agents
  
- **`doc/architecture/AGENT_COORDINATION_ARCHITECTURE.md`**
  - Internal agent communication
  - Data flow between Explain/Metrics/Dependencies/Refactor agents
  
- **`doc/architecture/WEBSOCKET_STREAMING_ARCHITECTURE.md`**
  - Real-time chunk streaming (Phase 1.2)
  - Event structure for TUI/WebUI

- **`doc/architecture/ASYNC_LLM_SECURITY_ARCHITECTURE.md`**
  - Async LLM processing (ki-core)
  - Secret filtering + error handling

### Implementation Guides
- **`INTEGRATION_GUIDE.md`** — Step-by-step for new clients
- **`CHUNK_FORMAT_SPEC.md`** — Standard chunk structure (observation/issue/solution)
- **`ERROR_HANDLING.md`** — What to do when backend fails

### Deployment (handled by stackctl)
- See `doc/deployment/` (not here)

## 🔄 Cross-Project Usage

This backend is shared by:
- **kicli-code-assist** — TUI + WebUI
- **ki-knowledge** — Coding Agent
- Future projects (new clients welcome)

Standard pattern for new clients:
```
1. Read AGENT_ROUTE_SPEC.md
2. Follow INTEGRATION_GUIDE.md
3. Use same chunk format (CHUNK_FORMAT_SPEC.md)
4. Report issues/extensions to this hub
```

## 📊 Status

- ✅ API endpoint: `/api/agent/route` (Phase 5.1 complete)
- ✅ Agent orchestration: 6-stage pipeline (Phase 5.1)
- ✅ Transparency: Reasoning traces + WebSocket streaming (Phase 5.5.2)
- 🟡 TUI integration: Starting Phase I1
- 🟡 WebUI integration: Full (Phase 1 complete, Phase 5.5.2 integrated)
- 🟡 ki-knowledge integration: Ready to consume

## 📝 Contributing to Backend Docs

When updating backend code:
1. Update YAML headers in modified docs (status, updated, update_reason)
2. If breaking API changes → update AGENT_ROUTE_SPEC.md + INTEGRATION_GUIDE.md
3. Keep Architecture docs in sync (link in cross_references)
4. Archive old docs in doc/architecture/archive/ (don't delete)

---

**Last updated:** 2026-11-06 | **By:** Copilot | **Phase:** I1-TUI-Integration

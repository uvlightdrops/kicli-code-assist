# Unified Server Management System - Executive Summary

## Overview

This is a comprehensive design for a **Unified Server Management System** for kicli-code-assist and the broader KI ecosystem (ki-knowledge, ki-core, stackctl).

**Problem Solved:** Ghost processes, no central visibility, manual PID killing, scattered logs, no dependency tracking.

**Solution:** Hybrid architecture with:
- ✅ Persistent JSON registry of all services
- ✅ CLI commands: `kicli-assist server:status`, `server:start`, `server:stop`, `server:logs`
- ✅ WebUI dashboard for real-time monitoring
- ✅ Optional background supervisor for health checks
- ✅ Audit trail for accountability
- ✅ Automatic orphan detection & cleanup

---

## Key Documents

### 1. **SERVER_MANAGEMENT_DESIGN.md** (Architecture Overview)
   - **What:** Executive summary, problem analysis, three architectural options
   - **Key Content:**
     - Option A (Daemon-only), Option B (Stateless), Option C (Hybrid - RECOMMENDED)
     - Data model (service registry schema)
     - CLI interface examples
     - WebUI components
     - Implementation roadmap (6 phases, 4 weeks)
   - **Audience:** Architects, team leads, stakeholders
   - **Length:** 3 pages

### 2. **SERVER_MANAGEMENT_DECISIONS.md** (Architectural Decisions)
   - **What:** Answers to the 5 key architectural questions
   - **Key Content:**
     - Why Option C (Hybrid) is best
     - Why JSON file + OS queries (not pure daemon or stateless)
     - Multi-project scope from day 1
     - Integration with ki_core.ConfigManager
     - Safety mechanisms (confirmations, audit trail)
   - **Audience:** Architects, engineers implementing Phase 1-2
   - **Length:** 4 pages

### 3. **SERVER_MANAGEMENT_FLOWS.md** (Data & Control Flows)
   - **What:** Visual ASCII diagrams showing how data flows through the system
   - **Key Content:**
     - System architecture diagram (complete overview)
     - State flow: Starting a service with dependencies
     - Orphan detection & recovery flow
     - Directory structure & file schemas
     - Concurrency & locking patterns
     - WebUI component layout
     - Dependency resolution graphs
     - Error scenarios & error handling
   - **Audience:** Engineers implementing backend, frontend, CLI
   - **Length:** 5 pages (heavy on diagrams)

### 4. **SERVER_MANAGEMENT_IMPLEMENTATION.md** (Implementation Guide)
   - **What:** Step-by-step implementation plan with code sketches
   - **Key Content:**
     - Project structure (where to add files)
     - Phase 1: Core registry (code skeleton, unit tests)
     - Phase 2: CLI commands
     - Phase 3: Optional supervisor
     - Phase 4: WebUI
     - Phase 5: Multi-project support
     - Phase 6: Testing & documentation
     - Success checklist
     - Deployment checklist
   - **Audience:** Engineers implementing the system, QA/testing teams
   - **Length:** 6 pages (heavy on code)

---

## Architecture at a Glance

```
User Interfaces:
  ├─ CLI: kicli-assist server:status/start/stop/logs/cleanup
  └─ WebUI: /dashboard/servers (React components, real-time WebSocket)
       ↓
Core Registry API (ServerRegistry class)
  ├─ Persistent: ~/.kicli/services.json + audit.jsonl
  ├─ Ephemeral: /proc queries, netstat, health checks
  └─ Thread-safe: File-based locking (.lock file)
       ↓
Optional Background Supervisor
  ├─ Health check loop (every 30s)
  ├─ Auto-restart on failure
  └─ WebSocket event broadcasting
       ↓
Managed Services
  ├─ kicli-backend (port 8000)
  ├─ kicli-frontend (port 3000)
  ├─ ki-django (port 8002)
  ├─ stackctl-api (port 5000)
  └─ ... (multi-project support)
```

---

## Quick Start (For Implementation)

### Week 1: Core Registry + CLI (MVP)
```bash
# What gets built:
✓ ServerRegistry class (CRUD, locking, audit)
✓ CLI commands: list, status, start, stop, logs
✓ Process management: spawn, kill, health checks
✓ Dependency resolution
✓ Port conflict detection
✓ Unit tests (70% coverage)

# Pain point solved:
❌ Ghost processes
✅ No more ghost processes (registry tracks PID)
✅ Can see what's running (server:list)
✅ Can stop services cleanly (server:stop)
✅ Can see logs (server:logs)
```

### Week 2: Supervisor + Web API
```bash
# What gets built:
✓ Background health check loop
✓ REST API endpoints (/api/servers/*)
✓ WebSocket event streaming
✓ Test coverage 75%+

# Pain point solved:
✅ Automatic crash detection
✅ WebUI real-time status
✅ API for third-party integrations
```

### Week 3-4: WebUI + Multi-Project + Polish
```bash
# What gets built:
✓ React ServerDashboard component
✓ Service table, detail view, log viewer
✓ Multi-project support (ki-knowledge, ki-core, stackctl)
✓ Comprehensive testing & documentation
✓ Test coverage 85%+

# Production ready:
✅ Full real-time visibility
✅ Works across all KI projects
✅ Audit trail for accountability
✅ Recovery from crashes
```

---

## Design Decisions (Summary)

| Decision | Choice | Why |
|----------|--------|-----|
| **Architecture** | Hybrid (A+B) | State persistence + zero-overhead fallback |
| **State Storage** | JSON file + OS queries | Audit trail + real-time accuracy + cross-platform |
| **Concurrency** | File-based locking | Simple, no background threads, works everywhere |
| **Scope** | Multi-project from day 1 | Future-proof; minimal added complexity |
| **Supervisor** | Optional (CLI flag) | Dev flexibility + production reliability |
| **Config** | Separate projects.yaml | Clean separation; can reuse ki_core validators |
| **Safety** | Confirmations + audit trail | Protection + accountability |

---

## File Manifest

```
doc/
├── SERVER_MANAGEMENT_README.md          ← This file (overview)
├── SERVER_MANAGEMENT_DESIGN.md          ← Architecture & options
├── SERVER_MANAGEMENT_DECISIONS.md       ← Architectural decisions
├── SERVER_MANAGEMENT_FLOWS.md           ← Data flows & diagrams
└── SERVER_MANAGEMENT_IMPLEMENTATION.md  ← Implementation guide

kicli_code_assist/server_management/ (to be created)
├── __init__.py
├── registry.py                  (Core registry class)
├── process.py                   (Process management)
├── health.py                    (Health checking)
├── audit.py                     (Audit logging)
├── config.py                    (Load projects.yaml)
└── utils.py                     (Helpers: port scanner, lock manager)

kicli_code_assist/cli/
└── server_commands.py           (CLI: server:* commands)

kicli_code_assist/web/
├── server_api.py                (REST API for registry)
└── supervisor.py                (Background health checks)

web/frontend/src/
├── pages/ServerDashboard.tsx    (Main dashboard page)
├── components/ServiceTable.tsx  (Service list)
├── components/ServiceDetail.tsx (Detail view)
├── components/LogViewer.tsx     (Log display)
└── hooks/useServerRegistry.ts   (API hook)

tests/test_server_management/
├── test_registry.py             (Unit tests)
├── test_process.py
├── test_health.py
├── test_api.py
├── test_cli.py
└── test_integration.py

config/
└── projects.yaml                (Service definitions)
```

---

## Key Features

### ✅ What Gets Solved

1. **Visibility** - Central registry of all services (status, PID, port, health)
2. **Control** - CLI commands to start/stop/restart services
3. **Reliability** - Dependency ordering (backends start first)
4. **Debugging** - Aggregated logs, health checks, audit trail
5. **Safety** - Confirmations, audit logging, no accidental kills
6. **Automation** - Optional supervisor for crash recovery
7. **Scalability** - Multi-project support (one system manages everything)

### ⚙️ Configuration

**~/.kicli/projects.yaml** (service definitions)
```yaml
projects:
  kicli-code-assist:
    services:
      - id: kicli-backend
        command: python -m flask run
        port: 8000
        dependencies: []
      - id: kicli-frontend
        command: npm run dev
        port: 3000
        dependencies: [kicli-backend]
```

**~/.kicli/services.json** (runtime state, auto-generated)
```json
{
  "services": [
    {
      "id": "kicli-backend",
      "status": "running",
      "pid": 12345,
      "started_at": "2026-10-28T02:05:00Z"
    }
  ]
}
```

### 🔒 Safety

- **File-based locking** prevents concurrent writes
- **Confirmation dialogs** for destructive operations
- **Audit trail** logs every action (user, timestamp, status)
- **Dependency alerts** warn when stopping services others depend on
- **Stale lock recovery** handles crashed supervisor

### 📊 Metrics

- Memory usage per service
- CPU usage per service
- Health check success rate
- Uptime tracking
- Crash detection & recovery

---

## Next Steps

### For Review
1. Read **SERVER_MANAGEMENT_DESIGN.md** (high-level architecture)
2. Review **SERVER_MANAGEMENT_DECISIONS.md** (answer the 5 questions)
3. Approve Option C (Hybrid) architecture

### For Implementation
1. Use **SERVER_MANAGEMENT_IMPLEMENTATION.md** as step-by-step guide
2. Follow the 6-phase roadmap (4 weeks to production)
3. Refer to **SERVER_MANAGEMENT_FLOWS.md** for data/control flows
4. Use provided code sketches as starting point

### For Design Refinement
- Adjust phase 3 (supervisor) based on team capacity
- Adjust phase 5 (multi-project) if focusing on single project
- Adjust timelines based on team size

---

## FAQ

**Q: Why Hybrid (Option C) instead of just Daemon (Option A)?**
A: Hybrid provides flexibility (optional supervisor), performance (cached state), and cross-platform compatibility. Option A adds complexity and daemon management overhead for dev environments.

**Q: Why separate JSON file instead of reading from /proc directly?**
A: Registry persists state across reboots, enables audit trail, allows state recovery after crashes, and performs better than querying /proc each time.

**Q: Won't file-based locking be slow?**
A: No - lock acquisition is <10ms, held for <100ms. Much faster than OS-level synchronization primitives.

**Q: Do we need the optional supervisor?**
A: No for MVP - CLI queries OS directly. Supervisor adds value (real-time monitoring, crash recovery) but can wait until Week 2.

**Q: Can this handle 100+ services?**
A: Yes - registry is just JSON, scales to thousands. Health check loop might need batching at scale (not in MVP).

**Q: How does this integrate with Kubernetes?**
A: Out of scope for MVP (dev environment). Future extension: read pod status from K8s API instead of /proc.

---

## References

- **Problem Statement:** Multiple ghost processes, no central visibility
- **Current State:** Each project manages processes independently
- **Design Approach:** Persistent registry + optional supervisor + direct OS queries
- **Scope:** kicli-code-assist (MVP), then ki-knowledge/ki-core/stackctl (Phase 5)
- **Timeline:** 4 weeks to production
- **Team:** Backend (registry/CLI), Frontend (WebUI/React), DevOps (supervisor systemd)

---

## Document Navigation

```
                    ┌─────────────────────────┐
                    │ You Are Here            │
                    │ README (Overview)       │
                    └────────────┬────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
    DESIGN.md              DECISIONS.md            FLOWS.md
    (Architecture)         (Key Q&A)               (Diagrams)
    Read this first        Then read this         Then read this
    3 pages                4 pages                5 pages
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
                      IMPLEMENTATION.md
                      (Step-by-step guide)
                      Then implement from this
                      6 pages + code sketches
```

---

**Status:** Design Complete | **Approved By:** [pending] | **Implementation Start:** Week 1 Day 1

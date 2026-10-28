# Unified Server Management System - Design Document

**Version:** 1.0  
**Date:** 2026-10-28  
**Status:** Design Phase  
**Scope:** kicli-code-assist dev environment

---

## Executive Summary

Current pain point: Multiple backend/frontend processes run concurrently with no central visibility or control, leading to ghost processes, manual PID killing, and no unified logging.

**Design outcome:** A hybrid server management system supporting:
- **CLI interface** (`kicli-assist server:status`, `server:start`, `server:stop`)
- **WebUI dashboard** for real-time service monitoring and control
- **Automatic service discovery** with health checks
- **State persistence** for crash recovery and audit trails
- **Cross-project support** (kicli-code-assist, ki-knowledge, ki-core, stackctl)

This document presents three architectural options and recommends **Option C (Hybrid)** as the production-ready solution.

---

## 1. Problem Analysis

### Current State
```
kicli-code-assist:
  ├─ Flask backend (port 8000)
  ├─ Vite frontend (port 3000)
  └─ LLM service (port 8001)

ki-knowledge:
  ├─ Django backend (port 8002)
  └─ React frontend (port 3001)

ki-core:
  └─ LSP/type checker (internal)

stackctl:
  ├─ HTTP API (port 5000)
  └─ Worker processes (multiple)
```

### Pain Points
1. **Visibility Gap**: Which services are running? No inventory/registry.
2. **Ghost Processes**: `Ctrl+C` leaves daemons running; manual `kill <PID>` required.
3. **No Dependency Tracking**: Frontend tries to connect to dead backend.
4. **Scattered Logs**: Each service writes to different locations; no aggregation.
5. **Port Conflicts**: No detection of port reuse (two services on 8000).
6. **Manual Recovery**: No state persistence for restart after crash.
7. **Cross-Project Complexity**: Each project manages itself in isolation.

---

## 2. Architecture Options

### Option A: Daemon-Based (Supervisor Process)

```
┌─────────────────────────────────────────┐
│    Always-Running Supervisor Daemon     │  (systemd service or simple bg loop)
│                                         │
│  ┌─────────────────┐  ┌──────────────┐ │
│  │ Service Registry│◄─►│ Health Checks│ │
│  │ (in-memory +    │  │ (ping/HTTP)  │ │
│  │  persistent)    │  └──────────────┘ │
│  └────────┬────────┘                    │
│           │                             │
│  ┌────────▼─────────┐  ┌──────────────┐ │
│  │ Process Manager  │◄─►│ Port Scanner │ │
│  │ (start/stop)     │  │ (conflict    │ │
│  │                  │  │  detection)  │ │
│  └────────┬────────┘  └──────────────┘ │
│           │                             │
│  ┌────────▼──────────────────────────┐  │
│  │ Log Aggregator & Streamer         │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
         ▲           │           ▲
        CLI    WebSocket    REST API
    (server:*)            (JSON)
```

**Pros:**
- ✅ Real-time health monitoring (background checks)
- ✅ Proactive orphan detection
- ✅ No startup latency (already running)
- ✅ True dependency triggering (if backend dies, notify frontend)

**Cons:**
- ❌ Adds complexity (new daemon to manage)
- ❌ Debugging harder (separate process)
- ❌ Resource overhead (always-running process)
- ❌ Cross-platform issues (Windows systemd vs. launchd vs. init.d)
- ❌ Requires graceful shutdown handling

### Option B: Stateless CLI/WebUI (Direct Query)

```
┌─────────────────────────────────────┐
│   CLI: kicli-assist server:status   │
└──────────────┬──────────────────────┘
               │ calls at runtime
    ┌──────────▼────────────┐
    │  Query /proc/*/status │
    │  Run systemctl status │
    │  Exec netstat -tulpn  │
    └──────────┬────────────┘
               │
     ┌─────────▼──────────┐
     │ Format JSON output │
     │ Display to user    │
     └────────────────────┘
```

**Pros:**
- ✅ Simple, no daemon overhead
- ✅ No state to persist/recover
- ✅ Works on any system (queries OS interfaces)
- ✅ Easy to debug

**Cons:**
- ❌ Slow for large process trees (~1-2s to query all)
- ❌ No state history (can't detect "service crashed at 3:45pm")
- ❌ No real-time log streaming (read file at time of query)
- ❌ No proactive health checks (only reactive)
- ❌ Harder to track cross-service dependencies

### Option C: Hybrid (Recommended) ⭐

```
┌──────────────────────────────────────────────────────────┐
│               Server Registry API                        │
│  (JSON file in ~/.kicli/services.json + REST endpoints)  │
└──────────────┬─────────────────────────────────┬─────────┘
               │                                 │
        ┌──────▼──────┐              ┌──────────▼──────┐
        │  Optional    │              │   Direct Query  │
        │  Background  │              │   (fallback)    │
        │  Supervisor  │              │                 │
        │  (via CLI)   │              │  ps/netstat     │
        └──────┬──────┘              │  systemctl      │
               │                      │                 │
        ┌──────▼──────┐              │                 │
        │ Enriches    │              │                 │
        │ state.json  │              │                 │
        │ with health │              │                 │
        │ checks      │              │                 │
        └─────────────┘              └────────────────┘
               ▲                              ▲
         (optional)                   (always available)
```

**Pros:**
- ✅ Flexibility: Supervisor optional (dev) vs. required (CI/production)
- ✅ Fast startup: No daemon blocking
- ✅ Persistent state for audit + recovery
- ✅ Graceful degradation: Works without supervisor
- ✅ Cross-platform: Queries standard OS interfaces
- ✅ Easy testing: Can mock both supervisor and query layer

**Cons:**
- ⚠️ More code: Implements both paths
- ⚠️ State sync complexity: File <-> actual processes
- ⚠️ Lock coordination: Prevent concurrent operations

**Recommendation: OPTION C** - Balances simplicity with real-world needs.

---

## 3. Recommended Architecture (Option C)

### 3.1 Data Model: Service Registry

**File:** `~/.kicli/services.json`

```json
{
  "version": "1.0",
  "last_updated": "2026-10-28T03:16:40Z",
  "supervisor_pid": 45827,
  "supervisor_started": "2026-10-28T02:00:00Z",
  "services": [
    {
      "id": "kicli-backend",
      "name": "kicli Backend API",
      "project": "kicli-code-assist",
      "type": "backend",
      "status": "running",
      "pid": 12345,
      "port": 8000,
      "started_at": "2026-10-28T02:05:00Z",
      "command": "cd /home/flow/dev_flow/kicli-code-assist && python -m flask run",
      "working_dir": "/home/flow/dev_flow/kicli-code-assist",
      "dependencies": [],
      "health_check": {
        "method": "http",
        "url": "http://localhost:8000/health",
        "interval_seconds": 30,
        "last_check": "2026-10-28T03:16:30Z",
        "status": "healthy"
      },
      "logs": {
        "stdout": "/home/flow/.kicli/logs/kicli-backend.stdout.log",
        "stderr": "/home/flow/.kicli/logs/kicli-backend.stderr.log"
      },
      "memory_usage_mb": 156,
      "cpu_percent": 0.5
    },
    {
      "id": "kicli-frontend",
      "name": "kicli Frontend Dev Server",
      "project": "kicli-code-assist",
      "type": "frontend",
      "status": "running",
      "pid": 12346,
      "port": 3000,
      "started_at": "2026-10-28T02:05:30Z",
      "command": "cd /home/flow/dev_flow/kicli-code-assist/web/frontend && npm run dev",
      "working_dir": "/home/flow/dev_flow/kicli-code-assist/web/frontend",
      "dependencies": ["kicli-backend"],
      "health_check": {
        "method": "http",
        "url": "http://localhost:3000",
        "interval_seconds": 30,
        "last_check": "2026-10-28T03:16:35Z",
        "status": "healthy"
      },
      "logs": {
        "stdout": "/home/flow/.kicli/logs/kicli-frontend.stdout.log",
        "stderr": "/home/flow/.kicli/logs/kicli-frontend.stderr.log"
      },
      "memory_usage_mb": 245,
      "cpu_percent": 1.2
    }
  ],
  "audit_log": [
    {
      "timestamp": "2026-10-28T02:05:00Z",
      "action": "start",
      "service_id": "kicli-backend",
      "user": "flow",
      "status": "success",
      "message": null
    },
    {
      "timestamp": "2026-10-28T03:10:15Z",
      "action": "health_check_failed",
      "service_id": "kicli-frontend",
      "user": "supervisor",
      "status": "failure",
      "message": "No response from http://localhost:3000 (timeout after 5s)"
    }
  ]
}
```

### 3.2 Service Registry Class

**File:** `kicli_code_assist/web/server_registry.py` (new)

```python
class ServerRegistry:
    """Manages service state persistence and querying."""
    
    def __init__(self, registry_file: str = "~/.kicli/services.json"):
        self.registry_file = Path(registry_file).expanduser()
        self.lock_file = self.registry_file.with_suffix('.lock')
        self._ensure_directories()
    
    def get_service(self, service_id: str) -> ServiceState | None:
        """Fetch service by ID."""
        
    def list_services(self, project: str = None, status: str = None) -> List[ServiceState]:
        """List all services, optionally filtered."""
        
    def register_service(self, service: ServiceDefinition) -> ServiceState:
        """Register and start a service."""
        
    def update_service(self, service_id: str, **updates) -> ServiceState:
        """Update service state (status, pid, health_check, etc)."""
        
    def remove_service(self, service_id: str):
        """Deregister a service."""
        
    def audit_log(self, action: str, service_id: str, status: str, message: str):
        """Write to audit trail."""
        
    def _acquire_lock(self, timeout: float = 5.0) -> bool:
        """Prevent concurrent writes; returns True if acquired."""
        
    def _release_lock(self):
        """Release lock file."""
```

---

## 4. CLI Interface

**Command structure:** `kicli-assist server:<action> [service-id] [options]`

```bash
# Status & Discovery
kicli-assist server:list                    # List all services
kicli-assist server:list --project ki-knowledge
kicli-assist server:list --status running
kicli-assist server:status <service-id>    # Show detailed status

# Control
kicli-assist server:start <service-id>     # Start service (and dependencies)
kicli-assist server:stop <service-id>      # Graceful stop (SIGTERM)
kicli-assist server:stop <service-id> --force  # Force stop (SIGKILL)
kicli-assist server:restart <service-id>   # Restart

# Debugging
kicli-assist server:logs <service-id> [--tail 50] [--follow]
kicli-assist server:health-check <service-id>
kicli-assist server:cleanup                # Kill orphaned processes

# Supervisor Control (if running)
kicli-assist server:supervisor:start       # Start background supervisor
kicli-assist server:supervisor:stop        # Stop supervisor
kicli-assist server:supervisor:status      # Check if running
```

---

## 5. WebUI Integration

### Dashboard Location
**New React page:** `web/frontend/src/pages/ServerDashboard.tsx`

**Integration points:**
- Add to main sidebar navigation
- `/dashboard/servers` route in React Router
- Connect to Flask API endpoints

### Features
1. **Service List Table**
   - Columns: Name | Status | PID | Port | Memory | CPU | Uptime
   - Color-coded status (🟢 running, 🔴 stopped, 🟡 unhealthy)
   - Click row to drill down

2. **Service Detail View**
   - Real-time health status + last check time
   - Dependencies visualization
   - Command line used to start
   - Port + process tree

3. **Live Logs Tab**
   - Last 100 lines (stdout + stderr combined)
   - Auto-scroll to tail
   - Search/filter logs
   - Export logs to file

4. **Control Buttons**
   - Start/Stop/Restart (with confirmation dialog)
   - Force kill (red button, extra confirmation)
   - Refresh health status

5. **System Statistics**
   - Total memory used by all services
   - CPU usage chart (last 5 minutes)
   - Port usage overview

---

## 6. Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1)
- [x] Design service registry schema
- [ ] Implement `ServerRegistry` class with file persistence
- [ ] Write unit tests for registry (CRUD, locking, audit log)
- [ ] Add service definition config format

### Phase 2: CLI Commands (Week 1-2)
- [ ] Implement `server:list`, `server:status` commands
- [ ] Add `server:start` and `server:stop` with dependency resolution
- [ ] Implement `server:logs`, `server:health-check`
- [ ] Write CLI integration tests

### Phase 3: Optional Supervisor (Week 2)
- [ ] Create background supervisor process
- [ ] Implement health check loop
- [ ] Add auto-restart on failure
- [ ] Graceful shutdown handling

### Phase 4: WebUI Integration (Week 2-3)
- [ ] Create `ServerDashboard` React component
- [ ] Implement REST API endpoints in Flask
- [ ] Add WebSocket streaming for real-time updates
- [ ] Test dashboard with live services

### Phase 5: Cross-Project Support (Week 3-4)
- [ ] Add multi-project config file format
- [ ] Extend `server:list --project <name>`
- [ ] Create shared service definitions (ki-knowledge, ki-core, stackctl)
- [ ] End-to-end test across projects

### Phase 6: Safety & Polish (Week 4)
- [ ] Add user confirmation dialogs
- [ ] Implement audit logging
- [ ] Write documentation + examples
- [ ] Performance testing

---

## 7. API Reference

### REST Endpoints (Flask Backend)

```
GET    /api/services                    List all services
GET    /api/services/<service_id>       Get service details
GET    /api/services/<service_id>/logs  Stream service logs
GET    /api/services/<service_id>/health  Check health
POST   /api/services/<service_id>/start
POST   /api/services/<service_id>/stop
POST   /api/services/<service_id>/restart
GET    /api/audit-log                   Fetch audit trail
```

### WebSocket Events

```
/ws/services
├─ service:updated        # Status/health changed
├─ service:created        # New service registered
├─ service:removed        # Service deregistered
└─ service:log            # New log line available
```

---

## 8. Data Flow Examples

### Starting a Service with Dependencies

```
CLI: kicli-assist server:start kicli-frontend
    ↓
Registry.get_service("kicli-frontend")
    ↓
Detect dependencies: ["kicli-backend"]
    ↓
Is kicli-backend running?
    ├─ NO: Start kicli-backend first, wait for health check (30s timeout)
    └─ YES: Continue
    ↓
Start kicli-frontend (spawn subprocess)
    ↓
Poll health check URL (http://localhost:3000)
    ├─ Success: Update registry status="running"
    └─ Timeout: Update status="unhealthy", log error
    ↓
Write to audit log: "start" action by "flow" user
    ↓
Return to CLI: "✓ kicli-frontend started (PID 12346)"
```

### Detecting Orphaned Processes

```
Registry.get_service("kicli-backend")
    ├─ status="running", pid=12345
    ↓
ps aux | grep 12345
    ├─ Process NOT FOUND
    ↓
Health check fails
    ↓
Supervisor detects dead process, updates status="stopped"
    ↓
Notification: "kicli-backend crashed at 2026-10-28 03:15:42"
    ↓
Auto-restart enabled?
    ├─ YES: kicli-assist server:start kicli-backend
    └─ NO: Alert user
```

### Port Conflict Detection

```
User tries: kicli-assist server:start kicli-backend
    ↓
Service definition says: port=8000
    ↓
netstat -tulpn | grep :8000
    ├─ Port already in use by PID 999 (different process)
    ↓
Error: "Port 8000 already in use by process 999 (/usr/bin/other-app)"
    ├─ Suggest: kicli-assist server:cleanup
    └─ Or: Use alternative port (--port 8001)
```

---

## 9. State Persistence & Recovery

### Lock Mechanism

```
┌──────────────────────┐
│ services.json        │ (actual registry state)
└──────────────────────┘
         ▲
         │
┌────────┴────────────────┐
│ services.json.lock      │
│ {pid: 12345, ts: 123}   │ (prevents concurrent writes)
└─────────────────────────┘

Lock acquisition:
1. Try to create/open .lock file (exclusive mode)
2. Write current PID + timestamp
3. On exit, remove .lock file
4. If lock is stale (>10min old), forcibly acquire
```

### Crash Recovery

If supervisor crashes:
1. Registry file persists (JSON)
2. On next command, registry reads state
3. Compares PIDs in registry vs. /proc
4. Marks dead processes as "stopped"
5. Alerts user about unexpected terminations

---

## 10. Risk Assessment & Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Supervisor crashes** | HIGH | Persistent registry file; graceful recovery on restart |
| **Concurrent writes** | HIGH | File-based locking (.lock file with PID) |
| **Port conflicts** | MEDIUM | Pre-start port scan; clear conflict message |
| **Ghost processes** | MEDIUM | Periodic health checks; auto-cleanup command |
| **Accidental kill** | MEDIUM | Confirmation dialogs; audit trail for accountability |
| **State desync** | MEDIUM | Version field in registry; periodic full reconciliation |
| **Cross-platform** | MEDIUM | Abstraction layer for OS commands (ps vs. tasklist) |

---

## 11. Configuration Format

**File:** `~/.kicli/projects.yaml` (defines service inventory)

```yaml
projects:
  kicli-code-assist:
    root: /home/flow/dev_flow/kicli-code-assist
    services:
      - id: kicli-backend
        name: Backend API
        type: backend
        command: python -m flask run
        port: 8000
        health_check:
          method: http
          url: /health
        dependencies: []
        
      - id: kicli-frontend
        name: Frontend Dev
        type: frontend
        command: cd web/frontend && npm run dev
        port: 3000
        health_check:
          method: http
          url: /
        dependencies:
          - kicli-backend
          
  ki-knowledge:
    root: /home/flow/dev_flow/ki-knowledge
    services:
      - id: ki-django-backend
        name: Django API
        type: backend
        command: python manage.py runserver 0.0.0.0:8002
        port: 8002
        health_check:
          method: http
          url: /health
        dependencies: []
```

**Integration:** Loaded by `ServerRegistry` on startup; merged with runtime state.

---

## 12. Success Criteria

✅ **MVP (Week 1-2):**
- [x] Registry file persists service state
- [x] CLI commands: `list`, `status`, `start`, `stop`, `logs`
- [x] Dependency resolution working
- [x] Port conflict detection active

✅ **Production Ready (Week 3-4):**
- [x] Optional supervisor running in background
- [x] WebUI dashboard functional
- [x] Audit logging comprehensive
- [x] Cross-project support stable
- [x] Documented & tested

---

## 13. Long-Term Vision

1. **Container Support**: Extend to Docker/Kubernetes (read container status)
2. **Cloud Deployment**: Sync registry to cloud for remote access
3. **Team Coordination**: Shared server state for multi-developer environments
4. **Performance Monitoring**: Persistent metrics + alerting
5. **Integration with CI/CD**: Trigger builds from server state changes

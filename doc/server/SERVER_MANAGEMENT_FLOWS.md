# Server Management System - Architecture Diagrams & Flows

## 1. System Overview (Option C: Hybrid)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    UNIFIED SERVER MANAGEMENT SYSTEM                      │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    USER INTERFACES                             │   │
│  │                                                                 │   │
│  │  ┌──────────────────┐          ┌──────────────────────────┐   │   │
│  │  │   CLI Interface  │          │     WebUI Dashboard      │   │   │
│  │  │                  │          │                          │   │   │
│  │  │ kicli-assist     │          │ React Component          │   │   │
│  │  │ server:status    │          │ /dashboard/servers       │   │   │
│  │  │ server:start     │          │ • Service list           │   │   │
│  │  │ server:stop      │          │ • Live logs              │   │   │
│  │  │ server:logs      │          │ • Health status          │   │   │
│  │  │ server:cleanup   │          │ • Control buttons        │   │   │
│  │  └────────┬─────────┘          └──────────┬───────────────┘   │   │
│  └───────────┼──────────────────────────────┼──────────────────┘   │
│              │                              │                      │
│  ┌───────────▼──────────────────────────────▼──────────────────┐   │
│  │                   CORE REGISTRY API                         │   │
│  │                                                              │   │
│  │  ServerRegistry class:                                       │   │
│  │  • get_service(id)                                           │   │
│  │  • list_services(project, status)                            │   │
│  │  • start_service(id) → spawn process                         │   │
│  │  • stop_service(id) → SIGTERM/SIGKILL                        │   │
│  │  • check_health(id) → HTTP probe                             │   │
│  │  • audit_log(action, service, user)                          │   │
│  │                                                              │   │
│  │  [File-based locking for concurrent safety]                 │   │
│  └───────────┬──────────────────────────────────────────────┬──┘   │
│              │                                              │        │
│  ┌───────────▼────────────────────┐  ┌───────────────────▼─────┐  │
│  │  PERSISTENT STORAGE            │  │  EPHEMERAL OS STATE    │  │
│  │                                │  │                        │  │
│  │ ~/.kicli/services.json         │  │ Real-time queries:     │  │
│  │ {                              │  │                        │  │
│  │   services: [                  │  │ • /proc/*/status       │  │
│  │     {                          │  │ • ps aux               │  │
│  │       id: "kicli-backend",     │  │ • netstat -tulpn       │  │
│  │       pid: 12345,              │  │ • systemctl status     │  │
│  │       status: "running",       │  │                        │  │
│  │       health: { ... },         │  │ Detects mismatches:    │  │
│  │       logs: { ... }            │  │ • Dead processes       │  │
│  │     }                          │  │ • Port conflicts       │  │
│  │   ],                           │  │ • Resource usage       │  │
│  │   audit_log: [ ... ]           │  │                        │  │
│  │ }                              │  │                        │  │
│  │                                │  │                        │  │
│  │ ~/.kicli/projects.yaml         │  │                        │  │
│  │ (service definitions)          │  │                        │  │
│  │                                │  │                        │  │
│  │ ~/.kicli/logs/                 │  │                        │  │
│  │ (stdout/stderr per service)    │  │                        │  │
│  │                                │  │                        │  │
│  │ ~/.kicli/audit.jsonl           │  │                        │  │
│  │ (who did what, when)           │  │                        │  │
│  └────────────────────────────────┘  └────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │         [OPTIONAL] BACKGROUND SUPERVISOR                  │  │
│  │                                                            │  │
│  │  • Runs as daemon/systemd service                          │  │
│  │  • Polls health checks every 30s                           │  │
│  │  • Updates services.json with new state                    │  │
│  │  • Triggers restart if enabled                             │  │
│  │  • Sends alerts on failure                                 │  │
│  │  • Gracefully shuts down on signal                         │  │
│  │                                                            │  │
│  │  PID stored in services.json.supervisor_pid               │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

                          MANAGED SERVICES
                                │
                ┌───────────────┼───────────────┐
                │               │               │
            ┌───▼────┐      ┌───▼────┐     ┌──▼────┐
            │ Backend │      │Frontend│     │ Worker│
            │(Python) │      │(Node)  │     │(Python)
            │ :8000   │      │ :3000  │     │:15000
            └─────────┘      └────────┘     └───────┘
```

---

## 2. State Flow Diagram: Starting a Service

```
START: user runs "kicli-assist server:start kicli-frontend"
    │
    ▼
ACQUIRE LOCK
    │ Exclusive access to ~/.kicli/services.json
    ├─ Lock exists? Check if stale (>10min)
    └─ Yes → Wait or fail with timeout
    │
    ▼
LOAD REGISTRY
    │ Read services.json
    │ Parse service definition for "kicli-frontend"
    │
    ├─ NOT FOUND? → Error: "Service not found"
    │
    ▼
CHECK DEPENDENCIES
    │ dependencies: ["kicli-backend"]
    │
    ├─ For each dependency:
    │   ├─ Is running? Check status + health
    │   │
    │   ├─ NO → Recursively call START
    │   │   └─ start_service("kicli-backend")
    │   │       └─ Wait for health check (30s timeout)
    │   │
    │   ├─ TIMEOUT? → Error: "Dependency failed to start"
    │   │
    │   └─ YES → Continue
    │
    ▼
PORT CONFLICT CHECK
    │ netstat -tulpn | grep :3000
    │
    ├─ Port in use? Check if it's our service (same PID)
    │   ├─ Different PID? → Error: "Port conflict with PID 999"
    │   └─ Same PID? → Service already running
    │
    ▼
SPAWN PROCESS
    │
    ├─ subprocess.Popen(
    │     command="cd /path && npm run dev",
    │     stdout=open("~/.kicli/logs/kicli-frontend.stdout.log", "a"),
    │     stderr=open("~/.kicli/logs/kicli-frontend.stderr.log", "a"),
    │     start_new_session=True  # Detach from parent
    │   )
    │
    ├─ Capture new PID
    │
    ▼
POLL HEALTH CHECK
    │ Check URL: http://localhost:3000
    │ Retry every 2s, timeout 30s
    │
    ├─ SUCCESS → Status = "running"
    │
    ├─ TIMEOUT → Status = "unhealthy"
    │   └─ Log: "Process started but failed health check"
    │
    ├─ HTTP ERROR → Status = "unhealthy"
    │   └─ Log: "Health check returned {status_code}"
    │
    ▼
UPDATE REGISTRY
    │ services.json[kicli-frontend] = {
    │   status: "running",
    │   pid: 54321,
    │   started_at: now(),
    │   health_status: "healthy",
    │   last_health_check: now()
    │ }
    │
    ▼
AUDIT LOG
    │ audit.jsonl << {
    │   timestamp: now(),
    │   action: "start",
    │   service_id: "kicli-frontend",
    │   user: "flow",
    │   status: "success",
    │   message: null
    │ }
    │
    ▼
RELEASE LOCK
    │ Remove ~/.kicli/services.json.lock
    │
    ▼
RETURN TO USER
    │ ✓ kicli-frontend started (PID 54321)
    │   Dependencies: kicli-backend (PID 12345)
    │   Health: healthy
    │   Logs: ~/.kicli/logs/kicli-frontend.stdout.log
    │
END
```

---

## 3. Detection & Recovery: Orphaned Process

```
BACKGROUND SUPERVISOR LOOP (Every 30 seconds)
    │
    ├─ FOR EACH service in registry:
    │  
    │   ▼
    │   READ REGISTRY STATE
    │   │ status="running", pid=12345
    │   │
    │   ▼
    │   CHECK IF PROCESS ALIVE
    │   │ ps -p 12345 > /dev/null
    │   │
    │   ├─ YES → Continue to health check
    │   │
    │   ├─ NO (Process is DEAD)
    │   │   │
    │   │   ▼
    │   │   UPDATE REGISTRY
    │   │   │ services.json[kicli-backend].status = "stopped"
    │   │   │ services.json[kicli-backend].stopped_at = now()
    │   │   │
    │   │   ▼
    │   │   AUDIT LOG (Crash detected)
    │   │   │ audit.jsonl << {
    │   │   │   timestamp: now(),
    │   │   │   action: "crash_detected",
    │   │   │   service_id: "kicli-backend",
    │   │   │   user: "supervisor",
    │   │   │   status: "failure",
    │   │   │   message: "Process died unexpectedly"
    │   │   │ }
    │   │   │
    │   │   ▼
    │   │   ALERT DEPENDENTS
    │   │   │ dependents = [kicli-frontend]
    │   │   │ FOR dependent in dependents:
    │   │   │   └─ Update dependent.health = "warning"
    │   │   │      Log: "Dependency kicli-backend crashed"
    │   │   │      Send WebSocket event to UI
    │   │   │
    │   │   ▼
    │   │   AUTO-RESTART? (if enabled)
    │   │   │ if config.auto_restart:
    │   │   │   └─ start_service("kicli-backend")
    │   │   │
    │   │   ▼
    │   │   END ITERATION
    │   │
    │   └─ Health check (process alive)
    │       │
    │       ▼
    │       PROBE HEALTH CHECK URL
    │       │ http://localhost:8000/health
    │       │ Timeout: 5s
    │       │
    │       ├─ SUCCESS (200 OK)
    │       │  └─ status = "healthy", last_check = now()
    │       │
    │       ├─ FAILURE (5xx or timeout)
    │       │  │
    │       │  ▼
    │       │  Is this first failure?
    │       │  ├─ NO → Already marked unhealthy
    │       │  │
    │       │  ├─ YES → First unhealthy
    │       │      │
    │       │      ▼
    │       │      UPDATE REGISTRY
    │       │      │ status = "unhealthy"
    │       │      │ health_status = "failing"
    │       │      │
    │       │      ▼
    │       │      AUDIT LOG
    │       │      │ action: "health_check_failed"
    │       │      │
    │       │      ▼
    │       │      SEND ALERT
    │       │      │ WebSocket: service:unhealthy
    │       │      │ CLI: Show warning on next "server:status"
    │       │      │
    │       │      END ITERATION
    │
    ▼
LOOP (sleep 30s, repeat)
```

---

## 4. Data Storage Structure

### Directory Hierarchy

```
~/.kicli/
├── services.json              ← Main registry (persistent state)
├── services.json.lock         ← Lock file (concurrent access control)
├── projects.yaml              ← Service definitions (all projects)
├── audit.jsonl                ← Audit trail (append-only)
├── logs/                       ← Service logs
│   ├── kicli-backend.stdout.log
│   ├── kicli-backend.stderr.log
│   ├── kicli-frontend.stdout.log
│   ├── kicli-frontend.stderr.log
│   ├── ki-django.stdout.log
│   └── ki-django.stderr.log
└── checkpoints/               ← Crash recovery snapshots
    ├── 2026-10-28-03-00.snapshot.json
    └── 2026-10-28-04-00.snapshot.json
```

### services.json Schema

```json
{
  "version": "1.0",
  "last_updated": "2026-10-28T03:16:40Z",
  "supervisor": {
    "pid": 45827,
    "started_at": "2026-10-28T02:00:00Z",
    "health": "running"
  },
  "services": [
    {
      "id": "kicli-backend",
      "project": "kicli-code-assist",
      "name": "Backend API",
      "type": "backend",
      "status": "running|stopped|unhealthy",
      "pid": 12345,
      "port": 8000,
      "started_at": "2026-10-28T02:05:00Z",
      "stopped_at": null,
      "command": "python -m flask run",
      "working_dir": "/home/flow/dev_flow/kicli-code-assist",
      "dependencies": [],
      "health_check": {
        "method": "http",
        "url": "http://localhost:8000/health",
        "interval_seconds": 30,
        "timeout_seconds": 5,
        "last_check": "2026-10-28T03:16:30Z",
        "last_status": "healthy",
        "consecutive_failures": 0
      },
      "logs": {
        "stdout": "~/.kicli/logs/kicli-backend.stdout.log",
        "stderr": "~/.kicli/logs/kicli-backend.stderr.log"
      },
      "resources": {
        "memory_mb": 156,
        "cpu_percent": 0.5,
        "last_measured": "2026-10-28T03:16:30Z"
      }
    }
  ],
  "audit_log": [
    {
      "timestamp": "2026-10-28T02:05:00Z",
      "action": "start|stop|restart|crash_detected|health_check_failed|health_restored",
      "service_id": "kicli-backend",
      "user": "flow|supervisor|webhook",
      "status": "success|failure|cancelled",
      "message": "Details about the action"
    }
  ]
}
```

---

## 5. Concurrency & Locking

### Lock Acquisition Pattern

```
Process A tries to START kicli-backend:
    │
    ▼
try:
    fd = os.open(
        "~/.kicli/services.json.lock",
        O_CREAT | O_EXCL | O_WRONLY  ← Exclusive! Fails if exists
    )
    write(fd, {"pid": 12345, "timestamp": "2026-10-28T03:16:40Z", ...})
    close(fd)
    ✓ ACQUIRED
│
├─ Perform registry updates
│
└─ os.remove("~/.kicli/services.json.lock")
   ✓ RELEASED

---

Process B tries to START kicli-frontend AT SAME TIME:
    │
    ▼
try:
    os.open(..., O_CREAT | O_EXCL | O_WRONLY)
    FileExistsError ← Lock held by Process A!
│
├─ Read lock file
│   ├─ Stale? (>10 minutes old) → Force remove & retry
│   └─ Fresh → Wait 0.1s, retry
│
└─ Retry with reduced timeout

If timeout > 0 and lock still held:
    ├─ Retry with shorter timeout
    └─ Loop until acquired or timeout=0

If timeout reached:
    └─ Raise RuntimeError("Could not acquire lock")
```

---

## 6. WebUI Component Layout

```
┌────────────────────────────────────────────────────────────────┐
│ 🖥️  Server Management Dashboard                               │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ Filter: [All Projects ▼] [All Status ▼] [Refresh]            │
└────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Service Summary:                                            │
│  Total: 5  Running: 4  Unhealthy: 1  Stopped: 0           │
│  Memory: 1.2GB  CPU: 3.2%                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Services Table                                              │
├─────────────────────────────────────────────────────────────┤
│ Name            │Project│Status  │PID  │Port│Memory│Uptime│
├─────────────────────────────────────────────────────────────┤
│ 🟢 Backend API  │kicli  │Running │1234 │8000│156MB │2h14m │
│ 🟢 Frontend     │kicli  │Running │1235 │3000│245MB │2h14m │
│ 🟡 LLM Service  │kicli  │Unhealthy│1236│8001│312MB │2h00m │
│ 🟢 Ki-Django    │ki-kn  │Running │1237 │8002│189MB │1h45m │
│ 🟢 Stackctl API │stack  │Running │1238 │5000│98MB  │30m   │
└─────────────────────────────────────────────────────────────┘

Click row to expand ▼

┌─────────────────────────────────────────────────────────────┐
│ ▼ kicli-backend (Backend API)                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Status:        🟢 Running                                   │
│ PID:           12345                                        │
│ Port:          8000                                         │
│ Command:       python -m flask run                          │
│ Started:       2026-10-28 02:05:00 (2h 14m ago)            │
│ Memory:        156 MB (avg: 140 MB, peak: 180 MB)          │
│ CPU:           0.5% (avg: 0.3%, peak: 1.2%)                │
│                                                             │
│ Dependencies:  None                                         │
│ Dependents:    kicli-frontend                               │
│                                                             │
│ Health Check:  ✓ Healthy (last: 2026-10-28 03:16:30)      │
│                GET /health → 200 OK (45ms)                  │
│                                                             │
│ Recent Logs:                                                │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 03:16:35 - INFO - Request POST /chat from 127.0.0.1   ││
│ │ 03:16:34 - DEBUG - LLM response: 2156 tokens           ││
│ │ 03:16:30 - INFO - Health check passed                  ││
│ │ 03:16:20 - DEBUG - Cache hit for context (2.3s)        ││
│ │ [Show more... (↑ scroll, ↓ tail 50, ⚡ follow)]       ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ Actions:                                                    │
│ [⏹️  Stop] [🔄 Restart] [⚙️  Config] [📋 Logs]             │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Audit Trail (last 10 actions)                               │
├─────────────────────────────────────────────────────────────┤
│ 03:16:30 | health_check_passed | kicli-backend | supervisor│
│ 03:10:15 | health_check_failed | kicli-frontend | supervisor│
│ 03:10:16 | restart             | kicli-frontend | supervisor│
│ 02:30:00 | start               | kicli-backend  | flow      │
│ ...                                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Dependency Resolution Graph

```
kicli-code-assist project:

    ┌──────────────────┐
    │ kicli-backend    │ (port 8000)
    │ Python / Flask   │
    │ No dependencies  │
    └────────┬─────────┘
             │
             │ [DEPENDS ON]
             ▼
    ┌──────────────────────┐
    │ kicli-frontend       │ (port 3000)
    │ Node / Vite          │
    │ Dep: kicli-backend   │
    └──────────────────────┘


ki-knowledge project:

    ┌──────────────────┐
    │ ki-django        │ (port 8002)
    │ Python / Django  │
    │ No dependencies  │
    └────────┬─────────┘
             │
             │ [DEPENDS ON]
             ▼
    ┌──────────────────────┐
    │ ki-react-frontend    │ (port 3001)
    │ Node / React         │
    │ Dep: ki-django       │
    └──────────────────────┘


START ki-frontend resolution tree:

    start(kicli-frontend)
         ├─ Check dependency: kicli-backend
         │   ├─ Is running? NO
         │   └─ start(kicli-backend)
         │       ├─ No dependencies
         │       ├─ Spawn process
         │       ├─ Poll health check
         │       └─ ✓ kicli-backend started
         │
         ├─ Dependency satisfied: kicli-backend ✓
         ├─ Spawn kicli-frontend
         ├─ Poll health check
         └─ ✓ kicli-frontend started


STOP kicli-backend resolution tree:

    stop(kicli-backend)
         ├─ Find dependents: [kicli-frontend]
         ├─ Alert: "Frontend depends on Backend"
         ├─ Send SIGTERM to kicli-backend (PID 12345)
         ├─ Wait for process death (timeout 10s)
         ├─ Update registry: status = "stopped"
         └─ Log dependents in audit trail
```

---

## 8. Error Scenarios & Handling

```
SCENARIO 1: Port Conflict
─────────────────────────

User: kicli-assist server:start kicli-backend
       But port 8000 already in use by Apache

Flow:
    get_service("kicli-backend")
         └─ port = 8000
         ├─ netstat -tulpn | grep :8000
         └─ Returns: "LISTEN 127.0.0.1:8000 (PID 999 /usr/bin/apache)"
    
    ├─ Is PID 999 our process?
    │   └─ NO (different PID)
    │
    └─ Error: "Port 8000 already in use by PID 999"
          ├─ Suggest: kicli-assist server:cleanup (might kill orphan)
          ├─ Or: Use alternative port: --port 8001
          └─ Return HTTP 409 to WebUI


SCENARIO 2: Dependency Not Running
────────────────────────────────────

User: kicli-assist server:start kicli-frontend
      But kicli-backend is stopped

Flow:
    get_service("kicli-frontend")
         ├─ dependencies = ["kicli-backend"]
         ├─ get_service("kicli-backend").status
         │   └─ "stopped"
         │
         └─ Trigger: start_service("kicli-backend") recursively
              ├─ Spawn backend process
              ├─ Poll health check (30s timeout)
              │
              ├─ TIMEOUT (backend not responding)
              │  │
              │  └─ Error: "Dependency kicli-backend failed to start"
              │       ├─ Reason: No response from http://localhost:8000/health
              │       ├─ Logs: ~/.kicli/logs/kicli-backend.stderr.log
              │       └─ Action: Fix backend, then retry
              │
              └─ SUCCESS
                   └─ Continue to start kicli-frontend


SCENARIO 3: Process Already Running
──────────────────────────────────────

User: kicli-assist server:start kicli-backend
      But kicli-backend already running (PID 12345)

Flow:
    get_service("kicli-backend")
         ├─ status = "running"
         ├─ pid = 12345
         │
         ├─ ps -p 12345
         │   └─ Process exists ✓
         │
         ├─ Health check: http://localhost:8000/health
         │   └─ 200 OK ✓
         │
         └─ Already running with PID 12345
              ├─ Return: "Service already running"
              └─ Return existing PID to user


SCENARIO 4: Stale Lock File
──────────────────────────────

Supervisor crashes while holding lock
    └─ services.json.lock remains:
          {
            "pid": 45827,
            "timestamp": "2026-10-28 02:00:00"
          }

User: kicli-assist server:start kicli-backend (12 hours later)

Flow:
    acquire_lock()
         ├─ Try to create .lock file
         ├─ FileExistsError (lock exists)
         │
         ├─ Read lock file
         │   ├─ timestamp = "2026-10-28 02:00:00" (12 hours ago)
         │   ├─ is_stale() = (now - timestamp) > 600s
         │   │   └─ TRUE
         │   │
         │   └─ Lock is stale, forcibly remove
         │
         ├─ os.remove(lock_file)
         │
         └─ Retry acquire_lock() ✓
```

# Server Management System - Key Architectural Decisions

## Answer to Question 1: Architecture Choice

**SELECTED: Option C (Hybrid)**

### Detailed Comparison

| Factor | Option A (Daemon) | Option B (Stateless) | Option C (Hybrid) |
|--------|-------------------|----------------------|-------------------|
| **Complexity** | High | Low | Medium |
| **Real-time monitoring** | ✅ Yes (background) | ❌ No (polling) | ✅ Yes (optional) |
| **Startup latency** | ✅ None | ✅ None | ✅ None |
| **Requires daemon** | ✅ Must run | ❌ No | ⚠️ Optional |
| **State persistence** | ✅ Yes | ❌ No | ✅ Yes |
| **Works offline** | ❌ Supervisor needed | ✅ Yes | ✅ Yes |
| **Dev experience** | ⚠️ Extra process | ✅ Simplest | ✅ Best |
| **Crash recovery** | ❌ Weak | ✅ Good | ✅ Excellent |
| **Cross-platform** | ❌ Difficult | ✅ Easy | ✅ Easy |
| **Learning curve** | High | Low | Medium |

### Why Not Option A (Daemon)?

- **Local development pain**: Developers would need to manage supervisor lifecycle
- **Debugging nightmare**: Errors in supervisor hard to trace
- **Cross-platform hell**: systemd (Linux) vs. launchd (macOS) vs. Windows Services
- **Resource overhead**: Always-running process consumes memory/CPU
- **Testing complexity**: Unit tests harder to write (need to mock daemon)

### Why Not Option B (Stateless)?

- **Slow to query**: `ps` + `netstat` + health checks = 1-2 second latency
- **No history**: Can't answer "when did the backend crash?"
- **Poor UX**: WebUI can't show real-time metrics or logs efficiently
- **Missing audit trail**: No accountability for who stopped what service
- **Dependency tracking impossible**: No state to reason about service relationships

### Why Option C Is Best

✅ **Graceful degradation**: Works perfectly without supervisor (CLI queries OS directly)
✅ **Performance**: Supervisor enriches cached state; queries are instant
✅ **Developer friendly**: Optional supervisor means dev can choose
✅ **Production ready**: Supervisor can run as systemd service in production
✅ **Testable**: Can mock both paths (with/without supervisor)
✅ **Future proof**: Easy to add Docker/Kubernetes support later

---

## Answer to Question 2: State Storage

**SELECTED: Hybrid JSON File + Ephemeral OS State**

### Storage Strategy

```
┌─────────────────────────────────────────┐
│       ~/.kicli/services.json            │  (persistent)
│                                         │
│  • Service metadata (id, command, etc)  │
│  • Last known state (status, PID, port) │
│  • Audit trail (timestamps, actions)    │
│  • Health check results (last 24h)      │
└─────────────────────────────────────────┘
                   ▲
         ┌─────────┼─────────┐
         │         │         │
    ┌────┴───┐ ┌──┴──┐  ┌───┴────┐
    │ /proc  │ │systemctl psctl   │
    └────────┘ │     │  │/netstat│
               └─────┘  └────────┘
             (ephemeral OS queries)
```

### Why NOT Pure /proc (Option B)?

**Problem:** `/proc` data is **ephemeral** - dies with reboot
- No history: "When did service crash?" → No answer
- No audit: "Who killed the backend?" → No answer
- Lost state: Crash recovery impossible

### Why NOT Pure JSON File (problematic)?

**Problem:** State goes stale
- Service shown as "running" but process is dead
- Need constant sync to reality (requires supervisor)

### Solution: Hybrid (Recommended)

1. **Registry file** (`services.json`):
   - Persistent storage of **intended state** + **history**
   - Audit trail: every action logged with timestamp + user
   - Metadata: service definition (command, port, health check URL)

2. **OS queries** (ps, netstat, systemctl):
   - Real-time **actual state** of processes
   - Detect mismatches (e.g., process dead but registry says running)
   - Port conflict detection

3. **Reconciliation logic**:
   ```python
   def get_actual_state(service_id):
       registry_entry = registry.get(service_id)
       actual_pid = find_process_by_pid(registry_entry.pid)
       
       if actual_pid is None:
           # Process is dead; update registry
           registry.update(service_id, status="stopped", end_time=now())
           return "stopped"
       
       # Process alive; do health check
       health = check_http_health(registry_entry.health_check_url)
       registry.update(service_id, health_status=health)
       return "running" if health else "unhealthy"
   ```

### Lock File Mechanism

**File:** `~/.kicli/services.json.lock`

```json
{
  "pid": 45827,
  "timestamp": "2026-10-28T03:16:40Z",
  "command": "kicli-assist server:start kicli-backend",
  "expired": false
}
```

**Acquisition logic:**

```python
def acquire_lock(timeout=5.0):
    # Try to create lock file exclusively
    try:
        fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, json.dumps({
            "pid": os.getpid(),
            "timestamp": datetime.now().isoformat(),
            "command": sys.argv
        }).encode())
        os.close(fd)
        return True
    except FileExistsError:
        # Lock exists; check if stale (>10 minutes old)
        lock_time = json.load(open(lock_file))["timestamp"]
        if (datetime.now() - datetime.fromisoformat(lock_time)).total_seconds() > 600:
            # Stale lock; forcibly remove
            os.remove(lock_file)
            return acquire_lock(timeout)  # Retry
        
        # Lock held by another process; wait
        time.sleep(0.1)
        return acquire_lock(timeout - 0.1)  # Retry with less timeout
    
    # Timeout exceeded
    raise RuntimeError("Could not acquire server registry lock")

def release_lock():
    try:
        os.remove(lock_file)
    except FileNotFoundError:
        pass  # Already released
```

**Benefits:**
- ✅ Prevents concurrent writes to JSON file
- ✅ Handles stale locks automatically
- ✅ Works on all platforms (no fcntl or Windows-specific code)
- ✅ Simple, no background threads

---

## Answer to Question 3: Scope (Single vs. Multi-Project)

**SELECTED: Multi-Project Support from Day 1**

### Rationale

Current landscape:
```
kicli-code-assist    ← Main focus
  ├─ Backend
  └─ Frontend

ki-knowledge         ← Will launch soon
  ├─ Django backend
  └─ React frontend

ki-core              ← Shared library
  └─ LSP service

stackctl             ← Companion tool
  ├─ HTTP API
  └─ Workers
```

**Why start multi-project?**

1. **Same pain everywhere**: All projects have scattered processes
2. **Almost no extra effort**: Just add `project` field to registry
3. **Future-proofs the system**: No refactoring needed later
4. **Enables cross-project scenarios**: "Stop all backends" command

### Implementation

**Configuration file:** `~/.kicli/projects.yaml`

```yaml
projects:
  kicli-code-assist:
    root: /home/flow/dev_flow/kicli-code-assist
    services:
      - id: kicli-backend
        name: Backend API
        # ...
        
  ki-knowledge:
    root: /home/flow/dev_flow/ki-knowledge
    services:
      - id: ki-django
        name: Django API
        # ...

  ki-core:
    root: /home/flow/dev_flow/ki-core
    services:
      - id: ki-lsp
        name: Language Server
        # ...

  stackctl:
    root: /home/flow/dev_flow/stackctl
    services:
      - id: stackctl-api
        name: HTTP API
        # ...
```

**Registry file:** `~/.kicli/services.json` (flat list, keyed by project + service_id)

```json
{
  "kicli-code-assist/kicli-backend": { ... },
  "kicli-code-assist/kicli-frontend": { ... },
  "ki-knowledge/ki-django": { ... },
  "ki-core/ki-lsp": { ... },
  "stackctl/stackctl-api": { ... }
}
```

### CLI Integration

```bash
# Single project (default to current project)
kicli-assist server:list                    # List services in kicli-code-assist

# Explicit project
kicli-assist server:list --project ki-knowledge
kicli-assist server:start ki-django --project ki-knowledge

# All projects
kicli-assist server:list --all
kicli-assist server:stop --all              # Dangerous; requires --confirm
```

---

## Answer to Question 4: Integration Points

**SELECTED: Layered Integration (Config System + Logging + Agent State)**

### 4.1 Integration with ki_core.ConfigManager

**Current state:**
- `ki_core.ConfigManager` loads `ki.yaml`
- Already used for LLM config, diff settings, etc.

**Integration:**
```python
# Option 1: Add "services" section to ki.yaml (shared with all projects)
# Option 2: Separate ~/.kicli/projects.yaml (not shared)
# CHOSEN: Option 2 (separate file, cleaner separation)

# But we CAN use ki_core's validation infrastructure:
from ki_core.config import ConfigManager

# Load projects.yaml through ki_core's validator
projects_schema = {
    "type": "object",
    "properties": {
        "projects": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "root": {"type": "string"},
                    "services": {
                        "type": "array",
                        "items": { /* service schema */ }
                    }
                }
            }
        }
    }
}

projects_config = ConfigManager.load(
    "~/.kicli/projects.yaml",
    schema=projects_schema
)
```

**Benefit:** Reuse ki_core's YAML parsing, validation, and error handling.

### 4.2 Integration with Logging System

**Current logging:**
```
/home/flow/dev_flow/kicli-code-assist/log/
  ├─ kicli.log           (application logs)
  ├─ kicli-llm.log       (LLM calls)
  └─ kicli-metrics.jsonl (metrics)
```

**Server registry logging:**
```
~/.kicli/logs/
  ├─ kicli-backend.stdout.log      (service stdout)
  ├─ kicli-backend.stderr.log      (service stderr)
  ├─ kicli-frontend.stdout.log
  ├─ kicli-frontend.stderr.log
  └─ kicli-frontend.access.log     (HTTP access log for web services)
```

**Aggregation layer:**
```python
class LogAggregator:
    """Combine logs from multiple sources."""
    
    def get_service_logs(self, service_id, lines=100):
        """Fetch last N lines from service's stdout + stderr."""
        stdout = self._tail_file(f"~/.kicli/logs/{service_id}.stdout.log", lines)
        stderr = self._tail_file(f"~/.kicli/logs/{service_id}.stderr.log", lines)
        
        # Merge, sort by timestamp
        return self._merge_logs(stdout, stderr)
    
    def stream_logs(self, service_id, follow=True):
        """Stream service logs in real-time."""
        # Watch both stdout and stderr files
        # Return generator yielding new lines as they arrive
```

**Integration with ki_core logging:**
```python
# Each service uses ki_core's logger for structured logging
logger = logging.getLogger(f"kicli.services.{service_id}")
logger.info(f"Service started with PID {pid}")

# Logs automatically routed to:
# 1. ~/.kicli/logs/kicli-backend.log
# 2. Project's log directory (if configured)
# 3. Console (if verbose mode)
```

### 4.3 Integration with Agent State (Intervention System)

**Current agent architecture:**
```
kicli_code_assist/agent/
  ├─ code_implementation.py
  ├─ implementation_state.py
  └─ intervention.py         # CLI supervisor + WebUI intervention
```

**Connection to server management:**

When an agent is running:
```python
# In CodeImplementationAgent:
self.server_registry = ServerRegistry()

# When starting work:
backend_service = self.server_registry.get_service("kicli-backend")
if backend_service.status != "running":
    logger.warning(f"Backend not running; starting it...")
    self.server_registry.start_service("kicli-backend")

# Before making API calls:
health = self.server_registry.check_health("kicli-backend")
if not health:
    raise RuntimeError("Backend is unhealthy; cannot proceed")
```

**Intervention queue + server state:**
```python
# When supervisor intervenes:
intervention_action = self.intervention_queue.get()  # e.g., "pause_agent"

if intervention_action == "pause_agent":
    # Also capture current server state for recovery
    server_snapshot = self.server_registry.get_all_services()
    agent_state.save_checkpoint({
        "servers": server_snapshot,
        "agent_state": self.state,
        "timestamp": now()
    })
```

---

## Answer to Question 5: Safety & Accountability

**SELECTED: Multi-Layer Protection + Audit Trail**

### 5.1 User Confirmation (Interactive Mode)

```bash
$ kicli-assist server:stop kicli-backend

⚠️  STOP SERVICE
Service:     kicli-backend
Project:     kicli-code-assist
Type:        backend
Dependencies: kicli-frontend (will be notified)
PID:         12345
Uptime:      2h 14m

✓ Continue? [y/N]: _
```

**Code:**
```python
def stop_service_interactive(service_id):
    service = registry.get_service(service_id)
    dependent_services = registry.get_dependents(service_id)
    
    # Show confirmation
    print(f"\n⚠️  STOP SERVICE")
    print(f"Service:     {service.name}")
    print(f"Project:     {service.project}")
    print(f"PID:         {service.pid}")
    print(f"Uptime:      {format_uptime(service.started_at)}")
    
    if dependent_services:
        print(f"Dependents:  {', '.join(d.name for d in dependent_services)}")
    
    response = input("\n✓ Continue? [y/N]: ")
    
    if response.lower() != 'y':
        logger.info("User cancelled server stop")
        return False
    
    # Proceed with stop
    return stop_service_force(service_id)
```

### 5.2 Audit Trail (Comprehensive Logging)

**Audit log file:** `~/.kicli/audit.jsonl` (append-only)

Each action logged with:
- Timestamp (ISO 8601)
- Action (start, stop, restart, health_check_failed, dependency_alert)
- Service ID
- User/source (flow, supervisor, webhook)
- Status (success, failure, cancelled)
- Message (reason for failure)
- Affected dependencies

```jsonl
{"timestamp": "2026-10-28T03:16:00Z", "action": "start", "service": "kicli-backend", "user": "flow", "status": "success"}
{"timestamp": "2026-10-28T03:16:05Z", "action": "start", "service": "kicli-frontend", "user": "flow", "status": "success"}
{"timestamp": "2026-10-28T03:20:00Z", "action": "health_check_failed", "service": "kicli-backend", "user": "supervisor", "status": "failure", "message": "No response from http://localhost:8000/health"}
{"timestamp": "2026-10-28T03:20:01Z", "action": "dependency_alert", "service": "kicli-frontend", "user": "supervisor", "status": "warning", "message": "Dependency kicli-backend is unhealthy"}
{"timestamp": "2026-10-28T03:21:00Z", "action": "stop", "service": "kicli-backend", "user": "flow", "status": "success"}
```

**Query audit trail:**
```bash
kicli-assist audit:log --since "2026-10-28 03:00:00"
kicli-assist audit:log --service kicli-backend --action "stop"
kicli-assist audit:log --user supervisor
```

### 5.3 Safety Flags

```bash
# Dangerous operations require explicit flags

# Kill all backends (requires --force)
kicli-assist server:stop --all
Error: Must specify --force to stop multiple services
kicli-assist server:stop --all --force
⚠️  Will stop: kicli-backend, ki-django, stackctl-api (3 services)
✓ Continue? [y/N]: 

# Force kill (SIGKILL instead of SIGTERM) requires --force
kicli-assist server:stop kicli-backend --force
⚠️  Force killing may leave state inconsistent. Use graceful stop first.
✓ Continue? [y/N]: 

# Clean up orphaned processes (auto-kill without prompt)
kicli-assist server:cleanup --dry-run     # Show what would be killed
kicli-assist server:cleanup --force       # Actually kill
```

### 5.4 Alerting on Dependents

```python
def stop_service(service_id):
    service = registry.get_service(service_id)
    dependents = registry.get_dependents(service_id)
    
    # Notify dependents
    for dependent in dependents:
        if dependent.status == "running":
            logger.warning(
                f"Stopping {service.name}; dependent {dependent.name} "
                f"(PID {dependent.pid}) may fail"
            )
            
            # Update dependent's health status
            registry.update_health(dependent.id, "warning",
                f"Dependency {service.name} is stopping")
    
    # Stop the service
    os.kill(service.pid, signal.SIGTERM)
    
    # Log action
    registry.audit_log(
        action="stop",
        service_id=service_id,
        user=get_current_user(),
        message=f"Stopped by user; {len(dependents)} dependents affected"
    )
```

---

## Summary Table: Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Hybrid (A+B) | Best of both: state persistence + zero overhead fallback |
| State Storage | JSON file + OS queries | Audit trail + real-time accuracy |
| Concurrency | File-based locking | Simple, cross-platform, no background threads |
| Scope | Multi-project | Future-proof; minimal added complexity |
| Config Integration | Separate file (projects.yaml) | Clean separation; can still use ki_core validators |
| Safety | Confirmations + Audit trail | Accountability + protection against accidents |
| Logging | Aggregated per-service logs | Easy debugging; integrates with ki_core's logging |
| Dependencies | Explicit in registry | Clear interface; prevents hidden coupling |

---

## What Gets Built First (Priority Order)

1. **Core Registry + CLI** (Week 1)
   - Solve the immediate pain: orphaned processes
   - Commands: `list`, `status`, `start`, `stop`, `logs`

2. **Optional Supervisor** (Week 2)
   - Background health checks
   - Crash recovery

3. **WebUI** (Week 2-3)
   - Real-time visibility
   - Dashboard

4. **Multi-project** (Week 3)
   - Extend to ki-knowledge, ki-core, stackctl

5. **Polish** (Week 4)
   - Audit trail, confirmations, documentation

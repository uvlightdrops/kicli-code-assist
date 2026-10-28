---
# Option C Integration Guide: stackctl + server_management
Status: In Progress (Phase 5.5.2)
Created: 2026-10-28
---

## Overview: Clean Layer Separation

```
┌─────────────────────────────────────────────────────┐
│ Layer 2: Full Stack Deployment                      │
│ Command: stackctl -t local start                    │
│ Config:  stack.yaml (root project)                  │
│ Features: Git orchestration, Build, All services   │
│ User:     Developer (local dev), DevOps (staging)   │
└─────────────────────────────────────────────────────┘
                        ↑ respects depends_on
                        ↑ waits for health_checks
                        ↑ aggregates logs
┌─────────────────────────────────────────────────────┐
│ Layer 1: Single Service Supervision                 │
│ Command: kicli-assist server start --service api    │
│ Config:  ki.yaml (app runtime config)               │
│ Features: Manual control, Debug, Live-reload        │
│ User:     Developer (debugging)                     │
└─────────────────────────────────────────────────────┘
                        ↓ reads log files
                        ↓ manages PID tracking
                        ↓ graceful shutdown
```

---

## Layer 1: server_management (Dev-Time Process Supervisor)

### When to Use
- **Debugging a single service** → Use `kicli-assist server`
- **Live code changes + auto-reload** → Use `kicli-assist server --watch` (future)
- **Inspecting process state** → Use `kicli-assist server status`
- **Manual control** → Use `kicli-assist server start/stop/restart`

### Configuration
Located in `ki.yaml` (application runtime config):

```yaml
services:
  kicli-backend:
    command: ["python", "-m", "uvicorn", "app:app"]
    cwd: /home/flow/dev_flow/kicli-code-assist
    port: 8000
    pidfile: ~/.kicli/services/kicli-backend.pid
    
  frontend:
    command: ["npm", "start"]
    cwd: /home/flow/dev_flow/kicli-code-assist/web
    port: 3000
    pidfile: ~/.kicli/services/frontend.pid
```

### Commands

```bash
# Show all running services
kicli-assist server status

# Start a single service (for debugging)
kicli-assist server start --service kicli-backend

# View logs in real-time (future: with --follow)
kicli-assist server logs --service kicli-backend

# Stop a service
kicli-assist server stop --service kicli-backend

# Restart a service
kicli-assist server restart --service kicli-backend
```

### Service Registry
Metadata stored in `~/.kicli/services.json`:
- PID
- Start time
- Port
- Command line

Used for:
- Detecting orphaned processes
- Health status tracking
- Log file location

---

## Layer 2: stackctl (Full-Stack Orchestration)

### When to Use
- **Start entire stack locally** → `stackctl -t local start`
- **Orchestrate multiple repos** → `stackctl clone`, `stackctl pull`, `stackctl checkout`
- **Deploy to staging** → `stackctl -t minikube start`
- **Deploy to production** → `stackctl -t k8s start`
- **View aggregated logs** → `stackctl logs api worker db` (future)

### Configuration
Located in `stack.yaml` or via config_loader in `pyproject.toml`:

```yaml
stack:
  name: kicli
  target: local
  services:
    db:
      kind: process
      command: ["python", "-m", "sqlite3", "app.db"]
      port: 5432
      health_path: /health          # NEW: health check endpoint
      health_timeout: 5              # NEW: seconds to wait for response
      health_retries: 3              # NEW: retry attempts
      health_interval: 0.5           # NEW: seconds between retries
      
    api:
      kind: process
      command: ["python", "-m", "uvicorn", "app:app", "--host", "{host}", "--port", "{port}"]
      port: 8000
      host: 0.0.0.0
      depends_on: [db]              # NEW: wait for db to be healthy first
      health_path: /docs
      health_timeout: 5
      
    worker:
      kind: process
      command: ["python", "worker.py"]
      port: 0                        # No port = no health check
      depends_on: [db]              # NEW: wait for db before starting
      
    frontend:
      kind: process
      command: ["npm", "start"]
      port: 3000
      host: 0.0.0.0
      depends_on: [api]             # NEW: api must be healthy first
      health_path: /                # Check root path

  k8s:
    namespace: kicli
    images: {app: {dockerfile: deploy/docker/Dockerfile}}
```

### Commands

```bash
# Git orchestration
stackctl clone                     # Clone missing sibling repos
stackctl checkout devel            # Checkout all repos to branch
stackctl pull                      # Update all repos (ff-only)
stackctl push                      # Push clean repos
stackctl repo-status               # Show git status of all repos

# Stack deployment
stackctl spec                      # Show resolved config
stackctl status                    # Show running services + health status
stackctl start [service ...]       # Start (respects depends_on, waits for health)
stackctl stop [service ...]        # Stop (reverse order)
stackctl restart [service ...]     # Restart (graceful)
stackctl logs [-f] [service ...]   # Stream aggregated logs (NEW, future)

# Minikube deployment
stackctl -t minikube start         # Build images, load, deploy with Helm
stackctl -t minikube status        # Show pods, services, URLs
stackctl -t minikube logs -f api   # Stream pod logs

# Kubernetes deployment
stackctl -t k8s start              # Push images to registry, deploy
stackctl -t k8s status             # Show deployment status
```

### Special Features

#### Service Dependencies (NEW)
```yaml
services:
  api:
    depends_on: [db]              # Wait for db to be healthy
  frontend:
    depends_on: [api, cache]      # Wait for both
```

- **Start order:** Respects `depends_on` (topological sort)
- **Health waiting:** After starting dependency, waits for `health_path` to respond
- **Stop order:** Reverse of start order (dependents stop first)
- **Validation:** Circular dependencies are detected and rejected

#### Health Checks (NEW)
```yaml
services:
  api:
    health_path: /health           # HTTP endpoint to check
    health_timeout: 5              # Max seconds to wait for response
    health_retries: 3              # Retry attempts before fail
    health_interval: 0.5           # Seconds between retries
```

- **Local target:** Uses HTTP GET on `http://{probe_host}:{port}{health_path}`
- **K8s target:** Translated to probes in Kubernetes deployment
- **Timeout behavior:** Waits for health before starting dependents

#### Unified Log Stream (NEW, future)
```bash
stackctl logs -f api worker       # Tail logs from api and worker
# Output:
# 2026-10-28 12:30:45 [api] GET /health 200
# 2026-10-28 12:30:46 [worker] Task queue initialized
# 2026-10-28 12:30:47 [api] POST /jobs 201
```

Features:
- Aggregates logs from all specified services
- Timestamp + service name prefix per line
- Color per service (stable colors)
- Real-time tail with `--follow/-f`
- Shows service exit events

---

## Workflow Examples

### Developer Workflow: Local Development

```bash
# Day 1: Clone project and dependencies
git clone https://github.com/org/kicli-code-assist.git
cd kicli-code-assist
stackctl clone                   # Clone ki-core, yaml-cfg, etc.
stackctl install                 # Install all as editable packages

# Start full stack (all dependencies respected)
stackctl -t local start
# Output:
#   Starting db...
#   db is healthy ✓
#   Starting api (depends on: db)...
#   api is healthy ✓
#   Starting frontend (depends on: api)...
#   frontend is healthy ✓

# View full logs
stackctl logs -f

# During development: debug single service
^C                               # Stop stackctl logs
kicli-assist server logs --service api --follow
# Just looking at api logs, not the whole stack
```

### Developer Workflow: Code Change + Testing

```bash
# Code change in api/app.py
# Quick restart just the api service
kicli-assist server restart --service api

# Or with auto-reload (future)
kicli-assist server start --watch --service api
# Watches app.py, auto-restarts on changes

# View logs
kicli-assist server logs --service api -f
```

### DevOps Workflow: Staging Deployment

```bash
# Prepare for staging
stackctl checkout staging
stackctl pull                   # Update all repos

# Deploy to minikube
stackctl -t minikube start
# Output:
#   Building images...
#   Pushing to minikube...
#   Deploying with Helm...
#   Waiting for readiness...
#   Services healthy ✓

# Check status
stackctl -t minikube status
#   Pod api-1234-abc [Running] 
#   Pod db-5678-def [Running]
#   Service api:     http://api.minikube.test:8000
#   Service frontend: http://frontend.minikube.test:3000

# Tail logs
stackctl logs -f
```

---

## Migration from Old System

### Before (No Option C):
```bash
# Confusing: which tool? How do dependencies work?
kicli-assist server start --service api
stackctl -t local start api
# Both do the same thing but different configurations!
```

### After (Option C):
```bash
# Clear responsibility:
kicli-assist server start --service api      # Manual dev control (ki.yaml)
stackctl -t local start                      # Orchestrated start with deps (stack.yaml)
stackctl -t minikube start                   # Production-like staging
```

---

## Configuration Best Practices

### Rule 1: ki.yaml is Runtime Config
```yaml
# ✅ CORRECT: Application-specific, runtime details
services:
  kicli-backend:
    command: ["python", "-m", "uvicorn"]
    cwd: /path/to/backend
    port: 8000
    pidfile: ~/.kicli/services/kicli-backend.pid
```

```yaml
# ❌ WRONG: Deployment orchestration (belongs in stack.yaml)
services:
  kicli-backend:
    depends_on: [db]          # NOT here!
    health_path: /health      # NOT here!
```

### Rule 2: stack.yaml is Deployment Spec
```yaml
# ✅ CORRECT: Orchestration, dependencies, health
stack:
  services:
    api:
      kind: process
      command: ["python", "app.py"]
      depends_on: [db]        # YES!
      health_path: /health    # YES!
```

```yaml
# ❌ WRONG: Runtime application config (belongs in ki.yaml)
stack:
  services:
    api:
      pidfile: ~/.kicli/services/api.pid  # NOT here!
      cwd: /app                           # Set via command line
```

### Rule 3: Don't Duplicate Service Definitions
```yaml
# ❌ WRONG: Same service in both files
# ki.yaml
services:
  api:
    command: ["python", "app.py"]
    port: 8000

# stack.yaml
stack:
  services:
    api:
      command: ["python", "app.py"]
      port: 8000

# ✅ CORRECT: Use mapping or shared template
# Future enhancement: stack.yaml references ki.yaml services?
```

---

## Troubleshooting

### Q: I ran `stackctl start` but service didn't start?
```bash
# Check: Did dependencies start successfully?
stackctl status

# Check: Health check failing?
stackctl logs api      # See actual error
```

### Q: I ran `kicli-assist server start` but it conflicts with stackctl?
```bash
# Both tools can manage same process, but:
# - stackctl: orchestrated, respects depends_on
# - server_management: manual, independent
# Use one or the other in a session, not both!
```

### Q: How do I debug a single service while full stack runs?
```bash
# Start full stack
stackctl -t local start

# In another terminal: debug single service
kicli-assist server logs --service api --follow
# Just watching api logs, not stopping/starting it
```

### Q: Can I use stack.yaml for production and ki.yaml for dev?
```bash
# Conceptually yes, but:
# - stack.yaml: designed for minikube/k8s (kind: compose, k8s overlays)
# - ki.yaml: designed for local app config (paths, secrets)
# They serve different purposes, don't force them
```

---

## Future Enhancements

1. **service_group in stack.yaml:** `start @backend` starts all services with group=backend
2. **Automatic ki.yaml ↔ stack.yaml sync:** Derive stack from ki config
3. **Environment secrets in stack.yaml:** Support `$VAR` expansion from .env files
4. **service.restart_policy:** auto-restart failed services
5. **Metrics + health:** Track uptime, error rates, slow endpoints
6. **UI Dashboard:** Visual service topology with health status
7. **server_management watch mode:** `kicli-assist server start --watch` for auto-reload

---

## See Also
- `/home/flow/dev_doc/MULTI_REPO_ORCHESTRATION_STUDY.md` - Architecture overview
- `/home/flow/dev_flow/stackctl/README.md` - stackctl detailed docs
- `/home/flow/dev_flow/kicli-code-assist/ki.yaml` - Current config example

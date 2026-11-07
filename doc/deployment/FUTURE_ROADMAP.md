---
title: Development Stack Future Roadmap
project: kicli-code-assist
scope: deployment
purpose: Roadmap and planning for development stack stabilization, deployment automation, and developer experience improvements
created: 2026-11-02T04:17
updated: 2026-11-07T19
update_reason: Add missing title, standardize scope and timestamps
status: active
semantic_blocks: [current-state, phase-1-immediate-fixes, phase-2-stabilization, phase-3-automation, monitoring-dashboard]
---

# Development Stack: Future Planning & Roadmap

## Current State (2026-11-02 04:15 UTC)

### What Works ✅
- Flask API starts correctly on :8000
- ConfigManager loads ki.yaml and merges stages (KI_STAGE=development works)
- CORS headers derived dynamically from config
- API returns correct message pointing to frontend

### What's Broken ❌
- Vite dev server: config evaluation order prevents env var passing
- Port/host configuration not reaching Vite correctly
- Process verification shows "running" but services actually broken
- No automated startup validation

### Knowledge Created This Session 📚
- `DEVELOPMENT_STACK_TROUBLESHOOTING.md` (detailed troubleshooting)
- `ANTI_PATTERNS_FAILED_APPROACHES.md` (17.5KB of lessons learned)
- Updated `.env.local` (startup env vars)
- Updated `vite.config.ts` (env var reading logic)
- Updated `stack.yaml` (frontend service config)

---

## Phase 1: Immediate Fixes (Next 2-3 hours)

### 1.1 Fix Vite Configuration (CRITICAL)

**Problem**: vite.config.ts can't read `VITE_*` env vars due to startup order.

**Solution**: Use CLI flags approach (most reliable)

```yaml
# config/defaults/stack.yaml - frontend section
frontend:
  command: [
    "{root}/web/frontend/node_modules/.bin/vite",
    "--host", "127.0.0.1",
    "--port", "5173"
  ]
  env:
    VITE_API_URL: "http://127.0.0.1:8000"
```

**Alternative for Stage Overrides**: Create wrapper script

```bash
# web/frontend/dev.sh
#!/bin/bash
set -e
cd "$(dirname "$0")"
exec ./node_modules/.bin/vite \
  --host "${VITE_HOST:-127.0.0.1}" \
  --port "${VITE_PORT:-5173}"
```

**Update stack.yaml**:
```yaml
frontend:
  command: ["{root}/web/frontend/dev.sh"]
  env:
    VITE_HOST: "127.0.0.1"
    VITE_PORT: "5173"
    VITE_API_URL: "http://127.0.0.1:8000"
```

**Test**: After fix, Vite should start on correct port

```bash
$ export KI_STAGE=development
$ source .env.local
$ .venv/bin/python -m stackctl -t local start
$ curl -I http://127.0.0.1:5173/
# Should return: HTTP/1.1 200 OK (not 404)
```

---

### 1.2 Create Development Startup Checklist

**File**: `docs/DEVELOPMENT_STARTUP_CHECKLIST.md`

```markdown
# Development Stack Startup Checklist

## Pre-Flight (Do Every Time)
- [ ] cd /home/flow/dev_flow/kicli-code-assist
- [ ] export KI_STAGE=development (or source .env.local)
- [ ] .venv/bin/python -m stackctl -t local stop (clean old processes)
- [ ] sleep 2

## Startup
- [ ] .venv/bin/python -m stackctl -t local start
- [ ] Wait 6-8 seconds for services to boot

## Verification (Do Every Time)
- [ ] curl http://127.0.0.1:8000/api/health → Should return 200 JSON
- [ ] curl http://127.0.0.1:8000/ → Should show message with :5173
- [ ] curl -I http://127.0.0.1:5173/ → Should return 200 OK
- [ ] Check logs: tail -f var/log/api.log var/log/frontend.log

## Browser Test
- [ ] Open http://127.0.0.1:5173 in browser
- [ ] Should load React app
- [ ] Check browser console for errors
- [ ] Test API call: check Network tab

## If Anything Fails
- See: doc/deployment/DEVELOPMENT_STACK_TROUBLESHOOTING.md
- See: doc/deployment/ANTI_PATTERNS_FAILED_APPROACHES.md
```

---

### 1.3 Create Validation Script

**File**: `scripts/validate_dev_setup.sh`

```bash
#!/bin/bash
set -e

echo "=== Development Stack Validation ==="
echo

# Check KI_STAGE
if [ -z "$KI_STAGE" ]; then
    echo "❌ KI_STAGE not set. Run: export KI_STAGE=development"
    exit 1
fi
echo "✅ KI_STAGE=$KI_STAGE"

# Check .env.local exists
if [ ! -f .env.local ]; then
    echo "⚠️  .env.local not found (optional but recommended)"
else
    echo "✅ .env.local exists"
fi

# Test API health
echo -n "Testing API health... "
if curl -s http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
    echo "✅"
else
    echo "❌ API not responding on :8000"
fi

# Test API root message
echo -n "Testing API message... "
if curl -s http://127.0.0.1:8000/ | grep -q "5173"; then
    echo "✅ (points to :5173)"
else
    echo "❌ (doesn't point to :5173)"
fi

# Test Vite
echo -n "Testing Vite... "
if curl -I http://127.0.0.1:5173/ 2>/dev/null | grep -q "200"; then
    echo "✅"
else
    echo "❌ Vite not responding on :5173"
fi

# Show config merge
echo
echo "=== Merged Config (stack.yaml) ==="
.venv/bin/python -m stackctl -t local spec | grep -A 20 "services:" | head -30

echo
echo "=== All Checks Complete ==="
```

**Make executable and add to docs**: 
```bash
chmod +x scripts/validate_dev_setup.sh
# Usage: ./scripts/validate_dev_setup.sh
```

---

### 1.4 Document Config Loading Order

**File**: `docs/CONFIG_LOADING_ORDER.md`

Sequence diagrams showing:
1. When KI_STAGE is read (ConfigManager import time)
2. When stack.yaml is merged
3. When Vite startup sequence happens
4. When Flask config is loaded
5. When .env.local is processed (if at all)

---

## Phase 2: Process Verification & Monitoring (3-4 hours)

### 2.1 Enhance stackctl Health Checks

**Problem**: Health checks report "running" but service is broken

**Solution**: stackctl should validate actual HTTP response, not just connection

- Make health check response validation stricter
- For frontend: expect `<!DOCTYPE html>` in response, not just 200 OK
- For API: expect valid JSON response to health endpoint
- Add detailed error logging when health check fails

---

### 2.2 Add Startup Validation to stackctl

After all services report "running", stackctl should:

```python
def validate_all_services():
    for service in stack.services:
        health = check_health(service)
        if not health['responsive']:
            logger.error(f"{service.name} started but not responding")
            return False
    return True
```

---

### 2.3 Create Monitor Script

**File**: `scripts/monitor_dev_stack.sh`

```bash
#!/bin/bash
# Continuous monitoring of dev stack
watch -n 2 'echo "=== API ===" && curl -s http://127.0.0.1:8000/api/health | jq . && echo "=== Vite ===" && curl -I http://127.0.0.1:5173/ 2>&1 | head -3'
```

---

## Phase 3: Documentation Consolidation (2-3 hours)

### 3.1 Complete Consolidation Phase 2

From `doc/deployment/CONSOLIDATION_STRATEGY.md`:

- Eliminate duplication of:
  - Stage merge semantics explanation (currently in: README, STACKCTL_ARCHITECTURE, deployment docs)
  - KI_STAGE documentation (scattered across 4+ files)
  - Service port documentation (frontend in multiple places)

- Create canonical versions in:
  - `dev_doc/DEPLOYMENT_STANDARDS.md` (already created, needs expansion)
  - Link from project-local docs

### 3.2 Add YAML Headers to All Remaining Docs

Missing headers in:
- `doc/deployment/CURRENT_STATUS.md` ✅ (done)
- `doc/deployment/STACKCTL_STATUS.md` ✅ (done)
- Any new troubleshooting docs created this session

### 3.3 Create Cross-Reference Index

**File**: `doc/deployment/INDEX.md`

```markdown
# Deployment Documentation Index

## By Topic
- **Getting Started**: DEVELOPMENT_STARTUP_CHECKLIST.md
- **Troubleshooting**: DEVELOPMENT_STACK_TROUBLESHOOTING.md
- **Architecture**: STACKCTL_ARCHITECTURE.md, STACK_YAML_VARIANTS.md
- **Configuration**: dev_doc/DEPLOYMENT_STANDARDS.md (canonical)
- **Failed Approaches**: ANTI_PATTERNS_FAILED_APPROACHES.md
- **Consolidation Plan**: CONSOLIDATION_STRATEGY.md

## By Audience
- **New Developers**: Start with DEVELOPMENT_STARTUP_CHECKLIST.md
- **DevOps**: See stackctl/doc/README.md + DEPLOYMENT_STANDARDS.md
- **Debugging**: See ANTI_PATTERNS_FAILED_APPROACHES.md first
- **Design Changes**: See CONSOLIDATION_STRATEGY.md for improvement areas
```

---

## Phase 4: Automation & CI/CD Integration (4-5 hours)

### 4.1 GitHub Actions Workflow for Dev Stack Validation

**File**: `.github/workflows/dev-stack-validation.yml`

```yaml
name: Dev Stack Validation
on: [pull_request, push]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Dependencies
        run: |
          python -m pip install -e .
          cd web/frontend && npm ci
      
      - name: Validate Config Schema
        run: python -m kicli_code_assist.validation.schema_check
      
      - name: Check for Hardcoded Ports
        run: python scripts/check_hardcoded_ports.py
      
      - name: Lint Deployment Docs
        run: python scripts/lint_deployment_docs.py
```

### 4.2 Pre-Commit Hook for Config Validation

**File**: `.git/hooks/pre-commit`

Before commit:
- Validate stack.yaml syntax
- Check for absolute paths in dependencies (already exists)
- Validate YAML headers on modified docs
- Check for hardcoded localhost/3000

---

## Phase 5: Knowledge Codification (2 hours)

### 5.1 Create Architecture Decision Records (ADRs)

**File**: `doc/deployment/adr/001-vite-cli-flags.md`

```markdown
# ADR-001: Use Vite CLI Flags for Port Configuration

## Problem
Vite config evaluation happens before env var loading, making `VITE_*` env vars unreliable.

## Decision
Use Vite CLI flags `--host` and `--port` directly in stack.yaml command array.

## Rationale
- CLI flags bypass config file, guaranteed to work
- Single source of truth (stack.yaml)
- Matches how other tools work

## Consequences
- Ports hardcoded in YAML (acceptable: only one place)
- Stage-specific variations require wrapper script
- Document pattern for future tools with similar issues

## Related
- ANTI_PATTERNS_FAILED_APPROACHES.md (why env vars didn't work)
- DEVELOPMENT_STACK_TROUBLESHOOTING.md (debugging guide)
```

### 5.2 Create Best Practices Guide

**File**: `doc/deployment/BEST_PRACTICES.md`

```markdown
# Development Stack Best Practices

## 1. Environment Variables
- Always export stage var BEFORE Python imports: `export KI_STAGE=development`
- Use .env.local for convenience, source it before every session
- Don't rely on env vars reaching nested config files (timing issues)

## 2. Configuration
- Define each setting in ONE place (stack.yaml)
- Use CLI flags to pass to tools (if tool supports)
- Use wrapper scripts if tool can't read flags
- Document where each tool reads its config

## 3. Port Management
- Development: API :8000, Frontend :5173 (in stack.yaml)
- Production: Single port :8000 (built static frontend)
- Never hardcode in config files AND code simultaneously
- Always verify with: curl -I http://localhost:PORT/

## 4. Debugging
- Always check logs FIRST: tail -f var/log/*.log
- Use validate_dev_setup.sh before asking for help
- Read ANTI_PATTERNS_FAILED_APPROACHES.md (likely your issue is there)
- Check KI_STAGE is set: echo $KI_STAGE

## 5. Documentation
- Every config change needs corresponding doc update
- Add YAML headers with timestamps and status
- Link cross-references (docs point to each other)
- Keep anti-patterns doc up-to-date with new failures
```

---

## Phase 6: Testing & Validation (2-3 hours)

### 6.1 Integration Tests

**File**: `tests/test_dev_stack_integration.py`

```python
def test_api_health():
    """API responds to health check"""
    response = requests.get('http://127.0.0.1:8000/api/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'

def test_api_root_message():
    """API root message points to correct frontend port"""
    response = requests.get('http://127.0.0.1:8000/')
    assert '5173' in response.text or ':5173' in response.text
    assert 'localhost' not in response.text  # Should use IP not hostname

def test_vite_responds():
    """Vite dev server responds with HTML"""
    response = requests.get('http://127.0.0.1:5173/', allow_redirects=False)
    # 200 OK with HTML, not 404
    assert response.status_code == 200
    assert '<!DOCTYPE' in response.text or '<html' in response.text
```

Run via: `pytest tests/test_dev_stack_integration.py -v`

---

## Phase 7: Automation Scripts (1-2 hours)

### 7.1 One-Command Startup

**File**: `scripts/dev-start.sh`

```bash
#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# Ensure env setup
if [ -z "$KI_STAGE" ]; then
    if [ -f .env.local ]; then
        source .env.local
    else
        export KI_STAGE=development
    fi
fi

echo "Starting development stack (KI_STAGE=$KI_STAGE)..."

# Kill old processes
.venv/bin/python -m stackctl -t local stop 2>/dev/null || true
sleep 2

# Start fresh
.venv/bin/python -m stackctl -t local start

# Wait for startup
sleep 6

# Validate
if ./scripts/validate_dev_setup.sh; then
    echo
    echo "✅ Development stack ready!"
    echo "   API: http://127.0.0.1:8000/"
    echo "   Frontend: http://127.0.0.1:5173/"
    echo "   Logs: tail -f var/log/*.log"
else
    echo
    echo "❌ Validation failed. Check logs and troubleshooting docs."
    exit 1
fi
```

Usage: `./scripts/dev-start.sh`

---

## Implementation Order & Ownership

| Phase | Task | Effort | Priority | Blocker? |
|-------|------|--------|----------|----------|
| 1.1 | Fix Vite via CLI flags | 30 min | CRITICAL | ✅ YES |
| 1.2 | Create startup checklist | 20 min | HIGH | ❌ No |
| 1.3 | Create validation script | 30 min | HIGH | ❌ No |
| 1.4 | Document config loading | 40 min | MEDIUM | ❌ No |
| 2.1 | Enhance health checks | 60 min | MEDIUM | ❌ No |
| 2.2 | Add startup validation | 40 min | MEDIUM | ❌ No |
| 2.3 | Create monitor script | 20 min | LOW | ❌ No |
| 3.1 | Complete consolidation P2 | 90 min | HIGH | ❌ No |
| 3.2 | Add YAML headers | 30 min | MEDIUM | ❌ No |
| 3.3 | Create doc index | 20 min | LOW | ❌ No |
| 4.1 | GitHub Actions workflow | 60 min | MEDIUM | ❌ No |
| 4.2 | Pre-commit hooks | 40 min | MEDIUM | ❌ No |
| 5.1 | Create ADRs | 30 min | LOW | ❌ No |
| 5.2 | Create best practices | 40 min | MEDIUM | ❌ No |
| 6.1 | Integration tests | 60 min | MEDIUM | ❌ No |
| 7.1 | One-command startup | 30 min | LOW | ❌ No |

---

## Success Criteria

### Phase 1 Complete
- ✅ Vite starts on :5173 and responds with HTML to /
- ✅ API on :8000 returns correct frontend URL
- ✅ Startup checklist document exists and is accurate
- ✅ Validation script runs successfully
- ✅ All logs show no errors

### Phase 2 Complete
- ✅ stackctl health checks catch broken services
- ✅ Validation script catches common issues automatically
- ✅ Monitor script shows real-time service status

### Phase 3 Complete
- ✅ No duplicated documentation
- ✅ All docs have YAML headers
- ✅ Cross-references are accurate
- ✅ New developers can find info quickly

### Phase 4 Complete
- ✅ GitHub Actions catches config issues in PRs
- ✅ Pre-commit hook prevents broken commits

### All Phases Complete
- ✅ A new developer can: `source .env.local && ./scripts/dev-start.sh`
- ✅ If anything breaks, `./scripts/validate_dev_setup.sh` pinpoints it
- ✅ Docs are single-source-of-truth, not scattered
- ✅ No "magic" configuration: all settings traceable to one file
- ✅ Anti-patterns doc prevents repeating same mistakes

---

## Future Considerations

### Multi-Host Deployment
- Currently targets localhost only
- Future: Support remote hosts (staging, prod)
- stackctl needs expansion for SSH/container targets

### Docker Integration
- Currently: native process spawning
- Future: Docker containers per service
- Affects: port mapping, volume mounts, health checks

### Kubernetes
- Beyond stackctl scope for now
- Helm charts could consume stack.yaml
- Future: Kustomize or ArgoCD integration

### Observability
- Currently: log files only
- Future: Centralized logging (ELK, Grafana)
- Future: Distributed tracing (Jaeger)

---

**Document Version**: 1.0  
**Last Updated**: 2026-11-02 04:17:00 UTC  
**Status**: Active Roadmap  
**Next Review**: After Phase 1 completion
# StackCtl Implementation Guide

## Overview

StackCtl is the orchestration tool for kicli-code-assist. It manages service startup (API, frontend) across different environments (dev/prod/minimal).

**Design Pattern**: Follows ki-knowledge architecture with stage-based configuration.

## Configuration Structure

```
config/
├── defaults/
│   └── stack.yaml           # Base stack definition (dev mode: API + frontend)
├── stages/
│   ├── .active_stage        # Marker file (contains active stage name)
│   ├── development.yaml     # Dev stage (pure comments, inherits defaults)
│   ├── production.yaml      # Prod stage (unified web service)
│   └── minimal.yaml         # Minimal stage (API only)
└── runtime/
    └── runtime.yaml         # Optional runtime-specific overrides
```

## Stages

### Development (Default)
- **Services**: API (`:8000`) + Frontend (`:5173` vite HMR)
- **Activation**: `export KI_STAGE=development` (or default)
- **Frontend**: Hot module replacement enabled
- **Use Case**: Local development with live reloads

**File**: `config/stages/development.yaml`
```yaml
# Pure comment-based override; inherits all services from defaults
# config/defaults/stack.yaml provides api + frontend services
```

### Production
- **Services**: Single unified `web` service (Flask API + pre-built static frontend)
- **Activation**: `export KI_STAGE=production`
- **Frontend**: Pre-built static files served by Flask
- **Prerequisite**: `npm run build` (builds frontend to `web/static/`)
- **Use Case**: Production deployment, staging environments

**File**: `config/stages/production.yaml`
```yaml
stack:
  name: kicli-assist-prod
  target: local
  services:
    web:
      kind: process
      command: ["{python}", "-m", "kicli_code_assist.web.server"]
      port: 8000
      env:
        KI_STAGE: "production"
      # ... health checks, logging
```

### Minimal
- **Services**: API only (`:8000`)
- **Activation**: `export KI_STAGE=minimal`
- **Frontend**: None
- **Use Case**: CI/CD testing, TUI environments, API-only deployments

**File**: `config/stages/minimal.yaml`
```yaml
stack:
  name: kicli-assist-minimal
  target: local
  services:
    api:
      kind: process
      command: ["{python}", "-m", "kicli_code_assist.web.server"]
      port: 8000
      # ... health checks, logging
```

## Usage

### Start Development (Default)
```bash
export KI_STAGE=development
stackctl -t local start

# Verify
curl http://127.0.0.1:8000/api/health      # API
open http://127.0.0.1:5173                  # Frontend
```

### Start Production
```bash
# Prerequisites
npm run build  # Build frontend to static/

# Start
export KI_STAGE=production
stackctl -t local start

# Verify
curl http://127.0.0.1:8000/api/health  # API + frontend
open http://127.0.0.1:8000              # Frontend (served by Flask)
```

### Start Minimal (API Only)
```bash
export KI_STAGE=minimal
stackctl -t local start

# Verify
curl http://127.0.0.1:8000/api/health
```

### Status Check
```bash
stackctl -t local status
```

### Stop Services
```bash
stackctl -t local stop
```

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `KI_STAGE` | Selects stage config | `development`, `production`, `minimal` |
| `PYTHONUNBUFFERED` | Python logging | `1` |

All variables defined in stage YAMLs are passed to services.

## How StackCtl Loads Config

1. **pyproject.toml** declares:
   ```toml
   [tool.stackctl]
   config_loader = "ki_core:load_config"
   config_key = "stack"
   ```

2. **stackctl** calls `ki_core.load_config('ki.yaml')`

3. **load_config** merges:
   - `config/defaults/stack.yaml` (base)
   - `config/stages/{KI_STAGE}.yaml` (overrides)
   - `config/runtime/runtime.yaml` (if present)

4. **stackctl** reads `result["stack"]` and starts services

## Files & Responsibilities

| File | Purpose | Edit When |
|------|---------|-----------|
| `config/defaults/stack.yaml` | Base service definitions | Adding services, changing dev defaults |
| `config/stages/development.yaml` | Dev-specific overrides | Non-existent; inherits all defaults |
| `config/stages/production.yaml` | Prod-specific overrides | Changing prod stack (e.g., single service) |
| `config/stages/minimal.yaml` | Minimal-specific overrides | Changing test/API-only stack |
| `config/stages/.active_stage` | Marker (documentation only) | Should match default KI_STAGE value |
| `pyproject.toml` | StackCtl config | Adding siblings, changing loader |
| `ki.yaml` | App-level config | Adding knowledge, jira, apps sections |

## Troubleshooting

### Config Loading Fails
```bash
cd /path/to/kicli-code-assist
source .venv/bin/activate
python -c "from ki_core.config import load_config; config = load_config('ki.yaml'); print(config.get('stack', {}).get('services', {}).keys())"
```
- Should output: `dict_keys(['api', 'frontend'])` for dev, or `['web']` for prod

### Service Won't Start
```bash
# Check logs
tail -f log/api.log
tail -f log/api.err.log

# Verify Python path
{python} -m kicli_code_assist.web.server
```

### Frontend Not Building (Production Mode)
```bash
npm run build
ls -la web/static/  # Should exist and contain index.html
```

## Alignment with ki-knowledge

Both projects use identical StackCtl patterns:
- Stages in `config/stages/{name}.yaml`
- Base config in `config/defaults/stack.yaml`
- `KI_STAGE` environment variable for selection
- `config_loader = "ki_core:load_config"` in pyproject.toml

See [ki-knowledge deployment](https://github.com/uvlightdrops/ki-knowledge/tree/main/config/stages) for reference.

## Legacy: Deprecation of deploy/ Folder

**Old approach** (DO NOT USE):
```bash
cd deploy
ln -sf stack-dev.yaml stack.yaml
cd ..
stackctl -t local start
```

**Reasons to avoid**:
- Creates two sources of truth (config/ and deploy/)
- Symlinks are fragile and error-prone
- Not compatible with ki-knowledge pattern
- No environment isolation

**Migration**: Use `export KI_STAGE=...` instead. See files in `deploy/` as reference only.

## Next Steps

- [ ] Test `KI_STAGE=development` with `stackctl -t local start`
- [ ] Test `KI_STAGE=production` (after `npm run build`)
- [ ] Test `KI_STAGE=minimal`
- [ ] Document CI/CD integration (GitHub Actions, etc.)
- [ ] Remove or archive `deploy/stack-*.yaml` files

# Deployment Documentation

Complete guide to deploying and managing kicli-code-assist using StackCtl.

## Quick Start

### Development (with hot reload)
```bash
export KI_STAGE=development
stackctl -t local start
# Browser: http://localhost:5173 (frontend)
# API: http://localhost:8000
```

### Production (pre-built frontend)
```bash
cd web/frontend && npm run build  # one-time
export KI_STAGE=production
stackctl -t local start
# Browser + API: http://localhost:8000
```

### Minimal (API-only, no frontend)
```bash
export KI_STAGE=minimal
stackctl -t local start
# API only: http://localhost:8000/api/...
```

## Overview

This directory contains comprehensive documentation for kicli-code-assist's deployment infrastructure:

- **StackCtl**: Process orchestration tool for managing services
- **Stages**: Configuration profiles for different deployment scenarios (development, production, minimal)
- **Architecture**: How services, configuration, and deployment work together

## Documentation Files

| File | Purpose |
|------|---------|
| **STACKCTL_ARCHITECTURE.md** | High-level architecture overview; read this first |
| **STACKCTL_IMPLEMENTATION.md** | Detailed implementation guide; how stages work internally |
| **STACKCTL_STATUS.md** | Current deployment status and known issues |
| **STACK_YAML_VARIANTS.md** | Legacy documentation (symlink-based system); archived |
| **SEMI_PROD_DEPLOYMENT.md** | Semi-production deployment notes |
| **OPTION2_STACKCTL_SYSTEMD.md** | systemd integration for production deployments |
| **kicli-web-option*.conf** | systemd service configuration templates |

## Stages

### 1. Development (`development.yaml`)
- **Services**: API (8000) + Frontend with HMR (5173)
- **Use Case**: Local development
- **Frontend**: Live reload via Vite
- **Activation**: `export KI_STAGE=development` (default)

### 2. Production (`production.yaml`)
- **Services**: Single unified `web` service (8000)
- **Use Case**: Production deployment, staging
- **Frontend**: Pre-built static files served by Flask
- **Activation**: `export KI_STAGE=production`
- **Prerequisite**: `npm run build`

### 3. Minimal (`minimal.yaml`)
- **Services**: API only (8000)
- **Use Case**: Testing, CI/CD, server-only deployments
- **Frontend**: None
- **Activation**: `export KI_STAGE=minimal`

## Configuration

Stage configuration resides in `config/stages/`:

```bash
config/
├── defaults/
│   └── stack.yaml           # Base stack definition
├── stages/
│   ├── development.yaml     # Dev stage
│   ├── production.yaml      # Prod stage  
│   └── minimal.yaml         # Minimal stage
```

**Stage selection** via environment variable:
```bash
export KI_STAGE=<stage_name>
```

The config system (ki_core) automatically loads the appropriate stage YAML.

## Troubleshooting

### Port Already in Use
```bash
lsof -i :8000
kill -9 <PID>
```

### Service Not Starting
```bash
stackctl -t local logs
tail -f var/log/api.log
```

### Frontend Not Loading
Ensure you've built the frontend:
```bash
cd web/frontend && npm run build
```

## CI/CD

GitHub Actions workflow in `.github/workflows/test.yml` uses the `minimal` stage for testing:
- Minimal dependencies (API-only)
- Fast startup and health checks
- Validates configuration system

## Key Features

✅ **Stage-based configuration**: Clean, environment-aware configuration
✅ **Multiple deployment modes**: Dev, production, minimal
✅ **Health checks**: Auto-validate service readiness
✅ **Process management**: StackCtl handles service lifecycle
✅ **Logs**: Centralized logging to `var/log/`

## Related

- **Architecture**: See `doc/ARCHITECTURE.md` for system-wide overview
- **Configuration**: See `ki_core.config` documentation for config system details
- **Legacy**: Old symlink-based approach archived in `deploy/legacy/`

## Questions?

See individual documentation files above or check the commit history for recent changes.

# ❌ DEPRECATED - Use `config/stages/` instead

This folder contains **legacy stack configurations** from before the stackctl stage-based refactoring.

## What Changed?

The project now uses **stage-based configuration** (cleaner, more maintainable):
- **Old system**: Symlinks (`stack.yaml` → `stack-dev.yaml`, `stack-prod.yaml`, etc.) in `deploy/`
- **New system**: Stage files (`config/stages/development.yaml`, `config/stages/production.yaml`, etc.) with environment variables

## Migration

**Before** (symlink-based):
```bash
cd deploy
ln -sf stack-dev.yaml stack.yaml
stackctl -t local start
```

**Now** (stage-based):
```bash
export KI_STAGE=development   # or production, minimal, etc.
stackctl -t local start
```

## Why the Change?

1. **Cleaner**: Stage selection via `KI_STAGE` env var (standard pattern)
2. **Version control friendly**: No symlinks to commit/maintain
3. **Compatible with other ki-ecosystem apps**: ki-knowledge uses the same pattern
4. **Non-destructive overrides**: YAML `__replace__` marker for full dict replacement

## Legacy Files

Archived in `deploy/legacy/`:
- `stack-dev.yaml` - Development (Vite HMR)
- `stack-minimal.yaml` - API-only
- `stack-semiprod.yaml` - Production (pre-built frontend)
- `stack-full.yaml` - With database support (unused)

These files are kept for reference only and should not be used.

## Documentation

See `doc/deployment/STACKCTL_IMPLEMENTATION.md` for the complete stage architecture and how to use it.


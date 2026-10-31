# StackCtl Architecture & Configuration Strategy

## Problem Statement

StackCtl was designed for ki-core configuration integration (see ki-knowledge). The naive `deploy/stack-*.yaml` + symlink approach bypasses this design and creates two sources of truth.

## Design Principles

1. **Single Source of Truth**: Stack config lives in `config/` hierarchy, not `deploy/`
2. **Stage-Based Overrides**: Different scenarios (dev/prod) are Stage configurations, not separate YAML files
3. **ki-core Integration**: StackCtl uses `config_loader = "ki_core:load_config"` to merge layered configs
4. **Deploy Folder**: Contains *documentation* and *legacy references* only, not active configs

## Configuration Hierarchy

```
config/defaults/stack.yaml          # Base config (all scenarios start here)
  ↓ (merge)
config/stages/development.yaml      # Dev overrides (HMR frontend, live config)
config/stages/production.yaml       # Prod overrides (static frontend, no HMR)
config/stages/minimal.yaml          # TUI-only overrides (no frontend service)
  ↓ (merge)
config/runtime/runtime.yaml         # Runtime-specific overrides (if needed)
```

## How StackCtl Resolves

1. StackCtl reads `pyproject.toml`:
   ```toml
   [tool.stackctl]
   config_loader = "ki_core:load_config"
   config_key = "stack"
   ```

2. Calls `ki_core.load_config()` which:
   - Loads `config/defaults/stack.yaml`
   - Merges active stage from `config/stages/{KI_STAGE}.yaml`
   - Merges runtime from `config/runtime/runtime.yaml`
   - Returns merged dict

3. StackCtl reads `result["stack"]` section

## Usage

```bash
# Development (default)
export KI_STAGE=development
stackctl -t local start

# Production
export KI_STAGE=production
stackctl -t local start

# Minimal (TUI-only)
export KI_STAGE=minimal
stackctl -t local start
```

## Migration from Symlink Approach

**OLD** (don't use):
```bash
cd deploy && ln -sf stack-dev.yaml stack.yaml && cd ..
stackctl -t local start
```

**NEW** (correct):
```bash
export KI_STAGE=development
stackctl -t local start
```

## Why This Matters

- **ki-knowledge** already uses this pattern correctly
- **kicli-code-assist** should follow same pattern for consistency
- **Operators** don't juggle symlinks; they set `KI_STAGE` environment variable
- **Deployment** is stage-aware (dev container sets KI_STAGE=development, prod sets KI_STAGE=production)

## Implementation Checklist

- [x] `config/defaults/stack.yaml` - Base config with all services
- [ ] `config/stages/development.yaml` - Dev overrides (vite HMR enabled)
- [ ] `config/stages/production.yaml` - Prod overrides (static frontend)
- [ ] `config/stages/minimal.yaml` - TUI-only (no frontend service)
- [ ] Update pyproject.toml to use `config_loader`
- [ ] Document in deploy/README.md (clarify this is for reference only)
- [ ] Remove old deploy/stack-*.yaml files once deprecated

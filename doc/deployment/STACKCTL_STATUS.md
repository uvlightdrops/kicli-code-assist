# StackCtl Configuration Status

**Last Updated**: 2024-11-01 (Current Session)
**Status**: 🟡 PARTIALLY WORKING - Config loading issue resolved

## Current State

### ✅ Working
- [ ] API starts successfully on :8000 (direct Python execution)
- [ ] Frontend starts on :5173 (vite dev with direct binary path)
- [ ] `pyproject.toml` configured for stackctl:
  ```toml
  [tool.stackctl]
  config_loader = "ki_core:load_config"
  config_key = "stack"
  ```
- [ ] Config structure in place:
  - `config/defaults/stack.yaml` - base stack definition
  - `config/stages/{development,production,minimal}.yaml` - stage overrides
  - `config/stages/.active_stage` - marker file
  - `ki.yaml` - minimal app config (auto-created)

### 🟡 Issues & Fixes Applied

#### Issue 1: Missing ki.yaml (FIXED ✅)
- **Problem**: `ki_core.load_config()` requires `ki.yaml` file, not directory
- **Solution**: Created minimal `ki.yaml` at project root
- **Verification**: `load_config('ki.yaml')` now returns dict instead of error

#### Issue 2: Config Merge Strategy (INVESTIGATING)
- **Problem**: Stage config not auto-merging with defaults
- **Ki-knowledge Pattern**: 
  - `config/defaults/stack.yaml` has full stack definition
  - `config/stages/*.yaml` have **partial overrides** (llm, apps, etc sections)
  - NOT separate full `stack:` sections
- **Current Implementation**: 
  - ✅ `config/defaults/stack.yaml` correct (full stack definition)
  - ❌ `config/stages/*.yaml` might have wrong structure (full stack sections vs overrides)
- **Next**: Verify stage YAML structure matches ki-knowledge pattern

#### Issue 3: Runtime Config Adapter (FIXED ✅)
- **Problem**: Flask routes tried to import non-existent `runtime_config` module
- **Solution**: Created `kicli_code_assist/runtime_config.py` (165 lines)
- **Provides**: snapshot(), save(), save_secret(), flatten() functions
- **Status**: Functional, wraps ki_core.runtime_settings

## Required Tests

### Test 1: Config Loading
```bash
cd /home/flow/dev_flow/kicli-code-assist
source .venv/bin/activate
python -c "
from ki_core.config import load_config
config = load_config('ki.yaml')
if 'stack' in config and isinstance(config['stack'], dict):
    print('✅ Config loading works')
    print(f'Services: {list(config[\"stack\"][\"services\"].keys())}')
else:
    print(f'❌ stack is {type(config.get(\"stack\"))}')
"
```

### Test 2: Stage Switching
```bash
export KI_STAGE=production
stackctl -t local status  # Should load prod config
```

### Test 3: Full Stack Startup
```bash
export KI_STAGE=development
stackctl -t local start
# Check: API on :8000, frontend on :5173
```

## Files Modified This Session

1. `config/defaults/stack.yaml` - Base stack config
2. `config/stages/development.yaml` - Dev overrides
3. `config/stages/production.yaml` - Prod overrides  
4. `config/stages/minimal.yaml` - Minimal overrides
5. `ki.yaml` - Auto-created, minimal app config
6. `kicli_code_assist/runtime_config.py` - Adapter layer (created earlier session)
7. `kicli_code_assist/llm_runtime.py` - LLM config stub (created earlier session)
8. `pyproject.toml` - Added stackctl tool config

## Ki-knowledge Reference

**Where**: `/home/flow/dev_flow/ki-knowledge/`
**Pattern**: 
- App config in `ki.yaml` (knowledge, jira, apps sections)
- Stack config split: `config/defaults/stack.yaml` + `config/stages/*.yaml`
- Stages are **partial** (override specific sections like `llm:`, `apps:`)
- NOT full duplicate `stack:` sections

**Lessons Learned**:
- Stage files should override, not replace
- Each stage file is minimal (only what differs from defaults)
- `config_loader = "ki_core:load_config"` handles the merge

## Next Steps

1. ✅ Verify stage YAML structure against ki-knowledge pattern
2. [ ] Test `KI_STAGE=development` → should merge properly
3. [ ] Test `KI_STAGE=production` → should remove frontend service
4. [ ] Test `KI_STAGE=minimal` → API only
5. [ ] Update deploy/README.md with KI_STAGE instructions
6. [ ] Remove or deprecate deploy/stack-*.yaml files

## Architecture Decision: Why Stage-Based?

- **Ki-knowledge precedent**: Proven pattern across similar infrastructure
- **Consistency**: All KI projects follow same deployment model
- **Maintainability**: Single source of truth (config/ hierarchy)
- **Operator UX**: Simple env var instead of symlink juggling
- **CI/CD**: Easy to parameterize for different environments

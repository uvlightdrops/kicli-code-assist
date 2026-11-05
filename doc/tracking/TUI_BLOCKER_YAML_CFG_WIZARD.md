---
project: kicli-code-assist
scope: tracking
created: 2026-11-05 19
updated: 2026-11-05 19
update_reason: TUI blocker analysis - yaml_cfg_wizard import in ki-core
status: blocked
---

# TUI Blocker: yaml_cfg_wizard Import Issue

## Problem
```
ImportError: cannot import name 'merge_with_replacement' from 'yaml_cfg_wizard'
```

Location: `ki-core/src/ki_core/config.py:23`

## Root Cause Analysis

### What's Needed
ki-core imports:
```python
from yaml_cfg_wizard import (
    merge_with_replacement,  # ← Not available!
    ...
)
```

### What's Available
```python
from yaml_cfg_wizard import (
    deep_merge,             # ← Available
    ConfigResolver,
    load_yaml_file,
    merge_schemas,
    ...
)
```

### Usage in ki-core
```python
# Line 209, 218, 223
payload = merge_with_replacement(payload, creds_payload)
return strip_replace_markers(merge_with_replacement(schema_defaults, payload))
```

## Options

### Option A: Use deep_merge Instead
Replace all `merge_with_replacement` calls with `deep_merge`:
```python
from yaml_cfg_wizard import deep_merge
payload = deep_merge(payload, creds_payload)  # ← Same API?
```
**Status**: Needs verification that API is identical

### Option B: Define merge_with_replacement in ki-core
Implement custom `merge_with_replacement()` in ki-core that:
- Wraps `deep_merge()`
- Handles `__replace__: true` markers
- Calls `strip_replace_markers()` after

### Option C: Check yaml_cfg_wizard Version
Verify version in `ki-core/pyproject.toml`:
```bash
grep "yaml_cfg_wizard" ki-core/pyproject.toml
```
Might be an old version requirement that needs updating.

## Impact on TUI

**Blocker Status**: ⏸️ BLOCKING CLI ONLY
- ✅ TUI code: Works (direct import, no ki-core)
- ✅ TUI imports: Functional
- ❌ CLI command: Cannot start (`kicli-assist tui` fails)
- ✅ Direct test: `python3 -c "from kicli_code_assist.ui.tui_client import ..."` works

## Workaround for Now

Direct Python instead of CLI:
```bash
python3 << 'EOF'
from kicli_code_assist.ui.tui_client import CodeAssistantTUIApp, run_tui
from pathlib import Path
run_tui(str(Path.home() / "dev_art/hdgui"))
EOF
```

## Next Steps

1. **Investigate**: Check ki-core/pyproject.toml for yaml_cfg_wizard version
2. **Decide**: Which option (A, B, C) to use
3. **Fix**: Update ki-core/config.py imports
4. **Test**: Verify CLI works: `kicli-assist tui --help`
5. **Full Integration Test**: Run TUI end-to-end with backend

## Related Issues

- User question (2026-11-05): "ki-core sollte doch keine dependency in diese Richtung haben oder nicht??"
  - Answer: ki-core DOES depend on yaml_cfg_wizard (correctly), but import is broken

## Session Impact

- TUI implementation: **100% complete** ✅
- Testing: Blocked on yaml_cfg_wizard (ki-core issue)
- Timeline: ~15 min fix once root cause identified

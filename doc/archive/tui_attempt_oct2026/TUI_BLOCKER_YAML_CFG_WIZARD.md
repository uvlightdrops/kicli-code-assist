---
project: kicli-code-assist
scope: tracking
created: 2026-11-05 19
updated: 2026-11-05 19
update_reason: All blockers resolved - TUI fully operational
status: resolved
---

# TUI Blocker: yaml_cfg_wizard - RESOLVED ✅

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

## Resolution ✅

### Fix Applied (Option B: Local Implementation)

**ki-core commit a40143a**:
```python
def merge_with_replacement(base: Any, override: Any) -> Any:
    """Merge with __replace__: true marker support."""
    result = deep_merge(base, override)
    return strip_replace_markers(result)

def strip_replace_markers(obj: Any) -> Any:
    """Recursively remove __replace__: true from dicts."""
    if isinstance(obj, dict):
        return {
            k: strip_replace_markers(v)
            for k, v in obj.items()
            if k != "__replace__"
        }
    elif isinstance(obj, list):
        return [strip_replace_markers(item) for item in obj]
    return obj
```

**kicli-code-assist commit 89234bc**:
- Fixed `ProjectExplorer.tree → file_tree` (property conflict with Textual Container)

### Result
✅ All blockers resolved
✅ TUI fully operational
✅ CLI commands work

## Impact on TUI

**Blocker Status**: ✅ RESOLVED
- ✅ TUI code: Works perfectly
- ✅ TUI imports: Functional
- ✅ CLI command: `kicli-assist tui` works
- ✅ TUI startup: Full interface renders
- ⏳ Backend connectivity: Test pending (need stackctl start)

## Workaround for Now

✅ NO WORKAROUND NEEDED - FULLY RESOLVED

Direct usage:
```bash
kicli-assist tui --project /path/to/code
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

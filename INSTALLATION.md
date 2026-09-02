# Installation Guide - kicli-code-assist

## One-Step Installation

Just run:

```bash
python3 install_local.py
```

This script automatically:
1. ✅ Creates a virtual environment (if needed)
2. ✅ Resolves `${HOME}` to your home directory
3. ✅ Expands ki-core path in `pyproject.toml`
4. ✅ Installs all dependencies
5. ✅ Verifies ki-core exists

## Quick Start

```bash
# Run the installer (one-time)
python3 install_local.py

# Activate venv
source venv/bin/activate

# Use the tool
kicli-assist tui          # Terminal UI
kicli-assist chat         # Simple chat mode
kicli-assist --help       # See all options
```

## How Dynamic Paths Work

**Problem:** Original hardcoded path broke for other users:
```toml
ki-core @ file:///home/flow/dev_flow/ki-core  ❌ Only works for user "flow"
```

**Solution:** Placeholder expanded at install time:
```toml
ki-core @ file://${HOME}/dev_flow/ki-core  ✅ Works for any user
```

The `install_local.py` script:
- Reads current user's `$HOME` via `Path.home()`
- Replaces `${HOME}` with actual path
- Updates `pyproject.toml` with expanded path
- Installs using venv's pip

## Requirements

- Python 3.10+
- `ki-core` at `~/dev_flow/ki-core`
- `ki-knowledge` at `~/dev_flow/ki-knowledge` (optional, for some features)

## Troubleshooting

### "ki-core not found at /home/youruser/dev_flow/ki-core"
```bash
# Verify ki-core exists
ls -la ~/dev_flow/ki-core
# Should show: __init__.py, core/, config.py, etc.
```

### Verify installation worked
```bash
source venv/bin/activate
python3 -c "from ki_core import Config; print('✅ Success')"
```

### If things go wrong
Delete `venv/` and re-run:
```bash
rm -rf venv/
python3 install_local.py
```

## For Multiple Users

Each user runs the installer once:
```bash
cd ~/projects/kicli-code-assist  # (wherever they cloned it)
python3 install_local.py
```

Each gets their own venv with paths expanded to their `$HOME`.


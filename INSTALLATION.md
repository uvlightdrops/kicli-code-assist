# Installation Guide - kicli-code-assist

## One-Step Installation

Just run:

```bash
python3 install_local.py
```

This script automatically:
1. ✅ Creates a virtual environment (if needed)
2. ✅ Verifies that a local `ki-core` checkout exists at `~/dev_flow/ki-core`
3. ✅ Installs `ki-core` in editable mode
4. ✅ Installs `kicli-code-assist` in editable mode
5. ✅ Keeps the project portable without machine-specific `file://` URLs

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

## How it works

The project now avoids hardcoded `file://${HOME}` package URLs. Instead, the installer explicitly installs the local `ki-core` checkout first, then installs the current project. This keeps the metadata stable and removes machine-specific path issues across different users or machines.

## Requirements

- Python 3.10+
- `ki-core` at `~/dev_flow/ki-core`
- `ki-knowledge` at `~/dev_flow/ki-knowledge` (optional, for some features)

## Troubleshooting

### "ki-core not found at /home/youruser/dev_flow/ki-core"
```bash
# Verify ki-core exists
ls -la ~/dev_flow/ki-core
# Should show: src/, README.md, pyproject.toml, etc.
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

Each user runs the installer once from their own clone and keeps a local venv. The project no longer depends on a single fixed absolute path.


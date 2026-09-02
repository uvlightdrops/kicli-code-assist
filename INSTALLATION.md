# Installation Guide - Dynamic ki-core Path

## Problem

The original `pyproject.toml` had hardcoded ki-core paths:
```toml
ki-core @ file:///home/flow/dev_flow/ki-core
```

This breaks if the project is moved to a different home directory or user.

## Solution

The `pyproject.toml` now uses a placeholder that gets expanded at install time:
```toml
ki-core @ file://${HOME}/dev_flow/ki-core
```

## Installation

Use the provided install script to expand the `$HOME` placeholder:

```bash
cd /home/flow/dev_flow/kicli-code-assist
python3 install_local.py
```

This script:
1. Resolves `${HOME}` to the current user's home directory
2. Verifies ki-core exists
3. Updates `pyproject.toml` with the expanded path
4. Installs the package with `pip install -e .`

## How It Works

### Before Installation
```
pyproject.toml contains:
  ki-core @ file://${HOME}/dev_flow/ki-core
```

### During Installation (install_local.py)
```python
home = str(Path.home())  # e.g., /home/flow
ki_core_path = os.path.join(home, "dev_flow", "ki-core")
# Result: /home/flow/dev_flow/ki-core

# Update pyproject.toml with expanded path
content = content.replace("${HOME}/dev_flow/ki-core", ki_core_path)
```

### After Installation
```
pyproject.toml contains:
  ki-core @ file:///home/flow/dev_flow/ki-core
```

## Verification

After installation, check that ki-core is properly installed:

```bash
python3 -c "from ki_core import Config; print('✅ ki-core imported successfully')"
```

## Environment

- `HOME`: Automatically resolved from `Path.home()`
- `DEV_FLOW`: Expected at `${HOME}/dev_flow`
- `KI-CORE`: Expected at `${HOME}/dev_flow/ki-core`

## Troubleshooting

### "ki-core not found"
```bash
# Check if ki-core exists
ls -la ~/dev_flow/ki-core

# Should show: __init__.py, core/, adapters/, config.py, etc.
```

### Installation fails with permission error
```bash
# Use --user flag
python3 install_local.py --user
```

### Manual installation
If the script fails, manually expand the path:
```bash
# Get your home directory
echo $HOME

# Replace ${HOME} in pyproject.toml with actual path
sed -i 's|${HOME}|/home/youruser|g' pyproject.toml

# Install
pip install -e .
```

## Notes

- The `install_local.py` script modifies `pyproject.toml` in-place
- Original paths are resolved relative to the current user's `$HOME`
- Each user needs to run `python3 install_local.py` when installing locally
- The modified `pyproject.toml` can be committed (it contains placeholder)

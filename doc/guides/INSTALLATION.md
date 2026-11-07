---
title: INSTALLATION
project: kicli-code-assist
scope: guides
purpose: Installation guide for setting up kicli-code-assist development environment
created: 2026-09-02T09:27:38+01:00
updated: 2026-11-07T17:10:00+01:00
update_reason: Applied semantic block tagging skill - added block IDs to H2 headings
semantic_blocks:
  - id: requirements
    title: Requirements
  - id: step-1-clone-repository
    title: Step 1: Clone Repository
  - id: step-2-create-virtual-environment
    title: Step 2: Create Virtual Environment
  - id: step-3-install-dependencies
    title: Step 3: Install Dependencies
  - id: step-4-generate-config
    title: Step 4: Generate Config
  - id: step-5-test-installation
    title: Step 5: Test Installation
  - id: configuration-details
    title: Configuration Details
  - id: troubleshooting
    title: Troubleshooting
  - id: advanced-setup
    title: Advanced Setup
  - id: updating
    title: Updating
  - id: support
    title: Support
status: active
---

# Installation Guide - KI Code Assistant

## Requirements [requirements]

- Python 3.10+
- Git
- Basic terminal knowledge
- SSH access (optional, for remote use)

## Step 1: Clone Repository [step-1-clone-repository]

```bash
# Create dev directory
mkdir -p ~/dev_flow
cd ~/dev_flow

# Clone ki-core (required dependency)
git clone <ki-core-repo-url> ki-core

# Clone kicli-code-assist
git clone <kicli-repo-url> kicli-code-assist
```

## Step 2: Create Virtual Environment [step-2-create-virtual-environment]

```bash
cd kicli-code-assist

# Create venv
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

## Step 3: Install Dependencies [step-3-install-dependencies]

```bash
# Install ki-core first (must be in ../ki-core)
pip install -e ../ki-core

# Install kicli-code-assist
pip install -e .
```

## Step 4: Generate Config [step-4-generate-config]

```bash
# Auto-generate config skeleton
yaml-cfg config skeleton -o ki.yaml

# Edit config with your settings
vim ki.yaml
```

**Required settings:**
- `llm.default_provider` - Choose: `openai`, `ollama`, or `ki`
- LLM provider credentials (API key or base URL)

**Optional settings:**
- `kicli.context.max_files` - Max files in context (default: 10)
- `kicli.workspace_root` - Project directory (auto-detected)
- `storage.cache_dir` - Cache directory

## Step 5: Test Installation [step-5-test-installation]

```bash
# Check environment
kicli-assist doctor

# Test with simple chat
kicli-assist chat --model gpt-4

# Or launch TUI
kicli-assist tui
```

---

## Configuration Details [configuration-details]

### Layered Config System

Your config is resolved from multiple sources in order:

1. **Environment Variables** (highest priority)
   ```bash
   export KI_CFG_LLM__DEFAULT_PROVIDER=openai
   ```

2. **Runtime Overrides** (`config/runtime/runtime.yaml`)

3. **Stage Overrides** (`config/stages/*.yaml`)

4. **Profile Overrides** (`config/profiles/*.yaml`)

5. **Defaults** (`config/defaults.yaml` - auto-generated)

6. **Main Config** (`ki.yaml`)

7. **Schema Defaults** (lowest priority)

### Config File Structure

```yaml
# llm.yaml
llm:
  default_provider: openai
  providers:
    openai:
      api_key: sk-...
      model: gpt-4
    ollama:
      base_url: http://localhost:11434
      model: llama3.2

# apps.kicli
apps:
  kicli:
    workspace_root: /path/to/project
    context:
      max_files: 10
      cache_enabled: true
    diff:
      format: unified
      context_lines: 3
```

### Environment-Specific Configs

```bash
# Create profile for different environments
mkdir -p config/profiles
mkdir -p config/stages

# Production profile
cat > config/profiles/production.yaml << 'PROFILE'
llm:
  providers:
    openai:
      model: gpt-4
PROFILE

# Staging stage
cat > config/stages/staging.yaml << 'STAGE'
kicli:
  context:
    max_files: 5
STAGE

# Use with environment variable
export KI_CFG_PROFILE=production
export KI_CFG_STAGE=staging
kicli-assist tui
```

---

## Troubleshooting [troubleshooting]

### Command Not Found

```bash
# Make sure venv is activated
source .venv/bin/activate

# Or use full path
.venv/bin/kicli-assist --help
```

### Config File Not Found

```bash
# Generate config
yaml-cfg config skeleton

# Inspect the resolved config tree
yaml-cfg config list --config ki.yaml
```

### Provider Not Found

```bash
# Check diagnostics
kicli-assist doctor

# Verify credentials
kicli-assist config show llm.providers.openai
```

### Import Errors

```bash
# Reinstall ki-core
pip install -e ../ki-core --force-reinstall

# Reinstall kicli-code-assist
pip install -e . --force-reinstall

# Check versions
pip show ki-core yaml-cfg-wizard
```

---

## Advanced Setup [advanced-setup]

### Remote Development (SSH)

```bash
# Install on remote server
ssh user@server
cd ~/dev_flow/kicli-code-assist
source .venv/bin/activate

# Use Tmux layout
kicli-assist tmux --simple
```

### Docker Setup (Optional)

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY . .
RUN pip install -e ../ki-core
RUN pip install -e .

CMD ["kicli-assist", "tui"]
```

### Development Mode

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run linter
ruff check .

# Run formatter
ruff format .
```

---

## Updating [updating]

```bash
# Activate venv
source .venv/bin/activate

# Pull latest code
git pull

# Reinstall packages
pip install -e ../ki-core --upgrade
pip install -e . --upgrade
```

---

## Support [support]

- **Diagnostics:** `kicli-assist doctor`
- **Help:** `kicli-assist --help`
- **Config Help:** `yaml-cfg config --help`
- **Issues:** Check [docs/](docs/)

---

**Last Updated:** 2026-09-05

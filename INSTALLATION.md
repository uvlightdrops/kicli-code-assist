# Installation Guide - KI Code Assistant

## Requirements

- Python 3.10+
- Git
- Basic terminal knowledge
- SSH access (optional, for remote use)

## Step 1: Clone Repository

```bash
# Create dev directory
mkdir -p ~/dev_flow
cd ~/dev_flow

# Clone ki-core (required dependency)
git clone <ki-core-repo-url> ki-core

# Clone kicli-code-assist
git clone <kicli-repo-url> kicli-code-assist
```

## Step 2: Create Virtual Environment

```bash
cd kicli-code-assist

# Create venv
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

## Step 3: Install Dependencies

```bash
# Install ki-core first (must be in ../ki-core)
pip install -e ../ki-core

# Install kicli-code-assist
pip install -e .
```

## Step 4: Generate Config

```bash
# Auto-generate config skeleton
kicli-assist config init -o ki.yaml

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

## Step 5: Test Installation

```bash
# Check environment
kicli-assist doctor

# Test with simple chat
kicli-assist chat --model gpt-4

# Or launch TUI
kicli-assist tui
```

---

## Configuration Details

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

## Troubleshooting

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
kicli-assist config init

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

## Advanced Setup

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

## Updating

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

## Support

- **Diagnostics:** `kicli-assist doctor`
- **Help:** `kicli-assist --help`
- **Config Help:** `yaml-cfg config --help`
- **Issues:** Check [docs/](docs/)

---

**Last Updated:** 2026-09-05

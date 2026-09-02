# Unified Configuration System

## Overview

kicli-code-assist now uses the unified configuration system from **ki-core**. This ensures consistency across all ki-ecosystem projects (ki-core, ki-knowledge, kicli-code-assist).

## Configuration Files

Configuration is loaded in this priority order:

1. **Environment Variables** (highest priority) - `KICLI_*`
2. **`ki.yaml`** (local config, non-sensitive)
3. **`creds.yaml`** (global credentials, gitignored)
4. **Defaults** (lowest priority)

## Setup

### 1. Copy Example Config

```bash
cp ki.yaml.example ki.yaml
```

### 2. Configure KI CLI Paths (Optional)

Add to `ki.yaml`:

```yaml
kicli:
  cache_dir: "~/dev_data/kicli-code-assist"
  session_dir: "~/dev_data/kicli-code-assist/sessions"
  chat_history_dir: "~/dev_data/kicli-code-assist/chat_history"
```

**Or use environment variables:**

```bash
export KICLI_CACHE_DIR="~/dev_data/kicli-code-assist"
export KICLI_SESSION_DIR="~/dev_data/kicli-code-assist/sessions"
export KICLI_CHAT_HISTORY_DIR="~/dev_data/kicli-code-assist/chat_history"
```

### 3. Run kicli-code-assist

```bash
kicli-assist tui
```

The app automatically loads configuration from ki-core's `Config.from_env()`.

## Configuration Locations Searched

```
./ki.yaml
./kicli.yaml
./config.yaml
./config/ki.yaml
./config/config.yaml
~/.config/ki/config.yaml
~/.config/kicli/config.yaml
```

## API Usage

### In Code

```python
from ki_core import Config

# Load configuration from YAML + environment
config = Config.from_env()

# Access kicli paths
cache_dir = config.kicli_cache_dir
chat_history_dir = config.kicli_chat_history_dir
session_dir = config.kicli_session_dir
```

### In chat_history.py

```python
from kicli_code_assist.chat_history import get_cache_dir, get_chat_history_dir

cache_dir = get_cache_dir()          # Uses Config.kicli_cache_dir
chat_dir = get_chat_history_dir()    # Uses Config.kicli_chat_history_dir
```

These helper functions automatically expand paths and create directories if needed.

## Integration with Other Settings

kicli-code-assist can also access other unified config settings:

```python
from ki_core import Config

config = Config.from_env()

# LLM Provider configuration
ollama_url = config.ollama_base_url
openai_key = config.openai_api_key

# Knowledge base settings
data_root = config.knowledge_data_root
embed_model = config.knowledge_embed_model

# HTTP settings
timeout = config.request_timeout
```

## Default Fallbacks

If no configuration is found:

- **kicli_cache_dir**: `~/dev_data/kicli-code-assist`
- **kicli_chat_history_dir**: `{cache_dir}/chat_history`
- **kicli_session_dir**: `{cache_dir}/sessions`

These match the original hardcoded paths for backward compatibility.

## Migration from Old System

If you had data in the old location (`~/.kicli`), you can migrate:

```bash
# Move old cache to new location
mkdir -p ~/dev_data/kicli-code-assist
mv ~/.kicli/* ~/dev_data/kicli-code-assist/
rmdir ~/.kicli
```

## Examples

### Example 1: Using Defaults (No Config File)

```bash
# Works immediately after install
kicli-assist tui

# Data saved to ~/dev_data/kicli-code-assist/
```

### Example 2: Custom Data Location

**ki.yaml:**
```yaml
kicli:
  cache_dir: "/opt/kicli-data"
  chat_history_dir: "/opt/kicli-data/chats"
```

**Run:**
```bash
kicli-assist tui

# Data saved to /opt/kicli-data/
```

### Example 3: Development vs Production

**config/dev.yaml:**
```yaml
kicli:
  cache_dir: "./local-data"
  chat_history_dir: "./local-data/chats"

ollama:
  base_url: "http://localhost:11434"
```

**config/prod.yaml:**
```yaml
kicli:
  cache_dir: "/var/kicli/data"
  chat_history_dir: "/var/kicli/data/chats"

openai:
  base_url: "https://api.openai.com/v1"
  model: "gpt-4"
```

**Run:**
```bash
# Development
python -c "from ki_core import Config; c = Config.from_yaml('config/dev.yaml')"

# Production
python -c "from ki_core import Config; c = Config.from_yaml('config/prod.yaml')"
```

## Debugging

### Check Current Configuration

```bash
python3 -c "
from ki_core import Config
config = Config.from_env()
print(f'Cache dir: {config.kicli_cache_dir}')
print(f'Chat history dir: {config.kicli_chat_history_dir}')
print(f'Session dir: {config.kicli_session_dir}')
"
```

### Check Which Config Files Were Found

```bash
# See which ki.yaml files exist
find ~/.config/ki -name "*.yaml" 2>/dev/null
find . -name "ki.yaml" -o -name "creds.yaml"

# Check current directory
ls -la ki.yaml creds.yaml config/*.yaml 2>/dev/null || echo "No config files here"
```

### Environment Variable Override

```bash
# Override config file with environment variable
export KICLI_CACHE_DIR="/tmp/test-cache"
python3 -c "
from ki_core import Config
config = Config.from_env()
print(f'Cache dir: {config.kicli_cache_dir}')
"
# Output: Cache dir: /tmp/test-cache
```

## Security

- **Keep API keys in `creds.yaml`**, not `ki.yaml`
- **Add `creds.yaml` to `.gitignore`**
- **Use environment variables for CI/CD**
- **Restrict file permissions**: `chmod 600 creds.yaml`

## Consistency Across Projects

All ki ecosystem projects use the same configuration system:

| Project | Config Section | Usage |
|---------|---|---|
| **ki-core** | All sections | LLM providers, HTTP settings |
| **ki-knowledge** | `knowledge:` | Data paths, embedding models |
| **kicli-code-assist** | `kicli:` | Cache dirs, session management |

This ensures consistent configuration management across all tools.

## Troubleshooting

### Config Not Loading

**Problem**: Changes to ki.yaml are not picked up

**Solution**:
1. Ensure ki.yaml is in the search path (see Configuration Locations)
2. Clear Python cache: `find . -type d -name __pycache__ -exec rm -r {} +`
3. Check environment variables: `echo $KICLI_CACHE_DIR`
4. Use `from_yaml()` with explicit path: `Config.from_yaml("path/to/ki.yaml")`

### Paths Not Expanding

**Problem**: `~/dev_data/` shows as literal string

**Solution**:
1. Paths are automatically expanded with `Path.expanduser()`
2. If using environment variables, expand them yourself: `export PATH="$(echo $PATH)"`
3. Use absolute paths instead of `~`

### Old Cache Still Being Used

**Problem**: Config points to new location but app uses old cache

**Solution**:
1. Clear Python import cache: `pip install -e . --force-reinstall`
2. Verify `get_cache_dir()` is using new path: Run debug check above
3. Manually move old data: See Migration section

## Future Enhancements

- [ ] Web UI for config management
- [ ] Config validation and schema
- [ ] Config profile switching (dev/prod)
- [ ] Auto-migration from old cache locations

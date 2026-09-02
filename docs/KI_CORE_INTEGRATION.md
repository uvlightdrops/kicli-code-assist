# kicli-code-assist + ki-core Integration

## Overview

kicli-code-assist now uses **ki-core** for all LLM provider access.

This means:
- ✅ Unified configuration (ki.yaml + creds.yaml)
- ✅ Support for multiple LLM providers (OpenAI, Ollama, Mock)
- ✅ Same Config object shared with ki-knowledge
- ✅ Easy provider switching

## Configuration

### Setup (First Time)

```bash
# Copy example config
cp /path/to/ki-core/ki.yaml.example ki.yaml

# Edit with your settings
vi ki.yaml

# (Optional) Create credentials file
cat > creds.yaml << 'EOF'
ki:
  base_url: "https://ki.company.com"
  api_key: "your-api-key"
EOF
chmod 600 creds.yaml
```

### Available Providers

**Ollama (Local)**
```yaml
ollama:
  base_url: "http://localhost:11434"
  model: "llama3.2"
```

**OpenAI (or compatible)**
```yaml
openai:
  base_url: "https://api.openai.com/v1"
  model: "gpt-4"
  api_key: ""  # Set in creds.yaml
```

**Company KI Server**
```yaml
ki:
  base_url: ""      # Set in creds.yaml
  api_key: ""       # Set in creds.yaml
  model: "google/gemma-4-26B-A4B-it"
```

## Usage

### Simple Chat with Different Providers

```bash
# Mock (no setup)
kicli-assist chat --provider mock

# Ollama (requires ollama serve)
kicli-assist chat --provider ollama

# OpenAI (requires KI_API_KEY)
kicli-assist chat --provider openai
```

### In Code

```python
from kicli_code_assist.examples.simple_chat import create_client
from ki_core import Config

# Load config
config = Config.from_env()

# Create client
client = create_client(config, provider="ollama")

# Use it
from ki_core.core.models import ChatRequest, Message, Role
request = ChatRequest(
    messages=[Message(role=Role.USER, content="Hello")]
)

response = client.chat(request)
print(response.message.content)
```

## Migration from Old Code

### Before (Old Config)
```python
from kicli.config import Config
from kicli.providers.ollama import OllamaProvider

config = Config.from_env()
provider = OllamaProvider(base_url=config.ollama_base_url)
```

### After (New ki-core)
```python
from ki_core import Config
from kicli_code_assist.examples.simple_chat import create_client

config = Config.from_env()
client = create_client(config, provider="ollama")
```

## Features

All kicli-code-assist features now work with **any LLM provider**:

- ✅ TUI (Terminal User Interface)
- ✅ Tmux launcher (for remote development)
- ✅ Simple chat interface
- ✅ Code generation and review
- ✅ Diff preview
- ✅ Safe code execution

Switch providers by changing `ki.yaml` or environment variables!

## Environment Variables (Override YAML)

```bash
# Ollama
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL="mistral"

# OpenAI
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4"

# Company KI Server
export KI_BASE_URL="https://ki.company.com"
export KI_API_KEY="..."
export KI_MODEL="google/gemma-4-26B-A4B-it"
```

## Examples

### Example 1: Use Ollama for Development

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Use kicli-code-assist
kicli-assist tui  # Uses ollama config from ki.yaml
```

### Example 2: Switch to OpenAI for Production

Just update `ki.yaml`:
```yaml
# Before
ollama:
  model: "mistral"

# After
openai:
  model: "gpt-4"
  api_key: ""  # Set in creds.yaml
```

Or via environment:
```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4"
kicli-assist chat --provider openai
```

### Example 3: Mock for Testing

```bash
# No setup needed
kicli-assist chat --provider mock
# Simulates AI responses
```

## Troubleshooting

**"ki_core not found"**
→ Install: `pip install ki-core` (or `pip install -e .` from kicli-code-assist)

**"Connection refused" (Ollama)**
→ Start Ollama first: `ollama serve`

**"Invalid API key" (OpenAI)**
→ Check `OPENAI_API_KEY` environment variable or `creds.yaml`

**"No models available" (Ollama)**
→ Download a model: `ollama pull llama3.2`

## Next Steps

1. Copy config from ki-core: `cp /path/to/ki-core/ki.yaml.example ki.yaml`
2. Edit ki.yaml with your provider settings
3. Run `kicli-assist chat --provider <your-provider>`
4. Try TUI: `kicli-assist tui`
5. Read [`CONFIG_GUIDE.md`](../ki-core/CONFIG_GUIDE.md) in ki-core for full options

## Documentation

- **kicli-code-assist README**: [`README.md`](README.md)
- **ki-core Config Guide**: See [`CONFIG_GUIDE.md`](../ki-core/CONFIG_GUIDE.md)
- **ki-core Getting Started**: See [`docs/GETTING_STARTED.md`](../ki-core/docs/GETTING_STARTED.md)

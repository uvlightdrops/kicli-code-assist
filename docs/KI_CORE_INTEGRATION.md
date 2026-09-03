# kicli-code-assist + ki-core Integration

`kicli-code-assist` uses `ki-core` for provider access and configuration loading.

## Effective config model

The assistant does not maintain its own separate YAML merge system anymore. It relies on:

1. `ki-core` base config discovery
2. optional layered project config under `config/`
3. `creds.yaml` for secrets
4. environment variables as final overrides

## Recommended project layout

```text
kicli-code-assist/
├── ki.yaml
├── creds.yaml
└── config/
    ├── defaults/
    ├── profiles/
    ├── stages/
    └── runtime/
        └── runtime.yaml
```

## Minimal setup

```bash
cp /path/to/ki-core/ki.yaml.example ki.yaml
chmod 600 creds.yaml
```

Example:

```yaml
ollama:
  base_url: "http://localhost:11434"
  model: "llama3.2"

kicli:
  cache_dir: "~/dev_data/kicli-code-assist"
  session_dir: "~/dev_data/kicli-code-assist/session"
  chat_history_dir: "~/dev_data/kicli-code-assist/chat_history"
  allowed_base_path: "/path/to/workspace"
```

Secrets:

```yaml
ki:
  base_url: "https://ki.company.com"
  api_key: "..."

openai:
  api_key: "sk-..."
```

## Used `Config` fields

`kicli-code-assist` currently reads:

- `kicli_cache_dir`
- `kicli_session_dir`
- `kicli_chat_history_dir`
- `kicli_allowed_base_path`
- provider fields such as `ki_base_url`, `ki_api_key`, `openai_api_key`, `ollama_base_url`
- `context_*` and `diff_*` settings

These come from `ki-core.Config.from_env()`.

## Notes

- Keep app-specific YAML under the `kicli:` section.
- Keep secrets in `creds.yaml`.
- Top-level legacy keys still work through `ki-core`, but `kicli:` is the preferred YAML shape.

# Unified Configuration System

`kicli-code-assist` now uses the layered `ki-core` configuration system end-to-end.

## Resolution order

1. base config file discovered by `ki-core`
2. optional `config/defaults/*.yaml`
3. optional `config/profiles/*.yaml`
4. optional `config/stages/*.yaml`
5. optional `config/runtime/runtime.yaml`
6. `creds.yaml` for secrets
7. environment variables

## Preferred YAML shape

```yaml
kicli:
  cache_dir: "~/dev_data/kicli-code-assist"
  session_dir: "~/dev_data/kicli-code-assist/session"
  chat_history_dir: "~/dev_data/kicli-code-assist/chat_history"
  allowed_base_path: "/path/to/workspace"
```

## Environment overrides

```bash
KICLI_CACHE_DIR=
KICLI_SESSION_DIR=
KICLI_CHAT_HISTORY_DIR=
KICLI_ALLOWED_BASE_PATH=
```

## Current behavior in the app

- `chat_history.py` uses `config.kicli_cache_dir` and `config.kicli_chat_history_dir`
- `task_tracker.py` uses `config.kicli_session_dir`
- `textual_app.py` uses `config.kicli_allowed_base_path`
- provider creation uses `ki-core.Config.from_env()`

## Recommendation

- Put shared AI/provider settings in the base `ki.yaml`
- Put app-specific overrides in the `kicli:` section
- Use `config/` layers for environment-specific overlays
- Keep secrets in `creds.yaml`

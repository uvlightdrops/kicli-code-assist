# kicli-code-assist + ki-core Integration

`kicli-code-assist` uses `ki-core` for provider access and configuration loading.

## Effective config model

The assistant does not maintain its own separate YAML merge system. It relies on:

1. `ki-core` base config discovery (`ki_core.load_config()`)
2. optional layered project config under `config/`
3. `creds.yaml` for secrets
4. schema validation + defaults from the merged YAML schema
   (`ki-core`'s generic base schema + this app's own
   `schema/kicli.schema.yaml`)
5. environment variables (`KI_CFG_*` prefix) as final overrides

`ki-core` itself has no app-specific config class. This app defines its
own thin, typed accessor - `kicli_code_assist.app_config.AppConfig` -
on top of the plain dict `ki_core.load_config()` returns.

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

Generate a config skeleton (merges ki-core's base schema with this app's
`schema/kicli.schema.yaml`, filling in all schema-declared defaults):

```bash
yaml-cfg config skeleton -o ki.yaml
chmod 600 creds.yaml
```

Example `ki.yaml`:

```yaml
llm:
  providers:
    ollama:
      base_url: "http://localhost:11434"
      model: "llama3.2"

storage:
  cache_dir: "~/dev_data/kicli-code-assist"
  session_dir: "~/dev_data/kicli-code-assist/session"
  history_dir: "~/dev_data/kicli-code-assist/chat_history"

apps:
  kicli:
    workspace_root: "/path/to/workspace"
```

Secrets (`creds.yaml`, deep-merged over `ki.yaml`):

```yaml
llm:
  providers:
    ki:
      base_url: "https://ki.company.com"
      api_key: "..."
    openai:
      api_key: "sk-..."
```

## Used `AppConfig` fields

`kicli_code_assist.app_config.AppConfig` (built from `ki_core.load_config()`)
exposes:

- `kicli_cache_dir`, `kicli_session_dir`, `kicli_chat_history_dir`,
  `kicli_allowed_base_path` (from `storage.*` / `apps.kicli.*`)
- provider fields: `ki_base_url`, `ki_api_key`, `openai_api_key`,
  `ollama_base_url`, etc. (from `llm.providers.*`, generic ki-core schema)
- `context_*` and `diff_*` settings (from `apps.kicli.context.*` /
  `apps.kicli.diff.*`)
- `raw`: the full resolved config dict, for consumers that need direct
  dict access (e.g. `security.*` for `kicli_code_assist.security`,
  `prompts.*` for `PromptManager`)

## Notes

- Keep app-specific YAML under `apps.kicli.*` (or the dedicated
  top-level sections this app owns: `storage`, `security`, `prompts`).
- Keep secrets in `creds.yaml`.
- The old flat legacy top-level keys (`ki:`, `ollama:`, `openai:`,
  `kicli:`, `context:`, `diff:`) have been removed from the schema and
  are no longer recognized - use the nested `llm.providers.*` /
  `apps.kicli.*` shape shown above.

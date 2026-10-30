
# KI Code Assistant

**Interactive AI-powered code generation and review tool** with Terminal UI and Tmux support.

[![Tests Passing](https://img.shields.io/badge/tests-passing-brightgreen)](#)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](#)
[![License](https://img.shields.io/badge/license-proprietary-red)](#)

---

## ✨ Features

- 🤖 **Code Generation** - Ask AI to generate, refactor, or document code
- 👁️ **Diff Preview** - Review changes before applying to files
- 💬 **Chat Interface** - Interactive TUI and Tmux layouts
- 📁 **File Browser** - Browse and load project files in context
- 🔒 **Safe Execution** - Command whitelisting and audit logging
- 🌐 **Remote Ready** - Full SSH support for remote development
- ⚙️ **Layered Config** - Environment-specific settings via ki-core
- 🧠 **Project Context** - Automatic file discovery and context loading

---

## 🚀 Quick Start

### Installation

```bash
# Setup directory structure
cd ~/dev_flow
git clone <ki-core-repo> ki-core
git clone <kicli-repo> kicli-code-assist

# Install
cd kicli-code-assist
python3 -m venv .venv
source .venv/bin/activate
pip install -e ../ki-core
pip install -e .
```

### Generate Initial Config

```bash
# Auto-generate config skeleton with all defaults
yaml-cfg config skeleton -o ki.yaml

# Edit with your settings
vim ki.yaml
```

### Run

```bash
# Terminal UI (recommended)
kicli-assist tui

# Tmux layout
kicli-assist tmux

# Simple chat
kicli-assist chat
```

---

## 📚 Documentation

### User Guides
- **[Installation Guide](doc/guides/INSTALLATION.md)** - Detailed setup instructions
- **[Chat Workflow Guide](doc/features/CHAT_WITH_FILES_WORKFLOW.md)** - Using chat with files
- **[Diff User Guide](doc/features/DIFF_USER_GUIDE.md)** - Reviewing and applying diffs
- **[File Browser Guide](doc/features/FILE_BROWSER.md)** - Browsing project files
- **[Chat History Guide](doc/features/CHAT_HISTORY_AND_PROMPTS.md)** - Session management

### Technical Reference
- **[Configuration System](doc/guides/YAML_CONFIG_SYSADMIN.md)** - Layered config setup
- **[Shared YAML configuration concepts](../yaml_cfg_wizard/doc/YAML_CONFIG_CONCEPTS.md)**
- **[Project Context](doc/guides/PROJECT_CONTEXT.md)** - Context detection and management
- **[Integration Status](INTEGRATION_STATUS.md)** - Current feature status

### Feature Status
- **[Customer Requests](doc/tracking/customer_requests.md)** - Tracked customer features
- **[Centralized Tracking](../../yaml_cfg_wizard/doc/FEATURE_STATUS.md)** - Full ecosystem status

### Legacy Documentation
- **[Archive](doc/archive/)** - Historical development phases (Phases 2-5)

---

## 🛠️ Commands

### TUI
```bash
kicli-assist tui               # Terminal UI
kicli-assist tui --provider openai  # Override provider
```

### Chat
```bash
kicli-assist chat              # Interactive chat
kicli-assist chat --model gpt-4     # Specific model
```

### Config Management
```bash
yaml-cfg config skeleton              # Generate skeleton
yaml-cfg config skeleton -o config.yaml  # Custom path

# Config inspection (via yaml-cfg-wizard)
yaml-cfg config show key
yaml-cfg config list
yaml-cfg config verify config.yaml schema.yaml
```

### System
```bash
kicli-assist doctor            # Environment diagnostics
kicli-assist openinterpreter   # Execute code with AI
kicli-assist tmux              # Tmux multi-pane layout
```

### Project server lifecycle

Assist delegates **all start/stop/restart operations to stackctl**. Open
**Tools → Servers** in the web UI, select a registered project, then inspect
live service status/logs or operate on one service/all services.

```bash
kicli-assist server --project /absolute/registered/project status
kicli-assist server --project /absolute/registered/project start -s backend
kicli-assist server --project /absolute/registered/project restart
kicli-assist server --project /absolute/registered/project stop
kicli-assist server --project /absolute/registered/project logs -s backend
```

The CLI defaults to the current directory, which must also be registered.
Discovery merges stackctl's `$XDG_STATE_HOME/stackctl/projects.json`
(`~/.local/state/stackctl/projects.json` by default), configured
`storage.project_root`, and Assist's existing `.kicli_project` markers/recent
project cache in the workspace. Only roots declaring `[tool.stackctl]` in their
own `pyproject.toml` appear in Servers or participate in aggregate status;
ordinary non-stack projects are skipped. Missing discovery files are normal,
but unreadable/malformed registries, metadata, or known project TOML produce
explicit errors rather than an apparently empty project list. A declared
stack with a missing/invalid runtime specification also produces an error.
The workspace defaults to the directory
containing the Assist checkout; override it server-side with
`storage.workspace_root`. Merely sending a path to the lifecycle API does not
register or authorize it. Assist invokes the central `~/.local/bin/stackctl`
(or `stackctl` from PATH if that user executable is absent), always with the
selected project as cwd. It never invokes a project wrapper or installs stackctl
in a project venv. The central tool loads project configuration and runs Python
services with that project's `.venv/bin/python` or `venv/bin/python`.

Assist's actual services are defined in `config/defaults/stack.yaml`:
`backend` on 8000 and the separately started, monitored Vite `frontend` on 3000.
The frontend is declared external; start it using its existing npm workflow.
Existing manually started
backend processes are recognized by command and project directory, so
`kicli-assist server stop -s backend` can stop them. No service is stopped as
part of updating this configuration. Django also defaults to 8000; configure
different ports before running both projects simultaneously.

API:

- `GET /api/server/projects` lists known project names and absolute paths.
- `GET /api/server/status?project=<registered-root>` returns live stackctl JSON
  (`project`, `root`, `target`, `services`). Without `project`, it queries known
  projects and returns combined services/counts and any per-project errors.
- `GET /api/server/logs?project=<registered-root>&service=backend` returns
  stackctl JSON logs. Repeat `service` to select multiple services.
- `POST /api/server/start`, `/stop`, `/restart` accept only
  `{"project": "/absolute/registered/root", "services": ["backend"]}`.
  Omit `services` or use `[]` for all services.

Service selections in both CLI and HTTP requests are validated against live
stackctl status. Names must begin with an ASCII letter/digit and contain only
letters, digits, `_`, `.`, or `-`; option-like/unknown names are rejected.
Clients cannot
supply commands, cwd, executable paths, targets, or environment overrides.
This integration currently supports **local targets only**, because stackctl's
JSON status/logs interface is local-only. It uses the project's configured
default target; there is no UI/API/CLI target override or automatic fallback
from `minikube`/`k8s` to local. A non-local default fails the live-status
validation before lifecycle commands execute. Configure a local target in
the project's own stack configuration to manage it here.
Status/log invocations time out after 15 seconds; lifecycle commands after
90 seconds. Nonzero exits, malformed JSON, missing executables, and timeouts
are surfaced as errors (502/503/504). A timeout does not guarantee that an
already-started background service was rolled back: refresh status before
retrying. Status distinguishes `running`, `unhealthy`, `stopped`, and `foreign`;
stackctl alone determines ownership and safe process handling.

The older `/api/server/register`, `/unregister`, `/detect-orphans`, `/cleanup`
and corresponding registry CLI commands remain **legacy bookkeeping only**.
They neither authorize project execution nor supply live stackctl status.
Their optional legacy implementation still requires ki-core; the lifecycle
bridge does not import its registry or ServiceController.

Targeted validation (including an actual isolated stackctl-managed HTTP server):

```bash
# Central ~/.local/bin/stackctl (or stackctl on PATH) must be installed.
# This interpreter supplies the isolated test project's Python environment.
STACKCTL_TEST_PYTHON=/path/to/stackctl/venv/bin/python \
  .venv/bin/python -m pytest tests/test_stackctl_bridge.py tests/test_click_cli.py \
  --basetemp=.test-stackctl
```

The live test uses an ephemeral localhost port, isolated project/state directories,
and stops its service in a `finally` block.

---

## ⚙️ Configuration

### Schema-Based System

Configuration schemas and defaults are provided via `yaml-cfg-wizard`:

1. **Base Schema** (ki-core)
   ```yaml
   ki-core/src/ki_core/schema/config.schema.yaml
   ```

2. **App Schema** (kicli-code-assist)
   ```yaml
   kicli-code-assist/schema/kicli.schema.yaml
   ```

3. **Resolution Order** (highest to lowest priority)
   - Credentials (`creds.yaml`)
   - Environment overrides (`KI_CFG_*`)
   - Runtime configuration (`config/runtime/`)
   - Selected stage (`config/stages/`)
   - Selected profile (`config/profiles/`)
   - Project config (`ki.yaml`)
   - Defaults directory (`config/defaults/`)
   - Schema defaults

### Generate Skeleton

```bash
yaml-cfg config skeleton -o ki.yaml
```

This generates a complete config file with:
- All LLM providers (OpenAI, Ollama, KI)
- Knowledge base settings
- Storage paths
- App-specific settings (context, diff, etc.)
- All defaults from merged schemas

### Edit Config

```yaml
# ki.yaml (no secrets here)
llm:
  provider: openai          # ki | openai | ollama | mock | auto
  providers:
    openai:
      base_url: https://api.openai.com/v1
      model: gpt-4o-mini

apps:
  kicli:
    context:
      max_files: 10
      cache_enabled: true
```

```yaml
# creds.yaml (project root, config/creds.yaml or ~/.config/ki/creds.yaml)
llm:
  providers:
    openai:
      api_key: <your key>
```

### Override with Environment

```bash
# Export to override config values (highest priority after creds.yaml)
export KI_CFG_LLM__PROVIDER=openai
export KI_CFG_APPS__KICLI__CONTEXT__MAX_FILES=20

kicli-assist tui  # Uses env overrides
```

### Live Settings (Web UI / TUI)

Web UI: **⚙️ Config** button or *Tools → 🛠 Konfiguration*. TUI: settings panel.
Both edit every schema field through the shared
`ki_core.runtime_settings.RuntimeSettings` service and write **only overrides** to
`config/runtime/runtime.yaml` (atomic, optimistic revision check). `ki.yaml`
is never rewritten.

Precedence: defaults → `ki.yaml` → stage → `runtime.yaml` → `KI_CFG_*` → `creds.yaml`.
Fields shadowed by `KI_CFG_*`/`creds.yaml` are shown with their source. Secrets
are never sent to the browser (only a *configured* flag). The Web UI section
*Zugangsdaten* is **write-only**: a new value (or *Entfernen*) is written to the
project-local `creds.yaml` (`config/creds.yaml` if that one is active; atomic,
mode 0600) and is live on the next request. An external/symlinked creds file
(e.g. `~/.config/ki/creds.yaml`) is not modified (503); edit it by hand.

| Applies | Paths |
|---|---|
| next request (live) | `llm.*` (provider, endpoints, models), `http.*` (timeout, TLS), `agent.*` |
| restart | everything else, e.g. `web.*`, `logging.*`, `storage.*`, `security.*`, `apps.kicli.*`, `system`, `stages`, `profiles` |
| read-only | secret values (write-only via *Zugangsdaten*), `prompts.*`, other apps (`apps.ki_knowledge`, `apps.ki_chat`, `apps.stackctl`), schema-less parts of `stack`/`services` (listed without values) |

The server re-reads the configuration when any config source changes
(fingerprint of ki.yaml, runtime.yaml, creds.yaml, config/defaults, stages,
profiles and `KI_CFG_*`), so LLM clients are rebuilt on the next request.

HTTP API (local only):

- `GET /api/settings` → `{revision, rows[], target, token, token_header}`
- `POST /api/settings` with header `X-Kicli-Settings-Token: <token>` and JSON
  `{revision, changes: {path: value}, remove: [path]}` → new snapshot plus
  `restart_required_paths`. Errors: 400 malformed, 403 access, 409 stale
  revision, 413 > 64 KiB, 415 not JSON, 422 validation, 503 store unavailable.
- `GET /api/settings/secrets` → `{revision, rows:[{path, configured,
  overridden, editable, reason, restart_required, applies}], target, token}`
  (no values, own creds revision). `POST /api/settings/secrets` (same token
  header) with exactly `{revision, path, value}` or `{revision, path,
  remove: true}`; `value` ≤ 8192 chars (blank = no-op), body ≤ 16 KiB. Returns
  the secret inventory only; same error codes as above.
- Access requires a loopback client, a local/configured `Host` and an
  `Origin`/`Referer` from `web.cors_origins` or the same origin. The token is
  random per server process. `/api/agent/config*` uses the same guard and
  persists into `agent.*`.

For scripts and probes, `kicli_code_assist.llm_runtime` provides
`chat_client(config, provider=..., model=...)`, `resolve_chat()` and
`LiveConfig(project_root).get()` (read-only, no file writes).

---

## 🧠 How It Works

### Chat Workflow

1. **Load Context** - Browse and select files to include
2. **Ask Question** - Chat with AI about your code
3. **Review Diff** - AI suggests changes (diff preview)
4. **Apply Changes** - Accept/reject modifications
5. **Iterate** - Continue conversation with updated context

### File Discovery

- Auto-discovers Python/JS/TS projects
- Respects `.gitignore` exclusions
- Intelligent relevance ranking
- Configurable context limits

### Safe Execution

- Command whitelisting (git, python, npm, etc.)
- Audit logging of all operations
- Dry-run capability
- User confirmation prompts

---

## 🔧 Development

### Project Structure

```
kicli-code-assist/
├── kicli_code_assist/
│   ├── cli.py              # CLI entrypoint
│   ├── ui/
│   │   ├── textual_app.py  # TUI implementation
│   │   └── components/     # UI components
│   ├── executor/           # Code execution
│   ├── diff/               # Diff engine
│   └── context/            # Project context
├── schema/
│   └── kicli.schema.yaml   # App-specific schema
├── config/
│   ├── defaults.yaml       # Generated defaults
│   ├── profiles/           # Profile overrides
│   └── stages/             # Stage overrides
├── doc/
│   ├── archive/            # Legacy phase docs
│   └── *.md                # Current guides
└── tests/                  # Test suite
```

### Running Tests

```bash
pytest tests/
pytest tests/ -v            # Verbose
pytest tests/test_diff.py   # Specific test
```

### Configuration for Development

```bash
# Create local dev config
yaml-cfg config skeleton

# Use local Ollama
export KI_CFG_LLM__DEFAULT_PROVIDER=ollama
export KI_CFG_OLLAMA__BASE_URL=http://localhost:11434

kicli-assist tui
```

---

## 📊 Current Status

**2 of 5 customer features complete:**
- ✅ Schema-based configuration system
- ✅ Chat history export
- 🚧 TUI focus management (partial)
- ⏳ Path security restrictions (pending)
- ⏳ Prompt templates (pending)

See [doc/tracking/customer_requests.md](doc/tracking/customer_requests.md) for details.

---

## 🔗 Related Projects

- **[ki-core](../../ki-core/)** - Configuration and LLM provider management
- **[yaml-cfg-wizard](../../yaml_cfg_wizard/)** - Config utilities and CLI
- **[ki-knowledge](../../ki-knowledge/)** - Knowledge base integration (optional)

---

## 📝 License

Proprietary - All rights reserved

---

## 🤝 Support

- **Issues:** Report via GitHub issues
- **Documentation:** See [doc/](doc/)
- **Config Help:** `kicli-assist doctor`
- **CLI Help:** `kicli-assist --help`

---

**Last Updated:** 2026-09-05  
**Version:** 0.1 (Foundation Complete)

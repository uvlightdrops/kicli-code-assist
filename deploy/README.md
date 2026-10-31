# Stack Configurations

Deploy configurations for different scenarios using stackctl.

## Variants

| File | Scenario | Frontend | Database | Use Case |
|------|----------|----------|----------|----------|
| **stack.yaml** | Default | Depends | No | Symlink (→ stack-semiprod.yaml) |
| stack-minimal.yaml | #1 Minimal | None | No | TUI-only, leanest setup |
| stack-dev.yaml | #2 Development | Vite HMR @ :5173 | No | Local dev with hot reload |
| stack-semiprod.yaml | #3 Production | Static via Flask | No | **Production default** |
| stack-full.yaml | #4 Full | Static via Flask | SQLite | Persistent storage (future) |

## Quick Start

**Development** (with HMR):
```bash
cd /path/to/kicli-code-assist
ln -sf deploy/stack-dev.yaml deploy/stack.yaml
stackctl -t local start

# Browser: http://localhost:5173 (React dev server)
# API: http://localhost:8000
```

**Production** (pre-built frontend):
```bash
cd /path/to/kicli-code-assist
cd web/frontend && npm run build  # one-time
cd ../..
ln -sf deploy/stack-semiprod.yaml deploy/stack.yaml
stackctl -t local start

# Browser: http://localhost:8000 (Flask serving static files)
# API: http://localhost:8000/api/...
```

**Minimal** (TUI only, no frontend):
```bash
cd /path/to/kicli-code-assist
ln -sf deploy/stack-minimal.yaml deploy/stack.yaml
stackctl -t local start

# API only: http://localhost:8000/api/...
```

## How Variant Switching Works

`stack.yaml` is a **symlink**. Change it to switch variants:

```bash
cd deploy
ln -sf stack-dev.yaml stack.yaml        # Development (HMR)
ln -sf stack-semiprod.yaml stack.yaml   # Production (default)
ln -sf stack-minimal.yaml stack.yaml    # TUI-only
ln -sf stack-full.yaml stack.yaml       # With database
cd ..
stackctl -t local start
```

stackctl reads `pyproject.toml` → `[tool.stackctl] spec_file = "deploy/stack.yaml"` → follows symlink.

## Frontend Build

Required for `stack-semiprod.yaml` and `stack-full.yaml`:

```bash
cd web/frontend
npm run build
# Output: kicli_code_assist/web/static/
```

Flask auto-serves these static files.

## Service Endpoints

- **API**: http://127.0.0.1:8000/api/...
- **Health**: http://127.0.0.1:8000/api/health
- **Frontend**: Depends on variant
  - Dev: http://127.0.0.1:5173/
  - Production: http://127.0.0.1:8000/

## Status & Logs

```bash
stackctl -t local status                    # Show all services
tail -f var/log/api.log                     # API logs
tail -f var/log/frontend.log                # Frontend logs (dev variant)
```

## Default Behavior

The symlink points to `stack-semiprod.yaml` for production safety.

For development, explicitly switch to `stack-dev.yaml` each time.

---

For detailed architecture and scenario explanations, see: `doc/deployment/STACK_YAML_VARIANTS.md`

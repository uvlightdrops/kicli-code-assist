---
title: Development Stack Troubleshooting Guide
project: kicli-code-assist
scope: deployment
purpose: Troubleshooting guide for development stack issues (stackctl, API, Vite frontend configuration)
created: 2026-11-02T04:10
updated: "2026-11-10 20"
update_reason: "Relocate shared documentation into doc/ and update references"
status: active
semantic_blocks: [core-problems, problem-1-env-vars, vite-solutions, quick-start, debugging-checklist]
---

# Development Stack Troubleshooting Guide

## CORE PROBLEMS IDENTIFIED (2026-11-02 04:15)

### Problem 1: Environment Variables Not Reaching Vite

**The Issue**: `vite.config.ts` reads `process.env.VITE_*` at **build/startup time**, not runtime.
- When stackctl passes `VITE_HOST=127.0.0.1` to Vite process, `process.env` in vite.config.ts is ALREADY evaluated
- Vite has `.env` & `.env.local` file support BUT only when loaded via `export` in shell OR dotenv in code
- Simply setting env vars doesn't auto-load `.env.local` into `process.env` before config reads it

**Root Cause**: Vite's config evaluation happens before `.env` loading.

**Current Fix Attempt**: `.env.local` file in frontend directory with VITE_* variables
- Does NOT work because vite.config.ts reads process.env before dotenv loads

**Correct Solution**:
1. **Option A**: Use Vite CLI flags `--host` and `--port` (bypasses config, controlled by runtime args)
   - Pro: Guaranteed to work, no file I/O needed
   - Con: Hardcoded in stack.yaml (not dynamic per stage)
   
2. **Option B**: Use shell env vars properly before Vite starts
   - Shell must `export VITE_PORT=5173` BEFORE running `npm run dev` or `vite`
   - Then vite.config.ts will read it from process.env
   - Pro: Works with .env.local file
   - Con: stackctl must properly pass env vars to child processes

3. **Option C**: Inline defaults in vite.config.ts instead of reading env
   - Hardcode `host: '127.0.0.1'` and `port: 5173` directly
   - Pro: Simple, guaranteed to work
   - Con: Not flexible for other stages (production, staging, etc.)

**Recommendation**: Combination of Option B + C
- Default in vite.config.ts: `host: '127.0.0.1'`, `port: 5173`
- Development stage can override via `.env.local` if needed
- Production stage can build with static config

---

## Quick Start (IMPORTANT: Do NOT skip KI_STAGE!)

```bash
cd /home/flow/dev_flow/kicli-code-assist
source .env.local  # Sets KI_STAGE=development + other env vars
.venv/bin/python -m stackctl -t local start
```

**Critical:** Without `KI_STAGE=development`, `config/stages/development.yaml` is NOT loaded and all services use hardcoded defaults.

### .env.local Reference

File: `.env.local` (created in project root)

```bash
export KI_STAGE=development
export FLASK_ENV=development
export FLASK_DEBUG=1
export LOG_LEVEL=DEBUG
```

This file should be sourced before every `stackctl start`. It is gitignored.

---

## Common Issues & Root Causes

### 1. Browser Cannot Reach Frontend (http://127.0.0.1:5173 returns 404 or no response)

#### Symptoms
- `curl http://127.0.0.1:5173/` returns 404 or times out
- Vite shows "ready" in logs but HTTP requests fail
- Browser shows connection refused

#### Root Cause Analysis (2026-11-02 Session)

**Problem Chain:**
1. `vite.config.ts` hardcoded `port: 3000, server: { port: 3000 }` and `target: http://localhost:8000`
2. `stack.yaml` specifies `port: 5173` but doesn't pass `--host` and `--port` CLI args to Vite
3. Vite started on port 3000 (from config file) instead of 5173 (from stackctl)
4. Vite listened on `localhost` instead of `127.0.0.1`
5. Result: Health check on `:5173` failed; HTTP requests to `:5173` got 404

**Fix Applied:**

- **`vite.config.ts`**: Read `VITE_PORT`, `VITE_HOST`, `VITE_API_URL` from environment
  ```typescript
  const port = parseInt(process.env.VITE_PORT || '3000', 10)
  const host = process.env.VITE_HOST || '127.0.0.1'
  const apiUrl = process.env.VITE_API_URL || 'http://localhost:8000'
  
  export default defineConfig({
    server: {
      host,
      port,
      strictPort: false,  // Fallback to next available port if occupied
      proxy: {
        '/api': { target: apiUrl, changeOrigin: true },
        '/socket.io': { target: apiUrl, ws: true },
      },
    },
  })
  ```

- **`config/defaults/stack.yaml`**: Pass env vars to Vite
  ```yaml
  frontend:
    env:
      VITE_API_URL: "http://127.0.0.1:8000"
      VITE_HOST: "127.0.0.1"
      VITE_PORT: "5173"
  ```

#### Verification

```bash
# Should return HTTP 200 and HTML content (not 404)
curl -v http://127.0.0.1:5173/

# Check Vite is bound to correct port
lsof -i :5173

# Check Vite logs for startup message with correct host/port
tail /home/flow/dev_flow/kicli-code-assist/var/log/frontend.log
```

**Current Status (2026-11-02 04:10)**: Vite now responds on port 5173 but returns 404. Investigation ongoing.

---

### 2. API Returns Hardcoded Port Message

#### Symptoms
```json
{
  "error": "Development mode detected",
  "message": "Use http://localhost:3000 for UI (Vite Dev Server)"
}
```

#### Root Cause
`server.py` routes had hardcoded `localhost:3000` instead of deriving from config.

#### Fix Applied (Earlier Session)

Modified `kicli_code_assist/web/server.py`:
- `index()` route: Derive `frontend_url` from config (stack.services.frontend.host:port)
- `serve_assets()` route: Same dynamic derivation

Modified `kicli_code_assist/web/server_config.py`:
- `get_cors_origins()`: 3-tier priority (explicit config → derived from stack → fallback)

#### Current Status
✅ FIXED - Message now shows correct `http://127.0.0.1:5173`

---

### 3. KI_STAGE Environment Variable Not Set

#### Symptoms
- `stackctl spec` shows default stack configuration (port 3000, localhost)
- `development.yaml` overrides are ignored
- All services use hardcoded defaults

#### Root Cause
`KI_STAGE=development` must be exported BEFORE calling Python modules. The ki_core ConfigManager reads this env var to select the active stage.

#### Fix Applied

Created `.env.local` file in project root and documented that it MUST be sourced:

```bash
source .env.local
.venv/bin/python -m stackctl -t local start
```

#### Verification

```bash
# Should show "development" stage active
echo $KI_STAGE

# Should show development.yaml values in merged config
.venv/bin/python -m stackctl -t local spec | grep -A 10 "services:"
```

---

### 4. Old Vite/API Processes Still Running

#### Symptoms
- `stackctl status` shows "running" but curl requests fail
- Code changes don't take effect
- New environment variables not applied

#### Solution

Always kill old processes before restart:

```bash
ps aux | grep -E "python -m kicli_code_assist|vite" | grep -v grep | awk '{print $2}' | xargs kill -9

# Then restart
cd /home/flow/dev_flow/kicli-code-assist
source .env.local
.venv/bin/python -m stackctl -t local start
```

Or simpler - use stackctl stop:

```bash
.venv/bin/python -m stackctl -t local stop
sleep 2
source .env.local
.venv/bin/python -m stackctl -t local start
```

---

## Service Health Checks

### API (Flask)
```bash
curl -s http://127.0.0.1:8000/api/health | jq .
# Should return 200 with health status

curl -s http://127.0.0.1:8000/ | jq .
# Should show message pointing to :5173 (not :3000)
```

### Frontend (Vite)
```bash
curl -I http://127.0.0.1:5173/
# Should return 200 OK (not 404)

curl http://127.0.0.1:5173/ | head -20
# Should return HTML with <div id="root"></div>
```

### Process Status
```bash
ps aux | grep -E "python -m kicli|vite" | grep -v grep

lsof -i :8000  # API port
lsof -i :5173  # Frontend port
```

### Log Files
```bash
tail -f /home/flow/dev_flow/kicli-code-assist/var/log/api.log
tail -f /home/flow/dev_flow/kicli-code-assist/var/log/frontend.log
```

---

## Configuration Files Reference

| File | Purpose | Key Section | Last Updated |
|------|---------|-------------|--------------|
| `config/defaults/stack.yaml` | Base stack config (ports, commands) | `services.api` / `services.frontend` | 2026-11-02 04:10 |
| `config/stages/development.yaml` | Stage-specific overrides | `web.cors_origins`, env vars | 2026-11-01 (filled) |
| `web/frontend/vite.config.ts` | Vite configuration | `server: { host, port, proxy }` | 2026-11-02 04:10 |
| `kicli_code_assist/web/server_config.py` | Flask config loading | `get_cors_origins()`, `get_web_settings()` | 2026-11-01 (enhanced) |
| `kicli_code_assist/web/server.py` | Flask routes | `index()`, `serve_assets()` | 2026-11-01 (fixed) |
| `.env.local` | Startup environment | All exports | 2026-11-02 04:09 (created) |

---

## Next Investigation Steps

1. ✅ Fix Vite config to read env vars (DONE)
2. ✅ Fix stack.yaml to pass env vars (DONE)
3. ⏳ Verify Vite actually serves `index.html` on `/` (returns 200)
4. ⏳ Test React app loads in browser
5. ⏳ Test API→Frontend communication (CORS, HMR)
6. ⏳ Test hot-reload functionality

---

## Cross-References

- **ki-ecosystem** deployment patterns: `ki-ecosystem/doc/DEPLOYMENT_*.md`
- **Canonical deployment standards**: `dev_doc/doc/DEPLOYMENT_STANDARDS.md`
- **Consolidation strategy**: `doc/deployment/CONSOLIDATION_STRATEGY.md`
- **stackctl architecture**: `stackctl/doc/README.md` + `stackctl/doc/ARCHITECTURE.md`

---

**Last Verified**: 2026-11-02 04:10:45 UTC  
**By**: Copilot (kicli-code-assist agent)  
**Status**: Investigation in progress - Vite now responds on correct port but returns 404
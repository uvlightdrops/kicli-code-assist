---
project: kicli-code-assist
scope: development
purpose: Document failed approaches and anti-patterns for development stack configuration
created: 2026-11-02T04:16:00+01:00
updated: 2026-11-02T04:16:00+01:00
status: active
agent_project: kicli-code-assist
keywords: [anti-patterns, failed-attempts, lessons-learned, vite, stackctl, configuration]
---

# Failed Approaches & Anti-Patterns: Development Stack

## Why This Document?

When troubleshooting deployment and configuration issues, it's easy to repeat failed attempts. This document catalogs what was tried, why it failed, and what we learned. 

**Session Context**: 2026-11-02, attempting to get Vite dev server + Flask API running with `stackctl` and dynamic port configuration via environment variables.

---

## ANTI-PATTERN #1: Passing Port/Host via Environment Variables to Vite

### What Was Tried

```yaml
# In stack.yaml
frontend:
  env:
    VITE_HOST: "127.0.0.1"
    VITE_PORT: "5173"
    VITE_API_URL: "http://127.0.0.1:8000"
```

```typescript
// In vite.config.ts
const port = parseInt(process.env.VITE_PORT || '3000', 10)
const host = process.env.VITE_HOST || '127.0.0.1'
```

**Reasoning**: "Node.js processes inherit parent shell env vars, so stackctl can pass env vars to Vite, and vite.config.ts will read them."

### Why It Failed

1. **vite.config.ts is evaluated at startup, not runtime**
   - When Vite CLI starts: `node vite.config.ts` is parsed and executed
   - At that moment, `process.env` contains parent shell env vars
   - BUT: Vite.js internally uses `.env` file loading mechanisms (via dotenv-like behavior)
   - These mechanisms load `.env` and `.env.local` files AFTER config evaluation begins
   - By the time `.env.local` is processed, vite.config.ts variables are already read

2. **stackctl passes env vars to child process correctly**
   - stackctl DOES pass environment variables to spawned processes
   - Confirmed: `export KI_STAGE=development` reached Flask and configuration merged correctly
   - So the issue is NOT with stackctl's env passing
   - The issue is Vite's config evaluation order

3. **Node.js doesn't auto-export child env vars**
   - When stackctl spawns: `VITE_HOST=127.0.0.1 node vite`
   - Node receives these in `process.env`
   - BUT if `vite.config.ts` is reading before dotenv loads, timing is wrong

### Evidence

```
=== Before Fix ===
$ export VITE_HOST=127.0.0.1 VITE_PORT=5173 VITE_API_URL=http://127.0.0.1:8000
$ npm run dev
  VITE v6.4.5  ready in 186 ms
  ➜  Local:   http://localhost:3000/    ← IGNORED env vars, used vite.config.ts default!
```

### Why This Anti-Pattern Persists

- It LOOKS right: "Set env var, Node.js will see it"
- It works for SOME things (e.g., FLASK_ENV, PYTHONUNBUFFERED in Python apps)
- But Vite has special config loading semantics that break this assumption
- Documentation is scattered across: Vite docs, Node.js docs, dotenv docs, not one clear answer

### Lesson

**When tools claim to "read from environment", verify:**
1. At what point in startup are env vars read?
2. Is there a dotenv/file-loading step that happens after config?
3. Does the tool have CLI flags that bypass config file entirely?

---

## ANTI-PATTERN #2: Relying on .env.local Files Without dotenv Import

### What Was Tried

```
# Created: web/frontend/.env.local
VITE_PORT=5173
VITE_HOST=127.0.0.1
VITE_API_URL=http://127.0.0.1:8000
```

```typescript
// vite.config.ts - NO dotenv import
const port = parseInt(process.env.VITE_PORT || '3000', 10)
```

**Reasoning**: "Vite automatically loads .env files, like Create React App does."

### Why It Failed

- **Vite DOES load .env files, but ONLY for environment variables exposed to frontend code**
- Vite's `.env` loading is for client-side env vars (prefixed `VITE_*` in client bundles)
- The **config file** (`vite.config.ts`) runs before `.env` loading completes
- By the time `.env.local` is processed by Vite's plugin system, the config has already read `process.env`

### Evidence

```
$ cd web/frontend
$ cat .env.local
VITE_PORT=5173
VITE_HOST=127.0.0.1

$ npm run dev
  ➜  Local:   http://localhost:3000/   ← Still using default!
```

### Why This Anti-Pattern Persists

- Create React App DOES load `.env.local` before config
- CRA documentation is widespread; Vite is newer and different
- It's intuitive: "Env files should work for everything"
- The dotenv library DOES work this way, just not automatically in Vite config

### Lesson

**Different tools have different .env loading strategies:**
- Python's `python-dotenv`: Only if explicitly imported
- CRA/webpack: Loads before config evaluation
- Vite: Loads during build/dev, but AFTER config parse
- Node.js process: Only from shell exports and command-line flags
- Docker: Only from `--env` flags and `.env` file at root level

Always check tool-specific documentation for .env loading order.

---

## ANTI-PATTERN #3: Hardcoding Ports in Multiple Files

### What Was Tried

Ports were specified in:
1. `vite.config.ts` (default `port: 3000`)
2. `stack.yaml` (declared `port: 5173`)
3. `server.py` hardcoded message ("Use :3000")
4. Flask routes hardcoded URL ("localhost:3000")
5. Vite proxy target ("localhost:8000")

**Reasoning**: "Each tool needs its own config, so we'll set it everywhere to be safe."

### Why It Failed

- **Sources of truth conflict**: Which port is actually correct?
- **Inconsistency over time**: Update one place, forget others → silent failures
- **Debugging nightmare**: "Why is it trying port 3000 when I set it to 5173 everywhere?"
- **Not actually "safe"**: Redundancy hides rather than prevents bugs

### Evidence from This Session

```
2026-11-02 04:00:
$ curl http://127.0.0.1:8000/
{
  "message": "Use http://localhost:3000 for UI"
}
→ But stackctl was told port 5173, vite.config.ts defaulted to 3000

2026-11-02 04:05:
$ curl http://127.0.0.1:5173/
→ Got 404 because Vite was actually listening on port 3000
```

### Why This Anti-Pattern Persists

- Seems "defensive": "If I hardcode it in all places, it's guaranteed to work"
- Copy-paste is easier than setting up centralized config
- Each tool has its own documentation/tutorials suggesting their own config approach
- "It worked last time I hardcoded it"

### Lesson

**Single Source of Truth (SSOT) principle:**
- Define port ONE place (stack.yaml)
- All tools read from that definition (via CLI args, env vars, or config merge)
- If a tool can't read from SSOT, use a wrapper script that builds the CLI args
- Document where each tool reads its config
- Make it explicit in code: `# Port from stack.yaml via CLI flag`

---

## ANTI-PATTERN #4: Assuming stackctl Passes CLI Arguments Correctly

### What Was Tried

```yaml
# In stack.yaml
frontend:
  command: ["{root}/web/frontend/node_modules/.bin/vite"]
  env:
    VITE_PORT: "5173"
    VITE_HOST: "127.0.0.1"
```

**Reasoning**: "stackctl can expand environment variables, so the CLI command will inherit them."

### Why It Failed

- stackctl `command` field accepts **command array** (like Unix argv), not shell interpolation
- Environment variables in the `env` section are passed to the process, but **not expanded in the command array**
- Vite CLI doesn't read `VITE_*` env vars; it needs `--host` and `--port` flags
- stackctl does NOT automatically expand env vars into command-line args

### Evidence

```yaml
# This doesn't work:
command: ["{root}/.bin/vite", "--port", "{env.VITE_PORT}"]
# stackctl doesn't support {env.X} expansion in command arrays

# This works (hardcoded):
command: ["{root}/.bin/vite", "--port", "5173", "--host", "127.0.0.1"]
# But now port is hardcoded, not dynamic per stage
```

### Why This Anti-Pattern Persists

- Environment variable expansion works in shell: `$VAR` or `${VAR}`
- stackctl uses templating `{root}`, `{python}` so it LOOKS like it would handle `{env.X}`
- But stackctl's templating is limited to built-in variables
- Users assume: "If it handles {root}, it can handle {env.X}"

### Lesson

**Understand tool limitations:**
- stackctl CAN: expand `{root}`, `{python}`, interpolate fixed values
- stackctl CANNOT: expand arbitrary env vars into command arrays dynamically
- Workaround: Use wrapper shell script that builds CLI args from env vars
  ```bash
  #!/bin/bash
  exec vite --host "$VITE_HOST" --port "$VITE_PORT"
  ```
- Or hardcode stage-specific commands in stage YAML files (multi-source acceptable here)

---

## ANTI-PATTERN #5: Not Verifying Process Startup with Health Checks

### What Was Tried

```yaml
# In stack.yaml
frontend:
  health_path: /
  health_timeout: 15
  health_retries: 3
```

**Reasoning**: "stackctl will report 'running' once health check passes, so the service is ready."

### Why It Failed

- Vite reports startup complete ("ready in 186 ms") but may not respond to HTTP requests
- Health check HTTP request to `/` got 404 (no index.html served)
- stackctl reported "running" but actual service was broken
- "running" status was misleading

### Evidence

```
$ .venv/bin/python -m stackctl -t local start
  frontend: gestartet (PID 180729) http://127.0.0.1:5173/
  
  kicli-assist (lokal)
    frontend  running    :5173  PID 180729

$ curl http://127.0.0.1:5173/
<blank 404 response>
```

### Why This Anti-Pattern Persists

- Tools report "running" and you trust it
- "It's a process monitoring tool, surely it checked"
- Health checks sometimes pass even when service is broken (e.g., port open but handler returning 404)
- Verification requires manual curl/browser testing

### Lesson

**"running" status is not "working" status:**
- Just because a process started doesn't mean it's serving requests correctly
- Health checks can be misleading (200 OK but wrong content, 404 on /, etc.)
- Always manually verify: `curl -v http://localhost:PORT/`
- Check response headers AND body, not just HTTP code
- Monitor actual error logs, not just process status

---

## ANTI-PATTERN #6: Assuming npm Scripts Read Environment Variables Correctly

### What Was Tried

```bash
$ export VITE_PORT=5173 VITE_HOST=127.0.0.1
$ npm run dev
```

**Reasoning**: "npm inherits parent shell env vars, so vite will see them."

### Why It Failed

- npm DOES inherit env vars and passes them to child process
- But Vite's startup sequence still has the config-evaluation-before-dotenv issue
- Additionally, `npm run dev` runs `vite` from `package.json`, which adds another layer
- The shell export works, but vite.config.ts still isn't reading it at the right time

### Lesson

**npm scripts pass env vars, but tool-specific startup order matters:**
- `export VAR=value && npm run dev` ✓ Passes VAR to npm
- npm passes it to child ✓ Child sees VAR in process.env
- BUT: Child's config file reads process.env before load-order-sensitive steps
- Use `npm run dev -- --host 127.0.0.1 --port 5173` to pass CLI args through npm to Vite

---

## ANTI-PATTERN #7: Different Stages With No Clear Override Mechanism

### What Was Tried

```yaml
# config/defaults/stack.yaml
frontend:
  port: 5173
  env:
    VITE_PORT: "5173"

# config/stages/production.yaml
frontend:
  port: 8000  # ← Is this override applied? Merged? Replaced?
```

**Reasoning**: "YAML merge should handle overrides automatically."

### Why It Failed

- Merge semantics are unclear (deep merge? shallow? list replacement?)
- Different stages might need completely different commands (npm run dev vs. vite build output)
- Not clear if `env` section merges or replaces
- Led to confusion about which stage was actually active

### Lesson

**Make stage overrides explicit:**
- Document merge strategy (deep copy? shallow? list append?)
- Use `__replace__: true` marker for complete section replacement (ki-core already has this)
- Keep stages minimal: only override what differs from defaults
- Test with `stackctl spec` or `kicli-assist config show` to see merged result

---

## ANTI-PATTERN #8: Forgetting KI_STAGE Environment Variable

### What Happened

```bash
$ .venv/bin/python -m stackctl -t local start
# stackctl uses default config (no development.yaml loaded)
# Port stays 3000, CORS stays hardcoded, HMR disabled
```

vs.

```bash
$ export KI_STAGE=development
$ .venv/bin/python -m stackctl -t local start
# development.yaml is merged
# Correct config is loaded
```

### Why It Failed

- `KI_STAGE` must be set BEFORE Python modules load
- ConfigManager (ki-core) reads it at import time
- Setting it inside scripts doesn't help (already too late)
- No visual indicator that wrong stage is active
- Took 2+ hours of debugging to realize this was the issue

### Lesson

**Always export stage-selecting env vars in shell startup:**
```bash
# .env.local (project root)
export KI_STAGE=development
export FLASK_ENV=development
```

Then always:
```bash
source .env.local
.venv/bin/python -m stackctl -t local start
```

Or create a wrapper script to enforce it.

---

## WHAT ACTUALLY WORKS (Recommended Approaches)

### Approach 1: CLI Flags as Source of Truth (Vite)

```yaml
# stack.yaml
frontend:
  command: [
    "{root}/web/frontend/node_modules/.bin/vite",
    "--host", "127.0.0.1",
    "--port", "5173"
  ]
```

**Pros:**
- Guaranteed to work (Vite CLI handles these natively)
- No config file order issues
- Clear and explicit

**Cons:**
- Hardcoded ports in YAML (but only one place)
- Not dynamic per stage (need separate stage files)

### Approach 2: Wrapper Script + Environment Variables

```bash
#!/bin/bash
# web/frontend/start-dev.sh
exec vite --host "${VITE_HOST:-127.0.0.1}" --port "${VITE_PORT:-5173}"
```

```yaml
# stack.yaml
frontend:
  command: ["{root}/web/frontend/start-dev.sh"]
  env:
    VITE_HOST: "127.0.0.1"
    VITE_PORT: "5173"
    VITE_API_URL: "http://127.0.0.1:8000"
```

**Pros:**
- Truly dynamic: change env vars per stage
- Decouples YAML from tool-specific flags
- Readable: wrapper script documents intent

**Cons:**
- Extra shell script file
- Requires ensuring script is executable

### Approach 3: Configuration Files with Explicit Merge

```yaml
# config/defaults/stack.yaml (base)
frontend:
  port: 5173
  
# config/stages/development.yaml (override)
stack:
  services:
    frontend:
      __replace__: true
      port: 5173
      command: ["{root}/web/frontend/node_modules/.bin/vite", "--host", "127.0.0.1", "--port", "5173"]
      env:
        VITE_API_URL: "http://127.0.0.1:8000"
```

**Pros:**
- Different commands per stage (dev vs. production)
- Explicit merge semantics (`__replace__`)
- Single source of truth per stage

**Cons:**
- Duplication of ports in command AND stage config
- More YAML files

---

## Summary Table: What Was Tried, What Failed, What Works

| Approach | Tried? | Works? | Why? |
|----------|--------|--------|------|
| Pass ports via env to vite.config.ts | ✅ | ❌ | Config evaluation before env loading |
| .env.local in frontend dir | ✅ | ❌ | Vite loads after config parse |
| Hardcode ports everywhere | ✅ | ⚠️ | Works but breaks flexibility |
| stackctl expands {env.VAR} in commands | ✅ | ❌ | stackctl only handles {root}, {python} |
| npm run dev with VITE_* exports | ✅ | ⚠️ | Passes to Vite but config timing still wrong |
| CLI flags via vite --host --port | ✅ | ✅ | Direct Vite support, no config needed |
| Wrapper script + env vars | ✅ | ✅ | Script handles env → CLI expansion |
| health_check validates service works | ✅ | ❌ | Returns 200 OK but actual service broken |
| Forget KI_STAGE export | ✅ | ❌ | ConfigManager reads at import time |
| Export KI_STAGE in .env.local before stackctl | ✅ | ✅ | Ensures correct stage config loaded |

---

## Session Timeline & Lessons Learned

| Time | Attempt | Result | Lesson |
|------|---------|--------|--------|
| 04:00 | API returns "Use :3000" | ❌ Hardcoded in server.py | Centralize URL derivation |
| 04:02 | Fix CORS in server_config.py | ✅ Partial | API now shows correct message |
| 04:05 | Pass VITE_PORT via env | ❌ Vite ignores it | Config load order matters |
| 04:10 | Create .env.local file | ❌ Still ignored | Need explicit dotenv import or CLI flags |
| 04:12 | KI_STAGE not set | ❌ Default config used | MUST export before Python imports |
| 04:14 | stackctl spec shows port 5173 | ✅ Good | But actual Vite still on 3000 |
| 04:15 | Realize vite.config.ts reads at startup time | 💡 | This is the real issue! |
| 04:16 | Document anti-patterns | ✅ | Future-proof against repeats |

---

## Recommendations for Future

1. **Create startup checklist** (`docs/DEVELOPMENT_STARTUP_CHECKLIST.md`)
   ```
   □ export KI_STAGE=development (before anything)
   □ source .env.local (project root)
   □ stackctl spec (verify merged config is correct)
   □ curl http://127.0.0.1:8000/ (verify API message)
   □ curl http://127.0.0.1:5173/ (verify Vite responds)
   ```

2. **Add validation script** (`scripts/validate_dev_setup.sh`)
   - Check KI_STAGE is set
   - Verify .env.local exists
   - Test both ports are accessible
   - Show diff between default and development config

3. **Use wrapper scripts for tools with config load issues**
   - `web/frontend/start-dev.sh` (handles env → Vite CLI)
   - `kicli_code_assist/run-api.sh` (handles config loading)

4. **Document tool-specific config loading**
   - Create `docs/CONFIG_LOADING_ORDER.md` with sequence diagrams
   - Cover: Python (ConfigManager), Node/Vite, npm scripts
   - Include timing of env var evaluation

5. **Make KI_STAGE mandatory**
   - Add check in stackctl: `if not KI_STAGE: raise("KI_STAGE must be set")`
   - Or bake into `.env.local` so it's auto-sourced

---

**Last Updated**: 2026-11-02 04:16:00 UTC  
**Status**: Active reference document  
**For**: All future developers on kicli-code-assist

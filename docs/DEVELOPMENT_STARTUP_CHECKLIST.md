---
project: kicli-code-assist
scope: development
purpose: Step-by-step checklist for reliable development stack startup
created: 2026-11-02T04:18:00+01:00
updated: 2026-11-02T04:18:00+01:00
status: active
agent_project: kicli-code-assist
---

# Development Stack Startup Checklist

Use this checklist **every time** you start the development environment.

## Pre-Flight (Before Starting)

- [ ] Terminal window open in: `/home/flow/dev_flow/kicli-code-assist`
- [ ] Run: `pwd` to confirm correct directory
- [ ] Check Python venv exists: `ls -la .venv/bin/python`

## Step 1: Set Environment

```bash
export KI_STAGE=development
```

Verify:
```bash
echo $KI_STAGE
# Should output: development
```

**Why**: ConfigManager (ki-core) reads `KI_STAGE` at import time. Without it, default config is used and all development.yaml overrides are ignored.

---

## Step 2: Stop Old Services (Clean Slate)

```bash
.venv/bin/python -m stackctl -t local stop
sleep 2
```

Verify no old processes:
```bash
ps aux | grep -E "vite|python -m kicli_code_assist" | grep -v grep
# Should return NOTHING (empty)
```

**Why**: Old processes can block ports or serve stale code. Always start clean.

---

## Step 3: Start Services

```bash
.venv/bin/python -m stackctl -t local start
```

Expected output:
```
api: gestartet (PID XXXXX) http://127.0.0.1:8000/api/health
  frontend: gestartet (PID XXXXX) http://127.0.0.1:5173/

kicli-assist (lokal)
  api       running    :8000  PID XXXXX
  frontend  running    :5173  PID XXXXX
```

Wait 6-8 seconds for services to fully boot.

---

## Step 4: Verification Tests

### 4A: API Health Check

```bash
curl -s http://127.0.0.1:8000/api/health | jq .
```

Expected output:
```json
{
  "status": "ok",
  "uptime": 2.5
}
```

**If fails**: See section "Troubleshooting: API Not Responding"

---

### 4B: API Root Message

```bash
curl -s http://127.0.0.1:8000/ | jq .
```

Expected output:
```json
{
  "error": "Development mode detected",
  "message": "Use http://127.0.0.1:5173 for UI (Vite Dev Server)",
  "production_usage": "Set FLASK_ENV=production to serve static builds from this port"
}
```

**Must contain**: `:5173` (not `:3000`, not `localhost`)

**If fails**: See section "Troubleshooting: Wrong Port in Message"

---

### 4C: Vite Frontend

```bash
curl -I http://127.0.0.1:5173/
```

Expected output:
```
HTTP/1.1 200 OK
Vary: Origin
Content-Type: text/html
```

**Must be**: HTTP 200, not 404 or connection refused

**If fails**: See section "Troubleshooting: Vite Not Responding"

---

### 4D: Browser Load Test (Optional)

Open in browser: `http://127.0.0.1:5173/`

- [ ] Page loads without errors
- [ ] React app renders (not blank page)
- [ ] Browser console has no red errors
- [ ] Logo/header visible

Press F12 to open Developer Tools → Console tab.

---

## Step 5: Inspect Logs (If Anything Failed)

```bash
# Watch API logs
tail -f var/log/api.log

# In another terminal, watch Frontend logs
tail -f var/log/frontend.log
```

**Common issues in logs:**
- `ModuleNotFoundError`: Missing dependency
- `Port already in use`: Old process still running
- `Connection refused`: Service didn't start
- `404 Not Found`: Vite config issue

---

## Success Indicators

✅ All verification tests passed
✅ No errors in logs
✅ Browser loads React app
✅ Network tab shows API calls succeeding

---

## Troubleshooting Quick Links

| Issue | Solution |
|-------|----------|
| "KI_STAGE not set" error | Run: `export KI_STAGE=development` |
| API not responding (:8000) | Check: `tail -f var/log/api.log` for errors |
| Vite not responding (:5173) | Check: `ps aux \| grep vite` (is it running?) |
| "Port already in use" | Run: `lsof -i :8000` and `lsof -i :5173` to see what's holding them |
| Browser shows blank page | Check browser console (F12) for JS errors |
| API message says ":3000" | Wrong stage loaded; verify `echo $KI_STAGE` |

For detailed troubleshooting, see: `doc/deployment/DEVELOPMENT_STACK_TROUBLESHOOTING.md`

For understanding why things fail, see: `doc/deployment/ANTI_PATTERNS_FAILED_APPROACHES.md`

---

## One-Line Quick Start (After First Setup)

```bash
cd /home/flow/dev_flow/kicli-code-assist && export KI_STAGE=development && .venv/bin/python -m stackctl -t local stop 2>/dev/null; sleep 2; .venv/bin/python -m stackctl -t local start
```

Then run validation:
```bash
./scripts/validate_dev_setup.sh
```

---

**Last Updated**: 2026-11-02 04:18:00 UTC  
**Status**: Ready to Use  
**Next Step**: Use this checklist before every development session

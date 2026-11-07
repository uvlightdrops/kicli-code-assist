---
title: HOT RELOAD DEV
project: kicli-code-assist
scope: guides
purpose: Development guide for enabling hot-reload during local development
created: 2026-10-18T18:12:45+01:00
updated: 2026-11-07T17:10:00+01:00
update_reason: Applied semantic block tagging skill - added block IDs to H2 headings
semantic_blocks:
  - id: problem
    title: Problem
  - id: solution-separate-llm-service
    title: Solution: Separate LLM Service
  - id: how-it-works
    title: How It Works
  - id: workflow-make-change-test-without-rest
    title: Workflow: Make Change → Test Without Restart
  - id: api-endpoints
    title: API Endpoints
  - id: configuration
    title: Configuration
  - id: troubleshooting
    title: Troubleshooting
  - id: when-to-use
    title: When to Use
  - id: future-auto-reload
    title: Future: Auto-Reload
status: active
---

# Hot-Reload Development Guide

## Problem [problem]
Mit jeder Änderung an `ai_workflow.py`, `llm_integration.py` etc., musste die ganze TUI neu gestartet werden.
Das ist **zeitaufwändig** beim Debugging.

## Solution: Separate LLM Service [solution-separate-llm-service]

Starte den LLM Service als **separaten Prozess**:

```bash
# Terminal 1: Start LLM Service
bash scripts/dev/llm_service.sh

# Terminal 2: Start TUI (connects to service)
kicli-assist tui
```

## How It Works [how-it-works]

1. **LLM Service** (Port 9001) läuft unabhängig
   - Handles all LLM queries
   - Can be reloaded WITHOUT restarting TUI

2. **TUI** connects to service via HTTP
   - Sends queries to `/query` endpoint
   - Receives responses
   - Can trigger service reload when needed

## Workflow: Make Change → Test Without Restart [workflow-make-change-test-without-rest]

```bash
# Terminal 1: Service running
python -m kicli_code_assist.services.llm_service

# Terminal 2: Edit code (e.g., llm_integration.py)
vim kicli_code_assist/llm_integration.py

# Terminal 3: Reload service (keep TUI running!)
curl -X POST http://127.0.0.1:9001/reload

# Terminal 2: Test change in TUI (still running!)
# Activate AI Suggestions checkbox → service returns new code
```

## API Endpoints [api-endpoints]

### Health Check
```bash
curl http://127.0.0.1:9001/health
```

### Query LLM
```bash
curl -X POST http://127.0.0.1:9001/query \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello"}
    ],
    "system_prompt": "You are helpful"
  }'
```

### Reload Service
```bash
curl -X POST http://127.0.0.1:9001/reload
```

## Configuration [configuration]

Default: `127.0.0.1:9001`

Custom port:
```bash
python -m kicli_code_assist.services.llm_service --port 9999
```

## Troubleshooting [troubleshooting]

### Service won't start
```bash
# Check dependencies
pip install fastapi uvicorn httpx pydantic
```

### Can't connect from TUI
```bash
# Verify service is running
curl http://127.0.0.1:9001/health

# Check logs in service terminal
```

### Changes not applied
Make sure to call `/reload` after editing code:
```bash
curl -X POST http://127.0.0.1:9001/reload
```

## When to Use [when-to-use]

✅ **Use Service for:**
- Developing `ai_workflow.py` (suggestions logic)
- Developing `llm_integration.py` (provider handling)
- Testing ResponseParser changes
- Iterating on LLM prompt engineering

❌ **Don't Use Service for:**
- UI Layout changes (need full TUI restart anyway)
- Widget hierarchy changes
- CSS/styling changes

## Future: Auto-Reload [future-auto-reload]

Could add file watcher that auto-reloads service on code change:
```bash
python -m kicli_code_assist.services.llm_service --watch
```

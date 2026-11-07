---
project: kicli-code-assist
scope: guides
created: 2026-11-05 16
updated: 2026-11-07T17:10:00+01:00
update_reason: Applied semantic block tagging skill - added block IDs to H2 headings
status: current
semantic_blocks:
  - id: motivation
    title: Motivation
  - id: installation
    title: Installation
  - id: usage
    title: Usage
  - id: controls
    title: Controls
  - id: workflow
    title: Workflow
  - id: example-session
    title: Example Session
  - id: architecture-diagram
    title: Architecture Diagram
  - id: troubleshooting
    title: Troubleshooting
  - id: advanced
    title: Advanced
  - id: next-steps
    title: Next Steps
agent_project: kicli-code-assist
---

# TUI Client Quick Start

## Motivation [motivation]
The Terminal User Interface (TUI) enables agent-driven code analysis on **jump hosts without GUI access**, using the same backend as the web UI. Ideal for K8s cluster management nodes where graphical browsers are unavailable.

## Installation [installation]

No extra installation needed—TUI is built into kicli-code-assist:

```bash
cd /path/to/kicli-code-assist
pip install -e .
```

Verify dependencies:
```bash
python3 -c "import textual; import httpx; import rich; print('✅ All OK')"
```

## Usage [usage]

### Local Development
```bash
# Start backend (from ki-ecosystem or project root)
.venv/bin/python -m stackctl start

# In another terminal, launch TUI
kicli-assist tui --project /path/to/project

# Or use current directory
kicli-assist tui
```

### Remote K8s Cluster
```bash
# From jump host, point to your production backend
kicli-assist tui \
  --project /path/to/repo \
  --api-url http://prod-backend.internal:8000
```

## Controls [controls]

| Key | Action |
|-----|--------|
| `F1` | Focus project tree (select file) |
| `F2` | Focus output panel (view results) |
| `F7` | Focus input field (type request) |
| `Enter` | Submit request |
| `Escape` | Clear input |
| `h` | Show help |
| `q` | Quit |

## Workflow [workflow]

1. **Select File** (F1): Navigate project tree, click file
2. **Enter Request** (F7): Type analysis request
   - "Analyze for performance issues"
   - "Refactor this function"
   - "Explain what this does"
3. **View Results** (F2): Watch real-time reasoning trace
4. **Review Output**: Syntax-highlighted code, metrics, suggestions

## Example Session [example-session]

```
Project Tree          │ Output Panel
━━━━━━━━━━━━━━━━━━━  │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 src/              │ Code Explanation
├─ main.py ◄─ SELECT │ ┌──────────────────────────┐
├─ utils.py          │ │ main() orchestrates...   │
└─ lib/              │ │                          │
                      │ │ def main():              │
                      │ │     initialize_system()  │
                      │ └──────────────────────────┘
                      │ Metrics:
                      │ • Complexity: 3/10
Input (F7)            │ • Maintainability: 8/10
━━━━━━━━━━━━━━━━━━━  │
> Refactor this function for clarity
[Send]                Status: ✅ Ready
```

## Architecture Diagram [architecture-diagram]

```
TUI Client (Your Terminal)
    │
    ├─► HTTP POST /api/agent/route
    │   └─ Project path, file, request
    │
    ├─► Parse JSON-L response stream
    │   └─ Reasoning events, code blocks, metrics
    │
    └─► Display via Textual + Rich
        └─ Syntax highlighting, tables, panels

Backend (localhost:8000 or remote)
    │
    ├─► CodeImplementationAgent
    ├─► MetaCoordinationAgent  
    ├─► ReasoningTracer (Phase 5.5.2)
    └─► LLM API
```

## Troubleshooting [troubleshooting]

### Backend Unreachable
```
❌ Cannot reach backend at http://localhost:8000
```
**Fix**: Ensure backend is running:
```bash
.venv/bin/python -m stackctl start
```

For remote backend, use `--api-url`:
```bash
kicli-assist tui --api-url http://my-backend:8000
```

### No Files Shown
**Problem**: Project tree is empty
- Verify `--project` path exists
- Check file permissions
- Project scanner respects `.gitignore`

### Slow Response
**Problem**: TUI hangs after submission
- Check backend logs: `tail -f log/kicli.log`
- Verify LLM provider configured: `echo $OPENAI_API_KEY`
- For large files, expect 5-10s processing time

## Advanced [advanced]

### Custom Configuration
Set environment variables before launch:

```bash
export TUI_API_URL="http://prod-backend:8000"
export TUI_MAX_LINES="1000"  # Output buffer size
export PYTHONUNBUFFERED=1    # Real-time logging

kicli-assist tui --project /code
```

### Logs
TUI logs to stderr (terminal) + file:
```bash
tail -f log/kicli.log          # Backend logs
tail -f log/kicli-llm.log      # LLM calls
```

### SSH Tunneling (for remote backend)
```bash
# On your local machine
ssh -L 8000:backend.internal:8000 jump-host

# Then on jump host
kicli-assist tui --api-url http://localhost:8000
```

## Next Steps [next-steps]

- **Integration Test**: See TUI_CLIENT_IMPLEMENTATION_PLAN.md Phase 4
- **WebSocket Streaming**: Real-time event updates (Phase 5)
- **Automation**: Batch requests from shell scripts

## Related Docs

- Architecture: `/doc/architecture/AGENT_ORCHESTRATION_ARCHITECTURE.md`
- Backend API: `/doc/guides/API_REFERENCE.md` (WIP)
- Phase 5 Agents: `/doc/phases/PHASE_5_3_SUMMARY.md`
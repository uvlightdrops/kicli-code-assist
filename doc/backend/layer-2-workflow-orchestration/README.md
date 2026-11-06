---
title: "Layer 2: Workflow Orchestration Layer"
project: kicli-code-assist
scope: backend
type: architecture
status: active
created: 2026-11-06T10:25:00+01:00
updated: 2026-11-06T10:25:00+01:00
update_reason: Initial layer structure documentation
cross_references:
  - ../layer-1-raw-llm/README.md
  - ../layer-3-autonomous-agent/README.md
  - ../../phases/PHASE_5_1_SUMMARY.md
---

# Layer 2: Workflow Orchestration Layer

Structured 6-stage pipeline that wraps Layer 1 primitives into meaningful workflows.

## Scope

- Intent detection (what does the user really want?)
- Workflow routing (which workflow to execute?)
- Agent selection (which agents can help?)
- Multi-agent execution (run agents in parallel/sequence)
- Response aggregation (combine results)
- Answer generation (format for user)
- Session management & state
- Chunk standardization (🔍 observation, ⚠️ issue, 💡 solution, ✅ impact, ℹ️ info)
- Error handling & fallback strategies

## Who Uses This?

- **TUI clients** call this via `POST /api/agent/route` (AGENT_ROUTE_SPEC.md)
- **Web UI** can call this for analysis requests
- **Layer 3 (Autonomous Agent)** orchestrates multiple Layer 2 workflows

## Documentation

| Document | Purpose | Status |
|----------|---------|--------|
| AGENT_ROUTE_SPEC.md | REST API specification & TUI integration guide | ✅ Complete |
| *TBD* | Error Handling & Retry Strategy | ❌ Missing |
| *TBD* | Session Management & State | ❌ Missing |
| *TBD* | Chunk Format Standardization | ⚠️ Partial (in AGENT_ROUTE_SPEC) |

## Integration Points

- Input: User query + file context from TUI
- Output: Structured {success, answer, tabs[], chunks[], actions[]}
- Timeout: ~32 seconds per request
- Caching: First request 2-5s, subsequent 1-3s

## Implementation

See `kicli_code_assist/agent/meta_coordinator.py` (6-stage pipeline) and `kicli_code_assist/web/server.py` (`/api/agent/route` endpoint).

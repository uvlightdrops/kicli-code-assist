---
title: Layer 2 - Workflow Orchestration Layer
project: kicli-code-assist
agent_project: kicli-code-assist
scope: Backend Architecture / Workflow Layer
purpose: Index and overview for Layer 2 workflow orchestration documentation
created: 2026-11-06T10:25:00+01:00
updated: 2026-11-07T12:38:00+01:00
update_reason: Upgraded to semantic schema, added Phase I2 docs
status: stable

semantic_blocks:
  - id: layer-2-overview
    type: architecture
    status: stable
    version: 2.0
    
  - id: docs-index
    type: implementation
    status: stable
    version: 1.0

relations:
  - target: ../layer-1-raw-llm/README.md
    type: depends-on
    reason: "Layer 2 wraps Layer 1 primitives"
    
  - target: ../layer-3-autonomous-agent/README.md
    type: part-of
    reason: "Layer 3 orchestrates multiple Layer 2 workflows"
    
  - target: PHASE_I2_PROJECTANALYZER_COMPLETE
    type: part-of
    reason: "Phase I2 implements multi-file context (Layer 2 capability)"
    
  - target: PHASE_I2_1_ENDPOINT_INTEGRATION
    type: part-of
    reason: "Endpoint integration is Layer 2 implementation"
    
  - target: PHASE_I2_2_TUI_INTEGRATION_COMPLETE
    type: part-of
    reason: "TUI integration demonstrates Layer 2 workflow"
    
  - target: AGENT_ROUTE_SPEC
    type: part-of
    reason: "REST API spec for Layer 2 orchestration endpoint"
---

# Layer 2 - Workflow Orchestration Layer

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
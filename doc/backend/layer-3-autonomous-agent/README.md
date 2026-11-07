---
title: Layer 3 - Autonomous Agent Layer
project: kicli-code-assist
agent_project: kicli-code-assist
scope: Backend Architecture / Autonomous Agent Layer
purpose: Index and overview for Layer 3 autonomous agent orchestration documentation
created: 2026-11-06T10:25:00+01:00
updated: 2026-11-07T12:38:00+01:00
update_reason: Upgraded to semantic schema
status: stable

semantic_blocks:
  - id: layer-3-overview
    type: architecture
    status: stable
    version: 1.0
    
  - id: agent-docs-index
    type: implementation
    status: stable
    version: 1.0

relations:
  - target: ../layer-1-raw-llm/README.md
    type: depends-on
    reason: "Uses Layer 1 via Layer 2"
    
  - target: ../layer-2-workflow-orchestration/README.md
    type: depends-on
    reason: "Orchestrates Layer 2 workflows autonomously"
    
  - target: AGENT_COORDINATION_ARCHITECTURE
    type: part-of
    reason: "Meta-coordination design for autonomy"
    
  - target: MULTIFILE_REFACTORING_ARCHITECTURE
    type: part-of
    reason: "Phase 5.5.1 implementation"
    
  - target: TRANSPARENCY_INTEGRATION_ARCHITECTURE
    type: part-of
    reason: "Phase 5.5.2 implementation"
---

# Layer 3 - Autonomous Agent Layer

Multi-agent reasoning with self-correction, transparency, and adaptive decision-making.

## Scope

- Meta-coordination (orchestrate Layer 2 workflows autonomously)
- Multi-agent reasoning & collaboration
- Self-correction & feedback loops
- Transparency & observability (reasoning traces, LLM call tracking, performance metrics)
- WebSocket streaming (real-time execution visibility)
- Adaptive decision-making (learn from outcomes)
- Agent capability discovery

## Who Uses This?

- **Advanced automation scenarios** where user can't specify exact workflow upfront
- **Self-improving systems** that adapt based on outcomes
- **Observable AI** scenarios where reasoning traces are valuable for debugging/audit
- Built on top of Layer 2 (doesn't call Layer 1 directly)

## Documentation

| Document | Purpose | Status |
|----------|---------|--------|
| AGENT_COORDINATION_ARCHITECTURE.md | 6-stage orchestration & agent selection | ✅ Complete |
| MULTIFILE_REFACTORING_ARCHITECTURE.md | Phase 5.5.1 implementation (multi-file changes) | ✅ Complete |
| TRANSPARENCY_INTEGRATION_ARCHITECTURE.md | Phase 5.5.2 transparency modules (traces, streaming) | ✅ Complete |
| *TBD* | Self-Correction & Feedback Loop Strategy | ❌ Missing |
| *TBD* | Agent Capability Discovery | ❌ Missing |

## Key Features (Phase 5.5.x Complete)

- **ReasoningTracer** (970 LOC): Capture intermediate reasoning steps
- **LLMCallTracker** (970 LOC): Track all LLM API calls with timing
- **PerformanceMetrics** (950 LOC): System-wide performance analysis
- **WebSocket Streaming**: Real-time execution events via `/agent/execution` namespace
- **REST API**: 9 historical query endpoints `/api/traces/...`
- **Test Coverage**: 93/93 tests passing

## Implementation

See:
- `kicli_code_assist/agent/meta_coordinator.py` (orchestration)
- `kicli_code_assist/agent/reasoning_tracer.py` (transparency module)
- `kicli_code_assist/agent/llm_call_tracker.py` (LLM tracking)
- `kicli_code_assist/agent/performance_metrics.py` (metrics)
- `kicli_code_assist/web/server.py` (WebSocket & REST endpoints)

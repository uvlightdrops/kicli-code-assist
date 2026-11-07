---
title: Layer 1 - Raw LLM Layer
project: kicli-code-assist
agent_project: kicli-code-assist
scope: Backend Architecture / Raw LLM Layer
purpose: Index and overview for Layer 1 raw LLM interface documentation
created: 2026-11-06T10:25:00+01:00
updated: 2026-11-07T12:38:00+01:00
update_reason: Upgraded to semantic schema
status: stable

semantic_blocks:
  - id: layer-1-overview
    type: architecture
    status: stable
    version: 1.0
    
  - id: layer-1-primitives
    type: implementation
    status: stable
    version: 1.0

relations:
  - target: ../layer-2-workflow-orchestration/README.md
    type: composed-of
    reason: "Layer 2 wraps Layer 1 primitives into workflows"
    
  - target: ../layer-3-autonomous-agent/README.md
    type: depends-on
    reason: "Layer 3 uses Layer 2, which uses Layer 1"
    
  - target: IDE_CAPABILITIES
    type: part-of
    reason: "Lists concrete capabilities built from Layer 1"
---

# Layer 1 - Raw LLM Layer

Direct interfaces to LLM providers, system commands, and file I/O primitives.

## Scope

- OpenAI API client (sync/async)
- Secret filtering & security
- File I/O operations
- OS command execution
- Error handling & retry logic at primitive level

## Who Uses This?

- Layer 2 (Workflow Orchestration) wraps these primitives into structured pipelines
- Layer 3 (Autonomous Agent) uses Layer 2, rarely calls Layer 1 directly
- TUI clients can call Layer 2 (AGENT_ROUTE_SPEC) without understanding Layer 1

## Documentation

| Document | Purpose | Status |
|----------|---------|--------|
| IDE_CAPABILITIES.md | What the TUI/WebUI can do with Layer 1 | ✅ Complete |
| *TBD* | LLM Client API Specification (ki_core AsyncOpenAIClient) | ⚠️ Partial |
| *TBD* | OS Command Execution Architecture | ❌ Missing |
| *TBD* | File I/O & Git Operations | ❌ Missing |

## Implementation Notes

- All async operations must use `AsyncOpenAIClient` from `ki_core/adapters/openai_async.py`
- Secret filtering via `SensitiveDataFilter` (ki_core/security)
- Error types in `ki_core/errors/structured.py` (Error, ValidationError, LLMError, RecoveryHints)

---
title: "Layer 1: Raw LLM Layer"
project: kicli-code-assist
scope: backend
type: architecture
status: active
created: 2026-11-06T10:25:00+01:00
updated: 2026-11-06T10:25:00+01:00
update_reason: Initial layer structure documentation
cross_references:
  - ../layer-2-workflow-orchestration/README.md
  - ../layer-3-autonomous-agent/README.md
---

# Layer 1: Raw LLM Layer

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
| *TBD* | LLM Client API Specification | ❌ Missing |
| *TBD* | OS Command Execution Architecture | ❌ Missing |
| *TBD* | File I/O & Git Operations | ❌ Missing |

## Implementation Notes

- All async operations must use `AsyncOpenAIClient` from `ki_core/adapters/openai_async.py`
- Secret filtering via `SensitiveDataFilter` (ki_core/security)
- Error types in `ki_core/errors/structured.py` (Error, ValidationError, LLMError, RecoveryHints)

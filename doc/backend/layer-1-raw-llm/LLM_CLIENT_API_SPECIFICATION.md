---
title: LLM Client API Specification
project: kicli-code-assist
agent_project: kicli-code-assist
scope: Backend Architecture / Layer 1 / LLM Integration
purpose: Complete API documentation for AsyncOpenAIClient and LLM interaction patterns
created: 2026-11-07T13:32:00+01:00
updated: 2026-11-07T13:32:00+01:00
update_reason: Initial placeholder with semantic schema
status: draft

semantic_blocks:
  - id: async-openai-client
    type: architecture
    status: draft
    version: 0.1
  - id: api-methods
    type: implementation
    status: draft
    version: 0.1
  - id: error-handling
    type: implementation
    status: draft
    version: 0.1
  - id: streaming-patterns
    type: implementation
    status: draft
    version: 0.1

relations:
  - target: IDE_CAPABILITIES.md
    type: part-of
    reason: "LLM capabilities are exposed via this API"
  - target: ../layer-2-workflow-orchestration/AGENT_ROUTE_SPEC.md
    type: depends-on
    reason: "Layer 2 wraps these LLM methods"
  - target: ../layer-2-workflow-orchestration/README.md
    type: composed-of
    reason: "Foundation for workflow orchestration"
---

# LLM Client API Specification

Complete specification for `AsyncOpenAIClient` from `ki_core/adapters/openai_async.py`.

## AsyncOpenAIClient [async-openai-client]

**Status:** TBD

Core async wrapper around OpenAI API. Provides:
- Sync & async methods for chat completion
- Secret filtering (via SensitiveDataFilter)
- Token counting & cost estimation
- Retry logic & exponential backoff
- Structured error handling

## API Methods [api-methods]

**Status:** TBD

### achat()

Async single chat completion.

```python
# TBD: Method signature
# TBD: Parameter documentation
# TBD: Return value structure
# TBD: Usage examples
```

### achat_stream()

Async streaming chat completion.

```python
# TBD: Method signature
# TBD: Parameter documentation
# TBD: Token/chunk handling
# TBD: Cancellation patterns
```

### Token Counting

```python
# TBD: count_tokens() implementation
# TBD: Cost calculation
# TBD: Rate limiting awareness
```

## Error Handling [error-handling]

**Status:** TBD

Integration with `ki_core/errors/structured.py`:
- `LLMError` for API failures
- `ValidationError` for invalid inputs
- `RecoveryHints` for client guidance

```python
# TBD: Error classification
# TBD: Retry strategies per error type
# TBD: Fallback patterns
```

## Streaming Patterns [streaming-patterns]

**Status:** TBD

Token streaming via Server-Sent Events (SSE):
- Chunk boundaries
- Token buffering
- Cancellation handling
- Performance metrics

```python
# TBD: Streaming API contract
# TBD: Backpressure handling
# TBD: WebSocket integration (if applicable)
```

## Implementation Notes

See `ki_core/src/ki_core/adapters/openai_async.py` for current implementation.


# Server Modularization Refactoring Plan

## Current State
- **server.py**: 1480 lines, 11 functions, 8 sections
- **Metrics**: Exceeds maintainability threshold (>1000 lines = critical)
- **Impact**: Hard to test, understand, debug; tight coupling between concerns

## Target Architecture

```
kicli_code_assist/web/
├── server.py              (200 lines) - App factory + entry point
├── server_config.py       (120 lines) - Configuration & logging setup
├── server_instances.py    (80 lines)  - Phase 2D singleton instances
├── server_routes.py       (600 lines) - REST endpoints (/api/agent/*, /api/project/*)
├── server_websocket.py    (300 lines) - WebSocket handlers
├── server_async.py        (200 lines) - Async processing (chat, reasoning streams)
└── __init__.py
```

## Phase 1: Extract Config & Instances (Low Risk)

**Target**: Move non-route code to separate modules for cleaner imports

### 1.1: server_config.py (NEW)
Extract from server.py lines ~1-60:
- `get_config()`
- Config validation helpers
- Logging setup constants

### 1.2: server_instances.py (NEW)
Extract Phase 2D singleton getters:
- `get_intent_detector()`
- `get_executor()`
- `get_aggregator()`
- `get_answer_generator()`
- Module-level `_intent_detector`, `_executor`, etc. globals

### 1.3: server.py (REFACTORED)
Keep only:
- Imports (simplified)
- `create_app()` function
- `main()` entry point
- Global app/socketio instances (created via create_app)

## Phase 2: Extract Routes (Medium Complexity)

### 2.1: server_routes.py (NEW)
Move `register_routes()` and all route handlers:
- GET /api/health
- POST /api/agent/route (Phase 2D unified endpoint)
- GET /api/agent/stream (reasoning WebSocket)
- POST /api/project/open
- GET /api/project/files
- POST /api/project/analyze
- etc.

Import from `server_instances` as needed.

### 2.2: server.py (UPDATED)
- Import `register_routes` from `server_routes`
- Call in `create_app()` as before
- No route handler code

## Phase 3: Extract WebSocket (Medium Complexity)

### 3.1: server_websocket.py (NEW)
Move `register_websocket()` and all handlers:
- `@socketio.on("chat:send")`
- `@socketio.on("chat:subscribe")`
- `@socketio.on("reasoning:subscribe")`
- etc.

### 3.2: server.py (UPDATED)
- Import `register_websocket` from `server_websocket`
- Call in `create_app()` as before

## Phase 4: Extract Async Processing (Medium Complexity)

### 4.1: server_async.py (NEW)
Move async functions:
- `process_chat_async()`
- `stream_reasoning_async()`
- `handle_stream_cancellation()`
- etc.

Helpers:
- Async context managers
- Event loop wrappers

### 4.2: server_routes.py (UPDATED)
- Import async functions from `server_async`
- Update route handlers to call async functions

## Implementation Order

1. **Phase 1 (NOW)**: Extract config & instances → server_config.py, server_instances.py
2. **Phase 2 (NEXT)**: Extract routes → server_routes.py
3. **Phase 3 (LATER)**: Extract WebSocket → server_websocket.py
4. **Phase 4 (LATER)**: Extract async → server_async.py

## Success Criteria

- ✅ All tests pass (integration + unit)
- ✅ Each module <500 lines
- ✅ Clear separation of concerns
- ✅ No circular imports
- ✅ Imports remain fast (<100ms)
- ✅ No runtime behavior changes
- ✅ API remains identical

## Estimated Effort
- Phase 1: 20 minutes (straightforward extraction)
- Phase 2: 30 minutes (modify route decorators)
- Phase 3: 25 minutes (WebSocket context management)
- Phase 4: 20 minutes (async event loop setup)
- Testing: 30 minutes

**Total**: ~2 hours

## Risk Mitigation
1. **Circular imports**: Use TYPE_CHECKING for forward refs
2. **Lost singletons**: Ensure Phase 2D instances persist across modules
3. **WebSocket context**: Keep socketio instance in main module
4. **Async state**: Thread safety in event loop wrapper

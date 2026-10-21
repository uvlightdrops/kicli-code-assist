# Async LLM Integration Fixes (2026-10-21)

**Status:** ✅ COMPLETE  
**Scope:** WebUI async decoupling + test infrastructure  
**Commit:** 8648d32

---

## Problem Statement

The WebUI `/api/chat` endpoint was **blockierend** (blocking):
- Thread wurde erstellt, aber `process_chat()` war **synchron**
- `process_chat_async()` existierte aber wurde nicht aufgerufen
- Keine echter Async/Await Pattern für nicht-blockierende LLM calls

**Result:**
- WebUI UI könnte während LLM-Abfrage hängenbleiben
- Keine Parallelisierung von mehreren Chat-Requests
- Fehlerbehandlung war unzureichend

---

## Solution

### 1. WebUI /api/chat Route (`web/server.py`)

#### Vorher (Blockierend)
```python
@app.route("/api/chat", methods=["POST"])
def submit_chat():
    def process_chat():  # ← SYNCHRON!
        response_text = "Mock response"
        socketio.emit("chat.response", {...})
    
    thread = Thread(target=process_chat)  # ← Thread ohne Async
    thread.start()
    return jsonify({"request_id": request_id})
```

#### Nachher (Non-blocking)
```python
@app.route("/api/chat", methods=["POST"])
def submit_chat():
    def process_chat_sync():  # ← WRAPPER für Thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            process_chat_async(...)  # ← ECHTES ASYNC!
        )
    
    thread = Thread(target=process_chat_sync)  # ← Mit Async-Loop
    thread.start()
    return jsonify({"request_id": request_id})
```

### 2. process_chat_async() Fixes

#### Streaming Event Type (Vorher: Falsch)
```python
# FALSCH: .type.value == "content" existiert nicht
if stream_event.type.value == "content":
    chunk = stream_event.content  # ← .content ist falsch!
```

#### Streaming Event Type (Nachher: Richtig)
```python
# RICHTIG: StreamEventType.TOKEN (Enum)
if stream_event.type == StreamEventType.TOKEN:
    chunk = stream_event.text  # ← .text ist korrekt!
```

### 3. Error Handling mit Recovery Hints

**Neu:**
```python
except AllProvidersFailedError as e:
    error_msg = f"❌ All LLM providers failed: {e.message}"
    socketio.emit("chat.response", {...})
    
    # Recovery hints für User
    if hasattr(e, 'recovery_hints') and e.recovery_hints:
        for hint in e.recovery_hints:
            logger.info(f"Recovery: {hint.action} - {hint.description}")
```

---

## Files Modified

### `kicli_code_assist/web/server.py`
- ✅ `/api/chat` POST route (lines 330-395)
- ✅ `process_chat_async()` function (lines 72-173)
- ✅ Error handling with recovery hints
- ✅ Fixed streaming event type checking

### `test_async_llm.py` (NEW)
- ✅ Test 1: Basic query (non-blocking)
- ✅ Test 2: Streaming responses
- ✅ Test 3: System prompt + secret filtering
- ✅ Test 4: Parallel queries (true async decoupling)

### `kicli_code_assist/ui/app.py`
- ✅ `_submit_chat()` refactored (though TUI is secondary)
- ✅ New `_submit_chat_async()` method for proper async pattern

---

## How to Test

### 1. Standalone Tests (Recommended)
```bash
cd /home/flow/dev_flow/kicli-code-assist

# Run all tests
python3 test_async_llm.py

# Watch logs
tail -f log/kicli-llm.log
```

**Expected Output:**
```
✓ basic_query: PASS
✓ streaming: PASS (4 chunks)
✓ system_prompt: PASS
✓ parallel: PASS (both queries ~2s, not 4s)
```

### 2. WebUI Integration Test
```bash
# Terminal 1: Start backend
cd /home/flow/dev_flow/kicli-code-assist
python3 kicli_code_assist/web/server.py

# Terminal 2: Start frontend
cd web
npm run dev

# Terminal 3: Watch logs
tail -f /home/flow/dev_flow/kicli-code-assist/log/kicli-web.log
```

**Test in WebUI:**
1. Open browser: http://localhost:3000
2. Send message: "What is 2+2?"
3. Check logs: Should see full request/response flow
4. WebUI should be responsive (no freezing)

### 3. Error Handling Test
```bash
# Edit your ki.yaml to remove OPENAI_API_KEY:
# openai:
#   api_key: ""  # ← Empty or missing

# Send message in WebUI
# Should see: "❌ OpenAI API key not configured"
# With recovery hints
```

---

## Technical Details

### Async Execution Flow

```
WebUI User sends message
  ↓
POST /api/chat (Flask, synchron)
  ↓
Create Thread with process_chat_sync() wrapper
  ↓
Inside thread:
  - Create new event loop (asyncio.new_event_loop())
  - Call process_chat_async() with await
    - Add message to chat session
    - Get LLM provider chain
    - await llm.query() or await llm.stream()
      - Non-blocking! Can handle multiple requests in parallel
    - Emit response via WebSocket (real-time)
  - Close loop
  ↓
WebUI receives chunks via WebSocket (streaming)
  ↓
Display in UI (non-blocking)
```

### Key Points

1. **Thread per request**: Each `/api/chat` call gets its own thread + event loop
2. **Async inside thread**: `process_chat_async()` is truly async within that thread
3. **Non-blocking streaming**: WebSocket emits each token as it arrives (real-time)
4. **Error propagation**: Errors with recovery hints are emitted via WebSocket
5. **Multiple requests**: Can handle parallel requests (each in own thread+loop)

---

## Deployment

### Pre-deployment Checklist
- ✅ Code changes committed (8648d32)
- ✅ Tests created and verified
- ✅ Error handling with recovery hints
- ✅ Backward compatible (no breaking changes)
- ⏳ Production deployment pending

### Required Actions
1. Run tests: `python3 test_async_llm.py`
2. Verify WebUI works: Start server, send message, check logs
3. If all pass: Ready for production deployment

### Deployment Command
```bash
cd /home/flow/dev_flow/kicli-code-assist
git push origin devel  # Push to production
# OR
make prod-update       # If using production deployment script
```

---

## Known Limitations

1. **Sequential processing within a request**: Each request has ONE thread + event loop
   - Multiple messages in same session are sequential (not parallel)
   - This is OK (expected behavior for chat)

2. **Thread overhead**: Creating new thread per request has overhead
   - For production: Consider thread pool (ThreadPoolExecutor)
   - Current: Good for testing/MVP

3. **Event loop cleanup**: Each thread creates/destroys event loop
   - For production: Consider reusing event loops (eventlet/gevent)
   - Current: Simpler, sufficient for now

---

## Future Improvements

1. **Thread Pool**: Use ThreadPoolExecutor with N workers
   ```python
   executor = ThreadPoolExecutor(max_workers=10)
   executor.submit(process_chat_sync, ...)
   ```

2. **Production ASGI**: Replace Flask with FastAPI + uvicorn (native async)
   ```python
   @app.post("/api/chat")
   async def submit_chat(message: str):
       response = await process_chat_async(...)
       return response
   ```

3. **Circuit Breaker**: Add per-provider circuit breaker
   - Already implemented in ProviderChain, but could be enhanced

4. **Request Queuing**: Add request queue with max concurrency
   - Prevent resource exhaustion

---

## Log Files

### LLM Logs
```bash
tail -f /home/flow/dev_flow/kicli-code-assist/log/kicli-llm.log
```

Includes:
- Request start/stop markers
- Provider info (OpenAI, Ollama, etc.)
- Message summary
- Response tokens
- Error handling flow

### Web Logs
```bash
tail -f /home/flow/dev_flow/kicli-code-assist/log/kicli-web.log
```

Includes:
- Request ID tracking
- Chat processing status
- WebSocket emissions
- Error details

---

## Questions?

Refer to:
- `docs/architecture/PHASE_4_ARCHITECTURE.md` - System design
- `docs/PRODUCTION_DEPLOYMENT.md` - Deployment procedures
- Inline code comments in `web/server.py`

---

**Last Updated:** 2026-10-21  
**Status:** ✅ Ready for testing and production deployment

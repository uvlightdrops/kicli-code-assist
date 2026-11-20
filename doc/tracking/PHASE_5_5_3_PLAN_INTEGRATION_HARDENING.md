---
title: "Phase 5.5.3 Plan: Integration Hardening"
project: kicli-code-assist
scope: backend
purpose: "Planning for Phase 5.5.3 - Performance, reliability, and robustness testing"
created: "2026-11-20 14"
updated: "2026-11-20 14"
status: active
---

# Phase 5.5.3: Integration Hardening - Detailed Plan

**Previous Phase**: 5.5.2 ✅ (Transparency & Observability)  
**Current Phase**: 5.5.3 (Integration Hardening)  
**Next Phase**: 5.5.4 (Frontend Integration)  
**Estimated Duration**: 3-4 hours

## Overview

Phase 5.5.3 hardens Phase 5.5.2's transparency system through:
1. **Load Testing** - 100-1000 concurrent execution tracking
2. **Error Resilience** - Network failures, timeouts, edge cases
3. **Performance Optimization** - Reduce overhead, optimize payload
4. **Monitoring & Observability** - Health checks, metrics collection

## Success Criteria

| Criterion | Current | Target | Status |
|-----------|---------|--------|--------|
| Concurrent Executions | 10 | 1000+ | ❌ UNTESTED |
| Memory Stability | Untested | <50MB delta per 100 executions | ❌ UNTESTED |
| WebSocket Reconnection | Manual | Auto-recover + notify | ❌ TODO |
| Event Ordering | Assumed | Guaranteed FIFO | ❌ UNTESTED |
| Error Propagation | Partial | 100% coverage | ❌ INCOMPLETE |
| Response Time P95 | Untested | <100ms for /api/traces | ❌ UNTESTED |

## Detailed Tasks

### TASK 1: Load Testing (1.5 hours)

**Goal**: Verify system handles 100-1000 concurrent executions without degradation

#### 1.1 Create Load Test Harness

**File**: `tests/test_phase_5_5_3_load.py`

```python
import asyncio
import time
from kicli_code_assist.web.execution_manager import get_execution_manager
from kicli_code_assist.agent.reasoning_tracer import ReasoningTracer
from kicli_code_assist.agent.llm_call_tracker import LLMCallTracker
from kicli_code_assist.agent.performance_metrics import PerformanceMetrics

class TestLoadHandling:
    @pytest.mark.slow  # Mark so it can be run separately
    def test_1000_concurrent_sessions(self):
        """Create 1000 concurrent ExecutionSessions and track them."""
        manager = get_execution_manager()
        
        # Create 1000 sessions
        sessions = []
        for i in range(1000):
            session = manager.create_session(f"Load test {i}")
            sessions.append(session)
            if i % 100 == 0:
                print(f"Created {i}/1000 sessions")
        
        # Verify all sessions exist
        assert len(sessions) == 1000
        
        # Simulate activity
        for session in sessions[:100]:  # Sample 100
            session.start()
            # Record reasoning
            tracer = ReasoningTracer(agent_id=session.execution_id)
            tracer.record_decision(
                decision_point="test",
                options=["a", "b"],
                selected="a",
                confidence=0.95
            )
            # Record LLM call
            tracker = LLMCallTracker(agent_id=session.execution_id)
            tracker.record_call(...)
            session.complete()
        
        # Measure memory
        import psutil
        process = psutil.Process()
        mem_mb = process.memory_info().rss / 1024 / 1024
        print(f"Memory after 1000 sessions: {mem_mb:.1f}MB")
        assert mem_mb < 500, "Memory usage exceeds 500MB"

    def test_stress_websocket_subscriptions(self):
        """Simulate 100 clients subscribing to same execution."""
        from flask_socketio import SocketIO
        from kicli_code_assist.web import server_websocket
        
        app = Flask(__name__)
        socketio = SocketIO(app, async_mode="threading")
        server_websocket.register_websocket(app, socketio)
        
        manager = get_execution_manager()
        session = manager.create_session("Stress test")
        execution_id = session.execution_id
        
        # Create 100 test clients
        clients = []
        for i in range(100):
            client = socketio.test_client(app, namespace="/agent/execution")
            client.emit("subscribe:execution", {"execution_id": execution_id})
            clients.append(client)
        
        # Verify all subscribed
        assert len(server_websocket._EXECUTION_SUBSCRIPTIONS[execution_id]) == 100
        
        # Emit event to all
        socketio.emit("agent:status", {
            "execution_id": execution_id,
            "status": "running"
        }, room=f"execution:{execution_id}")
        
        # Verify all received
        for client in clients:
            received = server_websocket.received(client, "agent:status")
            assert len(received) > 0
        
        print("✓ 100 concurrent WebSocket subscriptions OK")

    def test_memory_leak_long_running(self):
        """Run 100 session lifecycles and measure memory growth."""
        import psutil
        process = psutil.Process()
        manager = get_execution_manager()
        
        # Baseline
        mem_start = process.memory_info().rss
        
        # Run 100 cycles
        for cycle in range(100):
            session = manager.create_session(f"Cycle {cycle}")
            session.start()
            
            # Simulate work
            tracer = ReasoningTracer(agent_id=session.execution_id)
            for j in range(10):
                tracer.record_decision(...)
            
            session.complete()
            
            if cycle % 10 == 0:
                mem_now = process.memory_info().rss
                mem_delta_mb = (mem_now - mem_start) / 1024 / 1024
                print(f"Cycle {cycle}: Delta {mem_delta_mb:.1f}MB")
        
        # Verify memory growth is linear, not exponential
        mem_end = process.memory_info().rss
        mem_total_mb = (mem_end - mem_start) / 1024 / 1024
        avg_per_session = mem_total_mb / 100
        
        assert avg_per_session < 1.0, f"Each session uses {avg_per_session:.2f}MB"
        print(f"✓ Memory growth linear: {avg_per_session:.3f}MB per session")
```

**Run**:
```bash
pytest tests/test_phase_5_5_3_load.py::TestLoadHandling::test_1000_concurrent_sessions -v -s --tb=short
pytest tests/test_phase_5_5_3_load.py::TestLoadHandling::test_stress_websocket_subscriptions -v -s
pytest tests/test_phase_5_5_3_load.py::TestLoadHandling::test_memory_leak_long_running -v -s
```

#### 1.2 Benchmark REST API Endpoints

**File**: `tests/test_phase_5_5_3_perf.py`

```python
class TestAPIPerfomance:
    def test_get_traces_response_time(self):
        """Measure /api/traces endpoint response time."""
        from kicli_code_assist.web.server import app
        from kicli_code_assist.web.execution_manager import get_execution_manager
        
        client = app.test_client()
        manager = get_execution_manager()
        
        # Create 100 executions
        for i in range(100):
            session = manager.create_session(f"Trace {i}")
            session.start()
            session.complete()
        
        # Benchmark list endpoint
        import time
        start = time.time()
        for _ in range(10):
            resp = client.get("/api/traces?limit=10&offset=0")
        elapsed = (time.time() - start) / 10
        
        print(f"GET /api/traces: {elapsed*1000:.1f}ms avg")
        assert elapsed < 0.1, "Response time > 100ms"
    
    def test_get_traces_id_metrics_response_time(self):
        """Measure /api/traces/<id>/metrics endpoint response time."""
        # Create execution with metrics
        # Benchmark /api/traces/<id>/metrics
        # Assert < 50ms response time
        pass

    def test_websocket_event_latency(self):
        """Measure WebSocket event emission latency."""
        # Emit event
        # Measure time for clients to receive
        # Assert < 10ms
        pass
```

### TASK 2: Error Handling & Recovery (1 hour)

**Goal**: Handle edge cases gracefully

#### 2.1 Network Failure Resilience

**Updates to `server_websocket.py`**:

```python
@socketio.on("subscribe:execution", namespace="/agent/execution")
def handle_execution_subscribe(data):
    # ... existing code ...
    try:
        manager = get_execution_manager()
        session = manager.get_session(execution_id)
        
        if session:
            emit("agent:subscribed", {...})
        else:
            # 🔧 IMPROVED: Don't just error - create session if missing
            logger.warning(f"Session {execution_id} not found, creating...")
            session = manager.create_session(f"Auto-created for {execution_id}")
            emit("agent:subscribed", {...})
    
    except RuntimeError:
        # ExecutionManager not initialized (tests)
        emit("agent:subscribed", {...})
    
    except Exception as e:
        # 🔧 IMPROVED: Catch all exceptions, log, and notify client
        logger.error(f"Subscribe error: {e}", exc_info=True)
        emit("agent:error", {
            "execution_id": execution_id,
            "error": str(e),
            "recovery": "Retry subscription or refresh page"
        })

@socketio.on_error_default
def default_error_handler(e):
    """Global error handler for unhandled exceptions."""
    logger.error(f"Unhandled WebSocket error: {e}", exc_info=True)
    emit("agent:error", {
        "error": "Internal server error",
        "details": str(e) if app.debug else "See server logs"
    })
```

#### 2.2 Timeout & Recovery

**Updates to REST API**:

```python
# In agent_traces.py
from functools import wraps

def api_timeout(seconds=30):
    """Decorator to enforce API response timeout."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Request exceeded {seconds}s timeout")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                result = f(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result
        return wrapper
    return decorator

@app.route("/api/traces/<execution_id>/events")
@api_timeout(seconds=10)
def get_execution_events(execution_id):
    """Get events for execution (with timeout)."""
    try:
        manager = get_execution_manager()
        session = manager.get_session(execution_id)
        
        if not session:
            return {"error": "Execution not found"}, 404
        
        return {"events": session.get_events()}, 200
    
    except TimeoutError:
        return {"error": "Query timeout", "suggestion": "Filter by date range"}, 504
    except Exception as e:
        logger.error(f"Error fetching events: {e}", exc_info=True)
        return {"error": "Internal server error"}, 500
```

### TASK 3: Performance Optimization (1 hour)

**Goal**: Reduce overhead, improve responsiveness

#### 3.1 WebSocket Payload Optimization

**Update `server_websocket.py`**:

```python
def emit_optimized(event_name, data, **kwargs):
    """Emit event with compression for large payloads."""
    import json
    
    # For events > 10KB, only send summary + link to full data
    payload_size = len(json.dumps(data))
    
    if payload_size > 10_000:
        logger.debug(f"{event_name} payload {payload_size}B exceeds 10KB, summarizing...")
        
        if event_name == "agent:reasoning":
            # Send summary only
            summary = {
                "event_id": data.get("event_id"),
                "decision_point": data.get("decision_point"),
                "selected": data.get("selected"),
                "confidence": data.get("confidence"),
                # Omit: full_context, all_options
            }
            emit(event_name, summary, **kwargs)
            # Store full data for REST API
            manager.store_event_details(data)
        
        elif event_name == "agent:llm_call":
            # Send summary only
            summary = {
                "event_id": data.get("event_id"),
                "model": data.get("model"),
                "tokens": data.get("tokens"),
                "cost_usd": data.get("cost_usd"),
                # Omit: prompt, response (available via REST API)
            }
            emit(event_name, summary, **kwargs)
            manager.store_event_details(data)
    
    else:
        # Small payloads - send full data
        emit(event_name, data, **kwargs)
```

#### 3.2 Event Batching for High-Volume

```python
class EventBatcher:
    """Batch small events to reduce WebSocket overhead."""
    
    def __init__(self, batch_size=10, flush_interval_ms=100):
        self.batch_size = batch_size
        self.flush_interval_ms = flush_interval_ms
        self.buffer = []
        self.last_flush = time.time()
    
    def add_event(self, event_name, data):
        """Add event to batch."""
        self.buffer.append({"name": event_name, "data": data})
        
        if len(self.buffer) >= self.batch_size:
            self.flush()
        elif time.time() - self.last_flush > self.flush_interval_ms / 1000:
            self.flush()
    
    def flush(self):
        """Send batched events."""
        if not self.buffer:
            return
        
        emit("agent:batch", {
            "timestamp": time.time(),
            "count": len(self.buffer),
            "events": self.buffer
        })
        
        self.buffer = []
        self.last_flush = time.time()
```

### TASK 4: Comprehensive Test Suite (1 hour)

**Create**: `tests/test_phase_5_5_3_comprehensive.py`

```python
class TestErrorScenarios:
    """Test all error paths and edge cases."""
    
    def test_subscribe_with_missing_execution_id(self):
        """Subscribe without execution_id should error."""
        pass
    
    def test_subscribe_with_invalid_execution_id_format(self):
        """Subscribe with malformed UUID should error."""
        pass
    
    def test_concurrent_subscribe_unsubscribe(self):
        """Race condition: simultaneous subscribe and unsubscribe."""
        pass
    
    def test_websocket_disconnect_cleanup(self):
        """Subscriptions cleaned up after disconnect."""
        pass
    
    def test_api_query_with_invalid_date_range(self):
        """REST API should validate date parameters."""
        pass
    
    def test_api_pagination_boundary(self):
        """Test limit=0, offset > total, negative values."""
        pass
    
    def test_concurrent_api_queries(self):
        """Multiple simultaneous /api/traces queries."""
        pass

class TestReliability:
    """Test reliability under adverse conditions."""
    
    def test_session_survives_client_disconnect(self):
        """Execution continues after WebSocket client disconnects."""
        pass
    
    def test_metrics_accurate_after_error(self):
        """Performance metrics still accurate after exceptions."""
        pass
    
    def test_cost_calculation_precision(self):
        """Cost never rounds incorrectly (no accumulation errors)."""
        pass
```

## Deliverables

After Phase 5.5.3, we will have:

✅ Load test suite validating:
- 1000 concurrent execution sessions
- 100 concurrent WebSocket clients
- Memory stability (<1MB per session)
- No memory leaks over long runs

✅ Performance benchmark data:
- WebSocket event latency < 10ms
- REST API response time < 100ms
- Event processing overhead < 5%

✅ Error handling improvements:
- 100% error path coverage
- Graceful degradation
- Recovery procedures

✅ Hardened system ready for:
- Production deployment
- Phase 5.5.4 (Frontend Integration)
- Phase 6 (Persistence)

## Timeline

| Task | Duration | Status |
|------|----------|--------|
| Load Testing Harness | 1.5h | ⏳ QUEUE |
| Error Handling | 1h | ⏳ QUEUE |
| Performance Optimization | 1h | ⏳ QUEUE |
| Comprehensive Tests | 1h | ⏳ QUEUE |
| **Total** | **~4h** | ⏳ QUEUE |

## Success Metrics

- ✅ 1000 concurrent sessions supported
- ✅ Memory growth < 1MB per session
- ✅ WebSocket latency < 10ms (P95)
- ✅ All error scenarios handled
- ✅ 90%+ code coverage (transparency modules)
- ✅ No memory leaks detected

---

**Next**: After Phase 5.5.3 complete → Phase 5.5.4 (Frontend Integration with ReasoningPanel TUI widget)

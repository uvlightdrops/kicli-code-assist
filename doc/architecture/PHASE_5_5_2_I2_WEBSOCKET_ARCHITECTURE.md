---
title: "Phase 5.5.2.I2: WebSocket Streaming Architecture"
project: "kicli-code-assist"
scope: "architecture"
created: 2026-11-02T03:18:24+01:00
updated: 2026-11-02T03:18:24+01:00
update_reason: "Design for real-time transparency event streaming"
status: "active"
author: "Copilot"
---

# Phase 5.5.2.I2: WebSocket Streaming Architecture

**Objective:** Enable real-time event streaming from CodeImplementationAgent to frontend

---

## Architecture

### Event Flow

```
CodeImplementationAgent
  ├─ tracer.record_*()          (decision, execution, error)
  ├─ tracker.record_call()      (LLM call + cost)
  └─ metrics.record_*()         (timing, counters, gauges)
  
         ↓ (via TransparencyEventEmitter)
  
  WebSocket Events
  ├─ agent:decision              {confidence, options, selected}
  ├─ agent:execution             {action, result, duration}
  ├─ agent:error                 {type, message, recovery}
  ├─ agent:llm_call              {model, tokens, cost}
  └─ agent:metric_update         {phase, metrics}
  
         ↓ (via SocketIO)
  
  /agent/execution namespace (room: execution:{execution_id})
  
         ↓
  
  Frontend WebSocket Client
  └─ useReasoningStream hook
     └─ ReasoningPanel component (live display)
```

### WebSocket Namespace

**Namespace:** `/agent/execution`

**Connection:**
```javascript
const socket = io(window.location.origin, {
  namespace: '/agent/execution',
  query: { execution_id: 'test-123' }
});
```

**Events (Server → Client):**
```
agent:decision
  {
    "execution_id": "test-123",
    "timestamp": "2026-11-02T03:18:24Z",
    "options_considered": ["Option A", "Option B"],
    "option_selected": "Option A",
    "confidence_score": 0.95,
    "reasoning": "..."
  }

agent:execution
  {
    "execution_id": "test-123",
    "timestamp": "2026-11-02T03:18:24Z",
    "action": "llm_generation",
    "result": "success",
    "duration_ms": 2500,
    "output_length": 1500
  }

agent:error
  {
    "execution_id": "test-123",
    "timestamp": "2026-11-02T03:18:24Z",
    "error_type": "LLMClientError",
    "message": "Connection failed",
    "recovery_suggestion": "Check API keys"
  }

agent:llm_call
  {
    "execution_id": "test-123",
    "timestamp": "2026-11-02T03:18:24Z",
    "model": "gpt-4o",
    "purpose": "code_generation",
    "input_tokens": 2000,
    "output_tokens": 1500,
    "total_tokens": 3500,
    "cost": 0.0425,
    "latency_ms": 2500
  }

agent:metric_update
  {
    "execution_id": "test-123",
    "timestamp": "2026-11-02T03:18:24Z",
    "phase": "analysis",
    "metrics": {
      "files_analyzed": 10,
      "duration_ms": 500
    }
  }

agent:session_end
  {
    "execution_id": "test-123",
    "success": true,
    "total_events": 25,
    "total_duration_ms": 5000,
    "trace_file": "/traces/test-123.json"
  }
```

**Events (Client → Server):**
```
subscribe:execution
  { "execution_id": "test-123" }

unsubscribe:execution
  { "execution_id": "test-123" }

get:execution_status
  { "execution_id": "test-123" }
  → Response: agent:status { "execution_id": "...", "status": "running/completed", ... }
```

---

## Implementation Components

### 1. TransparencyEventEmitter (NEW)

**File:** `kicli_code_assist/agent/transparency_event_emitter.py`

**Purpose:** Bridge between Transparency Modules and WebSocket

**API:**
```python
class TransparencyEventEmitter:
    def __init__(self, socketio: SocketIO, execution_id: str):
        self.socketio = socketio
        self.execution_id = execution_id
        self.room = f"execution:{execution_id}"
    
    def emit_decision(self, options, selected, confidence, reasoning=""):
        """Emit decision event to WebSocket."""
        self.socketio.emit(
            "agent:decision",
            {
                "execution_id": self.execution_id,
                "timestamp": datetime.now().isoformat(),
                "options_considered": options,
                "option_selected": selected,
                "confidence_score": confidence,
                "reasoning": reasoning
            },
            room=self.room
        )
    
    def emit_execution(self, action, result, **kwargs):
        """Emit execution event."""
        
    def emit_error(self, error_type, message, recovery):
        """Emit error event."""
        
    def emit_llm_call(self, model, tokens_in, tokens_out, cost, latency_ms):
        """Emit LLM call event."""
        
    def emit_metric_update(self, phase, metrics):
        """Emit metrics update."""
        
    def emit_session_end(self, success, total_events, duration_ms, trace_file):
        """Emit session end event."""
```

### 2. Extended WebSocket Handler

**File:** `kicli_code_assist/web/server_websocket.py` (extend)

**New Handlers:**
```python
@socketio.on("subscribe:execution")
def handle_execution_subscribe(data):
    """Subscribe to execution events."""
    execution_id = data.get("execution_id")
    room = f"execution:{execution_id}"
    join_room(room)
    emit("agent:subscribed", {"execution_id": execution_id})

@socketio.on("unsubscribe:execution")
def handle_execution_unsubscribe(data):
    """Unsubscribe from execution events."""
    execution_id = data.get("execution_id")
    room = f"execution:{execution_id}"
    leave_room(room)
    emit("agent:unsubscribed", {"execution_id": execution_id})

@socketio.on("get:execution_status")
def handle_execution_status(data):
    """Get current execution status."""
    execution_id = data.get("execution_id")
    # Look up status from ExecutionManager
    status = get_execution_status(execution_id)
    emit("agent:status", status)
```

### 3. Integration with CodeImplementationAgent

**File:** `kicli_code_assist/agent/code_implementation.py` (extend)

**Constructor:**
```python
def __init__(self, project_root: str, enable_transparency: bool = True, 
             socketio: Optional[SocketIO] = None, execution_id: Optional[str] = None):
    # ... existing code ...
    self.socketio = socketio
    self.execution_id = execution_id
    
    if self.enable_transparency and self.socketio:
        from kicli_code_assist.agent.transparency_event_emitter import TransparencyEventEmitter
        self.event_emitter = TransparencyEventEmitter(socketio, execution_id)
    else:
        self.event_emitter = None
```

**In generate_code_via_llm():**
```python
if self.event_emitter:
    self.event_emitter.emit_decision(
        options=["cached", "llm", "template"],
        selected="llm",
        confidence=0.9
    )
```

**In apply_with_full_autonomy():**
```python
if self.event_emitter:
    self.event_emitter.emit_session_end(
        success=True,
        total_events=len(session.events),
        duration_ms=total_time,
        trace_file=trace_file
    )
```

---

## Frontend Integration (Phase 5.5.2.I4)

### useReasoningStream Hook

```typescript
function useReasoningStream(executionId: string) {
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState("idle");
  
  useEffect(() => {
    const socket = io(window.location.origin, {
      namespace: '/agent/execution'
    });
    
    socket.emit("subscribe:execution", { execution_id: executionId });
    
    socket.on("agent:decision", (event) => {
      setEvents(prev => [...prev, event]);
    });
    
    socket.on("agent:llm_call", (event) => {
      setEvents(prev => [...prev, event]);
    });
    
    socket.on("agent:session_end", (event) => {
      setStatus("completed");
    });
    
    return () => {
      socket.emit("unsubscribe:execution", { execution_id: executionId });
      socket.disconnect();
    };
  }, [executionId]);
  
  return { events, status };
}
```

### ReasoningPanel Component

```typescript
export function ReasoningPanel({ executionId }: { executionId: string }) {
  const { events, status } = useReasoningStream(executionId);
  
  return (
    <div className="reasoning-panel">
      <h3>Execution Trace</h3>
      <div className="event-stream">
        {events.map((event, i) => (
          <EventItem key={i} event={event} />
        ))}
      </div>
      <div className="status">{status}</div>
    </div>
  );
}
```

---

## Testing Strategy

### 1. Unit Tests

**File:** `tests/test_transparency_streaming.py`

```python
def test_event_emitter_decision():
    """Test decision event emission."""
    socketio = Mock()
    emitter = TransparencyEventEmitter(socketio, "test-123")
    
    emitter.emit_decision(
        options=["A", "B"],
        selected="A",
        confidence=0.9
    )
    
    socketio.emit.assert_called_once()
    args = socketio.emit.call_args
    assert args[0][0] == "agent:decision"
    assert args[0][1]["execution_id"] == "test-123"
    assert args[1]["room"] == "execution:test-123"

def test_websocket_subscription():
    """Test WebSocket subscription handling."""
    # Mock socketio + socket client
    # Emit subscribe:execution
    # Verify join_room() called
    # Verify agent:subscribed emitted
```

### 2. Integration Tests

```python
def test_full_streaming_workflow():
    """Test complete streaming workflow."""
    # 1. Start CodeImplementationAgent with socketio
    # 2. Emit various events (decision, execution, llm_call)
    # 3. Verify all events reach WebSocket
    # 4. Verify room subscriptions work
    # 5. Verify session_end event
```

### 3. End-to-End Tests

```python
def test_frontend_receives_events():
    """Test WebSocket events reach frontend."""
    # 1. Create test execution
    # 2. Connect frontend WebSocket client
    # 3. Subscribe to execution
    # 4. Trigger agent actions
    # 5. Verify events received in correct order
    # 6. Verify data format is correct
```

---

## Performance Considerations

### Event Rate Limiting
- Don't emit every tracer record (could be thousands/sec)
- Batch minor events (e.g., file analysis) 
- Emit important events immediately (decisions, errors, LLM calls)

### Room Management
- Clean up rooms when execution ends
- Auto-disconnect inactive subscribers (5 min timeout)
- Track active subscriptions per execution_id

### Memory
- Don't store full execution history in memory
- Load from JSON files on demand
- Stream only active events

---

## Implementation Phases

**Phase 5.5.2.I2a (30 min):** Create TransparencyEventEmitter
**Phase 5.5.2.I2b (20 min):** Extend server_websocket.py
**Phase 5.5.2.I2c (20 min):** Integrate with CodeImplementationAgent
**Phase 5.5.2.I2d (20 min):** Create tests
**Total:** ~90 minutes

---

**Architecture Document Created:** 2026-11-02T03:18:24+01:00  
**Status:** Ready for Implementation

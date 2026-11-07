---
title: "Frontend ReasoningPanel - Phase 5.5.2.I4 Concept"
project: "kicli-code-assist"
scope: "frontend-web"
purpose: "React component design for real-time agent transparency data visualization"
created: 2026-11-02T03:58:00+01:00
updated: 2026-11-07T20:57:37+01:00
update_reason: "Standardized YAML header; updated scope and relations; fixed title format"
status: "active"
agent_project: "kicli-code-assist"
relations:
  - target: ../README.md
    type: parent
  - target: README.md
    type: parent
  - target: ../architecture/PHASE_5_5_2_I2_WEBSOCKET_ARCHITECTURE.md
    type: reference
semantic_blocks:
  - id: component-architecture
    title: Component Architecture
  - id: hooks-implementation
    title: Hooks Implementation
  - id: component-details
    title: Component Details
  - id: styling-strategy
    title: Styling Strategy
  - id: integration-points
    title: Integration Points
  - id: performance-considerations
    title: Performance Considerations
  - id: testing-strategy
    title: Testing Strategy
  - id: implementation-checklist
    title: Implementation Checklist
  - id: next-steps
    title: Next Steps
---

# Frontend ReasoningPanel - Phase 5.5.2.I4 Concept

**Objective:** Create React component for displaying real-time agent transparency data

**Status:** Planning phase, ready for implementation  
**Estimated Duration:** 120 minutes

---

## Component Architecture [component-architecture]

### Entry Point: ReasoningPanel

```typescript
interface ReasoningPanelProps {
  executionId: string;
  onClose?: () => void;
  autoScroll?: boolean;
  maxHeight?: string;
}

export function ReasoningPanel({ executionId, onClose, autoScroll = true }: ReasoningPanelProps) {
  // 1. Subscribe to WebSocket events
  // 2. Fetch initial trace data
  // 3. Render event timeline
  // 4. Show metrics sidebar
  // 5. Display cost breakdown
}
```

### Data Flow

```
ReasoningPanel
├─ useReasoningStream hook (WebSocket)
│  ├─ Subscribe to /agent/execution namespace
│  ├─ Join room: execution:{executionId}
│  └─ Collect events: agent:decision|execution|error|llm_call|metric|session_end
│
├─ useExecutionHistory hook (REST API)
│  ├─ Fetch /api/traces/{executionId}
│  ├─ Fetch /api/traces/{executionId}/events
│  ├─ Fetch /api/traces/{executionId}/cost
│  └─ Fetch /api/traces/{executionId}/metrics
│
├─ EventTimeline component
│  ├─ DecisionEventItem (options, selected, confidence)
│  ├─ ExecutionEventItem (action, result, duration)
│  ├─ ErrorEventItem (error type, recovery)
│  ├─ LLMCallEventItem (model, tokens, cost)
│  └─ MetricEventItem (phase, counters)
│
├─ MetricsSidebar component
│  ├─ ExecutionStats (total time, events, decisions)
│  ├─ CostBreakdown (total cost, by model, by phase)
│  ├─ TokenUsage (input, output, total)
│  └─ PhaseTimeline (start, end, duration per phase)
│
└─ StatusFooter component
   ├─ Status indicator (running/completed/error)
   ├─ Total duration
   └─ Action buttons (export, refresh)
```

---

## Hooks Implementation [hooks-implementation]

### 1. useReasoningStream

```typescript
interface ReasoningEvent {
  execution_id: string;
  timestamp: string;
  event_type: "decision" | "execution" | "error" | "llm_call" | "metric" | "session_end";
  // ... event-specific fields
}

interface ReasoningStreamState {
  events: ReasoningEvent[];
  isConnected: boolean;
  isLoading: boolean;
  error?: string;
  status: "idle" | "running" | "completed" | "error";
}

function useReasoningStream(executionId: string): ReasoningStreamState {
  const [events, setEvents] = useState<ReasoningEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [status, setStatus] = useState<"idle" | "running" | "completed" | "error">("idle");
  
  useEffect(() => {
    const socket = io(window.location.origin, {
      namespace: '/agent/execution'
    });
    
    socket.on('connect', () => setIsConnected(true));
    socket.on('disconnect', () => setIsConnected(false));
    
    socket.emit('subscribe:execution', { execution_id: executionId });
    
    // Listen for all event types
    const handlers = {
      'agent:decision': (event) => setEvents(prev => [...prev, { ...event, event_type: 'decision' }]),
      'agent:execution': (event) => setEvents(prev => [...prev, { ...event, event_type: 'execution' }]),
      'agent:error': (event) => setEvents(prev => [...prev, { ...event, event_type: 'error' }]),
      'agent:llm_call': (event) => setEvents(prev => [...prev, { ...event, event_type: 'llm_call' }]),
      'agent:metric_update': (event) => setEvents(prev => [...prev, { ...event, event_type: 'metric' }]),
      'agent:session_end': (event) => {
        setEvents(prev => [...prev, { ...event, event_type: 'session_end' }]);
        setStatus('completed');
      },
      'agent:error': (data) => setStatus('error'),
    };
    
    Object.entries(handlers).forEach(([key, handler]) => {
      socket.on(key, handler);
    });
    
    setStatus('running');
    
    return () => {
      socket.emit('unsubscribe:execution', { execution_id: executionId });
      socket.disconnect();
    };
  }, [executionId]);
  
  return { events, isConnected, status };
}
```

### 2. useExecutionHistory

```typescript
interface ExecutionTrace {
  execution_id: string;
  agent_id: string;
  created_at: string;
  ended_at?: string;
  duration_seconds?: number;
}

interface ExecutionHistory {
  trace: ExecutionTrace | null;
  events: ReasoningEvent[];
  cost: { total_cost: number; total_calls: number; total_tokens: number } | null;
  metrics: Record<string, any> | null;
  isLoading: boolean;
  error?: string;
}

function useExecutionHistory(executionId: string): ExecutionHistory {
  const [trace, setTrace] = useState(null);
  const [events, setEvents] = useState<ReasoningEvent[]>([]);
  const [cost, setCost] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | undefined>();
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [traceRes, eventsRes, costRes, metricsRes] = await Promise.all([
          fetch(`/api/traces/${executionId}`),
          fetch(`/api/traces/${executionId}/events`),
          fetch(`/api/traces/${executionId}/cost`),
          fetch(`/api/traces/${executionId}/metrics`),
        ]);
        
        if (traceRes.ok) setTrace(await traceRes.json());
        if (eventsRes.ok) setEvents(await eventsRes.json());
        if (costRes.ok) setCost(await costRes.json());
        if (metricsRes.ok) setMetrics(await metricsRes.json());
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, [executionId]);
  
  return { trace, events, cost, metrics, isLoading, error };
}
```

---

## Component Details [component-details]

### EventTimeline Component

Displays chronological event sequence with visual markers:

```typescript
function EventTimeline({ events, autoScroll }: { events: ReasoningEvent[], autoScroll: boolean }) {
  const scrollRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events, autoScroll]);
  
  return (
    <div className="event-timeline" ref={scrollRef}>
      {events.map((event, i) => (
        <EventItem key={i} event={event} index={i} />
      ))}
    </div>
  );
}
```

### EventItem Components

#### DecisionEventItem
- Show all options considered
- Highlight selected option
- Display confidence score (0-1)
- Optional reasoning text

```typescript
function DecisionEventItem({ event }: { event: ReasoningEvent }) {
  return (
    <div className="event decision-event">
      <div className="icon">🔀</div>
      <div className="content">
        <h4>Decision</h4>
        <div className="options">
          {event.options_considered.map((opt, i) => (
            <span key={i} className={opt === event.option_selected ? 'selected' : ''}>
              {opt}
            </span>
          ))}
        </div>
        <span className="confidence">
          Confidence: {(event.confidence_score * 100).toFixed(0)}%
        </span>
      </div>
    </div>
  );
}
```

#### LLMCallEventItem
- Model name (gpt-4o, claude-3, etc.)
- Input/output token counts
- Cost in USD
- Latency in ms

```typescript
function LLMCallEventItem({ event }: { event: ReasoningEvent }) {
  return (
    <div className="event llm-event">
      <div className="icon">💰</div>
      <div className="content">
        <h4>{event.model} API Call</h4>
        <div className="tokens">
          <span>Input: {event.input_tokens}</span>
          <span>Output: {event.output_tokens}</span>
          <span>Total: {event.total_tokens}</span>
        </div>
        <div className="cost-latency">
          <span className="cost">${event.cost.toFixed(4)}</span>
          <span className="latency">{event.latency_ms}ms</span>
        </div>
      </div>
    </div>
  );
}
```

#### ErrorEventItem
- Error type (exception class)
- Error message
- Recovery suggestion
- Visual alert styling

```typescript
function ErrorEventItem({ event }: { event: ReasoningEvent }) {
  return (
    <div className="event error-event alert">
      <div className="icon">⚠️</div>
      <div className="content">
        <h4>{event.error_type}</h4>
        <p className="message">{event.message}</p>
        {event.recovery_suggestion && (
          <p className="recovery">💡 Try: {event.recovery_suggestion}</p>
        )}
      </div>
    </div>
  );
}
```

### MetricsSidebar Component

Displays aggregated metrics:

```typescript
function MetricsSidebar({ events, cost, metrics }: {
  events: ReasoningEvent[],
  cost: any,
  metrics: any
}) {
  const totalTime = calculateTotalTime(events);
  const decisionCount = events.filter(e => e.event_type === 'decision').length;
  const errorCount = events.filter(e => e.event_type === 'error').length;
  const llmCallCount = events.filter(e => e.event_type === 'llm_call').length;
  
  return (
    <div className="metrics-sidebar">
      <div className="stats">
        <Stat label="Duration" value={formatDuration(totalTime)} />
        <Stat label="Events" value={events.length} />
        <Stat label="Decisions" value={decisionCount} />
        <Stat label="LLM Calls" value={llmCallCount} />
        <Stat label="Errors" value={errorCount} icon={errorCount > 0 ? '⚠️' : '✓'} />
      </div>
      
      {cost && (
        <div className="cost-summary">
          <h3>Cost Analysis</h3>
          <CostBreakdown cost={cost} />
        </div>
      )}
      
      {metrics && (
        <div className="metrics-summary">
          <h3>Performance</h3>
          <MetricsBreakdown metrics={metrics} />
        </div>
      )}
    </div>
  );
}
```

---

## Styling Strategy [styling-strategy]

### CSS Layout

```css
.reasoning-panel {
  display: flex;
  height: 100%;
  gap: 16px;
  background: var(--color-bg-primary);
  padding: 16px;
  border-radius: 8px;
  overflow: hidden;
}

.event-timeline {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.event {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-left: 4px solid var(--color-border);
  background: var(--color-bg-secondary);
  border-radius: 4px;
  animation: slideIn 0.3s ease-out;
}

.event.decision-event { border-left-color: var(--color-blue); }
.event.llm-event { border-left-color: var(--color-green); }
.event.error-event { border-left-color: var(--color-red); }
.event.execution-event { border-left-color: var(--color-yellow); }

.metrics-sidebar {
  width: 300px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: var(--color-bg-secondary);
  padding: 12px;
  border-radius: 4px;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

---

## Integration Points [integration-points]

### 1. With Existing Agent UI
- Add ReasoningPanel to AgentChatContainer
- Toggle visibility with button or keyboard shortcut
- Pass execution_id from active execution

### 2. With WebSocket Server
- Already implemented in Phase I2
- WebSocket namespace: `/agent/execution`
- Event types: `agent:decision|execution|error|llm_call|metric|session_end`

### 3. With REST API
- Already implemented in Phase I3
- Endpoints for historical queries
- Cost and metrics analysis

---

## Performance Considerations [performance-considerations]

### Memory Management
- Limit displayed events to last 1000
- Virtualize long lists with react-window
- Clean up WebSocket listeners on unmount
- Debounce scroll events

### Network Optimization
- Single REST API call for historical data
- WebSocket for incremental events (minimal payload)
- Batch metric updates every 5 seconds
- Gzip response compression

### Rendering Performance
- Memoize event items with React.memo
- Use useMemo for computed values (total cost, duration)
- Lazy-load metrics visualizations (chart.js, recharts)
- Virtual scrolling for 1000+ events

---

## Testing Strategy [testing-strategy]

### Unit Tests (30 min)
- Hook tests (useReasoningStream, useExecutionHistory)
- Component tests (EventItem, MetricsSidebar)
- Utility tests (formatting, calculations)

### Integration Tests (20 min)
- WebSocket subscription flow
- REST API data loading
- Event rendering pipeline
- Metric aggregation

### Visual Tests (10 min)
- Snapshot tests for components
- Timeline layout correctness
- Metrics display accuracy

---

## Implementation Checklist [implementation-checklist]

### Phase I4a: Hooks & Utilities (40 min)
- [ ] useReasoningStream hook
- [ ] useExecutionHistory hook
- [ ] Formatting utilities (timestamp, duration, cost)
- [ ] Calculation utilities (totals, aggregates)
- [ ] Unit tests for hooks

### Phase I4b: Components (50 min)
- [ ] ReasoningPanel main component
- [ ] EventTimeline component
- [ ] EventItem variants (Decision, Execution, Error, LLMCall, Metric)
- [ ] MetricsSidebar component
- [ ] StatusFooter component
- [ ] Component tests

### Phase I4c: Styling & Integration (30 min)
- [ ] CSS styling (timeline, events, sidebar)
- [ ] Responsive layout
- [ ] Integration with Agent UI
- [ ] Export button (PDF, JSON, Markdown)
- [ ] Visual tests

---

## Next Steps [next-steps]

1. **Implement I4a:** Hooks and utilities
2. **Implement I4b:** Components and rendering
3. **Implement I4c:** Styling and integration
4. **Testing:** Unit, integration, visual
5. **Documentation:** API docs, usage examples
6. **Demo:** Real execution trace walkthrough

---

**Concept Created:** 2026-11-02T03:58:00+01:00  
**Status:** Ready for implementation  
**Estimated Duration:** 120 minutes
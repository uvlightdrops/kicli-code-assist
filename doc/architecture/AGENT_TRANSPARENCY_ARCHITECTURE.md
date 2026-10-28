# Agent Transparency Architecture
## Live Agent Thinking Visualization in WebUI

**Status:** Design Phase  
**Goal:** Enable real-time visibility into agent workflows from multiple input channels  
**Priority:** Phase 5.5 (Post-Autonomy Transparency)

---

## 1. Vision & Requirements

### User Experience Goal
```
User at WebUI                    Copilot Supervisor (CLI/API)
    ↓                                    ↓
    └─────── Shared Agent State ────────┘
             ↓         ↓         ↓
       Thinking    Execution  Results
          (Live streamed to both)
```

### Core Requirements
1. **Multi-Channel Input:** Manual (WebUI) + Autonomous (API/CLI supervision)
2. **Unified Agent State:** Single source of truth for agent progress
3. **Real-Time Streaming:** Agent thinking → both channels simultaneously
4. **Audit Trail:** Full history of decisions, supervisory interventions
5. **Intervention Points:** Both channels can pause/redirect workflow

---

## 2. Current State Analysis

### What We Have ✅
- **WebSocket Infrastructure:** `server_websocket.py` with reasoning:subscribe
- **Streaming Reasoning Agent:** `StreamingReasoningAgent` class exists
- **Phase 5.4 Implementation:** `apply_with_full_autonomy()` method works (but not streaming)
- **Frontend WebUI:** React-based project browser with modal system

### What's Missing ❌
- **Agent Internal State Streaming:** No live "thinking" during autonomy
- **Multi-Channel Orchestration:** No unified agent controller
- **Intervention Queue:** No way to pause/redirect from multiple channels
- **Frontend Visualization:** No panels showing agent workflow steps
- **State Synchronization:** No real-time sync between WebUI and supervisor

---

## 3. Architecture Design

### 3.1 Agent State Model

```python
@dataclass
class AgentStateSnapshot:
    """Current state of executing agent."""
    agent_id: str                      # e.g., "impl-001"
    task_id: str                       # e.g., "ki-knowledge-ingestion"
    status: str                        # "thinking", "executing", "paused", "done", "error"
    current_phase: str                 # "analysis", "planning", "coding", "testing", "rollback"
    progress: int                      # 0-100
    thinking_step: Optional[Dict]      # {"type": "decision", "reason": "...", "timestamp": ...}
    recent_actions: List[str]          # ["Opened file X", "Generated function Y", ...]
    next_action: str                   # What's about to happen
    error: Optional[Dict]              # If status == "error"
    metadata: Dict                     # Custom fields (branch, commit, test_results, etc.)
```

### 3.2 WebSocket Channels

**Broadcast Channels (Server → All Listeners):**
```
agent:state:{agent_id}         # Real-time state updates (60/sec max)
agent:thinking:{agent_id}      # Thinking steps (one per decision)
agent:action:{agent_id}        # Actions completed (file written, test run, etc.)
agent:error:{agent_id}         # Error events
```

**Command Channels (Listeners → Agent):**
```
agent:pause:{agent_id}         # {"reason": "..."}
agent:resume:{agent_id}        # Resume after pause
agent:redirect:{agent_id}      # {"new_goal": "...", "reason": "..."}
agent:rollback:{agent_id}      # Force rollback
```

### 3.3 Agent Controller (Central Orchestrator)

```python
class AgentController:
    """
    Central controller managing agent execution.
    
    Responsibilities:
    - Manage agent lifecycle (start, pause, resume, stop)
    - Broadcast state to all subscribed channels
    - Queue and process intervention commands
    - Persist execution history
    - Handle multiple input channels (WebUI, CLI supervisor, API)
    """
    
    async def execute_with_streaming(
        self,
        agent: CodeImplementationAgent,
        goal: GoalDefinition,
        context: Dict,
    ) -> ExecutionResult:
        """
        Execute agent with full state streaming.
        
        Flow:
        1. Create agent_id and task_id
        2. Broadcast "thinking" state
        3. Execute each phase with state updates
        4. Check intervention queue after each step
        5. Handle pause/resume/redirect
        6. Broadcast final result
        """
        
    async def on_intervention_command(
        self,
        agent_id: str,
        command: InterventionCommand,
    ) -> None:
        """Process pause/resume/redirect from any channel."""
        
    async def broadcast_state(
        self,
        agent_id: str,
        snapshot: AgentStateSnapshot,
    ) -> None:
        """Send state to all subscribed channels (WebSocket)."""
```

### 3.4 Frontend Visualization Component

**New React Component: `AgentWorkflowPanel.tsx`**

```typescript
interface AgentWorkflowState {
  agentId: string;
  taskId: string;
  status: "thinking" | "executing" | "paused" | "done" | "error";
  progress: number;
  currentPhase: string;
  thinkingSteps: ThinkingStep[];
  recentActions: string[];
  nextAction: string;
  error?: ErrorInfo;
}

export function AgentWorkflowPanel() {
  // Subscribe to agent:state:* channels
  // Display:
  //   - Progress bar with current phase
  //   - Thinking steps timeline
  //   - Action log (scrollable)
  //   - Error panel (if error)
  //   - Control buttons (Pause, Resume, Redirect, Rollback)
  //   - Real-time metric display
}
```

**Layout:**
```
┌─────────────────────────────────────────────────┐
│ Agent Workflow: ki-knowledge-ingestion          │
│ Status: Executing [████████░░] 72%              │
├─────────────────────────────────────────────────┤
│ Phase 5.4.2: Testing                            │
│ Next: Running pytest suite                      │
├─────────────────────────────────────────────────┤
│ Thinking Timeline:                              │
│ • [12:34:56] Decision: Use SourceAdapter ABC    │
│ • [12:34:57] Reason: Enables extensibility      │
│ • [12:34:58] Planning: 3 concrete adapters      │
├─────────────────────────────────────────────────┤
│ Action Log:                                     │
│ ✓ Created ki_knowledge/ingestion/ingestion.py   │
│ ✓ Generated SourceAdapter base class            │
│ ✓ Committed to feature branch                   │
│ ⟳ Running pytest tests...                       │
├─────────────────────────────────────────────────┤
│ [⏸ Pause] [▶ Resume] [⟳ Redirect] [⟲ Rollback] │
└─────────────────────────────────────────────────┘
```

---

## 4. Implementation Phases

### Phase 5.5.1: Agent State Model & Controller
- [ ] Implement `AgentStateSnapshot` dataclass
- [ ] Implement `AgentController` class with lifecycle methods
- [ ] Implement intervention queue system
- [ ] Add state persistence (JSON + optional DB)
- **Deliverable:** Agent can track & broadcast state during execution

### Phase 5.5.2: WebSocket Broadcasting
- [ ] Extend `server_websocket.py` with agent state channels
- [ ] Implement state serialization (JSON)
- [ ] Rate-limit thinking updates (max 10/sec)
- [ ] Add channel subscription/unsubscription logic
- [ ] Test with multiple concurrent subscribers
- **Deliverable:** Real-time state broadcast working

### Phase 5.5.3: Agent Integration
- [ ] Modify `apply_with_full_autonomy()` to use AgentController
- [ ] Add state snapshots after each phase sub-step
- [ ] Hook in intervention queue checks
- [ ] Stream thinking steps from LLM calls
- **Deliverable:** Autonomy method fully integrated with streaming

### Phase 5.5.4: Frontend Visualization
- [ ] Create `AgentWorkflowPanel.tsx` component
- [ ] Subscribe to `agent:state:*` channels on component mount
- [ ] Render progress bar, phase indicator, thinking timeline
- [ ] Implement action log scrolling
- [ ] Add control buttons (Pause, Redirect, Rollback)
- [ ] Style with project's design system
- **Deliverable:** Frontend panel showing live agent activity

### Phase 5.5.5: Multi-Channel Orchestration
- [ ] Create CLI supervisor command: `kicli-assist agent:supervise {goal}`
- [ ] Supervisor connects via API, subscribes to agent:state:*
- [ ] Implement pause/resume/redirect commands from CLI
- [ ] Add human-in-the-loop prompts for redirects
- [ ] Merge UI and CLI logs into unified audit trail
- **Deliverable:** Both human and supervisor can steer agent

### Phase 5.5.6: Testing & Validation
- [ ] End-to-end test: WebUI + Supervisor + Agent concurrently
- [ ] Stress test: 10+ concurrent agent executions
- [ ] Intervention test: Pause during execution, verify state
- [ ] Rollback test: Trigger rollback from UI, verify cleanup
- [ ] Integration test: ki-knowledge workflow with live visibility
- **Deliverable:** All systems working together, documented

---

## 5. Data Flow Diagrams

### 5.1 Normal Autonomy Flow (Current)
```
Goal → CodeImplementationAgent → apply_with_full_autonomy()
         ├─ Phase 5.4.1: Git
         ├─ Phase 5.4.2: Tests
         ├─ Phase 5.4.3: State
         ├─ Phase 5.4.4: Quality
         └─ Phase 5.4.5: Rollback
         ↓
       Result (after all phases complete)
```

### 5.2 Enhanced Flow with Streaming (Phase 5.5)
```
                    ┌─────────────────────────┐
                    │  AgentController        │
                    │  - Track state          │
                    │  - Broadcast updates    │
                    │  - Process interventions│
                    └────────────┬────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            ↓                    ↓                    ↓
         WebSocket          WebSocket          CLI/API
         Channel:            Channel:           Supervisor
        agent:state:*       agent:thinking:*    (read-only)
            ↓                    ↓                    ↓
        WebUI Panel          Thinking             Log
        (real-time)          Timeline             Monitor
            ↑                    ↑                    ↑
            └────────────────────┼────────────────────┘
                     Intervention Queue
                  (pause/resume/redirect)
```

### 5.3 Multi-Input Scenario
```
USER (WebUI)                    SUPERVISOR (CLI)
    │                               │
    ├─→ "Redirect to X" ────→ Intervention Queue ←─ "Pause after phase 2"
    │                               │
    └─ Listen to: state, thinking   │  Listen to: state, actions, errors
                                    ↓
                          CodeImplementationAgent
                          + AgentController
                          + Streaming
                                    │
                          Broadcast to both listeners
                                    │
                                    ↓
            ┌───────────────────────┴───────────────────┐
            │                                           │
        WebUI Panel                                CLI Monitor
        Shows progress,                       Shows log output
        thinking, actions                     and metrics
```

---

## 6. Code Locations & Changes

### New Files
```
kicli_code_assist/agent/
  ├─ agent_controller.py          (new: AgentController class)
  ├─ agent_state.py               (new: State models & snapshots)
  └─ intervention.py              (new: Intervention queue system)

kicli_code_assist/web/
  └─ agent_streaming.py           (new: WebSocket event handlers)

web/frontend/src/components/
  └─ AgentWorkflowPanel.tsx        (new: React visualization)

kicli_code_assist/
  └─ commands/
      └─ agent.py                 (new: CLI supervisor commands)
```

### Modified Files
```
kicli_code_assist/agent/code_implementation.py
  ├─ integrate AgentController
  ├─ add state snapshots
  └─ check intervention queue

kicli_code_assist/web/server_websocket.py
  ├─ add agent:state:* handlers
  ├─ add agent:pause handlers
  └─ add agent:redirect handlers

web/frontend/src/pages/ProjectPage.tsx
  ├─ add AgentWorkflowPanel
  └─ subscribe to agent channels
```

---

## 7. Example Usage Scenarios

### Scenario A: User Watching ki-knowledge Development
```
1. User opens kicli-assist WebUI
2. Selects: "Load Project: ki-knowledge"
3. Clicks: "New Task: Implement Hybrid Search"
4. Submits goal through WebUI form
5. AgentWorkflowPanel appears, showing:
   - Real-time progress bar
   - Agent thinking steps (decisions being made)
   - Action log (files being written, tests running)
6. User can:
   - Watch live (read-only)
   - Pause if something looks wrong
   - Redirect to different goal
   - Rollback if needed
```

### Scenario B: Supervisor Steering from CLI
```
1. User starts autonomous task via WebUI
2. Copilot opens terminal, runs:
   $ kicli-assist agent:supervise ki-knowledge-ingestion
3. Supervisor connects, sees:
   [12:34:56] Agent starting: impl-001
   [12:34:57] Analyzing ki-knowledge structure...
   [12:34:59] Decision: Use SourceAdapter pattern
   [12:35:01] Planning 3 concrete adapters...
   [12:35:03] Generating code...
4. Copilot can:
   - Send: pause impl-001
   - Wait for confirmation
   - Send: redirect impl-001 "focus on PDF adapter first"
   - Resume: impl-001
```

### Scenario C: Concurrent WebUI + Supervisor
```
User at WebUI                   Copilot Supervisor
   │                                 │
   ├─ Starts autonomous task  ──────→ (sees it starting)
   │                                 │
   ├─ Watches workflow panel  ←────── (pauses after analysis)
   │                                 │
   ├─ Reviews the thoughts   ←────── (shows thinking steps)
   │                                 │
   └─ Clicks "Redirect"      ──────→ (redirects to new goal)
                                    │
                              (resumes with new goal)
                                    │
                            (both see progress)
```

---

## 8. Technical Challenges & Solutions

### Challenge: State Consistency
**Problem:** Multiple channels might have stale state  
**Solution:** Use optimistic updates with server-side reconciliation
- WebSocket broadcasts are authoritative
- Clients show optimistic UI updates immediately
- Server confirms or reverts on next broadcast

### Challenge: Intervention Queue Concurrency
**Problem:** Multiple commands from WebUI and CLI simultaneously  
**Solution:** Serial queue with timestamp-based priority
```python
queue = PriorityQueue()
# Commands ordered by: [timestamp, channel_priority]
# CLI supervisor has slightly higher priority than WebUI
```

### Challenge: LLM Thinking Streaming
**Problem:** Agent uses LLM internally; how to stream thinking from it?  
**Solution:** Hook into LLM call, parse stream for "Thinking" markers
```python
async def stream_llm_response(prompt, on_thinking):
    async for chunk in llm.achat_stream(prompt):
        if chunk.startswith("Thinking:"):
            on_thinking(chunk)
        yield chunk
```

### Challenge: WebSocket Scalability
**Problem:** Many agents running + many watchers = lots of messages  
**Solution:** Use Redis pub/sub or room-based broadcasting
- One room per agent_id
- Only clients in that room receive updates
- Rate-limit to max 10 state updates/sec

---

## 9. Success Criteria

- [x] Agent state model defined
- [ ] AgentController class implemented
- [ ] WebSocket channels working
- [ ] Frontend panel displays live updates (< 500ms latency)
- [ ] CLI supervisor can pause/resume/redirect
- [ ] Multiple concurrent agents don't interfere
- [ ] Intervention queue processes commands correctly
- [ ] Full audit trail of all decisions + interventions
- [ ] End-to-end test passes: WebUI + Supervisor + Agent
- [ ] Documentation complete with examples

---

## 10. Timeline Estimate

| Phase | Tasks | Estimated Hours |
|-------|-------|-----------------|
| 5.5.1 | State model + Controller | 4-5 hours |
| 5.5.2 | WebSocket integration | 3-4 hours |
| 5.5.3 | Agent integration | 3-4 hours |
| 5.5.4 | Frontend component | 4-5 hours |
| 5.5.5 | CLI supervisor | 2-3 hours |
| 5.5.6 | Testing + validation | 3-4 hours |
| **Total** | | **19-25 hours** |

---

## 11. Configuration Decisions (User Input) ✅

### 1. Intervention Priority Strategy
**Decision:** Configurable, Default = **(C) User decides at prompt time**
- **Rationale:** Allows practice to determine best approach; supports concurrent work patterns already in use worldwide
- **Future Options:** Settings panel to switch between:
  - A) First-come-first-served queue (FIFO)
  - B) Supervisor always wins (CLI has higher authority)
  - C) User decides at prompt time (interactive conflict resolution)
- **Implementation:** `ki.yaml` config:
  ```yaml
  agent:
    intervention:
      mode: "user_prompt"  # or "queue", "supervisor"
  ```

### 2. Thinking Detail Level
**Decision:** Configurable, Default = **Balanced**
- **Rationale:** Live monitoring needs enough detail to understand reasoning; minimal is too sparse
- **Options:**
  - `minimal`: Only major decisions (file creation, test runs, commits)
  - `balanced`: Decisions + reasoning (recommended for most workflows) ← DEFAULT
  - `verbose`: All thinking steps including rejected options (for debugging)
- **Implementation:** `ki.yaml` config:
  ```yaml
  agent:
    streaming:
      thinking_detail: "balanced"  # or "minimal", "verbose"
  ```

### 3. Auto-Rollback on Error
**Decision:** Default = **Auto-rollback enabled**
- **Rationale:** Faster recovery, reduces supervision overhead, enables true autonomy
- **When Error Occurs:**
  1. Agent logs the error with full context
  2. Broadcasts error event to all listeners
  3. Automatically triggers Phase 5.4.5 (Rollback Manager)
  4. Cleans up: uncommitted changes, resets branch, reverts commits
  5. Broadcasts rollback completion
  6. Ready for next goal or manual intervention
- **Configuration:** `ki.yaml`:
  ```yaml
  agent:
    rollback:
      auto_on_error: true  # false to require manual decision
      log_error_artifacts: true  # keep error logs for analysis
  ```

---

### Configuration Example (ki.yaml with All Agent Settings)

```yaml
agent:
  # Intervention strategy when both WebUI and Supervisor send commands
  intervention:
    mode: "user_prompt"        # "queue" (FIFO) | "supervisor" (CLI wins) | "user_prompt" (ask)
    
  # Real-time thinking visibility
  streaming:
    thinking_detail: "balanced" # "minimal" | "balanced" | "verbose"
    state_broadcast_rate: 10    # max updates per second
    websocket_timeout: 30       # seconds before disconnection
    
  # Error recovery strategy
  rollback:
    auto_on_error: true        # Auto-rollback vs manual decision
    log_error_artifacts: true  # Keep error logs for analysis
    preserve_branch: false     # Keep feature branch after rollback
    
  # State persistence
  state:
    persistence: "json"         # "json" | "sqlite" (future)
    retention: "session"        # "session" | "7days" | "permanent" (future)
    export_on_completion: true  # Save to file after execution
```

---

### When & How to Adjust Settings

**At Runtime (Environment Variables):**
```bash
export KICLI_AGENT_INTERVENTION_MODE=supervisor
export KICLI_AGENT_THINKING_DETAIL=verbose
kicli-assist agent:run ki-knowledge-ingestion
```

**In Project Config (ki.yaml):**
```yaml
agent:
  intervention:
    mode: "user_prompt"
  streaming:
    thinking_detail: "balanced"
```

**Via WebUI (Future):**
- Settings panel in agent workflow widget
- Real-time adjustment during execution
- Per-execution overrides

**Philosophy:** Start conservative (user_prompt, balanced, auto-rollback), adjust based on real-world usage patterns.

---

## 12. Reference Implementation Notes

- `StreamingReasoningAgent` already exists; can be extended
- `apply_with_full_autonomy()` in `code_implementation.py` is the integration point
- `server_websocket.py` has room channel infrastructure already
- React frontend has modal system; AgentWorkflowPanel fits naturally
- Config system ready: settings go in ki.yaml + environment variable overrides

---

## 13. Next Step: Phase 5.5.1 Implementation

**Ready to start Phase 5.5.1 (Agent State Model & Controller)?**

First deliverable:
- `AgentStateSnapshot` dataclass (represents current agent state)
- `AgentController` class (manages lifecycle, broadcasts, intervention queue)
- Integration hooks in `apply_with_full_autonomy()`
- State persistence to JSON

Estimated time: 4-5 hours  
Prerequisites: None (builds on Phase 5.4)

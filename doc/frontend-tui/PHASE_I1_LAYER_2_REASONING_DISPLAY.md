# Phase I1: Layer 2 Reasoning Display

**Date**: 2026-11-07  
**Component**: Agent Tabs (Right Panel)  
**Intelligence Layer**: Layer 2 (Workflow Orchestration)  

## Overview

The TUI now displays the **Layer 2 (Workflow Orchestration)** reasoning process in the bottom panel ("Chunks"). This shows what the MetaCoordinationAgent is doing internally.

## Architecture

### Request Flow
```
User Action (FileTree Select + Click "Analyze")
  ↓
TUI: agent_tabs._perform_analysis()
  ↓
HTTP POST: /api/agent/route
  ├─ file_path: absolute
  ├─ project_root: absolute
  └─ scope: "file"
  ↓
Backend: MetaCoordinationAgent (Layer 2)
  ├─ Intent Detection: "suggest" (confidence: 0.5)
  ├─ Workflow Routing: "analysis"
  ├─ Agent Selection: [metrics, refactoring, dependencies]
  └─ Execution Coordination
  ↓
Response: {
  "answer": "...",           // Top panel
  "tabs": { ... },           // Reasoning data
  "agents_used": [...],      // Which agents ran
  "intent": {...},           // What was detected
  "timing": {...}            // Performance metrics
}
```

### UI Layout

```
┌─────────────────────────────────────────────┐
│  Agent Tabs (Right Panel)                   │
├─────────────────────────────────────────────┤
│  [Analyze Button]                           │
│  Explain | Metrics | Refactor | ...         │
├─────────────────────────────────────────────┤
│                                             │
│  ╔════════════════════════════════════════╗ │
│  ║ Answer (Conversational Response)       ║ │  <- top: agent_tabs.set_response()
│  ║                                        ║ │
│  ║ "Query: Analyze this file..."          ║ │
│  ║                                        ║ │
│  ║ (scrollable, shows main output)        ║ │
│  ╚════════════════════════════════════════╝ │
│                                             │
│  ╔════════════════════════════════════════╗ │
│  ║ Thinking / Reasoning Chunks            ║ │  <- bottom: agent_tabs.set_chunks()
│  ║                                        ║ │
│  ║ [execution] Agents ready: metrics,     ║ │
│  ║            refactoring, dependencies   ║ │
│  ║                                        ║ │
│  ║ (shows Layer 2 orchestration thinking) ║ │
│  ╚════════════════════════════════════════╝ │
│                                             │
└─────────────────────────────────────────────┘
```

## Layer 2 Reasoning

The MetaCoordinationAgent (Phase 5.1) performs 6-stage orchestration:

1. **Intent Detection**: What does the user want? (Explain, Refactor, etc.)
2. **Workflow Routing**: Which workflow path? (analysis, implementation, etc.)
3. **Agent Selection**: Which agents should run? (metrics, refactoring, dependencies)
4. **Execution**: Run the selected agents with coordination
5. **Aggregation**: Combine results from multiple agents
6. **Generation**: Generate conversational answer

## Response Parsing (HTTP Client)

The `http_client.py` extracts chunks using 3 strategies:

### Strategy 1: Explicit Chunks
```python
tabs.{tab_name}.chunks[] = [
  {type: "issue", content: "..."},
  {type: "solution", content: "..."}
]
```

### Strategy 2: Execution Results (Current Default)
```python
tabs.analysis.execution_results.{key} = "Agent X ready for execution"
# Extracted as chunks with type="execution"
```

### Strategy 3: Agents Used Context
```python
agents_used: ["metrics", "refactoring", "dependencies"]
# Fallback: create chunk showing which agents ran
```

## Chunk Types

| Type | Meaning | Display |
|------|---------|---------|
| `execution` | Agent execution info | "Agents ready for execution" |
| `observation` | Agent observation | Findings from analysis |
| `issue` | Problem identified | Code quality issue |
| `solution` | Suggested fix | Code improvement |
| `info` | General info | Context/metadata |

## Example Response

### Raw Backend Response
```json
{
  "success": true,
  "answer": "Query: Analyze this file",
  "intent": {
    "type": "suggest",
    "confidence": 0.5
  },
  "agents_used": ["metrics", "refactoring", "dependencies"],
  "tabs": {
    "analysis": {
      "execution_results": {
        "analysis": "Agents ['metrics', 'refactoring', 'dependencies'] ready for execution"
      }
    }
  },
  "workflow": "analysis"
}
```

### Parsed for UI
```python
response.answer = "Query: Analyze this file"
response.chunks = [
  ("execution", "Agents ['metrics', 'refactoring', 'dependencies'] ready for execution")
]
response.intent = "suggest"
response.agents_used = ["metrics", "refactoring", "dependencies"]
```

### UI Display
- **Top Panel** (answer): "Query: Analyze this file"
- **Bottom Panel** (chunks): "Agents [...] ready for execution"

## Phase I1.1: Streaming Reasoning (Future)

Currently (Phase I1):
- Backend does all coordination synchronously (2-5s delay)
- Single response at end
- User sees "thinking" after it's done

Future (Phase I1.1):
- WebSocket streaming of reasoning steps
- Real-time updates as agents run
- User sees: "Intent detected..." → "Routing workflow..." → "Selecting agents..." → "Done!"
- Much faster perceived responsiveness

## Testing

### Via TUI (Manual)
1. Start Backend: `KI_STAGE=development python -m stackenv start`
2. Start TUI: `python3 -m kicli_code_assist.ui.tui_client`
3. Select file in FileTree
4. Click "Analyze" button
5. Top panel: Shows answer
6. Bottom panel: Shows reasoning/chunks

### Via Script (Automated)
```bash
python3 scripts/test_phase_i1_integration.py
```

## Implementation Details

**File**: `kicli_code_assist/ui/http_client.py`  
**Method**: `_parse_response()` (lines 150-220)

**Strategy Order**:
1. Try explicit chunks from tabs
2. Try execution_results from tabs
3. Try summary from tabs
4. Fall back to agents_used list

**Result**: AnalysisResponse.chunks = List[(chunk_type, content)]

## Next Steps

- [ ] Phase I1.1: WebSocket streaming for real-time reasoning
- [ ] Phase I1.2: Expand execution_results with more detail
- [ ] Phase I1.3: Add reasoning filtering (show/hide details)
- [ ] Phase I2: Cache Layer 2 reasoning for repeated queries

## References

- Layer 2 (Workflow Orchestration): `doc/backend/layer-2-workflow-orchestration/`
- MetaCoordinationAgent: Phase 5.1
- Agent Tabs Widget: `kicli_code_assist/ui/widgets/agent_tabs.py`
- HTTP Client: `kicli_code_assist/ui/http_client.py`


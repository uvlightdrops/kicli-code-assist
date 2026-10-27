# Agent Coordination Architecture

**Phase**: 5 (Developer-Agent Interaction)  
**Status**: Planning  
**Date**: 2026-10-27

## Overview

The agent system operates in a **hierarchical, tool-based architecture** with clear separation between:
1. **Coordination Layer**: Meta-agents that orchestrate workflows
2. **Analysis Layer**: Specialized analysis agents (10 existing)
3. **Implementation Layer**: Agents that make changes (coding, review)
4. **Tool Layer**: Atomic operations (LLM calls, file I/O, git)

```
┌─────────────────────────────────────────────────────────────────┐
│ Developer → Chat Input (WebSocket)                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                    ┌────▼─────────────────────────────────────┐
                    │ 1. MetaCoordinationAgent (Orchestration) │
                    │    • Parse intent                        │
                    │    • Determine workflow                  │
                    │    • Route to sub-agents                 │
                    └────┬─────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┬────────────────────┐
        │                │                │                    │
   ┌────▼────────┐  ┌───▼──────┐   ┌────▼──────┐    ┌────────▼───┐
   │ Analysis    │  │ Coding   │   │ Review    │    │ Research   │
   │ Agents      │  │ Agent    │   │ Agent     │    │ Agent      │
   │ (10x)       │  │          │   │           │    │            │
   └────┬────────┘  └───┬──────┘   └────┬──────┘    └────────┬───┘
        │                │                │                    │
   ┌────▼────────────────▼────────────────▼────────────────────▼──┐
   │ Tool Layer (Atomic Operations)                               │
   │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
   │ │ LLM Tool │ │ File I/O │ │ Git Tool │ │ AST Tool │ ...    │
   │ └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
   └────────────────────────────────────────────────────────────┘
        │
        └────────────────────────┬──────────────────────────────┐
                                 │                              │
                    ┌────────────▼──────────┐    ┌─────────────▼──┐
                    │ WebSocket Streaming   │    │ File Changes   │
                    │ (Reasoning Process)   │    │ (Diffs/Tabs)   │
                    └──────────────────────┘    └────────────────┘
                                 │
                    ┌────────────▼──────────┐
                    │ Frontend UI           │
                    │ • Chat Tab            │
                    │ • Analysis Tab        │
                    │ • Editor Tab          │
                    └──────────────────────┘
```

## Component Inventory

### Analysis Layer (Phase 3 - Existing ✅)

| Agent | Lines | Purpose |
|-------|-------|---------|
| AgentIntentDetector | - | Intent classification (7 types) |
| AgentExecutor | - | Parallel agent execution |
| ResultAggregator | - | Synthesis of agent outputs |
| AnswerGenerator | 245 | Conversational responses (Phase 2E) |
| DependencyAnalyzer | - | Import/circular dependency analysis |
| RefactoringAnalyzer | - | 5 refactoring patterns |
| CodeMetricsAnalyzer | - | Maintainability, complexity |
| ReasoningAgent | - | Multi-step reasoning with visualization |
| StreamingReasoningAgent | - | Real-time WebSocket streaming |
| LLMEnsemble | - | OpenAI + Ollama voting |

### Coordination Layer (Phase 5 - To Build 🔨)

**MetaCoordinationAgent** (NEW - ~300 lines)
- Receives developer query from chat
- Calls IntentDetector to classify intent
- Determines workflow (analysis-only vs. implementation)
- Routes to appropriate sub-agents
- Coordinates parallel execution
- Aggregates results
- Returns structured response

**Example Workflows**:
```
Query: "Erkläre diese Datei"
  → Intent: "explain"
  → Workflow: "analysis"
  → Agents: [Metrics, Refactoring, Dependencies]
  → Result: Aggregated analysis + answer

Query: "Implementiere ein Feature: User Authentication"
  → Intent: "implement"
  → Workflow: "coding"
  → Agents: [CodingAgent + ToolSystem]
  → Result: Code changes + diff view

Query: "Review my code"
  → Intent: "review"
  → Workflow: "review"
  → Agents: [ReviewAgent + Analysis]
  → Result: Review comments + refactoring suggestions
```

### Implementation Layer (Phase 5 - To Build 🔨)

**CodingAgent** (~400 lines)
- Takes implementation task
- Uses LLM to generate code changes
- Calls FileWriteTool to create/modify files
- Validates syntax/imports
- Returns modified file list

**ReviewAgent** (~250 lines)
- Analyzes code changes
- Checks against best practices
- Calls DiffTool to generate diffs
- Uses LLMEnsemble for multiple perspectives
- Returns review comments with severity

**ResearchAgent** (~200 lines)
- Researches patterns, APIs, dependencies
- Uses WebSearchTool, DocParserTool
- Summarizes findings for context
- Returns relevant code examples

### Tool Layer (Phase 5 - To Build 🔨)

**LLM Tool**
- Wrapper around ki-core AsyncOpenAIClient
- Supports streaming, function calling
- Caches responses
- Handles retries/fallbacks

**File I/O Tools**
- `ReadFileTool(path)` → content
- `WriteFileTool(path, content)` → success
- `ListDirTool(path, pattern)` → files
- `CreateFileTool(path, template)` → new file

**Git Tools**
- `GitDiffTool(file_path)` → diff
- `GitStageTool(files)` → staged changes
- `GitStatusTool()` → status
- `GitCommitTool(message)` → commit

**AST Tools**
- `ParseFileTool(path)` → AST
- `FindSymbolTool(symbol)` → locations
- `ValidateSyntaxTool(code)` → errors

**Code Tools**
- `FormatCodeTool(code)` → formatted
- `LintCodeTool(code)` → issues
- `RunTestsTool(test_paths)` → results

## Interaction Flow

### Chat → Agent Flow (Example: "Erkläre diese Datei")

```
1. Developer types: "Erkläre diese Datei pipeline.py"
   └─ Sent via WebSocket to /api/agent/route

2. MetaCoordinationAgent receives query
   └─ Calls IntentDetector("Erkläre diese Datei")
   └─ Returns: Intent(type="explain", confidence=0.92)

3. MetaCoordinationAgent determines workflow
   └─ Intent="explain" → Workflow="analysis"
   └─ Select agents: [Metrics, Refactoring, Dependencies]

4. Execute analysis agents in parallel
   ├─ CodeMetricsAnalyzer.analyze(pipeline.py)
   │  └─ Returns: ComplexityMetrics, Maintainability
   ├─ RefactoringAnalyzer.analyze(pipeline.py)
   │  └─ Returns: [Suggestion1, Suggestion2, ...]
   └─ DependencyAnalyzer.analyze(pipeline.py)
      └─ Returns: DependencyGraph, CircularDeps

5. ResultAggregator synthesizes results
   └─ Combines metrics + suggestions + dependencies
   └─ Returns: AggregatedResult with tabs

6. AnswerGenerator creates conversational response
   └─ Input: Query + AggregatedResult
   └─ Output: "Die Datei pipeline.py enthält..."

7. WebSocket emit to frontend
   ├─ answer: "Die Datei pipeline.py..."
   ├─ tabs: {
   │    structure: {...},
   │    metrics: {...},
   │    dependencies: {...},
   │    refactor: {...}
   │  }
   └─ timing: {...}

8. Frontend displays in UI
   ├─ Chat tab: Shows detailed answer
   └─ Analysis tab: Shows tabs with request buttons
```

### Implementation Flow (Example: "Implement User Auth")

```
1. Developer types: "Implementiere User Authentication"
   └─ Sent via WebSocket

2. MetaCoordinationAgent receives query
   └─ Calls IntentDetector
   └─ Returns: Intent(type="implement")

3. MetaCoordinationAgent determines workflow
   └─ Intent="implement" → Workflow="coding"
   └─ Select agent: CodingAgent

4. CodingAgent processes task
   └─ Uses LLM to generate implementation plan
   └─ For each required file:
      ├─ Reads existing code context (ReadFileTool)
      ├─ Generates implementation (LLMTool)
      ├─ Writes to disk (WriteFileTool)
      └─ Validates syntax (ValidateSyntaxTool)

5. CodingAgent collects changes
   └─ For each modified file:
      ├─ Calls GitDiffTool to generate diff
      └─ Adds to change list

6. ReviewAgent reviews changes
   ├─ Reads all modified files
   ├─ Analyzes code quality (LintCodeTool)
   ├─ Gets multiple perspectives (LLMEnsemble)
   └─ Generates review comments

7. WebSocket stream results
   ├─ Emit reasoning/thinking process
   ├─ Emit file changes (diffs in tabs)
   ├─ Emit review comments
   └─ Ask for approval

8. Frontend displays changes
   ├─ Chat: Shows implementation plan + review
   ├─ Editor: Shows modified files in tabs
   └─ Diff view: Inline diffs
```

## Design Principles

1. **Layered Architecture**: Each layer has single responsibility
   - Coordination: Workflow orchestration
   - Analysis: Understanding code
   - Implementation: Making changes
   - Tools: Atomic operations

2. **Stateless Agents**: Agents don't maintain state
   - State passed via parameters
   - Enables testing, parallelization
   - Supports concurrent requests

3. **Tool-Based Design**: Agents use tools, not direct implementations
   - Easier to test (mock tools)
   - Easier to extend (add new tools)
   - Clear boundaries between concerns

4. **Streaming Results**: Long-running operations stream progress
   - WebSocket for real-time thinking
   - File diffs in tabs
   - User sees progress, not just final result

5. **LLM as Reasoning Engine**: LLM used for high-level decisions
   - Intent classification
   - Implementation planning
   - Code review and synthesis
   - NOT for low-level operations (AST, parsing, etc.)

## Implementation Order (Phase 5)

### Phase 5.1: MetaCoordinationAgent (High Priority)
- Orchestrates existing analysis agents
- Extends existing /api/agent/route logic
- Makes workflow routing explicit
- **Effort**: 100 lines refactoring + 200 lines new code

### Phase 5.2: Tool System (High Priority)
- Extract repeated operations into tools
- Build reusable primitives
- Enable agent independence
- **Files**: tools/llm_tool.py, tools/file_tools.py, tools/git_tools.py, tools/ast_tools.py

### Phase 5.3: CodingAgent (Medium Priority)
- Implements actual code changes
- Uses tools to manipulate files
- Integrates with git
- **File**: agent/coding_agent.py (~400 lines)

### Phase 5.4: ReviewAgent (Medium Priority)
- Analyzes code changes
- Multiple LLM perspectives
- Severity scoring
- **File**: agent/review_agent.py (~250 lines)

### Phase 5.5: ResearchAgent (Lower Priority)
- Background research capabilities
- Pattern lookup
- Dependency investigation
- **File**: agent/research_agent.py (~200 lines)

## Data Structures

```python
# Core request
class AgentRequest:
    query: str
    file_path: Optional[str]
    project_root: Path
    scope: str  # "folder" | "project"
    intent_type: Optional[str]  # Pre-classified if known
    context: Optional[Dict]  # User-provided context

# Coordination response
class CoordinationResult:
    intent: AgentIntent
    workflow: str  # "analysis" | "coding" | "review" | "research"
    agents_involved: List[str]
    results: Dict[str, Any]  # Per-agent results
    answer: str  # Conversational response
    actions: List[Action]  # Follow-up actions (if any)
    timing: TimingMetrics

# Tool results
class ToolResult:
    success: bool
    data: Any
    error: Optional[str]
    timing_ms: int
```

## Integration with Existing Code

**Existing components used**:
- IntentDetector (Phase 2A) ✅
- AgentExecutor (Phase 2B) ✅
- ResultAggregator (Phase 2C) ✅
- AnswerGenerator (Phase 2E) ✅
- All 10 analysis agents ✅
- StreamingReasoningAgent for WebSocket ✅
- server_routes.py for HTTP endpoints ✅

**New components to add**:
- MetaCoordinationAgent (5.1)
- Tool system (5.2)
- CodingAgent (5.3)
- ReviewAgent (5.4)
- Optional: ResearchAgent (5.5)

## Success Criteria

Phase 5.1: ✅
- [ ] MetaCoordinationAgent orchestrates existing agents
- [ ] Workflow routing explicit and configurable
- [ ] Chat → Analysis workflow end-to-end working
- [ ] All 3+ agents can run in parallel
- [ ] Results properly aggregated and streamed

Phase 5.2: ✅
- [ ] All tools work independently
- [ ] Tools are mockable for testing
- [ ] Clear error handling
- [ ] Performance acceptable (< 100ms per tool call)

Phase 5.3: ✅
- [ ] CodingAgent can implement simple tasks
- [ ] File creation, modification working
- [ ] Diffs generated correctly
- [ ] Syntax validation catches errors

Phase 5.4: ✅
- [ ] ReviewAgent analyzes code changes
- [ ] Multiple LLM perspectives integrated
- [ ] Review comments structured and actionable

## Open Questions

1. **Multi-Agent Coordination**: Should we use a framework like Langchain, AutoGen, or build custom?
   - **Decision pending**: Assess tradeoffs (complexity vs. control)

2. **State Management**: Where does multi-step workflow state live?
   - **Proposal**: ChatSession in Flask app.config, keyed by session_id

3. **Approval Gate**: Should CodingAgent require approval before writing files?
   - **Proposal**: Show diffs first, ask user to approve/modify

4. **Context Window**: How much code to include in LLM context?
   - **Proposal**: Use AST + file summaries to reduce tokens

## References

- docs/REFACTORING_SERVER_MODULARIZATION.md - Server architecture
- docs/ai_agent_intelligence_architecture.md - Theoretical foundations
- Checkpoint 007 - Phase 1-4 server modularization
- Checkpoint 005 - Phase 2 intelligent agent routing
- Checkpoint 003 - Phase 3 implementation

---
title: Agent Capability Discovery
project: kicli-code-assist
agent_project: kicli-code-assist
scope: Backend Architecture / Layer 3 / Agent Management
purpose: Runtime discovery of available agent capabilities, dynamic capability negotiation, and capability-based routing
created: 2026-11-07T13:32:00+01:00
updated: 2026-11-07T13:32:00+01:00
update_reason: Initial placeholder with semantic schema
status: draft

semantic_blocks:
  - id: capability-registry
    type: architecture
    status: draft
    version: 0.1
  - id: capability-schema
    type: architecture
    status: draft
    version: 0.1
  - id: dynamic-discovery
    type: implementation
    status: draft
    version: 0.1
  - id: capability-routing
    type: implementation
    status: draft
    version: 0.1

relations:
  - target: AGENT_COORDINATION_ARCHITECTURE.md
    type: extends
    reason: "Enhances agent selection stage with capability awareness"
  - target: ../layer-1-raw-llm/IDE_CAPABILITIES.md
    type: depends-on
    reason: "Layer 1 capabilities provide foundation"
  - target: ../layer-2-workflow-orchestration/AGENT_ROUTE_SPEC.md
    type: references
    reason: "Routing endpoint uses discovered capabilities"
---

# Agent Capability Discovery

Design for runtime discovery and negotiation of agent capabilities.

## Capability Registry [capability-registry]

**Status:** TBD

Central registry of available agents and their capabilities:
- ProjectAnalyzer: analyze files, detect patterns, build AST
- LLMAgent: generate code, explain concepts, refactor
- RefactoringAgent: suggest improvements, apply transformations
- TransparencyAgent: trace reasoning, track metrics, stream events
- ... (extensible)

Each agent registers:
- Name & version
- Supported languages
- Supported task types
- Performance characteristics (cost, speed, accuracy)
- Dependencies (what it requires from other layers)

```python
class AgentCapability(BaseModel):
    """Capability metadata for an agent."""
    agent_name: str
    agent_version: str
    capability_id: str  # e.g., "analyze-python-files"
    description: str
    supported_languages: List[str]
    task_types: List[str]  # e.g., ["analysis", "refactoring", "generation"]
    requires: List[str]  # Layer 1 capabilities it needs
    cost: float  # Relative cost (1.0 = baseline)
    speed: float  # Relative speed (1.0 = baseline)
    accuracy: float  # Relative accuracy (0-1)
```

## Capability Schema [capability-schema]

**Status:** TBD

Standard format for describing capabilities:
- **Domain**: What does this agent work with? (Python, TypeScript, git repos, etc.)
- **Operations**: What operations can it perform? (analyze, generate, refactor, explain)
- **Constraints**: Limitations (max file size, max complexity, etc.)
- **Performance**: Timing, cost, quality metrics
- **Preconditions**: What must be true before calling (e.g., "project must be in git repo")
- **Postconditions**: What's guaranteed after (e.g., "output is syntactically valid Python")

```python
# TBD: Formal schema (JSON Schema, OpenAPI, etc.)
# TBD: Version negotiation (agent supports multiple API versions)
```

## Dynamic Discovery [dynamic-discovery]

**Status:** TBD

Runtime capability detection:
- **Startup**: Each agent reports its capabilities
- **Heartbeat**: Periodic health checks (is agent still available?)
- **Hot reload**: New agents can be registered while system running
- **Fallback**: If agent becomes unavailable, route to alternative

```python
# TBD: Registration API
# TBD: Health check endpoint
# TBD: Capability cache invalidation
# TBD: Graceful degradation (fallback capabilities)
```

## Capability-Based Routing [capability-routing]

**Status:** TBD

Use discovered capabilities to select agents:

```python
# Given user request: "Refactor this Python file"
# 1. Query registry: agents with capability "refactor-python"
# 2. Filter by constraints: file size < 10KB, complexity < 50
# 3. Rank by performance: accuracy > 0.9, cost < $0.05
# 4. Select best match & execute
# 5. If fails, try next in ranking
```

Impact on `AGENT_COORDINATION_ARCHITECTURE`:
- **Stage 2 (Workflow Routing)**: Enhanced with capability-based filtering
- **Stage 3 (Agent Selection)**: Query registry instead of hardcoded list
- **Stage 5 (Aggregation)**: Combine results from dynamically selected agents

## Integration with Layer 3 Orchestration

Enables truly plug-and-play agent ecosystem:
- New agents can be added without modifying orchestration code
- System adapts to available capabilities at runtime
- Graceful degradation if agents become unavailable

## Future: Distributed Agent Mesh

Extend to support agents running on different machines:
- Service discovery (Consul, Kubernetes, etc.)
- Load balancing across agent instances
- Capability negotiation across network


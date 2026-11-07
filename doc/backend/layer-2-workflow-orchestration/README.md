---
title: Layer 2 Workflow Orchestration
project: kicli-code-assist
scope: backend-layer-2
purpose: Documentation hub for multi-file analysis, project context, and orchestration patterns
created: 2026-11-07T02:00:00+01:00
updated: 2026-11-07T16:20:00+01:00
update_reason: Updated after hybrid doc split; consolidated backend-only documentation
status: stable

semantic_blocks:
  - id: folder-index
    type: reference
    status: stable

relations:
  - target: ../../../frontend-tui/
    type: reference
    reason: "Companion frontend documentation"
---

# Layer 2: Workflow Orchestration

Multi-file project analysis, dependency tracking, and orchestration patterns.

## Documentation Index [folder-index]

| Document | Purpose | Status |
|----------|---------|--------|
| `PHASE_I2_PROJECTANALYZER_COMPLETE.md` | Core modules (ProjectGraph, StructureScanner, ImportAnalyzer, CodemetricsCollector) | ✅ COMPLETE |
| `PHASE_I2_MULTIFILE_ANALYSIS.md` | Architecture & design overview for multi-file analysis | ✅ COMPLETE |
| `PHASE_I2_1_ENDPOINT_INTEGRATION.md` | `/api/projects/analyze` REST endpoint specification | ✅ COMPLETE |
| `PHASE_I2_2_TUI_INTEGRATION_COMPLETE.md` | Reference to frontend-tui documentation | ➡️ MOVED |
| `AGENT_ROUTE_SPEC.md` | Agent routing with project context | TBD |
| `SESSION_MANAGEMENT_STATE.md` | Multi-agent state coordination | TBD |
| `CHUNK_FORMAT_STANDARDIZATION.md` | Payload standardization across endpoints | TBD |

## Key Architectural Concepts

### ProjectAnalyzer Module
- **StructureScanner**: Recursive file discovery
- **ImportAnalyzer**: Dependency graph construction
- **CodemetricsCollector**: Complexity metrics
- **ProjectGraph**: Impact zone calculation
- **ProjectAnalysisService**: Orchestration

### REST Endpoints
- `POST /api/projects/analyze` - Full project analysis with dependency graph

### Integration Points
- Backend: Layer 1 (Agent routing)
- Frontend: `doc/frontend-tui/` (TUI widget consumption)

## Related Documentation

**Frontend (TUI)**:
- `doc/frontend-tui/I2_ENDPOINT_CONSUMPTION_TUI.md` - HTTP client integration
- `doc/frontend-tui/TUI_TEXTUAL_ARCHITECTURE.md` - Framework overview

**Previous Layer**:
- `doc/backend/layer-1-agent-routing/` - Single-file analysis

---

**Total backend docs**: 3 active + 3 TBD  
**Last updated**: 2026-11-07

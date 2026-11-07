---
title: Frontend TUI Documentation
project: kicli-code-assist
scope: frontend-tui
purpose: Terminal UI implementation, widget architecture, and endpoint consumption
created: 2026-11-07T02:00:00+01:00
updated: 2026-11-07T17:30:00+01:00
update_reason: Applied semantic skills - added block tagging, cross-references, README table generation
status: stable

semantic_blocks:
  - id: folder-index
    title: Documentation Index
  - id: integration-flow
    title: Integration Flow
  - id: key-components
    title: Key Components

relations:
  - target: ../backend/layer-2-workflow-orchestration/PHASE_I2_1_ENDPOINT_INTEGRATION.md
    type: reference
    reason: "Backend REST API specification for ProjectAnalysis endpoint"
  - target: ../guides/
    type: reference
    reason: "General guides and operational procedures"
---

# Frontend TUI Documentation

Terminal user interface implementation using Textual framework.

## Documentation Index [folder-index]

### Complete Semantic Index

| File | Status | Purpose | Semantic Blocks |
|------|--------|---------|-----------------|
| [I1_ENDPOINT_CONSUMPTION_TUI.md](I1_ENDPOINT_CONSUMPTION_TUI.md) | ✅ active | Phase I1: TUI endpoint consumption (HTTP client) | integration-points, next-steps |
| [I2_ENDPOINT_CONSUMPTION_TUI.md](I2_ENDPOINT_CONSUMPTION_TUI.md) | ✅ active | Phase I2: Enhanced endpoint consumption with ProjectAnalysisPanel | http-client-interface, projectanalysispanel-widget, tui-layout-redesign |
| [PHASE_I1_LAYER_2_REASONING_DISPLAY.md](PHASE_I1_LAYER_2_REASONING_DISPLAY.md) | ✅ active | Phase I1: Layer 2 reasoning display implementation | overview, architecture, layer-2-reasoning, response-parsing-http-client, chunk-types |
| [PHASE_I1_REAL_LLM_IMPLEMENTATION.md](PHASE_I1_REAL_LLM_IMPLEMENTATION.md) | ✅ active | Phase I1: Real LLM integration with TUI backend | what-changed, architecture-tui-backend-flow, api-contract, testing, known-limitations |
| [TUI_TEXTUAL_ARCHITECTURE.md](TUI_TEXTUAL_ARCHITECTURE.md) | ✅ active | Textual framework architecture and widget patterns | widget-hierarchy, css-layout-strategy, widget-implementation-details, event-flow, async-pattern-http-to-tui |
| [UI_TABS.md](UI_TABS.md) | ✅ active | TUI tab interface, transparency, and workflow | tab-übersicht, llm-query-transparency-was-der-log-zeigt, workflow-übersicht, beispiel-ki-vorschläge-debugging, taste-keybindings |

### Legacy Documentation

| File | Status | Purpose |
|------|--------|---------|
| README.md | ✅ active | This index and integration documentation |



## Integration Flow

```
User Input (FileTree selection)
    ↓
FileTree triggers project_root change
    ↓
ProjectAnalysisPanel.set_project_root()
    ↓
HTTP client: analyze_project()
    ↓
Backend: /api/projects/analyze
    ↓
ProjectAnalysisPanel displays results
```

## Key Components

- **TUIBackendClient**: HTTP communication (endpoints I1 & I2)
- **ProjectAnalysisPanel**: Display for project-wide analysis results
- **TabbedContent**: Preview + Project tabs in main panel

---

**Total TUI docs**: 8 active  
**Last updated**: 2026-11-07

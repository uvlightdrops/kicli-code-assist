---
title: Endpoint Consumption (Phase I1)
project: kicli-code-assist
agent_project: kicli-code-assist
scope: frontend-tui
purpose: Document how TUI consumes the REST endpoint for project-wide analysis
created: 2026-11-07T14:30:00+01:00
updated: 2026-11-07T14:30:00+01:00
update_reason: Extracted from backend I2.1 doc; TUI-specific implementation
status: active
relations:
  - target: ../backend/layer-2-workflow-orchestration/PHASE_I2_1_ENDPOINT_INTEGRATION.md
    type: depends-on
    reason: "Consumes /api/projects/analyze endpoint"
  - target: README.md
    type: parent
semantic_blocks:
  - id: integration-points
    title: Integration Points
  - id: next-steps
    title: Next Steps
    reason: TUI documentation hub
---

# Project Analysis Endpoint - TUI Implementation

**Status**: 🔨 IN DEVELOPMENT - TUI consumption of `/api/projects/analyze`

## Integration Points [integration-points]

The TUI now calls `/api/projects/analyze` for project-wide analysis:

```python
# In agent_tabs.py or new ProjectPanel component:
response = http_client.analyze_project(project_root="/path/to/project")

# Display results:
# - Show dependency graph
# - Highlight critical files
# - Suggest refactoring opportunities
# - Display impact zones per file
```

## Next Steps [next-steps]

### Immediate:
- [ ] Extend TUI to call `/api/projects/analyze`
- [ ] Display project analysis in new "Project" panel
- [ ] Show high-impact files list
- [ ] Allow click-to-analyze per file

### Soon:
- [ ] Visualize dependency graph (ASCII/text)
- [ ] Show circular dependencies
- [ ] Suggest refactoring based on impact
- [ ] Implement caching for large projects

### Future:
- [ ] Git history analysis (commit frequency)
- [ ] Custom rule engine (project-specific checks)
- [ ] Best practices database
- [ ] Machine learning on common patterns

---

**Backend spec**: `../backend/layer-2-workflow-orchestration/PHASE_I2_1_ENDPOINT_INTEGRATION.md`

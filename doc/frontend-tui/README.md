---
title: Frontend Tui Documentation
project: kicli-code-assist
scope: frontend-tui
purpose: Central reference for frontend-tui documentation
created: 2026-11-07T18:07:00+01:00
updated: 2026-11-08 03
update_reason: Added MODAL_DIALOG_FLOWS.md comprehensive UI flow diagrams and workflow documentation
status: active
relations:
  - target: ../README.md
    type: parent
  - target: ../backend/layer-3-autonomous-agent/PROJECT_UNDERSTANDING_SYSTEM.md
    type: reference
    reason: Technical backend implementation
semantic_blocks:
  - documentation-index
  - navigation
---

# Frontend Tui Documentation

**Scope:** Frontend TUI Development

## Documentation Index [documentation-index]

| File | Status | Purpose |
|------|--------|---------|
| **MODAL_DIALOG_FLOWS.md** | **active** | **All modal/dialog workflows with state diagrams and data flow** |
| **PROJECT_UNDERSTANDING_USAGE.md** | **active** | **How to use Ctrl+U to analyze projects** |
| KEYBINDINGS.md | active | Complete TUI keyboard shortcuts and navigation reference |
| EDITOR_NAVIGATION.md | active | How to reach editor from FileTree, Preview, and new file workflows |
| I1_ENDPOINT_CONSUMPTION_TUI.md | active | HTTP client integration and endpoint consumption |
| I2_ENDPOINT_CONSUMPTION_TUI.md | stable | ProjectAnalysisPanel widget integration |
| I1_REAL_LLM_IMPLEMENTATION.md | in_progress | Backend LLM flow and API contract |
| TUI_TEXTUAL_ARCHITECTURE.md | in_progress | Widget hierarchy and event handling |
| UI_TABS.md | active | Tab layout and transparency display |
| TEXTUAL_HOWTO.md | reference | Textual framework best practices |

## Navigation [navigation]

- See: [MODAL_DIALOG_FLOWS.md](./MODAL_DIALOG_FLOWS.md) for all modal workflows and state diagrams
- See: [PROJECT_UNDERSTANDING_USAGE.md](./PROJECT_UNDERSTANDING_USAGE.md) for project analysis (Ctrl+U)
- See: [KEYBINDINGS.md](./KEYBINDINGS.md) for all shortcuts
- See: [EDITOR_NAVIGATION.md](./EDITOR_NAVIGATION.md) for editor access workflows
- Block IDs enable precise cross-document linking
- Parent directory: [../README.md](../README.md)

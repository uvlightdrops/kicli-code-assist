---
title: Frontend TUI Documentation
project: kicli-code-assist
agent_project: kicli-code-assist
scope: User Interface / Terminal UI Implementation
purpose: Documentation hub for TUI (Textual Terminal UI) architecture and implementation
created: 2026-11-06T10:00:11+01:00
updated: 2026-11-07T14:00:00+01:00
update_reason: Upgraded to semantic schema with semantic blocks and relations
status: stable

semantic_blocks:
  - id: tui-documentation-hub
    type: reference
    status: stable
    version: 1.0

relations:
  - target: TUI_TEXTUAL_ARCHITECTURE.md
    type: composed-of
    reason: "Core TUI architecture documentation"
  - target: PHASE_I1_REAL_LLM_IMPLEMENTATION.md
    type: composed-of
    reason: "LLM integration implementation"
  - target: PHASE_I1_LAYER_2_REASONING_DISPLAY.md
    type: composed-of
    reason: "Reasoning visualization layer"
  - target: ../backend/layer-2-workflow-orchestration/AGENT_ROUTE_SPEC.md
    type: depends-on
    reason: "Calls backend agent routing APIs"
  - target: ../features/README.md
    type: depends-on
    reason: "Implements user-facing features"
  - target: ../specifications/01_ARCHITECTURE.md
    type: references
    reason: "Follows TUI 2.0 system architecture"
---

# Frontend TUI Documentation [tui-documentation-hub]

Documentation specific to the TUI (Textual Terminal UI) implementation.

## Purpose

**TUI frontend for kicli-code-assist:** Terminal-based user interface built with Textual framework, enabling code analysis and AI assistance in terminal environments.

## Documentation Index

| Document | Blocks | Purpose | S |
|----------|--------|---------|---|
| **TUI_TEXTUAL_ARCHITECTURE.md** | – | Widget design, event handling, layout patterns | ✅ |
| **PHASE_I1_REAL_LLM_IMPLEMENTATION.md** | – | LLM integration and real agent execution | ✅ |
| **PHASE_I1_LAYER_2_REASONING_DISPLAY.md** | – | Reasoning trace visualization in TUI | ✅ |

## Related Documentation

- **Backend:** `doc/backend/AGENT_ROUTE_SPEC.md` — Agent routing API contract
- **Features:** `doc/features/` — User-facing features (AI workflow, file browser, chat, etc.)
- **Architecture:** `doc/specifications/01_ARCHITECTURE.md` — System-wide architecture
- **Code:** `kicli_code_assist/ui/` — TUI implementation

---

**Phase:** I1-TUI-Integration  
**Status:** Active Development
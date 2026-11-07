---
title: Backend API & Architecture Documentation
project: kicli-code-assist
agent_project: kicli-code-assist
scope: Backend Architecture / Meta-Documentation
purpose: Central hub for backend system architecture, APIs, and integration guides
created: 2026-11-06T09:20:00+01:00
updated: 2026-11-07T12:45:00+01:00
update_reason: Upgraded to semantic schema with layer documentation
status: stable

semantic_blocks:
  - id: layer-model
    type: architecture
    status: stable
    version: 1.0
  - id: layer-docs
    type: reference
    status: stable
    version: 1.0

relations:
  - target: layer-1-raw-llm/README.md
    type: composed-of
    reason: "Layer 1 is foundation of architecture"
  - target: layer-2-workflow-orchestration/README.md
    type: composed-of
    reason: "Layer 2 builds on Layer 1"
  - target: layer-3-autonomous-agent/README.md
    type: composed-of
    reason: "Layer 3 orchestrates Layers 1-2"
---

# Backend API & Architecture Documentation

Hub for backend system architecture, API specifications, and integration guides.

Organized by **3-layer intelligence model** for progressive complexity.

## 🎯 Quick Navigation

**TUI Integration (Phase I1)?**
→ [layer-2-workflow-orchestration/AGENT_ROUTE_SPEC.md](layer-2-workflow-orchestration/AGENT_ROUTE_SPEC.md)

**Understanding Full Architecture?**
→ Start with [layer-1-raw-llm/](layer-1-raw-llm/) → [layer-2-workflow-orchestration/](layer-2-workflow-orchestration/) → [layer-3-autonomous-agent/](layer-3-autonomous-agent/)

## 📊 3-Layer Model [layer-model]

```
Layer 3: Autonomous Agent Layer
├── Multi-agent reasoning & self-correction
├── Transparency & observability (traces, WebSocket streaming)
└── Decision-making based on outcomes
         ↓ uses ↓
Layer 2: Workflow Orchestration Layer
├── 6-stage pipeline (intent → routing → execution → aggregation → generation)
├── Session management & state
└── Structured error handling
         ↓ uses ↓
Layer 1: Raw LLM Layer
├── OpenAI API (sync/async)
├── Secret filtering & security
└── File I/O & OS commands
```

## 📚 Layer Documentation [layer-docs]

| Layer | Folder | Entry Point | Purpose |
|-------|--------|------------|---------|
| **Layer 1** | `layer-1-raw-llm/` | [README.md](layer-1-raw-llm/README.md) | LLM primitives, file I/O, OS commands |
| **Layer 2** | `layer-2-workflow-orchestration/` | [README.md](layer-2-workflow-orchestration/README.md) | Orchestration pipeline, REST API, TUI integration |
| **Layer 3** | `layer-3-autonomous-agent/` | [README.md](layer-3-autonomous-agent/README.md) | Multi-agent reasoning, transparency, streaming |

## 🔄 Cross-Project Usage

This backend is shared by:
- **kicli-code-assist** — TUI + WebUI
- **ki-knowledge** — Coding Agent (uses Layers 1-2)
- Future projects

**For new clients:** Read Layer 2 AGENT_ROUTE_SPEC.md, follow examples, reuse error handling patterns.

## 📝 Contributing

When updating backend:
1. Update YAML headers (updated date, update_reason)
2. Breaking API changes? Update AGENT_ROUTE_SPEC.md
3. Link to cross-layer dependencies in cross_references
4. Keep docs in sync with code

---

**Phase:** I1-TUI-Integration | **Status:** Restructured 2026-11-06

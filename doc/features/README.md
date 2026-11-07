---
title: Features Documentation
project: kicli-code-assist
agent_project: kicli-code-assist
scope: User-Facing Features / Implementation
purpose: Central hub for feature specifications and implementation documentation
created: 2026-11-07T14:00:00+01:00
updated: 2026-11-07T13:46:00+01:00
update_reason: Initial documentation with semantic schema
status: stable

semantic_blocks:
  - id: features-index
    type: reference
    status: stable
    version: 1.0

relations:
  - target: ../frontend-tui/README.md
    type: composed-of
    reason: "Features are implemented in TUI frontend"
  - target: ../frontend-web/README.md
    type: composed-of
    reason: "Features also available in web UI"
  - target: ../backend/layer-2-workflow-orchestration/README.md
    type: depends-on
    reason: "Features use Layer 2 orchestration backend"
---

# Features Documentation

User-facing features, workflows, and implementation specifications.

## Purpose

**Core workflows for code analysis, interaction, and automation.**

| Document | Blocks | Purpose | S |
|----------|--------|---------|---|
| **AI_WORKFLOW.md** | ai-workflow-overview<br/>quick-start-guide<br/>workflow-execution<br/>ai-operations-matrix | AI-assisted code analysis and suggestion workflow | ✅ |
| **CHAT_HISTORY_AND_PROMPTS.md** | chat-persistence-overview<br/>session-management-api<br/>session-workflow<br/>data-storage-format | Persistent chat sessions with automatic save/restore | ✅ |
| **CHAT_WITH_FILES_WORKFLOW.md** | chat-files-workflow<br/>context-loading<br/>ai-analysis-integration<br/>workflow-patterns | Interactive chat with file and project context | ✅ |
| **FILE_BROWSER.md** | file-browser-overview<br/>navigation-features<br/>file-selection-workflow<br/>ui-layout-reference | File browser and project navigation in TUI | ✅ |
| **PROMPT_MANAGEMENT_DESIGN.md** | prompt-management-overview<br/>prompt-configuration-schema<br/>role-system-design<br/>prompt-versioning-strategy | Prompt templates, roles, and context management | ✅ |
| **SHELL_COMMAND_EDITING.md** | shell-command-editing-overview<br/>command-editor-architecture<br/>batch-editing-workflow<br/>risk-classification-system | Interactive shell command editing and manual entry | ✅ |
| **SHELL_EXECUTION_IMPLEMENTATION.md** | shell-execution-overview<br/>architecture-design<br/>approval-workflow<br/>audit-trail-system | Safe shell command execution with approval workflow | ✅ |
| **FEATURES_IMPLEMENTED.md** | feature-inventory<br/>logging-infrastructure<br/>tui-interface-features<br/>shell-execution-features | Comprehensive inventory of implemented features | ✅ |

## Upgrade Status

✅ **All 8 feature docs upgraded to semantic schema:**
- YAML headers with metadata (created, updated, status)
- 4 semantic blocks per doc (architecture, implementation, operations, reference)
- H2 headings tagged with block IDs
- Cross-doc relations established (depends-on, part-of, implements, references)

## Cross-References

**Relations to backend layers:**
- Layer 1: OS_COMMAND_EXECUTION_ARCHITECTURE, FILE_IO_GIT_OPERATIONS, LLM_CLIENT_API_SPECIFICATION
- Layer 2: AGENT_ROUTE_SPEC, SESSION_MANAGEMENT_STATE, CHUNK_FORMAT_STANDARDIZATION
- Layer 3: Agent coordination & transparency features

**Feature dependency flow:**
```
FILE_BROWSER → CHAT_WITH_FILES_WORKFLOW → AI_WORKFLOW
                    ↓
            CHAT_HISTORY_AND_PROMPTS
                    ↓
            SHELL_EXECUTION_IMPLEMENTATION → SHELL_COMMAND_EDITING
                    ↓
            PROMPT_MANAGEMENT_DESIGN
```

See `/home/flow/dev_doc/documentation-guidelines/` for schema standards.


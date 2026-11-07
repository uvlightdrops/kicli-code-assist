---
title: Features Documentation
project: kicli-code-assist
scope: features
purpose: Feature documentation
created: 2026-11-07T18:07:00+01:00
updated: 2026-11-07T20:58:20
status: stable
semantic_blocks:
  - id: documentation-index
    type: implementation
    status: stable
    version: 1.0
  - id: navigation
    type: implementation
    status: stable
    version: 1.0
  - id: subfolders
    type: implementation
    status: stable
    version: 1.0
---

# Features Documentation

**Scope:** Feature Development & Planning

## Documentation Index [documentation-index]

| File | Status | Purpose | Semantic Blocks |
|------|--------|---------|-----------------|
| AI_WORKFLOW.md | stable | AI-assisted code analysis and suggestion workflow for editor | quick-start-guide, workflow-execution, ai-operations-matrix |
| CHAT_HISTORY_AND_PROMPTS.md | stable | Persistent chat sessions with automatic save/restore | chat-persistence-overview, session-management-api, session-workflow, data-sto... |
| CHAT_WITH_FILES_WORKFLOW.md | stable | Interactive chat with file and project context | workflow-patterns, context-loading, ai-analysis-integration |
| FEATURES_IMPLEMENTED.md | stable | Comprehensive inventory of implemented features with status and completion detai | feature-inventory, logging-infrastructure |
| FILE_BROWSER.md | stable | File browser and project navigation in TUI | file-browser-overview, navigation-features, file-selection-workflow, ui-layou... |
| PROMPT_MANAGEMENT_DESIGN.md | draft | Prompt templates, roles, and context management | prompt-management-overview, prompt-configuration-schema, prompt-versioning-st... |
| SHELL_COMMAND_EDITING.md | stable | Interactive shell command editing and manual entry | shell-command-editing-overview, command-editor-architecture, risk-classificat... |
| SHELL_EXECUTION_IMPLEMENTATION.md | stable | Safe shell command execution with approval workflow and audit trail | shell-execution-overview, approval-workflow, architecture-design, audit-trail... |

## Navigation [navigation]

- Browse by status: active, draft, archived
- Block IDs enable precise cross-document linking
- See parent directory: [../README.md](../README.md)

## Subfolders [subfolders]

- **archive/**
- **tui/**
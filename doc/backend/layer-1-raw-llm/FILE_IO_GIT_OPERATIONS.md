---
title: File I/O & Git Operations
project: kicli-code-assist
agent_project: kicli-code-assist
scope: Backend Architecture / Layer 1 / File System & VCS
purpose: Layer 1 primitives for file operations, directory traversal, and git integration
created: 2026-11-07T13:32:00+01:00
updated: "2026-11-10 20"
update_reason: "Update shared-documentation paths after relocation"
status: draft

semantic_blocks:
  - id: file-io-api
    type: architecture
    status: draft
    version: 0.1
  - id: directory-traversal
    type: architecture
    status: draft
    version: 0.1
  - id: git-operations
    type: architecture
    status: draft
    version: 0.1
  - id: safety-constraints
    type: architecture
    status: draft
    version: 0.1

relations:
  - target: IDE_CAPABILITIES.md
    type: part-of
    reason: "File & git ops are core Layer 1 capabilities"
  - target: ../layer-2-workflow-orchestration/PHASE_I2_PROJECTANALYZER_COMPLETE
    type: depends-on
    reason: "Project analysis uses file I/O to scan repos"
  - target: ../../../../../dev_doc/doc/security_guidelines.md
    type: references
    reason: "Security constraints for file system access"
---

# File I/O & Git Operations

Layer 1 primitives for filesystem and version control integration.

## File I/O API [file-io-api]

**Status:** TBD

Async file operations:
- Read files (with encoding detection)
- Write files (with atomic guarantees)
- Create/delete directories
- Check file existence, size, permissions
- Stat file metadata

```python
# TBD: Read API (async)
# TBD: Write API (atomic writes)
# TBD: Binary vs. text mode handling
# TBD: Encoding detection
# TBD: Large file streaming
```

## Directory Traversal [directory-traversal]

**Status:** TBD

Efficient directory scanning:
- Recursive file listing
- Pattern matching (glob, regex)
- Size/time filters
- Symlink handling
- .gitignore respect

```python
# TBD: Traversal API
# TBD: Filter chaining
# TBD: Performance optimizations (async generators)
```

## Git Operations [git-operations]

**Status:** TBD

Version control primitives:
- Read git status (staged, unstaged, untracked)
- Get current branch
- Show diff (file-level, hunk-level)
- Read commit history (log)
- Show commit details
- Read .gitignore patterns

```python
# TBD: Git CLI wrapper or libgit2?
# TBD: API design (async)
# TBD: Performance caching (git status)
# TBD: Error handling (not a git repo)
```

## Safety Constraints [safety-constraints]

**Status:** TBD

Filesystem sandboxing:
- Working directory restrictions (prevent `../../` escape)
- File size limits (prevent loading huge files)
- Symlink resolution limits (prevent loops)
- Permission checks (read-only vs. write)
- Rate limiting (prevent DoS via many small ops)

```python
# TBD: Validation rules
# TBD: Audit logging
```

## Use Cases

- Load source code for analysis
- Create/edit files during refactoring
- Check git status before committing
- Show diffs to user for review
- Scan project structure (for ProjectAnalyzer Phase I2)


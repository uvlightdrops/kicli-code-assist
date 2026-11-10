---
title: Chunk Format Standardization
project: kicli-code-assist
agent_project: kicli-code-assist
scope: Backend Architecture / Layer 2 / Response Format
purpose: Specification of chunk structure for agent responses, standardized observation/issue/solution taxonomy
created: 2026-11-07T13:32:00+01:00
updated: "2026-11-10 20"
update_reason: "Update shared-documentation paths after relocation"
status: draft

semantic_blocks:
  - id: chunk-taxonomy
    type: architecture
    status: draft
    version: 0.1
  - id: chunk-schema
    type: implementation
    status: draft
    version: 0.1
  - id: chunk-metadata
    type: implementation
    status: draft
    version: 0.1
  - id: validation-rules
    type: operations
    status: draft
    version: 0.1

relations:
  - target: AGENT_ROUTE_SPEC.md
    type: part-of
    reason: "Chunks are part of AGENT_ROUTE response format"
  - target: ../frontend-web/DIFF_USER_GUIDE.md
    type: depends-on
    reason: "Frontend renders chunks with type-specific UI"
  - target: ../../../../../dev_doc/doc/documentation-guidelines/AGENTIC_DOCUMENTATION_PATTERNS.md
    type: references
    reason: "Similar concerns to structured block documentation"
---

# Chunk Format Standardization

Specification of standardized response chunks from Layer 2 agents.

## Chunk Taxonomy [chunk-taxonomy]

**Status:** Partial (documented in AGENT_ROUTE_SPEC, needs formal schema)

Current chunk types used in TUI:
- 🔍 **observation**: Findings from analysis (e.g., "Found 5 high-complexity functions")
- ⚠️ **issue**: Problem identified (e.g., "Circular dependency between A and B")
- 💡 **solution**: Proposed fix or action (e.g., "Extract function into separate module")
- ✅ **impact**: Expected outcome (e.g., "Reduces cyclomatic complexity by 40%")
- ℹ️ **info**: Contextual information (e.g., "This pattern is used in 3 other files")

```python
# TBD: Formalize as Pydantic enum
# TBD: Add new types if needed (e.g., "recommendation", "decision", "tradeoff")
# TBD: Document when to use each type
```

## Chunk Schema [chunk-schema]

**Status:** TBD

```python
class Chunk(BaseModel):
    """Standardized response chunk from agent."""
    type: ChunkType  # observation | issue | solution | impact | info
    content: str  # Main text (markdown or plain text?)
    # TBD: Additional fields?
    code_snippet: Optional[str] = None  # Code excerpt if relevant
    file_path: Optional[str] = None  # File being discussed
    line_range: Optional[Tuple[int, int]] = None  # Start/end line numbers
    metadata: Dict[str, Any] = {}  # Extensible metadata
```

## Chunk Metadata [chunk-metadata]

**Status:** TBD

Metadata to include with chunks:
- **source**: Which agent generated this? (ProjectAnalyzer, LLM, etc.)
- **confidence**: How certain is this? (high/medium/low)
- **linked_chunks**: IDs of related chunks (for grouping in UI)
- **priority**: Important? (high/normal/low)
- **tags**: Categorical tags for filtering (#bug, #refactor, #performance)

```python
# TBD: Metadata schema
# TBD: UI treatment (display, filter, sort)
```

## Validation Rules [validation-rules]

**Status:** TBD

Requirements for chunks:
- Content must be non-empty
- Content length limits (e.g., 5000 chars max for TUI display)
- File paths must be absolute or project-relative (consistent format)
- Line numbers must be positive integers
- Code snippets must be valid code (or empty)

```python
# TBD: Validator implementation
# TBD: Error handling (invalid chunks logged, replaced with generic error)
```

## Integration with Frontend

- **TUI** (textual): Colored display with icons (🔍 ⚠️ 💡 ✅ ℹ️)
- **Web** (React): Tab-based organization, collapsible sections
- Both must handle unknown chunk types gracefully

## See Also

- AGENT_ROUTE_SPEC.md (current response format)
- Frontend specs: DIFF_USER_GUIDE.md, UI_TABS.md


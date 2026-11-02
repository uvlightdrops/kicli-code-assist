---
project: kicli-code-assist
scope: architecture
created: 2026-11-02 13
updated: 2026-11-02 13
update_reason: Created folder README with guidelines
status: current
agent_project: kicli-code-assist
cross_references:
  - /home/flow/dev_doc/DOCUMENTATION_ORGANIZATION_GUIDE.md
---

# Architecture Documentation

**Purpose:** Technical design and deep-dive architecture documentation for kicli-code-assist.

---

## What Goes Here

### ✅ DO Include

- **System Architecture** (`ARCHITECTURE.md`)
  - High-level design of major components
  - Data flow diagrams (text-based or descriptions)
  - Component relationships and dependencies

- **Component Architecture** (`*_ARCHITECTURE.md`)
  - Deep technical design of specific systems
  - Example: `PHASE_5_5_2_TRANSPARENCY_ARCHITECTURE.md` (how transparency modules work internally)
  - Detailed enough for a developer to understand implementation

- **API Design** (`API_*.md`)
  - REST/WebSocket endpoint specifications
  - Request/response schemas
  - Authentication & error handling

- **Data Models** (`DATA_MODEL.md`, `SCHEMA_*.md`)
  - Database schemas (if applicable)
  - Configuration schemas
  - Data structure specifications

- **Design Decisions** (`DESIGN_DECISIONS.md`, `ADR_*.md`)
  - Why we chose technology X over Y
  - Trade-off analysis
  - Architectural patterns used

- **Phase Architecture** (`*_ARCHITECTURE.md`)
  - Technical architecture for completed phases
  - NOT summaries—deep technical details
  - Complementary to `/phases/PHASE_X_SUMMARY.md`
  - Example: `TRANSPARENCY_MODULES_ARCHITECTURE.md` (not `PHASE_5_5_2_TRANSPARENCY_ARCHITECTURE.md`)

### ❌ DO NOT Include

- Feature user guides → `/features/`
- Setup/installation instructions → `/guides/`
- How-to tutorials → `/guides/`
- Phase completion summaries → `/phases/`
- Test results/reports → `/testing/`
- Session progress tracking → `/tracking/`
- Archived/superseded docs → `/archive/`

---

## File Naming Convention

```
ARCHITECTURE.md                  # Main architecture overview
COMPONENT_ARCHITECTURE.md        # Architecture for specific component
FEATURE_ARCHITECTURE.md          # Architecture deep-dive for feature
ASYNC_LLM_SECURITY_...          # Topic-specific architectures (no PHASE prefix)
WEBSOCKET_STREAMING_...         # Clear topic-based names
API_DESIGN.md                    # REST/WebSocket API specifications
DATA_MODEL.md                    # Database/data structure schemas
ADR_NNN_DECISION.md              # Architecture Decision Record
DESIGN_DECISIONS.md              # Collection of design decisions
```

**Examples (CORRECT):**
- `TRANSPARENCY_MODULES_ARCHITECTURE.md` ✅
- `WEBSOCKET_STREAMING_ARCHITECTURE.md` ✅
- `MULTIFILE_REFACTORING_ARCHITECTURE.md` ✅

**NOT:**
- `PHASE_5_5_2_TRANSPARENCY_ARCHITECTURE.md` ❌ (PHASE prefix)
- `PHASE_4_ARCHITECTURE.md` ❌ (Not descriptive)

---

## YAML Header Template

```yaml
---
project: kicli-code-assist
scope: architecture
created: 2026-MM-DD HH
updated: 2026-MM-DD HH
update_reason: "Why you created or updated this doc"
status: current
agent_project: kicli-code-assist
cross_references:
  - /path/to/related/doc.md
---
```

---

## Example: TRANSPARENCY_MODULES_ARCHITECTURE.md

**What it describes:**
- How the 3 transparency modules (ReasoningTracer, LLMCallTracker, PerformanceMetrics) work
- Internal design of each module
- How they integrate with CodeImplementationAgent
- WebSocket event streaming architecture
- REST API for historical queries

**NOT:**
- A summary of "we implemented transparency" (that's in `/phases/PHASE_5_5_2_SUMMARY.md`)
- Usage guide for developers (that would be in `/guides/` or `/features/`)

**Filename logic:**
- **WHAT** (no phase): Transparency Modules
- **HOW**: Architecture (technical deep-dive)
- Result: `TRANSPARENCY_MODULES_ARCHITECTURE.md`

---

## Related Documentation

- **Phase Summaries**: `/phases/README.md` (what was built in each phase)
- **Feature Guides**: `/features/` (how to use features)
- **Setup Guides**: `/guides/` (how to set up/configure the project)
- **Standards**: `/home/flow/dev_doc/DOCUMENTATION_ORGANIZATION_GUIDE.md` (ecosystem-wide guide)


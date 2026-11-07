---
title: Agent Route API Specification
project: kicli-code-assist
agent_project: kicli-code-assist
scope: Phase 5.1+ Backend / Agent Orchestration API
purpose: Specify REST endpoint for unified agent routing and multi-capability orchestration
created: 2026-11-06T09:20:00+01:00
updated: 2026-11-07T12:31:00+01:00
update_reason: Upgraded to semantic schema, added block IDs
status: stable

semantic_blocks:
  - id: api-specification
    type: implementation
    status: stable
    version: 2.0
    
  - id: request-schema
    type: implementation
    status: stable
    version: 1.0
    
  - id: response-schema
    type: implementation
    status: stable
    version: 1.0
    
  - id: error-handling
    type: implementation
    status: stable
    version: 1.0

relations:
  - target: PHASE_I2_1_ENDPOINT_INTEGRATION
    type: references
    reason: "Similar endpoint pattern for project analysis"
    
  - target: ../../../FUTURE_ROADMAP.md
    type: part-of
    reason: "Core capability for Phase 5.1+ orchestration"
---

# Agent Route API Specification

**Endpoint:** `POST /api/agent/route`
**Backend:** kicli-code-assist Flask server (default: http://localhost:8000)
**Phase:** 5.1+ (MetaCoordinationAgent orchestration)

---

## Quick Example (TUI Integration)

```python
import httpx

# User clicks "Analyze" on kicli_code_assist/ui/middleware.py
response = httpx.post(
    "http://localhost:8000/api/agent/route",
    json={
        "query": "Explain this file's purpose and structure",
        "file_path": "kicli_code_assist/ui/middleware.py",
        "project_root": "/home/flow/dev_flow/kicli-code-assist",
        "scope": "file",  # or "folder", "project"
        "session_id": "550e8400-e29b-41d4-a716-446655440000"
    }
)

result = response.json()
# result.success == True
# result.answer = "Detailed 300+ word response about the file"
# result.tabs.Explain = {...}
# result.tabs.Metrics = {...}
```

---

## Request Schema [request-schema]

**Method:** `POST`  
**Content-Type:** `application/json`

### Required Fields

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| `query` | string | "Explain this file" | Analysis request. Can be specific (Explain, Metrics, Refactor) or open-ended. |
| `file_path` | string | "src/main.py" or "/full/path/main.py" | Relative or absolute path. Required unless external_project_query=true. |
| `project_root` | string | "/home/flow/dev_flow/kicli-code-assist" | Must be inside `/home/flow/dev_flow/` (security boundary). |

### Optional Fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `scope` | string | "project" | "file", "folder", or "project". Affects agent selection. |
| `session_id` | string | auto-generated UUID | Re-use for related queries in same analysis session. |

### Example Request

```json
{
  "query": "What are the main performance bottlenecks?",
  "file_path": "kicli_code_assist/agent/meta_coordinator.py",
  "project_root": "/home/flow/dev_flow/kicli-code-assist",
  "scope": "file",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Response Schema [response-schema]

**Status 200 (Success)**

```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "query": "What are the main performance bottlenecks?",
  
  "answer": "This module orchestrates analysis workflows using a 6-stage pipeline...",
  
  "intent": {
    "type": "explain",
    "confidence": 0.92
  },
  
  "workflow": "analysis",
  "agents_used": ["explain", "metrics", "dependencies"],
  
  "tabs": {
    "Explain": {
      "summary": "Short (1-2 sentence) summary",
      "content": "Full detailed analysis",
      "chunks": [
        {"type": "observation", "content": "..."},
        {"type": "issue", "content": "..."},
        ...
      ]
    },
    "Metrics": {
      "summary": "Maintainability 7.2/10, Complexity high",
      "content": "Detailed metrics breakdown",
      "chunks": [
        {"type": "observation", "content": "..."},
        ...
      ]
    },
    "Dependencies": { ... },
    "Refactor": { ... }
  },
  
  "actions": [
    {"type": "refactor", "description": "Extract merge logic into separate class", "file": "config.py"}
  ],
  
  "timing": {
    "intent_ms": 123,
    "execution_ms": 456,
    "aggregation_ms": 789,
    "answer_ms": 234,
    "total_ms": 1602
  }
}
```

### Key Fields

| Field | Type | Purpose |
|-------|------|---------|
| `success` | bool | ✅ Always true on 200 |
| `session_id` | string | Matches request; track conversation |
| `answer` | string | Main conversational response (what user reads first) |
| `intent` | object | LLM detected query type + confidence (0.0-1.0) |
| `workflow` | string | "analysis" or "implementation" or custom |
| `agents_used` | array | Which agents ran (["explain", "metrics", ...]) |
| `tabs` | object | Per-agent detailed results (see below) |
| `actions` | array | Suggested code changes (refactor, etc) |
| `timing` | object | Performance metrics (ms) |

### Tab Structure (each tab like `tabs.Explain`)

```json
{
  "summary": "1-2 sentence headline",
  "content": "Full analysis (300+ words, scrollable)",
  "chunks": [
    {"type": "observation", "content": "Observed X in the code"},
    {"type": "issue", "content": "This causes performance problem"},
    {"type": "solution", "content": "Extract method M to fix"},
    {"type": "impact", "content": "Would improve metric Y by Z%"},
    {"type": "info", "content": "Additional context"}
  ]
}
```

---

## Chunk Types

Used in `tabs.*.chunks` array. Each chunk has `type` and `content`.

| Type | Icon | Use Case |
|------|------|----------|
| `observation` | 🔍 | "Found X in the code" |
| `issue` | ⚠️ | "This is problematic because..." |
| `solution` | 💡 | "Fix by doing..." |
| `impact` | ✅ | "Impact: metric improves by..." |
| `info` | ℹ️ | "Context: this pattern is..." |

**TUI rendering example:**
```
🔍 The file starts with import statements for logging, pathlib...
⚠️ The merge method contains nested if-elif blocks with cyclomatic complexity 8
💡 Extract merge logic into separate ConfigMerger class to reduce complexity
✅ Would improve maintainability index from 7.2 to 8.6
ℹ️ File follows PEP 8 style guidelines consistently
```

---

## Error Responses [error-handling]

**Status 400 (Bad Request)**

```json
{
  "success": false,
  "error": "Missing 'query' parameter",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

Common errors:
- `Missing 'query' parameter`
- `Missing 'file_path' parameter`
- `Access denied: path outside allowed root`
- `Access denied: file outside project`

**Status 500 (Server Error)**

```json
{
  "success": false,
  "error": "LLM API timeout after 30s",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

LLM errors (usually transient):
- `LLM API timeout`
- `Invalid API key`
- `Rate limited`

**TUI Handling Pattern:**

```python
if response.status_code == 200:
    result = response.json()
    if result["success"]:
        display_response(result)
    else:
        show_error(result["error"], recoverable=True)
elif response.status_code == 400:
    show_error("Invalid request", recoverable=False)
elif response.status_code == 403:
    show_error("Access denied", recoverable=False)
elif response.status_code == 500:
    show_error(response.json()["error"], recoverable=True)
else:
    show_error(f"HTTP {response.status_code}", recoverable=False)
```

---

## Query Patterns

The LLM detects intent from the query. Examples:

### Explain (Structure, Purpose, Flow)
```
"Explain this module"
"What does this class do?"
"Walk me through the initialization"
```
→ `intent.type = "explain"`

### Metrics (Complexity, Maintainability, Size)
```
"Show metrics"
"How complex is this?"
"Maintainability score?"
```
→ `intent.type = "metrics"`

### Dependencies (Imports, Circular, External)
```
"Show me dependencies"
"What does this import?"
"Are there circular deps?"
```
→ `intent.type = "dependencies"`

### Refactor (Improvements, Patterns, Issues)
```
"How would you refactor this?"
"What could be improved?"
"Code smells?"
```
→ `intent.type = "refactor"`

### Mixed (Open-ended, multiple agents)
```
"Analyze this file"
"Full code review"
"Tell me everything"
```
→ `agents_used = ["explain", "metrics", "dependencies", "refactor"]`

---

## Integration Checklist (for new clients)

- [ ] Backend running on http://localhost:8000 (or configure URL)
- [ ] Construct `POST /api/agent/route` request with required fields
- [ ] Parse response.json() to extract `answer` and `tabs[active_tab].chunks`
- [ ] Display `answer` in main panel (scrollable)
- [ ] Display `chunks` in sidebar/panel (list with emoji icons)
- [ ] Handle errors: 400 (show validation error), 500 (show transient error with retry)
- [ ] Re-use `session_id` for related queries in same analysis session
- [ ] Log `timing.total_ms` for performance monitoring

---

## Performance Notes

- **First request:** 2-5s (LLM inference + agent coordination)
- **Subsequent requests in session:** 1-3s (caching + hot LLM)
- **Timeout:** 30s (LLM API) + 2s (orchestration) = ~32s total
- **TUI recommendation:** Show spinner/loader while waiting, don't block UI

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-11-06 | Initial spec extracted from server_routes.py (Phase 5.1) |

---

**Last updated:** 2026-11-06 | **Status:** active | **Maintained by:** Backend Team

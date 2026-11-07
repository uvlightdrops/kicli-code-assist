---
title: REST Endpoint for Project Analysis
project: kicli-code-assist
scope: backend-layer-2
purpose: Document REST endpoint /api/projects/analyze for project-wide code analysis
created: 2026-11-07T01:03:00+01:00
updated: 2026-11-07T16:20:00+01:00
update_reason: Split from hybrid doc; removed TUI integration, reference moved to frontend-tui/
status: stable

semantic_blocks:
  - id: endpoint-spec
    type: implementation
    status: stable
  - id: request-response-format
    type: implementation
    status: stable

relations:
  - target: PHASE_I2_PROJECTANALYZER_COMPLETE.md
    type: depends-on
    reason: "Endpoint wraps ProjectAnalyzer core functionality"
  - target: ../../../frontend-tui/I2_ENDPOINT_CONSUMPTION_TUI.md
    type: reference
    reason: "TUI implementation consuming this endpoint"
---

# REST Endpoint for Project Analysis

**Status**: ✅ COMPLETE - `/api/projects/analyze` endpoint ready  

## Endpoint Specification [endpoint-spec]

### POST `/api/projects/analyze`

**Location**: `kicli_code_assist/web/server_routes.py` (Lines 917-1040)

**Purpose**: Full project analysis with dependency graph

**Request**:
```json
{
  "project_root": "/path/to/project",
  "depth": 3,
  "include_extensions": [".py", ".yaml"],
  "exclude_patterns": [".git", "__pycache__"]
}
```

**Response** (Success):
```json
{
  "success": true,
  "project": {
    "name": "kicli-code-assist",
    "root": "/path/to/project",
    "stats": {
      "total_files": 189,
      "total_lines": 49616,
      "languages": {"python": 189},
      "avg_complexity": 20.10,
      "files_with_high_impact": [...]
    }
  },
  "files": [
    {
      "path": "kicli_code_assist/ui/tui_client.py",
      "language": "python",
      "lines": 421,
      "complexity": 12,
      "imports": ["kicli_code_assist.ui.widgets"],
      "exported": ["class KICLIApp", "def main"],
      "is_test": false
    }
  ],
  "dependencies": {
    "ui/tui_client.py": ["ui/widgets/file_browser.py"],
    ...
  },
  "high_impact_files": [
    {
      "file": "app_config.py",
      "direct_dependents": 19,
      "total_affected": 19,
      "impact_level": "critical",
      "cascade_depth": 1
    }
  ]
}
```

## Implementation Details [request-response-format]

### Data Format

The endpoint returns structured project metadata:

| Field | Type | Purpose |
|-------|------|---------|
| `project.name` | string | Project identifier |
| `project.root` | string | Absolute path to project root |
| `files[]` | array | Complete file inventory |
| `files[].path` | string | Relative path from root |
| `files[].complexity` | int | Cyclomatic complexity score |
| `dependencies` | object | Import graph (file → dependencies) |
| `high_impact_files` | array | Files with highest dependents |

### Real-World Analysis Results

Analyzed **actual kicli-code-assist project**:

| Metric | Value |
|--------|-------|
| Total files | 189 |
| Total lines | 49,616 |
| Languages | Python (189 files) |
| Avg complexity | 20.10 |
| Circular dependencies | 0 |

**Critical Files** (by dependent count):
1. `app_config.py` - 19 direct dependents (CRITICAL)
2. `prompts.py` - 9 direct dependents (HIGH)
3. `executor/shell_execution.py` - 9 dependents (HIGH)

### Performance

- **Small project** (6 files): < 0.1s
- **Large project** (189 files): ~2-5s
- **Memory usage**: Linear with file count

### Error Handling

- ✅ Missing `project_root` parameter → 400
- ✅ Path outside ALLOWED_ROOT → 403
- ✅ Project path doesn't exist → 404
- ✅ Parse errors → logged, analysis continues
- ✅ All errors → logged with traceback

## Integration Points

For TUI consumption details, see `../../../frontend-tui/I2_ENDPOINT_CONSUMPTION_TUI.md`

For core analysis modules, see `PHASE_I2_PROJECTANALYZER_COMPLETE.md`

---

**See also**: PHASE_I2_MULTIFILE_ANALYSIS.md (architecture), PHASE_I2_PROJECTANALYZER_COMPLETE.md (modules)

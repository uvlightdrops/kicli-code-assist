# Backend Route Analysis: Project Analysis Panel Removal

**Date:** 2026-11-19  
**Analysis Type:** Endpoint orphaning assessment  
**Status:** Provisional (UI removed, backend routes still active for reference)

## Summary

With the removal of ProjectAnalysisPanel from the TUI middle pane, we need to audit which backend endpoints are now orphaned or underutilized. This document tracks which endpoints are potentially candidates for consolidation or deprecation in future phases.

## Endpoints Examined

### 1. POST /api/projects/analyze
**Location:** `kicli_code_assist/web/server_routes.py:1063`  
**Current Usage in TUI:** ⚠️ **ORPHANED** (was only called by ProjectAnalysisPanel)  
**Backend Client Method:** `BackendClient.analyze_project()`  
**Other UI References:** None found  

**Purpose:**
- Analyzes project structure, imports, and metrics
- Builds complete dependency graph and impact zones
- Returns high-impact files and circular dependencies

**Request Signature:**
```json
{
  "project_root": "/path/to/project",
  "depth": 3,
  "include_extensions": [".py", ".yaml"],
  "exclude_patterns": [".git", "__pycache__"]
}
```

**Response Signature:**
```json
{
  "success": true,
  "project": {
    "name": "...",
    "root": "...",
    "stats": {
      "total_files": 127,
      "total_lines": 45230,
      "languages": {"python": 89},
      "avg_complexity": 2.5
    }
  },
  "files": [...],
  "dependencies": {...},
  "high_impact_files": [...],
  "timestamp": "ISO-8601"
}
```

**Analysis:**
- ✅ Well-structured endpoint with comprehensive output
- ✅ Performs genuine analysis work (dependency graph, complexity)
- ⚠️ **UNUSED** in current TUI after ProjectAnalysisPanel removal
- **Recommendation:** Keep for now, could be useful for:
  - Future CLI tools
  - Backend-only analysis workflows
  - Programmatic access to project metrics
  - Right-pane "Metrics" tab expansion (if planned)

---

### 2. POST /api/projects/understand
**Location:** `kicli_code_assist/web/server_routes.py:1206`  
**Current Usage in TUI:** ⏸️ **REFERENCED but NOT TESTED**  
**Backend Client Method:** `BackendClient.understand_project()`  
**Other UI References:** Defined in http_client but no active caller found  

**Purpose:**
- Comprehensive project understanding analysis
- Generates project summary and documentation

**Request Signature:**
```json
{
  "project_root": "/path/to/project"
}
```

**Analysis:**
- ⚠️ **LIKELY UNUSED** - defined in http_client but no caller found in UI
- May have been intended for future features

**Recommendation:** Keep but mark as deprecated pending confirmation of non-usage

---

### 3. GET /api/projects/current
**Location:** `kicli_code_assist/web/server_routes.py:1009`  
**Current Usage in TUI:** ✅ **ACTIVE**  
**Purpose:** Get metadata of currently open project  

**Recommendation:** Keep (in use)

---

### 4. POST /api/projects/open
**Location:** `kicli_code_assist/web/server_routes.py:1019`  
**Current Usage in TUI:** ✅ **ACTIVE**  
**Purpose:** Open a project  

**Recommendation:** Keep (in use)

---

### 5. GET /api/projects/browse
**Location:** `kicli_code_assist/web/server_routes.py:1380`  
**Current Usage in TUI:** ⏸️ **Status unclear**  
**Purpose:** Browse available projects  

**Recommendation:** Audit usage

---

### 6. POST /api/projects/create
**Location:** `kicli_code_assist/web/server_routes.py:1304`  
**Current Usage in TUI:** ⏸️ **Status unclear**  
**Purpose:** Create new project  

**Recommendation:** Audit usage

---

## Removal Impact Analysis

### ProjectAnalysisPanel
- **File:** `kicli_code_assist/ui/widgets/project_analysis_panel.py`
- **Removed From:** TUI center pane (middle tab)
- **Endpoints Lost:**
  - `/api/projects/analyze` (direct dependency)
- **State:** File still exists (not deleted) for reference/archival
- **Future Use:** Could be archived or refactored into right-pane metrics tab

## Consolidation Opportunities

### Potential for Future Phases

1. **Right-Pane "Metrics" Tab Enhancement**
   - Current state: Likely focused on agent responses
   - Enhancement: Could consume `/api/projects/analyze` output
   - Benefit: Unified project insights without separate tab layer

2. **CLI Tool Integration**
   - `/api/projects/analyze` could serve backend-only CLI tools
   - Provides structured project metrics for automation

3. **Endpoint Consolidation**
   - `/api/projects/understand` could be merged with `/api/projects/analyze`
   - Reduce redundancy if both serve similar purposes

## Orphaned Code Summary

| Endpoint | File | Status | Recommendation |
|----------|------|--------|-----------------|
| POST /api/projects/analyze | server_routes.py:1063 | Orphaned | Archive for phase 2 |
| POST /api/projects/understand | server_routes.py:1206 | Unused | Verify then deprecate |
| ProjectAnalysisPanel | widgets/project_analysis_panel.py | Removed from UI | Archive for reference |

## Next Steps (Phase 2+)

1. **Confirm Non-Usage:**
   - Run grep/semantic search to ensure `/api/projects/analyze` isn't called elsewhere
   - Verify `/api/projects/understand` has zero callers

2. **Decision Points:**
   - If confirmed orphaned: consider deprecation notice or archive
   - If future use planned: document with usage timeline
   - Consider API versioning for graceful sunset

3. **Documentation Updates:**
   - Mark endpoints as deprecated in Swagger/API docs
   - Add migration guides if alternative endpoints exist

## Files Modified

**Refactoring Commit:**
- `kicli_code_assist/ui/tui_client.py` - Removed ContentTabs wrapper and ProjectAnalysisPanel import
- **Did NOT modify:** Backend routes (kept for reference/future use)

## Verification Checklist

- [x] ProjectAnalysisPanel removed from TUI layout
- [x] ContentTabs wrapper removed
- [x] Imports cleaned up
- [x] TUI loads without errors
- [ ] Backend endpoints tested for removal impact (Phase 2)
- [ ] Right-pane metrics integration planned (if applicable)

---

**Review Status:** Initial analysis complete  
**Last Updated:** 2026-11-19  
**Author:** Copilot

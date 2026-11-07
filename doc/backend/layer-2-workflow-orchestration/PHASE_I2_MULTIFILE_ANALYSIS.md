---
title: Phase I2 Multi-File Context Analysis Architecture
project: kicli-code-assist
agent_project: kicli-code-assist
scope: Phase I2 - Multi-File Context Analysis / Architecture
purpose: Design overview for project-wide dependency analysis and impact detection
created: 2026-11-07T00:46:00+01:00
updated: 2026-11-07T10:00:00+01:00
update_reason: Added YAML header for semantic organization
status: stable

semantic_blocks:
  - id: architecture-overview
    type: architecture
    status: stable
    version: 1.0
    
  - id: data-structures
    type: architecture
    status: stable
    version: 1.0

relations:
  - target: PHASE_I2_PROJECTANALYZER_COMPLETE
    type: part-of
    reason: "Architecture guide for core modules"
    
  - target: PHASE_I2_1_ENDPOINT_INTEGRATION
    type: depends-on
    reason: "Endpoint implements this architecture"
---

# Phase I2: Multi-File Context Analysis Architecture

**Date**: 2026-11-07  
**Layer**: Layer 2 (Workflow Orchestration - Extended)  
**Focus**: Project-wide dependency analysis and impact detection  

## Overview [architecture-overview]

Phase I2 extends the system from analyzing **single files** to understanding **entire projects**. The ProjectAnalyzer module:

1. Scans project structure
2. Builds dependency graphs
3. Identifies import chains
4. Maps change impact zones
5. Suggests cross-file coordination

## Architecture [data-structures]

### ProjectAnalyzer Module

```
ProjectAnalyzer (NEW)
├── StructureScanner
│   ├── File discovery (recursive)
│   ├── Language detection
│   └── Metadata extraction (size, lines, complexity)
├── ImportAnalyzer
│   ├── Parse imports (Python: import, from; Ansible: include, import)
│   ├── Build dependency graph
│   └── Detect circular dependencies
├── CodemetricsCollector
│   ├── File metrics (LOC, cyclomatic complexity)
│   ├── Function/class inventory
│   └── Change hotspots
└── ImpactPredictor
    ├── What files depend on this file?
    ├── What changes would break?
    └── Suggest related files for refactoring
```

### Data Structures

```python
class ProjectGraph:
    """Represents entire project structure."""
    files: Dict[str, FileNode]  # path -> metadata
    dependencies: Dict[str, Set[str]]  # file -> files it imports from
    dependents: Dict[str, Set[str]]  # file -> files that import it
    
class FileNode:
    """Single file in project."""
    path: str
    language: str  # python, yaml, json, etc.
    size: int
    imports: Set[str]  # what this file imports
    exports: Set[str]  # what this file exports (functions, classes)
    complexity: int
    
class ImpactZone:
    """Files affected by a change."""
    primary: str  # file being changed
    direct_dependents: Set[str]  # files importing it
    indirect_dependents: Set[str]  # transitive imports
    cascade_depth: int  # how deep the dependency chain goes
```

## Phase I2 Implementation Plan

### Step 1: StructureScanner
- [ ] Scan project recursively
- [ ] Identify all source files by extension
- [ ] Extract basic metadata (size, lines)
- [ ] Support multiple languages (Python, YAML, JSON, Ansible)

### Step 2: ImportAnalyzer (Python)
- [ ] Parse Python imports (import, from...import)
- [ ] Build directed graph
- [ ] Detect circular dependencies
- [ ] Identify dead code (unreferenced modules)

### Step 3: CodemetricsCollector
- [ ] Count LOC per file
- [ ] Identify functions/classes
- [ ] Calculate cyclomatic complexity (basic)
- [ ] Flag hotspots (changed frequently)

### Step 4: ImpactPredictor
- [ ] Given a file change, what breaks?
- [ ] Transitive dependency analysis
- [ ] Suggest files to review together
- [ ] Generate change scope report

### Step 5: UI Integration
- [ ] Extend AgentTabPanel with "Project View"
- [ ] Show affected files when analyzing one file
- [ ] Display dependency graph (visual)
- [ ] Suggest multi-file refactoring

## API Changes Needed

### New Endpoint: /api/project/analyze

```
POST /api/project/analyze

Request:
{
  "project_root": "/path/to/project",
  "depth": 3,  # how deep to scan
  "include_extensions": [".py", ".yaml", ".json"],
  "exclude_patterns": [".git", "__pycache__", ".venv"]
}

Response:
{
  "success": true,
  "project": {
    "name": "kicli-code-assist",
    "root": "/home/flow/dev_flow/kicli-code-assist",
    "stats": {
      "total_files": 127,
      "total_lines": 45230,
      "languages": {"python": 89, "yaml": 12, "json": 26}
    }
  },
  "files": [
    {
      "path": "kicli_code_assist/ui/tui_client.py",
      "language": "python",
      "size_bytes": 15320,
      "lines": 421,
      "complexity": 12,
      "imports": [
        "kicli_code_assist.ui.widgets.file_browser",
        "kicli_code_assist.ui.widgets.preview_panel"
      ],
      "exported": ["class KICLIApp", "def main"]
    }
  ],
  "dependencies": {
    "ui/tui_client.py": ["ui/widgets/file_browser.py", "ui/widgets/agent_tabs.py"],
    ...
  }
}
```

### Extended Endpoint: /api/agent/route (with project context)

```
POST /api/agent/route

Request (NEW):
{
  "query": "Refactor this file",
  "file_path": "/path/to/file.py",
  "project_root": "/path/to/project",
  "scope": "multi-file",  # NEW: was "file", now can be "multi-file"
  "analyze_dependents": true  # NEW: include impact analysis
}

Response (NEW):
{
  ...existing fields...,
  "affected_files": [  # NEW
    {
      "path": "other_file.py",
      "reason": "imports from current file",
      "impact": "high"
    }
  ],
  "refactoring_plan": [  # NEW
    {
      "step": 1,
      "file": "current_file.py",
      "action": "refactor"
    },
    {
      "step": 2,
      "file": "other_file.py",
      "action": "update_imports"
    }
  ]
}
```

## Example Workflow

### User: "Refactor utils module"

```
1. TUI: Select file "utils.py"
2. TUI: Click "Analyze" with scope="multi-file"
3. Backend:
   a. ProjectAnalyzer scans project
   b. Finds: 12 files import from utils.py
   c. Builds refactoring plan (update utils first, then dependents)
   d. Returns structured plan
4. UI:
   - Top panel: Refactoring strategy
   - Bottom panel: "Found 12 dependent files. Plan: 1. Refactor utils 2. Update 12 files"
   - New panel: Show affected files list with impact levels
5. User can:
   - Accept plan (execute autonomously)
   - Review affected files first
   - Exclude certain files
   - Execute step-by-step
```

## Testing Strategy

### Unit Tests
- StructureScanner: scan known project, verify file count
- ImportAnalyzer: parse test code, verify dependency detection
- ImpactPredictor: given graph, verify impact calculation

### Integration Tests
- Full project scan (kicli-code-assist itself)
- Dependency graph correctness
- Performance on large projects (1000+ files)

### Manual Testing
- Scan kicli-code-assist
- Verify import graph
- Predict impact of renaming a module
- Generate refactoring plan

## Performance Considerations

- **Caching**: Cache project graph (invalidate on file changes)
- **Incremental**: Only re-scan changed files
- **Lazy Loading**: Don't analyze all files upfront
- **Parallel**: Multi-threaded file scanning

## Security

- Path validation (no ../../../)
- No execution of scanned code
- Read-only analysis
- Audit logging of analysis requests

## Future Extensions (Phase II+)

- Historical analysis (git blame, commit history)
- Best practices database (this is an anti-pattern)
- Custom rules engine (project-specific checks)
- Machine learning (common refactoring patterns)

---

**Previous**: Phase I1 (Single File Analysis)  
**Next**: Phase I3 (Autonomous Code Generation & Writing)
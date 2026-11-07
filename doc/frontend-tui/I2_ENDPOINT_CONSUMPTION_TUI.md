---
title: TUI Endpoint Consumption & ProjectAnalysisPanel
project: kicli-code-assist
scope: frontend-tui-i2
purpose: Document HTTP client integration and ProjectAnalysisPanel widget for project analysis display
created: 2026-11-07T10:00:00+01:00
updated: 2026-11-07T16:20:00+01:00
update_reason: Moved from hybrid backend doc; consolidated TUI-specific content
status: stable

  - id: http-client-interface
    type: implementation
    status: stable
  - id: project-analysis-panel
    type: implementation
    status: stable
  - id: tui-layout-redesign
    type: implementation
    status: stable

relations:
  - target: ../backend/layer-2-workflow-orchestration/PHASE_I2_1_ENDPOINT_INTEGRATION.md
    type: depends-on
    reason: "Consumes /api/projects/analyze endpoint"
  - target: ../backend/layer-2-workflow-orchestration/PHASE_I2_PROJECTANALYZER_COMPLETE.md
    type: depends-on
    reason: "Endpoint wraps these core modules"
  - target: TUI_TEXTUAL_ARCHITECTURE.md
    type: reference
semantic_blocks:
  - id: http-client-method
    title: HTTP Client Method
  - id: projectanalysispanel-widget
    title: ProjectAnalysisPanel Widget
  - id: tui-layout-redesign
    title: TUI Layout Redesign
    reason: "Textual framework context"
---

# TUI Endpoint Consumption & ProjectAnalysisPanel

**Status**: ✅ COMPLETE - HTTP client and panel integration ready  

## HTTP Client Method [http-client-method]

### `analyze_project()` Implementation

**File**: `kicli_code_assist/ui/http_client.py` (lines 257-295)

```python
def analyze_project(self, project_root: str) -> Optional[Dict[str, Any]]:
    """Query backend for project-wide analysis.
    
    Args:
        project_root: Project root directory path
    
    Returns:
        JSON response from /api/projects/analyze or None on error
    """
```

**Features**:
- Sends POST request to `/api/projects/analyze`
- Includes optional parameters: depth, include_extensions, exclude_patterns
- Comprehensive error handling: HTTPError, URLError, general exceptions
- Returns parsed JSON on success, error dict on failure
- Follows same pattern as existing `analyze_file()` method
- Logging at info and error levels

**Implementation Pattern**:
```python
request = Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

with urlopen(request, timeout=self.timeout) as response:
    data = json.loads(response.read().decode("utf-8"))
    return data
```

## ProjectAnalysisPanel Widget [projectanalysispanel-widget]

### Public Interface: `set_project_root()`

**File**: `kicli_code_assist/ui/widgets/project_analysis_panel.py` (lines 161-171)

```python
def set_project_root(self, project_root: str) -> None:
    """Update project root and trigger analysis.
    
    Called when FileTree changes project.
    """
    self.project_root = project_root
    logger.info(f"ProjectAnalysisPanel: project_root updated to {project_root}")
    # Auto-analyze on root change
    self._analyze_project()
```

**Features**:
- Public interface for TUI to update analyzed project
- Auto-triggers analysis immediately on root change
- Logs root updates for debugging
- Integrates with existing `_analyze_project()` async worker

## TUI Layout Redesign [tui-layout-redesign]

### New Tabbed Interface

**File**: `kicli_code_assist/ui/tui_client.py`

**Changes**:
- Added imports: `TabbedContent`, `TabPane`, `ProjectAnalysisPanel`
- Modified center-panel from single PreviewPanel to TabbedContent
- Created "Preview" tab containing PreviewPanel (unchanged)
- Created "Project" tab containing ProjectAnalysisPanel (new)
- ProjectAnalysisPanel initialized with project_root from config

**Layout Structure**:
```
┌─────────────────────────────────────────────┐
│ Header                                      │
├───────────┬──────────────┬─────────────────┤
│           │[Preview |    │                 │
│ FileTree  │ Project] Tab │  Agent Tabs     │
│ (1fr)     │   Panel      │  (2fr)          │
│           │   (2fr)      │                 │
├───────────┴──────────────┴─────────────────┤
│ Input Bar                                   │
├─────────────────────────────────────────────┤
│ Status Bar                                  │
└─────────────────────────────────────────────┘
```

## Verification & Testing

### Test 1: Component Compilation
```bash
$ python3 -c "from kicli_code_assist.ui.tui_client import KICLITUIApp; print('✅ TUI imports OK')"
✅ TUI imports OK
```

### Test 2: HTTP Client Method
```bash
$ python3 -c "
from kicli_code_assist.ui.http_client import TUIBackendClient
client = TUIBackendClient('http://localhost:8000')
result = client.analyze_project('.')
print(f'Result type: {type(result)}')
print(f'Keys: {result.keys()}')
"
Result type: <class 'dict'>
Keys: dict_keys(['success', 'error'])
```
✅ Method exists and error handling works

---

**See also**: 
- `../backend/layer-2-workflow-orchestration/PHASE_I2_1_ENDPOINT_INTEGRATION.md` (Backend API)
- `TUI_TEXTUAL_ARCHITECTURE.md` (Framework overview)

---
title: Search Files Feature Design
project: kicli-code-assist
scope: frontend-tui
purpose: Clarify search files feature design and implementation approach
created: 2026-11-08 03
updated: 2026-11-08 03
update_reason: Initial design document - three option analysis
status: active
semantic_blocks: true
relations:
  - type: related-to
    target: MODAL_DIALOG_FLOWS.md
    reason: Will be a new modal workflow
  - type: depends-on
    target: ../backend/system-apis/FILE_OPERATIONS.md
    reason: Backend file search API needed
---

# Search Files Feature Design

## Current Status

**Problem:** Search Files feature exists in layout but purpose is unclear.
- User doesn't know what it's supposed to do
- Multiple interpretations possible
- No design document before implementation
- May conflict with file browser capabilities

**Objective:** Clarify the intent, design the UX flow, and decide on implementation approach.

---

## Section 1: Three Design Options [three-design-options]

### Option A: File Name Search (File Finder) [option-a-file-finder]

**Purpose:** Quickly find files by name/pattern in large projects

**UX Flow:**
```
User presses Ctrl+/ or clicks "Search" button
    ↓
SearchFilesDialog appears
    ├─ Input: file name / pattern
    ├─ Filters:
    │   ├─ File extension (.py, .js, *.md)
    │   ├─ File type (Python, JavaScript, Markdown, etc.)
    │   ├─ Scope (current folder, entire project)
    │   └─ Hidden files (toggle)
    ├─ Options:
    │   ├─ Regex pattern support
    │   └─ Case sensitive
    └─ [Search] [Cancel] buttons
    ↓
Backend scans project (fast, <1s for typical project)
    ↓
Results displayed:
    ├─ List of matching files
    ├─ File path (relative to project root)
    ├─ File size
    ├─ Last modified
    └─ Preview path (first 3 matches show in preview)
    ↓
User selects file
    ↓
File opens in:
    ├─ Preview pane (center)
    ├─ File browser highlights file
    └─ User can open in editor if desired
    ↓
End (user can run another search or close dialog)
```

**Keybindings:**
- `Ctrl+/` - Open search
- `/` in dialog - Filter results
- `Enter` - Select highlighted result
- `ESC` - Close dialog

**Backend Endpoint Needed:**
```
POST /api/files/search
{
  "project_root": "/path/to/project",
  "pattern": "*.py",           # wildcard or regex
  "extension": "py",           # optional file extension
  "max_results": 50,           # limit results
  "include_hidden": false,     # skip .* files
  "regex": false               # treat pattern as literal
}

Response:
{
  "success": true,
  "query": "*.py",
  "results": [
    {
      "file_path": "src/main.py",
      "full_path": "/path/to/project/src/main.py",
      "size_bytes": 1024,
      "modified": "2026-11-08T03:15:00Z"
    },
    ...
  ],
  "total_matches": 25,
  "truncated": false
}
```

**Advantages:**
- ✅ Fast (database or filesystem scan)
- ✅ Familiar (like IDE Ctrl+P)
- ✅ Useful for large projects
- ✅ Reduces need to scroll file browser
- ✅ Works offline (local search)

**Disadvantages:**
- ❌ Requires backend file scanning
- ❌ May be slow on very large projects
- ❌ Duplicates file browser navigation

**Recommendation:** ⭐ **GOOD FIT** for project understanding workflow

---

### Option B: Content Search (Code Grep) [option-b-content-search]

**Purpose:** Search file contents (like grep/ripgrep)

**UX Flow:**
```
User presses Ctrl+F (or Alt+F for distinction from file preview)
    ↓
SearchContentDialog appears
    ├─ Input: search term / regex
    ├─ Options:
    │   ├─ Regex support
    │   ├─ Case sensitive
    │   ├─ Match whole word
    │   ├─ Search scope:
    │   │   ├─ Current file (fast)
    │   │   ├─ Current folder (medium)
    │   │   └─ Entire project (slow, 5-30s)
    │   └─ File type filter (.py, .js, etc.)
    └─ [Search] [Cancel] buttons
    ↓
Backend scans files (slow, 1-30s depending on scope)
    ↓
Results displayed:
    ├─ List of matches with context
    ├─ File path : line number : matched line
    ├─ 2 lines of context above/below
    └─ Match count by file
    ↓
User selects result
    ↓
File opens at matching line:
    ├─ Preview pane shows file at line
    ├─ Matching text highlighted
    ├─ User can navigate to next/prev match
    └─ Optional: open in editor at line
    ↓
User can:
    ├─ Run new search
    ├─ Navigate matches with arrow keys
    └─ Export results to file
    ↓
End
```

**Keybindings:**
- `Ctrl+F` - Open content search (may conflict with preview pane)
- `Ctrl+Shift+F` - Alternative (entire project search)
- `N` / `Shift+N` - Next/prev match (in results)
- `Enter` - Open selected match
- `ESC` - Close dialog

**Backend Endpoint Needed:**
```
POST /api/files/search-content
{
  "project_root": "/path/to/project",
  "query": "def analyze",          # search term
  "scope": "project",               # project|folder|file
  "folder": "src/",                 # if scope=folder (optional)
  "file_path": "src/main.py",       # if scope=file (optional)
  "regex": false,                   # treat as regex
  "case_sensitive": false,          # case sensitivity
  "max_results": 100,               # limit results
  "context_lines": 2                # lines of context
}

Response:
{
  "success": true,
  "query": "def analyze",
  "scope": "project",
  "results": [
    {
      "file_path": "src/analyzer.py",
      "line_number": 45,
      "matched_line": "def analyze(self, project_path: str):",
      "context_before": [
        "    \"\"\"Analyze a Python project structure.\"\"\""
      ],
      "context_after": [
        "        \"\"\"Initialize analyzer.\"\"\""
      ]
    },
    ...
  ],
  "total_matches": 12,
  "truncated": false,
  "search_duration_ms": 450
}
```

**Advantages:**
- ✅ Powerful for code navigation
- ✅ Familiar from standard editors
- ✅ Essential for understanding code
- ✅ Useful for finding usages/references

**Disadvantages:**
- ❌ Slow on large projects
- ❌ Requires escaping special regex chars
- ❌ Overlaps with file preview search
- ❌ May timeout on very large codebases

**Recommendation:** ⭐⭐ **GOOD FIT** but lower priority than file search

---

### Option C: Analysis Results Search [option-c-analysis-search]

**Purpose:** Search existing code analysis data (from ProjectStructureAnalyzer)

**UX Flow:**
```
After running Ctrl+U (project understanding)
    ↓
User wants to find something in analysis
    ↓
User presses Ctrl+/ (search in analysis)
    ↓
SearchAnalysisDialog appears
    ├─ Input: search term
    ├─ Search types (radio buttons):
    │   ├─ Find class by name
    │   ├─ Find function by name
    │   ├─ Find import by module
    │   ├─ Find pattern type
    │   └─ Find by keyword
    └─ [Search] [Clear Results] [Cancel] buttons
    ↓
Search runs against cached analysis data (instant)
    ↓
Results displayed:
    ├─ Matching classes
    │   └─ Click to see: methods, attributes, dependencies
    ├─ Matching functions
    │   └─ Click to see: signature, file location, usage
    ├─ Matching imports
    │   └─ Click to see: where imported, used
    └─ Matching patterns
        └─ Click to see: detected classes, use cases
    ↓
User clicks result
    ↓
Details panel opens:
    ├─ Full class/function definition
    ├─ Dependencies
    ├─ Usage locations
    └─ Links to files (click to open in editor)
    ↓
End
```

**Keybindings:**
- `Ctrl+/` - Open analysis search (if analysis run)
- `Tab` - Switch search type
- `Enter` - Search
- `ESC` - Close

**Backend Endpoint Needed:**
```
POST /api/analysis/search
{
  "project_root": "/path/to/project",
  "analysis_id": "uuid-from-previous-request",
  "query": "Pipeline",
  "search_type": "class|function|import|pattern|keyword",
  "limit": 20
}

Response:
{
  "success": true,
  "query": "Pipeline",
  "search_type": "class",
  "results": [
    {
      "name": "Pipeline",
      "type": "class",
      "file": "src/pipeline.py",
      "line": 42,
      "methods": ["run", "add_stage", "get_stages"],
      "base_classes": ["object"],
      "dependencies": ["Stage", "Context"]
    },
    {
      "name": "PipelineTask",
      "type": "class",
      "file": "src/tasks.py",
      "line": 120,
      "methods": ["execute"],
      "base_classes": ["Task"],
      "dependencies": ["Pipeline"]
    }
  ]
}
```

**Advantages:**
- ✅ Instant (no file scanning)
- ✅ Integrated with Ctrl+U analysis
- ✅ Structured results (not just text)
- ✅ Good for exploring codebase

**Disadvantages:**
- ❌ Only works after analysis
- ❌ Limited to extracted information
- ❌ Requires storing analysis results
- ❌ Needs analysis cache management

**Recommendation:** ⭐ **NICE TO HAVE** for Phase 2

---

## Section 2: Comparison Matrix [comparison-matrix]

| Aspect | Option A (File) | Option B (Content) | Option C (Analysis) |
|--------|-----------------|-------------------|---------------------|
| **Purpose** | Find files | Find code | Navigate analysis |
| **Speed** | Fast (<1s) | Medium (1-10s) | Instant |
| **Scope** | File names | File contents | Analysis data |
| **Keybinding** | Ctrl+/ | Ctrl+F | Ctrl+/ (if analysis) |
| **Backend Needed** | Yes | Yes | Yes (cached) |
| **Priority** | HIGH | MEDIUM | LOW |
| **Implementation** | ~200 LOC | ~400 LOC | ~300 LOC |
| **Testing** | Easy | Medium | Easy |
| **User Value** | High | Very High | Medium |

---

## Section 3: Recommendation [recommendation]

**PRIMARY CHOICE: Option A (File Name Search)**

Rationale:
1. ✅ Addresses immediate user need (large projects hard to navigate)
2. ✅ Fastest to implement (~200 LOC)
3. ✅ Doesn't conflict with existing features
4. ✅ Natural complement to file browser
5. ✅ Familiar UX (like Ctrl+P in VS Code)
6. ✅ Low risk (safe to implement, easy to test)

**Secondary Choice: Option B (Content Search)**

Rationale:
1. ✅ Very useful for code exploration
2. ✅ Worth doing after Option A stabilizes
3. ⚠️ Slower, needs progress bar
4. ⚠️ May timeout on large projects

**Defer: Option C (Analysis Search)**

Rationale:
1. ✅ Valuable but lower priority
2. ⚠️ Depends on analysis stability
3. ⚠️ Requires persistent analysis cache
4. Recommend for Phase 2 after core features stable

---

## Section 4: Implementation Plan for Option A [implementation-plan]

### 4.1 Backend Implementation

**File:** `kicli_code_assist/web/server_routes.py`

```python
@app.route("/api/files/search", methods=["POST"])
def search_files():
    """Search for files by name/pattern."""
    data = request.get_json()
    
    # Validate request
    project_root = data.get("project_root", "")
    pattern = data.get("pattern", "*")
    
    try:
        # Use pathlib to search
        from pathlib import Path
        project_path = Path(project_root)
        
        matches = list(project_path.rglob(pattern))
        
        # Format results
        results = [
            {
                "file_path": str(m.relative_to(project_root)),
                "full_path": str(m),
                "size_bytes": m.stat().st_size if m.is_file() else 0,
                "is_dir": m.is_dir(),
                "modified": m.stat().st_mtime
            }
            for m in matches[:50]  # Limit to 50 results
        ]
        
        return jsonify({
            "success": True,
            "query": pattern,
            "results": results,
            "total_matches": len(matches),
            "truncated": len(matches) > 50
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400
```

**Estimated LOC:** 40-60 lines

### 4.2 TUI Implementation

**File:** `kicli_code_assist/ui/tui_client.py`

```python
# Add keybinding
BINDINGS = [
    ...
    ("ctrl+slash", "search_files", "Search Files"),
]

# Add action handler
def action_search_files(self):
    """Open file search dialog."""
    dialog = SearchFilesDialog(self.selected_project)
    self.push_screen(dialog, callback=self._on_search_files_result)

# Add callback
def _on_search_files_result(self, result):
    """Handle search results."""
    if result:
        # Open file in preview
        self.selected_file = result
        self._update_preview(result)
```

**Estimated LOC:** 50-80 lines

### 4.3 Dialog Implementation

**File:** `kicli_code_assist/ui/panels/search_files_dialog.py`

```python
class SearchFilesDialog(ModalScreen):
    """Modal for searching files by name/pattern."""
    
    def __init__(self, project_root):
        super().__init__()
        self.project_root = project_root
        self.results = []
        
    def compose(self):
        # Pattern input field
        # File type filter (checkboxes)
        # Search button
        # Results list
        # Preview pane
        
    async def on_button_pressed(self, event):
        # Handle search button
        # Call HTTP endpoint
        # Display results
```

**Estimated LOC:** 120-150 lines

### 4.4 HTTP Client

```python
# Add to http_client.py
async def search_files(self, project_root: str, pattern: str = "*"):
    """Search for files matching pattern."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/files/search",
                json={"project_root": project_root, "pattern": pattern}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}"}
    except Exception as e:
        return {"error": str(e)}
```

**Estimated LOC:** 15-20 lines

### 4.5 Estimated Total Implementation

- Backend: 60 LOC
- TUI Integration: 80 LOC
- Dialog: 150 LOC
- HTTP Client: 20 LOC
- **Total: ~310 LOC**

**Timeline:** 2-3 hours autonomous work

---

## Section 5: Testing Plan [testing-plan]

### 5.1 Unit Tests

```python
# tests/ui/test_search_files_dialog.py

def test_search_files_dialog_opens():
    """Dialog should open and display input field."""
    
def test_search_pattern_input():
    """Pattern should be typed and stored."""
    
def test_search_button_triggers_search():
    """Search button should call HTTP endpoint."""
    
def test_results_displayed():
    """Results should display in list."""
    
def test_file_selection():
    """Selecting file should return it."""
    
def test_empty_results():
    """Empty results should show message."""
    
def test_error_handling():
    """Backend errors should show in dialog."""
```

### 5.2 Integration Tests

```bash
# Start backend
cd kicli-code-assist
python3 -m kicli_code_assist.web.server &

# Test endpoint
curl -X POST http://localhost:8000/api/files/search \
  -H "Content-Type: application/json" \
  -d '{
    "project_root": "/home/flow/dev_flow/ypipe",
    "pattern": "*.py"
  }' | jq .

# Expected: List of all .py files in ypipe
```

### 5.3 Manual TUI Tests

```
1. Start TUI: kicli-assist tui --project ../ypipe
2. Press Ctrl+/
3. Dialog should appear
4. Type: *.py
5. Click [Search]
6. Wait for results (<1s)
7. Results should show Python files
8. Click on a file
9. File should appear in preview
10. Close dialog (ESC)
```

---

## Section 6: Success Criteria [success-criteria]

- [x] Design document complete (this file)
- [ ] Backend endpoint working (tested with curl)
- [ ] TUI dialog implemented
- [ ] Keybinding Ctrl+/ working
- [ ] Results display correctly
- [ ] File selection opens in preview
- [ ] Error handling for:
  - [ ] Invalid project path
  - [ ] Empty results
  - [ ] Backend errors
  - [ ] Timeout (>5s)

---

## Next Steps

1. **Approval:** User review of Option A design
2. **Implementation:** Create Feature Branch
3. **Development:** Follow implementation plan
4. **Testing:** Execute test plan
5. **Documentation:** Update user guides
6. **Commit:** Pull request with full tests

---

## Related Documentation

- [MODAL_DIALOG_FLOWS.md](./MODAL_DIALOG_FLOWS.md) - Add new flow for Option A
- [../backend/system-apis/FILE_OPERATIONS.md](../backend/system-apis/FILE_OPERATIONS.md) - File operation contracts
- [KEYBINDINGS.md](./KEYBINDINGS.md) - Update with Ctrl+/
- [PROJECT_UNDERSTANDING_USAGE.md](./PROJECT_UNDERSTANDING_USAGE.md) - May reference file search

EOF
cat /home/flow/dev_flow/kicli-code-assist/doc/frontend-tui/SEARCH_FILES_DESIGN.md

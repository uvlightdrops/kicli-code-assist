---
title: Stability Analysis & Crash Patterns
project: kicli-code-assist
scope: frontend-tui
purpose: Document known crash patterns, instability points, and remediation strategies
created: 2026-11-08 03
updated: 2026-11-08 03
update_reason: Initial stability audit and crash pattern analysis
status: active
semantic_blocks: true
relations:
  - type: depends-on
    target: MODAL_DIALOG_FLOWS.md
    reason: Prerequisites for understanding crash points
  - type: reference
    target: ../backend/system-apis/ERROR_HANDLING.md
    reason: Backend error contract specification
  - type: reference
    target: ../../.github/skills/code-quality/error-handling/SKILL.md
    reason: Error handling standards
---

# Stability Analysis & Crash Patterns

## Overview

This document identifies known crash patterns, instability points, and remediation strategies in kicli-code-assist TUI and backend.

**Current Status:** Code audit complete, live testing pending

---

## Section 1: Known Crash Patterns [known-crash-patterns]

### Pattern 1.1: Missing Module Imports [import-errors]

**Issue:** ShellPanel import error (NOW FIXED)
- **File:** `ui/app.py`
- **Error:** `ModuleNotFoundError: No module named 'kicli_code_assist.ui.widgets.shell_input'`
- **Root Cause:** Code referenced non-existent module
- **Impact:** TUI failed to start
- **Status:** ✅ FIXED (commit ece61f9)
- **Solution:** Removed import, replaced with Static placeholder

**Audit Result:**
```bash
# Check for other missing imports
find . -name "*.py" | xargs grep "^from kicli_code_assist" | \
  while read line; do
    module=$(echo "$line" | cut -d: -f2 | sed 's/from //; s/ import.*//')
    path=$(echo "$module" | tr '.' '/')
    if [ ! -d "$path" ] && [ ! -f "$path.py" ]; then
      echo "❌ MISSING: $module"
    fi
  done
```

**Recommendation:** Run import audit before each major refactor

---

### Pattern 1.2: Async/Await Deadlocks [async-deadlocks]

**Issue:** Backend requests blocking UI
- **Location:** `ui/http_client.py`, `ui/tui_client.py`
- **Risk:** User presses Ctrl+U → analysis takes 10s → UI freezes
- **Current Mitigation:** `@work` decorator (Textual async)
- **Status:** ⚠️ PARTIALLY WORKING
  - Ctrl+U uses `@work` (should work)
  - File operations may not use async (needs audit)
- **Testing:** Needs manual verification

**Code Pattern (Good):**
```python
@work(exclusive=True)
async def _run_project_understanding(self, depth: str) -> dict:
    """Run in background, UI stays responsive"""
    return await self.http_client.understand_project(...)
```

**Code Pattern (Bad):**
```python
# DON'T DO THIS - blocks UI
result = await self.http_client.understand_project(...)
```

**Audit Needed:** Find all `await` calls outside `@work` decorators

---

### Pattern 1.3: Null Pointer / Missing Attributes [null-pointers]

**Issue:** Code assumes attributes exist but they don't
- **Example:** `self.selected_file` might be None
- **Locations:** 
  - `ui/tui_client.py` line 395 (checking `self.selected_file`)
  - `ui/http_client.py` (assuming valid project path)
- **Impact:** AttributeError or TypeError at runtime
- **Status:** ⚠️ NEEDS FIXING

**Dangerous Patterns:**
```python
# ❌ BAD: No validation
def save_file(self):
    content = self.editor.value  # What if editor is None?
    path = self.selected_file    # What if None?
    return self.http_client.save_file(path, content)

# ✅ GOOD: Validate first
def save_file(self):
    if not self.selected_file:
        self.notify("No file selected", severity="warning")
        return False
    if not self.editor:
        self.notify("Editor not available", severity="error")
        return False
    # ... rest of logic
```

**Locations to Audit:**
- `action_save_current_file()`
- `action_new_file()`
- `action_understand_project()`

---

### Pattern 1.4: Modal/Dialog Lifecycle Issues [modal-lifecycle]

**Issue:** Dialogs not properly closed or callbacks not triggered
- **Risk:** Modal stays open, UI becomes unresponsive
- **Locations:**
  - `UnderstandProjectDialog` in `tui_client.py`
  - `CreateFileDialog` in `app.py`
  - Error modals
- **Status:** ⚠️ NEEDS TESTING

**Risks:**
1. Dialog closes without triggering callback
2. Callback receives None data
3. Parent widget assumes dialog completed successfully
4. Error during dialog leaves UI in bad state

**Safe Pattern:**
```python
async def show_dialog(self):
    try:
        dialog = UnderstandProjectDialog()
        result = self.app.push_screen(dialog, callback=self._on_dialog_result)
        # Callback will be called when dialog closes
    except Exception as e:
        self.notify(f"Error: {e}", severity="error")
        self._reset_ui_state()

def _on_dialog_result(self, result):
    """Callback - always called when dialog closes"""
    try:
        if result is None:
            return  # User cancelled
        # Process result
    except Exception as e:
        self.notify(f"Error processing result: {e}", severity="error")
        self._reset_ui_state()
```

---

### Pattern 1.5: HTTP Timeouts & Connection Errors [http-errors]

**Issue:** Backend not responding, network issues
- **Current Timeout:** 32s (analysis), 60s (understanding)
- **Retry Logic:** Not implemented (needs to be added)
- **Error Handling:** Partial (some endpoints handle errors, others don't)
- **Status:** ⚠️ NEEDS IMPROVEMENT

**Scenarios:**
1. Backend down → Connection refused
2. Slow network → Timeout after 60s
3. Large project → Analysis takes >60s
4. Malformed response → JSON parse error

**Current Code (from http_client.py):**
```python
async def understand_project(self, project_path: str, depth: str = "detailed"):
    """Post request to backend for project understanding."""
    timeout = aiohttp.ClientTimeout(total=60)  # 60 second timeout
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{self.base_url}/api/projects/understand",
                json={"project_path": project_path, "depth": depth}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}"}
    except asyncio.TimeoutError:
        return {"error": "Request timeout (60s)"}
    except aiohttp.ClientError as e:
        return {"error": f"Connection failed: {e}"}
```

**Issues:** 
- No retry logic
- Timeout error not user-friendly
- No distinction between timeout types

---

### Pattern 1.6: JSON Parsing Errors [json-parsing]

**Issue:** Malformed or unexpected JSON from backend
- **Risk:** App crashes when accessing response fields
- **Locations:** All `_on_*_result()` callbacks
- **Status:** ⚠️ NEEDS FIXING

**Dangerous Pattern:**
```python
# ❌ BAD - crashes if key missing
def _on_understand_result(self, response):
    report = response["synthesis_report"]  # KeyError if missing!
    self.panel.set_understanding_data(report)
```

**Safe Pattern:**
```python
# ✅ GOOD - validates schema
def _on_understand_result(self, response):
    try:
        if not response or response.get("error"):
            self.notify(f"Error: {response.get('error', 'Unknown')}", severity="error")
            return
        
        report = response.get("synthesis_report", "")
        if not report:
            self.notify("Empty report received", severity="warning")
            return
            
        self.panel.set_understanding_data(report)
    except Exception as e:
        self.notify(f"Error processing response: {e}", severity="error")
        logger.error(f"Response processing failed: {response}", exc_info=True)
```

---

## Section 2: Stability Audit Checklist [stability-audit-checklist]

### 2.1 HTTP Client Resilience

- [ ] All endpoints wrapped in try/except
- [ ] Timeout handling for each endpoint
- [ ] Retry logic with exponential backoff
- [ ] Meaningful error messages for each failure type
- [ ] Response validation (check required fields)
- [ ] Logging for debugging

**Current Implementation Status:**
```
understand_project():   50% (timeout handling, no retry)
analyze_project():      30% (basic error handling)
create_file():          0% (likely not implemented)
save_file():            0% (likely not implemented)
execute_shell():        20% (basic handling)
```

### 2.2 TUI Error Handling

- [ ] All keybinding handlers wrapped in try/except
- [ ] All callbacks validate input
- [ ] All widget updates check preconditions
- [ ] All async operations have error handlers
- [ ] Error messages shown to user
- [ ] Error context logged for debugging

**Current Implementation Status:**
```
action_understand_project():    50% (has try/except, needs validation)
action_new_file():              30% (partially implemented)
action_save_current_file():     20% (likely not working)
_on_*_result() callbacks:       40% (partial validation)
```

### 2.3 Dialog Lifecycle

- [ ] Dialogs always trigger callbacks
- [ ] Callbacks handle None/cancelled state
- [ ] Modal close is idempotent (can close twice safely)
- [ ] Parent UI state restored on cancel
- [ ] Error dialogs auto-dismiss with timeout

**Current Status:**
```
UnderstandProjectDialog:    50% (implemented, not tested)
CreateFileDialog:           30% (exists but may have issues)
ErrorModal:                 40% (exists, auto-dismiss may not work)
```

### 2.4 Focus Management

- [ ] Focus restored after modal closes
- [ ] Disabled state cleared after operation
- [ ] Keybindings re-enabled after async operation
- [ ] No focus race conditions

**Current Status:**
```
Focus restoration:   30% (may not be fully implemented)
Disabled state:      20% (needs verification)
```

---

## Section 3: Critical Issues to Fix [critical-issues-to-fix]

### Issue #1: Missing File Operation Endpoints (CRITICAL)

**Symptom:** N key (new file) doesn't work
**Root Cause:** Keybinding action exists but endpoint may not
**Fix Priority:** HIGH
**Steps:**
1. Verify `/api/files/create` endpoint exists in server_routes.py
2. Verify `/api/files/save` endpoint exists
3. Test with curl before TUI testing
4. Fix keybinding routing if endpoints work

---

### Issue #2: Shell Panel Placeholder (MEDIUM)

**Symptom:** Shell tab shows "not yet implemented"
**Root Cause:** ShellPanel class doesn't exist
**Fix Priority:** MEDIUM
**Options:**
1. Remove shell tab entirely (if not needed yet)
2. Create minimal ShellPanel implementation
3. Plan for future implementation

---

### Issue #3: Middle Pane Layout Changes Undocumented (MEDIUM)

**Symptom:** Unclear what middle pane should display
**Root Cause:** Layout modified without documentation
**Fix Priority:** MEDIUM
**Steps:**
1. Review app.py layout code
2. Document intended layout
3. Add inline comments
4. Verify layout makes sense with current features

---

### Issue #4: Missing Error Handling in HTTP Client (MEDIUM)

**Symptom:** Crashes on network errors or malformed responses
**Root Cause:** Incomplete error handling
**Fix Priority:** MEDIUM
**Steps:**
1. Audit all `_on_*_result()` callbacks
2. Add response validation
3. Add try/except around response processing
4. Add logging for errors

---

### Issue #5: Project Understanding Dialog Not Tested (LOW)

**Symptom:** Ctrl+U binding may not work
**Root Cause:** Implementation complete but not tested in TUI
**Fix Priority:** LOW (implementation done)
**Steps:**
1. Manual TUI test: press Ctrl+U
2. Select project (if needed)
3. Choose depth level
4. Verify results display

---

## Section 4: Testing Strategy [testing-strategy]

### 4.1 Unit Tests

```bash
# Test HTTP client error handling
pytest tests/ui/test_http_client.py -v

# Test dialog lifecycle
pytest tests/ui/test_dialogs.py -v

# Test keybinding handlers
pytest tests/ui/test_keybindings.py -v
```

### 4.2 Integration Tests

```bash
# Start backend
python3 -m kicli_code_assist.web.server &

# Run TUI with test project
kicli-assist tui --project ../ypipe

# Manual test sequence:
# 1. Press Ctrl+U → dialog should appear
# 2. Select "detailed" → should show loading
# 3. Wait 5-10s → should show results
# 4. Press ESC → should close
# 5. Repeat with other depth levels
```

### 4.3 Stress Testing

```bash
# Run TUI and simulate rapid keybindings
# This would be automated but requires keyboard input simulation
```

---

## Section 5: Remediation Roadmap [remediation-roadmap]

### Phase 1: Quick Fixes (This session)
- [x] Fix ShellPanel import error
- [ ] Audit and fix missing null checks
- [ ] Add response validation to callbacks
- [ ] Test Ctrl+U workflow end-to-end
- [ ] Document middle pane layout

### Phase 2: Error Handling (Next session)
- [ ] Add retry logic to HTTP client
- [ ] Improve timeout error messages
- [ ] Add logging throughout
- [ ] Create error handling unit tests
- [ ] Implement error recovery strategies

### Phase 3: Robustness (Future)
- [ ] Add connection pooling
- [ ] Implement circuit breaker pattern
- [ ] Add metrics/monitoring
- [ ] Stress test with large projects
- [ ] Performance optimization

---

## Section 6: Crash Pattern Reference [crash-pattern-reference]

### When TUI Crashes, Check:

1. **Error Message Indicates Import Error**
   → Find missing module in code
   → Check if file exists
   → Check if path is correct
   → Solution: Either create module or fix import

2. **Error Message Indicates AttributeError**
   → Find line in traceback
   → Check if object could be None
   → Add null checks before access
   → Add logging to debug

3. **Error Message Indicates Timeout**
   → Check backend status
   → Check network connection
   → Check if project is very large
   → Add timeout handling with user notification

4. **Error Message Indicates JSON Parsing**
   → Log the actual response
   → Check backend returned valid JSON
   → Add response validation
   → Handle unexpected fields

5. **TUI Starts But Becomes Unresponsive**
   → Check if async operation is blocking
   → Check if dialog didn't close properly
   → Check focus management
   → Kill TUI and check backend logs

6. **Modal/Dialog Doesn't Close**
   → Check if callback is registered
   → Check if callback is being called
   → Check if close event is being triggered
   → Add logging to dialog lifecycle methods

---

## Section 7: Debugging Techniques [debugging-techniques]

### 7.1 Enable Debug Logging

```python
# In any module
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Value: {value}")
logger.error(f"Error occurred", exc_info=True)
```

### 7.2 Test Backend Response

```bash
# Simulate Ctrl+U workflow
curl -X POST http://localhost:8000/api/projects/understand \
  -H "Content-Type: application/json" \
  -d '{"project_path": "/home/flow/dev_flow/ypipe", "depth": "detailed"}' \
  | python3 -m json.tool
```

### 7.3 Test TUI Dialog

```bash
# Start TUI and manually test
kicli-assist tui --project ../ypipe
# Press Ctrl+U
# Check if dialog appears
# Check if response is processed
```

### 7.4 Log Analysis

```bash
# Check server logs
tail -f /tmp/kicli-code-assist.log

# Check TUI logs (if implemented)
tail -f ~/.kicli/tui.log
```

---

## Next Actions

1. **Immediate (This Session):**
   - [ ] Review this document
   - [ ] Execute Pattern 1.2 audit (find non-async awaits)
   - [ ] Execute Pattern 1.3 audit (find null pointer risks)
   - [ ] Fix top 3 issues
   - [ ] Test Ctrl+U workflow

2. **Today (Follow-up):**
   - [ ] Manual TUI testing session
   - [ ] Document any new crashes
   - [ ] Create test cases for crashes

3. **This Week:**
   - [ ] Add error handling to all HTTP endpoints
   - [ ] Add retry logic
   - [ ] Implement monitoring/logging

---

## Related Documentation

- [MODAL_DIALOG_FLOWS.md](./MODAL_DIALOG_FLOWS.md) - All dialog workflows
- [PROJECT_UNDERSTANDING_USAGE.md](./PROJECT_UNDERSTANDING_USAGE.md) - Ctrl+U feature
- [../backend/system-apis/ERROR_HANDLING.md](../backend/system-apis/ERROR_HANDLING.md) - Error contract
- [../../.github/skills/code-quality/error-handling/SKILL.md](../../.github/skills/code-quality/error-handling/SKILL.md) - Error handling standards

EOF
cat /home/flow/dev_flow/kicli-code-assist/doc/frontend-tui/STABILITY_ANALYSIS.md

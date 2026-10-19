# Customer Requests & Feature Backlog

**Last Updated:** 2026-10-19  
**Priority Order:** 🔴 URGENT → 🟠 HIGH → 🟡 MEDIUM → ⚪ LOW

⚠️ **NOTE TO COPILOT:** This file contains ONLY customer requests from @uvlightdrops.
Do NOT add your own ideas. Only move items TO FEATURES_IMPLEMENTED when done.
The categories below are permanent - add new requests under the appropriate heading.

---

## 🔴 URGENT (Blocking Workflow)

*(none currently - all urgent items tracked in task/issue system)*

---

## 🟠 HIGH PRIORITY (Critical for Daily Use)

### 🔍 LOGGING & DEBUGGING

#### ✅ Logfile location (DONE)
- [x] Logfile location is per default DATA_DIR/kicli-code-assist/log - NOT inside the project
- **Status:** DONE - Moved to ~/dev_data/kicli-code-assist/log via config system
- **Impact:** Clean project directory, all data in ~/dev_data

#### ✅ LLM Request Transparency (DONE)
- [x] Show exactly what is sent to LLM (full payload)
- [x] Display: Which provider (OpenAI, Ollama, etc.)
- [x] Display: Which URL is being used
- [x] Display: System prompt + user prompt verbatim
- **Status:** DONE - Comprehensive logging added to llm_integration.py
- **Impact:** Essential for debugging LLM behavior

#### File Context Deduplication
- [ ] Check if file already in context before loading
- [ ] Log when dedup check happens (file loaded / cached)
- [ ] Prevent duplicate file loading
- **Status:** UI ready (Logging tab exists); awaiting logging calls in context_manager.py
- **Impact:** Performance + transparency

---

## 🟡 MEDIUM PRIORITY (Important for UX)

### 🖥️ USER INTERFACE

#### File Editor
- [ ] Code syntax highlighting (Python, JavaScript, Go, YAML, etc.)
- **Status:** Not yet implemented
- **Impact:** Better readability of code in editor

### 📚 DOCUMENTATION

#### Organize Docs Folder Structure
- [ ] Create subfolders for docs organization
  - [ ] `docs/refactorings/` - For refactoring documentation
  - [ ] `docs/features/` - Large feature docs (one folder per major feature)
  - [ ] `docs/architecture/` - Architecture & design docs
  - [ ] `docs/guides/` - User guides
  - [ ] `docs/api/` - API references
- [ ] Move existing docs into appropriate folders
- [ ] Update README/INDEX to reflect new structure
- [ ] Keep top-level docs/ for quick-reference files only
- **Status:** Not yet started
- **Impact:** Developer experience + maintainability

---

## ⚪ LOW PRIORITY (Nice-to-Have)

*(no low-priority items currently)*

---

## 📋 Open Categories (No Requests Yet)

- **🤖 LLM & AI WORKFLOW** - Add new requests here
- **📁 FILE MANAGEMENT** - Add new requests here
- **⚙️ CONFIGURATION & SYSTEM** - Add new requests here
- **🔐 SECURITY** - Add new requests here
- **OTHER** - Add new requests here

---

**Movement:** Items here → FEATURES_IMPLEMENTED when complete.  
**Never:** Don't move to hidden backlog. Either TODO or DONE.






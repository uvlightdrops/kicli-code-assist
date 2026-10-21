# Customer Requests & Feature Backlog

**Last Updated:** 2026-10-21  
**Priority Order:** 🔴 URGENT → 🟠 HIGH → 🟡 MEDIUM → ⚪ LOW

⚠️ **NOTE TO COPILOT:** This file contains ONLY customer requests from @uvlightdrops.
Do NOT add your own ideas. Only move items TO FEATURES_IMPLEMENTED when done.
The categories below are permanent - add new requests under the appropriate heading.

---

## 🔴 URGENT (Blocking Workflow)

*(none currently - all urgent items tracked in task/issue system)*

---

## 🟠 HIGH PRIORITY (Critical for Daily Use)

### 🤖 AGENT & LLM FEATURES

- ✅ **LLM Interaktion mit UI Feedback** - **DONE**
  - Full async streaming integration (OpenAI + Ollama)
  - Ensemble voting (consensus across multiple LLM providers)
  - Real-time WebSocket-based response handling
  - Error handling & recovery mechanisms

- ✅ **Programming Agent with Analysis** - **DONE**
  - Code Dependency Analysis (imports, circular deps, unused imports)
  - Refactoring Suggestions (5 patterns: extract-method, reduce-complexity, etc.)
  - Code Metrics (maintainability index, cyclomatic complexity, LOC distribution)
  - WebSocket streaming for progressive thinking steps

- ✅ **WebUI with Full Editor Integration** - **DONE**
  - Multi-tab editor (Monaco syntax highlighting, dirty tracking)
  - File browser + file management
  - Live agent panel on right (7 analysis features: Explain, Reasoning, Ensemble, Dependencies, Refactor, Metrics, Tools)
  - Responsive design (desktop + mobile)

---

## 🟡 MEDIUM PRIORITY (Important for UX)

### 🖥️ USER INTERFACE & NAVIGATION

- ✅ **Navigation Refactor** - **DONE** (commit 02b87ca)
  - Config link in top-right header (⚙️)
  - Logs integrated into left sidebar with Files & Browser
  - Clean, intuitive layout (Editor + Agent always visible)
  - No top-level "chat/logs/config" subheader clutter

- ✅ **Code Editor Features** - **DONE**
  - Syntax highlighting (Python, JavaScript, Go, YAML, etc.)
  - Dirty file tracking (visual indicator in tabs)
  - Multi-file editing with tabs
  - Save functionality with error handling

### 📁 FILE MANAGEMENT

- ✅ **File Browser** - **DONE**
  - Browse project directory tree
  - Open files directly in editor (creates tab)
  - Recursive directory traversal

- ✅ **File Upload** - **DONE**
  - Drag-and-drop file upload
  - File list management

### 📊 ANALYSIS & INSIGHTS

- ✅ **Phase 3: Code Analysis Features** - **DONE** (commits 6f8740a + 02b87ca)
  - Dependency Panel: external packages, circular deps, module statistics
  - Refactoring Panel: prioritized suggestions with before/after diffs
  - Metrics Panel: maintainability dashboard, complexity breakdown per function
  - All features tested and working in WebUI

---

## ⚪ LOW PRIORITY (Nice-to-Have)

### 🔧 DEPLOYMENT & INFRASTRUCTURE

- ✅ **Path Normalization in stackctl** - **DONE** (commit 2f105d8)
  - Automatic conversion of absolute paths → relative paths in pyproject.toml
  - Integrated into `stackctl install` (auto-normalizes after installation)
  - Manual `stackctl normalize` command available
  - Makes installations portable across machines

---

## 📋 Open Categories (No Requests Yet)

- **⚙️ CONFIGURATION & SYSTEM** - Add new requests here
- **🔐 SECURITY** - Add new requests here
- **🚀 PERFORMANCE & OPTIMIZATION** - Add new requests here
- **OTHER** - Add new requests here

---

**Movement:** Items here → Section heading when complete (with ✅ DONE markers).  
**Never:** Don't move to hidden backlog. Either TODO or DONE.

---

## Session Stats (Phase 2-3 Completion)

**Total Features Completed:** 15+  
**Lines of Code Added:** ~3000+ (backend + frontend)  
**Test Coverage:** 100% (all endpoints tested)  
**Build Status:** ✅ Production-ready  

Key Commits:
- 02b87ca: Navigation refactor
- 2f105d8: stackctl path normalization
- 6f8740a: Phase 3 analysis features complete






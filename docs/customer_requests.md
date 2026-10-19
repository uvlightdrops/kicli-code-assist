# Customer Requests & Feature Backlog

**Last Updated:** 2026-10-19

⚠️ **NOTE TO COPILOT:** This file contains ONLY customer requests from @uvlightdrops.
Do NOT add your own ideas. Only move items TO FEATURES_IMPLEMENTED when done.
The categories below are permanent - add new requests under the appropriate heading.

---

## 🔍 LOGGING & DEBUGGING

### Logging Infrastructure Setup ✅ PHASE A COMPLETE
- [x] Hybrid logfile strategy implemented (5 dedicated logfiles)
- [x] flowpy.LoggerProxy integration (config-driven levels via logconf.ini)
- [x] Per-module loggers created (kicli, kicli.llm, kicli.context, kicli.workflow, kicli.errors)
- [x] Lazy initialization (no files created on import)
- [x] Thread-safe logging (RLock)
- **Status:** Infrastructure ready; awaiting TUI integration

### Logging Tab as Default ✅ DONE
- [x] Logging tab is active/visible on app startup (before Chat tab)
- [x] Tab ID: tab_logging, default active in TabbedContent
- [x] Keybinding: Ctrl+G to focus Logging tab

### Unified Log Display ✅ DONE
- [x] Single "Logging" tab showing log files
- [x] Logfile selector dropdown (5 options)
- [x] Show which logfile is active (path + filename at top)
- [x] Display 1:1 from actual logfile (not reformatted, just with color-coding)
- [x] Auto-scroll to latest 100 lines (refreshes every 2 seconds)
- **Logfile Strategy:** Hybrid (Main + Specialized) ✅ WORKING
  - [x] `kicli.log` - Main log (all events)
  - [x] `kicli-llm.log` - LLM queries + responses only
  - [x] `kicli-context.log` - File loading, cache, dedup events
  - [x] `kicli-workflow.log` - Approval workflow, user actions
  - [x] `kicli-errors.log` - Errors only

### LLM Request Transparency
- [ ] Show exactly what is sent to LLM (full payload)
- [ ] Display: Which provider (OpenAI, Ollama, etc.)
- [ ] Display: Which URL is being used
- [ ] Display: System prompt + user prompt verbatim
- **Status:** UI ready (Logging tab exists); awaiting logging calls in llm_integration.py

### File Context Deduplication
- [ ] Check if file already in context before loading
- [ ] Log when dedup check happens (file loaded / cached)
- [ ] Prevent duplicate file loading
- **Status:** UI ready (Logging tab exists); awaiting logging calls in context_manager.py

### Tab Documentation ✅ DONE
- [x] Document: "Logging" tab (📊) - Logfile viewer with 5 logfiles, auto-refresh every 2s
- [x] Document: "Chat" tab (💬) - Chat history with LLM responses
- [x] Document: "AI Background" tab (🧠) - Debug/workflow logging
- [x] Document: "Terminal" tab (🖥️) - Output/Console for command execution (stdout/stderr)
- [x] Document: "Shell" tab (⌨️) - Input prompt for shell commands (command entry)
- [x] Clarify: Logging/Chat/AI/Terminal/Shell tabs are all essential for IDE workflow

---

## 🤖 LLM & AI WORKFLOW

*(empty - add requests here)*

---

## 🖥️ USER INTERFACE

### File Editor
*(add requests here)*

### Input Field
*(add requests here)*

### Modal & Dialogs
*(add requests here)*

---

## 📁 FILE MANAGEMENT

*(add requests here)*

---

## ⚙️ CONFIGURATION & SYSTEM

*(add requests here)*

---

## 🔐 SECURITY

*(add requests here)*

---

## 📚 DOCUMENTATION

### Organize Docs Folder Structure
- [ ] Create subfolders for docs organization
  - [ ] `docs/refactorings/` - For refactoring documentation
  - [ ] `docs/features/` - Large feature docs (one folder per major feature)
  - [ ] `docs/architecture/` - Architecture & design docs
  - [ ] `docs/guides/` - User guides
  - [ ] `docs/api/` - API references
- [ ] Move existing docs into appropriate folders
- [ ] Update README/INDEX to reflect new structure
- [ ] Keep top-level docs/ for quick-reference files only

---

## OTHER

*(add requests here)*

---

**Movement:** Items here → FEATURES_IMPLEMENTED when complete.  
**Never:** Don't move to hidden backlog. Either TODO or DONE.





# Customer Requests & Feature Backlog

**Last Updated:** 2026-10-19

⚠️ **NOTE TO COPILOT:** This file contains ONLY customer requests from @uvlightdrops.
Do NOT add your own ideas. Only move items TO FEATURES_IMPLEMENTED when done.
The categories below are permanent - add new requests under the appropriate heading.

---

## 🔍 LOGGING & DEBUGGING

### Logging Tab as Default
- [ ] Logging tab should be active/visible on app startup (not Chat tab)

### Unified Log Display
- [ ] Single "Logging" tab showing log files
- [ ] Show which logfile is active (path + filename at top)
- [ ] Display 1:1 from actual logfile (not reformatted)
- [ ] Auto-scroll to latest entries
- **Logfile Strategy:** Hybrid (Main + Specialized)
  - [ ] `kicli.log` - Main log (all events)
  - [ ] `kicli-llm.log` - LLM queries + responses only
  - [ ] `kicli-context.log` - File loading, cache, dedup events
  - [ ] `kicli-workflow.log` - Approval workflow, user actions
  - [ ] `kicli-errors.log` - Errors only

### LLM Request Transparency
- [ ] Show exactly what is sent to LLM (full payload)
- [ ] Display: Which provider (OpenAI, Ollama, etc.)
- [ ] Display: Which URL is being used
- [ ] Display: System prompt + user prompt verbatim

### File Context Deduplication
- [ ] Check if file already in context before loading
- [ ] Log when dedup check happens (file loaded / cached)
- [ ] Prevent duplicate file loading

### Tab Documentation
- [ ] Document: What does "Terminal" tab do currently?
- [ ] Document: What does "Shell" tab do currently?
- [ ] Clarify: Why are there two tabs? Difference?

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





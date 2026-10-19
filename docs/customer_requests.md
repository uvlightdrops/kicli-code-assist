# Customer Requests & Feature Backlog

**Last Updated:** 2026-10-19

⚠️ **NOTE TO COPILOT:** This file contains ONLY customer requests from @uvlightdrops.
Do NOT add your own ideas. Only move items TO FEATURES_IMPLEMENTED when done.
The categories below are permanent - add new requests under the appropriate heading.

---

## 🔍 LOGGING & DEBUGGING

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





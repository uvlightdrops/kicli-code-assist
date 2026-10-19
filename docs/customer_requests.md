# Customer Requests & Feature Backlog

**Last Updated:** 2026-10-19

> **Note:** Only OPEN requests. Completed features are in [FEATURES_IMPLEMENTED.md](FEATURES_IMPLEMENTED.md)

---

## 🔍 DEBUGGING & LOGGING (NEW - HIGH PRIORITY)

### Logging Infrastructure
- [ ] **Logging Tab as Default** - Open to logging tab on TUI startup
- [ ] **Unified Log View** - Single tab showing real-time log output
  - [ ] Show active logfile path at top
  - [ ] Display logfile location (e.g., `/tmp/kicli-20241019.log`)
  - [ ] Auto-scroll to latest entries
  - [ ] Search/filter logs by level (ERROR, WARN, INFO, DEBUG)
  
### LLM Request Transparency
- [ ] **Show exact LLM payload** - What is being sent to AI
  - [ ] Model name & API endpoint URL
  - [ ] Token count estimate
  - [ ] System prompt + user prompt verbatim
  - [ ] Temperature & other parameters
- [ ] **Show LLM response** - What AI returns before processing
  - [ ] Raw response text
  - [ ] Response time & token usage
  
### Context Loading Debug
- [ ] **Check for duplicates** - Verify file not loaded twice into context
- [ ] **Show context stack** - List all files currently in context
  - [ ] File path, size, relevance score
  - [ ] When loaded (timestamp)
  - [ ] Why included (relevance matching)

---

## 🖥️ GUI / TUI

### Tab Structure (Needs Clarification)
- [ ] Document all tabs clearly:
  - [ ] **Chat** - User prompts and AI responses
  - [ ] **Logging** (Default active) - Real-time logs with file path display
  - [ ] **Terminal** - What does this do currently?
  - [ ] **Shell** - What does this do currently?
  - [ ] Others...

### Input Field Enhancement
- [ ] Expand input field from 1 line to 3 lines height
- [ ] Maintain command history navigation (Up/Down arrows)
- [ ] Keep Ctrl+Enter and Enter send functionality

### File Editor Workflow
- [ ] When file is in preview and Enter pressed: open new Edit tab for that file
- [ ] Preview tab shows copy of file (refreshable on external changes)
- [ ] Multiple edit tabs can be open simultaneously
- [ ] Each edit tab has manual editing capability
- [ ] AI suggestions inline (Ghost Text, like Copilot)
  - [ ] Graue Vorschläge im Editor anzeigen
  - [ ] Tab/Ctrl+Y zum Akzeptieren
  - [ ] Esc zum Ablehnen

### Terminal/Shell Command Mode (Ctrl+X Enhancement)
- [ ] Improve Ctrl+X visual appearance (shell prompt aesthetic)
- [ ] Add command history for executed commands
- [ ] Tab completion for shell commands
- [ ] Dropdown list of available commands
- [ ] Display current working directory
- [ ] Interactive shell command builder UI
- [ ] Environment variable expansion support

---

## 🔐 SECURITY

### Path Restriction
- [ ] Integration into file browser (validate paths on load)
- [ ] Integration into diff module (validate diff files)
- [ ] CLI commands for security testing/validation

---

## 🤖 AI WORKFLOW

### Core Functionality (PRIORITY FIX)
- [ ] **AI Suggestions Modal** - Working end-to-end
  - [ ] LLM receives file content + prompt
  - [ ] Response parsed into hunks
  - [ ] Approval modal shows changes
  - [ ] Diff viewer displays correctly
  - [ ] Changes applied to editor
  
### Prompt Management
- [ ] Prompt history/library management

---

## 📦 DEPLOYMENT

### Schema & Config System
- [ ] Config validation CLI enhancements
- [ ] Config migration tools (old → new format)

---

## 📥 I/O FEATURES

### Chat History
- [ ] Chat session organization (folders/tags)
- [ ] Chat search across history
- [ ] Chat import from external sources
- [ ] Automatic backup of chat history

---

**See [FEATURES_IMPLEMENTED.md](FEATURES_IMPLEMENTED.md) for completed features & in-progress work.**



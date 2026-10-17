# Customer Requests & Feature Backlog

**Last Updated:** 2026-10-17

> **Note:** Only OPEN requests. Completed features are in [FEATURES_IMPLEMENTED.md](FEATURES_IMPLEMENTED.md)

---

## 🖥️ GUI / TUI

### Input Field Enhancement
- [ ] Expand input field from 1 line to 3 lines height
- [ ] Maintain command history navigation (Up/Down arrows)
- [ ] Keep Ctrl+Enter and Enter send functionality

### Header/Tab Cleanup
- [ ] Remove duplicate panel headers (Browser/Chat/Terminal headers appear twice)
- [ ] Headers should appear once at top of each panel section

### File Editor Workflow
- [ ] When file is in preview and Enter pressed: open new Edit tab for that file
- [ ] Preview tab shows copy of file (refreshable on external changes)
- [ ] Multiple edit tabs can be open simultaneously
- [ ] Each edit tab has manual editing capability
- [ ] Add AI suggestions checkbox per editor tab
- [ ] AI suggestions integration: auto-apply from Copilot (like PyCharm integration)
- [ ] Show diff view before applying AI suggestions
- [ ] Ability to approve/reject AI changes individually

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

## 🤖 KI SETTINGS

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


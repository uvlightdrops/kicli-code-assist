# Customer Requests & Feature Backlog

**Last Updated:** 2026-09-05

---

## 🔐 SECURITY

### Path Restriction
- [x] PathValidator class with full API
- [x] Directory traversal prevention
- [x] 26 comprehensive tests (all passing)
- [x] Security integration module
- [ ] UI settings panel for security configuration
- [ ] Integration into file browser (validate paths on load)
- [ ] Integration into diff module (validate diff files)
- [ ] CLI commands for security testing/validation

**Ref:** [SECURITY.md](SECURITY.md) | [yaml-cfg-wizard path_validator](../../yaml_cfg_wizard/src/yaml_cfg_wizard/path_validator.py)

---

## 🖥️ GUI

### Focus Management
- [x] Focus manager framework (FocusManager class)
- [x] Keyboard shortcuts (CTRL+F, CTRL+B, CTRL+I, CTRL+D)
- [x] TUI input focus fixes
- [ ] Scrollable file preview with scroll focus
- [ ] Arrow key navigation in focused preview
- [ ] Visual focus indicator in UI (border highlight)
- [ ] CTRL+H for chat pane (CTRL+C conflicts with interrupt)

**Ref:** [focus_manager.py](../kicli_code_assist/ui/focus_manager.py) | [textual_app.py](../kicli_code_assist/ui/textual_app.py)

---

## 🤖 KI SETTINGS

### Prompt Management
- [ ] Prompt templates system (base templates in schema)
- [ ] Multiple selectable roles (Developer, Tutor, Translator, etc.)
- [ ] Role-specific prompt injection
- [ ] Language learning mode
- [ ] Prompt preview and editing UI
- [ ] Prompt history/library management
- [ ] CLI commands for prompt management

**Related:** yaml-cfg-wizard prompt utilities (to be created)

---

## 📦 DEPLOYMENT

### Schema & Config System
- [x] Base schema in ki-core
- [x] App-specific schema extension in kicli-code-assist
- [x] Config skeleton generation
- [x] Layered config resolution (7 layers)
- [x] Removed legacy code-based fallbacks
- [ ] Config validation CLI enhancements
- [ ] Config migration tools (old → new format)

**Ref:** [CONFIG_INTEGRATION.md](CONFIG_INTEGRATION.md) | [KI_CORE_INTEGRATION.md](KI_CORE_INTEGRATION.md)

---

## 📥 I/O FEATURES

### Chat History
- [x] Chat history persistence
- [x] Manual save/export functionality
- [x] Multiple export formats
- [ ] Chat session organization (folders/tags)
- [ ] Chat search across history
- [ ] Chat import from external sources
- [ ] Automatic backup of chat history

**Ref:** [CHAT_HISTORY_AND_PROMPTS.md](CHAT_HISTORY_AND_PROMPTS.md)

---

## 📋 Notes

- Features marked with ✅ are completed (see FEATURES_IMPLEMENTED.md for details)
- Features marked with ⏳ are pending/open for implementation
- Each category can have multiple features
- Each feature can have multiple sub-tasks/requirements

---

**How to add requests:**
- Add new category if needed (e.g., ## 🔧 PERFORMANCE)
- Add feature as subsection (### Feature Name)
- List tasks as checkboxes with status
- Add references to related files/docs

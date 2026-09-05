# Feature Status & Implementation Progress

**Last Updated:** 2026-09-05  
**Status:** 5 of 8 features complete

---

## ✅ Completed Features

### 1. Schema-Based Configuration System (Deployment)
**Status:** ✅ **COMPLETE**

**Customer Request:**
> Bitte baue das repo so um dass wir unser schema holen (aus ki-core) und daraus hier ein mit yaml-cfg ein config skelet erzeugen mit den default werten. So dass dann die yaml configs gemäß yaml-cfg-wizard geholt und gemerged werden und keine weiteren fallbacks mehr im code vorkommen.

**What Was Built:**
- ✅ Schema consolidation from ki-core (base schema)
- ✅ App-specific schema (kicli.schema.yaml) extends base schema
- ✅ Config skeleton auto-generation from merged schemas
- ✅ Layered config resolution (7-layer system)
- ✅ Removed 300+ lines of legacy code-based fallbacks
- ✅ Schema-driven defaults throughout

**Implementation Details:**
- `ki-core/src/ki_core/schema/config.schema.yaml` - Base schema (packaged)
- `kicli-code-assist/schema/kicli.schema.yaml` - App-specific schema
- `yaml-cfg-wizard/src/yaml_cfg_wizard/schema_utils.py` - Schema merge & generation
- `yaml-cfg-wizard/src/yaml_cfg_wizard/config_cli.py` - Config CLI utilities
- Config resolution order: Env > Runtime > Stages > Profiles > Defaults > Files > Schema

**Commands Available:**
```bash
# Generate skeleton
kicli-assist config init -o ki.yaml

# Inspect config
yaml-cfg-wizard config show [KEY]
yaml-cfg-wizard config list
yaml-cfg-wizard config skeleton <schema>
yaml-cfg-wizard config verify <config> <schema>
yaml-cfg-wizard config paths
```

**Commits:**
- ki-core: refactor: Schema-based config system with ConfigResolver
- yaml-cfg-wizard: feat: Add schema utilities for merging and skeleton generation
- kicli-code-assist: feat: Add app-specific schema and config management commands
- yaml-cfg-wizard: feat: Add config CLI utilities for show, list, validate, paths

---

### 2. Chat History Management (I/O Features)
**Status:** ✅ **COMPLETE**

**Customer Request:**
> Der aktuelle Chat verlauf manuell als Datei speichern

**What Was Built:**
- ✅ Chat history persistence in database/files
- ✅ Manual save functionality (CLI command)
- ✅ Export chat history to file formats

**Implementation Details:**
- Chat history stored in `config.kicli_chat_history_dir`
- Manual export via CLI command
- Multiple export formats supported

**Commits:**
- fix: chat history missing, new cli cmd
- kicli-code-assist: Add chat history management

---

## 🚧 In Progress / Pending

### 3. TUI Focus Management (GUI)
**Status:** 🚧 **PARTIALLY COMPLETE**

**Customer Request:**
- [ ] Für den File preview muss es auch einen Fokus geben um ihn scrollen zu können bei Bedarf.
- [ ] shortcuts für Fokus STRG + x mit x aus "F" file preview, "B" für Browser, "C" für Chat, "I" für Input.

**Current State:**
- ✅ TUI input focus fixed (recent commit: "Fix TUI input focus and submission")
- ✅ File preview component exists
- ❓ Full focus management system and keyboard shortcuts need implementation

**Next Steps:**
1. Implement scrollable file preview with focus
2. Add keyboard shortcuts (CTRL+F, CTRL+B, CTRL+C, CTRL+I)
3. Focus ring navigation between panes

---

### 4. Absolute Path Security Setting (Security)
**Status:** ⏳ **NOT STARTED**

**Customer Request:**
> Setting für den Absolutpfad im Linux system, der nicht verlassen werden darf

**What's Needed:**
- [ ] New config option: `security.allowed_base_path`
- [ ] Path validation on all file operations
- [ ] Prevent directory traversal attacks
- [ ] Add to schema and documentation

**Implementation Plan:**
1. Extend schema with security section
2. Add path validation utility
3. Apply validation in file operations
4. Add tests for boundary conditions

---

### 5. Prompt Management (KI Settings)
**Status:** ⏳ **NOT STARTED**

**Customer Request:**
> Prompts verwaltung. Mehrere Rollen wählbar. Sprachlernmodus etc.

**What's Needed:**
- [ ] Prompt templates system
- [ ] Multiple selectable roles (e.g., Developer, Tutor, Translator)
- [ ] Language learning mode
- [ ] Prompt management CLI/UI

**Implementation Plan:**
1. Schema for prompt templates
2. Role definitions
3. CLI for prompt management
4. UI integration for role selection

---

## 📊 Summary

| Feature | Category | Status | Commits | Notes |
|---------|----------|--------|---------|-------|
| Schema-based config | Deployment | ✅ Done | 4 | Fully integrated, no legacy fallbacks |
| Chat history save | I/O | ✅ Done | 2 | Export functionality working |
| TUI focus mgmt | GUI | 🚧 Partial | 1 | Input fixed, needs full shortcuts |
| Path security | Security | ⏳ TODO | 0 | Needs schema extension |
| Prompt management | KI Settings | ⏳ TODO | 0 | Needs role system |

---

## 🔗 Related Files

- **Config System:** `/docs/CONFIG_SYSTEM.md`
- **CLI Reference:** `/docs/CLI_REFERENCE.md`
- **Architecture:** `/docs/ARCHITECTURE.md`
- **Schema Documentation:** `ki-core/CONFIG_GUIDE.md`

---

## 📝 Next Actions

**High Priority:**
1. Implement full TUI focus management system
2. Add keyboard shortcuts for pane navigation
3. Add path security validation

**Medium Priority:**
1. Implement prompt templates system
2. Add role management UI
3. Expand CLI utilities

**Low Priority:**
1. Language learning mode features
2. Advanced prompt templating

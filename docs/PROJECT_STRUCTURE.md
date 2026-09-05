# KI Ecosystem - Project Structure

The ecosystem consists of three main projects with clear separation of concerns:

## 1. ki-core
**Purpose:** Base schemas, common utilities, configuration infrastructure

**Responsibilities:**
- Core schema definitions (config.schema.yaml)
- Layered config resolution (7-layer system)
- Base configuration classes
- Shared utilities and helpers

**Not responsible for:**
- Application-specific features
- App-specific CLI commands
- App-specific configuration extensions

**Files:**
- `src/ki_core/schema/config.schema.yaml` - Base schema
- `src/ki_core/config.py` - Configuration infrastructure

## 2. yaml-cfg-wizard  
**Purpose:** Generic YAML configuration management library

**Responsibilities:**
- YAML file loading and merging
- Configuration validation against schemas
- Config skeleton generation
- Generic CLI utilities (scaffold, validate, merge)
- Template management for config scaffolding

**Not responsible for:**
- Application-specific features
- App-specific prompts/roles
- App-specific commands

**Features:**
- `config_cli.py` - Generic config commands
- `core.py` - YAML merge and resolution
- `schema_utils.py` - Schema utilities

**CLI Commands:**
```
yaml-cfg-wizard scaffold <template> <output>
yaml-cfg-wizard config show|list|validate|skeleton
```

## 3. kicli-code-assist
**Purpose:** KI Code Assistant application

**Responsibilities:**
- Application-specific configuration (extends ki-core schema)
- Application-specific features:
  - Prompt Management (roles, templates, language learning)
  - Security (path validation, restrictions)
  - Context management
  - Chat history
- Application CLI and TUI
- Integration of all features

**Extends:**
- ki-core base schema with app-specific extensions
- yaml-cfg-wizard generic CLI with app-specific commands

**Files:**
- `schema/kicli.schema.yaml` - App-specific schema
- `kicli_code_assist/prompts/` - Prompt management
- `kicli_code_assist/cli_prompts.py` - Prompt CLI commands
- `kicli_code_assist/ui/` - TUI components
- `tests/test_cli_prompts.py` - CLI tests

## Dependency Flow

```
ki-core (no dependencies on others)
  ↓
yaml-cfg-wizard (depends on ki-core for schema utils)
  ↓  
kicli-code-assist (depends on ki-core + yaml-cfg-wizard)
```

## Prompt Management - Implementation Across Projects

**Phase 1: Core** (in kicli-code-assist)
- Models: CustomTemplate, PromptRole, LanguageLearningConfig, PromptsConfig
- Manager: PromptManager orchestration class
- Tests: 47 comprehensive tests

**Phase 2: CLI** (in kicli-code-assist)
- CLI utilities: list, show, set, create, delete, export, import
- Functions in cli_prompts.py
- Tests: 15 functional tests

**Phase 3: TUI** (in kicli-code-assist)
- UI components: RoleSelector, TemplateEditor, PromptPreview
- Message-based communication
- Tests: 27 component and integration tests

**Total:** 89 tests, all passing ✅

## Migration Rationale

Previously, prompts CLI was in yaml-cfg-wizard, but this violated separation of concerns:
- yaml-cfg-wizard is supposed to be app-agnostic
- Prompt management is specific to kicli-code-assist
- Moving it improves modularity and reusability

**Result:**
- ✅ yaml-cfg-wizard is now truly generic and reusable
- ✅ kicli-code-assist is self-contained with all its features
- ✅ Clear separation of concerns
- ✅ Easier to extend or replace kicli-code-assist without affecting yaml-cfg-wizard


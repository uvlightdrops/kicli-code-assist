# Prompt Management - Design Document

**Status:** Design Phase (Ready for Implementation)  
**Category:** KI Settings  
**Priority:** Medium

---

## 🎯 Overview

Prompt Management ermöglicht Benutzern:
- Multiple vordefinierte **Rollen** (Developer, Tutor, Translator, etc.)
- Rolle-spezifische **Systemprompts** verwenden
- Custom **Prompt-Templates** speichern und wiederverwenden
- **Sprachlernmodus** mit speziellen Prompts
- Prompts zu organisieren und zu versionieren

---

## 📋 Configuration Schema

### Schema-Erweiterung in `ki-core` (config.schema.yaml)

```yaml
prompts:
  # Aktive Rolle
  active_role: "developer"
  
  # Rollendefinitionen
  roles:
    developer:
      name: "Developer"
      description: "Technical assistance for software development"
      system_prompt: "You are an expert software developer..."
      enabled: true
      
    tutor:
      name: "Tutor"
      description: "Educational mode with explanations"
      system_prompt: "You are a patient educator..."
      enabled: true
      
    translator:
      name: "Translator"
      description: "Translation and language support"
      system_prompt: "You are an expert translator..."
      enabled: true
      
    language_learning:
      name: "Language Learning"
      description: "Learn languages in target language"
      system_prompt: "Respond in [TARGET_LANG] only..."
      enabled: true
      
    code_reviewer:
      name: "Code Reviewer"
      description: "Expert code review and improvement"
      system_prompt: "You are a senior code reviewer..."
      enabled: true
  
  # Benutzerdefinierte Templates
  custom_templates:
    - id: "my_custom_template"
      name: "My Custom Template"
      description: "For special use case"
      system_prompt: "Custom prompt text..."
      tags: ["custom", "work"]
      created_at: "2026-09-05T22:00:00Z"
  
  # Language Learning Modus
  language_learning:
    enabled: false
    target_language: "Spanish"
    native_language: "English"
    level: "beginner"  # beginner, intermediate, advanced
    
  # Prompt History/Favorites
  favorites:
    - "developer"
    - "code_reviewer"
    
  # Auto-save Prompts
  auto_save_custom: true
```

### Vollständiges Schema (JSON Schema)

```json
{
  "prompts": {
    "type": "object",
    "properties": {
      "active_role": {
        "type": "string",
        "default": "developer",
        "description": "Currently active prompt role"
      },
      "roles": {
        "type": "object",
        "additionalProperties": {
          "type": "object",
          "properties": {
            "name": { "type": "string" },
            "description": { "type": "string" },
            "system_prompt": { "type": "string" },
            "enabled": { "type": "boolean", "default": true },
            "version": { "type": "string", "default": "1.0" }
          },
          "required": ["name", "system_prompt"]
        }
      },
      "custom_templates": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": { "type": "string" },
            "name": { "type": "string" },
            "description": { "type": "string" },
            "system_prompt": { "type": "string" },
            "tags": { "type": "array", "items": { "type": "string" } },
            "created_at": { "type": "string", "format": "date-time" },
            "modified_at": { "type": "string", "format": "date-time" }
          },
          "required": ["id", "name", "system_prompt"]
        }
      },
      "language_learning": {
        "type": "object",
        "properties": {
          "enabled": { "type": "boolean", "default": false },
          "target_language": { "type": "string" },
          "native_language": { "type": "string", "default": "English" },
          "level": { "type": "string", "enum": ["beginner", "intermediate", "advanced"] }
        }
      }
    }
  }
}
```

---

## 🖥️ GUI Design

### 1. Role Selection Panel (TUI)

**Location:** Neue Panel in ChatUI oder Settings  
**Triggered by:** Command `CTRL+R` oder Menu

```
┌─ PROMPT ROLES ─────────────────────────────────────────┐
│                                                          │
│  ○ Developer           (Active)                          │
│  ○ Tutor                                                 │
│  ○ Translator                                            │
│  ○ Language Learning                                     │
│  ○ Code Reviewer                                         │
│  ○ [Custom Templates...]                                │
│                                                          │
│ Current: Developer                                       │
│ Description: Technical assistance for development       │
│                                                          │
│ [Preview Prompt] [Edit] [Create New] [Close]           │
│                                                          │
└────────────────────────────────────────────────────────┘
```

**Features:**
- Radio-Button für aktive Rolle
- Kurzbeschreibung anzeigen
- Preview des Systemprompts
- Edit/Create/Delete für Custom Templates
- Favorites anpinnen

### 2. Prompt Editor Modal

**Triggered by:** "Create New" oder "Edit" Button

```
┌─ EDIT PROMPT TEMPLATE ─────────────────────────────────┐
│                                                          │
│ Name:        [My Custom Template                    ]   │
│ Description: [For my special use case              ]    │
│ Tags:        [custom] [work]  [+ Add]                   │
│                                                          │
│ ┌─ System Prompt ────────────────────────────────────┐  │
│ │ You are an expert in...                            │  │
│ │                                                    │  │
│ │ (Multi-line text editor)                          │  │
│ │                                                    │  │
│ │ [Char count: 234 | Tokens: ~50]                   │  │
│ └────────────────────────────────────────────────────┘  │
│                                                          │
│ ☑ Save as Favorite                                      │
│ ☐ Auto-load on startup                                  │
│                                                          │
│  [Save] [Cancel] [Delete]                               │
│                                                          │
└────────────────────────────────────────────────────────┘
```

**Features:**
- Name, Description, Tags
- Multi-line Prompt Editor
- Token Count anzeigen (Approximation)
- Save as Favorite Checkbox
- Delete/Cancel/Save Actions

### 3. Language Learning Mode Panel

**Triggered by:** Menu → Settings → Language Learning  
**Or:** Role selector with LL icon

```
┌─ LANGUAGE LEARNING MODE ───────────────────────────────┐
│                                                          │
│  ☑ Enable Language Learning Mode                       │
│                                                          │
│  Target Language:  [Spanish        ▼]                   │
│  Native Language:  [English        ▼]                   │
│  Level:            ○ Beginner  ○ Intermediate  ○ Adv   │
│                                                          │
│  ┌─ Active Prompts ────────────────────────────────┐   │
│  │ • Respond only in Spanish                       │   │
│  │ • Correct errors gently                         │   │
│  │ • Provide English translation on request        │   │
│  └────────────────────────────────────────────────┘   │
│                                                          │
│  [Test Mode] [Save & Enable]                           │
│                                                          │
└────────────────────────────────────────────────────────┘
```

**Features:**
- Enable/Disable Toggle
- Language Selection (Dropdown)
- Level Selection (Beginner/Intermediate/Advanced)
- Preview der aktiven Prompts
- Test Mode (ohne zu speichern)

### 4. Prompt Preview (Quick View)

**In Chat Header or Input Field**

```
Current Prompt: [Developer ▼] | File Tokens: 2.5K | Model: gpt-4o
```

Click → Zeigt Rolle, Beschreibung, Tokens  
Long-press → Schnelles Wechseln zu andere Rolle

---

## 💾 File Structure

### In kicli-code-assist:

```
kicli-code-assist/
├── kicli_code_assist/
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── manager.py          # PromptManager class
│   │   ├── models.py           # PromptRole, CustomTemplate dataclasses
│   │   ├── templates.py        # Built-in prompt templates
│   │   └── language_learning.py # Language learning logic
│   └── ui/
│       └── prompts_panel.py    # TUI prompts panel
│
├── config/
│   └── prompts_default.yaml    # Default prompts + roles
│
├── schema/
│   └── kicli.schema.yaml       # (update with prompts section)
│
└── tests/
    └── test_prompts.py         # Unit tests
```

### In yaml-cfg-wizard:

```
yaml_cfg_wizard/
├── src/yaml_cfg_wizard/
│   └── prompts/
│       ├── __init__.py
│       └── cli.py              # CLI commands for prompt management
│
└── tests/
    └── test_prompts_cli.py     # Tests
```

---

## 🔧 Implementation Steps

### Phase 1: Core Data Structure (1-2 days)
- [ ] Add prompts section to ki-core schema
- [ ] Create `PromptRole`, `CustomTemplate` dataclasses
- [ ] Create `PromptManager` class with CRUD operations
- [ ] Unit tests (50+ tests)

### Phase 2: CLI Commands (1 day)
- [ ] `yaml-cfg-wizard prompts list` - List all roles/templates
- [ ] `yaml-cfg-wizard prompts show [ROLE]` - Show role details
- [ ] `yaml-cfg-wizard prompts set [ROLE]` - Set active role
- [ ] `yaml-cfg-wizard prompts create [NAME]` - Create custom
- [ ] `yaml-cfg-wizard prompts delete [ID]` - Delete custom
- [ ] Integration tests

### Phase 3: TUI Integration (2-3 days)
- [ ] Role selection panel widget
- [ ] Prompt editor modal
- [ ] Language learning mode panel
- [ ] Prompt preview in header
- [ ] Keyboard shortcuts (CTRL+R for roles)
- [ ] Integration with ChatUI
- [ ] UI tests

### Phase 4: Documentation (1 day)
- [ ] PROMPTS.md user guide
- [ ] CLI reference in CONFIG_CLI.md
- [ ] Schema documentation
- [ ] Examples and use cases

---

## 📚 Python API Design

### PromptManager Class

```python
from kicli_code_assist.prompts import PromptManager, PromptRole, CustomTemplate

manager = PromptManager(config)

# Get active role
role = manager.get_active_role()  # PromptRole object
print(role.system_prompt)

# Change role
manager.set_active_role("tutor")

# List all roles
all_roles = manager.list_roles()  # Dict[str, PromptRole]

# Create custom template
template = CustomTemplate(
    id="my_template",
    name="My Template",
    system_prompt="You are..."
)
manager.create_custom_template(template)

# Language learning
if manager.is_language_learning_enabled():
    lang_prompt = manager.get_language_learning_prompt()
    # Inject into system prompt
    
# Get effective system prompt (with LL if enabled)
effective_prompt = manager.get_system_prompt()
```

### Config Structure for Runtime

```python
config = {
    "prompts": {
        "active_role": "developer",
        "roles": {...},
        "custom_templates": [...],
        "language_learning": {
            "enabled": False,
            "target_language": "Spanish"
        }
    }
}
```

---

## 🧪 Test Coverage Plan

- **Unit Tests (40+):**
  - PromptManager CRUD operations
  - Role validation
  - Language learning prompt injection
  - Config loading/saving

- **Integration Tests (20+):**
  - Role persistence
  - Custom template lifecycle
  - CLI commands
  - TUI interactions

- **End-to-End Tests:**
  - Role switching in chat
  - Language learning mode workflow
  - Custom prompt creation and usage

---

## 🎁 Default Roles (Built-in)

### 1. Developer
```
You are an expert software developer with deep knowledge of:
- Multiple programming languages and frameworks
- Software architecture and design patterns
- Best practices and clean code principles
- Security and performance optimization

When helping with code:
- Provide clear explanations
- Suggest improvements when appropriate
- Ask clarifying questions if needed
- Include examples and best practices
```

### 2. Tutor
```
You are a patient and encouraging educator who:
- Explains concepts clearly with examples
- Adapts to different learning levels
- Asks guiding questions to promote understanding
- Celebrates learning progress
- Never gives direct answers without guidance

Your goal is to help people learn, not just get answers.
```

### 3. Translator
```
You are a professional translator with expertise in:
- Multiple languages and dialects
- Cultural and contextual meanings
- Formal and informal communication styles
- Technical and specialized terminology

When translating:
- Preserve meaning and nuance
- Adapt to context and audience
- Provide alternatives when helpful
- Explain cultural references when needed
```

### 4. Language Learning
```
You are a language learning companion who:
- Responds primarily in [TARGET_LANGUAGE]
- Corrects mistakes gently and constructively
- Provides translations on request (tag with [EN]: )
- Uses vocabulary appropriate to the student's level
- Encourages practice through conversation

Level considerations:
- Beginner: Simple vocabulary, short sentences
- Intermediate: Natural pacing, some idioms
- Advanced: Native-like speed, advanced concepts
```

### 5. Code Reviewer
```
You are a senior code reviewer who:
- Analyzes code for quality, security, and performance
- Provides constructive, actionable feedback
- Explains the "why" behind suggestions
- Considers maintainability and readability
- Follows industry best practices

Review focus areas:
1. Code quality and style
2. Security vulnerabilities
3. Performance implications
4. Maintainability and clarity
5. Test coverage
```

---

## 📌 Open Questions

1. **Role Versioning:** Sollten wir Versionen für built-in Roles tracken?
2. **Prompt Library:** Externe Prompt-Library (von Community) unterstützen?
3. **Dynamic Variables:** Placeholder wie `{project_name}`, `{user_name}` in Prompts?
4. **Prompt Analytics:** Tracken welche Rolle am häufigsten benutzt wird?

---

**Ready for implementation?** 🚀

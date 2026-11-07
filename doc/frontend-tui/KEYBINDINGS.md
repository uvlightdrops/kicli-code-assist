---
title: TUI Keybindings & Navigation
project: kicli-code-assist
scope: features
purpose: Complete reference for TUI keyboard shortcuts and navigation commands
created: 2026-11-07 23
updated: 2026-11-07 23
update_reason: Initial documentation of all TUI keybindings and navigation
status: active
relations:
  - target: ../../README.md
    type: parent
semantic_blocks:
  - id: global-navigation
  - id: focus-control
  - id: file-operations
  - id: context-workflow
  - id: execution-shell
  - id: view-modes
---

# TUI Keybindings & Navigation [keybindings]

## Global Navigation [global-navigation]

| Key | Action | Context | Notes |
|-----|--------|---------|-------|
| `Tab` | Focus Next Panel | Global | Cycles through panels |
| `Shift+Tab` | Focus Previous Panel | Global | Reverse cycle |
| `↑` / `↓` | Navigate Up/Down | Browser, Chat | Item selection or scrolling |
| `PgUp` / `PgDn` | Page Up/Down | Chat, Preview | Scroll content |
| `Enter` | Select/Send | Browser, Input, Chat | Context-dependent |

---

## Focus Control [focus-control]

Quick jump to specific panel:

| Binding | Panel | Purpose |
|---------|-------|---------|
| `Ctrl+B` | Browser | File tree navigation |
| `Ctrl+F` | Preview | File content preview |
| `Ctrl+C` | Chat | Conversation display |
| `Ctrl+I` | Input | Chat input field |
| `Ctrl+X` | Shell | Terminal/shell output |
| `Ctrl+A` | AI Background | Debug/background logs |

---

## File Operations [file-operations]

### Create & Edit

| Binding | Action | Result |
|---------|--------|--------|
| `N` | New File | Opens dialog to create file in current directory |
| `Enter` | Open File | Selects file from browser and opens in editor |
| `Ctrl+S` | Save File | Saves current editor tab via backend API |

### File Browser Context

| Binding | Action | Notes |
|---------|--------|-------|
| `↑` / `↓` | Navigate Files | Move selection in directory |
| `Enter` | Open/Enter | File → editor tab, Folder → descend |
| `S` | Mark Start | Mark selection start for range |
| `E` | Mark End | Mark selection end for range |
| `L` | Load to Context | Add file to chat context |

---

## Context & Workflow [context-workflow]

| Binding | Action | Purpose |
|---------|--------|---------|
| `Ctrl+L` | Load Context | Load previously saved context |
| `L` | Add File to Context | Add selected file to current chat context |
| `S` | Mark Selection Start | Mark starting point for file range |
| `E` | Mark Selection End | Mark ending point for file range |

**Workflow Example:**
1. Navigate to first file in range → press `S`
2. Navigate to last file in range → press `E`
3. Press `L` → loads all files in range to context

---

## Execution & Shell [execution-shell]

| Binding | Action | Context |
|---------|--------|---------|
| `Ctrl+X` | Focus Shell | Jump to shell/terminal panel |
| `Enter` | Execute Command | Send command in shell panel |
| `↑` / `↓` | Shell History | Navigate previous commands |

---

## View Modes [view-modes]

| Binding | Action | Opens |
|---------|--------|-------|
| `Ctrl+O` | Open Prompts | Prompt manager/templates |
| `Ctrl+G` | Open Logs | Log viewer modal |
| `Q` | Quit | Exit application |

---

## Panel-Specific Behaviors

### Browser Panel
- **Navigation:** `↑↓` move cursor, `Enter` select
- **New File:** `N` opens create dialog
- **Selection:** `S` mark start, `E` mark end
- **Context:** `L` add to context

### Chat Panel
- **Scrolling:** `↑↓` scroll, `PgUp/PgDn` page
- **Input:** `Ctrl+I` focus input, `Enter` send
- **Background:** `Ctrl+A` show debug logs

### Editor Tab (File)
- **Edit:** Navigate with vim keys (in vim mode)
- **Save:** `Ctrl+S` saves to backend
- **Close:** Tab close button or `:q` in vim

### Preview Panel
- **Scroll:** `↑↓` line scroll, `PgUp/PgDn` page scroll
- **Select:** `Enter` to select highlighted file

---

## Input Dialog Shortcuts

When dialog is open (e.g., Create File):

| Binding | Action |
|---------|--------|
| `Enter` | Confirm/Submit |
| `Esc` | Cancel/Close |
| `Tab` | Focus next field |
| `Shift+Tab` | Focus previous field |

---

## Status Bar

Bottom of screen shows:
- **Current focus area** (Browser, Chat, etc.)
- **Mode indicator** (for vim editor)
- **Spinner** when AI processing
- **Available keybindings** for current context

---

## Tips & Tricks

1. **Quick File Workflow:**
   - `Ctrl+B` → navigate → `Enter` → edit → `Ctrl+S` → save

2. **Multi-File Context:**
   - `Ctrl+B` → `S` → navigate → `E` → `L` → adds all files to chat

3. **AI Background:**
   - `Ctrl+A` shows reasoning traces and LLM calls

4. **Shell Integration:**
   - `Ctrl+X` jump to shell → run commands → `Ctrl+C` back to chat

5. **Efficient Navigation:**
   - Use `Ctrl+X` shortcuts instead of `Tab` for faster panel switching

---

## Future Enhancements

- [ ] Customizable keybindings via config
- [ ] Binding profiles (vi, emacs, default)
- [ ] Macro support for common workflows
- [ ] Mouse support (click to focus panels)

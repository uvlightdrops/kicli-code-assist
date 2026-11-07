---
title: Editor Navigation & Access Workflow
project: kicli-code-assist
scope: frontend-tui
purpose: Document how to reach and open the editor from different TUI panels
created: 2026-11-07 23
updated: 2026-11-07 23
update_reason: Initial documentation of editor access workflows
status: active
relations:
  - target: README.md
    type: parent
  - target: KEYBINDINGS.md
    type: reference
semantic_blocks:
  - workflow-browser-to-editor
  - workflow-preview-to-editor
  - workflow-new-file
  - editor-features
  - focus-switching
---

# Editor Navigation & Access [editor-navigation]

## Browser → Editor Workflow [workflow-browser-to-editor]

**Goal:** Open file from FileTree for editing

### Steps

1. **Focus Browser Panel**
   - Press `Ctrl+B` to jump to Browser
   - Or press `Tab` repeatedly to cycle to Browser

2. **Navigate to File**
   - Use `↑` / `↓` to select file/folder
   - Press `Enter` to:
     - **Folder:** Descend into directory
     - **File:** Open in editor tab

3. **Editor Opens**
   - New tab created in LeftPanel (FileEditorPane)
   - Tab automatically focused
   - File content loaded with syntax highlighting
   - Status bar shows: "📝 {filename}"

### Result
```
FileTree                LeftPanel                  RightPanel
┌──────────┐            ┌──────────┐               ┌──────────┐
│ 📁 src   │            │ 📂 Browser │ │ 📄 main.py* │ Agent Tabs
│ 📄 main  │  --Enter→  │ ─────────── │ │ ✏ NORMAL   │
│ 📄 utils │            │            │ │            │
└──────────┘            └──────────────┘               └──────────┘
```

---

## Preview → Editor Workflow [workflow-preview-to-editor]

**Goal:** Open preview file directly into editor for full editing

### Steps

1. **Focus Preview Panel**
   - Press `Ctrl+F` to jump to Preview
   - Preview shows file content with line numbers

2. **Optional: Select Lines**
   - Press `S` on start line (mark start)
   - Navigate to end line
   - Press `E` to mark end (range marked with `*`)

3. **Open in Editor**
   - Press `Enter` on preview
   - File opens in LeftPanel editor tab
   - **Note:** Preview becomes frozen (🔒 FROZEN indicator)

4. **Switch Back to Preview**
   - Press `Ctrl+F` to return to frozen preview
   - Press `Ctrl+B` to return to browser

### Result
```
Preview (shows file read-only)    LeftPanel (full editor)
┌──────────────────────┐          ┌──────────────────────┐
│ main.py              │          │ 📄 main.py*          │
│─────────────────────│          │ ✏ INSERT            │
│  1 def hello():      │          │ def hello():         │
│* 2 print("hi")   ←──┤--Enter→  │ print("hi")     ←─┐  │
│* 3 hello()          │          │ hello()           │  │
│ 🔒 FROZEN           │          │ (editable, cursor)  │
└──────────────────────┘          └──────────────────────┘
```

---

## Create New File Workflow [workflow-new-file]

**Goal:** Create and open new file directly in editor

### Steps

1. **Navigate to Target Directory**
   - Press `Ctrl+B` (focus Browser)
   - Use `↑` / `↓` to select directory
   - Press `Enter` to descend into folder

2. **Create New File**
   - Press `N` to open "Create File" dialog
   - Enter relative path: `src/newfile.py`
   - Press `Enter` to create

3. **Result**
   - File created on backend
   - FileTree refreshes
   - New file opens in editor tab
   - Status: "✅ File created: src/newfile.py"

4. **Edit & Save**
   - Type code in editor
   - Press `Ctrl+S` to save to backend
   - Status: "💾 Saved: newfile.py"

---

## Current Editor Features [editor-features]

### File Management
| Action | Binding | Result |
|--------|---------|--------|
| New File | `N` | Open create dialog |
| Save | `Ctrl+S` | Save via backend API |
| Discard | Button in editor | Reload from disk |
| Close | Tab close button | Remove tab |

### Editing
| Mode | Keys | Behavior |
|------|------|----------|
| NORMAL | vim keys (hjkl, etc) | Navigation |
| INSERT | `i` or `a` | Type text |
| VISUAL | `v` | Select text |
| COMMAND | `:` | vim commands (`:w`, `:q`, etc) |

### Status Indicators
```
📝 main.py*     ◆ NORMAL
   filename     mode icon + name
   * = dirty
```

---

## Tab Navigation [focus-switching]

### Switch Between Tabs

**Option 1: Via Keyboard**
- `Ctrl+B` → Browser tab
- Click other tabs with Tab key
- Editor automatically has focus when tab opens

**Option 2: Via Mouse (future)**
- Click on tab name to switch

**Option 3: Via Action Keys**
- `Ctrl+B` Browser
- `Ctrl+F` Preview
- `Ctrl+C` Chat
- `Ctrl+I` Input

---

## Open Issues & Improvements

### Current Limitations
1. **No "Open in Editor" from Preview** - Currently uses PreviewEnter message
   - ✅ Works but freezes preview (might be confusing)
   - Could add visual feedback showing editor is now active

2. **File Browser Focus After Save**
   - When file is saved, focus stays in editor
   - Could jump back to browser to continue browsing

3. **No Direct File Search**
   - Have to scroll manually through tree
   - Could add Ctrl+F file search dialog

4. **Tab Close Confirmation**
   - No prompt for unsaved changes (auto-save handles this)
   - Could add warning dialog

### Potential Enhancements
- [ ] Add "Open in Editor" button/action to Preview
- [ ] Add breadcrumb navigation in editor header (show path)
- [ ] Add file diff view (before/after changes)
- [ ] Add file search/jump to line (`:` in vim)
- [ ] Add split view (editor + preview side-by-side)
- [ ] Persist editor tab state across sessions
- [ ] Add undo/redo for file operations

---

## Architecture Notes

### Message Flow
```
FileTree
  └─ on_select_cursor() 
     └─ load file content
        └─ create_editor_tab()
           └─ FileEditorPane widget created
           └─ Tab added to LeftPanel
           └─ Editor focused

Preview
  └─ on_action_enter()
     └─ post_message(PreviewEnter)
        └─ on_preview_pane_preview_enter()
           └─ create_editor_tab()
              └─ Editor focused
              └─ Preview frozen
```

### Key Classes
- **SelectableFileList** (`file_browser.py`): File navigation, open files
- **PreviewPane** (`preview_pane.py`): Read-only preview, open in editor
- **FileEditorPane** (`file_editor.py`): Full vim-like editor with save
- **LeftPanel** (`left_panel.py`): Tab container, editor tab management
- **CodeAssistantApp** (`app.py`): Message routing, editor dialog handling

---

## Usage Summary

| Starting Point | Action | Destination |
|---|---|---|
| FileTree | `↑↓ Enter` | Editor (new tab) |
| Preview | `↑↓ Page Enter` | Editor (new tab, preview frozen) |
| Browser | `N` | New File Dialog → Editor |
| Editor | `Ctrl+S` | Save to Backend |
| Editor | `Ctrl+B` | Switch to FileTree |

---
title: Multi-File Generation UI
project: kicli-code-assist
scope: frontend-tui
purpose: Design and implementation of tabbed file editor for multi-file code generation
created: 2026-11-18 06
updated: 2026-11-18 06
update_reason: Initial design documentation for Phase I3 multi-file generation
status: active
relations:
  - target: ../frontend-tui/README.md
    type: parent
    reason: TUI documentation index
  - target: ./PHASE_I3_UI_IMPROVEMENTS.md
    type: reference
    reason: Phase I3 UI enhancements
semantic_blocks: [ui-design, flow-diagram, components, file-status-icons, file-tree-integration, user-interactions, examples]
---

# Multi-File Generation UI Design

## Overview [ui-design]

```yaml
block-meta:
  updated: 2026-11-18 06
  status: active
```

When users request **multi-file code generation**, the system now presents files in a **tabbed editor pane** rather than a modal dialog. This aligns with standard IDE behavior and enables seamless multi-file workflows.

### Previous Approach (Removed)
- ❌ "Save all" modal overlay
- ❌ Non-standard UX (not like IDEs)
- ❌ Unclear file organization
- ❌ Required manual decision: save or cancel

### New Approach ✅
- ✅ Tabbed editor pane (like VS Code, PyCharm, etc.)
- ✅ Automatic file placement by agent (correct directory structure)
- ✅ Visual status indicators (new, changed, saved)
- ✅ Automatic file tree expansion + highlighting
- ✅ File-by-file or all-at-once viewing

---

## Flow Diagram [flow-diagram]

```
User Request
     ↓
Agent Generates Code
     ↓
CodeGenerationPanel receives code blocks
     ↓
├─ For each file:
│  ├─ Create Tab in TabedEditorPane
│  ├─ Show: Filename | Path | Content
│  ├─ Mark Status: 🆕 (new) or ⚡ (changed)
│  └─ Store file metadata
│
├─ User Reviews Files (can flip through tabs)
│
└─ Agent Saves Files
   ├─ Files written to correct directories
   ├─ Update Tab Icons: ⏳ → 💾
   ├─ Expand FileTree to show new files
   ├─ Highlight in FileTree (green for new, orange for modified)
   └─ Chat shows: "✅ Saved 5 files"
```

---

## UI Components [components]

```yaml
block-meta:
  updated: 2026-11-18 06
  status: active
  components:
    - TabedEditorPane (new)
    - CodeGenerationPanel (modified)
    - FileTree (modified)
```

### 1. TabedEditorPane (Replaces PreviewPane)

**Location:** `kicli_code_assist/ui/panels/tabbed_editor_pane.py`

**Responsibility:**
- Manage multiple file tabs
- Display one file at a time
- Track file status
- Handle keyboard/mouse navigation

**Structure:**

```
┌─────────────────────────────────────────┐
│ [✓ main.py] [⚡ config.yml] [💾 utils.py] │
├─────────────────────────────────────────┤
│                                         │
│  main.py (/src/main.py)                │
│  ─────────────────────────────          │
│                                         │
│   1 | import os                         │
│   2 | from pathlib import Path          │
│   3 |                                   │
│   4 | def main():                       │
│   5 |     print("Hello")                │
│                                         │
│                                         │
└─────────────────────────────────────────┘
```

**Keyboard Shortcuts:**
- `Tab` / `Shift+Tab` — Next/Previous file
- `Ctrl+Right` / `Ctrl+Left` — Next/Previous file
- `Ctrl+G` — Goto line number
- `Page Up` / `Page Down` — Scroll content
- `↑↓` — Navigate lines (when not in editor mode)

**Mouse:**
- Click tab header to switch files
- Scroll wheel to scroll content

---

## File Status Icons [file-status-icons]

```yaml
block-meta:
  updated: 2026-11-18 06
  status: active
  icons:
    - new: "🆕 or ✨"
    - changed: "⚡"
    - saved: "💾"
    - saving: "⏳"
    - error: "❌"
```

| Icon | Meaning | Color | When |
|------|---------|-------|------|
| 🆕 | New file | Green | Doesn't exist in project yet |
| ⚡ | Modified | Orange | File exists but content differs |
| 💾 | Saved | Blue | Successfully written to disk |
| ⏳ | Saving | Yellow | In progress (< 1 sec) |
| ❌ | Error | Red | Failed to save (permissions, path issue) |

**Tab Example:**
```
[🆕 auth.py] [⚡ config.yml] [💾 main.py]
```

---

## File Tree Integration [file-tree-integration]

```yaml
block-meta:
  updated: 2026-11-18 06
  status: active
```

After files are saved:

1. **Auto-Expand Directories**
   - Walk up the generated file paths
   - Expand all ancestor directories in FileTree
   - Example: If `src/auth/handlers.py` is new:
     ```
     src/              ← expand
       auth/           ← expand
         handlers.py   ← new file (green)
     ```

2. **Highlight New/Modified Files**
   - New files: **Green text** in FileTree
   - Modified files: **Orange text** in FileTree
   - Duration: 10 seconds, then fade to normal

3. **Example Visual:**
   ```
   📁 Project
   ├─ 📁 src            (expanded)
   │  ├─ 📁 auth        (expanded, orange border = contains changes)
   │  │  ├─ 🟢 handlers.py (NEW)
   │  │  ├─ 🟠 models.py (MODIFIED)
   │  │  └─ routes.py
   │  ├─ main.py
   │  └─ config.py
   ├─ 📁 tests          (collapsed)
   └─ 📁 docs
   ```

---

## User Interaction Flow [user-interactions]

```yaml
block-meta:
  updated: 2026-11-18 06
  status: active
```

### Scenario 1: Review and Accept Generation

```
1. User: "Generate a FastAPI app with auth"
   ↓
2. Agent generates:
   - main.py
   - auth/models.py
   - auth/routes.py
   - config.yml
   
3. TUI shows tabs:
   [🆕 main.py] [🆕 models.py] [🆕 routes.py] [🆕 config.yml]
   
4. User reviews (presses Tab to flip through files)
   
5. Agent auto-saves to correct directories
   - Saves to: src/main.py, src/auth/models.py, etc.
   
6. Tabs update:
   [💾 main.py] [💾 models.py] [💾 routes.py] [💾 config.yml]
   
7. FileTree auto-expands and highlights:
   📁 src (expanded)
   ├─ 🟢 main.py (NEW)
   ├─ 📁 auth (expanded)
   │  ├─ 🟢 models.py (NEW)
   │  └─ 🟢 routes.py (NEW)
   └─ 🟢 config.yml (NEW)
   
8. Chat shows:
   "✅ Saved 4 files to src/"
```

### Scenario 2: Modify Existing Files

```
1. User: "Add logging to main.py"
   
2. Agent modifies main.py:
   - Tab shows: [⚡ main.py] (orange = changed)
   
3. User can still use Tab to review other unchanged files
   
4. Agent saves changes:
   - Tab updates: [💾 main.py]
   - FileTree highlights: 🟠 main.py (orange, 10s animation)
   
5. User can then continue working
```

---

## Implementation Details [components-impl]

### TabedEditorPane Methods

```python
class TabedEditorPane(Static):
    """Multi-file editor with tabs."""
    
    def add_file_tab(
        self,
        filepath: str,
        content: str,
        status: str = "new"
    ) -> None:
        """Add a file tab.
        
        Args:
            filepath: Full or relative path
            content: File content
            status: "new" | "changed" | "saved" | "saving" | "error"
        """
        pass
    
    def mark_file_status(self, filepath: str, status: str) -> None:
        """Update file status icon.
        
        Called when agent saves file.
        """
        pass
    
    def get_active_file(self) -> Optional[Tuple[str, str]]:
        """Get currently displayed file."""
        return (filepath, content)
    
    def save_all_files(self) -> Dict[str, bool]:
        """Persist all files. Called by agent."""
        return {filepath: success, ...}
```

### CodeGenerationPanel Changes

```python
class CodeGenerationPanel(Static):
    
    def on_code_generated(self, code_blocks: List[CodeBlock]) -> None:
        """When agent generates code blocks."""
        for block in code_blocks:
            filepath = block.filepath
            content = block.content
            
            # Add to tabbed editor instead of modal
            self.tabbed_editor.add_file_tab(
                filepath=filepath,
                content=content,
                status="new"  # or "changed"
            )
    
    def on_files_saved(self, results: Dict[str, bool]) -> None:
        """When agent saves files."""
        for filepath, success in results.items():
            status = "saved" if success else "error"
            self.tabbed_editor.mark_file_status(filepath, status)
        
        # Expand and highlight in FileTree
        self._expand_and_highlight_tree(results.keys())
```

---

## Examples [examples]

```yaml
block-meta:
  updated: 2026-11-18 06
  status: active
```

### Example 1: Python Project Structure

**User Request:**
```
"Create a FastAPI project with:
- Main app in src/main.py
- Database models in src/db/models.py
- API routes in src/api/routes.py
- Config file"
```

**TUI Result:**

```
Tabs:
[🆕 main.py] [🆕 models.py] [🆕 routes.py] [🆕 config.yml]

After Save:
[💾 main.py] [💾 models.py] [💾 routes.py] [💾 config.yml]

FileTree:
📁 Project/
├─ 📁 src/ (expanded)
│  ├─ 🟢 main.py (NEW)
│  ├─ 📁 db/ (expanded)
│  │  └─ 🟢 models.py (NEW)
│  ├─ 📁 api/ (expanded)
│  │  └─ 🟢 routes.py (NEW)
│  └─ 🟢 config.yml (NEW)
├─ 📁 tests/
└─ README.md
```

### Example 2: Web Project

**User Request:**
```
"Generate a React component library with:
- Button component
- Modal component
- Utils file"
```

**Result:**

```
Tabs:
[🆕 Button.tsx] [🆕 Modal.tsx] [🆕 utils.ts]

FileTree:
📁 Project/
├─ 📁 src/ (expanded)
│  ├─ 📁 components/ (expanded)
│  │  ├─ 🟢 Button.tsx (NEW)
│  │  └─ 🟢 Modal.tsx (NEW)
│  └─ 🟢 utils.ts (NEW)
└─ package.json
```

---

## Why This Approach [rationale]

| Aspect | Before (Modal) | After (Tabs) |
|--------|----------------|--------------|
| **Familiarity** | Custom (not like IDEs) | Like VS Code, PyCharm |
| **Multi-file** | One choice: Save All or Cancel | Browse each, automatic save |
| **File Organization** | Unclear where files go | Agent knows correct paths |
| **User Control** | Binary (all or nothing) | Fine-grained (review before save) |
| **Visual Feedback** | Modal popup (intrusive) | Integrated in editor pane |
| **Scalability** | Breaks with many files | Works with 10+ files easily |

---

## Migration Notes

**What was removed:**
- ❌ `CodePreviewModal` class (no longer used)
- ❌ "Save all" button in modal

**What replaces it:**
- ✅ `TabedEditorPane` class (new)
- ✅ Automatic file saving by agent
- ✅ Tab-based navigation in existing editor pane

**Breaking Changes:**
- None for end-users (UI is better)
- API change: `PreviewPane.set_content()` → `TabedEditorPane.add_file_tab()`

---

## Future Enhancements

- Diff viewer (compare file before/after)
- Syntax highlighting per language
- Code folding
- Search/replace across files
- File drag-drop to reorder tabs

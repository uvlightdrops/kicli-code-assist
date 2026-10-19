# TUI File Browser

## Overview

The kicli-code-assist TUI now includes an integrated **file browser** that lets you browse and preview files in your project directory without leaving the terminal UI.

## Features

✅ **File Navigation**
- Browse directories with arrow keys
- Navigate parent directories
- Quick jump to home directory

✅ **File Preview**
- Preview selected files (first 15 lines)
- Shows file size in bytes/KB
- Syntax highlighting ready (future)

✅ **File Selection**
- Load files for code generation
- Mark current file for operations
- View file metadata

✅ **Smart Icons**
- 📁 Directories
- 🐍 Python files
- 📜 JavaScript
- 📘 TypeScript
- 📋 JSON
- ⚙️ YAML
- 📄 Text files
- 🔧 Shell scripts
- And more...

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `↑` / `↓` | Move up/down in file list |
| `Enter` | Open directory or send chat message |
| `L` | Load selected file |
| `H` | Go to home directory |
| `R` | Refresh file list |
| `?` | Show help |
| `Ctrl+C` | Quit |

## Layout

The TUI now uses a split-screen layout:

```
═══════════════════════════════════════════════════════════════
              KI Code Assistant
═══════════════════════════════════════════════════════════════
│                     │                                       │
│  📂 File Browser    │                                       │
│  (12 lines)         │  💬 Chat History                      │
│                     │  (8 lines)                            │
├─────────────────────┤                                       │
│  👁️ File Preview    │                                       │
│  (10 lines)         │  ⌨️ Input                             │
│                     │  (3 lines)                            │
│                     │                                       │
═══════════════════════════════════════════════════════════════
[↑↓] Navigate [ENTER] Open/Send [L] Load [H] Home [R] Refresh 
[?] Help [CTRL+C] Quit
═══════════════════════════════════════════════════════════════
```

## Usage Examples

### 1. Browse Project Files

```
Start: kicli-assist tui

→ 📁 ../
  📁 .git/
  📁 src/
  📁 tests/
  🐍 setup.py
  📄 README.md

Action: Press ↓ to navigate
```

### 2. Preview a File

```
Navigate to: src/main.py
→ 🐍 src/main.py (2.5KB)

Preview shows:
  def main():
      print("Hello world")
      ...
```

### 3. Load File for Code Generation

```
1. Navigate to file: 📄 example.txt
2. Press 'L' to load
3. Message: "📄 Loaded: example.txt"
4. Ask AI: "Refactor this file"
```

### 4. Navigate Directories

```
Current: /home/user/project
1. Press ↓ to highlight: 📁 src/
2. Press Enter to open
3. Now browsing: /home/user/project/src/
4. Press Enter on .. to go back
```

## Python API

### FileBrowser Class

```python
from kicli_code_assist.ui.file_browser import FileBrowser

# Create browser
browser = FileBrowser("/path/to/directory")

# Navigate
browser.select_next()     # Move down
browser.select_prev()     # Move up
browser.enter_selected()  # Enter directory

# Get selected item
item = browser.get_selected()
print(item.name)          # File/directory name
print(item.is_dir)        # Boolean
print(item.path)          # Full path

# Get preview
preview = browser.get_file_content_preview(max_lines=20)

# Get tree view
tree = browser.get_tree_view(max_items=30)
print(tree)

# Navigation helpers
browser.go_home()                    # Go to home directory
browser.go_to_path("/some/path")    # Jump to path
browser.refresh()                   # Refresh file list
```

## Features (Current)

✅ **Navigation**
- Browse files and directories
- Parent directory link (..)
- Smart sorting (dirs first, then files)

✅ **Preview**
- Text file preview (15 lines)
- File size display
- UTF-8 encoding support

✅ **Integration**
- Part of main TUI
- Keyboard shortcuts
- Real-time updates

## Future Enhancements

- [ ] Syntax highlighting in preview
- [ ] Search/filter files
- [ ] Bookmark/favorite directories
- [ ] File operations (copy, rename, delete)
- [ ] Git status indicator
- [ ] File thumbnails for images
- [ ] Fuzzy find with Ctrl+F
- [ ] Multiple file selection

## Technical Details

### File Sorting

Files are sorted with:
1. Directories first (alphabetical)
2. Then files (alphabetical)
3. Parent directory (..) at top

### Hidden Files

By default, hidden files (starting with `.`) are not shown to reduce clutter.

### Performance

Large directories (1000+ files) are handled efficiently:
- Non-blocking file listing
- Lazy loading of previews
- Limited display (max 30 items visible)

### Error Handling

- Permission denied: Silently skipped
- Unreadable files: Show "[Unable to read file]"
- Invalid paths: Fallback to current directory

## Keyboard Binding Details

| Mode | Binding | Action |
|------|---------|--------|
| Always | `Ctrl+C` | Quit application |
| File browser | `↑` / `↓` | Navigate files |
| File browser | `Enter` | Open directory |
| File browser | `L` | Load selected file |
| File browser | `H` | Go home |
| File browser | `R` | Refresh |
| Chat | `Enter` | Send message |
| Changes | `Tab` / `Shift+Tab` | Next/prev change |
| Changes | `Y` / `N` | Accept/reject |
| Help | `?` | Show help text |

## Examples

### Example 1: Load Python File

```bash
$ kicli-assist tui

[Navigate to: src/models.py]
Press L

Chat: "Can you add type hints to this file?"
[AI refactors the file]
```

### Example 2: Review Multiple Files

```bash
[Navigate to: src/views.py]
Review...

[Navigate to: src/controllers.py]
Press L
Chat: "Compare these two files"
```

### Example 3: Find and Load Config

```bash
Press H    (go to home)
[Navigate through directories]
Press Enter on: config/
[Navigate to: config.yaml]
Press L
Chat: "Validate this YAML configuration"
```

## Tips & Tricks

1. **Quick Navigation:** Press `H` to jump to home, then navigate from there
2. **Refresh:** Press `R` if files were modified externally
3. **Preview:** Hover over files to see size and type
4. **Keyboard Only:** All operations work without mouse
5. **Parent Dir:** Always shows `..` at top for quick navigation

## Troubleshooting

**Q: Files not showing up**
- A: Press `R` to refresh, or check file permissions

**Q: Preview shows garbage**
- A: File is binary or encoded differently, reload as needed

**Q: Slow with large directories**
- A: Use `.gitignore` to hide irrelevant files, then refresh

**Q: Can't navigate to a directory**
- A: Check permissions: `ls -la /path/to/dir`

## API Stability

The FileBrowser API is stable and ready for production use.

Version: 1.0 ✅
Status: Production Ready

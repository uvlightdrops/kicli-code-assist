# Tabbed File Editor System for kicli-code-assist

## Overview

The **Tabbed File Editor System** is a modern, multi-file display interface for the kicli-code-assist TUI. It elegantly replaces the previous single-file `PreviewPane` with a tab-based editor that supports:

- **Multi-file display** with intuitive tab navigation
- **Status tracking** for file lifecycle (new, modified, saved, saving, error)
- **Syntax highlighting** for 15+ programming languages
- **Keyboard-friendly** navigation (Ctrl+Left/Right, arrows, Page Up/Down)
- **Read-only display** mode (ideal for AI-generated code review)
- **Automatic save** with error handling and directory creation

## Architecture

### Component Overview

```
TabbedEditorPane (Static) [Main Container]
├── TabBar [Tab Headers with Icons]
├── FileContentViewer [Content Display with Syntax Highlighting]
│   └── Lines with Line Numbers
└── Status Bar [Tab Info and File Stats]
```

### File Structure

```
kicli_code_assist/ui/panels/
├── tabbed_editor_pane.py           # Main implementation (~550 LOC)
├── TABBED_EDITOR_INTEGRATION.md    # Integration guide
└── __init__.py                     # Module exports

tests/
└── test_tabbed_editor_pane.py      # Unit tests (69 tests, all passing)
```

## Usage Guide

### Basic Setup

```python
from kicli_code_assist.ui.panels.tabbed_editor_pane import TabbedEditorPane

# Create the editor
editor = TabbedEditorPane(id="file_editor")

# Add a file tab
editor.add_file_tab(
    filepath="/project/src/app.py",
    content="def main():\n    print('Hello')",
    status="new"  # or "modified", "saved", "saving", "error"
)
```

### Tab Management

```python
# Navigate tabs
editor.action_next_tab()      # Ctrl+Right or Tab
editor.action_prev_tab()      # Ctrl+Left or Shift+Tab

# Update file status
editor.mark_file_status("/path/to/file.py", "modified")

# Get active file
filepath, content = editor.get_active_file()
# Returns: ("/path/to/file.py", "file content") or None

# Remove a tab
editor.remove_file_tab("/path/to/file.py")
```

### File Operations

```python
# Save all files to disk
results = editor.save_all_files()

for filepath, success in results.items():
    if success:
        print(f"✓ Saved {filepath}")
    else:
        print(f"✗ Failed to save {filepath}")
        # Status is automatically set to "error"
```

### Content Navigation

```python
# Move cursor within content
editor.action_cursor_up()
editor.action_cursor_down()
editor.action_page_up()
editor.action_page_down()

# Note: Keyboard bindings work when editor has focus
# Press Ctrl+F to focus editor from main app
```

## Status Indicators

Each tab displays a status icon indicating file state:

| Icon | Status | Meaning | Auto-Triggered |
|------|--------|---------|-----------------|
| 🆕 | NEW | File is newly generated | `add_file_tab(..., "new")` |
| ⚡ | MODIFIED | File exists but differs | `add_file_tab(..., "modified")` |
| 💾 | SAVED | File saved to disk | `save_all_files()` |
| ⏳ | SAVING | Save in progress | During `save_all_files()` |
| ❌ | ERROR | Save failed | On exception during save |

## Integration with CodeGenerationPanel

```python
# In CodeGenerationPanel
from kicli_code_assist.ui.panels.tabbed_editor_pane import TabbedEditorPane

class CodeGenerationPanel(Static):
    def __init__(self):
        super().__init__()
        self.tabbed_editor = TabbedEditorPane()
    
    def on_code_generated(self, files: List[CodeFile]):
        """Called when agent generates code."""
        for code_file in files:
            status = "new" if code_file.is_new else "modified"
            self.tabbed_editor.add_file_tab(
                filepath=code_file.path,
                content=code_file.content,
                status=status
            )
    
    def save_generated_code(self):
        """Save all generated files."""
        results = self.tabbed_editor.save_all_files()
        
        # Update UI with results
        for filepath, success in results.items():
            if success:
                self.app.notify(f"✓ Saved {Path(filepath).name}")
            else:
                self.app.notify(f"✗ Failed to save {Path(filepath).name}")
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Tab Navigation** |
| `Ctrl+Left` | Go to previous tab |
| `Ctrl+Right` | Go to next tab |
| `Shift+Tab` | Go to previous tab (alternative) |
| `Tab` | Go to next tab (alternative) |
| **Content Navigation** |
| `↑` / `↓` | Move cursor up/down |
| `Page Up` | Scroll up one page |
| `Page Down` | Scroll down one page |
| `Ctrl+G` | Go to line (placeholder) |
| **Focus Management** |
| `Ctrl+F` | Focus editor (from main app) |

## Language Support

Automatic syntax highlighting for:

| Language | Extension | Lexer |
|----------|-----------|-------|
| Python | `.py` | python |
| JavaScript | `.js` | javascript |
| TypeScript | `.ts`, `.tsx` | typescript, tsx |
| JSX | `.jsx` | jsx |
| YAML | `.yaml`, `.yml` | yaml |
| JSON | `.json` | json |
| HTML | `.html` | html |
| CSS | `.css` | css |
| SQL | `.sql` | sql |
| Bash | `.sh` | bash |
| Go | `.go` | go |
| Rust | `.rs` | rust |
| Java | `.java` | java |
| C++ | `.cpp` | cpp |
| C | `.c` | c |
| Markdown | `.md` | markdown |

## Configuration

### CSS Customization

Modify `DEFAULT_CSS` in `TabbedEditorPane` class:

```python
DEFAULT_CSS = """
TabbedEditorPane {
    width: 1fr;
    height: 1fr;
    background: $surface;
    border: solid $primary;
}

TabbedEditorPane .tab-button.active {
    background: $primary;
    color: $text;
    bold: true;
}
"""
```

### Display Settings

```python
# Adjust page size for scrolling
viewer = FileContentViewer(tab)
viewer.page_size = 30  # Lines per page (default: 20)
```

## Testing

Run comprehensive test suite:

```bash
cd /home/flow/dev_flow/kicli-code-assist
source .venv/bin/activate
pytest tests/test_tabbed_editor_pane.py -v

# Run specific test class
pytest tests/test_tabbed_editor_pane.py::TestTabbedEditorPaneLogic -v

# Run with coverage
pytest tests/test_tabbed_editor_pane.py --cov=kicli_code_assist.ui.panels
```

### Test Coverage

- **69 test cases** covering all core functionality
- **File I/O tests** with temporary directories
- **Language detection** for 15+ file types
- **Tab navigation** and state management
- **Status tracking** and error handling
- **Save operations** with permission handling

## Performance

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Add tab | O(1) | Dict insertion |
| Remove tab | O(1) | Dict deletion, O(n) if switching active tab |
| Tab navigation | O(1) | Index lookup |
| Update status | O(1) | Dict lookup |
| Save all | O(n) | File I/O for each file |
| Render content | O(m) | m = visible lines (typically 20-30) |

## Common Patterns

### Pattern 1: Display Generated Code

```python
def handle_code_generation(response: str):
    """Parse response and display generated files."""
    code_blocks = extract_code_blocks(response)
    
    for filepath, content, language in code_blocks:
        editor.add_file_tab(filepath, content, "new")
    
    # Notify user
    print(f"Generated {len(code_blocks)} files")
```

### Pattern 2: Review and Save

```python
def review_and_save(files_to_review):
    """Let user review files before saving."""
    for filepath, content in files_to_review:
        editor.add_file_tab(filepath, content, "new")
    
    # User reviews in UI...
    
    # Save when ready
    results = editor.save_all_files()
    return results
```

### Pattern 3: Multi-Step Generation

```python
def iterative_generation():
    """Generate code in multiple steps."""
    
    # Step 1: Create structure
    editor.add_file_tab("src/__init__.py", "", "new")
    editor.add_file_tab("src/main.py", "def main(): pass", "new")
    
    # Step 2: Refine code
    editor.mark_file_status("src/main.py", "modified")
    new_content = refine_code("src/main.py")
    # Update content by removing and re-adding
    editor.remove_file_tab("src/main.py")
    editor.add_file_tab("src/main.py", new_content, "modified")
    
    # Step 3: Save all
    results = editor.save_all_files()
```

## Troubleshooting

### Tab Not Visible
- Ensure widget is mounted and has focus
- Check if ID is correct: `editor.query_one("#file-editor", TabbedEditorPane)`

### Syntax Highlighting Not Working
- Verify file extension is in extension map (see Language Support table)
- Rich library may not support your language - file type falls back to plain text

### Save Fails
- Check file permissions on target directory
- Verify parent directories can be created (`Path.mkdir(parents=True)`)
- Status will be set to "error" with exception details

### UI Not Updating
- Call `editor._refresh_ui()` after manual state changes (rarely needed)
- Textual handles most UI updates automatically

## Future Enhancements

Potential improvements for future versions:

1. **Line Selection**
   - Mark start/end lines
   - Copy selected content to clipboard
   - Append selection to chat context

2. **Diff View**
   - Compare against disk version
   - Show diff before saving

3. **Search and Replace**
   - Find text in current file
   - Find and replace across all files

4. **Tab Management**
   - Close button on tabs
   - Right-click context menu
   - Reorder tabs by dragging

5. **Content Editing**
   - Basic editing (read-write mode)
   - Undo/redo support
   - Dirty indicator

6. **File Tree Integration**
   - Auto-expand new directories
   - Highlight generated files
   - Right-click file browser integration

## Contributing

When extending TabbedEditorPane:

1. **Keep it focused** - Maintain single responsibility
2. **Add tests** - Every feature should have unit tests
3. **Document** - Update docstrings and this README
4. **Backward compatible** - Don't break existing API
5. **Performance** - Profile for large file counts

## License

Part of kicli-code-assist project. See project LICENSE.

## References

- **Textual Framework**: https://textual.textualize.io/
- **Rich Library**: https://rich.readthedocs.io/
- **Implementation**: `kicli_code_assist/ui/panels/tabbed_editor_pane.py`
- **Tests**: `tests/test_tabbed_editor_pane.py`
- **Integration Guide**: `kicli_code_assist/ui/panels/TABBED_EDITOR_INTEGRATION.md`

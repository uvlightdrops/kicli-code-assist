"""
Tabbed File Editor System - Integration Guide

This module provides a tabbed editor interface for displaying multiple generated/modified
files in the kicli-code-assist TUI. It replaces the previous PreviewPane with a tab-based
system that elegantly handles multi-file code generation.

## Quick Start

### Basic Usage

```python
from kicli_code_assist.ui.panels.tabbed_editor_pane import TabbedEditorPane

# Create the editor pane
editor = TabbedEditorPane()

# Add a generated file tab
editor.add_file_tab(
    filepath="/path/to/app.py",
    content="def hello():\n    return 'world'",
    status="new"  # Status: "new", "modified", "saved", "saving", "error"
)

# Navigate between tabs
editor.action_next_tab()      # Ctrl+Right
editor.action_prev_tab()      # Ctrl+Left

# Update file status
editor.mark_file_status("/path/to/app.py", "modified")

# Get active file content
filepath, content = editor.get_active_file()

# Save all files to disk
results = editor.save_all_files()
for filepath, success in results.items():
    print(f"{filepath}: {'✓' if success else '❌'}")
```

## Status Icons

- 🆕 NEW: File is new (didn't exist before)
- ⚡ MODIFIED: File exists but content differs
- 💾 SAVED: File is saved to disk
- ⏳ SAVING: Save operation in progress
- ❌ ERROR: Error occurred during save

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Ctrl+Left | Previous Tab |
| Ctrl+Right | Next Tab |
| Shift+Tab | Previous Tab |
| Tab | Next Tab |
| ↑/↓ | Navigate file content |
| Page Up/Down | Scroll through file |
| Ctrl+G | Go to line (placeholder) |

## Integration with CodeGenerationPanel

The CodeGenerationPanel can emit code blocks that automatically create tabs:

```python
# In CodeGenerationPanel message handler
code_blocks = extract_code_blocks(response)
for filepath, content, language in code_blocks:
    self.tabbed_editor.add_file_tab(filepath, content, status="new")
    self.tabbed_editor.mark_file_in_tree(filepath, "new")  # Optional tree integration
```

## Features

### Tab Navigation
- Click on tab headers to switch
- Use Ctrl+Left/Right or Tab/Shift+Tab for keyboard navigation
- Automatic wrap-around at list edges

### Status Tracking
- Each tab shows current file status via icon
- Status updates during save operations
- Error status for failed saves with error details

### Content Display
- Syntax highlighting based on file extension
- Line numbers for all files
- Read-only display (suitable for AI-generated code)
- Smooth scrolling with arrow keys and Page Up/Down

### File Operations
- Save all files at once to disk
- Automatic directory creation for nested paths
- Error handling with status feedback

### Language Support (Syntax Highlighting)
Automatic detection for: Python, JavaScript, TypeScript, JSX, TSX, YAML, JSON,
HTML, CSS, SQL, Bash, Go, Rust, Java, C++, C, Markdown

## Implementation Notes

### Architecture
- `TabbedEditorPane`: Main container widget inheriting from Static
- `FileContentViewer`: Displays single file with syntax highlighting
- `TabBar`: Renders tab headers with status icons
- `FileTab`: Data class representing tab state
- `FileStatus`: Enum for status indicators

### CSS Styling
All styling is defined in DEFAULT_CSS blocks - no external stylesheets required.

### Performance
- O(1) tab switching
- O(1) status updates
- O(n) save operations (where n = number of files)
- Lazy rendering (only active tab is fully rendered)

### Testing
Comprehensive unit tests in `tests/test_tabbed_editor_pane.py`:
- 69 test cases covering all core functionality
- File I/O testing with temporary directories
- Language detection for 15+ file types
- Tab navigation and state management

## Future Enhancements

Possible improvements:
1. Line selection for context extraction
2. Diff view against disk versions
3. Undo/redo for content changes
4. Search/replace within files
5. File renaming/deletion
6. Close button on tabs
7. Unsaved indicator
"""

# Example integration in CodeGenerationPanel
def example_integrate_with_code_gen_panel():
    """Example of how to integrate TabbedEditorPane with CodeGenerationPanel."""
    from kicli_code_assist.ui.panels.tabbed_editor_pane import TabbedEditorPane
    
    # Initialize
    tabbed_editor = TabbedEditorPane()
    
    # Simulate receiving code generation response
    generated_files = [
        ("src/main.py", "def main():\n    pass", "new"),
        ("tests/test_main.py", "import pytest\n\ndef test_main(): pass", "new"),
        ("README.md", "# My Project\n\nDemo app", "new"),
    ]
    
    # Add tabs for each generated file
    for filepath, content, status in generated_files:
        tabbed_editor.add_file_tab(filepath, content, status)
    
    # User reviews and saves
    results = tabbed_editor.save_all_files()
    
    # Show summary
    saved = sum(1 for success in results.values() if success)
    print(f"Saved {saved}/{len(results)} files")
    
    # Mark status after successful saves
    for filepath, success in results.items():
        status = "saved" if success else "error"
        tabbed_editor.mark_file_status(filepath, status)


if __name__ == "__main__":
    example_integrate_with_code_gen_panel()

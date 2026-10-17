# Vi/Vim Editor Quick Guide

## Modes

The editor has 4 modes, shown in the header with **BRIGHT BOLD COLORED ICONS**:

| Mode | Icon | Color | Entry | Exit |
|------|------|-------|-------|------|
| **NORMAL** | ◆ | Cyan | Esc | - |
| **INSERT** | ✏ | Green | i/a/o/O | Esc |
| **VISUAL** | ▢ | Yellow | v/V | Esc |
| **COMMAND** | : | Magenta | : | Esc |

**Mode Indicator**: Located in editor header top-right. Very visible with bright colors on dark background. Updates instantly as you type.

## Movement (NORMAL mode)

| Key | Action |
|-----|--------|
| `h` `j` `k` `l` | Left, Down, Up, Right |
| `w` | Move to next word start |
| `b` | Move to previous word start |
| `e` | Move to end of word |
| `0` | Move to line start |
| `$` | Move to line end |
| `gg` | Go to file start |
| `G` | Go to file end |
| `nG` | Go to line n |
| `:n` | Go to line n (command mode) |
| `/pattern` | Search pattern |
| `n` | Next search result |
| `N` | Previous search result |

## Editing (INSERT mode)

Press `i`, `a`, `o`, or `O` to enter INSERT mode:

| Key | Action |
|-----|--------|
| `i` | Insert before cursor |
| `a` | Insert after cursor |
| `o` | Open new line below |
| `O` | Open new line above |
| Type | Normal text input |
| `Esc` | Return to NORMAL mode |

## Operators (NORMAL mode)

Operators work with counts and motions:

| Operator | Action |
|----------|--------|
| `d` | Delete (dw, dd, dG) |
| `y` | Copy/Yank (yw, yy) |
| `c` | Change (cw, cc, cG) |
| `>` | Indent |
| `<` | Dedent |

Examples:
- `dw` - Delete word
- `dd` - Delete line
- `3dd` - Delete 3 lines
- `2w` - Move 2 words
- `cG` - Change to end of file
- `yy` - Copy line

## Visual Mode

Press `v` in NORMAL mode to select text:

| Key | Action |
|-----|--------|
| `v` | Character selection |
| `V` | Line selection |
| `hjkl` | Extend selection |
| `d` | Delete selection |
| `y` | Copy selection |
| `c` | Delete and insert |

## Commands (COMMAND mode)

Press `:` in NORMAL mode to enter COMMAND mode:

| Command | Action |
|---------|--------|
| `:q` | Quit editor (auto-save if dirty) |
| `:q!` | Quit without saving |
| `:nnn` | Go to line nnn |
| `:set number` | Show line numbers |

**Note**: `:w` (save) is **not needed**! The editor auto-saves after 2 seconds of inactivity, like VS Code.

## Auto-Save

The editor automatically saves your changes:
- You edit code → file marked as dirty
- Stop typing for 2 seconds → file auto-saves
- Notification shows: "💾 filename.py auto-saved"
- Dirty indicator (`*`) disappears

**Manual Save**: Click the 💾 Save button to save immediately.

## How It Works (Technical)

### Mode Indicator Updates
- **Event-Driven**: Uses VimTextArea.ModeChanged messages
- **Zero Lag**: Instant visual feedback
- **Bright Colors**: Cyan/Green/Yellow/Magenta on dark background for visibility
- **Icons**: Each mode has a distinctive icon for quick recognition

### Auto-Save vs :w
- **Old Way (:w)**: Press `:w` in NORMAL mode
- **New Way (Auto-Save)**: Edit, pause 2 seconds, done
- **Why Better**:
  - No mode switching required
  - No vim commands to remember  
  - Automatic background saves prevent data loss
  - Familiar to VS Code / modern editor users

## How It Works (Technical)

## Common Workflows

### Edit a file
1. Press Enter to open file in editor tab
2. Use vim motions to navigate
3. Press `i` to enter INSERT mode
4. Edit your code
5. Press `Esc` to return to NORMAL mode
6. Press `:w` to save

### Delete a line
1. In NORMAL mode, position cursor on line
2. Press `dd`

### Copy and paste
1. In NORMAL mode, select text with `v` or `V`
2. Press `y` to copy
3. Move cursor to new location
4. Press `p` to paste

### Find and replace
1. Press `/` to search
2. Type pattern and press Enter
3. Press `n` for next match
4. In NORMAL mode, press `c` to change

### Indent multiple lines
1. Select lines with `V`
2. Press `>` to indent (or `<` to dedent)

## Tips

- **Undo/Redo:** Not yet implemented (standard Vi doesn't have them either)
- **Marks:** Not yet implemented
- **Registers:** Not yet implemented
- **Status Bar:** Shows file path, dirty state, and mode
- **Line Numbers:** Can be enabled with `:set number`

## Status Indicator

The editor tab shows:
- `📝 filename.txt` - File being edited
- `📝 filename.txt*` - File has unsaved changes
- Mode indicator (NORMAL/INSERT/VISUAL/COMMAND) in top right

## Buttons

- **💾 Save** - Save file to disk (or `:w` in COMMAND mode)
- **↶ Discard** - Reload from disk, discard all changes
- **🤖 AI Suggestions** - Get AI suggestions for code (experimental)

---

For more vi/vim documentation, visit: https://www.vim.org/docs.php

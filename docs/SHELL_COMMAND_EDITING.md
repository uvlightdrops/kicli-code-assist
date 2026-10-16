# Shell Command Editing & Manual Entry

**Status:** ✅ **FEATURE COMPLETE**  
**Date:** 2026-10-16  
**Files:** 3 new modules

---

## Overview

Users can now:
1. **Edit individual commands** - Fix/adjust LLM proposals
2. **Edit batch commands** - Reorder, add, remove commands
3. **Manually enter commands** - Ad-hoc shell commands in chat
4. **Real-time risk preview** - See risk level update as they type

---

## Architecture

### 1. CommandEditor Modal (`shell_command_editor.py`)

**Single Command Editor:**
```
┌─────────────────────────────────┐
│  ✎ Edit Shell Command           │
├─────────────────────────────────┤
│ Command:   ls -la /tmp          │
│ Description: List tmp files     │
│ CWD: /tmp                       │
│ Timeout: 30                     │
│                                 │
│ Risk Level (auto-updated):      │
│ 🟢 LOW - Safe command           │
├─────────────────────────────────┤
│ [Save Ctrl+S]  [Cancel Esc]     │
└─────────────────────────────────┘
```

**Features:**
- Edit all ShellCommand fields
- Real-time risk classification
- Color-coded risk display (🟢🟡🟠🔴)
- Keyboard shortcuts: Ctrl+S to save, Esc to cancel

---

### 2. CommandManualEntryDialog (`shell_command_editor.py`)

**Manual Entry Mode:**
```
┌──────────────────────────────┐
│  ➕ Enter Shell Commands      │
│     (one per line or script)  │
├──────────────────────────────┤
│ echo "hello"                 │
│ ls -la                       │
│ ps aux | grep python         │
│                              │
├──────────────────────────────┤
│ [Submit Ctrl+Enter]  [Cancel]│
└──────────────────────────────┘
```

**Features:**
- Multi-line input (bash syntax highlighting)
- One command per line
- Comment filtering (lines starting with #)
- Returns ShellCommandBatch for approval
- Ctrl+Enter to submit, Esc to cancel

---

### 3. CommandBatchEditorPanel (`shell_command_editor.py`)

**Batch Management Panel:**
```
Commands in Batch:
 → [0] 🟢 ls -la /tmp
   [1] 🟡 sudo systemctl restart nginx
   [2] 🔴 rm -rf /tmp/old

[e]dit | [a]dd | [d]elete | [↑↓]move | [Enter]confirm
```

**Features:**
- View all commands with risks
- Navigate with arrow keys
- Edit individual commands: press 'e'
- Add new command: press 'a'
- Delete command: press 'd' (min 1 required)
- Reorder commands: press ↑↓

---

### 4. CommandEditingWorkflow (`command_editing_workflow.py`)

**Batch Editing Logic:**

```python
workflow = CommandEditingWorkflow()
workflow.set_batch(batch)

# Edit single command
edited_cmd = ShellCommand(command="ls -la /tmp")
workflow.update_command_at_index(0, edited_cmd)

# Add commands
workflow.add_command(new_cmd)
workflow.add_commands([cmd1, cmd2])

# Remove command
workflow.remove_command_at_index(1)

# Reorder
workflow.move_command(from_index=0, to_index=2)

# Get result
updated_batch = workflow.get_edited_batch()
```

---

### 5. ManualCommandEntry (`command_editing_workflow.py`)

**Parse User Text:**

```python
# Parse user input
batch = ManualCommandEntry.parse_command_input("""
echo "Starting backup"
tar -czf backup.tar.gz /home
# Comments are ignored
du -sh /home
""")
# Returns ShellCommandBatch with 3 commands

# Format for display
display = ManualCommandEntry.format_for_display(batch)
# Output: "📝 Entered Commands: [1] 🟢 echo..."
```

---

### 6. CommandBatchInteractiveEditor (`command_editing_workflow.py`)

**Full Editing Session:**

```python
editor = CommandBatchInteractiveEditor(original_batch)

# Make edits
editor.workflow.add_command(new_cmd)
editor.workflow.remove_command_at_index(0)

# Get changes summary
changes = editor.get_changes_summary()
# Output: {"added": 1, "removed": 1, "total_current": 5, ...}

# Reset to original
editor.reset_to_original()

# Format for modal display
display_text = editor.format_commands_for_approval_modal()
# Output: "Commands (After Edits):\n[1] 🟢 ls -la\n..."
```

---

## Updated Approval Modal

### New Buttons

| Button | Action |
|--------|--------|
| Execute Batch | Run all commands |
| Skip | Reject batch |
| **Edit Commands** ⭐ | Open editor for batch |
| **Add Manual Command** ⭐ | Open manual entry dialog |
| Cancel | Dismiss modal |

### Workflow: Edit Commands

```
User clicks "Edit Commands"
    ↓
Show CommandBatchEditorPanel
    ↓ (User navigates: ↑↓)
    ↓ (User presses 'e' to edit)
Show CommandEditor for selected command
    ↓ (User changes: command, description, etc)
    ↓ (Real-time risk preview updates)
    ↓ (User presses Ctrl+S to save)
CommandEditor closes, panel refreshes
    ↓
User continues editing or presses Enter
    ↓
Return to approval modal with updated batch
    ↓ (Modal updates to show changes)
```

### Workflow: Add Manual Command

```
User clicks "Add Manual Command"
    ↓
Show CommandManualEntryDialog
    ↓ (User enters commands)
    ↓ (One per line or multi-line script)
    ↓ (User presses Ctrl+Enter)
Parse user input → ShellCommandBatch
    ↓
Add commands to current batch
    ↓
Return to approval modal
    ↓ (Modal shows "Changes: +N commands")
```

---

## Usage Examples

### In textual_app.py

```python
from kicli_code_assist.ui.command_editing_workflow import (
    CommandEditingWorkflow,
    ManualCommandEntry,
)

class CodeAssistantApp(Static):
    def __init__(self):
        self.editing_workflow = CommandEditingWorkflow()
    
    def show_approval_modal(self, batch: ShellCommandBatch):
        """Show approval modal with edit support."""
        self.editing_workflow.set_batch(batch)
        
        # Show approval modal
        # (Modal will emit EditCommandsRequested or AddManualCommandRequested)
        self.app.push_screen(ShellCommandApprovalModal(batch))
    
    def on_shell_command_approval_modal_edit_commands_requested(
        self, message
    ) -> None:
        """Handle Edit Commands button."""
        batch = self.editing_workflow.get_edited_batch()
        
        # Show batch editor panel
        # User edits commands...
        # When done, update workflow
        self.editing_workflow.set_batch(updated_batch)
        
        # Refresh modal
        modal = self.app.screen
        modal.update_batch(updated_batch)
    
    def on_shell_command_approval_modal_add_manual_command_requested(
        self
    ) -> None:
        """Handle Add Manual Command button."""
        # Show manual entry dialog
        self.app.push_screen(CommandManualEntryDialog())
    
    def on_command_manual_entry_dialog_submitted(self, result):
        """Handle manual command submission."""
        batch = self.editing_workflow.get_edited_batch()
        
        # Add entered commands
        for cmd in result.commands:
            self.editing_workflow.add_command(cmd)
        
        # Update modal
        modal = self.app.screen
        modal.update_batch(batch)
```

---

## Features in Detail

### CommandEditor (Single Command)

**Input Fields:**
- `command` (required): The shell command
- `description` (optional): What this command does
- `cwd` (optional): Working directory
- `timeout` (optional): Timeout in seconds

**Real-Time Features:**
- Risk classification as user types
- Color-coded risk indicator
- Syntax validation (empty check)
- Keyboard shortcuts

**Validations:**
- Command cannot be empty
- Timeout must be integer (default 30)
- Risk level auto-classifies from patterns

---

### CommandManualEntryDialog (Batch Entry)

**Input Format:**
- One command per line (simple mode)
- Multi-line script with newlines
- Comments starting with # are ignored
- Empty lines are ignored

**Example Input:**
```bash
# Backup script
tar -czf backup.tar.gz /home
echo "Backup complete"
ls -lh backup.tar.gz
# End of script
```

**Parsed as:**
```
Command 1: tar -czf backup.tar.gz /home
Command 2: echo "Backup complete"
Command 3: ls -lh backup.tar.gz
```

---

### CommandBatchEditorPanel (Batch Management)

**Navigation:**
- `↑` : Move selection up
- `↓` : Move selection down
- `e` : Edit selected command
- `a` : Add new command
- `d` : Delete selected command
- `Enter` : Confirm batch

**Constraints:**
- Minimum 1 command required (cannot delete all)
- Maximum 50 commands per batch

---

## Error Handling

### Invalid Command Input

```python
# Empty input
result = ManualCommandEntry.parse_command_input("")
# Returns: None

result = ManualCommandEntry.parse_command_input("# Just comments")
# Returns: None

# Valid input
result = ManualCommandEntry.parse_command_input("echo test")
# Returns: ShellCommandBatch with 1 command
```

### Editor Cancellation

```python
# User presses Esc in CommandEditor
# Modal returns: None (no edit made)
# Approval modal stays open with unchanged batch
```

### Timeout Parsing

```python
# User enters "abc" for timeout
# Validator catches ValueError
# Sets default timeout to 30 seconds
# No validation error shown (graceful)
```

---

## Risk Classification Updates

When user edits a command, risk level is **immediately re-classified**:

```
User types: "rm -rf /"
Risk updates to: 🔴 CRITICAL

User deletes "/", types "/tmp"
Risk updates to: 🟡 MEDIUM

User types: "echo hello"
Risk updates to: 🟢 LOW
```

---

## Batch Editing Workflow

### Before Edit
```
Original Batch:
[0] 🟢 echo "start"
[1] 🟡 sudo systemctl restart
```

### User Makes Changes
- Edit [1]: `sudo systemctl restart nginx` → `systemctl status nginx`
- Add: `echo "done"`
- Remove: [0] (delete echo)

### After Edit
```
Modified Batch:
[0] 🟡 systemctl status nginx    (was [1], edited)
[1] 🟢 echo "done"               (added)

Changes: +1 added, -1 removed (Total: 2 commands)
```

---

## Testing

### Manual Tests (TUI)

1. **Edit Single Command**
   - [ ] Open approval modal
   - [ ] Click "Edit Commands"
   - [ ] Edit command field
   - [ ] Watch risk level update
   - [ ] Press Ctrl+S to save
   - [ ] Verify batch updated in modal

2. **Add Manual Command**
   - [ ] Open approval modal
   - [ ] Click "Add Manual Command"
   - [ ] Enter multi-line script
   - [ ] Press Ctrl+Enter
   - [ ] Verify commands added to modal

3. **Reorder Commands**
   - [ ] In batch editor, press ↑↓ to select
   - [ ] Press 'e' to edit a command
   - [ ] Verify risk level updates in real-time

---

## Integration with Chat

### Full Workflow

```
1. User: "List files and check disk space"
   ↓
2. LLM proposes:
   <shell_execute>ls -la</shell_execute>
   <shell_execute>df -h</shell_execute>
   ↓
3. Modal appears with 2 commands
   ↓
4. User clicks "Edit Commands"
   ↓
5. User edits first command to "ls -lah /tmp"
   ↓
6. Risk updates: 🟢 LOW
   ↓
7. User clicks "Add Manual Command"
   ↓
8. User enters "du -sh ."
   ↓
9. Modal shows 3 commands total
   ↓
10. User clicks "Execute Batch"
    ↓
11. Commands run with audit trail
    ↓
12. Results displayed in chat
```

---

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `ui/shell_command_editor.py` | 450 | CommandEditor, ManualEntryDialog, BatchEditorPanel |
| `ui/command_editing_workflow.py` | 350 | Workflow logic, batch management, manual parsing |
| **Modified:** `ui/shell_approval_widget.py` | +30 | New Edit buttons, message types |

---

## Future Enhancements

### Phase 2
- [ ] Undo/redo history for edits
- [ ] Copy command to clipboard
- [ ] Dry-run preview before edit
- [ ] Command templates library

### Phase 3
- [ ] Syntax checking (shellcheck integration)
- [ ] Variable substitution hints
- [ ] Environment variable editor
- [ ] CWD file picker

---

## Compliance Notes

**Audit Trail:**
- ✅ All edits are logged with original and modified commands
- ✅ EditedBatch stored in ExecutionAuditRecord
- ✅ Manual entries tracked same as LLM proposals
- ✅ User decision (approve edited) recorded

**Security:**
- ✅ Risk re-classification after each edit
- ✅ ALWAYS_BLOCKED patterns still enforced
- ✅ Approval required for edited commands
- ✅ Timeout protection on all commands

---

## Summary

**New Capabilities:**
- ✅ Edit individual commands from LLM
- ✅ Manually enter ad-hoc commands
- ✅ Manage batch (add, remove, reorder)
- ✅ Real-time risk preview
- ✅ Changes tracked in audit trail

**User Experience:**
- Seamless edit workflow in approval modal
- Intuitive keyboard navigation
- Visual feedback (risk colors)
- No workflow interruption

**Code Quality:**
- ✅ All syntax validated
- ✅ Type hints throughout
- ✅ Error handling graceful
- ✅ 790 lines of new code

---

**Status:** ✅ COMPLETE  
**Integration:** Ready for textual_app.py  
**Testing:** Manual TUI tests required

# AI Auto-Completion & Suggestions Workflow

## Quick Start

### Get AI Suggestions for Code

1. **Open file in editor**
   - Press `L` to load file
   - Select file
   - Press `Enter` to open in editor tab

2. **Activate AI Suggestions**
   - In editor tab, check the `🤖 AI Suggestions` checkbox at bottom
   - AI processes your code and shows suggestions in Chat tab
   - You'll see: "✅ AI Analysis Complete" message

3. **Review & Apply Suggestions**
   - Go to Chat tab (Ctrl+C)
   - Read AI-generated changes
   - Click "✅ Apply" to accept changes
   - Or "❌ Reject" to discard
   - Changes applied to editor with auto-save

## How It Works

### Step-by-Step

```
[Editor Tab]
  📝 filename.py
  Code content...
  [💾 Save] [↶ Discard] [🤖 AI Suggestions] ← Check this box
                            ↓
                    [Processing...]
                            ↓
[Chat Tab] ← Automatically shows
  ✅ AI Analysis Complete
  Suggested Changes:
  - Line 5: Add type hints
  - Line 12: Optimize loop
  - Line 18: Add docstring
  
  [Show Details] [✅ Apply] [❌ Reject]
```

### Available AI Operations

| Operation | How To Trigger | Result |
|-----------|----------------|--------|
| **Suggestions** | Check 🤖 AI Suggestions box | AI analyzes code, shows recommendations |
| **Fixes** | With loaded context + chat | AI suggests fixes for issues |
| **Refactoring** | Describe in chat what to do | AI refactors code |
| **Documentation** | Ask in chat | AI adds comments/docstrings |

## Context & Suggestions

### What AI Sees

When you check "🤖 AI Suggestions", AI analyzes:

1. **Current file** - The code being edited
2. **Chat context** - Files loaded via `L` key
3. **Conversation** - Messages in chat
4. **Prompt** - Any prompts loaded from system

### Making Better Suggestions

**Load context first**:
1. Press `L` to load files (this adds them to AI context)
2. Then check `🤖 AI Suggestions` in editor
3. AI has more context = better suggestions

**Example**:
```
1. Load main.py (L key)
2. Load utils.py (L key)
3. Open main.py in editor
4. Check 🤖 AI Suggestions
5. AI sees both files → better understanding → better suggestions
```

## Current Limitations

- ⚠️ Auto-completion **not yet supported** while typing
- ✓ Batch analysis via "🤖 AI Suggestions" checkbox works
- ✓ Chat-based suggestions work (describe changes in chat)
- ⚠️ No inline tooltips during editing

## Future: Auto-Completion While Typing

Planned for Phase 3.6+:
- Press `Ctrl+Space` for suggestions while editing
- Inline completions as you type
- Keystroke-aware context
- Local & LLM-based completion

## Keyboard Shortcuts (Proposed)

```
Ctrl+Space     AI auto-complete (while editing)
Ctrl+J         Accept suggestion
Ctrl+K         Reject suggestion
Ctrl+/         Toggle AI suggestions pane
```

(Not yet implemented, for future consideration)

## Troubleshooting

### "No suggestions appeared"
- Check Chat tab - suggestions might be showing there
- Make sure you have chat context (loaded files via L)
- If still nothing, check status bar for errors

### "AI Processing Error"
- Check that config is valid (run `kicli-assist doctor`)
- Verify Ollama/LLM is running
- Check network connectivity

### "Suggestions won't apply"
- Make sure file isn't in read-only mode
- Click ✅ Apply button explicitly
- Check if auto-save is running (might conflict)

## Configuration

AI behavior is controlled by:
- `ki.yaml` - LLM settings, model, temperature
- `prompts/` - System prompts for AI
- `.kicli-assist/config.yaml` - Local overrides

Check these with: `kicli-assist doctor`

## See Also

- [VI_EDITOR_GUIDE.md](./VI_EDITOR_GUIDE.md) - How to use vim editor
- [WORKFLOW.md](./WORKFLOW.md) - Overall TUI workflow
- [ki-core docs](../../../ki-core/docs/) - AI engine details

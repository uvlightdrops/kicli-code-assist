# Chat Integration: Files + Comments + KI

## Quick Start

### Workflow 1: Simple Chat with Loaded File (EMPFOHLEN)

```
1. kicli-assist tui

2. Navigate zu wichtiger File:
   ↓↓↓ [navigate down]
   L   [load file]
   Chat: "📄 Loaded: chat_session.py"

3. Frage im Input-Bereich schreiben:
   "Explain the load_project_context method
    and suggest improvements"

4. ENTER → KI antwortet mit:
   ✅ Verständnis der Methode
   ✅ Verständnis des ganzen Projekts
   ✅ Konkrete Verbesserungsvorschläge
```

### Workflow 2: Full Project Context + Specific File

```
1. kicli-assist tui

2. Projekt-Kontext laden:
   Ctrl+L → "✅ 📊 27 files, 104.1 KB loaded"

3. Spezifische File laden:
   ↓↓↓ [navigate down]
   L   [load file]
   Chat: "📄 Loaded: project_context.py"

4. Frage stellen:
   "How does the ProjectContextManager integrate
    with ChatSession? Should we optimize it?"

5. ENTER → KI bekommt ALLES:
   • Project-kompletter Kontext
   • Deine geladene File
   • Deine Frage
   • LLM kann informierte Antwort geben!
```

### Workflow 3: Comment + Question

```
1. File laden: L
   Chat: "📄 Loaded: chat_session.py"

2. Kontext im Chat geben:
   "I want to improve message formatting
    for better token handling. This is in chat_session.py"

3. Frage stellen:
   "How can we reduce token usage?
    Should we split long messages?"

4. ENTER → KI response mit vollem Kontext
```

## Available Commands

### Navigation (File Browser)
```
↑ / ↓           → Navigate files
Enter           → Open directory
L               → Load file (shows in preview)
H               → Home directory
R               → Refresh list
```

### Chat Control
```
[Type in input area]
Enter           → Send message to LLM
Ctrl+L          → Load project context
?               → Show help
Ctrl+C          → Quit
```

## What Happens When You Send a Message

1. **User Input**: "How does this work?"
2. **UI adds to chat**: "You: How does this work?"
3. **System actions**:
   - Adds to ChatSession history
   - Generates system prompt with:
     • Project structure (if loaded)
     • Key files and dependencies
     • Your question
   - Sends to LLM provider
   - Streams response back
4. **Response appears**: "Assistant: [LLM response]"
5. **Chat history updated**: Both messages in session

## Implementation Details

### What the LLM Sees

When you send a message, the LLM receives:

```
[SYSTEM PROMPT]
You are a helpful code assistant...

# PROJECT CONTEXT

You are assisting with the following project:

# Project: kicli-code-assist
**Language:** python
**Files:** 27
**Size:** 104.1 KB

## Dependencies
- python:pyproject.toml

## Structure
kicli-code-assist/
  README.md
  pyproject.toml
  kicli_code_assist/
    __init__.py
    cli.py
    chat_session.py     ← Loaded file
    ...

## Key Files Content
[README content]
[Config file content]
[Your loaded file content]
...

---

[USER MESSAGE]
Explain the load_project_context method
and suggest improvements
```

### File Loading Behavior

When you load a file with `L`:
1. File content shown in preview panel
2. "📄 Loaded: filename" message in chat
3. File name tracked in `state.current_file`
4. When you send a message, the LLM knows:
   - Which file you loaded
   - The full project context
   - The preview you're looking at

### Message Flow

```
User types "Explain this"
          ↓
Input buffer gets text
          ↓
Enter key pressed
          ↓
_send_chat_message()
          ↓
Add to ChatSession
          ↓
Get API messages (includes system prompt)
          ↓
Send to LLM provider
          ↓
Stream response back
          ↓
Display in chat
          ↓
Add to ChatSession history
          ↓
Ready for next message
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate files |
| `Enter` | Open dir or send message |
| `L` | Load selected file |
| `H` | Go to home directory |
| `R` | Refresh file list |
| `Ctrl+L` | Load project context |
| `?` | Show help |
| `Ctrl+C` | Quit |

## Tips & Tricks

### Tip 1: Load Context First
```
Ctrl+L → Load project context
This makes LLM aware of entire project structure
Helps with architecture questions
```

### Tip 2: Show the File You're Asking About
```
Load file with L
Type question mentioning the file
LLM sees both the code and your question
More accurate responses!
```

### Tip 3: Multi-File Questions
```
1. Load file 1 (L)
   "Loaded: auth.py"

2. Mention in message: "and also look at user.py"
   Chat: "How do auth.py and user.py interact?"

3. LLM can reason about both files
```

### Tip 4: Context First, Then Deep Dive
```
1. Ctrl+L → Get project overview
2. L → Load specific file
3. Ask detailed question about that file
4. LLM has context from step 1, specific code from step 2
```

## Troubleshooting

### No Response from LLM

**Problem**: Message sent but no response appears

**Solutions**:
1. Check provider is running (Ollama, OpenAI, etc.)
2. Check ki.yaml configuration
3. Check network connectivity
4. Increase timeout if slow provider

### LLM Response is Irrelevant

**Problem**: LLM doesn't understand your question

**Solutions**:
1. Load project context: `Ctrl+L`
2. Load the specific file: `L`
3. Be more specific in your question
4. Mention file names explicitly

### Message Takes Too Long

**Problem**: LLM response is slow

**Solutions**:
1. Reduce project context with selective loading
2. Use faster provider (local Ollama vs cloud OpenAI)
3. Ask shorter questions
4. Check token limit in ki.yaml

## Next Steps

Features to implement:
- [ ] Multi-file selection
- [ ] File annotations/comments panel
- [ ] Save conversation to file
- [ ] Syntax highlighting in file preview
- [ ] Code diff viewer for suggestions
- [ ] Context customization UI

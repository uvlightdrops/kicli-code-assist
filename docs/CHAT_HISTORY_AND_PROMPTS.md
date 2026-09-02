# Chat History & Session Management

## Overview

kicli-code-assist now supports persistent chat sessions with automatic save/restore functionality. Sessions are stored locally in `$HOME/dev_data/kicli-code-assist/chat_history/` and can be resumed at any time.

## Quick Start

### Starting a New Session
```bash
kicli-assist tui
```
Chat sessions auto-save. You can close and reopen the app.

### Viewing Available Sessions
```python
from kicli_code_assist.chat_history import ChatHistory

sessions = ChatHistory.list_sessions()
for session in sessions:
    print(f"{session['name']}: {session['message_count']} messages")
```

### Loading a Previous Session
```python
from kicli_code_assist.chat_session import ChatSession

session = ChatSession.load_session("my-chat-name")
print(session.history.get_messages())  # All previous messages
```

## Features

### 1. Automatic Persistence
- Every message is automatically saved to disk
- Sessions survive app crashes
- No manual saving required

### 2. Multiple Sessions
- Create unlimited independent chat sessions
- Switch between sessions
- Each has its own context and history

### 3. Session Management
```python
from kicli_code_assist.chat_history import ChatHistory

# List all sessions
sessions = ChatHistory.list_sessions()

# Load specific session
history = ChatHistory("my-session")

# Export session
markdown = ChatHistory.export_session("my-session", format="markdown")
json_data = ChatHistory.export_session("my-session", format="json")

# Clear a session
history.clear()
```

### 4. Export Options
Sessions can be exported to:
- **Markdown**: For sharing, documentation, blog posts
- **JSON**: For archiving, analysis, integration

Example:
```bash
# Export to Markdown
python3 -c "from kicli_code_assist.chat_history import ChatHistory; print(ChatHistory.export_session('debug-session', 'markdown'))" > debug.md

# Export to JSON
python3 -c "from kicli_code_assist.chat_history import ChatHistory; print(ChatHistory.export_session('debug-session', 'json'))" > debug.json
```

## LLM Roles & System Prompts

### Available Roles

kicli-code-assist comes with 5 pre-configured LLM roles:

#### 1. Code Assistant (Default)
Best for: Writing code, fixing bugs, implementing features
- Practical, solution-focused
- Code-first explanations
- Suggests best practices

#### 2. Architect
Best for: System design, refactoring, scaling decisions
- High-level thinking
- Trade-off analysis
- Long-term design perspective

#### 3. Debugger
Best for: Troubleshooting, root cause analysis, error investigation
- Systematic debugging approach
- Root cause identification
- Prevention strategies

#### 4. Reviewer
Best for: Code review, quality assessment, standards compliance
- Correctness and design evaluation
- Performance considerations
- Constructive feedback

#### 5. Explainer
Best for: Learning, documentation, understanding concepts
- Clear breakdowns of complex topics
- Multiple perspectives
- Analogies and examples

### Using Different Roles

#### In Python Code
```python
from kicli_code_assist.chat_session import ChatSession
from kicli_code_assist.prompts import PromptRole

# Create session with architect role
session = ChatSession(role=PromptRole.ARCHITECT)

# Change role
session.set_role(PromptRole.DEBUGGER)

# Get role-specific system prompt
prompt = session.get_system_prompt()
print(prompt)
```

#### In TUI
(Feature to be added) Toggle role with keyboard shortcut:
- `Ctrl+R`: Cycle through roles
- `Ctrl+P`: Show current role and system prompt

### System Prompt Structure

All system prompts include:

1. **Role Definition**: Clear explanation of LLM's purpose
2. **Communication Style**: Tone and approach
3. **Behavioral Rules**:
   - Accuracy & confidence standards
   - Response format expectations
   - Context awareness requirements
   - Error handling approach
   - Code quality standards
4. **Project Context** (optional): Project structure when loaded

Example:
```
You are a code assistant helping a developer write, debug, and improve code.

Your primary responsibilities:
- Provide working code examples with clear explanations
- Identify issues and suggest fixes with reasoning
...

## Core Behavioral Rules

1. **Accuracy & Confidence**
   - Always distinguish between certainty and speculation
   ...
```

## Prompt Templates

### Common Task Templates

For frequently needed tasks, use built-in prompt templates:

```python
from kicli_code_assist.prompts import PromptTemplates

# Refactoring request
prompt = PromptTemplates.refactor_request(
    code="def old_code(): pass",
    goals="Improve readability and performance",
    constraints="Must maintain API compatibility"
)

# Bug investigation
prompt = PromptTemplates.bug_report(
    error_message="ValueError: list index out of range",
    context="Processing user input from API",
    steps_to_reproduce="1. Send empty request\n2. See error"
)

# Architecture review
prompt = PromptTemplates.architecture_review(
    current_design="Monolithic service with database",
    concerns="Scalability with 1M+ users"
)

# Code review
prompt = PromptTemplates.code_review(
    code="new_implementation.py",
    context="Replaced legacy auth system"
)
```

## File Structure

```
$HOME/dev_data/kicli-code-assist/
  chat_history/
    default.json              # Default session
    debug-session.json        # Custom session
    feature-request.json      # Another session
```

Each session file contains:
```json
{
  "session_name": "debug-session",
  "created": 1693483200,
  "updated": 1693569600,
  "message_count": 24,
  "messages": [
    {
      "role": "user",
      "content": "How does auth work?",
      "timestamp": "2023-08-30T14:30:00",
      "metadata": {"context_included": true}
    },
    {
      "role": "assistant",
      "content": "...",
      "timestamp": "2023-08-30T14:30:15"
    }
  ]
}
```

## Best Practices

### Session Naming
Use descriptive names for easy identification:
- ✅ `debug-auth-issue`
- ✅ `refactor-api-layer`
- ✅ `feature-request-2023-09`
- ❌ `session1`
- ❌ `chat2`

### Role Selection
- Start with **Code Assistant** for general help
- Switch to **Architect** for design decisions
- Use **Debugger** for troubleshooting
- Use **Reviewer** for code quality checks
- Use **Explainer** for learning

### Context Usage
- Load project context for better answers
- Use specific sessions for different projects
- Export completed sessions for documentation

## Limitations & Future Features

### Current Limitations
- Maximum 100 messages per session (for context window limits)
- No built-in search across sessions
- Cannot merge sessions

### Planned Features (TODO)
- [ ] Session search and filtering
- [ ] Session merging
- [ ] Message editing/deletion
- [ ] Session tagging
- [ ] Auto-cleanup of old sessions
- [ ] Web UI for session browser
- [ ] Collaboration features (share sessions)

## Troubleshooting

### Sessions Not Loading
```bash
# Check session files exist
ls -la $HOME/dev_data/kicli-code-assist/chat_history/

# Check file permissions
chmod 644 $HOME/dev_data/kicli-code-assist/chat_history/*.json
```

### Session File Corrupted
```bash
# Restore from backup (manual)
# Or delete and start fresh:
rm $HOME/dev_data/kicli-code-assist/chat_history/corrupted-session.json
```

### Export Failed
```python
# Verify session exists
from kicli_code_assist.chat_history import ChatHistory
sessions = ChatHistory.list_sessions()
print(sessions)

# Try manual export
session = ChatHistory("your-session")
with open("export.json", "w") as f:
    f.write(session.export_session(session.session_name, "json"))
```

---
title: "Layer 1: IDE Capabilities with Raw Primitives"
project: kicli-code-assist
scope: backend
type: reference
status: active
created: 2026-11-06T10:28:00+01:00
updated: 2026-11-06T10:28:00+01:00
update_reason: Define what TUI + WebUI can do with Layer 1 primitives
cross_references:
  - README.md
  - ../layer-2-workflow-orchestration/AGENT_ROUTE_SPEC.md
---

# IDE Capabilities with Layer 1 Primitives

What the IDE (TUI + WebUI) can do with Raw LLM Layer.

## Core Capabilities

### 1. Query LLM for Analysis
- Send code snippets + context to OpenAI
- Get structured responses (observations, issues, solutions)
- Stream responses token-by-token for real-time display
- Cache results (same query = instant answer)

**From TUI:** User selects file → hits "Analyze" → LLM evaluates code in 2-5 seconds

### 2. Read & Filter Files Safely
- Load project files from disk (with `.gitignore` respect)
- Extract code context (surrounding 10 lines, function signatures, imports)
- **Filter secrets** before sending to LLM (no API keys, passwords, tokens in prompts)
- Handle large files (truncate gracefully, show "..." for preview)

**From TUI:** FileTree shows "README.md (1.2KB)" → click → loads file content → filtered & ready for analysis

### 3. Git Operations
- List modified files (since last commit)
- Show git diff for selected file
- Stage/unstage files (layer 2 feature, but uses Layer 1 primitives)
- Get commit history snippets

**From TUI:** "Show changes since commit" → runs `git diff` → displays in panel

### 4. Execute Terminal Commands (Safe)
- Run `ls`, `find`, `grep`, `wc` for project introspection
- Capture stdout/stderr
- Timeout protection (no hanging processes)
- Execute in project root (not user home)

**From TUI:** "Find all Python files" → runs `find . -name "*.py"` → shows results

### 5. Stream Long Responses
- LLM responses chunk by chunk (for responsiveness)
- Cancel mid-stream (user hits Escape)
- Display chunks in real-time as they arrive
- Count tokens (for quota tracking)

**From TUI:** Analyze button clicked → "🔍 Analyzing..." → chunks appear as they stream

### 6. Error Handling & Recovery
- Network timeouts → retry with backoff
- LLM rate limit → queue request
- Secret detection → warn user, don't send
- File access denied → surface error clearly

**From TUI:** Missing file → error panel shows "File not found: src/config.py (permission denied)"

---

## Implementation Checklist (for TUI Phase I1)

- [ ] OpenAI client: `AsyncOpenAIClient` from ki_core (handles async + retry)
- [ ] Secret filtering: `SensitiveDataFilter` from ki_core (blocks API keys before sending)
- [ ] File loading: Use `Path` + gitignore parser (kicli_code_assist/parsing/)
- [ ] Streaming: Token counter + cancel support (kicli_code_assist/streaming.py)
- [ ] Git commands: Use `subprocess` with timeout + cwd=project_root
- [ ] Error types: Use `ki_core.errors.structured` (Error, ValidationError, LLMError, RecoveryHints)

---

## Example: TUI "Analyze File" Flow

```
User: Clicks "Analyze" on src/main.py
  ↓
Layer 1 Primitives:
  1. Read file: load src/main.py (1.2KB)
  2. Filter: SensitiveDataFilter checks for secrets (✓ clean)
  3. Context: git diff to show recent changes
  4. Query: AsyncOpenAIClient.achat_stream("Analyze this file...")
  5. Stream: Token-by-token to UI panel
  ↓
User sees: Real-time chunks (observations, issues, solutions)
```

## What Layer 1 Does NOT Do

- ❌ Combine responses from multiple agents (that's Layer 2)
- ❌ Route workflows based on intent (that's Layer 2)
- ❌ Remember session history (that's Layer 2)
- ❌ Decide which agent to call (that's Layer 3)

Layer 1 is dumb & fast. Layer 2 makes it smart.

---

**For TUI integration:** Use Layer 2 `/api/agent/route` endpoint (wraps all Layer 1 primitives). See [AGENT_ROUTE_SPEC.md](../layer-2-workflow-orchestration/AGENT_ROUTE_SPEC.md).

# Phase 4: Architecture Overview

**Covers**: Async LLM Processing, Security, AI Workflow Integration  
**Status**: ✅ Complete  
**Components**: 15 new modules across ki-core + kicli-code-assist

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TUI Application Layer                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ CodeAssistantApp (ui/app.py)                                │   │
│  │ - AI workflow orchestration                                 │   │
│  │ - Message routing & state management                        │   │
│  └───────┬──────────────────────────────────┬──────────────────┘   │
│          │                                  │                       │
│  ┌──────▼──────┐              ┌────────────▼────────────┐          │
│  │ FileEditor  │              │ ApprovalModal (4.3)     │          │
│  │ - AI check  │──AI Request──│ - Hunk visualization    │          │
│  │ - Dirty trk │              │ - Line approval UI      │          │
│  └─────────────┘              └────────┬────────────────┘          │
│                                        │                            │
└────────────────────────────────────────┼────────────────────────────┘
                                         │
                    ┌────────────────────┴──────────────────┐
                    │                                       │
              ┌─────▼──────────┐           ┌──────────────▼──────┐
              │ AIWorkflowMgr  │           │ ApprovalWorkflow   │
              │ (ai_workflow)  │           │ (approval_workflow)│
              │ - LLM call     │           │ - CodeHunk         │
              │ - Response     │           │ - HunkStatus       │
              │   parsing      │           │ - Approval logic   │
              │ - Apply changes│           └────────────────────┘
              └────────┬───────┘
                       │
    ┌──────────────────┴──────────────────┐
    │ AsyncLLMIntegration (4.1)           │
    │ - achat() non-blocking calls        │
    │ - ProviderChain with fallback       │
    │ - Spinner feedback                  │
    └────────┬──────────────────────────┬─┘
             │                          │
   ┌─────────▼──────────┐    ┌──────────▼─────────────┐
   │ ki-core Adapters   │    │ Response Processing    │
   │                    │    │                        │
   │ AsyncOpenAIClient  │    │ ResponseParser (4.2)   │
   │ ProviderChain      │    │ - Multi-part parsing   │
   │ - retry logic      │    │ - TEXT/CODE/SHELL      │
   │ - exponential      │    │                        │
   │   backoff          │    │ EncryptionManager (4.2)│
   │                    │    │ - Fernet symmetric     │
   │ SensitiveDataFilter│    │ - Master key mgmt      │
   │ (4.1) - 10+ regex  │    │                        │
   │                    │    │ Structured Errors      │
   │ Error classes      │    │ - RecoveryHints        │
   │ - RecoveryHints    │    │ - User guidance        │
   └────────────────────┘    └────────────────────────┘
          ▲                             ▲
          └─────────────┬───────────────┘
                        │
                External LLM APIs
        (OpenAI, Anthropic, Ollama, etc)
```

---

## Component Details

### Phase 4.1: Async & Security Layer

#### AsyncOpenAIClient (`ki_core/adapters/openai_async.py`)
**Purpose**: Non-blocking LLM API calls

- Uses `asyncio.wait_for()` with configurable timeout
- Raises `LLMTimeoutError`, `LLMAuthError`, `LLMRateLimitError`
- Implements `achat()` and `achat_stream()` for async operations
- Fallback: All existing sync adapters can use `run_in_executor()`

**Key Design**:
```python
async def achat(prompt, messages, model):
    # asyncio.wait_for with timeout
    # Raises LLMTimeoutError if timeout
    # Returns parsed response string
```

#### ProviderChain (`ki_core/adapters/provider_chain.py`)
**Purpose**: Automatic fallback between multiple LLM providers

- Tries OpenAI → Anthropic → Ollama (configurable order)
- Exponential backoff retry: 2^attempt seconds (1s, 2s, 4s, ...)
- Circuit breaker: Stop after N consecutive failures per provider
- Tracks per-provider statistics for debugging

**Key Design**:
```python
async def achat(prompt, messages):
    for provider in self.providers:
        try:
            result = await provider.achat(...)
            return result
        except LLMTimeoutError:
            # Retry with backoff
            await asyncio.sleep(2 ** attempt)
        except LLMAuthError:
            # Don't retry auth errors
            break
```

#### SensitiveDataFilter (`ki_core/security/filters.py`)
**Purpose**: Detect and redact secrets before external LLM calls

- **10+ Regex Patterns**:
  - OpenAI keys: `sk-proj-*`, `sk-*`
  - Anthropic: `sk-ant-*`
  - AWS: `AKIA*`, `aws_secret_access_key`
  - Database URLs: `postgres://user:pass@host`
  - Private keys: `-----BEGIN PRIVATE KEY-----`
  - Slack tokens: `xoxb-*`, `xoxp-*`
  
- **RedactionLog**: Audit trail of what was redacted
- **Safe for LLM**: All secrets replaced with `[REDACTED]`

**Key Design**:
```python
def filter(text: str) -> str:
    for pattern in PATTERNS:
        text = re.sub(pattern, "[REDACTED]", text)
    return text
```

#### Structured Errors (`ki_core/errors/structured.py`)
**Purpose**: User-friendly error messages with recovery suggestions

- **Error Hierarchy**:
  - `KICoreError` (base)
    - `LLMTimeoutError` (with retry hint)
    - `LLMAuthError` (with config hint)
    - `LLMRateLimitError` (with backoff hint)
    - `LLMProviderError` (generic LLM error)
    - `AllProvidersFailedError` (all fallbacks exhausted)

- **RecoveryHint**: Machine-parseable action suggestions
  - `action`: "retry", "upgrade-model", "configure-api-key"
  - `description`: Human-readable explanation
  - `command`: Optional Python/shell to execute

**Key Design**:
```python
@dataclass
class RecoveryHint:
    action: str
    description: str
    command: Optional[str] = None

class LLMTimeoutError(KICoreError):
    def __init__(self, message: str):
        super().__init__(
            message,
            recovery_hints=[
                RecoveryHint("retry", "Retry with increased timeout"),
                RecoveryHint("fallback", "Try different LLM provider"),
            ]
        )
```

### Phase 4.2: Robustness Layer

#### EncryptionManager (`ki_core/security/encryption.py`)
**Purpose**: Encrypt sensitive data (chat history) at rest

- **Algorithm**: Fernet (symmetric encryption, AES-128-CBC + HMAC)
- **Key Source** (in order):
  1. Environment: `KI_MASTER_KEY`
  2. File: `~/.ki/master.key` (0o600 permissions)
  3. Auto-generate if missing

- **Features**:
  - Recursive dict/list encryption with `__encrypted__` markers
  - Metadata tracking (timestamp, version)
  - Base64 encoding for text storage

**Key Design**:
```python
class EncryptionManager:
    def encrypt(self, data: dict) -> bytes:
        # Recursively encrypt dicts/lists
        json_str = json.dumps(data)
        return cipher.encrypt(json_str.encode())
    
    def decrypt(self, encrypted: bytes) -> dict:
        decrypted_str = cipher.decrypt(encrypted).decode()
        return json.loads(decrypted_str)
```

#### ResponseParser (`ki_core/core/response_parser.py`)
**Purpose**: Parse LLM responses into structured parts

- **ResponsePartType**: TEXT, CODE, SHELL
- **Detects**:
  - Markdown code blocks with language tags
  - Shell commands (bash, sh, zsh, shell)
  - Plain text sections

- **Regex Strategy**:
  - MULTILINE + DOTALL flags for cross-line matching
  - Language detection for shell vs code classification
  - Handles multiple code blocks per response

**Key Design**:
```python
class ResponseParser:
    def parse(self, response: str) -> List[ResponsePart]:
        # Extract ```lang code_block ```
        # Classify language as SHELL or CODE
        # Return parts in order
```

### Phase 4.3: AI Workflow Layer

#### ApprovalWorkflow (`kicli_code_assist/approval_workflow.py`)
**Purpose**: Track and manage approval status of AI changes

- **CodeHunk**: Single file modification (lines X-Y)
  - `lines`: List of `LineModification` objects
  - `status`: PENDING / APPROVED / REJECTED / PARTIAL
  - Methods: `approve_all()`, `reject_line(n)`, `get_approval_percentage()`

- **LineModification**: Single line change
  - `line_number`, `original_line`, `modified_line`
  - `status`, `reason` (for rejection)

- **ApprovalSession**: Multi-hunk approval tracking
  - Aggregates hunks across file(s)
  - Tracks overall approval percentage
  - Provides summary reports

**Key Design**:
```python
@dataclass
class CodeHunk:
    file_path: str
    start_line: int
    end_line: int
    lines: List[LineModification]
    status: HunkStatus
    
    def approve_line(self, line_number: int) -> None:
        # Update line status
        # Recalculate hunk status
```

#### ApprovalModal (`kicli_code_assist/ui/modals/approval_modal.py`)
**Purpose**: Interactive UI for user approval of AI changes

- **Features**:
  - Show all hunks with status indicators
  - Preview of changes (first 5 lines)
  - Line-count and approval percentage
  - Buttons: Approve/Reject per hunk
  - Keyboard shortcuts: Enter (approve-all), Ctrl+R (reject-all)

- **Data Flow**:
  - Takes `ApprovalSession` as input
  - User clicks/types approvals
  - Returns updated `ApprovalSession` on dismiss

**Key Design**:
```python
class ApprovalModal(ModalScreen[Optional[ApprovalSession]]):
    def __init__(self, session: ApprovalSession):
        # Display hunks
        # Handle button clicks
        # Return session to caller
```

#### AIWorkflowManager (`kicli_code_assist/ai_workflow.py`)
**Purpose**: Orchestrate complete AI suggestion workflow

- **Flow**:
  1. `process_user_prompt()`: Send file + prompt to AsyncLLMIntegration
  2. `_create_hunks_from_response()`: Parse response into CodeHunks
  3. Create ApprovalSession
  4. (UI shows ApprovalModal)
  5. `apply_approved_changes()`: Apply approved lines to editor

- **Key Methods**:
  - `_build_context()`: Combine prompt + file info for LLM
  - `_parse_code_block_to_hunk()`: Match response to file lines
  - `get_session_summary()`: Generate report for user

**Key Design**:
```python
class AIWorkflowManager:
    async def process_user_prompt(self, prompt, file_context, ...):
        # 1. Call AsyncLLMIntegration.achat_with_context()
        # 2. Parse response into hunks
        # 3. Return AISuggestion with ApprovalSession
        
    def apply_approved_changes(self, suggestion, on_apply):
        # Build new file content from approved lines
        # Call on_apply(new_content)
```

#### CodeAssistantApp Integration (`kicli_code_assist/ui/app.py`)
**Purpose**: Connect UI events to AI workflow

- **Message Handler**: `on_file_editor_pane_ai_suggestions_requested()`
  - Triggered when user enables AI checkbox in FileEditorPane
  - Starts background worker for async processing

- **Worker Method**: `_process_ai_suggestions_worker()`
  - Runs async LLM call (non-blocking)
  - Updates UI with progress
  - Calls `_show_ai_approval_modal()` on completion

- **Approval Handler**: `_on_ai_approval_result()`
  - Receives updated ApprovalSession
  - Applies approved changes to active editor tab
  - Shows summary report

---

## Data Flow: AI Suggestion End-to-End

```
User Action: Enables "🤖 AI Suggestions" checkbox in FileEditorPane
                    ↓
FileEditorPane posts _AISuggestionsRequested message
                    ↓
CodeAssistantApp.on_file_editor_pane_ai_suggestions_requested()
                    ↓
Start background worker: _process_ai_suggestions_worker()
                    ↓
AIWorkflowManager.process_user_prompt() [ASYNC]
  1. Build context (file path + content + prompt)
  2. Call AsyncLLMIntegration.achat_with_context()
     - ProviderChain tries OpenAI → Anthropic → Ollama
     - On timeout: Exponential backoff retry
     - On auth error: Move to next provider
     - Secret filtering active: Remove API keys, passwords
  3. Parse response with ResponseParser
     - Extract TEXT, CODE, SHELL parts
  4. Create CodeHunks from response
     - Map lines to original file
     - Set line-by-line status = PENDING
  5. Create ApprovalSession
  6. Return AISuggestion
                    ↓
ApprovalModal shown to user
                    ↓
User approves/rejects hunks and lines
                    ↓
on_ai_approval_result() receives ApprovalSession
                    ↓
AIWorkflowManager.apply_approved_changes()
  - Build new content from approved lines
  - Call on_apply() callback
                    ↓
FileEditorPane content updated
User can review and save
```

---

## Security Design

### Secret Handling
1. **Pre-LLM Filtering**: SensitiveDataFilter catches secrets before sending
2. **Audit Trail**: RedactionLog tracks what was redacted (for compliance)
3. **Master Key Protection**: `~/.ki/master.key` with 0o600 permissions

### Error Safety
- No secrets in error messages (errors are user-safe)
- No stack traces exposed to user (RecoveryHints instead)
- All exceptions caught and converted to user-friendly hints

### Encryption Integrity
- Fernet includes HMAC verification (detects tampering)
- Key rotation support (new key → re-encrypt all data)
- Metadata versioning for future algorithm changes

---

## Performance Characteristics

| Operation | Time | Limiting Factor |
|-----------|------|-----------------|
| AsyncOpenAI.achat() | 1-10s | LLM API latency |
| ResponseParser.parse() | 10-50ms | Regex matching |
| EncryptionManager.encrypt(100KB) | 10-20ms | Fernet cipher |
| ApprovalModal.render() | < 5ms | Textual rendering |
| Apply approved changes | 1-5ms | File content update |

---

## Testing Strategy

### Phase 4.1 Tests (Async + Security)
- ✅ AsyncOpenAIClient initialization & timeouts
- ✅ ProviderChain fallback logic & retries
- ✅ Secret filtering (10+ patterns)
- ✅ Error recovery hints

### Phase 4.2 Tests (Robustness)
- ✅ Encryption roundtrip (encrypt → decrypt)
- ✅ Encrypted storage persistence
- ✅ Response parsing (single/multi-block)
- ✅ Shell command detection

### Phase 4.3 Tests (Workflow)
- ✅ CodeHunk line-level approval
- ✅ ApprovalSession percentage calculation
- ✅ AIWorkflowManager orchestration
- ✅ Context building & hunk creation

### Integration Tests
- ✅ Full secret filtering workflow
- ✅ End-to-end encryption workflow
- ✅ Error recovery chain

### Performance Tests
- ✅ Parser handles 100 code blocks efficiently (< 1s)
- ✅ Encryption handles 100KB data (< 100ms)
- ✅ Approval workflow with 100 hunks (< 500ms)

---

## Deployment & Operations

### Required Configuration
```bash
# LLM Provider
export OPENAI_API_KEY="sk-..."
export LLM_PROVIDER="openai"

# Optional: Master key location
export KI_MASTER_KEY_FILE="~/.ki/master.key"

# Optional: Approval settings
export AI_APPROVAL_REQUIRED=true
```

### Health Monitoring
```bash
kicli-assist doctor
# ✓ Config loaded
# ✓ LLM provider ready
# ✓ Encryption initialized
# ✓ Secret filtering active
```

### Rollback Plan
- Automatic if any Phase 4 deployment fails
- Manual: Revert to previous git tag + `make prod-update`

---

## Future Enhancements (Phase 5+)

1. **Better Context Matching**: Use embeddings to find exact lines changed
2. **Collaborative Approval**: Multiple users approve same suggestion
3. **AI Tuning**: Learn approval patterns per user (always reject certain types)
4. **Streaming Approval**: Show approval UI while LLM is streaming response
5. **Performance**: Cache parsed responses, parallel provider queries
6. **Security**: Key rotation automation, audit logging

---

**Document Updated**: 2024  
**Phase 4 Status**: ✅ COMPLETE

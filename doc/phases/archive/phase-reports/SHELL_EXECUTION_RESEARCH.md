# Shell Command Execution in AI Agents: Research & Implementation Guide

**Status:** Planning phase  
**Current Implementation:** None (Planned feature)  
**Research Horizon:** 2024–2025

---

## Executive Summary

Shell command execution is a **foundational capability** for sysadmin/DevOps AI agents. The 2024–2025 research landscape shows a clear consensus:

1. **Function Calling / Tool Use** is the standard abstraction (not string-based commands)
2. **Human-in-the-Loop (HITL) guardrails** are now **regulatory + enterprise mandates** (not optional)
3. **Audit trails and permission models** must be immutable and role-aware
4. **Approval workflows** must handle batches, escalation, timeouts, and session-level modes

---

## Part I: Tool Use & Function Calling (2024–2025)

### What's Emerging in Research

**Function Calling** is the industry standard for enabling LLM-based agents to take real-world actions. Rather than the agent generating free-form shell commands as text, it emits **structured function calls** with:
- Typed arguments (schema validation)
- Clear semantics (not ambiguous prose)
- Execution orchestrated by the host (safe isolation)

**Example (Structured vs. Text):**
```python
# ❌ Old (dangerous): "Please run: rm -rf /important/data"
# ✅ New (safe): 
{
  "tool": "shell_execute",
  "args": {
    "command": "ls -la /data",
    "timeout": 30,
    "safe_mode": True
  }
}
```

### Why This Matters

From **AWS, OpenAI, and Anthropic** docs (2024–2025):

- **Auditability:** Structured calls are machine-parseable; text is ambiguous
- **Guardrails:** Schemas enable pre-execution validation (blocklist, whitelist, etc.)
- **Chaining:** Agent can reason about output and chain calls (e.g., "run git status, then parse output")
- **Isolation:** Execution happens in controlled environment (container, sandbox, isolated venv)

### kicli-assist Implementation Strategy

For kicli-assist, the function-calling model translates to:

```python
@dataclass
class ShellCommandBatch:
    """A batch of shell commands proposed by LLM."""
    id: str  # unique ID
    commands: list[ShellCommand]  # list of commands
    description: str  # "Deploy new ki-core version"
    severity: str  # "low" | "medium" | "high" | "critical"
    estimated_duration_ms: int
    rollback_commands: Optional[list[ShellCommand]]  # if needed

@dataclass
class ShellCommand:
    """Single shell command."""
    command: str
    description: str  # "Pull latest from main branch"
    timeout_seconds: int = 30
    working_dir: Optional[str] = None  # ~/dev_flow/ki-core
    env_vars: Optional[dict] = None
```

---

## Part II: Human-in-the-Loop (HITL) Guardrails (Mandatory 2024–2025)

### Current Research Consensus

**HITL is no longer optional.** Key drivers:

1. **Regulatory (EU AI Act, NIST AI RMF):** High-risk AI actions require auditable human approval
2. **Risk Reduction:** Studies show 78% reduction in critical errors when HITL is integrated
3. **Enterprise Governance:** Board-level risk concern; requires documented decision trails

### Five Core HITL Patterns

From latest production systems (2024–2025):

1. **Approval Gate:**
   - Agent proposes action → pauses
   - Human reviews → approves/rejects/edits
   - If approved → executes with full audit trail

2. **Escalation Ladder:**
   - Low-risk actions: auto-approve or lightweight review
   - Medium-risk: manager approval needed
   - High-risk: escalate to senior/security team

3. **Confidence-Based Routing:**
   - If agent confidence < threshold → route to approval
   - If agent confidence > threshold → auto-execute (with logging)

4. **Collaborative Drafting:**
   - Agent drafts commands
   - Human can edit before execution
   - Only final, human-approved version runs

5. **Audit Trail & Lazy Review:**
   - All actions logged immutably
   - Some actions reviewed post-hoc (not blocking)
   - Enables pattern detection and learning

### kicli-assist Implementation Strategy

For your use case (sysadmin KI with session-level permissions):

```python
class ShellExecutionApproval:
    """HITL approval decision."""
    
    decision: Literal["approved", "rejected", "approved_edited", "pending"]
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None  # username or "auto"
    reason: Optional[str] = None  # why approved/rejected
    edited_commands: Optional[list[ShellCommand]] = None
    
    # Audit fields (immutable)
    audit_log: list[AuditEntry] = field(default_factory=list)
    session_permission_level: Literal["none", "batch", "session"] = "batch"

class AuditEntry:
    """Immutable record of action/decision."""
    timestamp: datetime
    action: str  # "proposed" | "reviewed" | "approved" | "executed" | "failed"
    actor: str  # username or "system"
    details: dict  # action-specific metadata
```

---

## Part III: Permission Models for Shell Execution

### Session-Level Permissions (Your Model)

You want: **"Approve once per session, auto-execute all commands for rest of session"**

This is a **valid HITL pattern** but requires careful implementation:

```python
class ChatSession:
    shell_execution_mode: Literal["off", "batch", "session"] = "batch"
    session_approved_at: Optional[datetime] = None
    session_approver: Optional[str] = None
    
    def should_auto_execute(self, command: ShellCommand) -> bool:
        """Check if command auto-executes without approval."""
        if self.shell_execution_mode == "session":
            return self.session_approved_at is not None
        return False
```

**Safety Considerations:**

- ✅ **Good for:** Dev/sysadmin flows where you trust the session context
- ⚠️ **Risk:** Agent could propose dangerous commands later in session
- **Mitigation:**
  1. Log every command that auto-executes (immutable audit trail)
  2. Offer "revoke session approval" at any time
  3. Hard-code blocklist for dangerous patterns (e.g., `rm -rf /`, format disks)
  4. Display executed commands in chat so user sees them happen

---

## Part IV: Risk Classification & Guardrails

### Research Recommendation: Multi-Level Approval

From HITL papers (2024):

```
Low-Risk (git status, ls):
  → Auto-execute + log
  
Medium-Risk (git commit, pip install):
  → Show batch, require batch approval
  
High-Risk (rm, dd, format):
  → Blocklist by default, manual approval needed
  
Critical-Risk (rm -rf /, chmod 000):
  → Always reject
```

### kicli-assist Implementation

```python
RISK_PATTERNS = {
    "low": [
        r"^git\s+(status|log|diff|branch)",
        r"^ls",
        r"^pwd",
        r"^cat\s+",
    ],
    "medium": [
        r"^git\s+(commit|push|pull)",
        r"^pip\s+install",
        r"^python\s+-m",
    ],
    "high": [
        r"^rm\s+",
        r"^chmod\s+",
        r"^chown\s+",
    ],
    "critical": [
        r"rm\s+-rf\s+/",
        r"mkfs\.",
        r"dd\s+if=.*of=",
    ],
}

def classify_risk(command: str) -> str:
    """Classify command risk level."""
    for level in ["critical", "high", "medium", "low"]:
        for pattern in RISK_PATTERNS[level]:
            if re.match(pattern, command):
                return level
    return "unknown"
```

---

## Part V: Audit Trail & Logging

### Industry Best Practice (2024–2025)

All HITL interactions must be **immutable, role-aware, and legally defensible:**

```python
@dataclass
class ExecutionAuditRecord:
    """Immutable record for compliance."""
    id: str  # UUID
    timestamp: datetime
    session_id: str
    
    # Proposed
    command_batch: ShellCommandBatch
    proposed_by: str  # "gpt-4o" or model name
    
    # Approval
    approval_decision: ShellExecutionApproval
    approved_by: Optional[str]  # username
    approval_timestamp: Optional[datetime]
    
    # Execution
    execution_results: Optional[list[ExecutionResult]]
    execution_timestamp: Optional[datetime]
    
    # Immutability
    hash_chain: str  # SHA256(previous_record + this_record)
```

**Storage:** `~/dev_data/kicli-assist/log/execution_audit.jsonl`

```json
{
  "id": "exec_abc123",
  "timestamp": "2025-10-16T13:58:00Z",
  "session_id": "chat_xyz789",
  "command_batch": {
    "commands": [
      {"command": "git pull", "description": "Update code"}
    ]
  },
  "approval_decision": {
    "decision": "approved",
    "approved_by": "flow",
    "session_permission_level": "session"
  },
  "execution_results": [
    {"success": true, "stdout": "Already up to date.", "returncode": 0}
  ]
}
```

---

## Part VI: Workflow: Proposed → Approved → Executed

### Complete Flow in kicli-assist TUI

```
┌─ LLM generates response ─────────────┐
│  "To update, run these commands:"   │
│                                      │
│  [1] git pull                        │
│  [2] pip install -e .                │
│  [3] stackctl pull                   │
│                                      │
│  ⚠️  Severity: MEDIUM                │
│                                      │
│  [Buttons]                           │
│  [Execute Batch]  [Skip]  [Edit]     │
│  [✓ Auto-approve for session]        │
└──────────────────────────────────────┘

User clicks "Execute Batch"
  ↓
[User approval recorded in audit trail]
  ↓
[Execute each command with SafeCodeExecutor]
  ↓
[Stream output to chat]
  ↓
[Log all results + decisions to audit trail]
  ↓
[Chat continues, LLM can reason about results]
```

---

## Part VII: Integration Checklist

### For kicli-assist Implementation

- [ ] **Message Type:** Define `CommandExecutionRequest` (extends `ChatMessage`)
- [ ] **Risk Classifier:** Implement `classify_risk()` and RISK_PATTERNS
- [ ] **Approval UI:** Textual widget showing batch + buttons (Execute/Skip/Edit/SessionMode)
- [ ] **Session State:** ChatSession tracks `shell_execution_mode`, `session_approved_at`
- [ ] **Executor:** Extend `SafeCodeExecutor` to use schemas, handle timeouts, capture output
- [ ] **Audit Trail:** Create `ExecutionAuditRecord` class, write to JSONL
- [ ] **System Prompt:** Update LLM system prompt to explain shell execution capability
- [ ] **Logging:** Centralize to `~/dev_data/kicli-assist/log/execution_audit.jsonl`
- [ ] **Error Handling:** Graceful fallback if execution fails (don't crash chat)
- [ ] **User Documentation:** Explain HITL, risk levels, session mode, audit trails

---

## Part VIII: Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Agent proposes `rm -rf /` | Blocklist critical patterns, always reject |
| User enables "session mode", then forgets | Display approval banner, offer revoke button |
| Audit trail lost or tampered | Hash-chain records, use append-only log file |
| Long command output fills memory | Stream output, cap log size per command |
| Session-level approval too permissive | Default to "batch" mode, require explicit session opt-in |
| GDPR/compliance concerns | Document who approved what, when, why (immutable) |

---

## Part IX: References & Further Reading

### 2024–2025 Research Papers & Resources

- **Function Calling & Tool Use:**
  - JetBrains Dev Ecosystem Survey 2026 (tool use adoption)
  - AWS Prescriptive Guidance: Tool-based agents for calling functions
  - Anthropic tool_use documentation

- **Human-in-the-Loop (HITL):**
  - EU AI Act Article 14 (human oversight requirements)
  - NIST AI Risk Management Framework
  - "Human-in-the-Loop AI Agents: Patterns and Best Practices" (dev.to, 2024)
  - "How to Build AI Human-In-The-Loop Guardrails" (AIReapps, 2024)

- **Shell Execution & Safety:**
  - OpenAI Agents SDK documentation (ShellTool)
  - "Building AI Agents" (TypeScript guide, Chapter 8: Shell Tool)
  - SafeCodeExecutor patterns (whitelist, blocklist, timeouts)

### Key Takeaways for kicli-assist

1. **Structured function calls > free-form text** (JSON schemas, typed args)
2. **HITL approval is mandatory**, not optional (regulatory + safety)
3. **Audit trails must be immutable** (hash-chain, role-based, timestamped)
4. **Session-level permissions are valid but risky** (mitigate with blocklists + logging)
5. **Risk classification drives approval intensity** (low = auto, high = escalate)

---

## Next Steps

1. **Define message types** (CommandExecutionRequest, ShellCommand, ShellExecutionApproval)
2. **Build approval UI** (Textual widget with Execute/Skip/Edit/SessionMode buttons)
3. **Extend SafeCodeExecutor** (schema validation, risk classification, timeout handling)
4. **Implement audit trail** (JSONL, hash-chain, immutable record storage)
5. **Update system prompt** (tell LLM about shell execution capability)
6. **Test workflow end-to-end** (propose → approve → execute → log)

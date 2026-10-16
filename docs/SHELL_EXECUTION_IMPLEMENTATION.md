# Shell Command Execution: Implementation Status & Next Steps

**Status:** Tasks 1-5 Complete ✅ | Task 6 (Integration) - Planning

---

## What's Been Implemented (Tasks 1-5)

### ✅ Task 1: Message Types
- `ShellCommand`, `ShellCommandBatch` dataclasses (type-safe)
- `RiskLevel` enum (LOW, MEDIUM, HIGH, CRITICAL)
- `classify_risk()` function with 50+ regex patterns
- `ShellExecutionApproval`, `ExecutionAuditRecord` for HITL
- Hash-chain support for immutable records
- Integrated into `ChatMessage` and `ChatSession`

### ✅ Task 2: TUI Approval Widget
- `ShellCommandApprovalModal` (Textual modal screen)
- Risk level color-coded display (🟢🟡🟠🔴)
- Syntax-highlighted command list (bash)
- Buttons: Execute | Skip | Edit | Cancel
- Session mode toggle (auto-approve for session)
- Message types: `CommandsApprovalRequested`, `CommandsExecuted`, `CommandsSkipped`

### ✅ Task 3: Extended Executor
- `SafeCodeExecutor.execute_batch()` for batch execution
- Risk-aware safety validation
- `ALWAYS_BLOCKED` commands (mkfs, dd, fdisk)
- 50+ forbidden patterns
- Timeout handling, env vars, working dir support
- 10KB output cap per command
- Unified `ExecutionResult` type

### ✅ Task 4: Audit Trail
- `AuditTrailLogger` for immutable JSONL logging
- Hash-chain integrity verification
- `read_records()`, `get_summary()`, `verify_integrity()`
- Export to JSON and CSV for analysis
- Append-only design (compliance-ready)

### ✅ Task 5: System Prompt
- `get_shell_execution_capability()` guidelines
- LLM knows how to propose `<shell_execute>` blocks
- Safety-first documentation
- Risk levels explained to model
- HITL workflow described

---

## Integration Points Still Needed (Task 6)

### 1. LLM Response Parser
**File:** `kicli_code_assist/executor/response_parser.py` (NEW)

```python
class ShellExecutionResponseParser:
    """Parse LLM responses for <shell_execute> blocks."""
    
    def parse(self, response_text: str) -> Optional[ShellCommandBatch]:
        """Extract commands from LLM response.
        
        Looks for:
        - <shell_execute> ... </shell_execute> blocks
        - Markdown ```bash ... ``` code blocks (heuristic)
        
        Returns:
            ShellCommandBatch or None if no commands found
        """
        # Parse XML-style or markdown blocks
        # Validate commands with safety patterns
        # Return ShellCommandBatch
```

### 2. Chat Integration
**File:** `kicli_code_assist/chat_session.py` (EXTEND)

```python
class ChatSession:
    def handle_shell_command_proposal(self, response_text: str):
        """Process LLM response, show approval UI if commands detected."""
        batch = self.parser.parse(response_text)
        if not batch:
            # No commands, display normally
            return response_text
        
        # Emit message for TUI to show approval modal
        # Pause chat until user approves/skips
        # If approved: execute_batch(), log to audit trail
        # If skipped: continue chat
        # Return execution results or skip message
```

### 3. TUI Integration
**File:** `kicli_code_assist/ui/textual_app.py` (EXTEND)

```python
class TextualApp:
    def on_commands_approval_requested(self, message: CommandsApprovalRequested):
        """Show approval modal when LLM proposes commands."""
        modal = ShellCommandApprovalModal(message.batch)
        self.push_screen(modal)
    
    def on_commands_executed(self, message: CommandsExecuted):
        """Display execution results in chat."""
        # Show results: stdout, stderr, success/failure
        # Update chat message with output
```

### 4. Audit Trail Integration
**File:** `kicli_code_assist/executor/audit_trail.py` (INIT)

```python
# In ChatSession.__init__():
audit_dir = Path(os.getenv("HOME")) / "dev_data" / "kicli-assist" / "log"
self.audit_logger = AuditTrailLogger(audit_dir / "execution_audit.jsonl")

# After execution:
self.audit_logger.log_execution(audit_record)
```

---

## End-to-End Workflow Diagram

```
User: "Deploy the latest code"
  ↓
LLM (with shell execution capability) → Proposes:
  "I'll update code and restart the service:
   <shell_execute>
   - git pull
   - pip install -e .
   - systemctl restart kicli-assist
   </shell_execute>"
  ↓
ResponseParser → Detects shell_execute block
  ↓
TUI Shows → ShellCommandApprovalModal
  ├─ Title: "Approve Shell Command Execution"
  ├─ Risk: 🟡 MEDIUM RISK
  ├─ Commands:
  │  1. 🟢 git pull
  │  2. 🟡 pip install -e .
  │  3. 🟡 systemctl restart kicli-assist
  ├─ Buttons:
  │  [Execute Batch] [Skip] [Edit] [Cancel]
  │  ☐ Auto-approve for session
  └─ User clicks: "Execute Batch"
  ↓
ChatSession.execute_shell_batch():
  1. Validate each command
  2. Call SafeCodeExecutor.execute_batch()
  3. Stream results to chat
  4. Log each result to AuditTrailLogger
  5. Create ExecutionAuditRecord with:
     - batch details
     - approval decision + approver
     - execution results + timing
  6. Hash-chain for integrity
  ↓
Audit Trail:
  ~/dev_data/kicli-assist/log/execution_audit.jsonl
  {
    "id": "exec_abc123",
    "timestamp": "2025-10-16T14:29:45Z",
    "session_id": "chat_xyz",
    "command_batch": { ... },
    "approval": {
      "decision": "approved",
      "approved_by": "flow",
      "session_permission_level": "batch"
    },
    "execution_results": [
      {"command": "git pull", "success": true, "stdout": "Already up to date", ...},
      {"command": "pip install -e .", "success": true, ...},
      {"command": "systemctl restart ...", "success": true, ...}
    ],
    "current_hash": "sha256:abc...",
    "previous_hash": "sha256:def..."
  }
  ↓
Chat resumes:
  "✓ All commands executed successfully! Code updated and service restarted."
```

---

## Test Cases for Task 6

### Test 1: Basic Batch Execution
```python
def test_basic_batch_approval_and_execution():
    """User approves batch, all commands execute."""
    session = ChatSession()
    batch = ShellCommandBatch(commands=[
        ShellCommand('git pull'),
        ShellCommand('echo "deploy"'),
    ])
    
    # Mock user approval
    approval = session.execute_shell_batch(batch, approver="test_user")
    
    # Assert: all commands executed
    assert approval.decision == ApprovalDecision.APPROVED
    assert len(approval.audit_log) > 0
```

### Test 2: Session-Level Auto-Approval
```python
def test_session_auto_approval():
    """After session-level approval, commands auto-execute."""
    session = ChatSession()
    session.approve_shell_execution_for_session("test_user")
    
    batch1 = ShellCommandBatch(commands=[ShellCommand('git status')])
    batch2 = ShellCommandBatch(commands=[ShellCommand('git log')])
    
    # Both should auto-execute without further approval
    assert session.should_auto_execute_shell(batch1) == True
    assert session.should_auto_execute_shell(batch2) == True
```

### Test 3: Risk Classification Blocks CRITICAL
```python
def test_critical_risk_blocked():
    """CRITICAL commands rejected unless allow_critical=True."""
    executor = SafeCodeExecutor(allow_critical=False)
    
    result = executor.execute("rm -rf /")
    
    assert result.success == False
    assert "CRITICAL risk" in result.stderr
```

### Test 4: Audit Trail Integrity
```python
def test_audit_trail_hash_chain():
    """Audit trail maintains hash-chain integrity."""
    logger = AuditTrailLogger(Path("/tmp/test_audit.jsonl"))
    
    record1 = ExecutionAuditRecord(id="exec_1")
    record2 = ExecutionAuditRecord(id="exec_2")
    
    logger.log_execution(record1)
    logger.log_execution(record2)
    
    # Verify integrity
    is_valid, errors = logger.verify_integrity()
    assert is_valid == True
    assert len(errors) == 0
```

### Test 5: LLM Response Parsing
```python
def test_parse_shell_execute_block():
    """Parser detects <shell_execute> blocks in LLM response."""
    response = """
    I'll deploy the code:
    
    <shell_execute>
    - git pull
    - pip install -e .
    - systemctl restart app
    </shell_execute>
    """
    
    parser = ShellExecutionResponseParser()
    batch = parser.parse(response)
    
    assert batch is not None
    assert len(batch.commands) == 3
    assert batch.commands[0].command == "git pull"
```

---

## Implementation Checklist for Task 6

- [ ] Create `response_parser.py` with `ShellExecutionResponseParser`
  - [ ] Parse `<shell_execute>` XML blocks
  - [ ] Parse markdown ```` ```bash ... ``` ```` blocks
  - [ ] Heuristic detection fallback
  - [ ] Unit tests for parsing

- [ ] Extend `chat_session.py`:
  - [ ] Add `execute_shell_batch()` method
  - [ ] Integrate `SafeCodeExecutor`
  - [ ] Integrate `AuditTrailLogger`
  - [ ] Handle approval workflow (UI interaction)
  - [ ] Stream execution results back to chat

- [ ] Extend `textual_app.py`:
  - [ ] Listen for `CommandsApprovalRequested` message
  - [ ] Push `ShellCommandApprovalModal` to screen
  - [ ] Handle modal result (approved/skipped/edited)
  - [ ] Display execution results inline in chat

- [ ] Audit trail initialization:
  - [ ] Create log directory structure
  - [ ] Initialize `AuditTrailLogger` in session
  - [ ] Log each execution to JSONL

- [ ] Comprehensive testing:
  - [ ] Unit tests for each component
  - [ ] Integration test: LLM → Parser → Approval → Execution → Audit
  - [ ] Manual testing in TUI
  - [ ] Edge cases: timeouts, command failures, user cancellation

- [ ] Documentation:
  - [ ] Update README with shell execution feature
  - [ ] Write user guide for approval workflow
  - [ ] Document audit trail format for compliance

---

## Configuration & Environment

### Log Directory
```bash
mkdir -p ~/dev_data/kicli-assist/log
chmod 755 ~/dev_data/kicli-assist
```

### Environment Variables
```bash
# Optional
export KICLI_SHELL_EXECUTION_ENABLED=true
export KICLI_SHELL_ALLOW_CRITICAL=false  # Block CRITICAL commands by default
export KICLI_SHELL_TIMEOUT=30  # 30 seconds per command
export KICLI_AUDIT_LOG_PATH=~/dev_data/kicli-assist/log/execution_audit.jsonl
```

---

## Safety & Compliance

### Security Layers
1. **Risk Classification** - Commands automatically classified
2. **Blocklist** - CRITICAL commands rejected by default
3. **Human Approval** - User must approve batch before execution
4. **Audit Trail** - All decisions immutably logged
5. **Hash-Chain** - Tampering detected by verification

### Compliance Standards
- **NIST AI RMF** - Audit trail satisfies human oversight requirement
- **EU AI Act Article 14** - Documented human approval for high-risk AI
- **HITL Governance** - Session-level permissions with revocation support

---

## Known Limitations & Future Work

### Phase 1 (Current)
- Basic batch execution
- Session-level permissions
- No command editing in approval modal
- No rollback capability

### Phase 2 (Future)
- Edit commands before execution
- Dry-run mode
- Rollback execution (revert last N commands)
- Command templates/macros
- Scheduled execution (cron-like)
- Multi-user approval workflows

### Phase 3 (Future)
- Integration with configuration management (Ansible, Terraform)
- Federated execution (multiple target hosts)
- Advanced filtering by risk, command type, user role

---

## References

- `docs/SHELL_EXECUTION_RESEARCH.md` - AI agent research & patterns
- `docs/YAML_CONFIG_ARCHITECTURE.md` - Architecture overview
- `ki-ecosystem/docs/DEPLOYMENT.md` - Target host deployment

---

## Getting Started

1. **After Task 6 implementation:**
   ```bash
   cd ~/dev_flow/kicli-code-assist
   python3 -m kicli_code_assist.ui.textual_app
   ```

2. **Start chat:**
   ```
   > Deploy the latest code
   ```

3. **See LLM propose commands, approve batch:**
   ```
   [Approval Modal appears]
   Risk: MEDIUM
   Commands: git pull, pip install -e .
   [Click Execute Batch]
   ```

4. **Check audit trail:**
   ```bash
   tail ~/dev_data/kicli-assist/log/execution_audit.jsonl
   ```

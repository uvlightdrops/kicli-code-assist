---
title: "Phase 5.5: Advanced Autonomy - Concept & Roadmap"
project: "kicli-code-assist"
scope: "phases"
created: 2026-11-02T00:09:00+01:00
updated: 2026-11-02T00:26:00+01:00
update_reason: "5.5.1 & 5.5.2 complete, 5.5.3 architecture documented"
status: "active"
author: "Copilot"
---

# Phase 5.5: Advanced Autonomy - Concept & Roadmap

## Executive Summary

**Vision:** Extend agent autonomy beyond single-file generation to multi-file refactoring, transparent reasoning, and deployment orchestration.

**Scope:** 3 sub-phases over 4 weeks
- **5.5.1 Multi-File Refactoring** - Agents handle cross-file changes atomically
- **5.5.2 Transparency & Observability** - Real-time reasoning + cost tracking
- **5.5.3 Orchestration Integration** - stackctl + staging verification

**Expected Impact:**
- Agent can tackle complex features (not just single files)
- Users see agent reasoning in real-time
- Code reaches staging automatically & safely

---

## Phase 5.5.1: Multi-File Refactoring (Week 1)

### Problem Statement
Current `CodeImplementationAgent.apply_with_full_autonomy()` handles **one file at a time**. Real refactorings need:
- Update class definition in `models.py`
- Update imports in `api.py`, `services.py`, `tests.py`
- Migrate data in migrations
- All atomic or all rollback

### Concept

**Architecture: Refactoring Coordinator**

```
User Request: "Rename UserAccount to User across project"
  ↓
1. Intent Detection → "multi_file_refactoring"
  ↓
2. Impact Analysis
   - Find all files affected (imports, usage, definitions)
   - Build dependency graph
   - Identify safe order
  ↓
3. Atomic Refactoring
   - Create feature branch
   - For each file (in order):
     * Generate changes via LLM
     * Verify AST + imports
     * Apply changes
   - Run full test suite (catches cross-file issues)
   - Commit atomically
  ↓
4. Rollback if Tests Fail
   - All changes reverted together
   - No partial state
```

### Core Components

**1. RefactoringAnalyzer**
- Scans project for usage of renamed entity
- Builds file dependency graph
- Suggests order of changes

**2. MultiFileCoordinator**
- Orchestrates changes across files
- Tracks which files modified
- Ensures consistency

**3. ImportResolver**
- Updates imports when files move/rename
- Detects circular import issues
- Validates import chains

### Implementation Plan

- [ ] `RefactoringAnalyzer.analyze_impact(entity_name, project_root)` → List[File]
- [ ] `MultiFileCoordinator.execute_refactoring(changes: List[FileChange])` → Result
- [ ] Extend `CodeImplementationAgent.apply_with_full_autonomy()` to accept `List[FileChange]`
- [ ] Update `TestRunner` to validate cross-file consistency
- [ ] Add `refactoring/` module in agent/

### Success Criteria

- ✅ Agent can rename class across 5+ files atomically
- ✅ All imports updated correctly
- ✅ Tests pass after refactoring
- ✅ Rollback works if any step fails
- ✅ Reports show which files changed

---

## Phase 5.5.2: Transparency & Observability (Week 2)

### Problem Statement
When agent executes, user has no visibility into:
- What reasoning led to this decision?
- Which LLM calls were made?
- How much did it cost (tokens)?
- Why did agent choose this workflow?

Current state: Logs buried in `log/kicli-llm.log`, not in agent output.

### Concept

**Architecture: Reasoning Stream + Cost Tracker**

```
Agent Execution:
  ├─ Intent Detection → Log reasoning
  ├─ Workflow Selection → Log decision + alternatives
  ├─ LLM Call → Log prompt + response + cost
  ├─ Code Generation → Log reasoning
  └─ Verification → Log results
  
  ↓ All collected in:
  
ReasoningTrace:
  - decisions: List[Decision]      # Why agent chose this
  - llm_calls: List[LLMCall]        # Prompts, responses, costs
  - errors: List[Error]             # What failed & why
  - timing: Dict[str, int]          # Performance metrics
  
  ↓ Exposed as:
  
CoordinationResult.reasoning_trace
  → Real-time streaming to frontend
  → Displayed in debug panel
  → Downloadable audit file
```

### Core Components

**1. ReasoningTracer**
- Captures all agent decisions
- Records reasoning + alternatives
- Thread-safe for concurrent agents

**2. LLMCallTracker**
- Intercepts LLM calls
- Logs prompt, response, token count
- Calculates cost (USD)
- Detects anomalies (unusually high token usage)

**3. PerformanceMetrics**
- Timeline: which phase took how long
- Bottleneck detection
- Comparison with historical runs

**4. AuditExporter**
- Export reasoning trace as JSON/YAML
- Human-readable summary
- Machine-parseable audit trail

### Implementation Plan

- [ ] `ReasoningTracer` class in agent/
- [ ] `LLMCallTracker` middleware for ki-core OpenAI client
- [ ] Extend `CoordinationResult` with `reasoning_trace` field
- [ ] WebSocket streaming of trace events (real-time)
- [ ] Frontend debug panel showing live reasoning
- [ ] Cost aggregation per agent, per day, per project

### Success Criteria

- ✅ User sees agent reasoning in real-time
- ✅ Cost tracking accurate to token level
- ✅ Audit trail downloadable for compliance
- ✅ <100ms overhead per decision
- ✅ Frontend shows decision tree + alternatives

---

## Phase 5.5.3: Orchestration Integration (Week 3-4)

### Problem Statement
After agent commits code to `devel` branch, what happens?
- Manual: Developer runs `git push`, then `stackctl -t minikube start` manually
- No verification that changes work in staging
- No feedback loop to agent

Goal: **Agent can orchestrate full pipeline: Code → Git → stackctl → Staging → Verify**

### Concept

**Architecture: DeploymentCoordinator + StagingVerifier**

```
Agent completes refactoring:
  ├─ Code generated & tested locally ✅
  ├─ Committed to feature branch ✅
  ├─ Tests pass ✅
  └─ Ready for deployment
    
    ↓
    
DeploymentCoordinator:
  1. Merge feature branch → devel (if tests pass)
  2. Call stackctl -t local status
  3. Verify all services still healthy
  4. Run integration tests (cross-service)
  5. Push to staging (second machine via git + stackctl)
  
    ↓
    
StagingVerifier:
  1. Wait for services up on staging
  2. Run smoke tests
  3. Compare API responses vs. prod (regression detection)
  4. Check logs for errors
  5. Report back to agent
  
    ↓
    
Result:
  - ✅ All checks pass → Ready for production
  - ❌ Staging failed → Rollback + analysis + report to dev
```

### Core Components

**1. DeploymentCoordinator**
- Merge branch (with safety checks)
- Run stackctl start/stop/restart
- Verify service health (HTTP health checks)
- Integration test execution

**2. StagingVerifier**
- SSH into staging host
- Wait for services online (with timeout)
- Run regression tests
- Analyze logs for anomalies
- Report metrics (latency, error rate)

**3. RollbackCoordinator**
- If staging fails: revert merge
- Notify dev/agent of failure
- Preserve logs for analysis

**4. DeploymentTracker**
- Audit trail: who deployed what when
- Cost per deployment (compute resources)
- Performance before/after
- Incident history

### Implementation Plan

- [ ] `DeploymentCoordinator` class (orchestrate stackctl)
- [ ] `StagingVerifier` class (SSH + health checks)
- [ ] Extend `CodeImplementationAgent` final step with deployment
- [ ] Add `staging_verification_pass` to success criteria
- [ ] Integration with multi-host setup (dev machine + staging)
- [ ] Metrics collection + dashboard

### Success Criteria

- ✅ Agent can merge + deploy to staging automatically
- ✅ Staging verification prevents broken code going live
- ✅ Rollback automatic if staging fails
- ✅ Full audit trail (who, what, when, why)
- ✅ Escalation to human if agent can't auto-recover

---

## Implementation Timeline

| Phase | Duration | Start | End | Deliverables |
|-------|----------|-------|-----|--------------|
| 5.5.1 | 1 week | 2026-11-02 | 2026-11-09 | Multi-file refactoring working, tests pass |
| 5.5.2 | 1 week | 2026-11-09 | 2026-11-16 | Reasoning trace + cost tracking exposed |
| 5.5.3 | 2 weeks | 2026-11-16 | 2026-11-30 | Full pipeline: code → staging → verify |

**Total: 4 weeks (Nov 2 - Nov 30)**

---

## Success Metrics

### Phase 5.5.1
- Agent successfully refactors class name across 5+ files
- 100% tests pass after refactoring
- Zero manual fixes needed

### Phase 5.5.2
- Reasoning trace captured for 100% of agent executions
- Cost tracking accurate within ±5% of OpenAI invoice
- Frontend displays reasoning in <1s

### Phase 5.5.3
- Code reaches staging automatically within 5 min of agent completion
- Staging verification catches 100% of obvious integration issues
- Rollback works reliably, zero orphaned deployments

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Cross-file changes too complex | High | Start with simple renames, expand to refactorings |
| LLM reasoning expensive | Medium | Cache prompts, reuse across similar tasks |
| Staging deployment race conditions | High | Mutex lock per deployment, queue if in progress |
| SSH access to staging unreliable | Medium | Fallback to local-only testing first |

---

## References

- Current implementation: `kicli_code_assist/agent/code_implementation.py`
- Phase 5.4 reference: `doc/phases/PHASE_5_4_SUMMARY.md`
- Autonomy analysis: `doc/phases/PHASE_5_AUTONOMY_ANALYSIS.md`
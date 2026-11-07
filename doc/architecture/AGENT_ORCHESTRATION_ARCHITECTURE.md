---
title: "Phase 5.5.3: Orchestration Integration - Architecture"
project: "kicli-code-assist"
scope: "architecture"
created: 2026-11-02T00:22:00+01:00
updated: 2026-11-02T00:22:00+01:00
update_reason: "Concept for stackctl + staging verification pipeline"
status: "active"
author: "Copilot"
---

# Phase 5.5.3: Orchestration Integration - Architecture

## Problem Statement

After agent commits code to feature branch, the feedback loop breaks:
- Developer must manually test locally
- Push to staging is manual
- No automated verification that changes work
- No rollback if staging breaks

**Goal:** Close the loop: Code → Git → stackctl → Staging → Verify → Prod-Ready

---

## Vision

```
Agent completes refactoring:
  ├─ Tests pass locally ✅
  ├─ Code committed to feature branch ✅
  ├─ Commit pushed to remote ✅
  
  ↓ [NEW]
  
  ├─ DeploymentCoordinator
  │  ├─ Merge feature branch → devel
  │  ├─ Verify local services still healthy
  │  ├─ Run integration tests
  │  ├─ Generate staging deployment request
  │  
  ├─ StagingVerifier (on 2nd dev machine)
  │  ├─ Git pull from devel
  │  ├─ Run stackctl start (staging environment)
  │  ├─ Wait for services online (5min timeout)
  │  ├─ Run smoke tests
  │  ├─ Compare API responses vs. production
  │  ├─ Analyze logs for errors
  │  ├─ Generate verification report
  │  
  ├─ Result
  │  ├─ ✅ All checks pass → Ready for production
  │  ├─ ✅ Create Pull Request for human review
  │  └─ ✅ Notify agent + human
  │  
  └─ On Failure
     ├─ ❌ Revert merge
     ├─ ❌ Stop staging services
     ├─ ❌ Create incident report
     └─ ❌ Notify human for manual intervention
```

---

## Architecture

### 1. DeploymentCoordinator (Local)

Orchestrates merge + local verification before staging.

```python
class DeploymentCoordinator:
    """Prepare code for staging deployment."""
    
    async def prepare_for_staging(
        self,
        feature_branch: str,
        agent_id: str,
        description: str
    ) → DeploymentPrepareResult:
        """
        Merge feature branch and run pre-staging checks.
        
        Steps:
        1. Fetch from remote
        2. Merge feature branch → devel (if no conflicts)
        3. Run stackctl health check (verify local services)
        4. Run integration test suite
        5. Generate staging deployment manifest
        """
        
    def merge_branch(self, feature_branch: str) → MergeResult:
        """Merge feature branch to devel."""
        # git fetch
        # git merge feature_branch
        # Handle conflicts: escalate to human
        
    def run_local_health_check(self) → HealthCheckResult:
        """Verify all local services still healthy."""
        # stackctl status --json
        # Check: api responds, frontend loads
        # Check: no service errors
        
    def run_integration_tests(self) → TestResult:
        """Run cross-service integration tests."""
        # Tests that verify:
        # - API ↔ Database
        # - Frontend ↔ API
        # - Service discovery
        # - No breaking changes
        
    def generate_staging_manifest(self) → StagingManifest:
        """Generate deployment request for staging."""
        # Captures: branch SHA, timestamp, changes, test results
        # Sent to staging verifier via message queue or HTTP
```

**Data Structure:**

```python
@dataclass
class DeploymentPrepareResult:
    success: bool
    feature_branch: str
    merge_sha: Optional[str]
    merge_conflicts: List[str]
    health_check_passed: bool
    integration_tests_passed: bool
    test_results: TestResult
    staging_manifest: Optional[StagingManifest]
    error: Optional[str]
    duration_ms: int
    
@dataclass
class StagingManifest:
    branch: str
    commit_sha: str
    timestamp: datetime
    agent_id: str
    description: str
    changes_summary: str
    test_results: TestResult
    ready_for_staging: bool
```

### 2. StagingVerifier (Remote)

Deployed on 2nd dev machine (staging host).

```python
class StagingVerifier:
    """Verify deployment works in staging environment."""
    
    def __init__(self, ssh_host: str, ssh_user: str, ssh_key: Path):
        """Connect to staging host via SSH."""
    
    async def verify_deployment(
        self,
        manifest: StagingManifest,
        timeout_sec: int = 300
    ) → StagingVerificationResult:
        """
        Pull changes and run full verification suite.
        
        Steps:
        1. SSH into staging
        2. Git pull from devel
        3. Run stackctl start
        4. Wait for services online (with timeout)
        5. Run smoke tests
        6. Compare vs. production (regression detection)
        7. Analyze logs
        8. Generate verification report
        """
        
    async def pull_and_prepare(self) → bool:
        """SSH: git pull && npm install (if needed)."""
    
    async def start_services(self) → bool:
        """SSH: stackctl -t local start."""
    
    async def wait_for_healthy(self, timeout_sec: int = 300) → HealthResult:
        """Poll: stackctl status until healthy or timeout."""
        # Checks:
        # - API port responding
        # - Frontend page loads
        # - Database accessible
        
    async def run_smoke_tests(self) → TestResult:
        """Run basic tests against staging."""
        # Tests:
        # - Health endpoints respond
        # - API returns expected data
        # - Frontend renders
        # - No critical errors in logs
        
    async def compare_with_production(self) -> RegressionReport:
        """Compare staging responses vs. production."""
        # Calls same endpoints on both
        # Compares: status codes, response times, data formats
        # Detects: breaking changes, performance regressions
        
    async def analyze_logs(self) → LogAnalysis:
        """Fetch and analyze service logs."""
        # Looks for: errors, warnings, stack traces
        # Severity: info, warn, error, critical
        
    async def cleanup_on_failure(self) → bool:
        """SSH: stackctl stop (clean up if failed)."""
```

**Data Structure:**

```python
@dataclass
class StagingVerificationResult:
    success: bool
    manifest: StagingManifest
    deployment_duration_ms: int
    service_startup_time_ms: int
    health_check_passed: bool
    smoke_tests_passed: bool
    regression_detected: bool
    regression_report: Optional[RegressionReport]
    log_analysis: LogAnalysis
    verification_timestamp: datetime
    error: Optional[str]
    severity: str  # "ok", "warning", "error", "critical"
    
@dataclass
class RegressionReport:
    """Comparison staging vs. production."""
    endpoints_tested: int
    regressions_found: int
    performance_degradation: Dict[str, float]  # endpoint → % slower
    breaking_changes: List[str]
    recommendations: List[str]

@dataclass
class LogAnalysis:
    """Analysis of service logs."""
    errors_found: int
    warnings_found: int
    critical_issues: List[str]
    suspicious_patterns: List[str]
```

### 3. RollbackCoordinator (Failure Handler)

```python
class RollbackCoordinator:
    """Handle failures during staging verification."""
    
    async def rollback_deployment(
        self,
        feature_branch: str,
        verification_result: StagingVerificationResult,
        reason: str
    ) → RollbackResult:
        """
        Revert changes if staging fails.
        
        Steps:
        1. Revert merge (git revert)
        2. Stop staging services
        3. Clean up feature branch
        4. Create incident report
        5. Notify developers
        """
        
    async def revert_merge(self) → bool:
        """git revert commit_sha."""
    
    async def stop_staging_services(self) → bool:
        """SSH: stackctl stop."""
    
    async def cleanup_branches(self, feature_branch: str) → bool:
        """Delete feature & temporary branches."""
    
    def create_incident_report(self) → IncidentReport:
        """Generate detailed failure analysis."""
```

### 4. DeploymentTracker (Audit)

```python
class DeploymentTracker:
    """Track all deployments for audit + learning."""
    
    def record_deployment(
        self,
        agent_id: str,
        branch: str,
        commit_sha: str,
        status: str,  # "success", "failed", "rolled_back"
        duration_sec: int,
        cost_estimate: float
    ) → DeploymentRecord:
        """Record deployment in audit trail."""
        # Stored in: ~/.kicli/deployments.json
        # Or: centralized metrics database
    
    def get_deployment_stats(self) → DeploymentStats:
        """Get aggregate statistics."""
        # Total deployments
        # Success rate
        # Average duration
        # Most common failures
        # Cost trends
```

---

## API Endpoints

### REST Endpoints

```python
@app.post("/api/agent/deployment/prepare")
async def prepare_deployment(request: PreparementRequest) → DeploymentPrepareResult:
    """Prepare code for staging."""
    # Request: {feature_branch, agent_id, description}
    # Response: Merge success, health checks, ready for staging?

@app.post("/api/agent/deployment/verify-staging")
async def verify_staging_deployment(manifest: StagingManifest) → StagingVerificationResult:
    """Send manifest to staging for verification."""
    # Calls StagingVerifier on remote host
    # Waits for result (can be long operation)
    # Returns complete verification result

@app.get("/api/agent/deployment/status/{deployment_id}")
async def get_deployment_status(deployment_id: str) → DeploymentStatus:
    """Check status of ongoing deployment."""
    # Real-time progress updates

@app.get("/api/agent/deployment/audit")
async def get_deployment_audit() → List[DeploymentRecord]:
    """Get audit trail of all deployments."""
```

### Async Message Queue (Optional)

For long-running deployments:

```python
# Producer (local)
async def queue_staging_verification(manifest: StagingManifest):
    await message_queue.publish("staging.verify", manifest)

# Consumer (staging host)
async def consumer_staging_verification():
    async for manifest in message_queue.subscribe("staging.verify"):
        result = await verifier.verify_deployment(manifest)
        await message_queue.publish("staging.verify.result", result)
```

---

## Integration with Phase 5.5.1 & 5.5.2

### CodeImplementationAgent Extension

```python
class CodeImplementationAgent:
    
    async def apply_with_full_autonomy_and_deploy(
        self,
        goal_id: str,
        goal_title: str,
        description: str,
        deploy_to_staging: bool = True
    ) → FullAutonomyResult:
        """
        Extended autonomy: Code → Git → Staging → Verify
        
        Returns same as apply_with_full_autonomy, plus:
        - deployment_prepare_result
        - staging_verification_result
        - deployment_record
        """
        
        # Step 1: Execute refactoring (Phase 5.5.1)
        refactoring_result = await self.apply_multi_file_refactoring(...)
        
        if not refactoring_result.success:
            return failure_result
        
        # Step 2: Record reasoning (Phase 5.5.2)
        # (already integrated)
        
        # Step 3: Deploy to staging (Phase 5.5.3)
        if deploy_to_staging:
            deployment_prep = await self.coordinator.prepare_for_staging(
                refactoring_result.branch_name,
                goal_id,
                description
            )
            
            if deployment_prep.success:
                staging_result = await self.verifier.verify_deployment(
                    deployment_prep.staging_manifest
                )
            
            return FullAutonomyResult(
                refactoring=refactoring_result,
                deployment_prep=deployment_prep,
                staging_verify=staging_result
            )
```

---

## Multi-Host Setup Example

```
Developer Machine (Local)
├─ kicli-code-assist/.venv
├─ stackctl -t local (port 5173, 8000)
├─ DeploymentCoordinator (runs locally)
└─ Git remote: https://github.com/uvlightdrops/kicli-code-assist

Staging Machine (2nd dev machine)
├─ kicli-code-assist/.venv
├─ stackctl -t local (staging environment)
├─ StagingVerifier (runs on this host)
├─ Git pull from main repo
└─ SSH accessible from dev machine
```

**Agent Workflow:**
1. Local: Refactor + test
2. Local: Merge to devel
3. Local: Health check
4. Staging (SSH): Git pull → stackctl start → smoke tests
5. Result: Verified or rolled back

---

## Success Criteria

- ✅ DeploymentCoordinator prepares code safely
- ✅ StagingVerifier deploys without manual intervention
- ✅ Timeout-based health checks (don't hang)
- ✅ Regression detection catches breaking changes
- ✅ Rollback automatic if staging fails
- ✅ Full audit trail + incident reports
- ✅ <5 min from commit to staging verification
- ✅ Zero manual SSH steps (fully automated)

---

## Files to Create

```
kicli_code_assist/agent/
├── deployment_coordinator.py
├── staging_verifier.py
├── rollback_coordinator.py
├── deployment_tracker.py
└── orchestration_integration.py
```

Plus remote deployment scripts on staging host.

---

## Next Steps

1. Implement coordination modules
2. Set up SSH access to staging host
3. Test end-to-end: code → staging → verify
4. Measure time: prepare + verify duration
5. Handle failure scenarios + rollback
6. Integrate with frontend for visibility

---
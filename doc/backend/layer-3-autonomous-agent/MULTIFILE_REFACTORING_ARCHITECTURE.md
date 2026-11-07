---
title: Multi-File Refactoring Coordinator
project: kicli-code-assist
agent_project: kicli-code-assist
scope: Backend Architecture / Layer 3 Autonomous Agents / Phase 5.5.1
purpose: Design multi-file refactoring coordination for Phase 5.5.1
created: 2026-11-02T00:10:00+01:00
updated: 2026-11-07T12:38:00+01:00
update_reason: Upgraded to semantic schema
status: stable

semantic_blocks:
  - id: refactoring-coordinator
    type: architecture
    status: stable
    version: 1.0

relations:
  - target: README
    type: part-of
    reason: "Phase 5.5.1 multi-file refactoring capability"
    
  - target: AGENT_COORDINATION_ARCHITECTURE
    type: depends-on
    reason: "Uses base agent coordination from 6-stage pipeline"
---

# Multi-File Refactoring Coordinator (Phase 5.5.1)

## Module Overview

Extends agent autonomy to handle refactorings spanning multiple files atomically.

## Architecture

```
MultiFileRefactoringAgent
├── RefactoringAnalyzer
│   ├── analyze_impact()      # Find affected files
│   ├── build_dependency_graph()
│   └── suggest_order()       # Safe change order
├── MultiFileCoordinator
│   ├── execute_refactoring() # Orchestrate changes
│   └── track_changes()
└── ImportResolver
    ├── update_imports()      # Fix import statements
    └── validate_chain()      # Check consistency
```

## Core Classes

### RefactoringAnalyzer

```python
class RefactoringAnalyzer:
    """Analyze code to find refactoring impacts."""
    
    def analyze_impact(
        self,
        project_root: str,
        entity_type: str,  # "class", "function", "constant"
        entity_name: str,  # Name to rename/move/refactor
        new_name: Optional[str] = None
    ) -> RefactoringImpact:
        """Find all files that use this entity."""
        # Returns: {files, definitions, usages, imports, dependencies}
    
    def build_dependency_graph(
        self,
        affected_files: List[str]
    ) -> nx.DiGraph:
        """Create dependency graph showing which file depends on which."""
        # Returns: Directed graph for topological sort
    
    def suggest_change_order(
        self,
        graph: nx.DiGraph,
        entity_location: str
    ) -> List[str]:
        """Determine safe order: dependencies first, then dependents."""
        # Returns: Ordered list of files to update
```

### MultiFileCoordinator

```python
class MultiFileCoordinator:
    """Coordinate atomic changes across multiple files."""
    
    async def execute_refactoring(
        self,
        goal_id: str,
        changes: List[FileChange],
        project_root: str,
        branch_name: str
    ) -> RefactoringResult:
        """Apply refactoring atomically: all succeed or all rollback."""
        
        # Flow:
        # 1. Create feature branch
        # 2. For each file (in safe order):
        #    - Generate changes via LLM
        #    - Verify syntax + imports
        #    - Apply changes
        # 3. Run full test suite
        # 4. If all pass: commit; else: rollback
```

### ImportResolver

```python
class ImportResolver:
    """Manage imports when code is refactored."""
    
    def update_imports(
        self,
        file_path: str,
        old_entity: str,
        new_entity: str,
        old_module: Optional[str] = None,
        new_module: Optional[str] = None
    ) -> str:
        """Update import statements in file."""
        # Changes:
        # from old_module import OldClass
        # → from new_module import NewClass
    
    def validate_import_chain(
        self,
        file_path: str
    ) -> List[str]:
        """Check for circular imports or missing dependencies."""
        # Returns: List of errors (or empty if OK)
```

## Data Structures

```python
@dataclass
class RefactoringImpact:
    """Analysis result: what needs to change."""
    entity_type: str
    entity_name: str
    files_with_definition: List[str]  # Where it's defined
    files_with_usage: List[str]       # Where it's used
    files_with_imports: List[str]     # Where it's imported
    total_affected_files: int
    dependency_graph: nx.DiGraph
    suggested_order: List[str]

@dataclass
class FileChange:
    """One file's worth of changes."""
    file_path: str
    old_content: str
    new_content: str
    change_type: str  # "rename", "move", "refactor", etc.
    reasoning: str

@dataclass
class RefactoringResult:
    """Result of multi-file refactoring."""
    success: bool
    goal_id: str
    branch_name: str
    commit_sha: Optional[str]
    files_changed: int
    test_results: TestRunResult
    changes: List[FileChange]
    duration_ms: int
    error: Optional[str]
    rollback_performed: bool
```

## Integration Points

### 1. Extend CodeImplementationAgent

```python
class CodeImplementationAgent:
    
    async def apply_multi_file_refactoring(
        self,
        goal_id: str,
        goal_title: str,
        refactoring_type: str,  # "rename_class", "extract_function", etc.
        entity_name: str,
        new_name: Optional[str] = None,
        description: str = "",
        project_root: str = "{root}"
    ) -> RefactoringResult:
        """Generate and apply multi-file refactoring."""
        
        # 1. Analyze impact
        analyzer = RefactoringAnalyzer()
        impact = analyzer.analyze_impact(
            project_root, entity_type, entity_name
        )
        
        # 2. Generate changes via LLM (for each file)
        coordinator = MultiFileCoordinator()
        result = await coordinator.execute_refactoring(...)
        
        # 3. Return result with audit trail
        return result
```

### 2. Extend MetaCoordinationAgent

```python
def _determine_workflow(self, intent: AgentIntent) -> str:
    """Return workflow type based on intent."""
    
    if intent["type"] == "multi_file_refactoring":
        return WorkflowType.REFACTORING  # New workflow type
    
    # ... existing workflows ...
```

### 3. Extend TestRunner

```python
class TestRunner:
    
    def validate_cross_file_consistency(
        self,
        project_root: str,
        changed_files: List[str]
    ) -> TestRunResult:
        """Run tests that validate changes across files."""
        
        # - Import resolution tests
        # - API compatibility tests
        # - Database migration tests
        # - End-to-end tests
```

## API Endpoints

### New REST Endpoint

```python
@app.post("/api/agent/refactor")
async def refactor_code(request: RefactorRequest) -> RefactoringResult:
    """
    Execute multi-file refactoring.
    
    Request:
    {
        "goal_id": "refactor-user-model",
        "goal_title": "Rename UserAccount to User",
        "refactoring_type": "rename_class",
        "entity_name": "UserAccount",
        "new_name": "User",
        "description": "Simplify class name across codebase"
    }
    
    Response:
    {
        "success": true,
        "files_changed": 7,
        "commit_sha": "abc123...",
        "test_results": {...},
        "changes": [...]
    }
    """
```

## Testing Strategy

### Unit Tests

```python
# test_refactoring_analyzer.py
def test_analyze_impact_finds_all_usages():
    """Analyzer finds all files using entity."""

def test_suggest_change_order():
    """Dependencies updated before dependents."""

# test_import_resolver.py
def test_update_imports_simple_rename():
    """Simple import update works."""

def test_update_imports_module_move():
    """Moving file updates imports correctly."""

def test_circular_import_detection():
    """Detects and reports circular imports."""

# test_multi_file_coordinator.py
def test_execute_refactoring_atomic():
    """All files changed or none (atomic)."""

def test_rollback_on_test_failure():
    """Failed tests trigger rollback."""

def test_commit_message_details():
    """Commit includes all changed files."""
```

### Integration Tests

```python
# Integration: full refactoring workflow
def test_rename_class_across_5_files():
    """Real-world scenario: rename class in models + imports."""
    
    # Create test project with:
    # - models.py: class UserAccount
    # - api.py: from models import UserAccount
    # - services.py: uses UserAccount
    # - tests/: tests importing UserAccount
    
    # Run refactoring
    # Verify: all imports updated, tests pass
```

## Success Criteria

- ✅ Analyzer correctly identifies all file impacts
- ✅ Import resolver handles 10+ import styles
- ✅ Coordinator runs atomically (all or nothing)
- ✅ Tests pass after refactoring
- ✅ Rollback works perfectly
- ✅ Handles circular import detection
- ✅ Real-world refactoring: rename UserAccount → User (7+ files)

## Files to Create/Modify

```
kicli_code_assist/agent/
├── refactoring_analyzer.py        # NEW
├── multi_file_coordinator.py      # NEW
├── import_resolver.py             # NEW
├── code_implementation.py          # MODIFY: add multi-file method
├── meta_coordinator.py             # MODIFY: add workflow type
└── test_runner.py                 # MODIFY: cross-file validation
```

---


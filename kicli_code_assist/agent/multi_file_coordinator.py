"""
Multi-file coordinator: Orchestrate atomic changes across multiple files.

Ensures atomicity: all files updated successfully or all rolled back.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional
import asyncio

from kicli_code_assist.agent.refactoring_analyzer import RefactoringAnalyzer, RefactoringImpact
from kicli_code_assist.agent.import_resolver import ImportResolver, ImportIssue
from kicli_code_assist.agent.git_manager import GitManager
from kicli_code_assist.agent.test_runner import TestRunner
from kicli_code_assist.agent.code_quality import CodeQualityChecker
from kicli_code_assist.agent.rollback_manager import RollbackManager
from kicli_code_assist.agent.implementation_state import ImplementationStateManager

logger = logging.getLogger("kicli-agent")


@dataclass
class FileChange:
    """One file's worth of changes."""
    file_path: str
    old_content: str
    new_content: str
    change_type: str  # "rename", "move", "refactor", "update_import"
    reasoning: str


@dataclass
class RefactoringResult:
    """Result of multi-file refactoring."""
    success: bool
    goal_id: str
    branch_name: str
    commit_sha: Optional[str]
    files_changed: int
    test_results: Optional[dict]  # TestRunResult
    changes: List[FileChange]
    duration_ms: int
    error: Optional[str]
    rollback_performed: bool
    impact_analysis: Optional[RefactoringImpact] = None
    import_issues: List[ImportIssue] = None


class MultiFileCoordinator:
    """Coordinate atomic changes across multiple files."""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.analyzer = RefactoringAnalyzer(project_root)
        self.import_resolver = ImportResolver(project_root)
        self.git_manager = GitManager(project_root)
        self.test_runner = TestRunner(project_root)
        self.quality_checker = CodeQualityChecker()
        self.rollback_manager = RollbackManager()
        self.state_manager = ImplementationStateManager()
    
    async def execute_refactoring(
        self,
        goal_id: str,
        refactoring_type: str,
        entity_name: str,
        new_entity_name: Optional[str] = None,
        description: str = "",
        branch_name: Optional[str] = None
    ) -> RefactoringResult:
        """
        Execute multi-file refactoring atomically.
        
        Flow:
        1. Analyze impact (which files affected)
        2. Create feature branch & capture rollback state
        3. For each file in safe order:
           - Generate changes (via LLM or deterministic rules)
           - Verify syntax + imports
           - Apply changes
        4. Run full test suite
        5. If all pass: commit; else: rollback
        
        Args:
            goal_id: Unique ID for this refactoring
            refactoring_type: "rename_class", "rename_function", "move_module", etc.
            entity_name: Original name
            new_entity_name: New name (if renaming)
            description: Why this refactoring
            branch_name: Git branch (auto-generated if None)
            
        Returns:
            RefactoringResult with success/failure info
        """
        import time
        start_time = time.time()
        
        logger.info(f"Starting refactoring: {refactoring_type} '{entity_name}'")
        
        # Track state
        self.state_manager.start_implementation(goal_id, f"Refactor {entity_name}", self.project_root)
        
        branch_name = branch_name or f"refactor/{entity_name.lower()}"
        changes = []
        
        try:
            # Step 1: Analyze impact
            logger.info("Step 1: Analyzing impact...")
            impact = self.analyzer.analyze_impact(
                entity_type=self._refactoring_to_entity_type(refactoring_type),
                entity_name=entity_name
            )
            
            if impact.total_affected_files == 0:
                logger.warning(f"Entity '{entity_name}' not found in project")
                return RefactoringResult(
                    success=False,
                    goal_id=goal_id,
                    branch_name=branch_name,
                    commit_sha=None,
                    files_changed=0,
                    test_results=None,
                    changes=[],
                    duration_ms=int((time.time() - start_time) * 1000),
                    error=f"Entity '{entity_name}' not found",
                    rollback_performed=False,
                    impact_analysis=impact
                )
            
            logger.info(f"Impact analysis: {impact.total_affected_files} files affected")
            
            # Step 2: Prepare rollback & create branch
            logger.info("Step 2: Creating feature branch...")
            self.rollback_manager.prepare_rollback(goal_id, branch_name)
            self.git_manager.create_branch(branch_name)
            
            # Step 3: Apply changes to each file (in safe order)
            logger.info("Step 3: Applying changes...")
            for file_path in impact.suggested_change_order:
                logger.debug(f"  Processing {file_path}...")
                
                try:
                    # Read original
                    with open(f"{self.project_root}/{file_path}", "r") as f:
                        original_content = f.read()
                    
                    # Determine change type
                    if file_path in impact.files_with_definition:
                        change_type = "rename_definition"
                    elif file_path in impact.files_with_import:
                        change_type = "update_import"
                    else:
                        change_type = "update_usage"
                    
                    # Apply change (deterministic rule-based or LLM)
                    new_content = self._apply_change(
                        original_content,
                        refactoring_type,
                        entity_name,
                        new_entity_name,
                        file_path,
                        change_type
                    )
                    
                    # Verify syntax
                    if not self._verify_syntax(new_content, file_path):
                        raise Exception(f"Syntax error after refactoring {file_path}")
                    
                    # Write change
                    with open(f"{self.project_root}/{file_path}", "w") as f:
                        f.write(new_content)
                    
                    # Track change
                    changes.append(FileChange(
                        file_path=file_path,
                        old_content=original_content,
                        new_content=new_content,
                        change_type=change_type,
                        reasoning=f"Refactor {refactoring_type}: {entity_name} → {new_entity_name}"
                    ))
                    
                    logger.debug(f"  ✓ {file_path}")
                
                except Exception as e:
                    logger.error(f"Error applying change to {file_path}: {e}")
                    raise
            
            # Step 4: Validate imports
            logger.info("Step 4: Validating imports...")
            all_import_issues = []
            for file_path in impact.all_affected_files:
                issues = self.import_resolver.validate_import_chain(file_path)
                all_import_issues.extend(issues)
            
            if any(issue.severity == "error" for issue in all_import_issues):
                raise Exception(f"Import validation failed: {all_import_issues}")
            
            # Step 5: Run tests
            logger.info("Step 5: Running tests...")
            self.git_manager.add_files(impact.all_affected_files)
            test_result = self.test_runner.run_tests()
            
            if not test_result.success:
                raise Exception(f"Tests failed: {test_result.summary}")
            
            # Step 6: Code quality check
            logger.info("Step 6: Checking code quality...")
            quality_result = self.quality_checker.run_all_checks(
                [f"{self.project_root}/{f}" for f in changes[0:1]]  # Sample check
            )
            
            if quality_result.should_block_commit:
                logger.warning("Code quality issues detected (non-blocking)")
            
            # Step 7: Commit
            logger.info("Step 7: Committing changes...")
            commit_msg = f"{refactoring_type}: {entity_name} → {new_entity_name or entity_name}\n\n"
            commit_msg += f"Files changed: {', '.join(f.file_path for f in changes)}\n"
            commit_msg += description
            
            commit_sha = self.git_manager.commit_changes(
                [f.file_path for f in changes],
                commit_msg
            )
            
            # Step 8: Push
            logger.info("Step 8: Pushing changes...")
            self.git_manager.push_to_remote(branch_name)
            
            # Success!
            duration_ms = int((time.time() - start_time) * 1000)
            self.state_manager.complete_implementation(goal_id, {
                "branch": branch_name,
                "commit_sha": commit_sha,
                "files_changed": len(changes),
                "test_results": test_result.summary,
                "duration_ms": duration_ms
            })
            
            logger.info(f"Refactoring complete: {len(changes)} files changed, {duration_ms}ms")
            
            return RefactoringResult(
                success=True,
                goal_id=goal_id,
                branch_name=branch_name,
                commit_sha=commit_sha,
                files_changed=len(changes),
                test_results=test_result.summary,
                changes=changes,
                duration_ms=duration_ms,
                error=None,
                rollback_performed=False,
                impact_analysis=impact,
                import_issues=all_import_issues
            )
        
        except Exception as e:
            logger.error(f"Refactoring failed: {e}")
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Rollback
            try:
                logger.info("Rolling back changes...")
                self.rollback_manager.rollback_implementation(goal_id)
                self.git_manager.delete_branch(branch_name)
                rollback_performed = True
            except Exception as e2:
                logger.error(f"Rollback also failed: {e2}")
                rollback_performed = False
            
            self.state_manager.fail_implementation(goal_id, str(e))
            
            return RefactoringResult(
                success=False,
                goal_id=goal_id,
                branch_name=branch_name,
                commit_sha=None,
                files_changed=len(changes),
                test_results=None,
                changes=changes,
                duration_ms=duration_ms,
                error=str(e),
                rollback_performed=rollback_performed,
                impact_analysis=None
            )
    
    def _refactoring_to_entity_type(self, refactoring_type: str) -> str:
        """Map refactoring type to entity type."""
        if "class" in refactoring_type or "Class" in refactoring_type:
            return "class"
        elif "function" in refactoring_type or "Function" in refactoring_type:
            return "function"
        elif "module" in refactoring_type or "Module" in refactoring_type:
            return "module"
        else:
            return "class"  # Default
    
    def _apply_change(
        self,
        content: str,
        refactoring_type: str,
        entity_name: str,
        new_entity_name: Optional[str],
        file_path: str,
        change_type: str
    ) -> str:
        """Apply deterministic refactoring change."""
        # For now: simple string replacement
        # In future: use AST-based transformation for precision
        
        if refactoring_type == "rename_class" and new_entity_name:
            # Replace class definition
            content = content.replace(f"class {entity_name}", f"class {new_entity_name}")
            
            # Use import resolver for imports
            content = self.import_resolver.update_imports(
                file_path,
                entity_name,
                new_entity_name
            )
        
        return content
    
    def _verify_syntax(self, content: str, file_path: str) -> bool:
        """Check Python syntax is valid."""
        try:
            import ast
            ast.parse(content)
            return True
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            return False

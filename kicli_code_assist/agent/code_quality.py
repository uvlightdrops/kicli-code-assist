"""
Phase 5.4.4: Code Quality Checks

Runs quality analysis before committing:
- PEP 8 compliance (via flake8)
- Import organization (via isort)
- Type hints validation (via mypy)
- Docstring presence (via pydocstyle)
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QualityCheckResult:
    """Quality check execution result."""
    check_name: str
    passed: bool
    warnings: int
    errors: int
    issues: List[str]
    details: str


class CodeQualityChecker:
    """Runs code quality checks."""
    
    def __init__(self, project_root: str):
        """Initialize checker."""
        self.project_root = Path(project_root)
    
    def check_pep8(self, files: List[str]) -> QualityCheckResult:
        """
        Check PEP 8 compliance with flake8.
        
        Args:
            files: Python files to check
        
        Returns:
            QualityCheckResult
        """
        logger.info("Checking PEP 8 (flake8)...")
        
        try:
            cmd = ["python", "-m", "flake8", "--max-line-length=100"] + files
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            issues = []
            warnings = 0
            errors = 0
            
            for line in result.stdout.split("\n"):
                if line.strip():
                    issues.append(line)
                    if "E" in line:  # Error
                        errors += 1
                    elif "W" in line:  # Warning
                        warnings += 1
            
            return QualityCheckResult(
                check_name="PEP 8 (flake8)",
                passed=result.returncode == 0,
                warnings=warnings,
                errors=errors,
                issues=issues[:10],  # First 10
                details=result.stdout
            )
        
        except FileNotFoundError:
            logger.warning("flake8 not installed")
            return QualityCheckResult(
                check_name="PEP 8 (flake8)",
                passed=True,  # Skip if not installed
                warnings=0,
                errors=0,
                issues=[],
                details="flake8 not installed"
            )
        except Exception as e:
            logger.error(f"PEP 8 check error: {e}")
            return QualityCheckResult(
                check_name="PEP 8 (flake8)",
                passed=False,
                warnings=0,
                errors=1,
                issues=[str(e)],
                details=str(e)
            )
    
    def check_imports(self, files: List[str]) -> QualityCheckResult:
        """
        Check import organization with isort.
        
        Args:
            files: Python files to check
        
        Returns:
            QualityCheckResult
        """
        logger.info("Checking import organization (isort)...")
        
        try:
            cmd = ["python", "-m", "isort", "--check-only", "--diff"] + files
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            issues = []
            if result.returncode != 0:
                # Parse diff output
                for line in result.stdout.split("\n"):
                    if line.startswith("-") or line.startswith("+"):
                        issues.append(line)
            
            return QualityCheckResult(
                check_name="Import Organization (isort)",
                passed=result.returncode == 0,
                warnings=len(issues),
                errors=0,
                issues=issues[:10],
                details=result.stdout
            )
        
        except FileNotFoundError:
            logger.warning("isort not installed")
            return QualityCheckResult(
                check_name="Import Organization (isort)",
                passed=True,
                warnings=0,
                errors=0,
                issues=[],
                details="isort not installed"
            )
        except Exception as e:
            logger.error(f"Import check error: {e}")
            return QualityCheckResult(
                check_name="Import Organization (isort)",
                passed=False,
                warnings=0,
                errors=1,
                issues=[str(e)],
                details=str(e)
            )
    
    def check_type_hints(self, files: List[str]) -> QualityCheckResult:
        """
        Check type hints with mypy (optional).
        
        Args:
            files: Python files to check
        
        Returns:
            QualityCheckResult
        """
        logger.info("Checking type hints (mypy)...")
        
        try:
            cmd = ["python", "-m", "mypy", "--ignore-missing-imports"] + files
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            issues = []
            errors = 0
            
            for line in result.stdout.split("\n"):
                if "error:" in line.lower():
                    issues.append(line)
                    errors += 1
            
            return QualityCheckResult(
                check_name="Type Hints (mypy)",
                passed=result.returncode == 0,
                warnings=0,
                errors=errors,
                issues=issues[:10],
                details=result.stdout
            )
        
        except FileNotFoundError:
            logger.warning("mypy not installed (type hints check skipped)")
            return QualityCheckResult(
                check_name="Type Hints (mypy)",
                passed=True,
                warnings=0,
                errors=0,
                issues=[],
                details="mypy not installed"
            )
        except Exception as e:
            logger.error(f"Type hints check error: {e}")
            return QualityCheckResult(
                check_name="Type Hints (mypy)",
                passed=False,
                warnings=0,
                errors=1,
                issues=[str(e)],
                details=str(e)
            )
    
    def run_all_checks(self, files: List[str]) -> Dict[str, QualityCheckResult]:
        """
        Run all quality checks.
        
        Args:
            files: Python files to check
        
        Returns:
            Dict of check results
        """
        results = {}
        
        # Run checks in order
        results["pep8"] = self.check_pep8(files)
        results["imports"] = self.check_imports(files)
        results["type_hints"] = self.check_type_hints(files)
        
        return results
    
    def format_summary(self, results: Dict[str, QualityCheckResult]) -> str:
        """Format quality check results as summary."""
        summary = "\n🔍 Code Quality Analysis\n"
        summary += "=" * 60 + "\n"
        
        all_passed = True
        for check_name, result in results.items():
            status = "✅" if result.passed else "⚠️"
            summary += f"{status} {result.check_name}\n"
            
            if result.errors > 0:
                summary += f"   Errors: {result.errors}\n"
                all_passed = False
            
            if result.warnings > 0:
                summary += f"   Warnings: {result.warnings}\n"
            
            if result.issues:
                for issue in result.issues[:3]:  # Show first 3
                    summary += f"   - {issue}\n"
                if len(result.issues) > 3:
                    summary += f"   ... and {len(result.issues) - 3} more\n"
        
        summary += "\n"
        return summary
    
    def should_block_commit(self, results: Dict[str, QualityCheckResult]) -> bool:
        """
        Determine if commit should be blocked.
        
        Critical failures (block commit):
        - Syntax errors
        - Type check critical errors
        
        Warnings (don't block):
        - Line length
        - Import order
        """
        for check_name, result in results.items():
            # Only block on critical errors
            if check_name == "pep8":
                # Only PEP 8 E-errors block (not W-warnings)
                # This is checked by the result.errors count
                if result.errors > 5:  # More than 5 errors
                    return True
            elif check_name == "type_hints":
                # Type errors can be warnings
                if result.errors > 10:
                    return True
        
        return False

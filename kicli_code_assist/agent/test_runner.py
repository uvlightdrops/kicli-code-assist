"""
Phase 5.4.2: Automated Test Execution

Runs tests to verify implementation works:
- Auto-detect test framework (pytest, unittest, tox)
- Execute tests with full output
- Parse results and report failures
- Block push if critical tests fail
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TestFramework(Enum):
    """Supported test frameworks."""
    PYTEST = "pytest"
    UNITTEST = "unittest"
    TOX = "tox"
    UNKNOWN = "unknown"


@dataclass
class TestResult:
    """Represents test execution result."""
    framework: TestFramework
    passed: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    errors: List[str]
    failures: List[str]
    stdout: str
    stderr: str
    duration_seconds: float


class TestRunner:
    """Runs and analyzes automated tests."""
    
    def __init__(self, project_root: str):
        """Initialize test runner for project."""
        self.project_root = Path(project_root)
    
    def detect_test_framework(self) -> TestFramework:
        """
        Auto-detect which test framework is used.
        
        Returns:
            Detected TestFramework enum
        """
        # Check for pytest.ini or setup.cfg with pytest
        if (self.project_root / "pytest.ini").exists():
            logger.info("Detected pytest (pytest.ini found)")
            return TestFramework.PYTEST
        
        # Check for tox.ini
        if (self.project_root / "tox.ini").exists():
            logger.info("Detected tox (tox.ini found)")
            return TestFramework.TOX
        
        # Check for test directories
        test_dirs = ["tests", "test"]
        for test_dir in test_dirs:
            test_path = self.project_root / test_dir
            if test_path.exists() and test_path.is_dir():
                # Check if tests use pytest conventions
                test_files = list(test_path.glob("test_*.py"))
                if test_files:
                    logger.info(f"Detected pytest (test_*.py files in {test_dir})")
                    return TestFramework.PYTEST
        
        # Check for unittest
        for py_file in self.project_root.glob("**/test*.py"):
            try:
                content = py_file.read_text()
                if "import unittest" in content or "from unittest" in content:
                    logger.info("Detected unittest")
                    return TestFramework.UNITTEST
            except:
                pass
        
        logger.warning("Could not detect test framework")
        return TestFramework.UNKNOWN
    
    def run_pytest(self) -> TestResult:
        """Run pytest tests."""
        logger.info("Running pytest...")
        
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "-v", "--tb=short"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            stdout = result.stdout
            stderr = result.stderr
            
            # Parse results
            passed = 0
            failed = 0
            skipped = 0
            failures = []
            errors = []
            
            # Simple parsing of pytest output
            for line in stdout.split("\n"):
                if " PASSED" in line:
                    passed += 1
                elif " FAILED" in line:
                    failed += 1
                    failures.append(line.split(":")[0].strip())
                elif " SKIPPED" in line:
                    skipped += 1
                elif " ERROR" in line:
                    errors.append(line)
            
            return TestResult(
                framework=TestFramework.PYTEST,
                passed=result.returncode == 0,
                total_tests=passed + failed + skipped,
                passed_tests=passed,
                failed_tests=failed,
                skipped_tests=skipped,
                errors=errors,
                failures=failures,
                stdout=stdout,
                stderr=stderr,
                duration_seconds=0.0
            )
        
        except subprocess.TimeoutExpired:
            logger.error("Pytest timed out after 300 seconds")
            return TestResult(
                framework=TestFramework.PYTEST,
                passed=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                errors=["Pytest timed out"],
                failures=[],
                stdout="",
                stderr="Timeout",
                duration_seconds=300
            )
        except Exception as e:
            logger.error(f"Failed to run pytest: {e}")
            return TestResult(
                framework=TestFramework.PYTEST,
                passed=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                errors=[str(e)],
                failures=[],
                stdout="",
                stderr=str(e),
                duration_seconds=0
            )
    
    def run_unittest(self) -> TestResult:
        """Run unittest tests."""
        logger.info("Running unittest...")
        
        try:
            result = subprocess.run(
                ["python", "-m", "unittest", "discover", "-v"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            stdout = result.stdout
            stderr = result.stderr
            
            # Parse unittest output
            passed = 0
            failed = 0
            skipped = 0
            failures = []
            
            for line in stdout.split("\n"):
                if line.startswith("test") and " ... ok" in line:
                    passed += 1
                elif line.startswith("test") and " ... FAIL" in line:
                    failed += 1
                    failures.append(line.split(" ")[0])
                elif line.startswith("test") and " ... skip" in line:
                    skipped += 1
            
            return TestResult(
                framework=TestFramework.UNITTEST,
                passed=result.returncode == 0,
                total_tests=passed + failed + skipped,
                passed_tests=passed,
                failed_tests=failed,
                skipped_tests=skipped,
                errors=[],
                failures=failures,
                stdout=stdout,
                stderr=stderr,
                duration_seconds=0
            )
        
        except Exception as e:
            logger.error(f"Failed to run unittest: {e}")
            return TestResult(
                framework=TestFramework.UNITTEST,
                passed=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                errors=[str(e)],
                failures=[],
                stdout="",
                stderr=str(e),
                duration_seconds=0
            )
    
    def run_tox(self) -> TestResult:
        """Run tox tests."""
        logger.info("Running tox...")
        
        try:
            result = subprocess.run(
                ["tox"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            stdout = result.stdout
            stderr = result.stderr
            
            return TestResult(
                framework=TestFramework.TOX,
                passed=result.returncode == 0,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                errors=[] if result.returncode == 0 else ["Tox failed"],
                failures=[],
                stdout=stdout,
                stderr=stderr,
                duration_seconds=0
            )
        
        except Exception as e:
            logger.error(f"Failed to run tox: {e}")
            return TestResult(
                framework=TestFramework.TOX,
                passed=False,
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                errors=[str(e)],
                failures=[],
                stdout="",
                stderr=str(e),
                duration_seconds=0
            )
    
    def run_tests(self) -> TestResult:
        """
        Run tests using detected framework.
        
        Returns:
            TestResult with execution details
        """
        framework = self.detect_test_framework()
        
        if framework == TestFramework.PYTEST:
            return self.run_pytest()
        elif framework == TestFramework.UNITTEST:
            return self.run_unittest()
        elif framework == TestFramework.TOX:
            return self.run_tox()
        else:
            logger.warning("No tests detected")
            return TestResult(
                framework=TestFramework.UNKNOWN,
                passed=True,  # Don't block if no tests
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                errors=["No tests found"],
                failures=[],
                stdout="",
                stderr="",
                duration_seconds=0
            )
    
    def format_result_summary(self, result: TestResult) -> str:
        """Format test result as human-readable summary."""
        summary = f"""
🧪 Test Results ({result.framework.value})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status:       {'✅ PASSED' if result.passed else '❌ FAILED'}
Total:        {result.total_tests}
Passed:       {result.passed_tests}
Failed:       {result.failed_tests}
Skipped:      {result.skipped_tests}
"""
        
        if result.failures:
            summary += f"\n⚠️  Failed tests:\n"
            for failure in result.failures[:5]:  # Show first 5
                summary += f"   - {failure}\n"
            if len(result.failures) > 5:
                summary += f"   ... and {len(result.failures) - 5} more\n"
        
        if result.errors:
            summary += f"\n🔴 Errors:\n"
            for error in result.errors[:3]:  # Show first 3
                summary += f"   - {error}\n"
        
        return summary

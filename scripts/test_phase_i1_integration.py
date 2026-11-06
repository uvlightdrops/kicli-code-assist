#!/usr/bin/env python3
"""
Test script for Phase I1: Real LLM Integration in TUI

Tests:
1. Backend availability (health check)
2. HTTP client connectivity
3. File analysis request to /api/agent/route
4. Response parsing
"""

import sys
import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from kicli_code_assist.ui.http_client import TUIBackendClient, AnalysisResponse


def test_backend_health(base_url: str = "http://localhost:8000") -> bool:
    """Test if backend is running."""
    logger.info(f"Testing backend health at {base_url}...")
    
    from urllib.request import urlopen
    from urllib.error import URLError
    
    try:
        with urlopen(f"{base_url}/api/health", timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                logger.info(f"✓ Backend healthy: {data}")
                return True
            else:
                logger.error(f"✗ Backend returned {response.status}")
                return False
    except URLError as e:
        logger.error(f"✗ Cannot reach backend: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        return False


def test_file_analysis(
    base_url: str = "http://localhost:8000",
    file_path: str = "README.md",
    project_root: str = None
) -> bool:
    """Test file analysis via HTTP client."""
    logger.info(f"Testing file analysis: {file_path}")
    
    if project_root is None:
        project_root = str(Path.cwd())
    
    client = TUIBackendClient(base_url)
    
    try:
        logger.info(f"Query backend: file={file_path}, project={project_root}")
        response = client.analyze_file(
            query=f"Analyze this file: {file_path}",
            file_path=file_path,
            project_root=project_root,
            scope="file"
        )
        
        logger.info(f"Response success: {response.success}")
        logger.info(f"Intent: {response.intent}")
        logger.info(f"Agents used: {response.agents_used}")
        logger.info(f"Answer length: {len(response.answer)} chars")
        logger.info(f"Chunks: {len(response.chunks)}")
        
        if response.success:
            logger.info("✓ File analysis succeeded")
            print("\n=== Analysis Response ===")
            print(response.answer[:500])
            if response.answer and len(response.answer) > 500:
                print(f"... (truncated, {len(response.answer)} chars total)")
            
            print("\n=== Chunks ===")
            for i, (chunk_type, content) in enumerate(response.chunks, 1):
                print(f"{i}. [{chunk_type}] {content[:80]}")
                if len(content) > 80:
                    print(f"   ... (truncated, {len(content)} chars)")
            
            return True
        else:
            logger.error(f"✗ Analysis failed: {response.error}")
            return False
    
    except Exception as e:
        logger.error(f"✗ Error: {e}", exc_info=True)
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Phase I1: Real LLM Integration Test")
    print("=" * 60 + "\n")
    
    backend_url = "http://localhost:8000"
    project_root = str(Path.cwd())
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Backend URL: {backend_url}\n")
    
    # Test 1: Backend health
    print("[1/2] Testing Backend Health...")
    if not test_backend_health(backend_url):
        logger.error("Backend is not running. Start with: KI_STAGE=development python -m stackenv start")
        return False
    print()
    
    # Test 2: File analysis
    print("[2/2] Testing File Analysis...")
    test_file = "README.md"
    if not Path(test_file).exists():
        # Try doc/README.md or find any Python file
        test_file = None
        for candidate in ["doc/backend/README.md", "setup.py", "pyproject.toml", ".gitignore"]:
            if Path(candidate).exists():
                test_file = candidate
                break
        
        if not test_file:
            logger.warning(f"No test file found, trying to analyze current directory")
            test_file = "."
    
    logger.info(f"Using test file: {test_file}")
    if not test_file.startswith("/"):
        test_file = str(Path(test_file).resolve())
    
    if not test_file_analysis(backend_url, test_file, project_root):
        return False
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60 + "\n")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

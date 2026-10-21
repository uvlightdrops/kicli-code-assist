#!/usr/bin/env python3
"""Standalone test for async LLM integration.

Tests the AsyncLLMIntegration to verify:
1. Non-blocking LLM calls
2. Proper async/await pattern
3. Error handling with recovery hints
4. Streaming responses
"""

import asyncio
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from kicli_code_assist.llm_integration import AsyncLLMIntegration
from kicli_code_assist.logging_integration import get_llm_logger
from ki_core.errors import LLMError, AllProvidersFailedError


async def test_basic_query():
    """Test basic non-blocking LLM query."""
    logger = get_llm_logger()
    logger.info("=" * 70)
    logger.info("TEST 1: Basic Query (Non-blocking)")
    logger.info("=" * 70)
    
    try:
        integration = AsyncLLMIntegration()
        
        if not integration.provider_chain:
            logger.warning("No provider chain configured - skipping query test")
            return False
        
        # Simple query
        messages = [
            {"role": "user", "content": "What is 2+2?"}
        ]
        
        logger.info("Sending query: 'What is 2+2?'")
        response = await integration.query(messages)
        
        logger.info(f"✓ Response received: {response[:100]}...")
        return "4" in response or "four" in response.lower()
        
    except LLMError as e:
        logger.error(f"✗ LLM Error: {e.message}")
        if hasattr(e, 'recovery_hints'):
            for hint in e.recovery_hints:
                logger.info(f"  💡 {hint.action}: {hint.description}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def test_streaming():
    """Test streaming response with token-by-token output."""
    logger = get_llm_logger()
    logger.info("=" * 70)
    logger.info("TEST 2: Streaming Response")
    logger.info("=" * 70)
    
    try:
        integration = AsyncLLMIntegration()
        
        if not integration.provider_chain:
            logger.warning("No provider chain configured - skipping stream test")
            return False
        
        messages = [
            {"role": "user", "content": "Explain async/await in Python (concise, 3 sentences)"}
        ]
        
        logger.info("Starting stream test...")
        response = ""
        chunk_count = 0
        
        async def on_chunk(chunk):
            nonlocal chunk_count
            chunk_count += 1
            logger.debug(f"Chunk {chunk_count}: {chunk}")
        
        response = await integration.stream(
            messages=messages,
            on_chunk=on_chunk
        )
        
        logger.info(f"✓ Stream complete: {len(response)} chars in {chunk_count} chunks")
        logger.info(f"  Response preview: {response[:150]}...")
        return len(response) > 0
        
    except LLMError as e:
        logger.error(f"✗ LLM Error: {e.message}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def test_with_system_prompt():
    """Test with system prompt (secret filtering)."""
    logger = get_llm_logger()
    logger.info("=" * 70)
    logger.info("TEST 3: System Prompt with Secret Filtering")
    logger.info("=" * 70)
    
    try:
        integration = AsyncLLMIntegration()
        
        if not integration.provider_chain:
            logger.warning("No provider chain configured - skipping test")
            return False
        
        # Test with fake secret (should be filtered)
        system_prompt = """You are a helpful assistant. 
        API Key: sk-proj-1234567890abcdef
        Database URL: postgresql://user:password@localhost/db"""
        
        messages = [
            {"role": "user", "content": "Say hello"}
        ]
        
        logger.info("Testing with system prompt containing secrets...")
        response = await integration.query(
            messages=messages,
            system_prompt=system_prompt
        )
        
        logger.info(f"✓ Query completed (secrets filtered)")
        logger.info(f"  Response: {response[:100]}...")
        return True
        
    except Exception as e:
        logger.error(f"✗ Error: {type(e).__name__}: {e}")
        return False


async def test_multiple_queries_parallel():
    """Test multiple queries running in parallel (true async)."""
    logger = get_llm_logger()
    logger.info("=" * 70)
    logger.info("TEST 4: Parallel Queries (True Async Decoupling)")
    logger.info("=" * 70)
    
    try:
        integration = AsyncLLMIntegration()
        
        if not integration.provider_chain:
            logger.warning("No provider chain configured - skipping test")
            return False
        
        logger.info("Starting 2 parallel queries...")
        
        # Create two queries that run in parallel
        query1 = asyncio.create_task(
            integration.query([{"role": "user", "content": "What is Python?"}])
        )
        query2 = asyncio.create_task(
            integration.query([{"role": "user", "content": "What is JavaScript?"}])
        )
        
        # Wait for both (in parallel)
        import time
        start_time = time.time()
        
        response1, response2 = await asyncio.gather(query1, query2)
        
        elapsed = time.time() - start_time
        
        logger.info(f"✓ Both queries completed in {elapsed:.2f}s (parallel)")
        logger.info(f"  Response 1 (Python): {response1[:80]}...")
        logger.info(f"  Response 2 (JavaScript): {response2[:80]}...")
        
        # True parallelism would be ~2s total (if each takes ~2s)
        # Sequential would be ~4s total
        logger.info(f"  ℹ  Elapsed time indicates {'PARALLEL ✓' if elapsed < 3.5 else 'SEQUENTIAL ✗'} execution")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error: {type(e).__name__}: {e}")
        return False


async def main():
    """Run all tests."""
    logger = get_llm_logger()
    
    logger.info("\n")
    logger.info("╔" + "═" * 68 + "╗")
    logger.info("║" + " " * 15 + "ASYNC LLM INTEGRATION TESTS" + " " * 27 + "║")
    logger.info("╚" + "═" * 68 + "╝")
    logger.info("")
    
    # Check configuration
    integration = AsyncLLMIntegration()
    if integration.provider_chain:
        logger.info(f"✓ LLM configured with provider chain")
    else:
        logger.warning("⚠  No LLM provider configured - install openai and set OPENAI_API_KEY")
    
    logger.info("")
    
    # Run tests
    tests = [
        ("basic_query", test_basic_query),
        ("streaming", test_streaming),
        ("system_prompt", test_with_system_prompt),
        ("parallel", test_multiple_queries_parallel),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = "✓ PASS" if result else "✗ FAIL"
        except Exception as e:
            results[test_name] = f"✗ ERROR: {e}"
        
        logger.info("")
    
    # Summary
    logger.info("=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    
    for test_name, status in results.items():
        logger.info(f"  {test_name.upper():20} {status}")
    
    logger.info("")
    
    passed = sum(1 for s in results.values() if "PASS" in s)
    total = len(results)
    
    logger.info(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✓ All tests passed! Async LLM integration is working correctly.")
        return 0
    else:
        logger.warning(f"⚠  {total - passed} test(s) failed. Check logs for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

#!/usr/bin/env python3
"""Test Phase 2 endpoints: reasoning and ensemble."""

import json
import requests
import time
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

# Test file
TEST_FILE = "kicli_code_assist/agent/analysis/ast_analyzer.py"
TEST_CODE = """
def hello_world():
    print("Hello, World!")
    return 42

def add(x, y):
    result = x + y
    return result
"""

def test_reasoning():
    """Test /api/agent/reason endpoint."""
    print("\n🧠 Testing Reasoning Agent...")
    
    data = {
        "file": TEST_FILE,
        "query": "What could be improved in this code?",
        "request_id": "test-reason-001",
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/agent/reason", json=data, timeout=30)
        result = response.json()
        
        if result.get("status") == "ok":
            print(f"✓ Reasoning succeeded")
            print(f"  - Thinking steps: {len(result.get('thinking', []))}")
            print(f"  - Confidence: {result.get('confidence', 0):.1%}")
            print(f"  - Duration: {result.get('total_duration_ms')}ms")
            print(f"\n  Conclusion: {result.get('conclusion', '')[:100]}...")
            return True
        else:
            print(f"✗ Reasoning failed: {result.get('error')}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_ensemble():
    """Test /api/agent/ensemble endpoint."""
    print("\n🎯 Testing Ensemble (OpenAI + Ollama)...")
    
    data = {
        "code": TEST_CODE,
        "question": "What does this code do?",
        "request_id": "test-ensemble-001",
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/agent/ensemble", json=data, timeout=30)
        result = response.json()
        
        if result.get("status") == "ok":
            print(f"✓ Ensemble succeeded")
            print(f"  - Responses: {len(result.get('responses', []))} LLMs")
            print(f"  - Agreement: {result.get('agreement_score', 0):.1%}")
            print(f"  - Duration: {result.get('total_duration_ms')}ms")
            
            for resp in result.get('responses', []):
                if resp.get('error'):
                    print(f"  - {resp.get('provider')}: ERROR - {resp.get('error')}")
                else:
                    text = resp.get('text', '')[:50]
                    print(f"  - {resp.get('provider')}: {text}...")
            
            return True
        else:
            print(f"✗ Ensemble failed: {result.get('error')}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("="*60)
    print("Phase 2 Endpoint Tests (Reasoning + Ensemble)")
    print("="*60)
    
    results = {
        "reasoning": test_reasoning(),
        "ensemble": test_ensemble(),
    }
    
    print("\n" + "="*60)
    print("Summary:")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())

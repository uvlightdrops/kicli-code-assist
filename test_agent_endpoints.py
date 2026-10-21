#!/usr/bin/env python3
"""Test the new /api/agent/* endpoints."""

import requests
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"


def test_explain_endpoint():
    """Test /api/agent/explain endpoint."""
    print("\n" + "=" * 70)
    print("TEST: /api/agent/explain")
    print("=" * 70)

    payload = {
        "file": "kicli_code_assist/web/server.py",
        "line": 50,
    }

    try:
        response = requests.post(f"{BASE_URL}/api/agent/explain", json=payload, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response received:")
            print(f"  - Status: {data.get('status')}")
            print(f"  - File: {data.get('file')}")
            print(f"  - Summary: {data.get('summary')[:100]}...")
            print(f"  - Functions found: {len(data.get('functions', []))}")
            print(f"  - Classes found: {len(data.get('classes', []))}")
            print(f"  - Affected files: {data.get('affected_files')}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False

    except requests.ConnectionError:
        print("❌ Connection error - server not running on http://127.0.0.1:8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_suggest_endpoint():
    """Test /api/agent/suggest endpoint."""
    print("\n" + "=" * 70)
    print("TEST: /api/agent/suggest")
    print("=" * 70)

    payload = {
        "file": "kicli_code_assist/web/server.py",
    }

    try:
        response = requests.post(f"{BASE_URL}/api/agent/suggest", json=payload, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response received:")
            print(f"  - Status: {data.get('status')}")
            print(f"  - File: {data.get('file')}")
            print(f"  - Summary: {data.get('summary')}")
            print(f"  - Suggestions: {len(data.get('suggestions', []))}")
            for i, sugg in enumerate(data.get("suggestions", [])[:3], 1):
                print(f"    {i}. {sugg.get('type')}: {sugg.get('message')[:60]}...")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False

    except requests.ConnectionError:
        print("❌ Connection error - server not running")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "🚀 PROGRAMMING AGENT ENDPOINT TESTS 🚀".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")

    print("\n⚠️  Make sure server is running:")
    print("   cd /home/flow/dev_flow/kicli-code-assist")
    print("   python3 -m kicli_code_assist.web.server")

    input("\n✅ Server running? Press Enter to continue...")

    results = []

    results.append(("Explain Endpoint", test_explain_endpoint()))
    results.append(("Suggest Endpoint", test_suggest_endpoint()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\nResult: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All endpoints working!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

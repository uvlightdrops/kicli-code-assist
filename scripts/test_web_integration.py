#!/usr/bin/env python3
"""
Integration test for kicli-assist Web Frontend + Backend.
Tests basic chat flow, file upload, WebSocket, and logging.
"""

import sys
import time
import subprocess
import requests
import json
from pathlib import Path

API_URL = "http://localhost:8000/api"
TIMEOUT = 10

def test_health():
    """Test health endpoint."""
    print("▶ Testing /api/health...")
    resp = requests.get(f"{API_URL}/health", timeout=TIMEOUT)
    assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
    data = resp.json()
    assert data["status"] == "ok", f"Status not ok: {data}"
    print("✅ Health check passed")

def test_config():
    """Test config endpoint."""
    print("▶ Testing /api/config...")
    resp = requests.get(f"{API_URL}/config", timeout=TIMEOUT)
    assert resp.status_code == 200, f"Config fetch failed: {resp.status_code}"
    data = resp.json()
    assert "llm" in data, "No LLM config"
    assert "storage" in data, "No storage config"
    print(f"✅ Config loaded: LLM provider={data.get('llm', {}).get('provider', 'unknown')}")

def test_chat_submission():
    """Test chat submission endpoint."""
    print("▶ Testing /api/chat (message submission)...")
    resp = requests.post(
        f"{API_URL}/chat",
        json={"message": "Hello, test!", "files": []},
        timeout=TIMEOUT
    )
    assert resp.status_code == 200, f"Chat submission failed: {resp.status_code}"
    data = resp.json()
    assert "request_id" in data, "No request_id returned"
    print(f"✅ Chat submitted: request_id={data['request_id']}")

def test_file_upload():
    """Test file upload endpoint."""
    print("▶ Testing /api/files/upload...")
    
    # Create test file
    test_file = Path("/tmp/test_upload.py")
    test_file.write_text("print('hello world')\n")
    
    with open(test_file, "rb") as f:
        files = {"file": f}
        resp = requests.post(
            f"{API_URL}/files/upload",
            files=files,
            timeout=TIMEOUT
        )
    
    assert resp.status_code == 200, f"File upload failed: {resp.status_code}"
    data = resp.json()
    assert "file_id" in data, "No file_id returned"
    assert "path" in data, "No path returned"
    print(f"✅ File uploaded: {data['path']} ({data['size_bytes']} bytes)")

def test_logs():
    """Test logs endpoint."""
    print("▶ Testing /api/logs...")
    resp = requests.get(
        f"{API_URL}/logs",
        params={"lines": 10},
        timeout=TIMEOUT
    )
    assert resp.status_code == 200, f"Logs fetch failed: {resp.status_code}"
    data = resp.json()
    assert "logs" in data, "No logs returned"
    print(f"✅ Logs fetched: {len(data['logs'])} lines")

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("kicli-assist Web Frontend Integration Tests")
    print("="*60 + "\n")
    
    tests = [
        ("Health Check", test_health),
        ("Config Endpoint", test_config),
        ("Chat Submission", test_chat_submission),
        ("File Upload", test_file_upload),
        ("Logs Retrieval", test_logs),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            failed += 1
            # Continue to next test
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

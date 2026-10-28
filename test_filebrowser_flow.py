#!/usr/bin/env python3
"""
Test the FileBrowser API flow to identify issues
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"
PROJECT_PATH = "/home/flow/dev_flow/ki-knowledge"

print("=" * 60)
print("FileBrowser Flow Test")
print("=" * 60)

# Test 1: Open project
print("\n[1] Testing POST /api/projects/open")
print(f"    Payload: {{'path': '{PROJECT_PATH}'}}")
try:
    resp = requests.post(f"{BASE_URL}/api/projects/open", json={"path": PROJECT_PATH})
    print(f"    Status: {resp.status_code}")
    data = resp.json()
    print(f"    Response: {json.dumps(data, indent=2)}")
    
    if resp.status_code == 200 and data.get('success'):
        project = data.get('data', {})
        project_id = project.get('id')
        print(f"    ✓ Project opened successfully")
        print(f"      - ID: {project_id}")
        print(f"      - Name: {project.get('name')}")
        print(f"      - Path: {project.get('path')}")
    else:
        print(f"    ✗ Failed to open project")
except Exception as e:
    print(f"    ✗ Error: {e}")
    exit(1)

# Test 2: List files with empty path (like initial load)
print("\n[2] Testing GET /api/project/files with empty path")
params = {
    "path": "",
    "project": PROJECT_PATH
}
print(f"    Params: {params}")
try:
    resp = requests.get(f"{BASE_URL}/api/project/files", params=params)
    print(f"    Status: {resp.status_code}")
    data = resp.json()
    
    if resp.status_code == 200:
        items = data.get('items', [])
        print(f"    ✓ Got {len(items)} items")
        if items:
            print(f"    First 3 items:")
            for item in items[:3]:
                icon = "📁" if item['type'] == 'folder' else "📄"
                print(f"      {icon} {item['name']} ({item['type']})")
    else:
        print(f"    ✗ Error: {data.get('error', 'Unknown error')}")
        
except Exception as e:
    print(f"    ✗ Error: {e}")
    
# Test 3: List files with full project path
print("\n[3] Testing GET /api/project/files with full project path")
params = {
    "path": PROJECT_PATH,
    "project": PROJECT_PATH
}
print(f"    Params: {params}")
try:
    resp = requests.get(f"{BASE_URL}/api/project/files", params=params)
    print(f"    Status: {resp.status_code}")
    data = resp.json()
    
    if resp.status_code == 200:
        items = data.get('items', [])
        print(f"    ✓ Got {len(items)} items")
    else:
        print(f"    ✗ Error: {data.get('error', 'Unknown error')}")
        
except Exception as e:
    print(f"    ✗ Error: {e}")

# Test 4: List files from a subdirectory
print("\n[4] Testing GET /api/project/files with subdirectory")
params = {
    "path": "config",
    "project": PROJECT_PATH
}
print(f"    Params: {params}")
try:
    resp = requests.get(f"{BASE_URL}/api/project/files", params=params)
    print(f"    Status: {resp.status_code}")
    data = resp.json()
    
    if resp.status_code == 200:
        items = data.get('items', [])
        print(f"    ✓ Got {len(items)} items in 'config' directory")
        if items:
            for item in items[:3]:
                icon = "📁" if item['type'] == 'folder' else "📄"
                print(f"      {icon} {item['name']}")
    else:
        print(f"    ✗ Error: {data.get('error', 'Unknown error')}")
        
except Exception as e:
    print(f"    ✗ Error: {e}")

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)

#!/usr/bin/env python3
"""
Check script: Detect absolute paths in all project pyproject.toml files.
Run this regularly to catch absolute paths that slip through.

Usage:
    python3 check_absolute_paths.py
    python3 check_absolute_paths.py /home/flow/dev_flow/kicli-code-assist
"""

import sys
import re
from pathlib import Path

def check_pyproject(file_path):
    """Check a single pyproject.toml for absolute paths."""
    try:
        content = file_path.read_text()
    except FileNotFoundError:
        return None, f"File not found: {file_path}"
    
    issues = []
    
    # Pattern: file:/// followed by absolute path (not ${PROJECT_DIR})
    absolute_pattern = re.compile(r'file:///[a-zA-Z/]')
    
    for i, line in enumerate(content.split('\n'), 1):
        if 'file://' in line and '${PROJECT_DIR}' not in line:
            if absolute_pattern.search(line):
                issues.append((i, line.strip()))
    
    return issues, None

def main():
    # Check specific path or default to common locations
    if len(sys.argv) > 1:
        check_paths = [Path(sys.argv[1])]
    else:
        check_paths = [
            Path("/home/flow/dev_flow/kicli-code-assist"),
            Path("/home/flow/dev_flow/ki-core"),
            Path("/home/flow/dev_flow/ki-knowledge"),
            Path("/home/flow/dev_flow/stackctl"),
            Path("/home/flow/dev_flow/yaml_cfg_wizard"),
            Path("/home/flow/dev_flow/flowpy"),
        ]
    
    found_issues = False
    
    for project_path in check_paths:
        pyproject = project_path / "pyproject.toml"
        
        if not pyproject.exists():
            continue
        
        issues, error = check_pyproject(pyproject)
        
        if error:
            print(f"⚠️  {project_path.name}: {error}")
            continue
        
        if issues:
            found_issues = True
            print(f"❌ {project_path.name}: Found absolute paths in pyproject.toml")
            for line_num, line in issues:
                print(f"   Line {line_num}: {line}")
            print()
        else:
            print(f"✅ {project_path.name}: OK (using relative paths)")
    
    if found_issues:
        print("\n🔧 Fix with ${PROJECT_DIR}:")
        print("   file://${PROJECT_DIR}/../../ki-core")
        sys.exit(1)
    else:
        print("\n✨ All projects clean!")
        sys.exit(0)

if __name__ == "__main__":
    main()

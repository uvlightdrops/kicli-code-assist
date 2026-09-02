#!/usr/bin/env python3
"""Install kicli-code-assist with dynamic ki-core path resolution."""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get home directory dynamically
    home = str(Path.home())
    ki_core_path = os.path.join(home, "dev_flow", "ki-core")
    ki_core_url = f"file://{ki_core_path}"
    
    print(f"🔧 Installing kicli-code-assist")
    print(f"  Home: {home}")
    print(f"  Ki-Core: {ki_core_path}")
    
    # Check if ki-core exists
    if not os.path.isdir(ki_core_path):
        print(f"❌ Error: ki-core not found at {ki_core_path}")
        sys.exit(1)
    
    # Read pyproject.toml
    project_dir = os.path.dirname(os.path.abspath(__file__))
    pyproject_path = os.path.join(project_dir, "pyproject.toml")
    
    with open(pyproject_path, "r") as f:
        content = f.read()
    
    # Replace dynamic placeholder if it exists
    if "${HOME}/dev_flow/ki-core" in content or "$HOME" in content:
        content = content.replace("${HOME}/dev_flow/ki-core", ki_core_path)
        content = content.replace("$HOME", home)
        
        # Write back
        with open(pyproject_path, "w") as f:
            f.write(content)
        print(f"✅ Updated pyproject.toml with expanded paths")
    
    # Install with pip
    print("\n📦 Installing with pip...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", project_dir],
        cwd=project_dir
    )
    
    if result.returncode == 0:
        print("\n✅ Installation successful!")
    else:
        print("\n❌ Installation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()

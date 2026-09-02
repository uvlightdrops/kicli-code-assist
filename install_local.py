#!/usr/bin/env python3
"""Install kicli-code-assist with dynamic ki-core path resolution."""

import os
import sys
import subprocess
import venv
from pathlib import Path

def main():
    project_dir = Path(__file__).parent.absolute()
    venv_dir = project_dir / "venv"
    home = str(Path.home())
    ki_core_path = os.path.join(home, "dev_flow", "ki-core")
    
    print(f"🔧 Installing kicli-code-assist")
    print(f"  Home: {home}")
    print(f"  Project: {project_dir}")
    print(f"  Ki-Core: {ki_core_path}")
    
    # Check if ki-core exists
    if not os.path.isdir(ki_core_path):
        print(f"❌ Error: ki-core not found at {ki_core_path}")
        sys.exit(1)
    
    # Create venv if it doesn't exist
    if not venv_dir.exists():
        print(f"\n📦 Creating virtual environment at {venv_dir}...")
        venv.create(venv_dir, with_pip=True)
        print(f"✅ venv created")
    
    # Get pip executable from venv
    pip_exe = venv_dir / "bin" / "pip" if os.name != "nt" else venv_dir / "Scripts" / "pip.exe"
    
    # Read pyproject.toml and replace placeholder
    pyproject_path = project_dir / "pyproject.toml"
    with open(pyproject_path, "r") as f:
        content = f.read()
    
    if "${HOME}/dev_flow/ki-core" in content or "$HOME" in content:
        content = content.replace("${HOME}/dev_flow/ki-core", ki_core_path)
        content = content.replace("$HOME", home)
        
        with open(pyproject_path, "w") as f:
            f.write(content)
        print(f"\n✅ Updated pyproject.toml with expanded paths")
    
    # Install with venv's pip
    print(f"\n📦 Installing packages...")
    result = subprocess.run(
        [str(pip_exe), "install", "-e", str(project_dir)],
        cwd=str(project_dir)
    )
    
    if result.returncode == 0:
        print(f"\n✅ Installation successful!")
        print(f"\n📝 To activate: source {venv_dir}/bin/activate")
    else:
        print(f"\n❌ Installation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()

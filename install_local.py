#!/usr/bin/env python3
"""Install kicli-code-assist together with the local ki-core checkout."""

import os
import subprocess
import sys
import venv
from pathlib import Path


def main() -> None:
    project_dir = Path(__file__).resolve().parent
    venv_dir = project_dir / "venv"
    ki_core_path = Path.home() / "dev_flow" / "ki-core"

    print("🔧 Installing kicli-code-assist")
    print(f"  Project: {project_dir}")
    print(f"  Ki-Core: {ki_core_path}")

    if not ki_core_path.is_dir():
        print(f"❌ Error: ki-core not found at {ki_core_path}")
        sys.exit(1)

    if not venv_dir.exists():
        print(f"\n📦 Creating virtual environment at {venv_dir}...")
        venv.create(venv_dir, with_pip=True)
        print("✅ venv created")

    pip_exe = venv_dir / "bin" / "pip" if os.name != "nt" else venv_dir / "Scripts" / "pip.exe"

    print("\n📦 Installing local ki-core...")
    result = subprocess.run([str(pip_exe), "install", "-e", str(ki_core_path)], cwd=str(project_dir))
    if result.returncode != 0:
        print("\n❌ ki-core installation failed!")
        sys.exit(result.returncode)

    print("\n📦 Installing kicli-code-assist...")
    result = subprocess.run([str(pip_exe), "install", "-e", str(project_dir)], cwd=str(project_dir))
    if result.returncode != 0:
        print("\n❌ kicli-code-assist installation failed!")
        sys.exit(result.returncode)

    print("\n✅ Installation successful!")
    print(f"\n📝 To activate: source {venv_dir}/bin/activate")


if __name__ == "__main__":
    main()

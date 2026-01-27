"""Build Windows installer for HifzDefend."""

import subprocess
import sys
from pathlib import Path
import shutil

def build_executable():
    """Build executable using PyInstaller."""
    print("Building executable...")

    cmd = [
        "pyinstaller",
        "--name=hifzdefend",
        "--onefile",
        "--windowed",
        "--icon=assets/icon.ico",
        "--add-data=src/hifzdefend/licensing/keys/public.pem;hifzdefend/licensing/keys",
        "--add-data=config/hifzdefend.toml.example;config",
        "--hidden-import=anthropic",
        "--hidden-import=chromadb",
        "--hidden-import=fastapi",
        "--hidden-import=stripe",
        "src/hifzdefend/__main__.py",
    ]

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("ERROR: PyInstaller build failed")
        return False

    print("✓ Executable built successfully")
    return True


def build_installer():
    """Build installer using NSIS."""
    print("Building installer...")

    nsis_script = Path("installer/hifzdefend.nsi")

    if not nsis_script.exists():
        print(f"ERROR: NSIS script not found: {nsis_script}")
        return False

    # Find NSIS compiler
    nsis_paths = [
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe",
    ]

    makensis = None
    for path in nsis_paths:
        if Path(path).exists():
            makensis = path
            break

    if not makensis:
        print("ERROR: NSIS not found. Install from https://nsis.sourceforge.io/")
        return False

    cmd = [makensis, str(nsis_script)]
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("ERROR: NSIS build failed")
        return False

    print("✓ Installer built successfully")
    return True


def main():
    """Main build process."""
    print("=" * 60)
    print("HifzDefend Windows Installer Build")
    print("=" * 60)
    print()

    # Step 1: Build executable
    if not build_executable():
        sys.exit(1)

    print()

    # Step 2: Build installer
    if not build_installer():
        sys.exit(1)

    print()
    print("=" * 60)
    print("Build completed successfully!")
    print("=" * 60)
    print()
    print("Installer location: dist/HifzDefend-0.3.0-Setup.exe")
    print()


if __name__ == "__main__":
    main()

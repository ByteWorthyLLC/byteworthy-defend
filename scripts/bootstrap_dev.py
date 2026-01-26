"""
HifzDefend Development Environment Bootstrap Script

This script automates the setup of the development environment:
- Creates virtual environment (.venv)
- Installs dependencies (pip install -e ".[dev]")
- Sets up pre-commit hooks
- Creates default directories (logs, reports, quarantine)
- Generates default configuration
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def print_step(message: str) -> None:
    """Print a formatted step message."""
    print(f"\n{'='*60}")
    print(f"  {message}")
    print(f"{'='*60}\n")


def run_command(cmd: list[str], description: str, check: bool = True) -> bool:
    """Run a command and handle errors."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False


def main() -> int:
    """Main bootstrap function."""
    print_step("HifzDefend Development Environment Bootstrap")

    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    print(f"Project root: {project_root}")

    # Check Python version
    if sys.version_info < (3, 10):
        print(f"ERROR: Python 3.10+ required (found {platform.python_version()})")
        return 1

    print(f"Python version: {platform.python_version()}")

    # Step 1: Create virtual environment
    print_step("Step 1: Creating virtual environment")
    venv_path = project_root / ".venv"
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}")
    else:
        if not run_command([sys.executable, "-m", "venv", ".venv"], "Create venv"):
            return 1
        print(f"Virtual environment created at {venv_path}")

    # Determine pip executable path
    if platform.system() == "Windows":
        pip_exe = venv_path / "Scripts" / "pip.exe"
        python_exe = venv_path / "Scripts" / "python.exe"
    else:
        pip_exe = venv_path / "bin" / "pip"
        python_exe = venv_path / "bin" / "python"

    # Step 2: Upgrade pip
    print_step("Step 2: Upgrading pip")
    if not run_command([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], "Upgrade pip"):
        return 1

    # Step 3: Install project with dev dependencies
    print_step("Step 3: Installing HifzDefend with dev dependencies")
    if not run_command([str(pip_exe), "install", "-e", ".[dev]"], "Install package"):
        return 1

    # Step 4: Create default directories
    print_step("Step 4: Creating default directories")
    default_dirs = [
        project_root / "logs",
        project_root / "reports",
        project_root / "quarantine",
    ]

    # Also create user-specific directories
    local_appdata = Path(os.environ.get("LOCALAPPDATA", "~/.local/share")).expanduser()
    hifz_data_dir = local_appdata / "HifzDefend"
    user_dirs = [
        hifz_data_dir,
        hifz_data_dir / "logs",
        hifz_data_dir / "reports",
        hifz_data_dir / "quarantine",
    ]

    for directory in default_dirs + user_dirs:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created: {directory}")

    # Step 5: Generate default configuration
    print_step("Step 5: Generating default configuration")
    config_path = hifz_data_dir / "hifzdefend.toml"
    if config_path.exists():
        print(f"Configuration already exists at {config_path}")
    else:
        default_config_path = project_root / "config" / "hifzdefend.defaults.toml"
        if default_config_path.exists():
            import shutil
            shutil.copy(default_config_path, config_path)
            print(f"Configuration copied to {config_path}")
        else:
            print(f"WARNING: Default config not found at {default_config_path}")

    # Step 6: Set up pre-commit hooks
    print_step("Step 6: Setting up pre-commit hooks")
    precommit_config = project_root / ".pre-commit-config.yaml"
    if precommit_config.exists():
        if not run_command([str(pip_exe), "install", "pre-commit"], "Install pre-commit"):
            print("WARNING: Failed to install pre-commit")
        else:
            if not run_command([str(python_exe), "-m", "pre_commit", "install"], "Install hooks", check=False):
                print("WARNING: Failed to install pre-commit hooks")
    else:
        print(f"WARNING: .pre-commit-config.yaml not found")

    # Final summary
    print_step("Bootstrap Complete!")
    print("Next steps:")
    print(f"1. Activate virtual environment:")
    if platform.system() == "Windows":
        print(f"   .venv\\Scripts\\activate")
    else:
        print(f"   source .venv/bin/activate")
    print(f"2. Verify installation: hifzdefend --version")
    print(f"3. Check ClamAV status: hifzdefend status")
    print(f"4. Run tests: pytest")
    print(f"\nConfiguration location: {config_path}")
    print(f"Data directory: {hifz_data_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

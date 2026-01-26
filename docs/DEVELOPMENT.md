# HifzDefend Development Guide

Guide for developers contributing to HifzDefend.

## Development Setup

### 1. Clone Repository
```bash
git clone --recurse-submodules <repository-url>
cd HifzDefend
```

### 2. Run Bootstrap Script
```bash
python scripts/bootstrap_dev.py
```

This automates:
- Virtual environment creation
- Dependency installation
- Pre-commit hook setup
- Directory creation

### 3. Activate Virtual Environment
```powershell
.venv\Scripts\activate
```

### 4. Install ClamAV
Follow [INSTALLATION.md](INSTALLATION.md) to install and configure ClamAV.

### 5. Set Up Windows Defender Exclusions
```powershell
# As Administrator
.\scripts\setup_defender_exclusions.ps1
```

## Project Structure

```
HifzDefend/
├── src/hifzdefend/          # Main package (src layout)
│   ├── core/                # Scanner and engine
│   ├── config/              # Configuration system
│   ├── reporting/           # Logging and reports
│   ├── cli/                 # CLI commands
│   └── utils/               # Utilities and exceptions
├── tests/                   # Test suite
│   ├── test_core/           # Core tests
│   ├── test_config/         # Config tests
│   ├── integration/         # Integration tests
│   └── conftest.py          # Pytest fixtures
├── config/                  # Default configurations
├── scripts/                 # Setup and utility scripts
├── docs/                    # Documentation
└── pyproject.toml           # Project configuration
```

## Development Workflow

### 1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow coding standards:
- PEP 8 style (enforced by black)
- Type hints for functions
- Docstrings for public APIs
- Tests for new features

### 3. Run Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=hifzdefend --cov-report=html

# Specific test file
pytest tests/test_core/test_scanner.py

# Skip slow tests
pytest -m "not slow"

# Integration tests only
pytest tests/integration/
```

### 4. Check Code Quality
```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/

# Run all pre-commit hooks
pre-commit run --all-files
```

### 5. Commit Changes
```bash
git add .
git commit -m "Add feature: description"
```

Pre-commit hooks will automatically:
- Format code with black
- Lint with ruff
- Check for security issues
- Validate YAML/TOML files

### 6. Push and Create PR
```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Testing

### Test Structure

```
tests/
├── conftest.py              # Fixtures
├── test_core/               # Core component tests
│   ├── test_scanner.py
│   └── test_engine.py
├── test_config/             # Configuration tests
│   └── test_loader.py
├── integration/             # End-to-end tests
│   └── test_scan_flow.py
└── fixtures/                # Test data
    └── eicar_test.zip       # Encrypted EICAR
```

### Writing Tests

**Unit Test Example:**
```python
def test_scan_clean_file(clamav_scanner, clean_file):
    """Test scanning a clean file."""
    result = clamav_scanner.scan_file(clean_file)
    assert result.is_clean
    assert not result.is_infected
```

**Integration Test Example:**
```python
@pytest.mark.integration
@pytest.mark.requires_clamav
def test_scan_with_quarantine(scan_engine, eicar_file):
    """Test complete scan with auto-quarantine."""
    report = scan_engine.scan_path(eicar_file)
    assert report.threats_count == 1
    assert report.threats_found[0]["quarantined"]
```

### Test Fixtures

Available fixtures (see `tests/conftest.py`):
- `temp_dir` - Temporary directory
- `clean_file` - Clean test file
- `eicar_file` - Extracted EICAR test file
- `test_config` - Test configuration
- `clamav_scanner` - ClamAV scanner instance
- `scan_engine` - Scan engine instance

### Test Markers

- `@pytest.mark.slow` - Slow tests (skip with `-m "not slow"`)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.requires_clamav` - Requires ClamAV daemon

## Code Style

### Python Style Guide

We follow PEP 8 with these specifics:
- Line length: 100 characters
- Use double quotes for strings
- Type hints for function signatures
- Docstrings in Google style

### Example Function
```python
def scan_file(self, file_path: Union[str, Path]) -> ScanResult:
    """
    Scan a single file for malware.

    Args:
        file_path: Path to file to scan

    Returns:
        ScanResult object with scan results

    Raises:
        ScannerError: If scan fails
    """
    # Implementation
```

### Imports

Order imports as:
1. Standard library
2. Third-party packages
3. Local imports

```python
import os
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from ..config.loader import get_config
from ..utils.exceptions import ScannerError
```

## Adding New Features

### Adding a CLI Command

1. Add function to `src/hifzdefend/cli/commands.py`:
```python
@cli.command()
@click.argument("path")
def mycommand(path: str):
    """My new command."""
    console.print(f"Running on {path}")
```

2. Add tests to `tests/test_cli/test_commands.py`

3. Update documentation in `docs/USAGE.md`

### Adding Configuration Option

1. Add field to Pydantic model in `src/hifzdefend/config/loader.py`:
```python
class ScanningConfig(BaseModel):
    my_new_option: bool = False
```

2. Add to default config in `config/hifzdefend.defaults.toml`:
```toml
[scanning]
my_new_option = false
```

3. Add tests to `tests/test_config/test_loader.py`

### Adding Scanner Feature

1. Add method to `ClamAVScanner` in `src/hifzdefend/core/scanner.py`
2. Add integration to `ScanEngine` in `src/hifzdefend/core/engine.py`
3. Add tests to `tests/test_core/test_scanner.py`
4. Update CLI commands to use new feature

## Security

### Security Checklist

When adding features, ensure:
- [ ] Input validation (especially file paths)
- [ ] No SQL injection vulnerabilities
- [ ] No command injection vulnerabilities
- [ ] No path traversal vulnerabilities
- [ ] Proper error handling (don't expose sensitive info)
- [ ] Audit logging for security events

### Security Tools

Run security checks:
```bash
# Dependency vulnerabilities
pip-audit

# Code security issues
bandit -r src/

# Check for secrets in code
pre-commit run detect-private-key --all-files
```

## Git Workflow

### Commit Messages

Follow conventional commits:
```
type(scope): description

feat(scanner): add support for custom signatures
fix(quarantine): handle permission errors correctly
docs(readme): update installation instructions
test(scanner): add tests for archive scanning
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `style`, `chore`

### Branch Naming

- `feature/feature-name` - New features
- `fix/bug-description` - Bug fixes
- `docs/doc-description` - Documentation
- `refactor/refactor-description` - Code refactoring

## Debugging

### Enable Debug Logging

Edit configuration:
```toml
[logging]
level = "DEBUG"
```

Or set environment variable:
```bash
export HIFZDEFEND_LOG_LEVEL=DEBUG
```

### Debug with VS Code

`.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "HifzDefend Scan",
            "type": "python",
            "request": "launch",
            "module": "hifzdefend",
            "args": ["scan", "path/to/test"],
            "console": "integratedTerminal"
        }
    ]
}
```

### Common Issues

**Import errors:**
```bash
# Reinstall in editable mode
pip install -e .
```

**ClamAV connection errors:**
```bash
# Check daemon status
hifzdefend status

# Restart daemon
taskkill /F /IM clamd.exe
cd "C:\Program Files\ClamAV"
.\clamd.exe
```

## Release Process

### Version Bump

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Commit changes:
   ```bash
   git commit -m "chore: bump version to 0.2.0"
   ```

### Create Release

1. Tag release:
   ```bash
   git tag -a v0.2.0 -m "Release v0.2.0"
   git push origin v0.2.0
   ```

2. Create GitHub release with changelog

3. Build distribution:
   ```bash
   python -m build
   ```

## Contributing Guidelines

### Before Submitting PR

- [ ] Code passes all tests (`pytest`)
- [ ] Code formatted with black
- [ ] No linting errors (ruff)
- [ ] Type checking passes (mypy)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Pre-commit hooks pass

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guide
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

## Resources

- **ClamAV Documentation**: https://docs.clamav.net/
- **Click Documentation**: https://click.palletsprojects.com/
- **Rich Documentation**: https://rich.readthedocs.io/
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **Pytest Documentation**: https://docs.pytest.org/

## Getting Help

- Open an issue on GitHub
- Check existing documentation
- Review test examples
- Ask in pull request comments

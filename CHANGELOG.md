# Changelog

All notable changes to HifzDefend will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure and configuration
- Git repository with ClamAV submodule
- Development environment setup

## [0.1.0] - TBD

### Added
- MVP CLI scanner functionality
- ClamAV integration via clamd daemon
- Configuration system with TOML and Pydantic validation
- Structured JSON logging with rotation
- CLI commands: scan, status, update, quarantine, list-quarantine, config-show
- EICAR test file generation and handling
- Windows Defender exclusions PowerShell script
- Comprehensive test suite with pytest
- Pre-commit hooks for code quality
- Complete documentation (README, INSTALLATION, USAGE, DEVELOPMENT, SECURITY, ARCHITECTURE)

### Security
- Input validation for file paths (path traversal prevention)
- Parameterized logging (log injection prevention)
- Quarantine security with read-only and no-execute permissions
- Encrypted EICAR test file storage

[Unreleased]: https://github.com/yourusername/hifzdefend/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/hifzdefend/releases/tag/v0.1.0

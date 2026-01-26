# HifzDefend Security Documentation

Comprehensive security considerations, best practices, and threat model for HifzDefend.

## Table of Contents
- [Threat Model](#threat-model)
- [Security Features](#security-features)
- [Secure Configuration](#secure-configuration)
- [Windows Defender Exclusions](#windows-defender-exclusions)
- [EICAR Test File Handling](#eicar-test-file-handling)
- [Quarantine Security](#quarantine-security)
- [Secure Coding Practices](#secure-coding-practices)
- [Incident Response](#incident-response)
- [Security Reporting](#security-reporting)

## Threat Model

### Assets
- **User files**: Files being scanned
- **Quarantined files**: Infected files in quarantine
- **Configuration**: Application settings
- **Logs**: Audit trail and scan reports
- **ClamAV virus database**: Malware signatures

### Threats
1. **Malware Execution**: Malware executed during scanning
2. **Path Traversal**: Attacker manipulates file paths
3. **Log Injection**: Attacker injects malicious log entries
4. **Configuration Tampering**: Unauthorized config changes
5. **Quarantine Escape**: Malware breaks out of quarantine
6. **TOCTOU Attacks**: Time-of-check-time-of-use race conditions
7. **Denial of Service**: Resource exhaustion attacks

### Mitigations

| Threat | Mitigation |
|--------|-----------|
| Malware Execution | ClamAV daemon process isolation, no direct file execution |
| Path Traversal | Path validation with `Path.resolve()`, base path checking |
| Log Injection | Parameterized logging with structured JSON |
| Config Tampering | Pydantic validation, restricted file permissions |
| Quarantine Escape | Read-only permissions (chmod 0444), no execute bit |
| TOCTOU | File hash verification before and after operations |
| DoS | File size limits, timeout configuration, resource monitoring |

## Security Features

### Input Validation

All user-provided file paths are validated:
```python
def validate_path(path: Path, base_path: Optional[Path] = None) -> Path:
    """Validate path to prevent path traversal."""
    resolved_path = path.resolve()

    if base_path is not None:
        try:
            resolved_path.relative_to(base_path.resolve())
        except ValueError:
            raise PathTraversalError(
                f"Path {path} is outside allowed directory {base_path}"
            )

    return resolved_path
```

### Structured Logging

JSON-formatted logs prevent log injection:
```python
log_scan_event(
    logger,
    action="threat_detected",
    file_path=str(file_path),  # Parameterized, not concatenated
    threat_name=threat_name,
    file_hash=file_hash
)
```

### Quarantine Security

Quarantined files are secured:
1. **Renamed**: UUID-based names (e.g., `a3f8b2e1-9d4c-4a7b-8e5f.quarantined`)
2. **Read-Only**: `chmod 0444` (owner read, no write/execute)
3. **Hash Verification**: SHA256 hash stored for integrity checking
4. **Atomic Moves**: `shutil.move()` ensures atomic operations

### File Hash Verification

TOCTOU protection through hash verification:
```python
# Before quarantine
original_hash = calculate_file_hash(file_path)

# Move to quarantine
shutil.move(file_path, quarantine_path)

# Verify integrity
quarantine_hash = calculate_file_hash(quarantine_path)
assert original_hash == quarantine_hash
```

## Secure Configuration

### File Permissions

Configuration files should have restricted permissions:
```powershell
# Windows: Only owner can read/write
icacls "%LOCALAPPDATA%\HifzDefend\hifzdefend.toml" /inheritance:r /grant:r "%USERNAME%:(R,W)"
```

### Sensitive Data

Never store sensitive data in configuration:
- ❌ API keys
- ❌ Passwords
- ❌ Private keys
- ✅ Connection settings
- ✅ File paths
- ✅ Scanning preferences

### Configuration Validation

Pydantic models enforce type safety and validation:
```python
class ClamAVConfig(BaseModel):
    host: str = "localhost"
    port: int = Field(default=3310, ge=1, le=65535)  # Valid port range
    timeout: int = Field(default=60, ge=1, le=600)   # Reasonable timeout
```

## Windows Defender Exclusions

### Security Risk

Windows Defender exclusions **reduce system security**:
- Excluded paths are not scanned by Windows Defender
- Malware in excluded paths will not be detected
- Only use in development environments

### Excluded Paths

The setup script excludes:
```
- tests/fixtures        (EICAR test files)
- logs/                 (Log files)
- quarantine/           (Quarantined malware)
- .venv/                (Python virtual environment)
- src/                  (Source code)
- %LOCALAPPDATA%\HifzDefend
```

### Excluded Processes

```
- python.exe
- pytest.exe
```

### Best Practices

1. **Development Only**: Never use exclusions in production
2. **Review Regularly**: Audit exclusions monthly
3. **Remove When Done**: Run removal script after development
4. **Document Justification**: Understand why each exclusion is needed
5. **Limit Scope**: Exclude only necessary paths

### Applying Exclusions

```powershell
# Preview (no changes)
.\scripts\setup_defender_exclusions.ps1 -WhatIf

# Apply
.\scripts\setup_defender_exclusions.ps1

# Remove
.\scripts\setup_defender_exclusions.ps1 -Remove
```

### Verify Exclusions

```powershell
# List excluded paths
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath

# List excluded processes
Get-MpPreference | Select-Object -ExpandProperty ExclusionProcess
```

## EICAR Test File Handling

### What is EICAR?

EICAR (European Institute for Computer Antivirus Research) test file:
- Harmless text string recognized by all AV software
- Used to test antivirus detection without real malware
- **NOT actual malware** - safe for testing

### EICAR String

```
X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*
```

### Storage Requirements

**Never commit unencrypted EICAR files:**
- ✅ Store in password-protected ZIP
- ✅ Encrypt with password "infected"
- ✅ Store in `tests/fixtures/eicar_test.zip`
- ❌ Never commit `eicar.txt` to Git
- ❌ Never commit unencrypted EICAR

### .gitignore Protection

```gitignore
# Security - Never commit malware samples
*.com
*.exe
eicar.txt
eicar*.txt
test_malware.*
*.vir
```

### Generating EICAR

```bash
# Encrypted (safe)
python scripts/generate_eicar.py

# Plain (will be detected!)
python scripts/generate_eicar.py --plain
```

### Handling in Tests

```python
@pytest.fixture
def eicar_file(temp_dir, eicar_zip_path):
    """Extract EICAR to temp directory."""
    eicar_path = temp_dir / "eicar.txt"

    with zipfile.ZipFile(eicar_zip_path, 'r') as zf:
        zf.setpassword(b'infected')
        zf.extract('eicar.txt', temp_dir)

    yield eicar_path

    # Cleanup
    if eicar_path.exists():
        eicar_path.unlink()
```

## Quarantine Security

### Quarantine Process

1. **Pre-Move Verification**:
   - Calculate SHA256 hash of original file
   - Verify file exists and is accessible

2. **Atomic Move**:
   - Use `shutil.move()` for atomic operation
   - Rename to UUID-based filename

3. **Post-Move Security**:
   - Set read-only permissions (`chmod 0444`)
   - Remove execute permissions
   - Verify hash matches original

4. **Audit Logging**:
   - Log quarantine action
   - Store original path, hash, threat name
   - Record timestamp

### Quarantine Directory

```
%LOCALAPPDATA%\HifzDefend\quarantine\
├── a3f8b2e1-9d4c-4a7b-8e5f.quarantined
├── b7e9c3f2-4d8a-4b2c-9f6e.quarantined
└── metadata.json  (future: quarantine metadata)
```

### Permissions

```python
# Set read-only, no execute
quarantine_path.chmod(0o444)
```

Windows equivalent:
```powershell
icacls "quarantine\file.quarantined" /deny *S-1-1-0:(X)
```

### TOCTOU Protection

```python
# Time-of-check
original_hash = calculate_file_hash(file_path)

# Time-of-use
shutil.move(file_path, quarantine_path)

# Verification
if calculate_file_hash(quarantine_path) != original_hash:
    raise QuarantineError("File modified during quarantine")
```

## Secure Coding Practices

### Path Traversal Prevention

```python
# ❌ Unsafe
def scan_file(user_path: str):
    file_path = Path(user_path)
    return scanner.scan(file_path)

# ✅ Safe
def scan_file(user_path: str):
    file_path = validate_path(Path(user_path))
    return scanner.scan(file_path)
```

### Log Injection Prevention

```python
# ❌ Unsafe (string concatenation)
logger.info(f"Scanning file: {user_input}")

# ✅ Safe (parameterized)
logger.info("Scanning file: %s", user_input)
```

### Command Injection Prevention

```python
# ❌ Unsafe (shell=True)
subprocess.run(f"scan {user_input}", shell=True)

# ✅ Safe (list of args)
subprocess.run(["scan", user_input])
```

### SQL Injection (Not Applicable)

HifzDefend doesn't use SQL databases. If future versions do:
```python
# ✅ Use parameterized queries
cursor.execute("SELECT * FROM scans WHERE path = ?", (user_path,))
```

### Dependency Management

```bash
# Pin dependencies in pyproject.toml
clamd>=1.0.2,<2.0.0

# Regular audits
pip-audit

# Check for known vulnerabilities
bandit -r src/
```

## Incident Response

### If Malware Detected

1. **Automatic Response** (if `auto_quarantine=true`):
   - File moved to quarantine
   - Original file removed
   - Audit log entry created

2. **Manual Response**:
   ```bash
   # Quarantine manually
   hifzdefend quarantine path/to/file --threat-name "Malware.Name"

   # Verify quarantine
   hifzdefend list-quarantine
   ```

3. **Investigation**:
   - Check audit logs: `%LOCALAPPDATA%\HifzDefend\logs\audit.log`
   - Review scan report
   - Determine infection source

4. **System Scan**:
   ```bash
   # Full system scan
   hifzdefend scan C:\

   # Scan common infection points
   hifzdefend scan %TEMP%
   hifzdefend scan %USERPROFILE%\Downloads
   ```

### If False Positive

1. **Verify File is Clean**:
   - Check file source (trusted vendor?)
   - Verify digital signature
   - Check hash on VirusTotal

2. **Report to ClamAV**:
   - Visit: https://www.clamav.net/reports/fp
   - Submit false positive report

3. **Add Exclusion** (if verified clean):
   ```toml
   [scanning]
   excluded_paths = ["C:\\TrustedApp\\file.dll"]
   ```

### If Quarantine Breach

If a quarantined file is accessed:

1. **Check Windows Security Logs**:
   ```powershell
   Get-EventLog -LogName Security -Newest 100
   ```

2. **Review HifzDefend Audit Logs**:
   ```bash
   type %LOCALAPPDATA%\HifzDefend\logs\audit.log | findstr "quarantine"
   ```

3. **Verify Quarantine Integrity**:
   ```bash
   # Check file permissions
   icacls %LOCALAPPDATA%\HifzDefend\quarantine\*
   ```

4. **Re-secure Quarantine**:
   ```python
   for qfile in quarantine_dir.glob("*.quarantined"):
       qfile.chmod(0o444)
   ```

## Security Reporting

### Reporting Vulnerabilities

**DO NOT** open public issues for security vulnerabilities.

Instead:
1. Email: security@hifzdefend.local (if available)
2. Use GitHub private security advisory
3. Encrypt message with PGP (if key provided)

### What to Include

- Description of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (optional)
- Your contact information

### Response Timeline

- **24 hours**: Initial acknowledgment
- **7 days**: Preliminary assessment
- **30 days**: Fix developed and tested
- **90 days**: Public disclosure (after patch release)

## Security Checklist

### For Developers

- [ ] Input validation on all user input
- [ ] Parameterized logging (no string concatenation)
- [ ] Path traversal checks
- [ ] No command injection vulnerabilities
- [ ] No SQL injection (if database added)
- [ ] Proper error handling (don't expose sensitive data)
- [ ] Security tests added
- [ ] Audit logging for security events
- [ ] Code reviewed by another developer
- [ ] Dependencies audited with `pip-audit`

### For Users

- [ ] ClamAV virus definitions up to date
- [ ] Configuration file has restricted permissions
- [ ] Windows Defender exclusions minimal and reviewed
- [ ] Quarantine directory secured
- [ ] Audit logs reviewed regularly
- [ ] No sensitive data in logs or config
- [ ] Backup quarantine metadata
- [ ] Remove exclusions when not developing

## Additional Resources

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **ClamAV Security**: https://www.clamav.net/documents/security
- **NIST Cybersecurity Framework**: https://www.nist.gov/cyberframework
- **Windows Security**: https://docs.microsoft.com/en-us/windows/security/

## Conclusion

Security is a shared responsibility. Developers must write secure code, and users must follow security best practices. Regular audits, updates, and vigilance are essential to maintaining a secure system.

**Remember**: HifzDefend is a development tool. For production antivirus needs, use enterprise-grade solutions with professional support.

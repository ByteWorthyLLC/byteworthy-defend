# HifzDefend Installation Guide

This guide provides detailed instructions for installing HifzDefend and its dependencies on Windows.

## Prerequisites

### System Requirements
- **Operating System**: Windows 10 or Windows 11
- **Python**: Version 3.10 or higher
- **RAM**: Minimum 4 GB (8 GB recommended)
- **Disk Space**: At least 2 GB free space
- **Administrator Access**: Required for Windows Defender exclusions

### Required Software
1. **Python 3.10+**
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"

2. **Git** (optional, but recommended)
   - Download from: https://git-scm.com/download/win
   - Choose default settings during installation

3. **ClamAV for Windows**
   - Download from: https://www.clamav.net/downloads
   - Choose the latest Windows installer (e.g., ClamAV-0.103.x-win-x64.exe)

## Step 1: Install ClamAV

### 1.1 Download and Install
1. Download ClamAV Windows installer from https://www.clamav.net/downloads
2. Run the installer as Administrator
3. Install to the default location: `C:\Program Files\ClamAV`
4. Complete the installation

### 1.2 Configure ClamAV Daemon (clamd)

1. Open `C:\Program Files\ClamAV\conf\clamd.conf` in a text editor (as Administrator)

2. Make the following changes:
   ```
   # Comment out or remove this line:
   # Example

   # Uncomment these lines:
   TCPSocket 3310
   TCPAddr 127.0.0.1
   ```

3. Save the file

### 1.3 Configure FreshClam (Database Updater)

1. Open `C:\Program Files\ClamAV\conf\freshclam.conf` in a text editor (as Administrator)

2. Comment out the Example line:
   ```
   # Example
   ```

3. Save the file

### 1.4 Download Virus Definitions

Open PowerShell as Administrator and run:
```powershell
cd "C:\Program Files\ClamAV"
.\freshclam.exe
```

This will download the latest virus definitions (may take several minutes).

### 1.5 Start ClamAV Daemon

In PowerShell:
```powershell
cd "C:\Program Files\ClamAV"
.\clamd.exe
```

Keep this window open. ClamAV daemon will run in the foreground.

**Note**: For production use, you can install ClamAV as a Windows service (see Advanced Setup below).

### 1.6 Verify ClamAV is Running

Open a new PowerShell window and test the connection:
```powershell
Test-NetConnection -ComputerName localhost -Port 3310
```

You should see `TcpTestSucceeded : True`.

## Step 2: Install HifzDefend

### 2.1 Get HifzDefend

**Option A: Clone with Git (Recommended)**
```bash
git clone --recurse-submodules <repository-url>
cd HifzDefend
```

**Option B: Download ZIP**
1. Download the repository as ZIP
2. Extract to `C:\Users\YourName\Documents\HifzDefend`
3. Open PowerShell in that directory

### 2.2 Run Bootstrap Script

This script automates the setup:
```bash
python scripts/bootstrap_dev.py
```

The script will:
- Create a virtual environment (`.venv`)
- Install all dependencies
- Set up pre-commit hooks
- Create default directories
- Generate default configuration

### 2.3 Activate Virtual Environment

```powershell
.venv\Scripts\activate
```

Your prompt should now show `(.venv)` at the beginning.

### 2.4 Verify Installation

```bash
# Check HifzDefend version
hifzdefend --version

# Check system status
hifzdefend status
```

You should see ClamAV daemon status as "Running".

## Step 3: Configure Windows Defender Exclusions

**IMPORTANT**: This step reduces system security and should only be done in development environments.

### 3.1 Preview Exclusions

```powershell
# Run as Administrator
.\scripts\setup_defender_exclusions.ps1 -WhatIf
```

### 3.2 Apply Exclusions

```powershell
# Run as Administrator
.\scripts\setup_defender_exclusions.ps1
```

This will add exclusions for:
- `tests/fixtures` (EICAR test files)
- `logs` directory
- `quarantine` directory
- `.venv` directory
- `%LOCALAPPDATA%\HifzDefend`
- Python and pytest processes

### 3.3 Verify Exclusions

```powershell
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
Get-MpPreference | Select-Object -ExpandProperty ExclusionProcess
```

## Step 4: Generate EICAR Test File

For testing malware detection:

```bash
python scripts/generate_eicar.py
```

This creates an encrypted EICAR test file at `tests/fixtures/eicar_test.zip`.

## Step 5: Test Installation

### 5.1 Test Status Command
```bash
hifzdefend status
```

Expected output:
```
✓ ClamAV daemon: Running
Version: ClamAV 0.103.x/...
```

### 5.2 Test Clean File Scan
```bash
hifzdefend scan README.md
```

Expected: No threats detected.

### 5.3 Test EICAR Detection
```bash
# Extract EICAR for testing (will be detected!)
python scripts/generate_eicar.py --plain --output tests/fixtures/eicar.txt

# Scan it
hifzdefend scan tests/fixtures/eicar.txt
```

Expected: Threat detected (EICAR-Test-File).

### 5.4 Run Test Suite
```bash
pytest
```

Expected: All tests pass (or skip if ClamAV not running).

## Advanced Setup

### Installing ClamAV as Windows Service

For production use, install ClamAV as a service:

1. Open PowerShell as Administrator
2. Navigate to ClamAV directory:
   ```powershell
   cd "C:\Program Files\ClamAV"
   ```
3. Install service:
   ```powershell
   .\clamd.exe --install
   ```
4. Start service:
   ```powershell
   Start-Service clamd
   ```
5. Verify service is running:
   ```powershell
   Get-Service clamd
   ```

### Automatic Virus Definition Updates

Set up a scheduled task for automatic updates:

1. Open Task Scheduler
2. Create Basic Task
3. Name: "ClamAV Update"
4. Trigger: Daily at 2:00 AM
5. Action: Start a program
6. Program: `C:\Program Files\ClamAV\freshclam.exe`
7. Finish

### Custom Configuration

Create custom configuration at `%LOCALAPPDATA%\HifzDefend\hifzdefend.toml`:

```toml
[clamav]
host = "localhost"
port = 3310
timeout = 60

[scanning]
max_file_size = 104857600
excluded_paths = [
    "C:\\MyProject\\.venv",
    "C:\\Users\\YourName\\AppData\\Local\\Temp",
]

[quarantine]
auto_quarantine = true
```

## Troubleshooting

### ClamAV Won't Start

**Problem**: `clamd.exe` fails to start

**Solutions**:
1. Check if another process is using port 3310:
   ```powershell
   netstat -ano | findstr :3310
   ```
2. Verify `clamd.conf` has `TCPSocket 3310` uncommented
3. Check Windows Firewall isn't blocking the port
4. Review ClamAV logs in `C:\Program Files\ClamAV\logs`

### HifzDefend Can't Connect to ClamAV

**Problem**: `hifzdefend status` shows "ClamAV daemon: Not running"

**Solutions**:
1. Ensure `clamd.exe` is running
2. Test port connectivity:
   ```powershell
   Test-NetConnection -ComputerName localhost -Port 3310
   ```
3. Check configuration in `hifzdefend.toml`
4. Try restarting ClamAV daemon

### Import Errors

**Problem**: `ModuleNotFoundError` when running `hifzdefend`

**Solutions**:
1. Ensure virtual environment is activated
2. Reinstall in development mode:
   ```bash
   pip install -e .
   ```
3. Check Python version is 3.10+:
   ```bash
   python --version
   ```

### Windows Defender Blocking Files

**Problem**: Windows Defender quarantines test files

**Solutions**:
1. Run exclusion script as Administrator:
   ```powershell
   .\scripts\setup_defender_exclusions.ps1
   ```
2. Temporarily disable real-time protection (not recommended)
3. Restore quarantined files from Windows Security

### Permission Denied Errors

**Problem**: Cannot create quarantine directory or logs

**Solutions**:
1. Run PowerShell as Administrator
2. Check NTFS permissions on project directory
3. Verify `%LOCALAPPDATA%` is writable

## Uninstallation

### Remove HifzDefend
```bash
# Deactivate virtual environment
deactivate

# Remove project directory
cd ..
rm -r HifzDefend
```

### Remove Windows Defender Exclusions
```powershell
# Run as Administrator
.\scripts\setup_defender_exclusions.ps1 -Remove
```

### Uninstall ClamAV
1. Open "Add or Remove Programs"
2. Find "ClamAV"
3. Click "Uninstall"
4. Follow prompts

## Next Steps

- Read [USAGE.md](USAGE.md) for CLI usage guide
- Review [DEVELOPMENT.md](DEVELOPMENT.md) if contributing
- Check [SECURITY.md](SECURITY.md) for security best practices

## Support

If you encounter issues not covered here:
1. Check existing GitHub issues
2. Review ClamAV documentation: https://docs.clamav.net/
3. Open a new issue with:
   - Operating system version
   - Python version
   - ClamAV version
   - Error messages and logs

# HifzDefend Installer Build Guide

This guide explains how to build the Windows installer for HifzDefend.

## Prerequisites

### Required Software

1. **Python 3.10+**
   - Download from https://www.python.org/downloads/

2. **PyInstaller**
   ```bash
   pip install pyinstaller
   ```

3. **NSIS 3.x** (Nullsoft Scriptable Install System)
   - Download from https://nsis.sourceforge.io/Download
   - Install to default location (C:\Program Files\NSIS)

4. **All HifzDefend dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Optional Tools

- **Resource Hacker** - For editing icons
- **Inno Setup** - Alternative to NSIS

## Building the Installer

### Quick Build

Run the automated build script:

```bash
python scripts/build_installer.py
```

This will:
1. Build the executable with PyInstaller
2. Package it with NSIS
3. Output: `dist/HifzDefend-0.3.0-Setup.exe`

### Manual Build Process

#### Step 1: Build Executable

```bash
pyinstaller --name=hifzdefend \
    --onefile \
    --windowed \
    --icon=assets/icon.ico \
    --add-data="src/hifzdefend/licensing/keys/public.pem;hifzdefend/licensing/keys" \
    --add-data="config/hifzdefend.toml.example;config" \
    src/hifzdefend/__main__.py
```

Output: `dist/hifzdefend.exe`

#### Step 2: Create Installer

```bash
"C:\Program Files\NSIS\makensis.exe" installer\hifzdefend.nsi
```

Output: `dist/HifzDefend-0.3.0-Setup.exe`

## Installer Configuration

### NSIS Script (installer/hifzdefend.nsi)

Key configuration:
- App name and version
- Installation directory
- File associations
- Start menu shortcuts
- Uninstaller
- Windows Defender exclusions

### Customization

Edit `installer/hifzdefend.nsi` to customize:

**Installation directory:**
```nsi
InstallDir "$PROGRAMFILES64\HifzDefend"
```

**Shortcuts:**
```nsi
CreateShortcut "$DESKTOP\HifzDefend.lnk" "$INSTDIR\hifzdefend.exe"
```

**Auto-start:**
```nsi
WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "HifzDefend" "$INSTDIR\hifzdefend.exe"
```

## Installer Features

### Included Components

- Main application executable
- Python runtime (embedded)
- Configuration templates
- License file
- Public key for license validation
- Shortcuts (desktop + start menu)
- Uninstaller

### Installation Steps

1. Welcome screen
2. License agreement
3. Installation directory selection
4. File copying
5. Registry keys creation
6. Shortcuts creation
7. Windows Defender exclusions (optional)
8. Completion

### Silent Installation

```cmd
HifzDefend-0.3.0-Setup.exe /S
```

Flags:
- `/S` - Silent install
- `/D=C:\Custom\Path` - Custom install directory

### Uninstallation

**GUI:**
- Settings → Apps → HifzDefend → Uninstall

**Silent:**
```cmd
"C:\Program Files\HifzDefend\Uninstall.exe" /S
```

## Code Signing

### Why Sign?

- Windows SmartScreen won't block
- Builds user trust
- Required for some enterprise environments

### How to Sign

1. **Get certificate:**
   - Purchase from DigiCert, Sectigo, etc.
   - Or use self-signed for testing

2. **Sign executable:**
   ```cmd
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist\hifzdefend.exe
   ```

3. **Sign installer:**
   ```cmd
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist\HifzDefend-0.3.0-Setup.exe
   ```

### Self-Signed Certificate (Testing Only)

```powershell
# Create certificate
$cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=HifzDefend" -CertStoreLocation Cert:\CurrentUser\My

# Export certificate
Export-PfxCertificate -Cert $cert -FilePath HifzDefend.pfx -Password (ConvertTo-SecureString -String "password" -Force -AsPlainText)

# Sign
signtool sign /f HifzDefend.pfx /p password /fd SHA256 dist\HifzDefend-0.3.0-Setup.exe
```

## Troubleshooting

### PyInstaller Issues

**Missing module:**
```bash
pyinstaller --hidden-import=missing_module ...
```

**DLL not found:**
```bash
pyinstaller --add-binary="path/to/dll.dll;." ...
```

**Too large:**
- Use `--onedir` instead of `--onefile`
- Exclude unnecessary packages: `--exclude-module=matplotlib`

### NSIS Issues

**File not found:**
- Check paths in .nsi script
- Use absolute paths or correct relative paths

**Permission denied:**
- Run as administrator
- Check file locks

**Wrong architecture:**
- Use `$PROGRAMFILES64` for 64-bit
- Use `$PROGRAMFILES32` for 32-bit

## Distribution

### Upload to GitHub Releases

```bash
gh release create v0.3.0 \
    dist/HifzDefend-0.3.0-Setup.exe \
    --title "HifzDefend v0.3.0" \
    --notes "See CHANGELOG.md for details"
```

### Checksum

Generate SHA256 checksum:

```powershell
certutil -hashfile dist\HifzDefend-0.3.0-Setup.exe SHA256
```

Include in release notes for verification.

## Auto-Update Integration

The installer integrates with HifzDefend's auto-update system:

1. Update checker queries GitHub releases
2. Finds latest `.exe` installer
3. Downloads installer
4. Runs installer with `/S /restart` flags
5. Installer updates files and restarts app

## Best Practices

1. **Version consistency:** Match version in all files
2. **Clean build:** Delete `build/` and `dist/` before building
3. **Test install:** Test on clean Windows VM
4. **Test uninstall:** Verify clean removal
5. **Code sign:** Always sign production releases
6. **Checksum:** Provide SHA256 for verification
7. **Release notes:** Include detailed changelog
8. **Backup:** Keep previous versions available

## File Sizes

Typical installer sizes:
- With embedded Python: ~80-120 MB
- With external Python: ~20-40 MB
- Compressed with LZMA: ~40-60 MB

## Resources

- NSIS Documentation: https://nsis.sourceforge.io/Docs/
- PyInstaller Manual: https://pyinstaller.org/en/stable/
- Code Signing Guide: https://docs.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools

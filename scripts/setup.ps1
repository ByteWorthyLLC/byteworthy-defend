# HifzDefend Installation Script
# Automated setup for Windows

param(
    [switch]$SkipApiKey,
    [switch]$NoClamAV,
    [string]$PythonVersion = "3.12"
)

# Colors for output
$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"
$Cyan = "Cyan"

Write-Host "`n" -NoNewline
Write-Host "========================================" -ForegroundColor $Cyan
Write-Host " HifzDefend Installation" -ForegroundColor $Cyan
Write-Host " Preserving Your Digital Safety (حفظ)" -ForegroundColor $Cyan
Write-Host "========================================" -ForegroundColor $Cyan
Write-Host ""

# Step 1: Check Python version
Write-Host "[1/7] Checking Python installation..." -ForegroundColor $Cyan

try {
    $pythonCommand = Get-Command python -ErrorAction Stop
    $pythonVersionOutput = python --version 2>&1
    Write-Host "[OK] Python found: $pythonVersionOutput" -ForegroundColor $Green

    # Parse version
    if ($pythonVersionOutput -match "Python (\d+)\.(\d+)\.(\d+)") {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]

        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
            Write-Host "[FAIL] Python 3.11+ required. Current: Python $major.$minor" -ForegroundColor $Red
            Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor $Yellow
            exit 1
        }
    }
}
catch {
    Write-Host "[FAIL] Python not found" -ForegroundColor $Red
    Write-Host "Please install Python 3.11+ from: https://www.python.org/downloads/" -ForegroundColor $Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor $Yellow
    exit 1
}

# Step 2: Create virtual environment
Write-Host "`n[2/7] Creating virtual environment..." -ForegroundColor $Cyan

$venvPath = ".venv312"

if (Test-Path $venvPath) {
    Write-Host "[OK] Virtual environment already exists" -ForegroundColor $Yellow
}
else {
    try {
        python -m venv $venvPath
        Write-Host "[OK] Virtual environment created: $venvPath" -ForegroundColor $Green
    }
    catch {
        Write-Host "[FAIL] Failed to create virtual environment" -ForegroundColor $Red
        Write-Host "Error: $_" -ForegroundColor $Red
        exit 1
    }
}

# Step 3: Activate virtual environment
Write-Host "`n[3/7] Activating virtual environment..." -ForegroundColor $Cyan

$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (Test-Path $activateScript) {
    try {
        & $activateScript
        Write-Host "[OK] Virtual environment activated" -ForegroundColor $Green
    }
    catch {
        Write-Host "[FAIL] Could not activate virtual environment" -ForegroundColor $Red
        Write-Host "Try running: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor $Yellow
        exit 1
    }
}
else {
    Write-Host "[FAIL] Activation script not found" -ForegroundColor $Red
    exit 1
}

# Step 4: Upgrade pip
Write-Host "`n[4/7] Upgrading pip..." -ForegroundColor $Cyan

try {
    python -m pip install --upgrade pip setuptools wheel -q
    Write-Host "[OK] Pip upgraded successfully" -ForegroundColor $Green
}
catch {
    Write-Host "[WARNING] Could not upgrade pip" -ForegroundColor $Yellow
}

# Step 5: Install HifzDefend
Write-Host "`n[5/7] Installing HifzDefend..." -ForegroundColor $Cyan

try {
    Write-Host "Installing core dependencies..." -ForegroundColor $Cyan
    pip install -e ".[dev]" -q
    Write-Host "[OK] Core dependencies installed" -ForegroundColor $Green

    Write-Host "Installing AI dependencies (anthropic, chromadb, sentence-transformers)..." -ForegroundColor $Cyan
    pip install anthropic chromadb sentence-transformers -q
    Write-Host "[OK] AI dependencies installed" -ForegroundColor $Green
}
catch {
    Write-Host "[FAIL] Installation failed" -ForegroundColor $Red
    Write-Host "Error: $_" -ForegroundColor $Red
    Write-Host "`nTry manual installation:" -ForegroundColor $Yellow
    Write-Host "  pip install -e "".[dev]""" -ForegroundColor $Yellow
    Write-Host "  pip install anthropic chromadb sentence-transformers" -ForegroundColor $Yellow
    exit 1
}

# Step 6: Check for Claude API key
Write-Host "`n[6/7] Checking Claude API key..." -ForegroundColor $Cyan

$apiKey = $env:CLAUDE_API_KEY

if (-not $apiKey) {
    Write-Host "[WARNING] CLAUDE_API_KEY not set" -ForegroundColor $Yellow

    if (-not $SkipApiKey) {
        Write-Host "`nTo use AI features, you need a Claude API key." -ForegroundColor $Cyan
        Write-Host "Get your key at: https://console.anthropic.com/settings/keys" -ForegroundColor $Cyan
        Write-Host ""

        $response = Read-Host "Do you have a Claude API key? (y/n)"

        if ($response -eq 'y' -or $response -eq 'Y') {
            $key = Read-Host "Enter your Claude API key (starts with sk-ant-)"

            if ($key -and $key.StartsWith("sk-ant-")) {
                try {
                    [Environment]::SetEnvironmentVariable("CLAUDE_API_KEY", $key, "User")
                    $env:CLAUDE_API_KEY = $key
                    Write-Host "[OK] API key saved!" -ForegroundColor $Green
                    Write-Host "Note: Restart your terminal for the change to take effect" -ForegroundColor $Yellow
                }
                catch {
                    Write-Host "[WARNING] Could not save API key permanently" -ForegroundColor $Yellow
                    Write-Host "Set manually: `$env:CLAUDE_API_KEY = 'your-key'" -ForegroundColor $Yellow
                }
            }
            else {
                Write-Host "[WARNING] Invalid API key format (should start with sk-ant-)" -ForegroundColor $Yellow
                Write-Host "You can set it later: `$env:CLAUDE_API_KEY = 'sk-ant-...'" -ForegroundColor $Yellow
            }
        }
        else {
            Write-Host "[OK] Skipping API key setup" -ForegroundColor $Yellow
            Write-Host "You can add it later: https://console.anthropic.com/settings/keys" -ForegroundColor $Yellow
        }
    }
}
else {
    Write-Host "[OK] API key found: $($apiKey.Substring(0, 12))..." -ForegroundColor $Green
}

# Step 7: Test installation
Write-Host "`n[7/7] Testing installation..." -ForegroundColor $Cyan

try {
    $version = hifzdefend --version 2>&1
    Write-Host "[OK] HifzDefend installed successfully!" -ForegroundColor $Green
    Write-Host "Version: $version" -ForegroundColor $Green
}
catch {
    Write-Host "[FAIL] Could not verify installation" -ForegroundColor $Red
    Write-Host "Error: $_" -ForegroundColor $Red
    exit 1
}

# ClamAV info
if (-not $NoClamAV) {
    Write-Host "`n[INFO] ClamAV Status:" -ForegroundColor $Cyan
    Write-Host "ClamAV is OPTIONAL for AI features." -ForegroundColor $Yellow
    Write-Host "AI script analysis works WITHOUT ClamAV." -ForegroundColor $Yellow
    Write-Host "Only needed for traditional antivirus scanning." -ForegroundColor $Yellow
    Write-Host "`nTo install ClamAV (optional):" -ForegroundColor $Cyan
    Write-Host "  Download from: https://www.clamav.net/downloads" -ForegroundColor $Cyan
}

# Success message
Write-Host "`n" -NoNewline
Write-Host "========================================" -ForegroundColor $Green
Write-Host " Installation Complete!" -ForegroundColor $Green
Write-Host "========================================" -ForegroundColor $Green
Write-Host ""

# Next steps
Write-Host "Next steps:" -ForegroundColor $Cyan
Write-Host "  1. " -NoNewline
Write-Host "Test AI features:" -ForegroundColor $Cyan
Write-Host "     hifzdefend query ""what is hifzdefend?""" -ForegroundColor $Yellow
Write-Host ""
Write-Host "  2. " -NoNewline
Write-Host "Analyze a script:" -ForegroundColor $Cyan
Write-Host "     echo ""Write-Host 'Hello, World!'""" -NoNewline -ForegroundColor $Yellow
Write-Host " > test.ps1" -ForegroundColor $Yellow
Write-Host "     hifzdefend analyze-script test.ps1" -ForegroundColor $Yellow
Write-Host ""
Write-Host "  3. " -NoNewline
Write-Host "View all commands:" -ForegroundColor $Cyan
Write-Host "     hifzdefend --help" -ForegroundColor $Yellow
Write-Host ""
Write-Host "  4. " -NoNewline
Write-Host "Read documentation:" -ForegroundColor $Cyan
Write-Host "     docs\QUICKSTART.md" -ForegroundColor $Yellow
Write-Host "     docs\AI_USAGE.md" -ForegroundColor $Yellow
Write-Host "     docs\TROUBLESHOOTING.md" -ForegroundColor $Yellow
Write-Host ""

if (-not $env:CLAUDE_API_KEY) {
    Write-Host "[REMINDER] Don't forget to set your Claude API key:" -ForegroundColor $Yellow
    Write-Host "  Get key: https://console.anthropic.com/settings/keys" -ForegroundColor $Yellow
    Write-Host "  Set key: `$env:CLAUDE_API_KEY = 'sk-ant-...'" -ForegroundColor $Yellow
    Write-Host ""
}

Write-Host "Need help? Check docs\TROUBLESHOOTING.md" -ForegroundColor $Cyan
Write-Host ""

# Create a test file for user to try
$testScript = @"
# Test script for HifzDefend
Write-Host "This is a safe test script"
Get-Date
"@

try {
    $testScript | Out-File -FilePath "test_script.ps1" -Encoding UTF8
    Write-Host "[OK] Created test_script.ps1 for you to analyze" -ForegroundColor $Green
}
catch {
    # Ignore if file creation fails
}

Write-Host "Happy scanning! 🛡️" -ForegroundColor $Green
Write-Host ""

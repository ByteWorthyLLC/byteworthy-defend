<#
.SYNOPSIS
    Set up Windows Defender exclusions for HifzDefend development.

.DESCRIPTION
    This script adds Windows Defender exclusions for HifzDefend directories
    and processes to prevent interference during development and testing.

    WARNING: This reduces system security. Only use in development environments
    and remove exclusions when no longer needed.

.PARAMETER WhatIf
    Preview changes without applying them.

.PARAMETER Remove
    Remove previously added exclusions.

.PARAMETER ProjectPath
    Path to HifzDefend project (default: C:\Users\richa\Documents\HifzDefend)

.EXAMPLE
    .\setup_defender_exclusions.ps1 -WhatIf
    Preview exclusions without applying.

.EXAMPLE
    .\setup_defender_exclusions.ps1
    Apply exclusions.

.EXAMPLE
    .\setup_defender_exclusions.ps1 -Remove
    Remove exclusions.

.NOTES
    Requires Administrator privileges.
#>

param(
    [switch]$WhatIf,
    [switch]$Remove,
    [string]$ProjectPath = "C:\Users\richa\Documents\HifzDefend"
)

# Check for Administrator privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script requires Administrator privileges." -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  HifzDefend - Windows Defender Exclusions" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Verify project path exists
if (-not (Test-Path $ProjectPath)) {
    Write-Host "ERROR: Project path not found: $ProjectPath" -ForegroundColor Red
    exit 1
}

Write-Host "Project path: $ProjectPath" -ForegroundColor White

# Define paths to exclude
$pathExclusions = @(
    Join-Path $ProjectPath "tests\fixtures"
    Join-Path $ProjectPath "logs"
    Join-Path $ProjectPath "reports"
    Join-Path $ProjectPath "quarantine"
    Join-Path $ProjectPath ".venv"
    Join-Path $ProjectPath "src"
    "$env:LOCALAPPDATA\HifzDefend"
)

# Define processes to exclude
$processExclusions = @(
    "python.exe"
    "pytest.exe"
)

# Define extensions to exclude (in project directories only)
$extensionExclusions = @(
    ".py"
    ".pyc"
    ".pyo"
)

Write-Host ""
Write-Host "Paths to exclude:" -ForegroundColor Yellow
foreach ($path in $pathExclusions) {
    Write-Host "  - $path"
}

Write-Host ""
Write-Host "Processes to exclude:" -ForegroundColor Yellow
foreach ($process in $processExclusions) {
    Write-Host "  - $process"
}

Write-Host ""

if ($WhatIf) {
    Write-Host "WhatIf mode: No changes will be made." -ForegroundColor Cyan
    Write-Host ""
    exit 0
}

if ($Remove) {
    Write-Host "Removing exclusions..." -ForegroundColor Yellow
    Write-Host ""

    # Remove path exclusions
    foreach ($path in $pathExclusions) {
        try {
            Remove-MpPreference -ExclusionPath $path -ErrorAction SilentlyContinue
            Write-Host "[OK] Removed path: $path" -ForegroundColor Green
        } catch {
            Write-Host "[SKIP] Path not found in exclusions: $path" -ForegroundColor Gray
        }
    }

    # Remove process exclusions
    foreach ($process in $processExclusions) {
        try {
            Remove-MpPreference -ExclusionProcess $process -ErrorAction SilentlyContinue
            Write-Host "[OK] Removed process: $process" -ForegroundColor Green
        } catch {
            Write-Host "[SKIP] Process not found in exclusions: $process" -ForegroundColor Gray
        }
    }

    Write-Host ""
    Write-Host "Exclusions removed successfully." -ForegroundColor Green
    Write-Host "Your system security has been restored." -ForegroundColor Green
} else {
    Write-Host "Adding exclusions..." -ForegroundColor Yellow
    Write-Host ""

    # Add path exclusions
    foreach ($path in $pathExclusions) {
        # Create directory if it doesn't exist
        if (-not (Test-Path $path)) {
            New-Item -ItemType Directory -Path $path -Force | Out-Null
            Write-Host "[CREATED] Directory: $path" -ForegroundColor Cyan
        }

        try {
            Add-MpPreference -ExclusionPath $path
            Write-Host "[OK] Added path: $path" -ForegroundColor Green
        } catch {
            Write-Host "[ERROR] Failed to add path: $path" -ForegroundColor Red
            Write-Host "  Error: $_" -ForegroundColor Red
        }
    }

    # Add process exclusions
    foreach ($process in $processExclusions) {
        try {
            Add-MpPreference -ExclusionProcess $process
            Write-Host "[OK] Added process: $process" -ForegroundColor Green
        } catch {
            Write-Host "[ERROR] Failed to add process: $process" -ForegroundColor Red
            Write-Host "  Error: $_" -ForegroundColor Red
        }
    }

    Write-Host ""
    Write-Host "=============================================" -ForegroundColor Cyan
    Write-Host "  Exclusions added successfully!" -ForegroundColor Green
    Write-Host "=============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "IMPORTANT SECURITY NOTES:" -ForegroundColor Yellow
    Write-Host "  - These exclusions reduce system security" -ForegroundColor Yellow
    Write-Host "  - Only use in development environments" -ForegroundColor Yellow
    Write-Host "  - Remove exclusions when done: .\setup_defender_exclusions.ps1 -Remove" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To verify exclusions:" -ForegroundColor Cyan
    Write-Host "  Get-MpPreference | Select-Object -ExpandProperty ExclusionPath" -ForegroundColor White
    Write-Host "  Get-MpPreference | Select-Object -ExpandProperty ExclusionProcess" -ForegroundColor White
}

Write-Host ""

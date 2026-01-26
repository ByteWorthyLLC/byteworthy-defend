# HifzDefend Launcher Script
# This script loads the .env file and runs HifzDefend with proper encoding

param(
    [Parameter(Position=0, Mandatory=$false)]
    [string]$Command,

    [Parameter(Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$hifzdefend = Join-Path $scriptDir ".venv\Scripts\hifzdefend.exe"

# Check if HifzDefend is installed
if (-not (Test-Path $hifzdefend)) {
    Write-Host "[ERROR] HifzDefend not found at: $hifzdefend" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install HifzDefend first:" -ForegroundColor Yellow
    Write-Host "  cd $scriptDir" -ForegroundColor White
    Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  pip install -e ." -ForegroundColor White
    exit 1
}

# Load .env file if it exists
$envFile = Join-Path $scriptDir ".env"
if (Test-Path $envFile) {
    Write-Host "[INFO] Loading environment variables from .env..." -ForegroundColor Cyan
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#')) {
            if ($line -match '^([^=]+)=(.*)$') {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                [Environment]::SetEnvironmentVariable($key, $value, 'Process')
                Write-Host "  [OK] Loaded: $key" -ForegroundColor Green
            }
        }
    }
    Write-Host ""
}

# Activate virtual environment
Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Cyan
& "$scriptDir\.venv\Scripts\Activate.ps1"

# Set Python encoding to UTF-8 to handle Rich library's Unicode
$env:PYTHONIOENCODING = "utf-8"

# Build command line
if ($Command) {
    $cmdLine = @($Command) + $Args
    Write-Host "[RUN] hifzdefend $($cmdLine -join ' ')" -ForegroundColor Cyan
    Write-Host ""
    & $hifzdefend @cmdLine
}
else {
    # No command - show help
    & $hifzdefend --help
}

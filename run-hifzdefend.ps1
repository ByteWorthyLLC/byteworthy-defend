# HifzDefend Easy Launcher
# Quick script to run HifzDefend commands

param(
    [Parameter(Position=0)]
    [string]$Command = "status",

    [Parameter(Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

# Activate virtual environment and run command
$venvPath = Join-Path $PSScriptRoot ".venv\Scripts"
$hifzdefend = Join-Path $venvPath "hifzdefend.exe"

if (-not (Test-Path $hifzdefend)) {
    Write-Host "ERROR: HifzDefend not found. Please run setup.ps1 first." -ForegroundColor Red
    exit 1
}

# Set UTF-8 encoding to handle Unicode
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "Running HifzDefend..." -ForegroundColor Cyan
Write-Host ""

# Run the command
& $hifzdefend $Command @Args

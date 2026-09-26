<#
.SYNOPSIS
    SceneDiff Backend Quality Gate Pipeline (Windows PowerShell)
    Validates Ruff linting, Ruff formatting, MyPy strict type checking, and Pytest.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"

Set-Location $BackendDir

# Resolve virtual environment python if available
$VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $VenvBin = Join-Path $BackendDir ".venv\Scripts"
    $env:PATH = "$VenvBin;$env:PATH"
}

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "==> 1/4 Running Ruff Lint Check..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
ruff check .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "==> 2/4 Running Ruff Format Verification..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
ruff format --check .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "==> 3/4 Running MyPy Strict Type Checking..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
mypy .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "==> 4/4 Running Pytest Test Suite..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
pytest -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==================================================" -ForegroundColor Green
Write-Host "==> ALL QUALITY GATES PASSED! Ready for commit. <=" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

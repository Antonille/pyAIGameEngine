[CmdletBinding()]
param(
    [switch]$ForcePyBullet
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $ProjectRoot

Write-Host "[pyAIGameEngine] Project root: $ProjectRoot" -ForegroundColor Cyan

$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    throw "Expected venv Python not found at $PythonExe. Create .venv first (recommended: py -3.12 -m venv .venv)."
}

function Invoke-Py {
    param([string[]]$PyArgs)
    & $PythonExe @PyArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed: $($PyArgs -join ' ')"
    }
}

function Install-PackageSafe {
    param([string]$Package)
    Write-Host "Installing $Package ..."
    & $PythonExe -m pip install $Package
    if ($LASTEXITCODE -ne 0) {
        throw "Failed installing $Package"
    }
}

Write-Host "Bootstrapping pip / packaging tools ..."
Invoke-Py -PyArgs @('-m', 'ensurepip', '--upgrade')
Invoke-Py -PyArgs @('-m', 'pip', 'install', '--upgrade', 'pip', 'wheel', 'setuptools<82')

Write-Host "Installing editable POC1 package ..."
Invoke-Py -PyArgs @('-m', 'pip', 'install', '-e', '.\POC1_SoaFirst')

$baselinePackages = @(
    'numpy',
    'pyglet',
    'moderngl',
    'gymnasium',
    'pettingzoo',
    'numba',
    'joblib',
    'pydantic',
    'matplotlib',
    'pillow'
)

foreach ($pkg in $baselinePackages) {
    Install-PackageSafe -Package $pkg
}

Write-Host "Checking MSVC / Windows SDK environment ..."
$msvcCheckScript = Join-Path $ProjectRoot 'scripts\windows\check_msvc_env.ps1'
$msvcReady = $false
try {
    & powershell -ExecutionPolicy Bypass -File $msvcCheckScript -Quiet
    $msvcReady = ($LASTEXITCODE -eq 0)
}
catch {
    Write-Warning "MSVC check script errored. PyBullet will be skipped for this run."
    Write-Warning $_.Exception.Message
    $msvcReady = $false
}

if ($msvcReady -or $ForcePyBullet) {
    try {
        Install-PackageSafe -Package 'pybullet'
    }
    catch {
        Write-Warning "PyBullet installation failed."
        Write-Warning $_.Exception.Message
        Write-Warning "Continuing with fallback-capable baseline install."
    }
}
else {
    Write-Warning "MSVC not configured in this shell. Skipping pybullet install."
    Write-Host "Use x64 Native Tools Command Prompt / Developer PowerShell for VS 2022, then rerun this script to enable PyBullet."
}

Write-Host "Installing torch CPU baseline ..."
Invoke-Py -PyArgs @('-m', 'pip', 'install', 'torch', 'torchvision', 'torchaudio')

Write-Host "Running import validation ..."
$validationCode = @"
import numpy, pyglet, moderngl, gymnasium, pettingzoo, numba, joblib, pydantic, torch
print("baseline imports ok")
"@
$tempFile = Join-Path $env:TEMP "pyaigameengine_validate_imports.py"
Set-Content -Path $tempFile -Value $validationCode -Encoding UTF8

& $PythonExe $tempFile
$validationExit = $LASTEXITCODE
Remove-Item $tempFile -ErrorAction SilentlyContinue

if ($validationExit -ne 0) {
    throw 'Baseline import validation failed.'
}

Write-Host "Install/update pass complete." -ForegroundColor Green
Write-Host "Next:"
Write-Host "  powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_poc1_validation.ps1"

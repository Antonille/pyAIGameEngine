[CmdletBinding()]
param(
    [ValidateSet("numpy", "numba")]
    [string]$BackendMode = "numpy",
    [switch]$TryPyBullet
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $ProjectRoot

$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    throw "Expected venv Python not found at $PythonExe"
}

$PocRoot = Join-Path $ProjectRoot "POC1_SoaFirst"
$BenchmarkScript = Join-Path $PocRoot "scripts\run_benchmark.py"
$RolloutScript = Join-Path $PocRoot "scripts\run_gym_rollout.py"
$ViewerScript = Join-Path $PocRoot "scripts\run_viewer.py"
$MSVCScript = Join-Path $ProjectRoot "scripts\windows\check_msvc_env.ps1"

Write-Host "[pyAIGameEngine] POC1 validation" -ForegroundColor Cyan

# Baseline import validation
$validationCode = @"
import numpy, pyglet, moderngl, gymnasium, pettingzoo, numba, joblib, pydantic, torch
print("baseline imports ok")
"@
$tempFile = Join-Path $env:TEMP "pyaigameengine_validate_runtime.py"
Set-Content -Path $tempFile -Value $validationCode -Encoding UTF8
& $PythonExe $tempFile
$baselineExit = $LASTEXITCODE
Remove-Item $tempFile -ErrorAction SilentlyContinue

if ($baselineExit -ne 0) {
    throw "Baseline imports failed."
}

# Quiet MSVC check
$msvcReady = $false
try {
    & powershell -ExecutionPolicy Bypass -File $MSVCScript -Quiet *> $null
    $msvcReady = ($LASTEXITCODE -eq 0)
}
catch {
    $msvcReady = $false
}

# Detect pybullet without surfacing traceback noise
$pybulletAvailable = $false
$pybulletCheckFile = Join-Path $env:TEMP "pyaigameengine_check_pybullet.py"
Set-Content -Path $pybulletCheckFile -Encoding UTF8 -Value @"
try:
    import pybullet  # noqa: F401
    raise SystemExit(0)
except Exception:
    raise SystemExit(1)
"@
& $PythonExe $pybulletCheckFile *> $null
$pybulletExit = $LASTEXITCODE
Remove-Item $pybulletCheckFile -ErrorAction SilentlyContinue

if ($pybulletExit -eq 0) {
    $pybulletAvailable = $true
}

$usePyBullet = $TryPyBullet -and $pybulletAvailable

if ($usePyBullet) {
    Write-Host "Using backend: pybullet"
} else {
    Write-Host "Using backend: simple ($BackendMode)"
}

if (Test-Path $BenchmarkScript) {
    if ($usePyBullet) {
        & $PythonExe $BenchmarkScript --backend pybullet
    } else {
        & $PythonExe $BenchmarkScript --backend-mode $BackendMode
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Benchmark failed."
    }
}

if (Test-Path $RolloutScript) {
    if ($usePyBullet) {
        & $PythonExe $RolloutScript --backend pybullet
    } else {
        & $PythonExe $RolloutScript --backend-mode $BackendMode
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Gym rollout failed."
    }
}

Write-Host "Viewer is optional/manual:"
Write-Host "$PythonExe .\\POC1_SoaFirst\\scripts\\run_viewer.py"

if (-not $pybulletAvailable) {
    Write-Warning "PyBullet is not installed in this .venv. Fallback backend validation passed; native physics validation was skipped."
    Write-Host "To enable PyBullet later, open a Visual Studio Developer shell and rerun install_project.ps1."
} elseif (-not $msvcReady) {
    Write-Warning "PyBullet is installed, but MSVC is not currently configured in this shell."
} elseif ($TryPyBullet) {
    Write-Host "Native PyBullet validation requested and attempted."
}

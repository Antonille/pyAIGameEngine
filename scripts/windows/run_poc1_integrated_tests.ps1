[CmdletBinding()]
param(
    [ValidateSet("numpy", "numba")]
    [string]$BackendMode = "numpy",
    [int]$Steps = 500,
    [int]$Bodies = 1024,
    [switch]$WarmupNumba,
    [ValidateSet("core", "with_adapter", "all")]
    [string]$SuiteGroup = "core",
    [string]$SnapshotId = "candidate_snapshot",
    [string]$ExecutionMode = "benchmark",
    [string]$Note
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $ProjectRoot
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    throw "Expected venv Python not found at $PythonExe"
}
$env:PYTHONPATH = (Join-Path $ProjectRoot "POC1_SoaFirst\src")
$ArgsList = @(
    (Join-Path $ProjectRoot "POC1_SoaFirst\scripts\run_integrated_tests.py"),
    "--backend-mode", $BackendMode,
    "--steps", "$Steps",
    "--bodies", "$Bodies",
    "--suite-group", $SuiteGroup,
    "--snapshot-id", $SnapshotId,
    "--execution-mode", $ExecutionMode
)
if ($WarmupNumba) { $ArgsList += "--warmup-numba" }
if ($Note) { $ArgsList += @("--note", $Note) }
& $PythonExe @ArgsList
if ($LASTEXITCODE -ne 0) {
    throw "Integrated test harness failed."
}

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
    [string]$Note,
    [string]$ConsoleLogPath
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $ProjectRoot
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    throw "Expected venv Python not found at $PythonExe"
}
$env:PYTHONPATH = (Join-Path $ProjectRoot "POC1_SoaFirst\src")

if (-not $ConsoleLogPath) {
    $LogsRoot = Join-Path $ProjectRoot "POC1_SoaFirst\artifacts\test\generated\console_logs"
    New-Item -ItemType Directory -Path $LogsRoot -Force | Out-Null
    $Timestamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
    $ConsoleLogPath = Join-Path $LogsRoot ("integrated_tests_{0}_{1}_{2}.log" -f $Timestamp, $SuiteGroup, $BackendMode)
}
Write-Host "console_log_path=$ConsoleLogPath"

$ArgsList = @(
    (Join-Path $ProjectRoot "POC1_SoaFirst\scripts\run_integrated_tests.py"),
    "--backend-mode", $BackendMode,
    "--steps", "$Steps",
    "--bodies", "$Bodies",
    "--suite-group", $SuiteGroup,
    "--snapshot-id", $SnapshotId,
    "--execution-mode", $ExecutionMode,
    "--console-log-path", $ConsoleLogPath
)
if ($WarmupNumba) { $ArgsList += "--warmup-numba" }
if ($Note) { $ArgsList += @("--note", $Note) }
& $PythonExe @ArgsList
if ($LASTEXITCODE -ne 0) {
    throw "Integrated test harness failed."
}

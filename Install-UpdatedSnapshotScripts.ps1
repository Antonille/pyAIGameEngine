[CmdletBinding()]
param(
    [string]$TargetScriptsRoot,
    [switch]$BackupExisting,
    [switch]$ShowPlannedActions
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$packageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceScriptsRoot = Join-Path $packageRoot 'scripts\windows'

if (-not (Test-Path -LiteralPath $sourceScriptsRoot)) {
    throw ('Source scripts folder not found: ' + $sourceScriptsRoot)
}

if ([string]::IsNullOrWhiteSpace($TargetScriptsRoot)) {
    $TargetScriptsRoot = $env:path_pyEngine_scripts
}
if ([string]::IsNullOrWhiteSpace($TargetScriptsRoot)) {
    throw 'TargetScriptsRoot was not provided and environment variable path_pyEngine_scripts is not set.'
}
if (-not (Test-Path -LiteralPath $TargetScriptsRoot)) {
    throw ('Target scripts folder does not exist: ' + $TargetScriptsRoot)
}

$timestamp = Get-Date -Format 'yyyy-MM-dd_HHmmss'
$backupRoot = Join-Path $TargetScriptsRoot ('archive_before_rev4_6_' + $timestamp)
$files = Get-ChildItem -LiteralPath $sourceScriptsRoot -File

foreach ($file in $files) {
    $targetPath = Join-Path $TargetScriptsRoot $file.Name
    if ($ShowPlannedActions) {
        Write-Host ('plan copy ' + $file.FullName + ' -> ' + $targetPath)
    }
}
if ($ShowPlannedActions) { return }

if ($BackupExisting) {
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    foreach ($file in $files) {
        $targetPath = Join-Path $TargetScriptsRoot $file.Name
        if (Test-Path -LiteralPath $targetPath) {
            Copy-Item -LiteralPath $targetPath -Destination (Join-Path $backupRoot $file.Name) -Force
            Write-Host ('backup=' + $targetPath)
        }
    }
    Write-Host ('backup_root=' + $backupRoot)
}

foreach ($file in $files) {
    $targetPath = Join-Path $TargetScriptsRoot $file.Name
    Copy-Item -LiteralPath $file.FullName -Destination $targetPath -Force
    Write-Host ('updated=' + $targetPath)
}

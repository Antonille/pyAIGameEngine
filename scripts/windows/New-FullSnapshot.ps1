[CmdletBinding()]
param(
    [string]$ProjectRoot = 'C:\PythonDev\Dev1\pyGames\pyAIGameEngine',
    [string]$RevisionsRoot = 'C:\PythonDev\Dev1\pyGames\Revs_pyAIGameEngine',
    [string]$SnapshotLabel = 'candidate_full_snapshot',
    [switch]$OpenFolder
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Resolve-ScriptDirectory {
    if ($PSScriptRoot) { return $PSScriptRoot }
    if ($MyInvocation.MyCommand.Path) { return (Split-Path -Parent $MyInvocation.MyCommand.Path) }
    return (Get-Location).Path
}

function Resolve-ProjectRoot([string]$ExplicitProjectRoot) {
    if ($ExplicitProjectRoot) {
        return (Resolve-Path -LiteralPath $ExplicitProjectRoot).Path
    }
    $scriptDir = Resolve-ScriptDirectory
    return (Resolve-Path -LiteralPath (Join-Path $scriptDir '..\..')).Path
}

function Get-RelativePathCompat([string]$FullPath, [string]$ProjectRootPath) {
    $relative = $FullPath.Substring($ProjectRootPath.Length)
    $relative = ($relative -replace '^[\\/]+', '')
    return $relative
}

function Should-ExcludePath([string]$FullPath, [string]$ProjectRootPath) {
    $relative = Get-RelativePathCompat -FullPath $FullPath -ProjectRootPath $ProjectRootPath
    if (-not $relative) { return $true }

    $normalized = $relative -replace '/', '\\'
    $parts = $normalized.Split('\\')
    foreach ($part in $parts) {
        if ($part -in @('.venv','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache','build','dist','snapshots_out','.git')) { return $true }
        if ($part -like '*.egg-info') { return $true }
        if ($part -like '*.pyc' -or $part -like '*.pyo' -or $part -like '*.nbc' -or $part -like '*.nbi') { return $true }
    }
    return $false
}

$ProjectRoot = Resolve-ProjectRoot -ExplicitProjectRoot $ProjectRoot
if (-not (Test-Path -LiteralPath $ProjectRoot)) { throw "Project root not found: $ProjectRoot" }
if (-not (Test-Path -LiteralPath $RevisionsRoot)) { New-Item -ItemType Directory -Path $RevisionsRoot | Out-Null }

$timestamp = Get-Date -Format 'yyyy-MM-dd_HHmmss'
$zipName = "pyAIGameEngine_${SnapshotLabel}_${timestamp}.zip"
$zipPath = Join-Path $RevisionsRoot $zipName

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("pyAIGameEngine_full_snapshot_" + [guid]::NewGuid().ToString('N'))
$stageRoot = Join-Path $tempRoot 'pyAIGameEngine'
New-Item -ItemType Directory -Path $stageRoot -Force | Out-Null

try {
    Get-ChildItem -LiteralPath $ProjectRoot -Recurse -Force -File | ForEach-Object {
        if (Should-ExcludePath -FullPath $_.FullName -ProjectRootPath $ProjectRoot) { return }
        $relative = Get-RelativePathCompat -FullPath $_.FullName -ProjectRootPath $ProjectRoot
        $target = Join-Path $stageRoot $relative
        $targetDir = Split-Path -Parent $target
        if (-not (Test-Path -LiteralPath $targetDir)) { New-Item -ItemType Directory -Path $targetDir -Force | Out-Null }
        Copy-Item -LiteralPath $_.FullName -Destination $target -Force
    }

    if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
    [System.IO.Compression.ZipFile]::CreateFromDirectory($tempRoot, $zipPath)

    Write-Host "created_full_snapshot=$zipPath"
    Write-Host "snapshot_layout=standard-root-folder"
    if ($OpenFolder) { Start-Process explorer.exe $RevisionsRoot | Out-Null }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) { Remove-Item -LiteralPath $tempRoot -Recurse -Force }
}

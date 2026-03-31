[CmdletBinding()]
param(
    [string]$ProjectRoot = 'C:\PythonDev\Dev1\pyGames\pyAIGameEngine',
    [string]$RevisionsRoot = 'C:\PythonDev\Dev1\pyGames\Revs_pyAIGameEngine',
    [ValidateSet('LastAny','LastFull')]
    [string]$SinceMode = 'LastAny',
    [string]$SnapshotLabel = 'candidate_sparse_snapshot',
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

function Get-ReferenceTime([string]$Root, [string]$Mode) {
    if (-not (Test-Path -LiteralPath $Root)) { throw "Revisions root not found: $Root" }
    $zips = Get-ChildItem -LiteralPath $Root -Filter *.zip -File | Sort-Object LastWriteTimeUtc -Descending
    if (-not $zips) { return [datetime]::MinValue }
    if ($Mode -eq 'LastAny') { return $zips[0].LastWriteTimeUtc }
    $full = $zips | Where-Object { $_.Name -match 'full' } | Select-Object -First 1
    if ($full) { return $full.LastWriteTimeUtc }
    return [datetime]::MinValue
}

$ProjectRoot = Resolve-ProjectRoot -ExplicitProjectRoot $ProjectRoot
if (-not (Test-Path -LiteralPath $ProjectRoot)) { throw "Project root not found: $ProjectRoot" }
if (-not (Test-Path -LiteralPath $RevisionsRoot)) { New-Item -ItemType Directory -Path $RevisionsRoot | Out-Null }

$referenceTime = Get-ReferenceTime -Root $RevisionsRoot -Mode $SinceMode
$timestamp = Get-Date -Format 'yyyy-MM-dd_HHmmss'
$zipName = "pyAIGameEngine_${SnapshotLabel}_${timestamp}.zip"
$zipPath = Join-Path $RevisionsRoot $zipName

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("pyAIGameEngine_sparse_snapshot_" + [guid]::NewGuid().ToString('N'))
$stageRoot = Join-Path $tempRoot 'pyAIGameEngine'
New-Item -ItemType Directory -Path $stageRoot -Force | Out-Null

$copiedCount = 0
try {
    Get-ChildItem -LiteralPath $ProjectRoot -Recurse -Force -File | ForEach-Object {
        if (Should-ExcludePath -FullPath $_.FullName -ProjectRootPath $ProjectRoot) { return }
        if ($_.LastWriteTimeUtc -le $referenceTime) { return }
        $relative = Get-RelativePathCompat -FullPath $_.FullName -ProjectRootPath $ProjectRoot
        $target = Join-Path $stageRoot $relative
        $targetDir = Split-Path -Parent $target
        if (-not (Test-Path -LiteralPath $targetDir)) { New-Item -ItemType Directory -Path $targetDir -Force | Out-Null }
        Copy-Item -LiteralPath $_.FullName -Destination $target -Force
        $copiedCount++
    }

    if ($copiedCount -eq 0) {
        Write-Warning "No files newer than reference time $referenceTime were found. No sparse snapshot created."
        return
    }

    if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
    [System.IO.Compression.ZipFile]::CreateFromDirectory($tempRoot, $zipPath)

    Write-Host "created_sparse_snapshot=$zipPath"
    Write-Host "snapshot_layout=standard-root-folder"
    Write-Host "files_included=$copiedCount"
    Write-Host "reference_time_utc=$referenceTime"
    if ($OpenFolder) { Start-Process explorer.exe $RevisionsRoot | Out-Null }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) { Remove-Item -LiteralPath $tempRoot -Recurse -Force }
}

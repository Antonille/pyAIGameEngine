[CmdletBinding()]
param(
    [string]$SnapshotsRoot = "C:\PythonDev\Dev1\pyGames\Revs_pyAIGameEngine",
    [string]$ProjectRoot   = "C:\PythonDev\Dev1\pyGames\pyAIGameEngine",
    [switch]$ClearProject,
    [string[]]$PreserveTopLevel = @('.venv', '.git', 'scripts')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-SnapshotKind([string]$Name) {
    $n = $Name.ToLowerInvariant()
    if ($n -match 'full_snapshot' -or $n -match 'candidate_full_snapshot') { return 'full' }
    if ($n -match 'sparse_snapshot' -or $n -match 'candidate_sparse_snapshot') { return 'sparse' }
    return 'unknown'
}

function Test-LegacySparseRootLayout {
    param([string]$Root)

    $markers = @(
        (Join-Path $Root 'pyproject.toml'),
        (Join-Path $Root 'docs'),
        (Join-Path $Root 'scripts'),
        (Join-Path $Root 'POC1_SoaFirst')
    )
    $hits = ($markers | Where-Object { Test-Path -LiteralPath $_ }).Count
    return ($hits -ge 2)
}

function New-NormalizedProjectFolder {
    param([string]$TempRoot)

    $normalizedRoot = Join-Path $TempRoot '__normalized_pyAIGameEngine'
    New-Item -ItemType Directory -Path $normalizedRoot -Force | Out-Null

    $wrapperNames = @('OPEN_THIS_FIRST.md', 'SNAPSHOT_INDEX.json')
    $wrapperPatterns = @('*_contents.txt')

    foreach ($item in Get-ChildItem -LiteralPath $TempRoot -Force) {
        if ($item.Name -eq '__normalized_pyAIGameEngine') { continue }
        if ($wrapperNames -contains $item.Name) { continue }
        if ($wrapperPatterns | Where-Object { $item.Name -like $_ }) { continue }
        Copy-Item -LiteralPath $item.FullName -Destination (Join-Path $normalizedRoot $item.Name) -Recurse -Force
    }

    return $normalizedRoot
}

function Expand-SnapshotToTemp {
    param([string]$ZipPath)

    $tempRoot = Join-Path $env:TEMP ("pyAIGameEngine_rebuild_" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $tempRoot | Out-Null
    Expand-Archive -Path $ZipPath -DestinationPath $tempRoot -Force

    $projectFolder = Join-Path $tempRoot 'pyAIGameEngine'
    if (Test-Path -LiteralPath $projectFolder) {
        return @{ TempRoot = $tempRoot; ProjectFolder = $projectFolder; SnapshotLayout = 'standard-root-folder' }
    }

    $candidate = Get-ChildItem -Path $tempRoot -Directory -Recurse |
        Where-Object { $_.Name -eq 'pyAIGameEngine' } |
        Select-Object -First 1
    if ($candidate) {
        return @{ TempRoot = $tempRoot; ProjectFolder = $candidate.FullName; SnapshotLayout = 'nested-root-folder' }
    }

    if (Test-LegacySparseRootLayout -Root $tempRoot) {
        $normalizedRoot = New-NormalizedProjectFolder -TempRoot $tempRoot
        return @{ TempRoot = $tempRoot; ProjectFolder = $normalizedRoot; SnapshotLayout = 'legacy-rootless-sparse' }
    }

    throw "Expanded snapshot is not recognized as a pyAIGameEngine snapshot: $ZipPath"
}

function Copy-Tree {
    param([string]$Source,[string]$Destination)
    robocopy $Source $Destination /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
    $rc = $LASTEXITCODE
    if ($rc -ge 8) { throw "robocopy failed with exit code $rc" }
}

function Clear-ProjectSafe {
    param([string]$Root,[string[]]$Preserve)
    foreach ($item in Get-ChildItem -LiteralPath $Root -Force) {
        if ($Preserve -contains $item.Name) {
            Write-Host "preserve=$($item.FullName)"
            continue
        }
        Remove-Item -LiteralPath $item.FullName -Recurse -Force
        Write-Host "removed=$($item.FullName)"
    }
}

$zips = Get-ChildItem -Path $SnapshotsRoot -File -Filter *.zip | Sort-Object LastWriteTimeUtc
if (-not $zips) { throw "No zip snapshots found in $SnapshotsRoot" }
$full = $zips | Where-Object { (Get-SnapshotKind $_.Name) -eq 'full' } | Select-Object -Last 1
if (-not $full) { throw "No full snapshot found in $SnapshotsRoot" }
$sparse = $zips | Where-Object { $_.LastWriteTimeUtc -gt $full.LastWriteTimeUtc -and (Get-SnapshotKind $_.Name) -eq 'sparse' } | Sort-Object LastWriteTimeUtc

Write-Host "full_snapshot=$($full.FullName)"
Write-Host "full_snapshot_lastwrite=$($full.LastWriteTime)"
Write-Host "sparse_count=$($sparse.Count)"
foreach ($s in $sparse) { Write-Host "apply_sparse=$($s.Name)" }

if ($ClearProject) {
    Clear-ProjectSafe -Root $ProjectRoot -Preserve $PreserveTopLevel
}

$allToApply = @($full) + @($sparse)
foreach ($zip in $allToApply) {
    $expanded = Expand-SnapshotToTemp -ZipPath $zip.FullName
    Write-Host "snapshot_layout[$($zip.Name)]=$($expanded.SnapshotLayout)"
    try {
        Copy-Tree -Source $expanded.ProjectFolder -Destination $ProjectRoot
        Write-Host "applied=$($zip.Name)"
    } finally {
        if (Test-Path -LiteralPath $expanded.TempRoot) {
            Remove-Item -LiteralPath $expanded.TempRoot -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}
Write-Host "rebuild_complete=$ProjectRoot"

[CmdletBinding()]
param(
    [string]$SnapshotsRoot = "C:\PythonDev\Dev1\pyGames\Revs_pyAIGameEngine",
    [string]$ProjectRoot   = "C:\PythonDev\Dev1\pyGames\pyAIGameEngine",
    [switch]$PreferSparse,
    [switch]$PreferFull,
    [switch]$ListOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-SnapshotKind([string]$Name) {
    $n = $Name.ToLowerInvariant()
    if ($n -match 'full_snapshot' -or $n -match 'candidate_full_snapshot') { return 'full' }
    if ($n -match 'sparse_snapshot' -or $n -match 'candidate_sparse_snapshot') { return 'sparse' }
    return 'unknown'
}

function Get-LatestSnapshot {
    param([string]$Root,[bool]$WantSparse,[bool]$WantFull)

    $items = Get-ChildItem -Path $Root -File -Filter *.zip | Sort-Object LastWriteTimeUtc
    if (-not $items) { throw "No zip snapshots found in $Root" }

    if ($WantSparse -and -not $WantFull) {
        $items = $items | Where-Object { (Get-SnapshotKind $_.Name) -eq 'sparse' }
    } elseif ($WantFull -and -not $WantSparse) {
        $items = $items | Where-Object { (Get-SnapshotKind $_.Name) -eq 'full' }
    }

    $latest = $items | Sort-Object LastWriteTimeUtc | Select-Object -Last 1
    if (-not $latest) { throw "No matching snapshot found in $Root" }
    return $latest
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

    $tempRoot = Join-Path $env:TEMP ("pyAIGameEngine_apply_" + [guid]::NewGuid().ToString('N'))
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

$latest = Get-LatestSnapshot -Root $SnapshotsRoot -WantSparse:$PreferSparse.IsPresent -WantFull:$PreferFull.IsPresent
$kind = Get-SnapshotKind $latest.Name
Write-Host "latest_snapshot=$($latest.FullName)"
Write-Host "snapshot_kind=$kind"
Write-Host "snapshot_lastwrite=$($latest.LastWriteTime)"
if ($ListOnly) { return }

$expanded = Expand-SnapshotToTemp -ZipPath $latest.FullName
Write-Host "snapshot_layout=$($expanded.SnapshotLayout)"
try {
    Copy-Tree -Source $expanded.ProjectFolder -Destination $ProjectRoot
    Write-Host "applied_snapshot_to=$ProjectRoot"
} finally {
    if (Test-Path -LiteralPath $expanded.TempRoot) {
        Remove-Item -LiteralPath $expanded.TempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

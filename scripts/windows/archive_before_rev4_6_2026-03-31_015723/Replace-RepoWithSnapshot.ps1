param(
    [Parameter(Mandatory = $true)]
    [string]$ZipPath,
    [string]$RepoRoot = "C:\PythonDev\Dev1\pyGames\pyAIGameEngine",
    [switch]$CreateCommit,
    [string]$CommitMessage = "Apply cleaned full snapshot"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $ZipPath)) {
    throw "Zip not found: $ZipPath"
}
if (-not (Test-Path -LiteralPath $RepoRoot)) {
    throw "Repo root not found: $RepoRoot"
}
if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot '.git'))) {
    throw "Repo root does not contain .git: $RepoRoot"
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("pyAIGameEngine_snapshot_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tempRoot | Out-Null
try {
    Expand-Archive -LiteralPath $ZipPath -DestinationPath $tempRoot -Force
    $snapshotRoot = Join-Path $tempRoot 'pyAIGameEngine'
    if (-not (Test-Path -LiteralPath $snapshotRoot)) {
        $dirs = Get-ChildItem -LiteralPath $tempRoot -Directory
        if ($dirs.Count -eq 1) {
            $snapshotRoot = $dirs[0].FullName
        }
    }
    if (-not (Test-Path -LiteralPath $snapshotRoot)) {
        throw "Could not locate extracted snapshot root under $tempRoot"
    }

    Get-ChildItem -LiteralPath $RepoRoot -Force | Where-Object { $_.Name -ne '.git' } | Remove-Item -Recurse -Force
    robocopy $snapshotRoot $RepoRoot /MIR /NFL /NDL /NJH /NJS /NP | Out-Null

    git -C $RepoRoot status --short
    if ($CreateCommit) {
        git -C $RepoRoot add -A
        git -C $RepoRoot commit -m $CommitMessage
    }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}

[CmdletBinding()]
param(
    [string]$SnapshotsRoot = "C:\PythonDev\Dev1\pyGames\Revs_pyAIGameEngine",
    [string]$ProjectRoot   = "C:\PythonDev\Dev1\pyGames\pyAIGameEngine",
    [switch]$PreferSparse,
    [switch]$PreferFull,
    [switch]$ListOnly,
    [switch]$ConfigureGitIdentity,
    [switch]$CommitAndPush,
    [string]$GitHubUsername = "Antonille",
    [string]$RepoName = "pyAIGameEngine",
    [string]$GitUserEmail = "scott.antonille@gmail.com",
    [string]$GitUserName = "Scott Antonille",
    [string]$BranchName = "main",
    [string]$CommitMessage = "Apply latest snapshot"
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

function Expand-SnapshotToTemp {
    param([string]$ZipPath)

    $tempRoot = Join-Path $env:TEMP ("pyAIGameEngine_apply_" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $tempRoot | Out-Null
    Expand-Archive -Path $ZipPath -DestinationPath $tempRoot -Force

    $projectFolder = Join-Path $tempRoot 'pyAIGameEngine'
    if (Test-Path -LiteralPath $projectFolder) {
        return @{ TempRoot = $tempRoot; ProjectFolder = $projectFolder; SnapshotLayout = 'full-root-folder' }
    }

    $rootMarkers = @(
        (Join-Path $tempRoot 'POC1_SoaFirst'),
        (Join-Path $tempRoot 'docs'),
        (Join-Path $tempRoot 'scripts'),
        (Join-Path $tempRoot 'pyproject.toml'),
        (Join-Path $tempRoot 'README.md'),
        (Join-Path $tempRoot 'SNAPSHOT_INDEX.json')
    )

    $markerHits = ($rootMarkers | Where-Object { Test-Path -LiteralPath $_ }).Count
    if ($markerHits -ge 2) {
        return @{ TempRoot = $tempRoot; ProjectFolder = $tempRoot; SnapshotLayout = 'legacy-sparse-root-layout' }
    }

    $candidate = Get-ChildItem -Path $tempRoot -Directory -Recurse |
        Where-Object { $_.Name -eq 'pyAIGameEngine' } |
        Select-Object -First 1

    if ($candidate) {
        return @{ TempRoot = $tempRoot; ProjectFolder = $candidate.FullName; SnapshotLayout = 'nested-full-root-folder' }
    }

    throw "Expanded snapshot is not recognized as a rooted or legacy sparse pyAIGameEngine snapshot: $ZipPath"
}

function Copy-Tree {
    param([string]$Source,[string]$Destination)
    robocopy $Source $Destination /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
    $rc = $LASTEXITCODE
    if ($rc -ge 8) { throw "robocopy failed with exit code $rc" }
}

function Invoke-Git {
    param(
        [string[]]$Arguments,
        [string]$WorkingDirectory
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = 'git'
    $psi.WorkingDirectory = $WorkingDirectory
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    foreach ($arg in $Arguments) {
        [void]$psi.ArgumentList.Add($arg)
    }

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi

    [void]$process.Start()
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()

    if ($stdout) {
        $stdout.TrimEnd("`r", "`n").Split([Environment]::NewLine) | ForEach-Object {
            if ($_ -ne '') { Write-Host $_ }
        }
    }
    if ($stderr) {
        $stderr.TrimEnd("`r", "`n").Split([Environment]::NewLine) | ForEach-Object {
            if ($_ -ne '') { Write-Warning $_ }
        }
    }

    if ($process.ExitCode -ne 0) {
        throw "git $($Arguments -join ' ') failed with exit code $($process.ExitCode)"
    }

    return @{
        StdOut = $stdout
        StdErr = $stderr
        ExitCode = $process.ExitCode
    }
}

function Update-GitRepo {
    param(
        [string]$RepoRoot,
        [string]$GitHubUsername,
        [string]$RepoName,
        [string]$GitUserEmail,
        [string]$GitUserName,
        [string]$BranchName,
        [string]$CommitMessage,
        [bool]$ConfigureIdentity
    )

    if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot '.git'))) {
        throw "Project root is not a git repository: $RepoRoot"
    }

    $remoteUrl = "https://github.com/$GitHubUsername/$RepoName.git"
    Write-Host "git_remote_url=$remoteUrl"

    if ($ConfigureIdentity) {
        Invoke-Git -WorkingDirectory $RepoRoot -Arguments @('config','user.email',$GitUserEmail) | Out-Null
        Invoke-Git -WorkingDirectory $RepoRoot -Arguments @('config','user.name',$GitUserName) | Out-Null
        Write-Host "git_user_email=$GitUserEmail"
        Write-Host "git_user_name=$GitUserName"
    }

    $hasOrigin = $true
    try {
        Invoke-Git -WorkingDirectory $RepoRoot -Arguments @('remote','get-url','origin') | Out-Null
    } catch {
        $hasOrigin = $false
    }

    if ($hasOrigin) {
        Invoke-Git -WorkingDirectory $RepoRoot -Arguments @('remote','set-url','origin',$remoteUrl) | Out-Null
    } else {
        Invoke-Git -WorkingDirectory $RepoRoot -Arguments @('remote','add','origin',$remoteUrl) | Out-Null
    }

    Invoke-Git -WorkingDirectory $RepoRoot -Arguments @('branch','-M',$BranchName) | Out-Null
    Write-Host 'git_staging_mode=all_changes'
    Write-Host 'git_staging_note=staging new files, modified files, and deletions via git add -A'
    Invoke-Git -WorkingDirectory $RepoRoot -Arguments @('add','-A') | Out-Null

    $statusResult = Invoke-Git -WorkingDirectory $RepoRoot -Arguments @('status','--porcelain')
    $statusLines = @()
    if ($statusResult.StdOut) {
        $statusLines = $statusResult.StdOut.TrimEnd("`r", "`n").Split([Environment]::NewLine) | Where-Object { $_ -ne '' }
    }

    if ($statusLines.Count -gt 0) {
        Write-Host 'git_changes_detected=true'
        Write-Host 'git_status_short_begin'
        $statusLines | ForEach-Object { Write-Host $_ }
        Write-Host 'git_status_short_end'
        Invoke-Git -WorkingDirectory $RepoRoot -Arguments @('commit','-m',$CommitMessage) | Out-Null
    } else {
        Write-Host 'git_changes_detected=false'
        Write-Host 'No tracked or staged changes detected after snapshot apply. Skipping commit.'
    }

    Invoke-Git -WorkingDirectory $RepoRoot -Arguments @('push','-u','origin',$BranchName) | Out-Null
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

    if ($CommitAndPush) {
        Update-GitRepo `
            -RepoRoot $ProjectRoot `
            -GitHubUsername $GitHubUsername `
            -RepoName $RepoName `
            -GitUserEmail $GitUserEmail `
            -GitUserName $GitUserName `
            -BranchName $BranchName `
            -CommitMessage $CommitMessage `
            -ConfigureIdentity:$ConfigureGitIdentity.IsPresent
    }
} finally {
    if (Test-Path -LiteralPath $expanded.TempRoot) {
        Remove-Item -LiteralPath $expanded.TempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

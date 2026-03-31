[CmdletBinding()]
param(
    [string]$SnapshotsRoot,
    [string]$ProjectRoot,
    [string]$ScriptsRoot,
    [switch]$ClearProject,
    [switch]$AllowDirtyRepo,
    [switch]$ConfigureGitIdentity,
    [switch]$CommitAndPush,
    [switch]$SetRemoteUrl,
    [string]$GitHubUsername,
    [string]$RepoName,
    [string]$GitUserEmail,
    [string]$GitUserName,
    [string]$BranchName,
    [string]$CommitMessage = 'Rebuild project from snapshots',
    [string[]]$PreserveTopLevel = @('.git','.venv')
)

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $here 'pyAIGameEngine.Common.ps1')

$context = Resolve-ProjectContext -ProjectRoot $ProjectRoot -ScriptsRoot $ScriptsRoot -RevisionsRoot $SnapshotsRoot -GitHubUsername $GitHubUsername -RepoName $RepoName -GitUserEmail $GitUserEmail -GitUserName $GitUserName -BranchName $BranchName

Write-Info ('runtime=' + $context.Runtime)
Write-Info ('project_root=' + $context.ProjectRoot)
Write-Info ('scripts_root=' + $context.ScriptsRoot)
Write-Info ('snapshots_root=' + $context.RevisionsRoot)

if ((Test-Path -LiteralPath (Join-Path $context.ProjectRoot '.git'))) {
    if ((-not $AllowDirtyRepo) -and (Test-GitRepoDirty -RepoRoot $context.ProjectRoot)) {
        throw 'Git working tree is dirty. Commit/stash changes first or rerun with -AllowDirtyRepo.'
    }
}

$inventory = Get-SnapshotInventory -Root $context.RevisionsRoot
$inventory = $inventory | Where-Object { $_.Kind -ne 'utility' }
if (-not $inventory) { throw ('No snapshot zip files found in ' + $context.RevisionsRoot) }

$full = $inventory | Where-Object { $_.Kind -eq 'full' } | Sort-Object TimestampUtc, Revision, Name | Select-Object -Last 1
if (-not $full) { throw ('No full snapshot found in ' + $context.RevisionsRoot) }

$incrementals = $inventory | Where-Object {
    ($_.Kind -eq 'sparse' -or $_.Kind -eq 'patch') -and $_.TimestampUtc -gt $full.TimestampUtc
} | Sort-Object TimestampUtc, Revision, Name

Write-Info ('full_snapshot=' + $full.FullName)
Write-Info ('full_snapshot_timestamp_utc=' + $full.TimestampUtc.ToString('o'))
Write-Info ('incremental_count=' + ($incrementals | Measure-Object).Count)
foreach ($entry in $incrementals) {
    Write-Info ('apply_incremental=' + $entry.Name)
}

if ($ClearProject) {
    Clear-ProjectKeep -ProjectRoot $context.ProjectRoot -PreserveTopLevel $PreserveTopLevel
}

$allToApply = @($full) + @($incrementals)
foreach ($record in $allToApply) {
    $expanded = Expand-SnapshotToTemp -ZipPath $record.FullName -TempPrefix 'pyAIGameEngine_rebuild'
    Write-Info ('snapshot_layout[' + $record.Name + ']=' + $expanded.SnapshotLayout)
    try {
        Invoke-RobocopyDirectory -Source $expanded.ProjectFolder -Destination $context.ProjectRoot
        Write-Info ('applied=' + $record.Name)
    } finally {
        if ($expanded -and $expanded.TempRoot -and (Test-Path -LiteralPath $expanded.TempRoot)) {
            Remove-Item -LiteralPath $expanded.TempRoot -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

if ($ConfigureGitIdentity -and -not $CommitAndPush) {
    Ensure-GitIdentityAndRemote -RepoRoot $context.ProjectRoot -GitHubUsername $context.GitHubUsername -RepoName $context.RepoName -GitUserEmail $context.GitUserEmail -GitUserName $context.GitUserName -BranchName $context.BranchName -SetRemoteUrl:$SetRemoteUrl.IsPresent
}

if ($CommitAndPush) {
    Ensure-GitIdentityAndRemote -RepoRoot $context.ProjectRoot -GitHubUsername $context.GitHubUsername -RepoName $context.RepoName -GitUserEmail $context.GitUserEmail -GitUserName $context.GitUserName -BranchName $context.BranchName -SetRemoteUrl:$SetRemoteUrl.IsPresent
    Commit-AndPushIfChanged -RepoRoot $context.ProjectRoot -BranchName $context.BranchName -CommitMessage $CommitMessage
}

Write-Info ('rebuild_complete=' + $context.ProjectRoot)

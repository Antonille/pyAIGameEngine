[CmdletBinding()]
param(
    [string]$SnapshotsRoot,
    [string]$ProjectRoot,
    [string]$ScriptsRoot,
    [ValidateSet('any','full','sparse','patch')]
    [string]$SnapshotKind = 'any',
    [ValidateSet('Overlay','Replace')]
    [string]$SyncMode = 'Overlay',
    [string]$ZipPath,
    [switch]$PreferSparse,
    [switch]$PreferFull,
    [switch]$ListOnly,
    [switch]$AllowDirtyRepo,
    [switch]$ConfigureGitIdentity,
    [switch]$CommitAndPush,
    [switch]$SetRemoteUrl,
    [string]$GitHubUsername,
    [string]$RepoName,
    [string]$GitUserEmail,
    [string]$GitUserName,
    [string]$BranchName,
    [string]$CommitMessage = 'Apply latest snapshot',
    [string[]]$PreserveTopLevel = @('.git','.venv')
)

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $here 'pyAIGameEngine.Common.ps1')

if ($PreferSparse) { $SnapshotKind = 'sparse' }
if ($PreferFull) { $SnapshotKind = 'full' }

$context = Resolve-ProjectContext -ProjectRoot $ProjectRoot -ScriptsRoot $ScriptsRoot -RevisionsRoot $SnapshotsRoot -GitHubUsername $GitHubUsername -RepoName $RepoName -GitUserEmail $GitUserEmail -GitUserName $GitUserName -BranchName $BranchName

Write-Info ('runtime=' + $context.Runtime)
Write-Info ('project_root=' + $context.ProjectRoot)
Write-Info ('scripts_root=' + $context.ScriptsRoot)
Write-Info ('snapshots_root=' + $context.RevisionsRoot)
Write-Info ('sync_mode=' + $SyncMode)

if ((Test-Path -LiteralPath (Join-Path $context.ProjectRoot '.git'))) {
    if ((-not $AllowDirtyRepo) -and (Test-GitRepoDirty -RepoRoot $context.ProjectRoot)) {
        throw 'Git working tree is dirty. Commit/stash changes first or rerun with -AllowDirtyRepo.'
    }
}

$inventory = Get-SnapshotInventory -Root $context.RevisionsRoot
if (-not $inventory) { throw ('No snapshot zip files found in ' + $context.RevisionsRoot) }

if ($ZipPath) {
    $zipResolved = Resolve-ExistingPath $ZipPath
    if (-not $zipResolved) { throw ('Specified ZipPath not found: ' + $ZipPath) }
    $record = $inventory | Where-Object { $_.FullName -eq $zipResolved } | Select-Object -First 1
    if (-not $record) {
        $item = Get-Item -LiteralPath $zipResolved
        $record = [pscustomobject]@{
            Name = $item.Name
            FullName = $item.FullName
            Kind = Get-SnapshotKindFromName $item.Name
            TimestampUtc = $item.LastWriteTimeUtc
            Revision = Convert-RevisionStringToNumber -Name $item.Name
            LastWriteTimeUtc = $item.LastWriteTimeUtc
            Manifest = Get-SnapshotManifestFromZip -ZipPath $item.FullName
        }
    }
} else {
    $record = Get-LatestSnapshotRecord -Inventory $inventory -SnapshotKind $SnapshotKind
}

Write-Info ('selected_snapshot=' + $record.FullName)
Write-Info ('selected_snapshot_kind=' + $record.Kind)
Write-Info ('selected_snapshot_timestamp_utc=' + $record.TimestampUtc.ToString('o'))
Write-Info ('selected_snapshot_revision=' + $record.Revision)

if ($ListOnly) {
    $inventory | Where-Object { $_.Kind -ne 'utility' } | Sort-Object TimestampUtc, Revision, Name | ForEach-Object {
        Write-Host ('candidate kind={0} timestamp_utc={1} revision={2} name={3}' -f $_.Kind, $_.TimestampUtc.ToString('o'), $_.Revision, $_.Name)
    }
    return
}

$expanded = Expand-SnapshotToTemp -ZipPath $record.FullName -TempPrefix 'pyAIGameEngine_apply'
Write-Info ('snapshot_layout=' + $expanded.SnapshotLayout)
try {
    if ($SyncMode -eq 'Replace') {
        Clear-ProjectKeep -ProjectRoot $context.ProjectRoot -PreserveTopLevel $PreserveTopLevel
    }
    Invoke-RobocopyDirectory -Source $expanded.ProjectFolder -Destination $context.ProjectRoot
    Write-Info ('applied_snapshot_to=' + $context.ProjectRoot)

    if ($ConfigureGitIdentity -and -not $CommitAndPush) {
        Ensure-GitIdentityAndRemote -RepoRoot $context.ProjectRoot -GitHubUsername $context.GitHubUsername -RepoName $context.RepoName -GitUserEmail $context.GitUserEmail -GitUserName $context.GitUserName -BranchName $context.BranchName -SetRemoteUrl:$SetRemoteUrl.IsPresent
    }

    if ($CommitAndPush) {
        Ensure-GitIdentityAndRemote -RepoRoot $context.ProjectRoot -GitHubUsername $context.GitHubUsername -RepoName $context.RepoName -GitUserEmail $context.GitUserEmail -GitUserName $context.GitUserName -BranchName $context.BranchName -SetRemoteUrl:$SetRemoteUrl.IsPresent
        Commit-AndPushIfChanged -RepoRoot $context.ProjectRoot -BranchName $context.BranchName -CommitMessage $CommitMessage
    }
} finally {
    if ($expanded -and $expanded.TempRoot -and (Test-Path -LiteralPath $expanded.TempRoot)) {
        Remove-Item -LiteralPath $expanded.TempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

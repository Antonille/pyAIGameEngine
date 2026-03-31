[CmdletBinding()]
param(
    [string]$ProjectRoot,
    [string]$ScriptsRoot,
    [string]$RevisionsRoot,
    [ValidateSet('LastAny','LastFull')]
    [string]$SinceMode = 'LastAny',
    [string]$SnapshotLabel = 'candidate_sparse_snapshot',
    [switch]$OpenFolder
)

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $here 'pyAIGameEngine.Common.ps1')

$context = Resolve-ProjectContext -ProjectRoot $ProjectRoot -ScriptsRoot $ScriptsRoot -RevisionsRoot $RevisionsRoot -GitHubUsername $null -RepoName 'pyAIGameEngine' -GitUserEmail $null -GitUserName $null -BranchName 'main'

Write-Info ('runtime=' + $context.Runtime)
Write-Info ('project_root=' + $context.ProjectRoot)
Write-Info ('scripts_root=' + $context.ScriptsRoot)
Write-Info ('revisions_root=' + $context.RevisionsRoot)

$inventory = Get-SnapshotInventory -Root $context.RevisionsRoot
$inventory = $inventory | Where-Object { $_.Kind -ne 'utility' }
$referenceTime = [datetime]::MinValue
if ($inventory) {
    if ($SinceMode -eq 'LastAny') {
        $referenceTime = ($inventory | Sort-Object TimestampUtc, Revision, Name | Select-Object -Last 1).TimestampUtc
    } else {
        $lastFull = $inventory | Where-Object { $_.Kind -eq 'full' } | Sort-Object TimestampUtc, Revision, Name | Select-Object -Last 1
        if ($lastFull) { $referenceTime = $lastFull.TimestampUtc }
    }
}

$timestamp = Get-Date -Format 'yyyy-MM-dd_HHmmss'
$zipName = ('pyAIGameEngine_{0}_{1}.zip' -f $SnapshotLabel, $timestamp)
$zipPath = Join-Path $context.RevisionsRoot $zipName
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('pyAIGameEngine_sparse_snapshot_' + [guid]::NewGuid().ToString('N'))
$stageRoot = Join-Path $tempRoot 'pyAIGameEngine'
New-Item -ItemType Directory -Path $stageRoot -Force | Out-Null

$copiedCount = 0
try {
    Get-ChildItem -LiteralPath $context.ProjectRoot -Recurse -Force -File | ForEach-Object {
        if (Should-ExcludePath -FullPath $_.FullName -ProjectRootPath $context.ProjectRoot) { return }
        if ($_.LastWriteTimeUtc -le $referenceTime) { return }
        $relative = Get-RelativePathCompat -FullPath $_.FullName -ProjectRootPath $context.ProjectRoot
        $target = Join-Path $stageRoot $relative
        $targetDir = Split-Path -Parent $target
        if (-not (Test-Path -LiteralPath $targetDir)) { New-Item -ItemType Directory -Path $targetDir -Force | Out-Null }
        Copy-Item -LiteralPath $_.FullName -Destination $target -Force
        $copiedCount++
    }

    if ($copiedCount -eq 0) {
        Write-Warning ('No files newer than reference time ' + $referenceTime.ToString('o') + ' were found. No sparse snapshot created.')
        return
    }

    $index = New-SnapshotIndexObject -SnapshotKind 'sparse' -ProjectRoot $context.ProjectRoot -ScriptsRoot $context.ScriptsRoot -SnapshotLabel $SnapshotLabel
    $index['reference_time_utc'] = $referenceTime.ToString('o')
    $index['files_included'] = $copiedCount
    Write-SnapshotIndexFile -StageRoot $stageRoot -SnapshotIndex $index

    if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
    [System.IO.Compression.ZipFile]::CreateFromDirectory($tempRoot, $zipPath)

    Write-Info ('created_sparse_snapshot=' + $zipPath)
    Write-Info 'snapshot_layout=standard-root-folder'
    Write-Info ('files_included=' + $copiedCount)
    Write-Info ('reference_time_utc=' + $referenceTime.ToString('o'))
    if ($OpenFolder) { Start-Process explorer.exe $context.RevisionsRoot | Out-Null }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) { Remove-Item -LiteralPath $tempRoot -Recurse -Force }
}

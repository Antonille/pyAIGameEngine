[CmdletBinding()]
param(
    [string]$ProjectRoot,
    [string]$ScriptsRoot,
    [string]$RevisionsRoot,
    [string]$SnapshotLabel = 'candidate_full_snapshot',
    [switch]$OpenFolder
)

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $here 'pyAIGameEngine.Common.ps1')

$context = Resolve-ProjectContext -ProjectRoot $ProjectRoot -ScriptsRoot $ScriptsRoot -RevisionsRoot $RevisionsRoot -GitHubUsername $null -RepoName 'pyAIGameEngine' -GitUserEmail $null -GitUserName $null -BranchName 'main'

Write-Info ('runtime=' + $context.Runtime)
Write-Info ('project_root=' + $context.ProjectRoot)
Write-Info ('scripts_root=' + $context.ScriptsRoot)
Write-Info ('revisions_root=' + $context.RevisionsRoot)

$timestamp = Get-Date -Format 'yyyy-MM-dd_HHmmss'
$zipName = ('pyAIGameEngine_{0}_{1}.zip' -f $SnapshotLabel, $timestamp)
$zipPath = Join-Path $context.RevisionsRoot $zipName
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('pyAIGameEngine_full_snapshot_' + [guid]::NewGuid().ToString('N'))
$stageRoot = Join-Path $tempRoot 'pyAIGameEngine'
New-Item -ItemType Directory -Path $stageRoot -Force | Out-Null

$fileCount = 0
try {
    Get-ChildItem -LiteralPath $context.ProjectRoot -Recurse -Force -File | ForEach-Object {
        if (Should-ExcludePath -FullPath $_.FullName -ProjectRootPath $context.ProjectRoot) { return }
        $relative = Get-RelativePathCompat -FullPath $_.FullName -ProjectRootPath $context.ProjectRoot
        $target = Join-Path $stageRoot $relative
        $targetDir = Split-Path -Parent $target
        if (-not (Test-Path -LiteralPath $targetDir)) { New-Item -ItemType Directory -Path $targetDir -Force | Out-Null }
        Copy-Item -LiteralPath $_.FullName -Destination $target -Force
        $fileCount++
    }

    $index = New-SnapshotIndexObject -SnapshotKind 'full' -ProjectRoot $context.ProjectRoot -ScriptsRoot $context.ScriptsRoot -SnapshotLabel $SnapshotLabel
    $index['files_included'] = $fileCount
    Write-SnapshotIndexFile -StageRoot $stageRoot -SnapshotIndex $index

    if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
    [System.IO.Compression.ZipFile]::CreateFromDirectory($tempRoot, $zipPath)

    Write-Info ('created_full_snapshot=' + $zipPath)
    Write-Info 'snapshot_layout=standard-root-folder'
    Write-Info ('files_included=' + $fileCount)
    if ($OpenFolder) { Start-Process explorer.exe $context.RevisionsRoot | Out-Null }
}
finally {
    if (Test-Path -LiteralPath $tempRoot) { Remove-Item -LiteralPath $tempRoot -Recurse -Force }
}

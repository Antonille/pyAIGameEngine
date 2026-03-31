[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Write-Info {
    param([string]$Message)
    Write-Host $Message
}

function Get-PowerShellRuntimeLabel {
    if ($PSVersionTable.PSEdition) {
        return ($PSVersionTable.PSEdition + ' ' + $PSVersionTable.PSVersion.ToString())
    }
    return ('Desktop ' + $PSVersionTable.PSVersion.ToString())
}

function Resolve-ExistingPath {
    param([string]$PathValue)
    if ([string]::IsNullOrWhiteSpace($PathValue)) { return $null }
    if (-not (Test-Path -LiteralPath $PathValue)) { return $null }
    return (Resolve-Path -LiteralPath $PathValue).Path
}

function Get-ParentDirectory {
    param([string]$PathValue,[int]$Levels)
    $current = $PathValue
    $i = 0
    while ($i -lt $Levels -and $current) {
        $current = Split-Path -Parent $current
        $i++
    }
    return $current
}

function Test-LooksLikeProjectRoot {
    param([string]$PathValue)
    if ([string]::IsNullOrWhiteSpace($PathValue)) { return $false }
    if (-not (Test-Path -LiteralPath $PathValue)) { return $false }
    $markers = @(
        (Join-Path $PathValue 'pyproject.toml'),
        (Join-Path $PathValue 'scripts\\windows'),
        (Join-Path $PathValue 'README.md'),
        (Join-Path $PathValue '.git')
    )
    $hits = ($markers | Where-Object { Test-Path -LiteralPath $_ }).Count
    return ($hits -ge 2)
}

function Test-LooksLikeScriptsRoot {
    param([string]$PathValue)
    if ([string]::IsNullOrWhiteSpace($PathValue)) { return $false }
    if (-not (Test-Path -LiteralPath $PathValue)) { return $false }
    $markers = @(
        (Join-Path $PathValue 'Apply-LatestSnapshot.ps1'),
        (Join-Path $PathValue 'Rebuild-ProjectFromSnapshots.ps1'),
        (Join-Path $PathValue 'New-SparseSnapshot.ps1'),
        (Join-Path $PathValue 'New-FullSnapshot.ps1')
    )
    $hits = ($markers | Where-Object { Test-Path -LiteralPath $_ }).Count
    return ($hits -ge 2)
}

function Test-LooksLikeRevisionsRoot {
    param([string]$PathValue)
    if ([string]::IsNullOrWhiteSpace($PathValue)) { return $false }
    if (-not (Test-Path -LiteralPath $PathValue)) {
        return ($PathValue -match 'Revs_pyAIGameEngine')
    }
    if ($PathValue -match 'Revs_pyAIGameEngine') { return $true }
    $zipCount = (Get-ChildItem -LiteralPath $PathValue -Filter *.zip -File -ErrorAction SilentlyContinue | Measure-Object).Count
    return ($zipCount -ge 1)
}

function Resolve-ProjectContext {
    param(
        [string]$ProjectRoot,
        [string]$ScriptsRoot,
        [string]$RevisionsRoot,
        [string]$GitHubUsername,
        [string]$RepoName,
        [string]$GitUserEmail,
        [string]$GitUserName,
        [string]$BranchName
    )

    $envProject = $env:path_pyAIGameEngine
    $envScripts = $env:path_pyEngine_scripts
    $envRevisions = $env:path_revs_pyAIGameEngine
    if ([string]::IsNullOrWhiteSpace($envRevisions) -and -not [string]::IsNullOrWhiteSpace($env:path_revs_pyAIGameEmpirre)) {
        $envRevisions = $env:path_revs_pyAIGameEmpirre
    }

    $resolvedScripts = Resolve-ExistingPath $ScriptsRoot
    if (-not $resolvedScripts) { $resolvedScripts = Resolve-ExistingPath $envScripts }
    if (-not $resolvedScripts) {
        if ($PSScriptRoot -and (Test-LooksLikeScriptsRoot $PSScriptRoot)) {
            $resolvedScripts = (Resolve-Path -LiteralPath $PSScriptRoot).Path
        }
    }

    $derivedProjectFromScripts = $null
    if ($resolvedScripts) {
        $candidate = Get-ParentDirectory -PathValue $resolvedScripts -Levels 2
        if (Test-LooksLikeProjectRoot $candidate) {
            $derivedProjectFromScripts = (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    $resolvedProject = Resolve-ExistingPath $ProjectRoot
    if (-not (Test-LooksLikeProjectRoot $resolvedProject)) { $resolvedProject = $null }

    $envProjectResolved = Resolve-ExistingPath $envProject
    if (Test-LooksLikeProjectRoot $envProjectResolved) {
        if (-not $resolvedProject) { $resolvedProject = $envProjectResolved }
    }

    if (-not $resolvedProject -and $derivedProjectFromScripts) {
        $resolvedProject = $derivedProjectFromScripts
    }

    if (-not $resolvedProject) {
        throw 'Unable to resolve project root. Set environment variable path_pyAIGameEngine to the repo root or path_pyEngine_scripts to the scripts\\windows folder.'
    }

    if (-not $resolvedScripts) {
        $candidate = Join-Path $resolvedProject 'scripts\\windows'
        if (Test-LooksLikeScriptsRoot $candidate) {
            $resolvedScripts = (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    if (-not $resolvedScripts) {
        throw 'Unable to resolve scripts root. Set environment variable path_pyEngine_scripts to the scripts\\windows folder.'
    }

    $resolvedRevisions = Resolve-ExistingPath $RevisionsRoot
    if (-not (Test-LooksLikeRevisionsRoot $resolvedRevisions)) { $resolvedRevisions = $null }
    if (-not $resolvedRevisions -and -not [string]::IsNullOrWhiteSpace($RevisionsRoot) -and (Test-LooksLikeRevisionsRoot $RevisionsRoot)) {
        $resolvedRevisions = $RevisionsRoot
    }

    $envRevisionsResolved = Resolve-ExistingPath $envRevisions
    if (Test-LooksLikeRevisionsRoot $envRevisionsResolved) {
        if (-not $resolvedRevisions) { $resolvedRevisions = $envRevisionsResolved }
    }
    if (-not $resolvedRevisions -and -not [string]::IsNullOrWhiteSpace($envRevisions) -and (Test-LooksLikeRevisionsRoot $envRevisions)) {
        $resolvedRevisions = $envRevisions
    }

    if (-not $resolvedRevisions -and $envProjectResolved -and (Test-LooksLikeRevisionsRoot $envProjectResolved) -and (-not (Test-LooksLikeProjectRoot $envProjectResolved))) {
        $resolvedRevisions = $envProjectResolved
    }

    if (-not $resolvedRevisions) {
        $defaultRevs = Join-Path (Split-Path -Parent $resolvedProject) 'Revs_pyAIGameEngine'
        if (Test-LooksLikeRevisionsRoot $defaultRevs) {
            $resolvedRevisions = $defaultRevs
        } else {
            $resolvedRevisions = $defaultRevs
            if (-not (Test-Path -LiteralPath $resolvedRevisions)) {
                New-Item -ItemType Directory -Path $resolvedRevisions -Force | Out-Null
            }
        }
    }

    if (-not (Test-Path -LiteralPath $resolvedRevisions)) {
        New-Item -ItemType Directory -Path $resolvedRevisions -Force | Out-Null
    }

    $resolvedGitHubUsername = $GitHubUsername
    if ([string]::IsNullOrWhiteSpace($resolvedGitHubUsername)) {
        $resolvedGitHubUsername = Get-GitHubUsernameFromOrigin -RepoRoot $resolvedProject
    }
    if ([string]::IsNullOrWhiteSpace($resolvedGitHubUsername) -and -not [string]::IsNullOrWhiteSpace($env:GITHUB_USERNAME)) {
        $resolvedGitHubUsername = $env:GITHUB_USERNAME
    }
    if ([string]::IsNullOrWhiteSpace($resolvedGitHubUsername)) {
        $resolvedGitHubUsername = 'Antonille'
    }

    $resolvedRepoName = $RepoName
    if ([string]::IsNullOrWhiteSpace($resolvedRepoName)) { $resolvedRepoName = 'pyAIGameEngine' }

    $resolvedGitUserEmail = $GitUserEmail
    if ([string]::IsNullOrWhiteSpace($resolvedGitUserEmail)) { $resolvedGitUserEmail = 'Scott.Antonille@gmail.com' }

    $resolvedGitUserName = $GitUserName
    if ([string]::IsNullOrWhiteSpace($resolvedGitUserName)) { $resolvedGitUserName = 'Scott Antonille' }

    $resolvedBranchName = $BranchName
    if ([string]::IsNullOrWhiteSpace($resolvedBranchName)) { $resolvedBranchName = 'main' }

    return [pscustomobject]@{
        ProjectRoot = $resolvedProject
        ScriptsRoot = $resolvedScripts
        RevisionsRoot = $resolvedRevisions
        GitHubUsername = $resolvedGitHubUsername
        RepoName = $resolvedRepoName
        GitUserEmail = $resolvedGitUserEmail
        GitUserName = $resolvedGitUserName
        BranchName = $resolvedBranchName
        Runtime = Get-PowerShellRuntimeLabel
    }
}

function Get-GitHubUsernameFromOrigin {
    param([string]$RepoRoot)
    if ([string]::IsNullOrWhiteSpace($RepoRoot)) { return $null }
    if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot '.git'))) { return $null }
    try {
        $origin = (& git -C $RepoRoot remote get-url origin 2>$null)
        if (-not $origin) { return $null }
        $originText = ($origin | Select-Object -First 1).ToString().Trim()
        if ($originText -match 'github\.com[:/](?<owner>[^/]+)/(?<repo>[^/.]+)(\.git)?$') {
            return $matches['owner']
        }
    } catch {
        return $null
    }
    return $null
}

function Invoke-GitCommand {
    param([string]$RepoRoot,[string[]]$Arguments)
    $output = & git -C $RepoRoot @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    if ($output) { $output | ForEach-Object { Write-Host $_ } }
    if ($exitCode -ne 0) {
        throw ('git ' + ($Arguments -join ' ') + ' failed with exit code ' + $exitCode)
    }
    return $output
}

function Test-GitRepoDirty {
    param([string]$RepoRoot)
    if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot '.git'))) { return $false }
    $status = & git -C $RepoRoot status --porcelain 2>$null
    return [bool]$status
}

function Ensure-GitIdentityAndRemote {
    param(
        [string]$RepoRoot,
        [string]$GitHubUsername,
        [string]$RepoName,
        [string]$GitUserEmail,
        [string]$GitUserName,
        [string]$BranchName,
        [switch]$SetRemoteUrl
    )
    if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot '.git'))) {
        throw ('Project root is not a git repository: ' + $RepoRoot)
    }
    Invoke-GitCommand -RepoRoot $RepoRoot -Arguments @('config','user.email',$GitUserEmail) | Out-Null
    Invoke-GitCommand -RepoRoot $RepoRoot -Arguments @('config','user.name',$GitUserName) | Out-Null
    Invoke-GitCommand -RepoRoot $RepoRoot -Arguments @('branch','-M',$BranchName) | Out-Null

    if ($SetRemoteUrl) {
        $remoteUrl = ('https://github.com/{0}/{1}.git' -f $GitHubUsername, $RepoName)
        $hasOrigin = $true
        try {
            Invoke-GitCommand -RepoRoot $RepoRoot -Arguments @('remote','get-url','origin') | Out-Null
        } catch {
            $hasOrigin = $false
        }
        if ($hasOrigin) {
            Invoke-GitCommand -RepoRoot $RepoRoot -Arguments @('remote','set-url','origin',$remoteUrl) | Out-Null
        } else {
            Invoke-GitCommand -RepoRoot $RepoRoot -Arguments @('remote','add','origin',$remoteUrl) | Out-Null
        }
        Write-Info ('git_remote_url=' + $remoteUrl)
    }
}

function Commit-AndPushIfChanged {
    param(
        [string]$RepoRoot,
        [string]$BranchName,
        [string]$CommitMessage
    )
    Invoke-GitCommand -RepoRoot $RepoRoot -Arguments @('add','-A') | Out-Null
    $status = & git -C $RepoRoot status --porcelain 2>$null
    if ($status) {
        Write-Info 'git_changes_detected=true'
        Invoke-GitCommand -RepoRoot $RepoRoot -Arguments @('commit','-m',$CommitMessage) | Out-Null
    } else {
        Write-Info 'git_changes_detected=false'
        Write-Info 'No changes detected. Skipping commit.'
    }
    Invoke-GitCommand -RepoRoot $RepoRoot -Arguments @('push','-u','origin',$BranchName) | Out-Null
}

function Get-SnapshotKindFromName {
    param([string]$Name)
    $n = $Name.ToLowerInvariant()
    if ($n -match 'snapshot_script_updates' -or $n -match 'console_log_capture' -or $n -match 'support_bundle' -or $n -match 'log_capture' -or $n -match 'tooling_only') { return 'utility' }
    if ($n -match 'full_snapshot' -or $n -match 'candidate_full_snapshot') { return 'full' }
    if ($n -match 'sparse_snapshot' -or $n -match 'candidate_sparse_snapshot') { return 'sparse' }
    if ($n -match '(_|-)patch(\.zip)?$' -or $n -match 'candidate_patch' -or $n -match 'rev[0-9._-]+_patch') { return 'patch' }
    return 'unknown'
}

function Convert-RevisionStringToNumber {
    param([string]$Name)
    if ([string]::IsNullOrWhiteSpace($Name)) { return 0.0 }
    if ($Name -match 'REV(?<rev>[0-9]+(?:\.[0-9]+)?)') {
        return [double]::Parse($matches['rev'], [System.Globalization.CultureInfo]::InvariantCulture)
    }
    if ($Name -match 'rev(?<rev>[0-9]+(?:_[0-9]+)?)') {
        $revText = ($matches['rev'] -replace '_', '.')
        return [double]::Parse($revText, [System.Globalization.CultureInfo]::InvariantCulture)
    }
    return 0.0
}

function Get-TimestampFromNameOrFallback {
    param([string]$Name,[datetime]$Fallback)
    if ($Name -match '(?<stamp>20[0-9]{2}-[01][0-9]-[0-3][0-9]_[0-2][0-9][0-5][0-9][0-5][0-9])') {
        try {
            return [datetime]::ParseExact($matches['stamp'],'yyyy-MM-dd_HHmmss',[System.Globalization.CultureInfo]::InvariantCulture,[System.Globalization.DateTimeStyles]::AssumeLocal)
        } catch {
            return $Fallback
        }
    }
    return $Fallback
}

function Get-SnapshotManifestFromZip {
    param([string]$ZipPath)
    $zip = $null
    try {
        $zip = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
        $entry = $zip.Entries | Where-Object {
            $_.FullName -eq 'pyAIGameEngine/SNAPSHOT_INDEX.json' -or $_.FullName -eq 'SNAPSHOT_INDEX.json'
        } | Select-Object -First 1
        if (-not $entry) { return $null }
        $stream = $entry.Open()
        $reader = New-Object System.IO.StreamReader($stream)
        try {
            $jsonText = $reader.ReadToEnd()
            if ([string]::IsNullOrWhiteSpace($jsonText)) { return $null }
            return ($jsonText | ConvertFrom-Json)
        } finally {
            $reader.Dispose()
            $stream.Dispose()
        }
    } catch {
        return $null
    } finally {
        if ($zip) { $zip.Dispose() }
    }
}

function Get-SnapshotInventory {
    param([string]$Root)
    if (-not (Test-Path -LiteralPath $Root)) { throw ('Snapshots root not found: ' + $Root) }
    $items = Get-ChildItem -LiteralPath $Root -Filter *.zip -File -ErrorAction Stop
    $result = @()
    foreach ($item in $items) {
        $manifest = Get-SnapshotManifestFromZip -ZipPath $item.FullName
        $kind = $null
        if ($manifest -and $manifest.snapshot_kind) { $kind = $manifest.snapshot_kind.ToString().ToLowerInvariant() }
        if ([string]::IsNullOrWhiteSpace($kind)) { $kind = Get-SnapshotKindFromName $item.Name }
        $timestamp = $item.LastWriteTimeUtc
        if ($manifest -and $manifest.created_utc) {
            try {
                $timestamp = [datetime]::Parse($manifest.created_utc.ToString(), [System.Globalization.CultureInfo]::InvariantCulture, [System.Globalization.DateTimeStyles]::RoundtripKind)
            } catch {
                $timestamp = Get-TimestampFromNameOrFallback -Name $item.Name -Fallback $item.LastWriteTimeUtc
            }
        } else {
            $timestamp = Get-TimestampFromNameOrFallback -Name $item.Name -Fallback $item.LastWriteTimeUtc
        }
        $revision = Convert-RevisionStringToNumber -Name $item.Name
        $result += [pscustomobject]@{
            Name = $item.Name
            FullName = $item.FullName
            Kind = $kind
            TimestampUtc = $timestamp.ToUniversalTime()
            Revision = $revision
            LastWriteTimeUtc = $item.LastWriteTimeUtc
            Manifest = $manifest
        }
    }
    return $result | Sort-Object @{Expression='TimestampUtc';Descending=$false}, @{Expression='Revision';Descending=$false}, @{Expression='Name';Descending=$false}
}

function Select-SnapshotCandidates {
    param([object[]]$Inventory,[string]$SnapshotKind)
    $filtered = $Inventory | Where-Object { $_.Kind -ne 'utility' }
    if (-not [string]::IsNullOrWhiteSpace($SnapshotKind) -and $SnapshotKind -ne 'any') {
        $filtered = $filtered | Where-Object { $_.Kind -eq $SnapshotKind }
    }
    return $filtered
}

function Get-LatestSnapshotRecord {
    param([object[]]$Inventory,[string]$SnapshotKind)
    $filtered = Select-SnapshotCandidates -Inventory $Inventory -SnapshotKind $SnapshotKind
    if (-not $filtered) {
        throw ('No matching snapshot candidates found for kind=' + $SnapshotKind)
    }
    return ($filtered | Sort-Object @{Expression='TimestampUtc';Descending=$false}, @{Expression='Revision';Descending=$false}, @{Expression='Name';Descending=$false} | Select-Object -Last 1)
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
    $wrapperNames = @('OPEN_THIS_FIRST.md','SNAPSHOT_INDEX.json')
    $wrapperPatterns = @('*_contents.txt')
    foreach ($item in Get-ChildItem -LiteralPath $TempRoot -Force) {
        if ($item.Name -eq '__normalized_pyAIGameEngine') { continue }
        if ($wrapperNames -contains $item.Name) { continue }
        $skip = $false
        foreach ($pattern in $wrapperPatterns) {
            if ($item.Name -like $pattern) { $skip = $true; break }
        }
        if ($skip) { continue }
        Copy-Item -LiteralPath $item.FullName -Destination (Join-Path $normalizedRoot $item.Name) -Recurse -Force
    }
    return $normalizedRoot
}

function Expand-SnapshotToTemp {
    param([string]$ZipPath,[string]$TempPrefix)
    $tempRoot = Join-Path $env:TEMP (($TempPrefix) + '_' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
    Expand-Archive -Path $ZipPath -DestinationPath $tempRoot -Force

    $rootProject = Join-Path $tempRoot 'pyAIGameEngine'
    if (Test-Path -LiteralPath $rootProject) {
        return @{ TempRoot = $tempRoot; ProjectFolder = $rootProject; SnapshotLayout = 'standard-root-folder' }
    }

    $candidate = Get-ChildItem -Path $tempRoot -Directory -Recurse | Where-Object { $_.Name -eq 'pyAIGameEngine' } | Select-Object -First 1
    if ($candidate) {
        return @{ TempRoot = $tempRoot; ProjectFolder = $candidate.FullName; SnapshotLayout = 'nested-root-folder' }
    }

    if (Test-LegacySparseRootLayout -Root $tempRoot) {
        $normalized = New-NormalizedProjectFolder -TempRoot $tempRoot
        return @{ TempRoot = $tempRoot; ProjectFolder = $normalized; SnapshotLayout = 'legacy-rootless-sparse' }
    }

    throw ('Expanded snapshot is not recognized as a pyAIGameEngine snapshot: ' + $ZipPath)
}

function Invoke-RobocopyDirectory {
    param([string]$Source,[string]$Destination)
    robocopy $Source $Destination /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
    $rc = $LASTEXITCODE
    if ($rc -ge 8) { throw ('robocopy failed with exit code ' + $rc) }
}

function Clear-ProjectKeep {
    param([string]$ProjectRoot,[string[]]$PreserveTopLevel)
    foreach ($item in Get-ChildItem -LiteralPath $ProjectRoot -Force) {
        if ($PreserveTopLevel -contains $item.Name) {
            Write-Info ('preserve=' + $item.FullName)
            continue
        }
        Remove-Item -LiteralPath $item.FullName -Recurse -Force
        Write-Info ('removed=' + $item.FullName)
    }
}

function Get-RelativePathCompat {
    param([string]$FullPath,[string]$ProjectRootPath)
    $relative = $FullPath.Substring($ProjectRootPath.Length)
    $relative = ($relative -replace '^[\\/]+', '')
    return $relative
}

function Should-ExcludePath {
    param([string]$FullPath,[string]$ProjectRootPath)
    $relative = Get-RelativePathCompat -FullPath $FullPath -ProjectRootPath $ProjectRootPath
    if (-not $relative) { return $true }
    $normalized = $relative -replace '/', '\\'
    $parts = $normalized.Split('\\')
    foreach ($part in $parts) {
        if ($part -in @('.venv','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache','build','dist','snapshots_out','.git','.vs','.idea')) { return $true }
        if ($part -like '*.egg-info') { return $true }
        if ($part -like '*.pyc' -or $part -like '*.pyo' -or $part -like '*.nbc' -or $part -like '*.nbi') { return $true }
    }
    return $false
}

function New-SnapshotIndexObject {
    param([string]$SnapshotKind,[string]$ProjectRoot,[string]$ScriptsRoot,[string]$SnapshotLabel)
    return [ordered]@{
        tool = 'pyAIGameEngine snapshot tooling'
        snapshot_kind = $SnapshotKind
        snapshot_label = $SnapshotLabel
        created_utc = ([datetime]::UtcNow.ToString('o'))
        powershell_runtime = Get-PowerShellRuntimeLabel
        project_root_name = 'pyAIGameEngine'
        source_project_root = $ProjectRoot
        source_scripts_root = $ScriptsRoot
    }
}

function Write-SnapshotIndexFile {
    param([string]$StageRoot,[object]$SnapshotIndex)
    $path = Join-Path $StageRoot 'SNAPSHOT_INDEX.json'
    ($SnapshotIndex | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $path -Encoding UTF8
}

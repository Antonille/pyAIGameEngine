[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$PackageName,

    [ValidateSet('Overlay','Mirror')]
    [string]$SyncMode = 'Overlay',

    [switch]$PreviewOnly,
    [switch]$CommitAndPush,

    [string]$CommitMessage = 'Apply package update from revisions',
    [string]$GitUserEmail = 'Scott.Antonille@gmail.com',
    [string]$GitUserName  = 'Scott Antonille',
    [string]$BranchName   = 'main'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-CanonicalEnvValue {
    param([Parameter(Mandatory = $true)][string]$Name)

    $value = [Environment]::GetEnvironmentVariable($Name, 'Process')
    if (-not $value) {
        $value = [Environment]::GetEnvironmentVariable($Name, 'User')
    }
    if (-not $value) {
        $value = [Environment]::GetEnvironmentVariable($Name, 'Machine')
    }
    if (-not $value) {
        throw "Required environment variable '$Name' was not found in Session, User, or Machine scope."
    }
    return $value
}

function Resolve-PackagePath {
    param(
        [Parameter(Mandatory = $true)][string]$RevisionsRoot,
        [string]$RequestedName
    )

    if ($RequestedName) {
        if (Test-Path -LiteralPath $RequestedName) {
            return (Resolve-Path -LiteralPath $RequestedName).Path
        }

        $combined = Join-Path $RevisionsRoot $RequestedName
        if (Test-Path -LiteralPath $combined) {
            return (Resolve-Path -LiteralPath $combined).Path
        }

        throw "Package was not found as a direct path or under revisions root: $RequestedName"
    }

    $candidates = Get-ChildItem -LiteralPath $RevisionsRoot -Force |
        Where-Object {
            ($_.PSIsContainer -or $_.Extension -ieq '.zip') -and
            $_.Name -notmatch 'console_log_capture' -and
            $_.Name -notmatch 'snapshot_script_updates'
        } |
        Sort-Object LastWriteTimeUtc

    if (-not $candidates) {
        throw "No package folders or zip files were found under revisions root: $RevisionsRoot"
    }

    return $candidates[-1].FullName
}

function New-TempDirectory {
    param([string]$Prefix = 'pyAIGameEngine_apply_pkg_')
    $path = Join-Path $env:TEMP ($Prefix + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $path -Force | Out-Null
    return $path
}

function Resolve-TransferRoot {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (Test-Path -LiteralPath (Join-Path $Path '.git')) {
        throw "Refusing to use a source package that itself contains .git: $Path"
    }

    $children = Get-ChildItem -LiteralPath $Path -Force
    if ($children.Count -eq 1 -and $children[0].PSIsContainer) {
        return $children[0].FullName
    }
    return $Path
}

function Get-RobocopyArguments {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination,
        [Parameter(Mandatory = $true)][string]$Mode,
        [bool]$Preview
    )

    $args = @($Source, $Destination)
    if ($Mode -eq 'Mirror') {
        $args += '/MIR'
    } else {
        $args += '/E'
    }

    if ($Preview) { $args += '/L' }

    $args += @('/R:1', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS', '/NP', '/XD', '.git', '.venv')
    return $args
}

function Invoke-RobocopySafe {
    param([string[]]$Arguments)
    & robocopy @Arguments | Out-Host
    if ($LASTEXITCODE -ge 8) {
        throw "robocopy failed with exit code $LASTEXITCODE"
    }
}

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    & git -C $RepoRoot @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

$RepoRoot     = Get-CanonicalEnvValue -Name 'path_pyAIGameEngine'
$RevisionsRoot = Get-CanonicalEnvValue -Name 'path_revs_pyAIGameEngine'
$ScriptsRoot  = Get-CanonicalEnvValue -Name 'path_pyEngine_scripts'

if (-not (Test-Path -LiteralPath $RepoRoot)) { throw "Repo root not found: $RepoRoot" }
if (-not (Test-Path -LiteralPath $RevisionsRoot)) { throw "Revisions root not found: $RevisionsRoot" }
if (-not (Test-Path -LiteralPath $ScriptsRoot)) { throw "Scripts root not found: $ScriptsRoot" }
if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot '.git'))) { throw "Repo root is not a git repository: $RepoRoot" }

$PackagePath = Resolve-PackagePath -RevisionsRoot $RevisionsRoot -RequestedName $PackageName

$runtime = if ($PSVersionTable.PSEdition) { $PSVersionTable.PSEdition } else { 'Desktop' }
Write-Host "runtime=$runtime $($PSVersionTable.PSVersion.ToString())"
Write-Host "repo_root=$RepoRoot"
Write-Host "revisions_root=$RevisionsRoot"
Write-Host "scripts_root=$ScriptsRoot"
Write-Host "package_path=$PackagePath"
Write-Host "sync_mode=$SyncMode"

$tempRoot = $null
try {
    if ((Get-Item -LiteralPath $PackagePath).PSIsContainer) {
        $sourceRoot = Resolve-TransferRoot -Path $PackagePath
    } else {
        if ([IO.Path]::GetExtension($PackagePath) -ine '.zip') {
            throw "Package is a file but not a .zip: $PackagePath"
        }
        $tempRoot = New-TempDirectory
        Expand-Archive -LiteralPath $PackagePath -DestinationPath $tempRoot -Force
        $sourceRoot = Resolve-TransferRoot -Path $tempRoot
    }

    Write-Host "source_root=$sourceRoot"

    Write-Host ''
    Write-Host 'Preview...'
    Invoke-RobocopySafe -Arguments (Get-RobocopyArguments -Source $sourceRoot -Destination $RepoRoot -Mode $SyncMode -Preview $true)

    if ($PreviewOnly) {
        Write-Host ''
        Write-Host 'PreviewOnly requested. No changes applied.'
        return
    }

    Write-Host ''
    Write-Host 'Applying package...'
    Invoke-RobocopySafe -Arguments (Get-RobocopyArguments -Source $sourceRoot -Destination $RepoRoot -Mode $SyncMode -Preview $false)

    Write-Host ''
    Write-Host 'git status after apply:'
    & git -C $RepoRoot status --short

    if ($CommitAndPush) {
        Invoke-Git -RepoRoot $RepoRoot -Arguments @('config','user.email',$GitUserEmail)
        Invoke-Git -RepoRoot $RepoRoot -Arguments @('config','user.name',$GitUserName)
        Invoke-Git -RepoRoot $RepoRoot -Arguments @('add','-A')

        $status = & git -C $RepoRoot status --porcelain
        if ($LASTEXITCODE -ne 0) {
            throw 'git status --porcelain failed.'
        }

        if ($status) {
            Invoke-Git -RepoRoot $RepoRoot -Arguments @('commit','-m',$CommitMessage)
            Invoke-Git -RepoRoot $RepoRoot -Arguments @('push','origin',$BranchName)
        } else {
            Write-Host 'No changes detected. Skipping commit and push.'
        }
    }
}
finally {
    if ($tempRoot -and (Test-Path -LiteralPath $tempRoot)) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

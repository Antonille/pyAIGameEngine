[CmdletBinding()]
param(
    [string]$ScriptsRoot = "C:\PythonDev\Dev1\pyGames\pyAIGameEngine\scripts\windows",
    [string]$DesktopPath = [Environment]::GetFolderPath('Desktop'),
    [switch]$ToDesktop,
    [switch]$ToScriptsFolder
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $ToDesktop -and -not $ToScriptsFolder) {
    $ToScriptsFolder = $true
}

$targets = @()
if ($ToScriptsFolder) { $targets += $ScriptsRoot }
if ($ToDesktop)      { $targets += $DesktopPath }

$wshell = New-Object -ComObject WScript.Shell
$psExe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"

$map = @(
    @{ Name = 'Apply Latest Snapshot';        Script = 'Apply-LatestSnapshot.ps1';        Args = '-ExecutionPolicy Bypass -File "{0}"' },
    @{ Name = 'Rebuild Project From Snapshots'; Script = 'Rebuild-ProjectFromSnapshots.ps1'; Args = '-ExecutionPolicy Bypass -File "{0}" -ClearProject' },
    @{ Name = 'Create Candidate Sparse Snapshot'; Script = 'New-SparseSnapshot.ps1';      Args = '-ExecutionPolicy Bypass -File "{0}" -SinceMode LastAny' },
    @{ Name = 'Create Candidate Full Snapshot'; Script = 'New-FullSnapshot.ps1';          Args = '-ExecutionPolicy Bypass -File "{0}"' }
)

foreach ($folder in $targets) {
    if (-not (Test-Path -LiteralPath $folder)) { New-Item -ItemType Directory -Path $folder -Force | Out-Null }
    foreach ($entry in $map) {
        $scriptPath = Join-Path $ScriptsRoot $entry.Script
        $lnkPath = Join-Path $folder ($entry.Name + '.lnk')
        $shortcut = $wshell.CreateShortcut($lnkPath)
        $shortcut.TargetPath = $psExe
        $shortcut.Arguments = [string]::Format($entry.Args, $scriptPath)
        $shortcut.WorkingDirectory = $ScriptsRoot
        $shortcut.IconLocation = "$psExe,0"
        $shortcut.Save()
        Write-Host "created_shortcut=$lnkPath"
    }
}

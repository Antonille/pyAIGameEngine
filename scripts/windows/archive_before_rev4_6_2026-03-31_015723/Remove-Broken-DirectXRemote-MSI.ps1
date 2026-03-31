[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [switch]$Remove,
    [string]$BackupDir = "$env:USERPROFILE\Desktop\DirectXRemote_MSI_Backup"
)

$ErrorActionPreference = 'Stop'

function Test-IsAdmin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p = New-Object Security.Principal.WindowsPrincipal($id)
    $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Export-RegKey {
    param(
        [Parameter(Mandatory)][string]$RegPath,
        [Parameter(Mandatory)][string]$OutFile
    )
    $native = $RegPath -replace '^HKLM:\\','HKEY_LOCAL_MACHINE\'
    & reg.exe export "$native" "$OutFile" /y | Out-Null
}

function Safe-BackupKey {
    param([string]$Path)
    if (Test-Path $Path) {
        $safe = ($Path -replace '[\\:\{\}]','_') + '.reg'
        $out = Join-Path $BackupDir $safe
        Export-RegKey -RegPath $Path -OutFile $out
        Write-Host "Backed up: $Path" -ForegroundColor Green
        return $true
    }
    return $false
}

function Safe-RemoveKey {
    param([string]$Path)
    if (Test-Path $Path) {
        Write-Host "Removing:  $Path" -ForegroundColor Red
        Remove-Item -LiteralPath $Path -Recurse -Force
    }
}

if (-not (Test-IsAdmin)) {
    throw "Run PowerShell as Administrator."
}

New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

$displayNamePattern = 'Windows SDK DirectX x64 Remote'
$cacheGuid = '{D112F2CE-F362-616D-E13D-EA6A44AEDE6F}'
$versionText = '10.1.26100.4654'

$uninstallRoots = @(
    'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
    'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'
)

$matches = @()

foreach ($root in $uninstallRoots) {
    if (Test-Path $root) {
        Get-ChildItem $root | ForEach-Object {
            try {
                $p = Get-ItemProperty $_.PSPath
                if (
                    ($p.DisplayName -like "*$displayNamePattern*") -or
                    ($_.PSChildName -eq $cacheGuid) -or
                    ($p.UninstallString -like "*$displayNamePattern*") -or
                    ($p.DisplayVersion -eq $versionText)
                ) {
                    $matches += [pscustomobject]@{
                        KeyName         = $_.PSChildName
                        RegistryPath    = $_.PSPath
                        DisplayName     = $p.DisplayName
                        DisplayVersion  = $p.DisplayVersion
                        Publisher       = $p.Publisher
                        UninstallString = $p.UninstallString
                    }
                }
            } catch {}
        }
    }
}

Write-Host "`nPotential uninstall entries:`n" -ForegroundColor Cyan
if ($matches.Count -gt 0) {
    $matches | Sort-Object DisplayName, DisplayVersion | Format-Table -AutoSize
} else {
    Write-Host "No matching uninstall entries found under standard Uninstall keys." -ForegroundColor Yellow
}

# Search the Installer tree for the cache GUID fragments or display name
$registryCandidates = @(
    "HKLM:\SOFTWARE\Classes\Installer\Products",
    "HKLM:\SOFTWARE\Classes\Installer\Features",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer\UserData\S-1-5-18\Products"
)

$extraHits = @()

foreach ($base in $registryCandidates) {
    if (Test-Path $base) {
        Get-ChildItem $base -ErrorAction SilentlyContinue | ForEach-Object {
            $hit = $false
            if ($_.PSChildName -like "*D112F2CE*") { $hit = $true }
            if ($_.PSChildName -like "*EA6A44AEDE6F*") { $hit = $true }

            if (-not $hit) {
                try {
                    $p = Get-ItemProperty $_.PSPath -ErrorAction Stop
                    foreach ($prop in $p.PSObject.Properties) {
                        $val = [string]$prop.Value
                        if ($val -like "*$displayNamePattern*" -or $val -like "*$versionText*") {
                            $hit = $true
                            break
                        }
                    }
                } catch {}
            }

            if ($hit) {
                $extraHits += $_.PSPath
            }
        }
    }
}

Write-Host "`nAdditional Installer-tree hits:`n" -ForegroundColor Cyan
if ($extraHits.Count -gt 0) {
    $extraHits | Sort-Object -Unique | ForEach-Object { Write-Host $_ }
} else {
    Write-Host "No obvious matching Installer-tree keys found." -ForegroundColor Yellow
}

$pathsToBackup = @()
$pathsToBackup += $matches.RegistryPath
$pathsToBackup += $extraHits
$pathsToBackup = $pathsToBackup | Sort-Object -Unique

Write-Host "`nBacking up matched keys...`n" -ForegroundColor Cyan
foreach ($path in $pathsToBackup) {
    Safe-BackupKey -Path $path | Out-Null
}

if (-not $Remove) {
    Write-Host "`nPreview only. No deletion done." -ForegroundColor Yellow
    Write-Host "If these look correct, rerun with:"
    Write-Host "  .\Remove-Broken-DirectXRemote-MSI.ps1 -Remove"
    exit
}

Write-Host "`nDeleting matched keys...`n" -ForegroundColor Cyan
foreach ($path in $pathsToBackup) {
    if ($PSCmdlet.ShouldProcess($path, "Delete stale MSI registration")) {
        Safe-RemoveKey -Path $path
    }
}

Write-Host "`nDone. Reboot, then retry the Visual Studio install." -ForegroundColor Green
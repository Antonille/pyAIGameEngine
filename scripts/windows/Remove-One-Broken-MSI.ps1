[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$ProductCode = "{D112F2CE-F362-616D-E13D-EA6A44AEDE6F}",
    [switch]$Remove,
    [string]$BackupDir = "$env:USERPROFILE\Desktop\BrokenMSI_Backup"
)

$ErrorActionPreference = 'Stop'

function Convert-ProductCodeToPackedGuid {
    param([Parameter(Mandatory)][string]$Guid)

    $g = $Guid.Trim('{}').ToUpperInvariant()
    if ($g -notmatch '^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$') {
        throw "Invalid product code GUID format: $Guid"
    }

    $parts = $g.Split('-')

    $p1 = -join ($parts[0].ToCharArray()[-1..-8])
    $p2 = -join ($parts[1].ToCharArray()[-1..-4])
    $p3 = -join ($parts[2].ToCharArray()[-1..-4])

    $swapPairs = {
        param([string]$s)
        $chars = $s.ToCharArray()
        $out = New-Object System.Collections.Generic.List[char]
        for ($i = 0; $i -lt $chars.Length; $i += 2) {
            $out.Add($chars[$i + 1])
            $out.Add($chars[$i])
        }
        -join $out
    }

    $p4 = & $swapPairs $parts[3]
    $p5 = & $swapPairs $parts[4]

    return "$p1$p2$p3$p4$p5"
}

function To-RegExePath {
    param([string]$Path)

    if ($Path -like 'Microsoft.PowerShell.Core\Registry::*') {
        return ($Path -replace '^Microsoft\.PowerShell\.Core\\Registry::', '')
    }
    elseif ($Path -like 'HKLM:\*') {
        return ($Path -replace '^HKLM:\\', 'HKEY_LOCAL_MACHINE\')
    }
    else {
        return $Path
    }
}

function Backup-Key {
    param([string]$Path)

    if (Test-Path $Path) {
        $native = To-RegExePath $Path
        $safe = ($native -replace '[\\:\{\}]','_') + '.reg'
        $outfile = Join-Path $BackupDir $safe
        & reg.exe export "$native" "$outfile" /y | Out-Null
        Write-Host "Backed up: $native" -ForegroundColor Green
    }
}

function Remove-Key {
    param([string]$Path)
    if (Test-Path $Path) {
        Remove-Item -LiteralPath $Path -Recurse -Force
        Write-Host "Removed: $Path" -ForegroundColor Red
    }
}

$packed = Convert-ProductCodeToPackedGuid $ProductCode

$paths = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\$ProductCode",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\$ProductCode",
    "HKLM:\SOFTWARE\Classes\Installer\Products\$packed",
    "HKLM:\SOFTWARE\Classes\Installer\Features\$packed",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer\UserData\S-1-5-18\Products\$packed"
)

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

Write-Host "`nTarget product code: $ProductCode"
Write-Host "Packed product code: $packed`n"

Write-Host "Matching keys found:`n" -ForegroundColor Cyan
foreach ($p in $paths) {
    if (Test-Path $p) {
        Write-Host "  FOUND  $p" -ForegroundColor Yellow
    } else {
        Write-Host "  MISS   $p" -ForegroundColor DarkGray
    }
}

Write-Host "`nBacking up found keys...`n" -ForegroundColor Cyan
foreach ($p in $paths) {
    Backup-Key $p
}

if (-not $Remove) {
    Write-Host "`nPreview only. No deletion performed." -ForegroundColor Yellow
    Write-Host "If the found keys look correct, rerun with -Remove"
    exit
}

Write-Host "`nDeleting found keys...`n" -ForegroundColor Cyan
foreach ($p in $paths) {
    if (Test-Path $p) {
        if ($PSCmdlet.ShouldProcess($p, "Delete stale MSI registration")) {
            Remove-Key $p
        }
    }
}

Write-Host "`nDone. Reboot, then retry the Visual Studio install." -ForegroundColor Green
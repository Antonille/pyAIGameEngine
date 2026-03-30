[CmdletBinding()]
param(
    [string]$ProjectRoot,
    [string]$Revision = '0.0.8',
    [string]$OutputDir,
    [string]$SevenZipPath
)

$ErrorActionPreference = 'Stop'

function Resolve-ProjectRoot {
    param([string]$ExplicitRoot)

    if ($ExplicitRoot) {
        return (Resolve-Path $ExplicitRoot).Path
    }

    if ($PSScriptRoot) {
        return (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
    }

    if ($MyInvocation.MyCommand.Path) {
        $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
        return (Resolve-Path (Join-Path $scriptDir '..\..')).Path
    }

    return (Get-Location).Path
}

function Find-SevenZip {
    param([string]$Explicit)

    if ($Explicit -and (Test-Path $Explicit)) { return $Explicit }

    $cmd = Get-Command 7z.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $cmd = Get-Command 7z -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $candidates = @(
        'C:\Program Files\7-Zip\7z.exe',
        'C:\Program Files (x86)\7-Zip\7z.exe'
    )

    foreach ($c in $candidates) {
        if (Test-Path $c) { return $c }
    }

    return $null
}

$ProjectRoot = Resolve-ProjectRoot -ExplicitRoot $ProjectRoot

if (-not $OutputDir) {
    $OutputDir = Join-Path $ProjectRoot 'snapshots_out'
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

$stamp = Get-Date -Format 'yyyy-MM-dd_HH-mm'
$outZip = Join-Path $OutputDir ("pyAIGameEngine_full_clean_snapshot_{0}_{1}.zip" -f $Revision, $stamp)
$excludeFile = Join-Path $ProjectRoot 'scripts\windows\snapshot_clean_excludes.txt'

$sevenZip = Find-SevenZip -Explicit $SevenZipPath
if (-not $sevenZip) {
    throw '7-Zip executable not found. Install 7-Zip or provide -SevenZipPath.'
}

if (-not (Test-Path $excludeFile)) {
    throw "Exclude pattern file not found: $excludeFile"
}

$excludeArgs = @()
Get-Content $excludeFile | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith('#')) {
        $excludeArgs += "-xr!$line"
    }
}

Write-Host "[pyAIGameEngine] Project root: $ProjectRoot" -ForegroundColor Cyan
Write-Host "[pyAIGameEngine] 7-Zip: $sevenZip" -ForegroundColor Cyan
Write-Host "[pyAIGameEngine] Exclude file: $excludeFile" -ForegroundColor Cyan

Push-Location $ProjectRoot
try {
    if (Test-Path $outZip) {
        Remove-Item $outZip -Force
    }

    & $sevenZip 'a' '-tzip' $outZip '.\*' @excludeArgs

    if ($LASTEXITCODE -ne 0) {
        throw '7-Zip archive creation failed.'
    }
}
finally {
    Pop-Location
}

Write-Host "Created clean snapshot: $outZip" -ForegroundColor Green
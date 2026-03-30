Param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot | Split-Path -Parent)
)
$ErrorActionPreference = 'Stop'
$stamp = Get-Date -Format 'yyyy-MM-dd_HH-mm'
$outDir = Join-Path $ProjectRoot 'snapshots_out'
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$outZip = Join-Path $outDir ("POC1_SoaFirst_$stamp.zip")

Add-Type -AssemblyName System.IO.Compression.FileSystem
if (Test-Path $outZip) { Remove-Item $outZip -Force }
[System.IO.Compression.ZipFile]::CreateFromDirectory((Join-Path $ProjectRoot 'POC1_SoaFirst'), $outZip)
Write-Host "Created POC1 package: $outZip"

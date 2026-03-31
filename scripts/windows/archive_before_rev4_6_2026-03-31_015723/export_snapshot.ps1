Param(
    [string]$ProjectRoot = 'C:\PythonDev\Dev1\pyGames\pyAIGameEngine',
    [string]$Revision = '0.0.9'
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$stamp = Get-Date -Format 'yyyy-MM-dd_HH-mm'
$outDir = Join-Path $ProjectRoot 'snapshots_out'
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$outZip = Join-Path $outDir ("pyAIGameEngine_Rev_${Revision}_${stamp}.zip")
$tempDir = Join-Path $env:TEMP ("pyAIGameEngine_snapshot_${stamp}")
if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
New-Item -ItemType Directory -Path $tempDir | Out-Null
$copyRoot = Join-Path $tempDir 'pyAIGameEngine'
New-Item -ItemType Directory -Path $copyRoot | Out-Null
$excludeDirs = @('.venv','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache','build','dist','snapshots_out','.git')
$excludeExts = @('.pyc','.pyo','.nbc','.nbi')
Get-ChildItem -Path $ProjectRoot -Force | ForEach-Object {
    if ($excludeDirs -contains $_.Name) { return }
    Copy-Item $_.FullName -Destination $copyRoot -Recurse -Force
}
Get-ChildItem -Path $copyRoot -Recurse -Force | Where-Object { $excludeDirs -contains $_.Name -or $excludeExts -contains $_.Extension -or $_.Name -like '*.egg-info' } | ForEach-Object {
    if ($_.PSIsContainer) { Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue } else { Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue }
}
if (Test-Path $outZip) { Remove-Item $outZip -Force }
[System.IO.Compression.ZipFile]::CreateFromDirectory($tempDir, $outZip)
Write-Host "created_clean_snapshot=$outZip"
Write-Host "snapshot_layout=standard-root-folder"
Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue

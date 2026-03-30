Param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot | Split-Path -Parent),
    [string]$Message = 'Update project state'
)
$ErrorActionPreference = 'Stop'
Set-Location $ProjectRoot

git add .
try { git commit -m $Message } catch { Write-Warning 'Nothing to commit.' }
try { git push } catch { Write-Warning 'Push failed or no remote configured yet.' }

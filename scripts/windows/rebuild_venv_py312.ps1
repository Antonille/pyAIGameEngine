Param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot | Split-Path -Parent)
)
$ErrorActionPreference = 'Stop'
Set-Location $ProjectRoot
if (Test-Path .venv) {
    Remove-Item -Recurse -Force .venv
}
powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot 'scripts\windows\install_project.ps1') -ProjectRoot $ProjectRoot -PythonSpec '3.12'

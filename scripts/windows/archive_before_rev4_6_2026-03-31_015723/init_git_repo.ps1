Param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot | Split-Path -Parent),
    [string]$RepoName = 'pyAIGameEngine',
    [string]$Revision = '0.0.9',
    [switch]$CreateGitHubRepo
)
$ErrorActionPreference = 'Stop'
Set-Location $ProjectRoot

if (-not (Test-Path .git)) {
    git init
    git branch -M main
}

git add .
try { git commit -m "Initialize pyAIGameEngine revision $Revision" } catch { Write-Warning 'Nothing to commit or initial commit already exists.' }

if ($CreateGitHubRepo) {
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        throw "gh CLI is required to create the GitHub repo."
    }
    gh repo create $RepoName --private --source . --remote origin --push
}

Write-Host "Git initialization complete."

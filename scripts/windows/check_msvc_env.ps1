[CmdletBinding()]
param(
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"

function Write-Info {
    param([string]$Message)
    if (-not $Quiet) { Write-Host $Message }
}

function Write-StatusLine {
    param(
        [string]$Label,
        [object]$Value
    )
    if (-not $Quiet) {
        $padded = $Label.PadRight(22)
        Write-Host ("  {0}: {1}" -f $padded, $Value)
    }
}

function Test-NonEmptyEnv {
    param([string]$Name)
    $v = [Environment]::GetEnvironmentVariable($Name, "Process")
    return -not [string]::IsNullOrWhiteSpace($v)
}

function Find-VsWhere {
    $candidates = @()

    if (-not [string]::IsNullOrWhiteSpace(${env:ProgramFiles(x86)})) {
        $candidates += (Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe')
    }
    if (-not [string]::IsNullOrWhiteSpace($env:ProgramFiles)) {
        $candidates += (Join-Path $env:ProgramFiles 'Microsoft Visual Studio\Installer\vswhere.exe')
    }

    return $candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique -First 1
}

function Get-VsWhereJson {
    param(
        [string]$VsWherePath,
        [string[]]$Arguments
    )

    if ([string]::IsNullOrWhiteSpace($VsWherePath)) {
        return $null
    }

    $output = & $VsWherePath @Arguments 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace(($output | Out-String))) {
        return $null
    }

    try {
        return ($output | Out-String | ConvertFrom-Json)
    }
    catch {
        return $null
    }
}

function Test-HeaderReachable {
    param([string]$HeaderName)

    $include = [Environment]::GetEnvironmentVariable("INCLUDE", "Process")
    if ([string]::IsNullOrWhiteSpace($include)) {
        return $false
    }

    $includePaths = $include -split ';' | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    foreach ($p in $includePaths) {
        $candidate = Join-Path $p $HeaderName
        if (Test-Path $candidate) {
            return $true
        }
    }
    return $false
}

Write-Info "[pyAIGameEngine] MSVC environment check"

$vswherePath = Find-VsWhere
$vswhereAvailable = -not [string]::IsNullOrWhiteSpace($vswherePath)

$clCmd = Get-Command cl -ErrorAction SilentlyContinue
$clAvailable = $null -ne $clCmd

$includeSet = Test-NonEmptyEnv "INCLUDE"
$libSet = Test-NonEmptyEnv "LIB"
$vcToolsSet = Test-NonEmptyEnv "VCToolsInstallDir"
$vcInstallSet = Test-NonEmptyEnv "VCINSTALLDIR"
$vsInstallSet = Test-NonEmptyEnv "VSINSTALLDIR"
$winSdkSet = Test-NonEmptyEnv "WindowsSdkDir"
$stringHeaderReachable = Test-HeaderReachable -HeaderName 'string.h'

$cppWorkloadDetected = $false
if ($vswhereAvailable) {
    $vsDetectedSummary = Get-VsWhereJson -VsWherePath $vswherePath -Arguments @(
        '-latest',
        '-products', '*',
        '-requires', 'Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
        '-format', 'json'
    )

    if ($vsDetectedSummary -is [System.Array]) {
        $cppWorkloadDetected = $vsDetectedSummary.Count -gt 0
    }
    elseif ($null -ne $vsDetectedSummary) {
        $cppWorkloadDetected = $true
    }
}

$headerEnvPresent = $includeSet -and $libSet
$msvcConfigured = $clAvailable -and $headerEnvPresent -and $stringHeaderReachable

Write-StatusLine "cl available" $clAvailable
Write-StatusLine "vswhere available" $vswhereAvailable
Write-StatusLine "C++ workload detected" $cppWorkloadDetected
Write-StatusLine "VCToolsInstallDir set" $vcToolsSet
Write-StatusLine "VCINSTALLDIR set" $vcInstallSet
Write-StatusLine "VSINSTALLDIR set" $vsInstallSet
Write-StatusLine "WindowsSdkDir set" $winSdkSet
Write-StatusLine "header env present" $headerEnvPresent
Write-StatusLine "string.h reachable" $stringHeaderReachable
Write-StatusLine "MSVC configured" $msvcConfigured

if ($vswhereAvailable) {
    Write-StatusLine "vswhere path" $vswherePath
}
if ($clAvailable) {
    Write-StatusLine "cl source" $clCmd.Source
}

if ($msvcConfigured) {
    exit 0
}

if (-not $Quiet) {
    Write-Warning "MSVC is not fully configured for source builds in this shell."
    Write-Host "Recommended next steps:"
    Write-Host '  1) Open "x64 Native Tools Command Prompt for VS 2022" or "Developer PowerShell for VS 2022".'
    Write-Host "  2) Ensure the C++ workload / MSVC toolset / Windows SDK are installed."
    Write-Host "  3) Rerun install_project.ps1 in that shell if you want PyBullet."
}
exit 1

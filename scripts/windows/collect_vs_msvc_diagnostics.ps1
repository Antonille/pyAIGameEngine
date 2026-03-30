[CmdletBinding()]
param(
    [string]$OutDir = '.\diagnostics\vs_tools',
    [switch]$IncludeEnvDump
)

$ErrorActionPreference = 'Continue'

function Save-Text([string]$Path, [string]$Content) {
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    Set-Content -Path $Path -Value $Content -Encoding UTF8
}

function Run-And-Save {
    param([string]$Label, [scriptblock]$ScriptBlock, [string]$Path)
    try {
        $output = & $ScriptBlock 2>&1 | Out-String
    } catch {
        $output = "ERROR while collecting $Label`r`n$($_ | Out-String)"
    }
    Save-Text -Path $Path -Content $output
}

function Get-VsWherePath {
    $candidates = @(
        Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe',
        Join-Path $env:ProgramFiles 'Microsoft Visual Studio\Installer\vswhere.exe'
    ) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique
    if ($candidates.Count -gt 0) { return $candidates[0] }
    return $null
}

$timestamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$root = Join-Path $OutDir $timestamp
New-Item -ItemType Directory -Force -Path $root | Out-Null

$vswhere = Get-VsWherePath
Save-Text (Join-Path $root '20_vswhere_path.txt') ($vswhere ?? 'vswhere.exe not found')
if ($vswhere) {
    Run-And-Save 'vswhere all' { & $vswhere -all -products * -format json } (Join-Path $root '21_vswhere_all.json')
    Run-And-Save 'vswhere C++ workloads' { & $vswhere -all -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -format json } (Join-Path $root '22_vswhere_cpp.json')
}

Run-And-Save 'MSVC env vars' {
    @(
        'INCLUDE','LIB','LIBPATH','PATH','VCToolsInstallDir','VCINSTALLDIR','VSINSTALLDIR',
        'VisualStudioVersion','WindowsSdkDir','WindowsSDKVersion','UCRTVersion','UniversalCRTSdkDir'
    ) | ForEach-Object {
        '{0}={1}' -f $_, [Environment]::GetEnvironmentVariable($_, 'Process')
    }
} (Join-Path $root '40_msvc_env_vars.txt')

Run-And-Save 'cl /Bv' { cmd /c 'cl /Bv' } (Join-Path $root '41_cl_Bv.txt')

$headerReport = New-Object System.Collections.Generic.List[string]
foreach ($hdr in @('string.h','stdlib.h','stdio.h')) {
    $headerReport.Add("### $hdr")
    $found = Get-ChildItem 'C:\Program Files\Microsoft Visual Studio','C:\Program Files (x86)\Windows Kits','C:\Program Files\Windows Kits' -Recurse -Filter $hdr -ErrorAction SilentlyContinue | Select-Object -First 10 -ExpandProperty FullName
    if ($found) {
        foreach ($f in $found) { $headerReport.Add($f) }
    } else {
        $headerReport.Add('NOT FOUND')
    }
    $headerReport.Add('')
}
Save-Text (Join-Path $root '42_header_search.txt') ($headerReport -join "`r`n")

$compileDir = Join-Path $root 'compile_test'
New-Item -ItemType Directory -Force -Path $compileDir | Out-Null
Save-Text (Join-Path $compileDir 'test_stringh.c') "#include <string.h>`n#include <stdio.h>`nint main(void){printf(\"ok\\n\"); return 0;}"
Run-And-Save 'Compile tiny C test' {
    Push-Location $compileDir
    try { cmd /c 'cl /nologo test_stringh.c' } finally { Pop-Location }
} (Join-Path $root '43_compile_test.txt')

if ($IncludeEnvDump) {
    Run-And-Save 'Full env dump' { Get-ChildItem Env: | Sort-Object Name } (Join-Path $root '99_env_full_dump.txt')
}

Write-Host "Diagnostic bundle written to: $root"
Write-Host 'Review: 20_vswhere_path.txt, 21_vswhere_all.json, 22_vswhere_cpp.json, 40_msvc_env_vars.txt, 41_cl_Bv.txt, 42_header_search.txt, 43_compile_test.txt'

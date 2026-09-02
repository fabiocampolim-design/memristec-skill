# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
<#
.SYNOPSIS
  Create the conda env `memristec` for memristec-skill and register its Jupyter kernel.
.PARAMETER DryRun
  Print every command without executing it.
.PARAMETER Conda
  Path to conda.exe (default: %USERPROFILE%\miniconda3\Scripts\conda.exe).
#>
param(
  [switch]$DryRun,
  [string]$Conda = "$env:USERPROFILE\miniconda3\Scripts\conda.exe"
)
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$yml  = Join-Path (Split-Path -Parent $here) "environment-memristec.yml"
$steps = @()
function Step($name, $cmd) {
  Write-Host "== $name"
  Write-Host "   $cmd"
  if ($DryRun) { $script:steps += "$name : DRY-RUN"; return }
  Invoke-Expression $cmd
  if ($LASTEXITCODE -ne 0) { $script:steps += "$name : FAIL ($LASTEXITCODE)"; Write-Host ($script:steps -join "`n"); exit 1 }
  $script:steps += "$name : OK"
}
if (-not (Test-Path $Conda)) { Write-Host "FAIL: conda not found at $Conda (pass -Conda)"; exit 1 }
if (-not (Test-Path $yml))   { Write-Host "FAIL: $yml missing"; exit 1 }
Step "create-env"       "& `"$Conda`" env create -f `"$yml`" -y"
Step "register-kernel"  "& `"$env:USERPROFILE\miniconda3\envs\memristec\python.exe`" -m ipykernel install --user --name memristec-mc --display-name `"Python 3.12 (memristec)`""
Step "verify-imports"   "& `"$env:USERPROFILE\miniconda3\envs\memristec\python.exe`" -c `"import numpy, scipy, matplotlib, yaml, pytest; print('imports ok')`""
Write-Host ($steps -join "`n")
exit 0

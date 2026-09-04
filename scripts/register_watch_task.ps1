# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
<#
.SYNOPSIS  Register (or -Remove) a weekly Windows Task Scheduler job that runs
           watch_upstream.py --weekly on the local clone named by MEMRISTEC_MODEL_LIBRARY
           (playbook S8 / rule 23).
.PARAMETER Python   interpreter (default %USERPROFILE%\miniconda3\envs\memristec\python.exe)
.PARAMETER Clone    local clone of the MemrisTec Model Library (default: $env:MEMRISTEC_MODEL_LIBRARY)
.PARAMETER Day      weekday of the trigger (default Monday)
.PARAMETER At       time of the trigger, HH:mm (default 08:00)
.PARAMETER Remove   unregister the task instead
.PARAMETER DryRun   print what would be registered, register nothing
.PARAMETER Version  print the memristec-skill version
Exit 0 ok, 1 failed.
#>
param(
    [string]$Python = "$env:USERPROFILE\miniconda3\envs\memristec\python.exe",
    [string]$Clone = $env:MEMRISTEC_MODEL_LIBRARY,
    [string]$Day = "Monday",
    [string]$At = "08:00",
    [switch]$Remove,
    [switch]$DryRun,
    [switch]$Version
)
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($Version) { Write-Output ("memristec-skill " + (Get-Content (Join-Path $here "..\VERSION") -Raw).Trim()); exit 0 }
$script = Join-Path $here "watch_upstream.py"
$name = "memristec-skill upstream watch"
$argument = "`"$script`" --weekly -q"
if ($Clone) { $argument = "$argument --clone `"$Clone`"" }
if ($DryRun) {
    Write-Output "DRY-RUN: Register-ScheduledTask '$name' weekly $Day $At -> `"$Python`" $argument"
    exit 0
}
if ($Remove) {
    Unregister-ScheduledTask -TaskName $name -Confirm:$false
    Write-Output "removed '$name'"
    exit 0
}
if (-not (Test-Path $Python)) { Write-Output "python not found: $Python"; exit 1 }
if (-not $Clone) { Write-Output "no clone: set MEMRISTEC_MODEL_LIBRARY or pass -Clone"; exit 1 }
$action = New-ScheduledTaskAction -Execute $Python -Argument $argument -WorkingDirectory $here
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Day -At $At
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1)
Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings `
    -Description "memristec-skill S8 weekly upstream watch (git fetch of the MemrisTec Model Library clone, branch/folder/tag deltas)" -Force | Out-Null
Write-Output "registered '$name' weekly $Day $At -> $Python"

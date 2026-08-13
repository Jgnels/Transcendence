[CmdletBinding()]
param(
    [switch]$Force
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Rollback = Join-Path $PSScriptRoot "rollback_live_probe.ps1"
$Parameters = @{ Confirm = $false }
if ($Force) { $Parameters.Force = $true }
& $Rollback @Parameters
if (-not $?) { throw "Battle replay probe rollback failed." }
Write-Host "The launcher active-mod list was not changed. Restore your normal mod configuration manually." -ForegroundColor Yellow

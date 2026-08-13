[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [switch]$RemoveProbePack,
    [switch]$Force
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = Join-Path $PSScriptRoot "..\.." }
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$Latest = Join-Path $RepoRoot "local_inputs\runtime_probe\sessions\latest.json"
if (Test-Path -LiteralPath $Latest -PathType Leaf) {
    $Session = Get-Content -LiteralPath $Latest -Raw | ConvertFrom-Json
    if ($Session.watcher_stop_file) { New-Item -ItemType File -Force -Path ([string]$Session.watcher_stop_file) | Out-Null }
}
if ($RemoveProbePack) {
    $RollbackLiveProbe = Join-Path $PSScriptRoot "rollback_live_probe.ps1"
    $RollbackParameters = @{ Confirm = $false }
    if ($Force) { $RollbackParameters.Force = $true }
    & $RollbackLiveProbe @RollbackParameters
    if (-not $?) { throw "Probe rollback failed." }
}
Write-Host "SFO session watcher stop requested." -ForegroundColor Green
Write-Host "The SFO pack, active mod list, and saves were not modified by this rollback."

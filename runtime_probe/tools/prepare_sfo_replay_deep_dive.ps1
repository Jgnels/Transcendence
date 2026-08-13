[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [switch]$SkipProbeInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    if ([string]::IsNullOrWhiteSpace($PSScriptRoot)) { throw "Supply -RepoRoot explicitly." }
    $RepoRoot = Join-Path $PSScriptRoot "..\.."
}
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path

if (-not $SkipProbeInstall) {
    Write-Host "" 
    Write-Host "==> Building, validating, and installing the read-only battle replay probe" -ForegroundColor Cyan
    $PrepareLiveProbe = Join-Path $PSScriptRoot "prepare_live_probe.ps1"
    $Parameters = @{
        InstallBattleReplay = $true
        Force = $true
        Confirm = $false
    }
    & $PrepareLiveProbe @Parameters
    if (-not $?) { throw "Battle replay probe installation failed." }
}

$CohortPath = Join-Path $RepoRoot "runtime_probe\fixtures\sfo_replay_deep_dive_cohort_v0.1Z.json"
$Cohort = Get-Content -LiteralPath $CohortPath -Raw | ConvertFrom-Json
$Installed = $null
$MachinePath = Join-Path $RepoRoot "local_inputs\machine_profiles\gaming_laptop_private.json"
if (Test-Path -LiteralPath $MachinePath -PathType Leaf) {
    $Machine = Get-Content -LiteralPath $MachinePath -Raw | ConvertFrom-Json
    $Installed = Join-Path ([string]$Machine.game.install_path) "data\transcendence_battle_replay_probe.pack"
}
if ($Installed -and -not (Test-Path -LiteralPath $Installed -PathType Leaf)) {
    throw "The replay probe was not found after installation: $Installed"
}

Write-Host ""
Write-Host "SFO REPLAY DEEP-DIVE PREPARATION COMPLETE" -ForegroundColor Green
Write-Host "The launcher active-mod list was not changed."
Write-Host "For each replay, enable exactly SFO plus transcendence_battle_replay_probe.pack." -ForegroundColor Yellow
Write-Host "The probe is read-only, issues no orders, and does not modify saves." -ForegroundColor Green
Write-Host ""
Write-Host "Frozen replay cohort:" -ForegroundColor Cyan
foreach ($Replay in @($Cohort.replays)) {
    Write-Host "  $($Replay.battle_name)"
    Write-Host "    filename: $($Replay.filename)"
    Write-Host "    SHA-256: $($Replay.sha256)"
}
Write-Host ""
Write-Host "Run one exact replay at a time with runtime_probe\tools\run_sfo_replay_deep_dive.ps1." -ForegroundColor Yellow

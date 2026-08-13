[CmdletBinding()]
param(
    [string]$RepoRoot = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = Join-Path $PSScriptRoot "..\.." }
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path

$ContractPath = Join-Path $RepoRoot "runtime_probe\fixtures\sfo_chaos_defeat_replay_contract_v0.2B.json"
$Contract = Get-Content -LiteralPath $ContractPath -Raw | ConvertFrom-Json

& (Join-Path $PSScriptRoot "prepare_sfo_replay_deep_dive.ps1") -RepoRoot $RepoRoot

Write-Host ""
Write-Host "CHAOS DEFEAT REPLAY PREPARATION COMPLETE" -ForegroundColor Green
Write-Host ("Exact replay title: {0}" -f [string]$Contract.replay.display_title)
Write-Host ("Replay SHA-256: {0}" -f [string]$Contract.replay.sha256)
Write-Host "Enable exactly SFO plus transcendence_battle_replay_probe.pack."
Write-Host "The exact frozen shadow pack is accepted only as a script-equivalent read-only observer if WH3 records that container."
Write-Host "Do not issue commands during replay playback."

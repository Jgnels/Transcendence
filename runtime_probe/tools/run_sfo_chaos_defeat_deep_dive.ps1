[CmdletBinding()]
param(
    [string]$ReplayPath = "",
    [string]$RepoRoot = "",
    [int]$TimeoutMinutes = 45
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = Join-Path $PSScriptRoot "..\.." }
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path

function Get-PythonCommand {
    $Python = Get-Command python -ErrorAction SilentlyContinue
    $Prefix = @()
    if (-not $Python) {
        $Python = Get-Command py -ErrorAction SilentlyContinue
        if ($Python) { $Prefix = @("-3") }
    }
    if (-not $Python) { throw "Python 3 was not found." }
    return [pscustomobject]@{ Command = $Python.Source; Prefix = $Prefix }
}
function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

$ContractPath = Join-Path $RepoRoot "runtime_probe\fixtures\sfo_chaos_defeat_replay_contract_v0.2B.json"
$Contract = Get-Content -LiteralPath $ContractPath -Raw | ConvertFrom-Json
$ExpectedReplaySha = [string]$Contract.replay.sha256
$BattleLabel = [string]$Contract.replay.battle_label

if ([string]::IsNullOrWhiteSpace($ReplayPath)) {
    $ReplayRoot = Join-Path $env:APPDATA "The Creative Assembly\Warhammer3\replays"
    $Candidates = @()
    if (Test-Path -LiteralPath $ReplayRoot -PathType Container) {
        foreach ($Candidate in @(Get-ChildItem -LiteralPath $ReplayRoot -File -Filter "*.replay" -ErrorAction SilentlyContinue)) {
            if ((Get-Sha256 $Candidate.FullName) -eq $ExpectedReplaySha) { $Candidates += $Candidate.FullName }
        }
    }
    if ($Candidates.Count -ne 1) {
        throw "The exact Chaos defeat replay was not found uniquely. Supply -ReplayPath to the preserved test.replay file."
    }
    $ReplayPath = $Candidates[0]
}
$ReplayPath = (Resolve-Path -LiteralPath $ReplayPath).Path
if ((Get-Sha256 $ReplayPath) -ne $ExpectedReplaySha) {
    throw "Replay hash mismatch for the exact Chaos defeat contract."
}

$Python = Get-PythonCommand
& $Python.Command @($Python.Prefix) `
    (Join-Path $PSScriptRoot "capture_sfo_replay_deep_dive.py") `
    --repo-root $RepoRoot `
    --replay-path $ReplayPath `
    --expected-replay-sha256 $ExpectedReplaySha `
    --battle-label $BattleLabel `
    --expected-pack-sha256 ([string]$Contract.environment.battle_replay_pack_sha256) `
    --expected-equivalent-pack-sha256 ([string]$Contract.environment.script_equivalent_shadow_pack_sha256) `
    --expected-sfo-pack-sha256 ([string]$Contract.environment.sfo_pack_sha256) `
    --sfo-workshop-id ([string]$Contract.environment.sfo_workshop_id) `
    --source-contract-digest ([string]$Contract.result_digest) `
    --corpus-version ([string]$Contract.capture.corpus_version) `
    --timeout-minutes $TimeoutMinutes
if ($LASTEXITCODE -ne 0) { throw "Chaos defeat replay deep dive did not fully verify; exit code $LASTEXITCODE." }

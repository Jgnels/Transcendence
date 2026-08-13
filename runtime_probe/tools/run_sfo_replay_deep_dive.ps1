[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("Ubersreik", "Marienburg")]
    [string]$Battle,
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

$Cohort = Get-Content -LiteralPath (Join-Path $RepoRoot "runtime_probe\fixtures\sfo_replay_deep_dive_cohort_v0.1Z.json") -Raw | ConvertFrom-Json
$Baseline = Get-Content -LiteralPath (Join-Path $RepoRoot "runtime_probe\fixtures\sfo_observed_combined_v0.1Z.json") -Raw | ConvertFrom-Json
$BattleName = "Battle of $Battle"
$Matches = @($Cohort.replays | Where-Object { [string]$_.battle_name -eq $BattleName })
if ($Matches.Count -ne 1) { throw "Could not resolve the frozen replay contract for $BattleName." }
$Replay = $Matches[0]

if ([string]::IsNullOrWhiteSpace($ReplayPath)) {
    $ReplayRoot = Join-Path $env:APPDATA "The Creative Assembly\Warhammer3\replays"
    $Candidates = @()
    if (Test-Path -LiteralPath $ReplayRoot -PathType Container) {
        foreach ($Candidate in @(Get-ChildItem -LiteralPath $ReplayRoot -File -Filter "*.replay" -ErrorAction SilentlyContinue)) {
            if ((Get-Sha256 $Candidate.FullName) -eq [string]$Replay.sha256) { $Candidates += $Candidate.FullName }
        }
    }
    if ($Candidates.Count -ne 1) {
        throw "The exact $BattleName replay was not found uniquely. Supply -ReplayPath to the preserved file."
    }
    $ReplayPath = $Candidates[0]
}
$ReplayPath = (Resolve-Path -LiteralPath $ReplayPath).Path
if ((Get-Sha256 $ReplayPath) -ne [string]$Replay.sha256) {
    throw "Replay hash mismatch for $BattleName."
}

$Python = Get-PythonCommand
& $Python.Command @($Python.Prefix) `
    (Join-Path $PSScriptRoot "capture_sfo_replay_deep_dive.py") `
    --repo-root $RepoRoot `
    --replay-path $ReplayPath `
    --expected-replay-sha256 ([string]$Replay.sha256) `
    --battle-label $BattleName `
    --expected-pack-sha256 ([string]$Cohort.capture_contract.probe_pack_sha256) `
    --expected-sfo-pack-sha256 ([string]$Baseline.environment.sfo_pack_sha256) `
    --timeout-minutes $TimeoutMinutes
if ($LASTEXITCODE -ne 0) { throw "SFO replay deep dive did not fully verify; exit code $LASTEXITCODE." }

[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [int]$MinimumTurns = 5,
    [int]$MinimumCompletedBattles = 2
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    if ([string]::IsNullOrWhiteSpace($PSScriptRoot)) {
        throw "PowerShell did not provide PSScriptRoot; supply -RepoRoot explicitly."
    }
    $RepoRoot = Join-Path $PSScriptRoot "..\.."
}
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

$LatestSession = Join-Path $RepoRoot "local_inputs\runtime_probe\sessions\latest.json"
if (-not (Test-Path -LiteralPath $LatestSession -PathType Leaf)) {
    throw "SFO combined-session manifest not found. Run prepare_sfo_combined_session.ps1 first."
}
$Session = Get-Content -LiteralPath $LatestSession -Raw | ConvertFrom-Json
if ([int]$Session.schema_version -ne 2 -or [string]$Session.session_kind -ne "SFO_COMBINED_CAMPAIGN_BATTLE") {
    throw "The latest session is not an SFO combined-session schema-2 manifest."
}
foreach ($Path in @(
    [string]$Session.environment_profile_public,
    [string]$Session.checkpoint_manifest
)) {
    if ([string]::IsNullOrWhiteSpace($Path)) { throw "The SFO session manifest is incomplete." }
}

$StopFile = [string]$Session.watcher_stop_file
New-Item -ItemType File -Force -Path $StopFile | Out-Null
$WatcherStopped = $false
$CheckpointState = $null
for ($Attempt = 0; $Attempt -lt 150; $Attempt++) {
    if (Test-Path -LiteralPath ([string]$Session.checkpoint_manifest) -PathType Leaf) {
        try {
            $CandidateState = Get-Content -LiteralPath ([string]$Session.checkpoint_manifest) -Raw | ConvertFrom-Json
            if (
                [int]$CandidateState.schema_version -eq 2 -and
                [string]$CandidateState.handshake_token -ceq [string]$Session.watcher_handshake_token -and
                [string]$CandidateState.state -in @("STOPPED", "FAILED")
            ) {
                $CheckpointState = $CandidateState
                $WatcherStopped = $true
                break
            }
        } catch {
            # The manifest is atomically replaced; retry a transient read race.
        }
    }
    Start-Sleep -Milliseconds 200
}
if (-not $WatcherStopped) { throw "The authoritative checkpoint manifest did not reach a terminal state." }
if ([string]$CheckpointState.state -ne "STOPPED" -or @($CheckpointState.violations).Count -ne 0) {
    throw "The checkpoint watcher reported failure: $([string]::Join(', ', @($CheckpointState.violations)))"
}

$RecoveryWarnings = @()
if (Test-Path -LiteralPath ([string]$Session.watcher_status) -PathType Leaf) {
    try {
        $Status = Get-Content -LiteralPath ([string]$Session.watcher_status) -Raw | ConvertFrom-Json
        if ([string]$Status.handshake_token -cne [string]$Session.watcher_handshake_token) {
            $RecoveryWarnings += "WATCHER_STATUS_HANDSHAKE_MISMATCH_IGNORED"
        }
    } catch {
        $RecoveryWarnings += "WATCHER_STATUS_UNREADABLE_IGNORED_CHECKPOINT_MANIFEST_AUTHORITATIVE"
    }
} else {
    $RecoveryWarnings += "WATCHER_STATUS_ABSENT_CHECKPOINT_MANIFEST_AUTHORITATIVE"
}

$EvidenceParent = Join-Path $RepoRoot "local_inputs\logs\wh3"
$BeforeEvidence = @(Get-ChildItem -LiteralPath $EvidenceParent -Directory -Filter "probe_*" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
$BeforeExports = @(Get-ChildItem -LiteralPath (Join-Path $RepoRoot "local_inputs\runtime_probe\exports") -File -Filter "Transcendence_Campaign_Battle_Evidence_*.zip" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)

& powershell.exe -NoProfile -ExecutionPolicy Bypass `
    -File (Join-Path $PSScriptRoot "collect_campaign_battle.ps1") `
    -RepoRoot $RepoRoot `
    -MinimumTurns $MinimumTurns `
    -MinimumCompletedBattles $MinimumCompletedBattles `
    -InputLogPath ([string]$Session.runtime_log) `
    -SkipUploadZip
$LegacyExit = $LASTEXITCODE

$EvidenceRoot = Get-ChildItem -LiteralPath $EvidenceParent -Directory -Filter "probe_*" |
    Where-Object { $BeforeEvidence -notcontains $_.FullName } |
    Sort-Object LastWriteTimeUtc -Descending |
    Select-Object -First 1 -ExpandProperty FullName
if (-not $EvidenceRoot) { throw "Could not identify the combined evidence folder." }

$LogPath = Join-Path $EvidenceRoot "transcendence_runtime_log.txt"
$CampaignSummary = Join-Path $EvidenceRoot "probe_summary.json"
$BattleSummary = Join-Path $EvidenceRoot "battle_summary.json"
$EvidenceManifest = Join-Path $EvidenceRoot "evidence_manifest.json"
$CampaignReport = Join-Path $EvidenceRoot "campaign_shadow_report.json"
$BattleReport = Join-Path $EvidenceRoot "battle_report.json"
$SfoVerification = Join-Path $EvidenceRoot "sfo_combined_verification.json"
foreach ($Path in @($LogPath, $CampaignSummary, $BattleSummary, $EvidenceManifest, $CampaignReport, $BattleReport)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing combined evidence file: $Path" }
}

$Python = Get-PythonCommand
& $Python.Command @($Python.Prefix) `
    (Join-Path $PSScriptRoot "verify_sfo_combined_session.py") `
    --log $LogPath `
    --campaign-summary $CampaignSummary `
    --battle-summary $BattleSummary `
    --evidence-manifest $EvidenceManifest `
    --campaign-report $CampaignReport `
    --battle-report $BattleReport `
    --environment-profile ([string]$Session.environment_profile_public) `
    --checkpoint-manifest ([string]$Session.checkpoint_manifest) `
    --expected-pack-sha256 ([string]$Session.installed_shadow_pack_sha256) `
    --expected-handshake-token ([string]$Session.watcher_handshake_token) `
    --minimum-turns $MinimumTurns `
    --minimum-completed-battles $MinimumCompletedBattles `
    --output $SfoVerification
$SfoExit = $LASTEXITCODE

$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$Bundle = Join-Path $EvidenceRoot "sfo_public_upload_bundle"
New-Item -ItemType Directory -Force -Path $Bundle | Out-Null
$PublicFiles = @(
    @{ Source = [string]$Session.environment_profile_public; Name = "sfo_environment_attestation.json" },
    @{ Source = $CampaignSummary; Name = "campaign_probe_summary.json" },
    @{ Source = $BattleSummary; Name = "battle_summary.json" },
    @{ Source = $CampaignReport; Name = "campaign_shadow_report.json" },
    @{ Source = $BattleReport; Name = "battle_report.json" },
    @{ Source = $SfoVerification; Name = "sfo_combined_verification.json" }
)
$Records = @()
foreach ($Item in $PublicFiles) {
    $Destination = Join-Path $Bundle $Item.Name
    Copy-Item -LiteralPath $Item.Source -Destination $Destination -Force
    $Records += [ordered]@{
        name = $Item.Name
        size_bytes = [int64](Get-Item -LiteralPath $Destination).Length
        sha256 = Get-Sha256 $Destination
    }
}
$Verification = Get-Content -LiteralPath $SfoVerification -Raw | ConvertFrom-Json
$PublicManifest = Join-Path $Bundle "export_manifest.json"
[ordered]@{
    schema_version = 1
    gate = "SFO_COMBINED_CAMPAIGN_BATTLE_CONTINUITY"
    exported_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    verification_status = [string]$Verification.status
    verification_result_digest = [string]$Verification.result_digest
    private_raw_log_preserved_locally = $true
    raw_log_included = $false
    private_paths_included = $false
    active_mod_list_modified = $false
    save_modified = $false
    recovery_warnings = @($RecoveryWarnings)
    files = $Records
} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $PublicManifest -Encoding UTF8

$ExportRoot = Join-Path $RepoRoot "local_inputs\runtime_probe\exports"
New-Item -ItemType Directory -Force -Path $ExportRoot | Out-Null
$ZipPath = Join-Path $ExportRoot ("Transcendence_SFO_CombinedSession_" + $Timestamp + ".zip")
$ZipReceipt = Join-Path $EvidenceRoot "sfo_public_zip_verification.json"
& $Python.Command @($Python.Prefix) `
    (Join-Path $PSScriptRoot "build_public_evidence_zip.py") `
    --source-dir $Bundle `
    --output $ZipPath `
    --manifest $PublicManifest `
    --receipt $ZipReceipt
if ($LASTEXITCODE -ne 0) { throw "Deterministic public evidence ZIP verification failed with exit code $LASTEXITCODE." }

# Remove the older generic upload ZIP because it contains private combined-session materials.
Get-ChildItem -LiteralPath $ExportRoot -File -Filter "Transcendence_Campaign_Battle_Evidence_*.zip" -ErrorAction SilentlyContinue |
    Where-Object { $BeforeExports -notcontains $_.FullName } |
    Remove-Item -Force

Write-Host ""
if ($SfoExit -eq 0) {
    Write-Host "SFO COMBINED CAMPAIGN + BATTLE CONTINUITY GATE PASSED" -ForegroundColor Green
} else {
    Write-Host "SFO EVIDENCE EXPORTED, BUT THE LIVE GATE REMAINS OPEN" -ForegroundColor Yellow
}
Write-Host "The raw log and checkpoint snapshots remain private under local_inputs."
Write-Host "Upload this path-free ZIP:" -ForegroundColor Yellow
Write-Host $ZipPath -ForegroundColor Yellow
if ($SfoExit -ne 0) { exit $SfoExit }
if ($LegacyExit -ne 0) { exit $LegacyExit }

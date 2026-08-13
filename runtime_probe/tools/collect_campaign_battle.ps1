[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [int]$MinimumTurns = 5,
    [int]$MinimumCompletedBattles = 2,
    [string]$InputLogPath = "",
    [switch]$SkipUploadZip
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    if ([string]::IsNullOrWhiteSpace($PSScriptRoot)) {
        throw "PowerShell did not provide PSScriptRoot; supply -RepoRoot explicitly."
    }
    $RepoRoot = Join-Path $PSScriptRoot "..\.."
}

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

if ($MinimumTurns -lt 3) { throw "MinimumTurns cannot be less than 3." }
if ($MinimumCompletedBattles -lt 1) { throw "At least one completed battle is required." }

$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$EvidenceParent = Join-Path $RepoRoot "local_inputs\logs\wh3"
New-Item -ItemType Directory -Force -Path $EvidenceParent | Out-Null
$Before = @(Get-ChildItem -LiteralPath $EvidenceParent -Directory -Filter "probe_*" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)

$TotalWatch = [System.Diagnostics.Stopwatch]::StartNew()
$CollectionWatch = [System.Diagnostics.Stopwatch]::StartNew()
if ([string]::IsNullOrWhiteSpace($InputLogPath)) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass `
        -File (Join-Path $PSScriptRoot "collect_probe_logs.ps1") `
        -EvidencePhase campaign_battle
} else {
    $InputLogPath = (Resolve-Path -LiteralPath $InputLogPath).Path
    & powershell.exe -NoProfile -ExecutionPolicy Bypass `
        -File (Join-Path $PSScriptRoot "collect_probe_logs.ps1") `
        -LogPaths $InputLogPath `
        -EvidencePhase campaign_battle
}
if ($LASTEXITCODE -ne 0) { throw "Base evidence collection failed with exit code $LASTEXITCODE." }
$CollectionWatch.Stop()

$EvidenceRoot = Get-ChildItem -LiteralPath $EvidenceParent -Directory -Filter "probe_*" |
    Where-Object { $Before -notcontains $_.FullName } |
    Sort-Object LastWriteTimeUtc -Descending |
    Select-Object -First 1 -ExpandProperty FullName
if (-not $EvidenceRoot) { throw "Could not identify the new evidence folder." }

$CampaignSummaryPath = Join-Path $EvidenceRoot "probe_summary.json"
$ManifestPath = Join-Path $EvidenceRoot "evidence_manifest.json"
foreach ($Path in @($CampaignSummaryPath, $ManifestPath)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing evidence file: $Path" }
}

$InitialManifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$CollectedLogs = @($InitialManifest.logs)
if ($CollectedLogs.Count -ne 1) {
    throw "Expected exactly one combined runtime log, found $($CollectedLogs.Count)."
}
$LogPath = [string]$CollectedLogs[0].private_copy
if (-not (Test-Path -LiteralPath $LogPath -PathType Leaf)) {
    throw "Collected runtime log is missing: $LogPath"
}

$Python = Get-PythonCommand
$CampaignReportPath = Join-Path $EvidenceRoot "campaign_shadow_report.json"
$BattleSummaryPath = Join-Path $EvidenceRoot "battle_summary.json"
$BattleReportPath = Join-Path $EvidenceRoot "battle_report.json"
$VerificationPath = Join-Path $EvidenceRoot "campaign_battle_verification.json"

$CampaignWatch = [System.Diagnostics.Stopwatch]::StartNew()
& $Python.Command @($Python.Prefix) (Join-Path $PSScriptRoot "run_shadow_campaign.py") $LogPath --output $CampaignReportPath
if ($LASTEXITCODE -ne 0) { throw "Campaign shadow pipeline failed with exit code $LASTEXITCODE." }
$CampaignWatch.Stop()

$BattleWatch = [System.Diagnostics.Stopwatch]::StartNew()
& $Python.Command @($Python.Prefix) (Join-Path $PSScriptRoot "parse_battle_log.py") $LogPath --output $BattleSummaryPath
$BattleParseExit = $LASTEXITCODE
if ($BattleParseExit -eq 0) {
    & $Python.Command @($Python.Prefix) (Join-Path $PSScriptRoot "run_battle_report.py") $LogPath --output $BattleReportPath
    $BattleReportExit = $LASTEXITCODE
} else {
    $BattleReportExit = $BattleParseExit
    [ordered]@{
        schema_version = 1
        mode = "BATTLE_OBSERVATION_NO_ORDERS"
        evidence_label = "UNVERIFIED"
        battle_count = 0
        completed_battle_count = 0
        battle_reports = @()
        authority = [ordered]@{
            unitcontrollers_created = $false
            orders_emitted = $false
            battle_speed_modified = $false
            save_values_written = $false
            visibility_modified = $false
        }
        warnings = @("No valid TRANS_BATTLE session was parsed.")
    } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $BattleReportPath -Encoding UTF8
    [ordered]@{
        schema_version = 1
        evidence_status = "UNVERIFIED"
        battle_session_count = 0
        completed_battle_count = 0
        sessions = @()
        capability_failures = @("battle_probe_not_observed")
        warnings = @("No valid TRANS_BATTLE session was parsed.")
    } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $BattleSummaryPath -Encoding UTF8
}
$BattleWatch.Stop()

$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$Manifest | Add-Member -NotePropertyName "processing" -NotePropertyValue ([ordered]@{
    collection_and_campaign_parse_ms = [math]::Round($CollectionWatch.Elapsed.TotalMilliseconds, 3)
    campaign_pipeline_ms = [math]::Round($CampaignWatch.Elapsed.TotalMilliseconds, 3)
    battle_pipeline_ms = [math]::Round($BattleWatch.Elapsed.TotalMilliseconds, 3)
}) -Force
$Manifest | Add-Member -NotePropertyName "campaign_shadow_report" -NotePropertyValue ([ordered]@{ path = $CampaignReportPath; sha256 = Get-Sha256 $CampaignReportPath }) -Force
$Manifest | Add-Member -NotePropertyName "battle_summary" -NotePropertyValue ([ordered]@{ path = $BattleSummaryPath; sha256 = Get-Sha256 $BattleSummaryPath }) -Force
$Manifest | Add-Member -NotePropertyName "battle_report" -NotePropertyValue ([ordered]@{ path = $BattleReportPath; sha256 = Get-Sha256 $BattleReportPath }) -Force
$Manifest | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $ManifestPath -Encoding UTF8

$ShadowPack = @($Manifest.installed_probe_packs | Where-Object { $_.name -eq "transcendence_shadow_probe.pack" })
if ($ShadowPack.Count -ne 1) { throw "Could not identify the installed shadow pack." }
$ExpectedShadowHash = [string]$ShadowPack[0].staged_sha256

& $Python.Command @($Python.Prefix) `
    (Join-Path $PSScriptRoot "verify_campaign_battle_gate.py") `
    --log $LogPath `
    --campaign-summary $CampaignSummaryPath `
    --battle-summary $BattleSummaryPath `
    --manifest $ManifestPath `
    --campaign-report $CampaignReportPath `
    --battle-report $BattleReportPath `
    --expected-pack-sha256 $ExpectedShadowHash `
    --minimum-turns $MinimumTurns `
    --minimum-completed-battles $MinimumCompletedBattles `
    --output $VerificationPath
$VerifierExit = $LASTEXITCODE
$TotalWatch.Stop()

$ExportRoot = Join-Path $RepoRoot "local_inputs\runtime_probe\exports"
New-Item -ItemType Directory -Force -Path $ExportRoot | Out-Null
$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$BundleFolder = Join-Path $EvidenceRoot "upload_bundle"
New-Item -ItemType Directory -Force -Path $BundleFolder | Out-Null

$ExportFiles = @(
    @{ Source = $LogPath; Name = "transcendence_runtime_log.txt" },
    @{ Source = $CampaignSummaryPath; Name = "campaign_probe_summary.json" },
    @{ Source = $BattleSummaryPath; Name = "battle_summary.json" },
    @{ Source = $ManifestPath; Name = "evidence_manifest.json" },
    @{ Source = $CampaignReportPath; Name = "campaign_shadow_report.json" },
    @{ Source = $BattleReportPath; Name = "battle_report.json" },
    @{ Source = $VerificationPath; Name = "campaign_battle_verification.json" }
)
if ($null -ne $Manifest.combined_session_manifest) {
    $SessionEvidencePath = [string]$Manifest.combined_session_manifest.private_copy
    if (-not (Test-Path -LiteralPath $SessionEvidencePath -PathType Leaf)) {
        throw "Combined-session evidence manifest is missing: $SessionEvidencePath"
    }
    $ExportFiles += @{ Source = $SessionEvidencePath; Name = "combined_session_manifest.json" }
}
$ExportRecords = @()
foreach ($Item in $ExportFiles) {
    if (-not (Test-Path -LiteralPath $Item.Source -PathType Leaf)) { throw "Export file missing: $($Item.Source)" }
    $Destination = Join-Path $BundleFolder $Item.Name
    Copy-Item -LiteralPath $Item.Source -Destination $Destination -Force
    $ExportRecords += [ordered]@{ name = $Item.Name; size_bytes = [int64](Get-Item -LiteralPath $Destination).Length; sha256 = Get-Sha256 $Destination }
}

$Verification = Get-Content -LiteralPath $VerificationPath -Raw | ConvertFrom-Json
$ExportManifestPath = Join-Path $BundleFolder "export_manifest.json"
[ordered]@{
    schema_version = 1
    exported_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    gate = "CONSOLIDATED_CAMPAIGN_AND_BATTLE_SHADOW"
    minimum_turns = $MinimumTurns
    minimum_completed_battles = $MinimumCompletedBattles
    verification_status = [string]$Verification.status
    verification_result_digest = [string]$Verification.result_digest
    total_collection_processing_ms = [math]::Round($TotalWatch.Elapsed.TotalMilliseconds, 3)
    files = $ExportRecords
} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $ExportManifestPath -Encoding UTF8

$ZipPath = $null
if (-not $SkipUploadZip) {
    $ZipPath = Join-Path $ExportRoot ("Transcendence_Campaign_Battle_Evidence_" + $Timestamp + ".zip")
    Compress-Archive -Path (Join-Path $BundleFolder "*") -DestinationPath $ZipPath -Force
}

Write-Host ""
if ($VerifierExit -eq 0) {
    Write-Host "CONSOLIDATED CAMPAIGN + BATTLE GATE PASSED" -ForegroundColor Green
} else {
    Write-Host "EVIDENCE EXPORTED, BUT THE COMBINED GATE DID NOT PASS" -ForegroundColor Yellow
    Write-Host "This usually means fewer than five turns or no completed manually fought battle was captured."
}
Write-Host "Evidence folder: $EvidenceRoot"
if ($SkipUploadZip) {
    Write-Host "Generic private upload ZIP skipped; the SFO collector will create the path-free verified bundle." -ForegroundColor Green
} else {
    Write-Host "Upload this single ZIP:" -ForegroundColor Yellow
    Write-Host $ZipPath -ForegroundColor Yellow
}
if ($VerifierExit -ne 0) { exit $VerifierExit }

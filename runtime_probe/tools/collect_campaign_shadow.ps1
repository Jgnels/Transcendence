﻿[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [int]$MinimumTurns = 5
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
    if (-not $Python) {
        throw "Python 3 was not found."
    }
    return [pscustomobject]@{
        Command = $Python.Source
        Prefix = $Prefix
    }
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

if ($MinimumTurns -lt 3) {
    throw "MinimumTurns cannot be less than 3 for a consolidated campaign run."
}

$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$EvidenceParent = Join-Path $RepoRoot "local_inputs\logs\wh3"
New-Item -ItemType Directory -Force -Path $EvidenceParent | Out-Null
$Before = @(
    Get-ChildItem -LiteralPath $EvidenceParent -Directory -Filter "probe_*" `
        -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty FullName
)

$CollectionWatch = [System.Diagnostics.Stopwatch]::StartNew()
& powershell.exe -NoProfile -ExecutionPolicy Bypass `
    -File (Join-Path $PSScriptRoot "collect_probe_logs.ps1") `
    -EvidencePhase campaign_shadow
if ($LASTEXITCODE -ne 0) {
    throw "Base shadow evidence collection failed with exit code $LASTEXITCODE."
}
$CollectionWatch.Stop()

$EvidenceRoot = Get-ChildItem -LiteralPath $EvidenceParent -Directory -Filter "probe_*" |
    Where-Object { $Before -notcontains $_.FullName } |
    Sort-Object LastWriteTimeUtc -Descending |
    Select-Object -First 1 -ExpandProperty FullName
if (-not $EvidenceRoot) {
    throw "Could not identify the newly collected evidence folder."
}

$LogPath = Join-Path $EvidenceRoot "lua_mod_log.txt"
$SummaryPath = Join-Path $EvidenceRoot "probe_summary.json"
$ManifestPath = Join-Path $EvidenceRoot "evidence_manifest.json"
foreach ($Path in @($LogPath, $SummaryPath, $ManifestPath)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Collected evidence file is missing: $Path"
    }
}

$Python = Get-PythonCommand
$CampaignPath = Join-Path $EvidenceRoot "campaign_shadow_report.json"
$CampaignWatch = [System.Diagnostics.Stopwatch]::StartNew()
& $Python.Command @($Python.Prefix) `
    (Join-Path $PSScriptRoot "run_shadow_campaign.py") `
    $LogPath `
    --output $CampaignPath
if ($LASTEXITCODE -ne 0) {
    throw "Multi-turn shadow pipeline failed with exit code $LASTEXITCODE."
}
$CampaignWatch.Stop()

$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$Manifest | Add-Member -NotePropertyName "processing" -NotePropertyValue ([ordered]@{
    collection_and_parse_ms = [math]::Round($CollectionWatch.Elapsed.TotalMilliseconds, 3)
    campaign_pipeline_ms = [math]::Round($CampaignWatch.Elapsed.TotalMilliseconds, 3)
}) -Force
$Manifest | Add-Member -NotePropertyName "campaign_shadow_report" -NotePropertyValue ([ordered]@{
    path = $CampaignPath
    sha256 = Get-Sha256 $CampaignPath
}) -Force
$Manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $ManifestPath -Encoding UTF8

$VerificationPath = Join-Path $EvidenceRoot "campaign_shadow_verification.json"
$VerificationWatch = [System.Diagnostics.Stopwatch]::StartNew()
& $Python.Command @($Python.Prefix) `
    (Join-Path $PSScriptRoot "verify_shadow_campaign.py") `
    --log $LogPath `
    --summary $SummaryPath `
    --manifest $ManifestPath `
    --campaign-report $CampaignPath `
    --minimum-turns $MinimumTurns `
    --output $VerificationPath
$VerifierExit = $LASTEXITCODE
$VerificationWatch.Stop()
if ($VerifierExit -ne 0) {
    throw "Consolidated shadow verification did not pass. Review $VerificationPath."
}

$ExportRoot = Join-Path $RepoRoot "local_inputs\runtime_probe\exports"
New-Item -ItemType Directory -Force -Path $ExportRoot | Out-Null
$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$BundleFolder = Join-Path $EvidenceRoot "upload_bundle"
New-Item -ItemType Directory -Force -Path $BundleFolder | Out-Null

$ExportFiles = @(
    @{ Source = $LogPath; Name = "lua_mod_log.txt" },
    @{ Source = $SummaryPath; Name = "probe_summary.json" },
    @{ Source = $ManifestPath; Name = "evidence_manifest.json" },
    @{ Source = $CampaignPath; Name = "campaign_shadow_report.json" },
    @{ Source = $VerificationPath; Name = "campaign_shadow_verification.json" }
)
$ExportRecords = @()
foreach ($Item in $ExportFiles) {
    $Destination = Join-Path $BundleFolder $Item.Name
    Copy-Item -LiteralPath $Item.Source -Destination $Destination -Force
    $ExportRecords += [ordered]@{
        name = $Item.Name
        size_bytes = [int64](Get-Item -LiteralPath $Destination).Length
        sha256 = Get-Sha256 $Destination
    }
}

$ExportManifestPath = Join-Path $BundleFolder "export_manifest.json"
$ExportManifest = [ordered]@{
    schema_version = 1
    exported_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    gate = "CONSOLIDATED_CAMPAIGN_SHADOW"
    minimum_turns = $MinimumTurns
    verification_status = "OBSERVED"
    verification_sha256 = Get-Sha256 $VerificationPath
    verifier_runtime_ms = [math]::Round($VerificationWatch.Elapsed.TotalMilliseconds, 3)
    files = $ExportRecords
}
$ExportManifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ExportManifestPath -Encoding UTF8

$ZipPath = Join-Path $ExportRoot ("Transcendence_Campaign_Shadow_Evidence_" + $Timestamp + ".zip")
Compress-Archive -Path (Join-Path $BundleFolder "*") -DestinationPath $ZipPath -Force

Write-Host ""
Write-Host "CONSOLIDATED CAMPAIGN SHADOW RUN PASSED" -ForegroundColor Green
Write-Host "Evidence folder: $EvidenceRoot"
Write-Host "Upload this single ZIP:" -ForegroundColor Yellow
Write-Host $ZipPath -ForegroundColor Yellow

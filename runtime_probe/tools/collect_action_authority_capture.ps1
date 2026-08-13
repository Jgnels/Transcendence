#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [string]$InputLogPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    if ([string]::IsNullOrWhiteSpace($PSScriptRoot)) { throw "Supply -RepoRoot explicitly." }
    $RepoRoot = Join-Path $PSScriptRoot "..\.."
}
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
function Get-Sha256([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Get-PythonCommand {
    $Python = Get-Command python -ErrorAction SilentlyContinue; $Prefix = @()
    if (-not $Python) { $Python = Get-Command py -ErrorAction SilentlyContinue; if ($Python) { $Prefix = @("-3") } }
    if (-not $Python) { throw "Python 3 was not found." }
    return [pscustomobject]@{ Command = $Python.Source; Prefix = $Prefix }
}

$PreparedPath = Join-Path $RepoRoot "local_inputs\runtime_probe\action_authority\sessions\latest.json"
if (-not (Test-Path -LiteralPath $PreparedPath -PathType Leaf)) { throw "Prepared action-authority session missing. Run prepare_action_authority_capture.ps1 first." }
$Prepared = Get-Content -LiteralPath $PreparedPath -Raw -Encoding UTF8 | ConvertFrom-Json
$PreparedAt = [DateTimeOffset]::Parse([string]$Prepared.prepared_at_utc).UtcDateTime
if ([string]::IsNullOrWhiteSpace($InputLogPath)) { $InputLogPath = [string]$Prepared.runtime_log }
$InputLogPath = (Resolve-Path -LiteralPath $InputLogPath).Path
$LogInfo = Get-Item -LiteralPath $InputLogPath
if ($LogInfo.LastWriteTimeUtc -lt $PreparedAt) { throw "Runtime log predates the prepared session and is stale." }

$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$EvidenceRoot = Join-Path $RepoRoot ("local_inputs\runtime_probe\action_authority\captures\capture_" + $Timestamp)
$ExportRoot = Join-Path $RepoRoot "local_inputs\runtime_probe\exports"
New-Item -ItemType Directory -Force -Path $EvidenceRoot, $ExportRoot | Out-Null
$PrivateLog = Join-Path $EvidenceRoot "action_authority_runtime_log.txt"
Copy-Item -LiteralPath $InputLogPath -Destination $PrivateLog -Force
$PreparedCopy = Join-Path $EvidenceRoot "prepared_manifest.json"
Copy-Item -LiteralPath $PreparedPath -Destination $PreparedCopy -Force

$Python = Get-PythonCommand
$SummaryPath = Join-Path $EvidenceRoot "action_authority_summary.json"
$VerificationPath = Join-Path $EvidenceRoot "action_authority_verification.json"
& $Python.Command @($Python.Prefix) (Join-Path $RepoRoot "runtime_probe\tools\parse_action_authority_log.py") $PrivateLog --output $SummaryPath | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Action-authority log parsing failed with exit code $LASTEXITCODE." }
& $Python.Command @($Python.Prefix) (Join-Path $RepoRoot "runtime_probe\tools\verify_action_authority_capture.py") $SummaryPath $PreparedCopy --expected-pack-sha256 ([string]$Prepared.installed_pack_sha256) --output $VerificationPath | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Action-authority verification failed with exit code $LASTEXITCODE." }

$PublicAttestation = [ordered]@{
    schema_version = 1
    capture_kind = "action_authority"
    prepared_at_utc = [string]$Prepared.prepared_at_utc
    pack_name = [string]$Prepared.pack_name
    staged_pack_sha256 = [string]$Prepared.staged_pack_sha256
    installed_pack_sha256 = [string]$Prepared.installed_pack_sha256
    runtime_log_cleared = [bool]$Prepared.runtime_log_cleared
    active_mod_list_modified = [bool]$Prepared.active_mod_list_modified
    wh3_save_modified = [bool]$Prepared.wh3_save_modified
    project_orders_enabled = [bool]$Prepared.project_orders_enabled
}
$PublicAttestationPath = Join-Path $EvidenceRoot "public_preparation_attestation.json"
$PublicAttestation | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $PublicAttestationPath -Encoding UTF8

$PublicManifest = [ordered]@{
    schema_version = 2
    capture_kind = "action_authority"
    collected_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    raw_log_sha256 = Get-Sha256 $PrivateLog
    raw_log_size_bytes = [int64](Get-Item -LiteralPath $PrivateLog).Length
    raw_log_included_in_export = $false
    prepared_manifest_sha256 = Get-Sha256 $PreparedCopy
    preparation_attestation_sha256 = Get-Sha256 $PublicAttestationPath
    summary_sha256 = Get-Sha256 $SummaryPath
    verification_sha256 = Get-Sha256 $VerificationPath
    installed_pack_sha256 = [string]$Prepared.installed_pack_sha256
    authority = "NO_ORDERS"
    project_issue_attempt_count = 0
    direct_acknowledgement_count = 0
}
$PublicManifestPath = Join-Path $EvidenceRoot "public_capture_manifest.json"
$PublicManifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $PublicManifestPath -Encoding UTF8

$ExportStage = Join-Path $EvidenceRoot "public_export"
New-Item -ItemType Directory -Force -Path $ExportStage | Out-Null
Copy-Item -LiteralPath $SummaryPath, $VerificationPath, $PublicAttestationPath, $PublicManifestPath -Destination $ExportStage -Force
$ZipPath = Join-Path $ExportRoot ("Transcendence_ActionAuthorityCapture_" + $Timestamp + ".zip")
Compress-Archive -Path (Join-Path $ExportStage "*") -DestinationPath $ZipPath -CompressionLevel Optimal

Write-Host "`nACTION-AUTHORITY CAPTURE COMPLETE" -ForegroundColor Green
Write-Host "Private raw evidence retained locally: $PrivateLog"
Write-Host "Public-safe export: $ZipPath"
Write-Host "Export SHA-256: $(Get-Sha256 $ZipPath)"
Write-Host "Upload the single ZIP. It excludes the raw runtime log and personal paths." -ForegroundColor Yellow

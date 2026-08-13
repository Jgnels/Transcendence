[CmdletBinding()]
param([string]$RepoRoot = "")
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    if ([string]::IsNullOrWhiteSpace($PSScriptRoot)) { throw "PowerShell did not provide PSScriptRoot; supply -RepoRoot explicitly." }
    $RepoRoot = Join-Path $PSScriptRoot "..\.."
}
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
function Get-PythonCommand {
    $Python = Get-Command python -ErrorAction SilentlyContinue; $Prefix = @()
    if (-not $Python) { $Python = Get-Command py -ErrorAction SilentlyContinue; if ($Python) { $Prefix = @("-3") } }
    if (-not $Python) { throw "Python 3 was not found." }
    return [pscustomobject]@{ Command = $Python.Source; Prefix = $Prefix }
}

$Root = Join-Path $RepoRoot "local_inputs\runtime_probe\campaign_feasibility_embedded_sessions"
$Latest = Join-Path $Root "latest.json"
if (-not (Test-Path -LiteralPath $Latest -PathType Leaf)) { throw "No embedded campaign feasibility retry session was prepared." }
$Manifest = Get-Content -LiteralPath $Latest -Raw | ConvertFrom-Json
$RuntimeLog = [string]$Manifest.runtime_log
$Backup = [string]$Manifest.probe_backup_private
$InstalledProbe = [string]$Manifest.installed_probe
$Python = Get-PythonCommand

try {
    if (-not (Test-Path -LiteralPath $RuntimeLog -PathType Leaf)) { throw "WH3 runtime log was not created for the embedded retry." }
    $RuntimeText = Get-Content -LiteralPath $RuntimeLog -Raw
    $PollTick = $RuntimeText -match 'FEASIBILITY_POLL_TICK'
    $RequestSeen = $RuntimeText -match 'FEASIBILITY_REQUEST_SEEN'
    $QueryResult = $RuntimeText -match 'FEASIBILITY_QUERY_RESULT'
    $PacketEnd = $RuntimeText -match 'FEASIBILITY_PACKET_END'
    $Rejected = $RuntimeText -match 'FEASIBILITY_REQUEST_REJECTED'
    if (-not $PacketEnd) {
        throw "The embedded read-only query packet did not complete. Runtime diagnostics: poll_tick=$PollTick request_seen=$RequestSeen query_result=$QueryResult packet_end=$PacketEnd rejected=$Rejected. Do not repeat WH3; preserve this log for diagnosis."
    }

    $Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
    $OutputDir = Join-Path $Root ("public_export_" + $Timestamp)
    $Zip = Join-Path $Root ("Transcendence_CampaignFeasibilityEmbeddedObservation_" + $Timestamp + ".zip")
    & $Python.Command @($Python.Prefix) (Join-Path $PSScriptRoot "build_campaign_feasibility_live_artifact.py") `
        --log $RuntimeLog `
        --plan ([string]$Manifest.plan) `
        --environment ([string]$Manifest.environment_public) `
        --expected-pack-sha256 ([string]$Manifest.probe_pack_sha256) `
        --output-dir $OutputDir `
        --zip $Zip
    if ($LASTEXITCODE -ne 0) { throw "Embedded campaign feasibility adjudication failed with exit code $LASTEXITCODE." }
    Write-Host ""
    Write-Host "CAMPAIGN FEASIBILITY EMBEDDED OBSERVATION EXPORTED" -ForegroundColor Green
    Write-Host "Upload this single ZIP to the project chat:"
    Write-Host $Zip -ForegroundColor Yellow
}
finally {
    if ($Backup -and (Test-Path -LiteralPath $Backup -PathType Leaf)) {
        Copy-Item -LiteralPath $Backup -Destination $InstalledProbe -Force
        Write-Host "Restored the pre-retry campaign feasibility probe pack." -ForegroundColor DarkGray
    }
}

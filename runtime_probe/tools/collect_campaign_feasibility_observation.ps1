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
    $Python = Get-Command python -ErrorAction SilentlyContinue
    $Prefix = @()
    if (-not $Python) { $Python = Get-Command py -ErrorAction SilentlyContinue; if ($Python) { $Prefix = @("-3") } }
    if (-not $Python) { throw "Python 3 was not found." }
    return [pscustomobject]@{ Command = $Python.Source; Prefix = $Prefix }
}

$SessionsRoot = Join-Path $RepoRoot "local_inputs\runtime_probe\campaign_feasibility_sessions"
$Latest = Join-Path $SessionsRoot "latest.json"
if (-not (Test-Path -LiteralPath $Latest -PathType Leaf)) { throw "No prepared campaign feasibility session was found." }
$Session = Get-Content -LiteralPath $Latest -Raw | ConvertFrom-Json
$StatusPath = [string]$Session.sidecar_status
if (-not (Test-Path -LiteralPath $StatusPath -PathType Leaf)) { throw "Sidecar status is missing; the prepared session cannot be verified." }
$Status = Get-Content -LiteralPath $StatusPath -Raw | ConvertFrom-Json
if ([string]$Status.state -ne "CAPTURE_COMPLETE") {
    $RuntimeLogForDiagnosis = [string]$Session.runtime_log
    $RuntimeText = if (Test-Path -LiteralPath $RuntimeLogForDiagnosis -PathType Leaf) { Get-Content -LiteralPath $RuntimeLogForDiagnosis -Raw -ErrorAction SilentlyContinue } else { "" }
    $PollTick = $RuntimeText -match 'FEASIBILITY_POLL_TICK'
    $RequestSeen = $RuntimeText -match 'FEASIBILITY_REQUEST_SEEN'
    $QueryResult = $RuntimeText -match 'FEASIBILITY_QUERY_RESULT'
    $Rejected = $RuntimeText -match 'FEASIBILITY_REQUEST_REJECTED'
    throw "The read-only query packet did not complete. Current sidecar state: $($Status.state). Runtime diagnostics: poll_tick=$PollTick request_seen=$RequestSeen query_result=$QueryResult rejected=$Rejected. WAITING_FOR_CURRENT_ASSIGNMENT means no v0.2G assignment existed and no query was run."
}

$StopFile = [string]$Session.sidecar_stop_file
New-Item -ItemType File -Force -Path $StopFile | Out-Null
Start-Sleep -Milliseconds 500

$RuntimeLog = [string]$Session.runtime_log
if (-not (Test-Path -LiteralPath $RuntimeLog -PathType Leaf)) { throw "Runtime log is missing: $RuntimeLog" }
$SessionRoot = Split-Path -Parent ([string]$Session.sidecar_status)
$PlanPath = Join-Path $SessionRoot "current_feasibility_plan.json"
if (-not (Test-Path -LiteralPath $PlanPath -PathType Leaf)) { throw "Sidecar plan is missing: $PlanPath" }
$EnvironmentPublic = [string]$Session.environment_public
$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$ExportsRoot = Join-Path $RepoRoot "local_inputs\runtime_probe\exports"
$OutputDir = Join-Path $SessionRoot "public_export"
$ZipPath = Join-Path $ExportsRoot ("Transcendence_CampaignFeasibilityObservation_" + $Timestamp + ".zip")
New-Item -ItemType Directory -Force -Path $ExportsRoot, $OutputDir | Out-Null

$Python = Get-PythonCommand
& $Python.Command @($Python.Prefix) (Join-Path $PSScriptRoot "build_campaign_feasibility_live_artifact.py") `
    --log $RuntimeLog `
    --plan $PlanPath `
    --environment $EnvironmentPublic `
    --expected-pack-sha256 ([string]$Session.probe_pack_sha256) `
    --output-dir $OutputDir `
    --zip $ZipPath
if ($LASTEXITCODE -ne 0) { throw "Campaign feasibility live verification failed with exit code $LASTEXITCODE." }

$RequestFile = [string]$Session.request_file
if (Test-Path -LiteralPath $RequestFile -PathType Leaf) { Remove-Item -LiteralPath $RequestFile -Force }
Write-Host ""
Write-Host "CAMPAIGN FEASIBILITY OBSERVATION EXPORTED" -ForegroundColor Green
Write-Host "Upload this single ZIP to the project chat:"
Write-Host $ZipPath -ForegroundColor Yellow

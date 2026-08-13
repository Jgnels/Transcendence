[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [string]$CampaignDifficulty = "Legendary",
    [string]$BattleDifficulty = "Very Hard",
    [bool]$Ironman = $true,
    [bool]$BattleRealism = $true,
    [string]$BattlefieldLimitations = "OWNER_CONFIGURED",
    [string]$Faction = "Karl Franz / Reikland",
    [string]$SfoWorkshopId = "2792731173"
)

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
    if (-not $Python) {
        $Python = Get-Command py -ErrorAction SilentlyContinue
        if ($Python) { $Prefix = @("-3") }
    }
    if (-not $Python) { throw "Python 3 was not found." }
    return [pscustomobject]@{ Command = $Python.Source; Prefix = $Prefix }
}
function Get-Sha256([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }

$MachineManifestPath = Join-Path $RepoRoot "local_inputs\machine_profiles\gaming_laptop_private.json"
if (-not (Test-Path -LiteralPath $MachineManifestPath -PathType Leaf)) { throw "Private machine manifest not found: $MachineManifestPath" }
$MachineManifest = Get-Content -LiteralPath $MachineManifestPath -Raw | ConvertFrom-Json
$GameRoot = [string]$MachineManifest.game.install_path
if (-not $GameRoot -or -not (Test-Path -LiteralPath $GameRoot -PathType Container)) { throw "WH3 installation path is missing or invalid in the private machine manifest." }
$GameData = Join-Path $GameRoot "data"
$ProbeName = "transcendence_campaign_feasibility_probe.pack"
$InstalledProbe = Join-Path $GameData $ProbeName

$SessionsRoot = Join-Path $RepoRoot "local_inputs\runtime_probe\campaign_feasibility_sessions"
$LatestPath = Join-Path $SessionsRoot "latest.json"
if (-not (Test-Path -LiteralPath $LatestPath -PathType Leaf)) { throw "No prior campaign feasibility session is available for an embedded retry." }
$Prior = Get-Content -LiteralPath $LatestPath -Raw | ConvertFrom-Json
$PriorSessionRoot = Split-Path -Parent ([string]$Prior.sidecar_status)
$PriorStatusPath = [string]$Prior.sidecar_status
$PriorPlan = Join-Path $PriorSessionRoot "current_feasibility_plan.json"
$PriorRequest = [string]$Prior.request_file
if (-not (Test-Path -LiteralPath $PriorStatusPath -PathType Leaf)) { throw "Prior sidecar status is missing: $PriorStatusPath" }
$PriorStatus = Get-Content -LiteralPath $PriorStatusPath -Raw | ConvertFrom-Json
if ([string]$PriorStatus.state -ne "WAITING_FOR_QUERY_RESULTS") { throw "Embedded retry requires a prior WAITING_FOR_QUERY_RESULTS session; current state is $($PriorStatus.state)." }
if (-not (Test-Path -LiteralPath $PriorPlan -PathType Leaf)) { throw "Prior saved feasibility plan is missing: $PriorPlan" }
if (-not (Test-Path -LiteralPath $PriorRequest -PathType Leaf)) { throw "Prior canonical request is missing: $PriorRequest" }

$Plan = Get-Content -LiteralPath $PriorPlan -Raw | ConvertFrom-Json
if ([string]$Plan.authority -ne "NO_ORDERS" -or [string]$Plan.application_authority -ne "PROHIBITED") { throw "Prior plan authority boundary is not acceptable." }

# Freeze the prior request before stopping the stale helper.
$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$EmbeddedSessionsRoot = Join-Path $RepoRoot "local_inputs\runtime_probe\campaign_feasibility_embedded_sessions"
$SessionId = "campaign_feasibility_embedded_" + $Timestamp
$SessionRoot = Join-Path $EmbeddedSessionsRoot $SessionId
New-Item -ItemType Directory -Force -Path $SessionRoot | Out-Null
$FrozenPlan = Join-Path $SessionRoot "embedded_feasibility_plan.json"
$FrozenRequest = Join-Path $SessionRoot "embedded_request_private.txt"
Copy-Item -LiteralPath $PriorPlan -Destination $FrozenPlan -Force
Copy-Item -LiteralPath $PriorRequest -Destination $FrozenRequest -Force

# Stop only the sidecar explicitly bound to the prior session.
try {
    $PriorPid = [int]$Prior.sidecar_pid
    $Process = Get-Process -Id $PriorPid -ErrorAction SilentlyContinue
    if ($Process) { Stop-Process -Id $PriorPid -Force -ErrorAction SilentlyContinue }
} catch {}

$Python = Get-PythonCommand
$GeneratedRoot = Join-Path $SessionRoot "generated_probe_private"
& $Python.Command @($Python.Prefix) (Join-Path $PSScriptRoot "build_embedded_campaign_feasibility_probe.py") `
    --plan $FrozenPlan `
    --request $FrozenRequest `
    --output-dir $GeneratedRoot
if ($LASTEXITCODE -ne 0) { throw "Embedded campaign feasibility probe build failed with exit code $LASTEXITCODE." }
$GeneratedManifestPath = Join-Path $GeneratedRoot "embedded_probe_manifest.json"
$GeneratedPack = Join-Path $GeneratedRoot $ProbeName
$GeneratedManifest = Get-Content -LiteralPath $GeneratedManifestPath -Raw | ConvertFrom-Json
if ([string]$GeneratedManifest.policy_authority -ne "NO_ORDERS" -or [string]$GeneratedManifest.application_authority -ne "PROHIBITED") { throw "Generated embedded probe failed authority validation." }

$ProbeBackup = Join-Path $SessionRoot "pre_retry_probe_backup_private.pack"
if (Test-Path -LiteralPath $InstalledProbe -PathType Leaf) { Copy-Item -LiteralPath $InstalledProbe -Destination $ProbeBackup -Force }
Copy-Item -LiteralPath $GeneratedPack -Destination $InstalledProbe -Force
if ((Get-Sha256 $InstalledProbe) -ne [string]$GeneratedManifest.pack_sha256) { throw "Installed embedded probe hash mismatch." }

# The embedded retry deliberately does not use the old runtime request file.
if (Test-Path -LiteralPath $PriorRequest -PathType Leaf) { Remove-Item -LiteralPath $PriorRequest -Force }
$RuntimeLog = Join-Path $GameRoot "transcendence_runtime_log.txt"
$ArchiveRoot = Join-Path $RepoRoot "local_inputs\runtime_probe\runtime_log_archives"
New-Item -ItemType Directory -Force -Path $ArchiveRoot | Out-Null
if (Test-Path -LiteralPath $RuntimeLog -PathType Leaf) {
    Copy-Item -LiteralPath $RuntimeLog -Destination (Join-Path $ArchiveRoot ("transcendence_runtime_log_before_embedded_" + $Timestamp + ".txt")) -Force
    Remove-Item -LiteralPath $RuntimeLog -Force
}

Write-Host ""
Write-Host "SFO READ-ONLY EMBEDDED FEASIBILITY RETRY SETUP" -ForegroundColor Yellow
Write-Host "In the WH3 launcher, keep exactly these two mods enabled and every other mod disabled:"
Write-Host "  1. SFO: Grimhammer III (Workshop item $SfoWorkshopId)"
Write-Host "  2. $ProbeName"
Write-Host "The probe filename is unchanged, but this session uses a generated read-only pack with the exact prior query packet embedded before WH3 starts."
Write-Host "Close the launcher after confirming that load order. Do not launch WH3 yet."
$Confirmation = (Read-Host "Type READY after the launcher shows only those two enabled mods").Trim()
if ($Confirmation -ine "READY") { throw "Embedded campaign feasibility retry preparation cancelled." }

$EnvironmentPrivate = Join-Path $SessionRoot "sfo_environment_private.json"
$EnvironmentPublic = Join-Path $SessionRoot "sfo_environment_attestation.json"
& $Python.Command @($Python.Prefix) (Join-Path $PSScriptRoot "capture_sfo_environment.py") `
    --game-root $GameRoot `
    --appdata-root $env:APPDATA `
    --shadow-pack $InstalledProbe `
    --probe-name $ProbeName `
    --sfo-workshop-id $SfoWorkshopId `
    --campaign-difficulty $CampaignDifficulty `
    --battle-difficulty $BattleDifficulty `
    --ironman $Ironman.ToString().ToLowerInvariant() `
    --battle-realism $BattleRealism.ToString().ToLowerInvariant() `
    --battlefield-limitations $BattlefieldLimitations `
    --faction $Faction `
    --private-output $EnvironmentPrivate `
    --public-output $EnvironmentPublic
if ($LASTEXITCODE -ne 0) { throw "SFO embedded feasibility environment preflight failed with exit code $LASTEXITCODE." }

$Manifest = [ordered]@{
    schema_version = 1
    session_kind = "SFO_CAMPAIGN_FEASIBILITY_EMBEDDED_READ_ONLY"
    session_id = $SessionId
    source_session_id = [string]$Prior.session_id
    prepared_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    runtime_log = $RuntimeLog
    plan = $FrozenPlan
    request_private = $FrozenRequest
    generated_probe_manifest = $GeneratedManifestPath
    probe_name = $ProbeName
    probe_pack_sha256 = [string]$GeneratedManifest.pack_sha256
    plan_digest = [string]$GeneratedManifest.plan_digest
    turn = [int]$GeneratedManifest.turn
    query_count = [int]$GeneratedManifest.query_count
    environment_private = $EnvironmentPrivate
    environment_public = $EnvironmentPublic
    probe_backup_private = $ProbeBackup
    installed_probe = $InstalledProbe
    policy_authority = "NO_ORDERS"
    application_authority = "PROHIBITED"
    orders_emitted = $false
    save_values_written = $false
}
$ManifestPath = Join-Path $SessionRoot "session_manifest_private.json"
$Manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ManifestPath -Encoding UTF8
New-Item -ItemType Directory -Force -Path $EmbeddedSessionsRoot | Out-Null
Copy-Item -LiteralPath $ManifestPath -Destination (Join-Path $EmbeddedSessionsRoot "latest.json") -Force

Write-Host ""
Write-Host "CAMPAIGN FEASIBILITY EMBEDDED RETRY READY" -ForegroundColor Green
Write-Host "Generated probe SHA-256: $($Manifest.probe_pack_sha256)"
Write-Host "Plan digest: $($Manifest.plan_digest)"
Write-Host "Turn: $($Manifest.turn)"
Write-Host "Queries: $($Manifest.query_count)"
Write-Host "Session: $SessionId"
Write-Host ""
Write-Host "Now launch WH3 and load the SAME unchanged SFO save/campaign state used for the failed request session." -ForegroundColor Yellow
Write-Host "Remain on the campaign map for about 20 seconds. Do not end the turn, save, move an army, attack, or issue any order."
Write-Host "Then exit WH3 completely and run collect_campaign_feasibility_embedded_retry.ps1."

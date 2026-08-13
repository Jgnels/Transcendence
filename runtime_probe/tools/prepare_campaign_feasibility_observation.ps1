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

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Quote-ProcessArgument([string]$Value) {
    return '"' + $Value.Replace('"', '\"') + '"'
}

$MachineManifestPath = Join-Path $RepoRoot "local_inputs\machine_profiles\gaming_laptop_private.json"
if (-not (Test-Path -LiteralPath $MachineManifestPath -PathType Leaf)) { throw "Private machine manifest not found: $MachineManifestPath" }
$MachineManifest = Get-Content -LiteralPath $MachineManifestPath -Raw | ConvertFrom-Json
$GameRoot = [string]$MachineManifest.game.install_path
if (-not $GameRoot -or -not (Test-Path -LiteralPath $GameRoot -PathType Container)) { throw "WH3 installation path is missing or invalid in the private machine manifest." }
$GameData = Join-Path $GameRoot "data"
$ProbeName = "transcendence_campaign_feasibility_probe.pack"
$ProbePack = Join-Path $GameData $ProbeName

Write-Host ""
Write-Host "==> Building and installing the dedicated read-only campaign feasibility probe" -ForegroundColor Cyan
$PrepareLiveProbe = Join-Path $PSScriptRoot "prepare_live_probe.ps1"
$PrepareArguments = @{
    InstallCampaignFeasibility = $true
    Force = $true
    Confirm = $false
}
& $PrepareLiveProbe @PrepareArguments
if (-not (Test-Path -LiteralPath $ProbePack -PathType Leaf)) { throw "Installed feasibility probe not found: $ProbePack" }

Write-Host ""
Write-Host "SFO READ-ONLY FEASIBILITY SESSION SETUP" -ForegroundColor Yellow
Write-Host "In the WH3 launcher, enable exactly these two mods and disable every other mod:"
Write-Host "  1. SFO: Grimhammer III (Workshop item $SfoWorkshopId)"
Write-Host "  2. $ProbeName"
Write-Host "Close the launcher after applying that load order. Do not launch WH3 yet."
$Confirmation = (Read-Host "Type READY after the launcher shows only those two enabled mods").Trim()
if ($Confirmation -ine "READY") { throw "Campaign feasibility observation preparation cancelled." }

$Python = Get-PythonCommand
$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$SessionId = "campaign_feasibility_" + $Timestamp
$SessionsRoot = Join-Path $RepoRoot "local_inputs\runtime_probe\campaign_feasibility_sessions"
$SessionRoot = Join-Path $SessionsRoot $SessionId
New-Item -ItemType Directory -Force -Path $SessionRoot | Out-Null

$EnvironmentPrivate = Join-Path $SessionRoot "sfo_environment_private.json"
$EnvironmentPublic = Join-Path $SessionRoot "sfo_environment_attestation.json"
& $Python.Command @($Python.Prefix) (Join-Path $PSScriptRoot "capture_sfo_environment.py") `
    --game-root $GameRoot `
    --appdata-root $env:APPDATA `
    --shadow-pack $ProbePack `
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
if ($LASTEXITCODE -ne 0) { throw "SFO feasibility environment preflight failed with exit code $LASTEXITCODE." }

$RuntimeLog = Join-Path $GameRoot "transcendence_runtime_log.txt"
$RequestFile = Join-Path $GameRoot "transcendence_campaign_feasibility_request.txt"
$ArchiveRoot = Join-Path $RepoRoot "local_inputs\runtime_probe\runtime_log_archives"
New-Item -ItemType Directory -Force -Path $ArchiveRoot | Out-Null
if (Test-Path -LiteralPath $RuntimeLog -PathType Leaf) {
    $ArchivePath = Join-Path $ArchiveRoot ("transcendence_runtime_log_before_" + $Timestamp + ".txt")
    Copy-Item -LiteralPath $RuntimeLog -Destination $ArchivePath -Force
    Remove-Item -LiteralPath $RuntimeLog -Force
}
if (Test-Path -LiteralPath $RequestFile -PathType Leaf) {
    $RequestArchive = Join-Path $SessionRoot "previous_request_private.txt"
    Copy-Item -LiteralPath $RequestFile -Destination $RequestArchive -Force
    Remove-Item -LiteralPath $RequestFile -Force
}

$Status = Join-Path $SessionRoot "sidecar_status.json"
$StopFile = Join-Path $SessionRoot "stop_sidecar.request"
$SidecarStdout = Join-Path $SessionRoot "sidecar_stdout_private.log"
$SidecarStderr = Join-Path $SessionRoot "sidecar_stderr_private.log"
$SidecarScript = Join-Path $PSScriptRoot "watch_campaign_feasibility.py"
$Arguments = @()
foreach ($PrefixArgument in @($Python.Prefix)) { $Arguments += (Quote-ProcessArgument ([string]$PrefixArgument)) }
$Arguments += (Quote-ProcessArgument $SidecarScript)
$Arguments += '"--log"'; $Arguments += (Quote-ProcessArgument $RuntimeLog)
$Arguments += '"--request-file"'; $Arguments += (Quote-ProcessArgument $RequestFile)
$Arguments += '"--session-root"'; $Arguments += (Quote-ProcessArgument $SessionRoot)
$Arguments += '"--status"'; $Arguments += (Quote-ProcessArgument $Status)
$Arguments += '"--stop-file"'; $Arguments += (Quote-ProcessArgument $StopFile)
$Arguments += '"--poll-seconds"'; $Arguments += '"0.5"'
$Sidecar = Start-Process -FilePath $Python.Command -ArgumentList ($Arguments -join " ") -WindowStyle Hidden -RedirectStandardOutput $SidecarStdout -RedirectStandardError $SidecarStderr -PassThru

$Ready = $false
for ($Attempt = 0; $Attempt -lt 50; $Attempt++) {
    if (Test-Path -LiteralPath $Status -PathType Leaf) {
        try {
            $State = Get-Content -LiteralPath $Status -Raw | ConvertFrom-Json
            if ([string]$State.state -eq "WAITING_FOR_LOG") { $Ready = $true; break }
        } catch {}
    }
    $Sidecar.Refresh()
    if ($Sidecar.HasExited) { break }
    Start-Sleep -Milliseconds 200
}
if (-not $Ready) {
    if (-not $Sidecar.HasExited) { Stop-Process -Id $Sidecar.Id -Force -ErrorAction SilentlyContinue }
    $Details = if (Test-Path -LiteralPath $SidecarStderr) { (Get-Content -LiteralPath $SidecarStderr -Raw -ErrorAction SilentlyContinue).Trim() } else { "" }
    throw "Campaign feasibility sidecar did not initialize. $Details"
}

$Environment = Get-Content -LiteralPath $EnvironmentPublic -Raw | ConvertFrom-Json
$Manifest = [ordered]@{
    schema_version = 1
    session_kind = "SFO_CAMPAIGN_FEASIBILITY_READ_ONLY"
    session_id = $SessionId
    prepared_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    runtime_log = $RuntimeLog
    request_file = $RequestFile
    probe_name = $ProbeName
    probe_pack_sha256 = Get-Sha256 $ProbePack
    environment_private = $EnvironmentPrivate
    environment_public = $EnvironmentPublic
    environment_public_sha256 = Get-Sha256 $EnvironmentPublic
    sfo_pack_sha256 = [string]$Environment.sfo.pack_sha256
    wh3_executable_sha256 = [string]$Environment.game.executable_sha256
    sidecar_pid = $Sidecar.Id
    sidecar_status = $Status
    sidecar_stop_file = $StopFile
    sidecar_stdout_private = $SidecarStdout
    sidecar_stderr_private = $SidecarStderr
    active_mod_list_modified = $false
    orders_emitted = $false
    save_values_written = $false
}
$ManifestPath = Join-Path $SessionRoot "session_manifest_private.json"
$Manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ManifestPath -Encoding UTF8
New-Item -ItemType Directory -Force -Path $SessionsRoot | Out-Null
Copy-Item -LiteralPath $ManifestPath -Destination (Join-Path $SessionsRoot "latest.json") -Force

Write-Host ""
Write-Host "CAMPAIGN FEASIBILITY OBSERVATION READY" -ForegroundColor Green
Write-Host "Probe SHA-256: $($Manifest.probe_pack_sha256)"
Write-Host "SFO SHA-256: $($Manifest.sfo_pack_sha256)"
Write-Host "Session: $SessionId"
Write-Host ""
Write-Host "Now launch WH3, load a current SFO campaign, and remain on the campaign map." -ForegroundColor Yellow
Write-Host "The probe captures the loaded current state on first tick; you do NOT need to end the turn, save, move an army, or issue any order."
Write-Host "Give it about 20 seconds. If the current state yields a v0.2G force assignment, the exact v0.2H query packet runs automatically."
Write-Host "Then exit WH3 completely and run collect_campaign_feasibility_observation.ps1."

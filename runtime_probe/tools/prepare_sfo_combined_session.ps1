[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [switch]$SkipProbeInstall,
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

function Quote-ProcessArgument([string]$Value) {
    return '"' + $Value.Replace('"', '\"') + '"'
}

$MachineManifestPath = Join-Path $RepoRoot "local_inputs\machine_profiles\gaming_laptop_private.json"
if (-not (Test-Path -LiteralPath $MachineManifestPath -PathType Leaf)) {
    throw "Private machine manifest not found: $MachineManifestPath"
}
$MachineManifest = Get-Content -LiteralPath $MachineManifestPath -Raw | ConvertFrom-Json
$GameRoot = [string]$MachineManifest.game.install_path
if (-not $GameRoot -or -not (Test-Path -LiteralPath $GameRoot -PathType Container)) {
    throw "WH3 installation path is missing or invalid in the private machine manifest."
}
$GameData = Join-Path $GameRoot "data"
$ShadowPack = Join-Path $GameData "transcendence_shadow_probe.pack"

# A Python launcher may have left the real read-only watcher alive after an older
# preparation failed before session_manifest_private.json was written. Stop only
# those incomplete preparation sessions; never touch a canonical active session.
$ExistingSessionsRoot = Join-Path $RepoRoot "local_inputs\runtime_probe\sessions"
if (Test-Path -LiteralPath $ExistingSessionsRoot -PathType Container) {
    foreach ($PriorSession in @(Get-ChildItem -LiteralPath $ExistingSessionsRoot -Directory -Filter "sfo_combined_*" -ErrorAction SilentlyContinue)) {
        $PriorManifest = Join-Path $PriorSession.FullName "session_manifest_private.json"
        $PriorCheckpointManifest = Join-Path $PriorSession.FullName "checkpoint_manifest_private.json"
        $PriorStatus = Join-Path $PriorSession.FullName "watcher_status.json"
        $PriorStop = Join-Path $PriorSession.FullName "stop_watcher.request"
        if (-not (Test-Path -LiteralPath $PriorManifest -PathType Leaf)) {
            try {
                $PriorControl = $null
                foreach ($Candidate in @($PriorCheckpointManifest, $PriorStatus)) {
                    if (Test-Path -LiteralPath $Candidate -PathType Leaf) {
                        try {
                            $CandidateState = Get-Content -LiteralPath $Candidate -Raw | ConvertFrom-Json
                            if ([string]$CandidateState.state -in @("WAITING_FOR_LOG", "WATCHING", "STOPPED", "FAILED")) {
                                $PriorControl = $Candidate
                                $PriorState = $CandidateState
                                break
                            }
                        } catch {}
                    }
                }
                if ($PriorControl -and [string]$PriorState.state -in @("WAITING_FOR_LOG", "WATCHING")) {
                    New-Item -ItemType File -Force -Path $PriorStop | Out-Null
                    for ($PriorAttempt = 0; $PriorAttempt -lt 25; $PriorAttempt++) {
                        Start-Sleep -Milliseconds 200
                        foreach ($Candidate in @($PriorCheckpointManifest, $PriorStatus)) {
                            if (-not (Test-Path -LiteralPath $Candidate -PathType Leaf)) { continue }
                            try {
                                $CandidateState = Get-Content -LiteralPath $Candidate -Raw | ConvertFrom-Json
                                if ([string]$CandidateState.state -in @("STOPPED", "FAILED")) {
                                    $PriorState = $CandidateState
                                    break
                                }
                            } catch {}
                        }
                        if ([string]$PriorState.state -in @("STOPPED", "FAILED")) { break }
                    }
                }
            } catch {
                Write-Host "Warning: could not confirm cleanup of incomplete watcher session $($PriorSession.Name)." -ForegroundColor Yellow
            }
        }
    }
}

if (-not $SkipProbeInstall) {
    Write-Host "" 
    Write-Host "==> Building, validating, and installing the read-only combined shadow probe" -ForegroundColor Cyan
    $PrepareLiveProbe = Join-Path $PSScriptRoot "prepare_live_probe.ps1"
    $PrepareLiveProbeParameters = @{
        InstallShadow = $true
        Force = $true
        Confirm = $false
    }
    & $PrepareLiveProbe @PrepareLiveProbeParameters
    if (-not $?) { throw "Shadow-probe installation failed." }
}
if (-not (Test-Path -LiteralPath $ShadowPack -PathType Leaf)) {
    throw "Installed shadow probe not found: $ShadowPack"
}

Write-Host ""
Write-Host "SFO SESSION MOD SETUP REQUIRED" -ForegroundColor Yellow
Write-Host "In the WH3 launcher, enable exactly these two mods and disable every other mod:"
Write-Host "  1. SFO: Grimhammer III (Workshop item $SfoWorkshopId)"
Write-Host "  2. transcendence_shadow_probe.pack"
Write-Host "Close the launcher after applying that load order. Do not launch WH3 yet."
$Confirmation = (Read-Host "Type READY after the launcher shows only those two enabled mods").Trim()
if ($Confirmation -ine "READY") { throw "SFO combined-session preparation cancelled." }

$Python = Get-PythonCommand
$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$SessionId = "sfo_combined_" + $Timestamp
$SessionRoot = Join-Path $RepoRoot ("local_inputs\runtime_probe\sessions\" + $SessionId)
$CheckpointRoot = Join-Path $SessionRoot "checkpoints"
$EnvironmentPrivate = Join-Path $SessionRoot "sfo_environment_private.json"
$EnvironmentPublic = Join-Path $SessionRoot "sfo_environment_attestation.json"
$WatcherStatus = Join-Path $SessionRoot "watcher_status.json"
$CheckpointManifest = Join-Path $SessionRoot "checkpoint_manifest_private.json"
$StopFile = Join-Path $SessionRoot "stop_watcher.request"
New-Item -ItemType Directory -Force -Path $SessionRoot, $CheckpointRoot | Out-Null

& $Python.Command @($Python.Prefix) `
    (Join-Path $PSScriptRoot "capture_sfo_environment.py") `
    --game-root $GameRoot `
    --appdata-root $env:APPDATA `
    --shadow-pack $ShadowPack `
    --sfo-workshop-id $SfoWorkshopId `
    --campaign-difficulty $CampaignDifficulty `
    --battle-difficulty $BattleDifficulty `
    --ironman $Ironman.ToString().ToLowerInvariant() `
    --battle-realism $BattleRealism.ToString().ToLowerInvariant() `
    --battlefield-limitations $BattlefieldLimitations `
    --faction $Faction `
    --private-output $EnvironmentPrivate `
    --public-output $EnvironmentPublic
if ($LASTEXITCODE -ne 0) { throw "SFO environment preflight failed with exit code $LASTEXITCODE." }

$RuntimeLog = Join-Path $GameRoot "transcendence_runtime_log.txt"
$ArchiveRoot = Join-Path $RepoRoot "local_inputs\runtime_probe\runtime_log_archives"
New-Item -ItemType Directory -Force -Path $ArchiveRoot | Out-Null
$Archived = $null
if (Test-Path -LiteralPath $RuntimeLog -PathType Leaf) {
    $ArchivePath = Join-Path $ArchiveRoot ("transcendence_runtime_log_before_" + $Timestamp + ".txt")
    Copy-Item -LiteralPath $RuntimeLog -Destination $ArchivePath -Force
    $Archived = [ordered]@{
        path = $ArchivePath
        size_bytes = [int64](Get-Item -LiteralPath $ArchivePath).Length
        sha256 = Get-Sha256 $ArchivePath
    }
    Remove-Item -LiteralPath $RuntimeLog -Force
}

$WatcherScript = Join-Path $PSScriptRoot "watch_combined_runtime_log.py"
$WatcherStdout = Join-Path $SessionRoot "watcher_stdout_private.log"
$WatcherStderr = Join-Path $SessionRoot "watcher_stderr_private.log"
$NonceBytes = New-Object byte[] 32
$Random = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try { $Random.GetBytes($NonceBytes) } finally { $Random.Dispose() }
$WatcherHandshakeToken = -join ($NonceBytes | ForEach-Object { $_.ToString("x2") })

$WatcherArguments = @()
foreach ($PrefixArgument in @($Python.Prefix)) {
    $WatcherArguments += (Quote-ProcessArgument ([string]$PrefixArgument))
}
$WatcherArguments += (Quote-ProcessArgument $WatcherScript)
$WatcherArguments += '"--log"'
$WatcherArguments += (Quote-ProcessArgument $RuntimeLog)
$WatcherArguments += '"--checkpoint-root"'
$WatcherArguments += (Quote-ProcessArgument $CheckpointRoot)
$WatcherArguments += '"--stop-file"'
$WatcherArguments += (Quote-ProcessArgument $StopFile)
$WatcherArguments += '"--status"'
$WatcherArguments += (Quote-ProcessArgument $WatcherStatus)
$WatcherArguments += '"--manifest"'
$WatcherArguments += (Quote-ProcessArgument $CheckpointManifest)
$WatcherArguments += '"--poll-seconds"'
$WatcherArguments += '"2"'
$WatcherArguments += '"--interval-seconds"'
$WatcherArguments += '"15"'
$WatcherArguments += '"--growth-bytes"'
$WatcherArguments += '"1000000"'
$WatcherArguments += '"--handshake-token"'
$WatcherArguments += (Quote-ProcessArgument $WatcherHandshakeToken)
$Watcher = Start-Process -FilePath $Python.Command `
    -ArgumentList ($WatcherArguments -join " ") `
    -WindowStyle Hidden `
    -RedirectStandardOutput $WatcherStdout `
    -RedirectStandardError $WatcherStderr `
    -PassThru

$WatcherReady = $false
$WatcherRuntimePid = $null
for ($Attempt = 0; $Attempt -lt 100; $Attempt++) {
    # The checkpoint manifest is authoritative. watcher_status.json remains a
    # redundant human-readable diagnostic and may be absent or unreadable.
    if (Test-Path -LiteralPath $CheckpointManifest -PathType Leaf) {
        try {
            $WatcherState = Get-Content -LiteralPath $CheckpointManifest -Raw | ConvertFrom-Json
            if (
                [int]$WatcherState.schema_version -eq 2 -and
                [string]$WatcherState.handshake_token -ceq $WatcherHandshakeToken -and
                [string]$WatcherState.state -in @("WAITING_FOR_LOG", "WATCHING")
            ) {
                $WatcherRuntimePid = [int]$WatcherState.pid
                $WatcherReady = $true
                break
            }
        } catch {
            # Atomic replacement can briefly race indexing or antivirus; retry.
        }
    }
    $Watcher.Refresh()
    if ($Watcher.HasExited -and $Watcher.ExitCode -ne 0) { break }
    Start-Sleep -Milliseconds 200
}
if (-not $WatcherReady) {
    try {
        if ($WatcherRuntimePid) { Stop-Process -Id $WatcherRuntimePid -Force -ErrorAction SilentlyContinue }
        $Watcher.Refresh()
        if (-not $Watcher.HasExited) { Stop-Process -Id $Watcher.Id -Force -ErrorAction SilentlyContinue }
    } catch {}
    $StartupDetails = @()
    if (Test-Path -LiteralPath $WatcherStderr -PathType Leaf) {
        $ErrorText = (Get-Content -LiteralPath $WatcherStderr -Raw -ErrorAction SilentlyContinue).Trim()
        if ($ErrorText) { $StartupDetails += "stderr: $ErrorText" }
    }
    if (Test-Path -LiteralPath $WatcherStdout -PathType Leaf) {
        $OutputText = (Get-Content -LiteralPath $WatcherStdout -Raw -ErrorAction SilentlyContinue).Trim()
        if ($OutputText) { $StartupDetails += "stdout: $OutputText" }
    }
    $Watcher.Refresh()
    if ($Watcher.HasExited) { $StartupDetails += "launcher_exit_code: $($Watcher.ExitCode)" }
    $DetailSuffix = if ($StartupDetails.Count -gt 0) { " " + ($StartupDetails -join " | ") } else { " Private diagnostics: $WatcherStderr and $WatcherStdout" }
    throw ("The append-log checkpoint watcher did not initialize." + $DetailSuffix)
}

$Environment = Get-Content -LiteralPath $EnvironmentPublic -Raw | ConvertFrom-Json
if ([string]$Environment.probe_binding.status -eq "DEFERRED_RUNTIME_MARKER") {
    Write-Host ""
    Write-Host "PRELAUNCH PROBE ENTRY DEFERRED" -ForegroundColor Yellow
    Write-Host "The launcher-state file contains only the exact SFO entry before WH3 starts."
    Write-Host "The installed probe hash is preserved, but this session will certify probe loading only from exact runtime markers."
    Write-Host "If the probe was not actually enabled, collection will fail closed and make no compatibility claim."
}
$SessionManifest = [ordered]@{
    schema_version = 2
    session_kind = "SFO_COMBINED_CAMPAIGN_BATTLE"
    session_id = $SessionId
    prepared_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    runtime_log = $RuntimeLog
    runtime_log_cleared = (-not (Test-Path -LiteralPath $RuntimeLog))
    previous_runtime_log = $Archived
    staged_shadow_pack_sha256 = Get-Sha256 (Join-Path $RepoRoot "local_inputs\runtime_probe\staged\transcendence_shadow_probe.pack")
    installed_shadow_pack_sha256 = Get-Sha256 $ShadowPack
    environment_profile_private = $EnvironmentPrivate
    environment_profile_public = $EnvironmentPublic
    environment_profile_public_sha256 = Get-Sha256 $EnvironmentPublic
    sfo_pack_sha256 = [string]$Environment.sfo.pack_sha256
    sfo_workshop_id = [string]$Environment.sfo.workshop_id
    checkpoint_root = $CheckpointRoot
    checkpoint_manifest = $CheckpointManifest
    watcher_status = $WatcherStatus
    watcher_stop_file = $StopFile
    watcher_launcher_pid = $Watcher.Id
    watcher_runtime_pid = $WatcherRuntimePid
    watcher_handshake_token = $WatcherHandshakeToken
    watcher_stdout_private = $WatcherStdout
    watcher_stderr_private = $WatcherStderr
    active_mod_list_modified = $false
    wh3_save_modified = $false
    expected_runtime_markers = @(
        "TRANS_PROBE|1|RUNTIME_BEGIN|probe_kind=shadow|runtime=campaign",
        "TRANS_BATTLE|2|RUNTIME_BEGIN|probe_kind=battle_replay_shadow|runtime=battle"
    )
}
$LatestSessionRoot = Join-Path $RepoRoot "local_inputs\runtime_probe\sessions"
$ManifestPath = Join-Path $SessionRoot "session_manifest_private.json"
$SessionManifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $ManifestPath -Encoding UTF8
Copy-Item -LiteralPath $ManifestPath -Destination (Join-Path $LatestSessionRoot "latest.json") -Force

Write-Host ""
Write-Host "SFO COMBINED SESSION READY" -ForegroundColor Green
Write-Host "Exact SFO pack SHA-256: $($Environment.sfo.pack_sha256)"
Write-Host "Exact WH3 executable SHA-256: $($Environment.game.executable_sha256)"
Write-Host "Shadow probe SHA-256: $($SessionManifest.installed_shadow_pack_sha256)"
Write-Host "Checkpoint watcher PID: $WatcherRuntimePid"
Write-Host "Session manifest: $ManifestPath"
Write-Host ""
Write-Host "Launch WH3 once and remain in the same game process." -ForegroundColor Yellow
Write-Host "Play through at least five local-faction turn starts and manually fight two campaign battles."
Write-Host "Return fully to the campaign map after each battle. You do not need to save and quit after battles."
Write-Host "After the final return to campaign, exit WH3 completely and run collect_sfo_combined_session.ps1."

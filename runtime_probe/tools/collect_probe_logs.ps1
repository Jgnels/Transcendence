[CmdletBinding()]
param(
    [string[]]$LogPaths = @(),
    [ValidateSet("generic", "observer", "shadow", "campaign_shadow", "campaign_battle", "persistence_write", "persistence_reload")]
    [string]$EvidencePhase = "generic"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$MachineManifestPath = Join-Path $RepoRoot "local_inputs\machine_profiles\gaming_laptop_private.json"
if (-not (Test-Path -LiteralPath $MachineManifestPath)) {
    throw "Private machine manifest not found: $MachineManifestPath"
}
$MachineManifest = Get-Content -LiteralPath $MachineManifestPath -Raw | ConvertFrom-Json
$GameRoot = [string]$MachineManifest.game.install_path

$CombinedSessionRecord = $null
if ($LogPaths.Count -eq 0) {
    $UseCombinedRuntimeLog = $EvidencePhase -in @(
        "shadow",
        "campaign_shadow",
        "campaign_battle"
    )
    $CombinedRuntimeLog = Join-Path $GameRoot "transcendence_runtime_log.txt"
    $LegacyModLog = Join-Path $GameRoot "lua_mod_log.txt"

    if ($EvidencePhase -eq "campaign_battle") {
        $SessionManifestPath = Join-Path $RepoRoot "local_inputs\runtime_probe\sessions\latest.json"
        if (-not (Test-Path -LiteralPath $SessionManifestPath -PathType Leaf)) {
            throw "Combined-session manifest missing. Run prepare_combined_session.ps1 before WH3."
        }
        $SessionManifest = Get-Content -LiteralPath $SessionManifestPath -Raw | ConvertFrom-Json
        $PreparedAt = [DateTimeOffset]::Parse([string]$SessionManifest.prepared_at_utc).UtcDateTime
        if (-not (Test-Path -LiteralPath $CombinedRuntimeLog -PathType Leaf)) {
            throw "The required append-only combined runtime log was not created: $CombinedRuntimeLog"
        }
        $RuntimeInfo = Get-Item -LiteralPath $CombinedRuntimeLog
        if ($RuntimeInfo.LastWriteTimeUtc -lt $PreparedAt) {
            throw "The combined runtime log predates the prepared session and is stale."
        }
        $LogPaths = @($CombinedRuntimeLog)
        $CombinedSessionRecord = [ordered]@{
            private_copy = $SessionManifestPath
            sha256 = Get-Sha256 $SessionManifestPath
            prepared_at_utc = [string]$SessionManifest.prepared_at_utc
            expected_runtime_log = [string]$SessionManifest.runtime_log
            staged_shadow_pack_sha256 = [string]$SessionManifest.staged_shadow_pack_sha256
            installed_shadow_pack_sha256 = [string]$SessionManifest.installed_shadow_pack_sha256
        }
    }
    elseif ($UseCombinedRuntimeLog -and (Test-Path -LiteralPath $CombinedRuntimeLog -PathType Leaf)) {
        $LogPaths = @($CombinedRuntimeLog)
    }
    elseif (Test-Path -LiteralPath $LegacyModLog -PathType Leaf) {
        $LogPaths = @($LegacyModLog)
    }
    else {
        throw "No Transcendence runtime log was found. Expected $CombinedRuntimeLog or $LegacyModLog."
    }
}

$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$EvidenceRoot = Join-Path $RepoRoot ("local_inputs\logs\wh3\probe_" + $Timestamp)
New-Item -ItemType Directory -Force -Path $EvidenceRoot | Out-Null

if ($null -ne $CombinedSessionRecord) {
    $SessionEvidencePath = Join-Path $EvidenceRoot "combined_session_manifest.json"
    Copy-Item -LiteralPath ([string]$CombinedSessionRecord.private_copy) -Destination $SessionEvidencePath -Force
    $CombinedSessionRecord.private_copy = $SessionEvidencePath
    $CombinedSessionRecord.sha256 = Get-Sha256 $SessionEvidencePath
}

$Copied = @()
foreach ($SourcePath in $LogPaths) {
    $Resolved = (Resolve-Path -LiteralPath $SourcePath).Path
    $Name = [IO.Path]::GetFileName($Resolved)
    $Destination = Join-Path $EvidenceRoot $Name
    if (Test-Path -LiteralPath $Destination) {
        $Destination = Join-Path $EvidenceRoot (([IO.Path]::GetFileNameWithoutExtension($Name)) + "_" + $Copied.Count + ([IO.Path]::GetExtension($Name)))
    }
    Copy-Item -LiteralPath $Resolved -Destination $Destination -Force
    $Copied += [ordered]@{
        source = $Resolved
        private_copy = $Destination
        size_bytes = [int64](Get-Item -LiteralPath $Destination).Length
        sha256 = Get-Sha256 $Destination
    }
}

$LoadedProbeKinds = @()
foreach ($LogRecord in $Copied) {
    $Text = Get-Content -LiteralPath $LogRecord.private_copy -Raw
    $Matches = [regex]::Matches(
        $Text,
        'TRANS_PROBE\|1\|PACK_LOADED\|probe_kind=([^|\r\n]+)'
    )
    foreach ($Match in $Matches) {
        $Kind = [string]$Match.Groups[1].Value
        if ($LoadedProbeKinds -notcontains $Kind) {
            $LoadedProbeKinds += $Kind
        }
    }
}
$LoadedProbeKinds = @($LoadedProbeKinds | Sort-Object)

$BattleProbeLoaded = $false
foreach ($LogRecord in $Copied) {
    $Text = Get-Content -LiteralPath $LogRecord.private_copy -Raw
    if ($Text -match 'TRANS_BATTLE\|1\|PACK_LOADED\|probe_kind=(battle_shadow|battle_replay_shadow)') {
        $BattleProbeLoaded = $true
        break
    }
}

$ExpectedLoadedKinds = @()
if ($EvidencePhase -eq "observer") {
    $ExpectedLoadedKinds = @("observer")
}
elseif ($EvidencePhase -in @("shadow", "campaign_shadow", "campaign_battle")) {
    $ExpectedLoadedKinds = @("shadow")
}
elseif ($EvidencePhase -in @("persistence_write", "persistence_reload")) {
    $ExpectedLoadedKinds = @("persistence")
}
$UnexpectedLoadedKinds = @(
    $LoadedProbeKinds | Where-Object { $ExpectedLoadedKinds.Count -gt 0 -and $ExpectedLoadedKinds -notcontains $_ }
)

$UsedMods = Join-Path $env:APPDATA "The Creative Assembly\Warhammer3\scripts\used_mods.txt"
$UsedModsRecord = $null
if (Test-Path -LiteralPath $UsedMods -PathType Leaf) {
    $UsedModsDestination = Join-Path $EvidenceRoot "used_mods.txt"
    Copy-Item -LiteralPath $UsedMods -Destination $UsedModsDestination -Force
    $UsedModsRecord = [ordered]@{
        private_copy = $UsedModsDestination
        size_bytes = [int64](Get-Item -LiteralPath $UsedModsDestination).Length
        sha256 = Get-Sha256 $UsedModsDestination
    }
}

$InstalledProbePacks = @()
foreach ($PackName in @(
    "transcendence_observer_probe.pack",
    "transcendence_persistence_probe.pack",
    "transcendence_shadow_probe.pack"
)) {
    $InstalledPath = Join-Path (Join-Path $GameRoot "data") $PackName
    if (Test-Path -LiteralPath $InstalledPath -PathType Leaf) {
        $StagedPath = Join-Path $RepoRoot ("local_inputs\runtime_probe\staged\" + $PackName)
        $StagedSha = $null
        if (Test-Path -LiteralPath $StagedPath -PathType Leaf) {
            $StagedSha = Get-Sha256 $StagedPath
        }
        $InstalledSha = Get-Sha256 $InstalledPath
        $InstalledProbePacks += [ordered]@{
            name = $PackName
            installed_sha256 = $InstalledSha
            staged_sha256 = $StagedSha
            matches_staged = ($null -ne $StagedSha -and $InstalledSha -eq $StagedSha)
            loaded_in_log = (
                ($PackName -eq "transcendence_observer_probe.pack" -and $LoadedProbeKinds -contains "observer") -or
                ($PackName -eq "transcendence_persistence_probe.pack" -and $LoadedProbeKinds -contains "persistence") -or
                ($PackName -eq "transcendence_shadow_probe.pack" -and $LoadedProbeKinds -contains "shadow")
            )
            size_bytes = [int64](Get-Item -LiteralPath $InstalledPath).Length
        }
    }
}

$LatestInstallRecord = $null
$LatestInstallManifest = Join-Path $RepoRoot "local_inputs\runtime_probe\installations\latest.json"
if (Test-Path -LiteralPath $LatestInstallManifest -PathType Leaf) {
    $LatestInstallRecord = [ordered]@{
        private_copy = $LatestInstallManifest
        sha256 = Get-Sha256 $LatestInstallManifest
    }
}

$Python = Get-Command python -ErrorAction SilentlyContinue
$PythonArgs = @()
if (-not $Python) {
    $Python = Get-Command py -ErrorAction SilentlyContinue
    if ($Python) { $PythonArgs = @("-3") }
}
if (-not $Python) {
    throw "Python 3 was not found."
}

$CopiedPaths = @($Copied | ForEach-Object { $_.private_copy })
$SummaryPath = Join-Path $EvidenceRoot "probe_summary.json"
& $Python.Source @PythonArgs `
    (Join-Path $RepoRoot "runtime_probe\tools\parse_probe_log.py") `
    @CopiedPaths `
    --output $SummaryPath
if ($LASTEXITCODE -ne 0) {
    throw "Probe log parsing failed with exit code $LASTEXITCODE."
}

$EvidenceManifest = [ordered]@{
    schema_version = 4
    collected_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    evidence_phase = $EvidencePhase
    loaded_probe_kinds = $LoadedProbeKinds
    expected_loaded_probe_kinds = $ExpectedLoadedKinds
    unexpected_loaded_probe_kinds = $UnexpectedLoadedKinds
    battle_probe_loaded = $BattleProbeLoaded
    logs = $Copied
    installed_probe_packs = $InstalledProbePacks
    used_mods = $UsedModsRecord
    latest_install_manifest = $LatestInstallRecord
    combined_session_manifest = $CombinedSessionRecord
    summary = [ordered]@{
        path = $SummaryPath
        sha256 = Get-Sha256 $SummaryPath
    }
}
$EvidenceManifestPath = Join-Path $EvidenceRoot "evidence_manifest.json"
$EvidenceManifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $EvidenceManifestPath -Encoding UTF8

if ($EvidencePhase -in @("persistence_write", "persistence_reload")) {
    $RoundTripRoot = Join-Path $RepoRoot "local_inputs\runtime_probe\persistence_roundtrip"
    New-Item -ItemType Directory -Force -Path $RoundTripRoot | Out-Null
    $StateName = if ($EvidencePhase -eq "persistence_write") { "write.json" } else { "reload.json" }
    $PhaseState = [ordered]@{
        schema_version = 1
        phase = $EvidencePhase
        collected_at_utc = $EvidenceManifest.collected_at_utc
        evidence_root = $EvidenceRoot
        log_path = [string]$Copied[0].private_copy
        evidence_manifest_path = $EvidenceManifestPath
        summary_path = $SummaryPath
    }
    $PhaseState | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $RoundTripRoot $StateName) -Encoding UTF8
}

Write-Host "Probe evidence collected and parsed." -ForegroundColor Green
Write-Host "Evidence folder: $EvidenceRoot"
Write-Host "Summary: $SummaryPath"

[CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact="High")]
param(
    [switch]$InstallObserver,
    [switch]$InstallPersistence,
    [switch]$InstallShadow,
    [switch]$InstallBattleReplay,
    [switch]$InstallCampaignFeasibility,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Confirm-Explicit([string]$Message) {
    if ($Force) { return $true }
    $answer = Read-Host "$Message Type YES to continue"
    return $answer -ceq "YES"
}

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$LocalRoot = Join-Path $RepoRoot "local_inputs\runtime_probe"
$StageRoot = Join-Path $LocalRoot "staged"
$InstallRoot = Join-Path $LocalRoot "installations"
New-Item -ItemType Directory -Force -Path $StageRoot, $InstallRoot | Out-Null

Write-Host "Building and testing deterministic probe packs..." -ForegroundColor Cyan
& powershell.exe -NoProfile -ExecutionPolicy Bypass `
    -File (Join-Path $PSScriptRoot "build.ps1")
if ($LASTEXITCODE -ne 0) {
    throw "Probe build failed with exit code $LASTEXITCODE."
}

$DistRoot = Join-Path $RepoRoot "dist\runtime_probe"
$BuildManifest = Join-Path $DistRoot "probe_build_manifest.json"
if (-not (Test-Path -LiteralPath $BuildManifest)) {
    throw "Build manifest not found: $BuildManifest"
}
$BuildData = Get-Content -LiteralPath $BuildManifest -Raw | ConvertFrom-Json
$ObserverBuilds = @($BuildData.packs | Where-Object { $_.probe_kind -eq "observer" })
$PersistenceBuilds = @($BuildData.packs | Where-Object { $_.probe_kind -eq "persistence" })
$ShadowBuilds = @($BuildData.packs | Where-Object { $_.probe_kind -eq "shadow" })
$BattleReplayBuilds = @($BuildData.packs | Where-Object { $_.probe_kind -eq "battle_replay" })
$CampaignFeasibilityBuilds = @($BuildData.packs | Where-Object { $_.probe_kind -eq "campaign_feasibility" })
if ($ObserverBuilds.Count -ne 1) {
    throw "Expected exactly one observer pack in the build manifest."
}
if ($PersistenceBuilds.Count -ne 1) {
    throw "Expected exactly one persistence pack in the build manifest."
}
if ($ShadowBuilds.Count -ne 1) {
    throw "Expected exactly one shadow pack in the build manifest."
}
if ($BattleReplayBuilds.Count -ne 1) {
    throw "Expected exactly one battle replay pack in the build manifest."
}
if ($CampaignFeasibilityBuilds.Count -ne 1) {
    throw "Expected exactly one campaign feasibility pack in the build manifest."
}
$ObserverBuild = $ObserverBuilds[0]
$PersistenceBuild = $PersistenceBuilds[0]
$ShadowBuild = $ShadowBuilds[0]
$BattleReplayBuild = $BattleReplayBuilds[0]
$CampaignFeasibilityBuild = $CampaignFeasibilityBuilds[0]

Get-ChildItem -LiteralPath $DistRoot -File | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $StageRoot $_.Name) -Force
}
Write-Host "Staged probe artifacts under $StageRoot" -ForegroundColor Green
Write-Host "Observer pack SHA-256: $($ObserverBuild.pack_sha256)" -ForegroundColor Green
Write-Host "Persistence pack SHA-256: $($PersistenceBuild.pack_sha256)" -ForegroundColor Green
Write-Host "Shadow pack SHA-256: $($ShadowBuild.pack_sha256)" -ForegroundColor Green
Write-Host "Battle replay pack SHA-256: $($BattleReplayBuild.pack_sha256)" -ForegroundColor Green
Write-Host "Campaign feasibility pack SHA-256: $($CampaignFeasibilityBuild.pack_sha256)" -ForegroundColor Green

if (-not $InstallObserver -and -not $InstallPersistence -and -not $InstallShadow -and -not $InstallBattleReplay -and -not $InstallCampaignFeasibility) {
    Write-Host "No game files were modified." -ForegroundColor Green
    Write-Host "To install a read-only probe, rerun with -InstallObserver, -InstallShadow, or -InstallBattleReplay."
    exit 0
}

$MachineManifestPath = Join-Path $RepoRoot "local_inputs\machine_profiles\gaming_laptop_private.json"
if (-not (Test-Path -LiteralPath $MachineManifestPath)) {
    throw "Private machine manifest not found: $MachineManifestPath"
}
$MachineManifest = Get-Content -LiteralPath $MachineManifestPath -Raw | ConvertFrom-Json
$GameRoot = [string]$MachineManifest.game.install_path
if (-not $GameRoot -or -not (Test-Path -LiteralPath $GameRoot -PathType Container)) {
    throw "WH3 installation path is missing or invalid in the private machine manifest."
}
$GameData = Join-Path $GameRoot "data"
if (-not (Test-Path -LiteralPath $GameData -PathType Container)) {
    throw "WH3 data directory not found: $GameData"
}

$Requested = @()
if ($InstallObserver) {
    $Requested += [pscustomobject]@{
        Name = "transcendence_observer_probe.pack"
        SaveMutation = $false
        Warning = "This pack is read-only and writes structured records to lua_mod_log.txt."
    }
}
if ($InstallPersistence) {
    $Requested += [pscustomobject]@{
        Name = "transcendence_persistence_probe.pack"
        SaveMutation = $true
        Warning = "This optional pack writes one project-owned integer to any save loaded while it is enabled."
    }
}
if ($InstallShadow) {
    $Requested += [pscustomobject]@{
        Name = "transcendence_shadow_probe.pack"
        SaveMutation = $false
        Warning = "This read-only pack records bounded shadow-planning inputs and never issues orders."
    }
}

if ($InstallBattleReplay) {
    $Requested += [pscustomobject]@{
        Name = "transcendence_battle_replay_probe.pack"
        SaveMutation = $false
        Warning = "This read-only battle-only pack records dense replay telemetry and never issues orders."
    }
}

if ($InstallCampaignFeasibility) {
    $Requested += [pscustomobject]@{
        Name = "transcendence_campaign_feasibility_probe.pack"
        SaveMutation = $false
        Warning = "This read-only campaign pack records observer-safe state and executes only whitelisted v0.2H query surfaces; it never issues orders."
    }
}

if ($InstallPersistence -and -not (Confirm-Explicit "The persistence probe writes one inert project value into the loaded save.")) {
    throw "Persistence installation cancelled."
}
if (-not (Confirm-Explicit "Copy the requested probe pack(s) into the WH3 data folder. The script will not enable them in the launcher.")) {
    throw "Installation cancelled."
}

$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$BackupRoot = Join-Path $LocalRoot ("backups\" + $Timestamp)
New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
$Records = @()

foreach ($Item in $Requested) {
    $Source = Join-Path $StageRoot $Item.Name
    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
        throw "Staged pack missing: $Source"
    }
    $Destination = Join-Path $GameData $Item.Name
    $BackupPath = $null
    $OriginalSha = $null

    if (Test-Path -LiteralPath $Destination -PathType Leaf) {
        $OriginalSha = Get-Sha256 $Destination
        $BackupPath = Join-Path $BackupRoot $Item.Name
        Copy-Item -LiteralPath $Destination -Destination $BackupPath -Force
    }

    if ($PSCmdlet.ShouldProcess($Destination, "Install $($Item.Name)")) {
        Copy-Item -LiteralPath $Source -Destination $Destination -Force
    }
    $InstalledSha = Get-Sha256 $Destination
    $SourceSha = Get-Sha256 $Source
    if ($InstalledSha -ne $SourceSha) {
        throw "Installed hash mismatch for $($Item.Name)."
    }

    $Records += [ordered]@{
        name = $Item.Name
        destination = $Destination
        source_sha256 = $SourceSha
        installed_sha256 = $InstalledSha
        save_mutation = [bool]$Item.SaveMutation
        warning = $Item.Warning
        previous_sha256 = $OriginalSha
        backup_path = $BackupPath
    }
}

$NextSteps = @("Open the WH3 launcher mod manager.")
if ($InstallPersistence) {
    $NextSteps += @(
        "Enable only transcendence_persistence_probe.pack.",
        "Use a disposable fresh pure-vanilla Karl Franz campaign.",
        "Reach first tick, manually save, exit, and run runtime_probe\\tools\\collect_persistence_phase.ps1 -Phase Write.",
        "Restart WH3, load that exact save, reach first tick, exit, and run runtime_probe\\tools\\collect_persistence_phase.ps1 -Phase Reload.",
        "Do not open a valued save while the persistence pack is enabled."
    )
}
elseif ($InstallCampaignFeasibility) {
    $NextSteps += @(
        "Enable exactly SFO: Grimhammer III plus transcendence_campaign_feasibility_probe.pack for the dedicated read-only observation.",
        "Run runtime_probe\tools\prepare_campaign_feasibility_observation.ps1 before launching WH3.",
        "Load a current campaign and remain on the campaign map; no turn advance or manual order is required for the first-tick capture.",
        "Exit WH3 after the capture completes, then run runtime_probe\tools\collect_campaign_feasibility_observation.ps1."
    )
}
elseif ($InstallBattleReplay) {
    $NextSteps += @(
        "Disable the observer, persistence, and combined shadow probes.",
        "Enable only transcendence_battle_replay_probe.pack.",
        "Open the preserved Battle of Eilhart replay and let it finish.",
        "Use the v0.1K dense replay capture watcher before launching WH3.",
        "This pack is read-only and cannot issue orders or modify saves."
    )
}
elseif ($InstallShadow) {
    $NextSteps += @(
        "Disable the observer and persistence probes.",
        "Enable only transcendence_shadow_probe.pack.",
        "Start a new pure-vanilla Karl Franz Immortal Empires campaign.",
        "Play through at least five consecutive local-faction turn starts.",
        "Manually fight at least one ordinary campaign battle; a field battle is preferred.",
        "Exit WH3 and run runtime_probe\\tools\\collect_campaign_battle.ps1.",
        "Upload the single ZIP created under local_inputs\\runtime_probe\\exports."
    )
}
elseif ($InstallObserver) {
    $NextSteps += @(
        "Enable only transcendence_observer_probe.pack.",
        "Start a new pure-vanilla Karl Franz Immortal Empires campaign and reach local-faction turn start.",
        "Exit WH3 and run runtime_probe\\tools\\collect_probe_logs.ps1 -EvidencePhase observer."
    )
}

$InstallManifest = [ordered]@{
    schema_version = 2
    installed_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    game_root = $GameRoot
    active_mod_list_modified = $false
    packs = $Records
    next_steps = $NextSteps
}
$ManifestPath = Join-Path $InstallRoot ("install_" + $Timestamp + ".json")
$LatestPath = Join-Path $InstallRoot "latest.json"
$InstallManifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ManifestPath -Encoding UTF8
Copy-Item -LiteralPath $ManifestPath -Destination $LatestPath -Force

Write-Host "Probe pack installation completed." -ForegroundColor Green
Write-Host "Installation manifest: $ManifestPath"
if ($InstallPersistence) {
    Write-Host "The active mod list was not changed. Enable only the persistence pack manually in the launcher." -ForegroundColor Yellow
    Write-Host "Use a disposable campaign only." -ForegroundColor Yellow
}
elseif ($InstallCampaignFeasibility) {
    Write-Host "The active mod list was not changed. Enable the campaign feasibility pack only with the exact SFO pack for the dedicated observation."
    Write-Host "The campaign feasibility pack is read-only and does not issue campaign orders." -ForegroundColor Green
}
elseif ($InstallBattleReplay) {
    Write-Host "The active mod list was not changed. Enable only the battle replay pack manually in the launcher."
    Write-Host "The battle replay pack is read-only and does not issue orders." -ForegroundColor Green
}
elseif ($InstallShadow) {
    Write-Host "The active mod list was not changed. Enable only the shadow pack manually in the launcher."
    Write-Host "The shadow pack is read-only and does not issue campaign or battle orders." -ForegroundColor Green
}
else {
    Write-Host "The active mod list was not changed. Enable only the observer pack manually in the launcher."
}

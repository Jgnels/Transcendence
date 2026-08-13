[CmdletBinding()]
param(
    [string]$RepoRoot = ""
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

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
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

$RuntimeLog = Join-Path $GameRoot "transcendence_runtime_log.txt"
$ArchiveRoot = Join-Path $RepoRoot "local_inputs\runtime_probe\runtime_log_archives"
$SessionRoot = Join-Path $RepoRoot "local_inputs\runtime_probe\sessions"
New-Item -ItemType Directory -Force -Path $ArchiveRoot, $SessionRoot | Out-Null

$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
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

$StagedPack = Join-Path $RepoRoot "local_inputs\runtime_probe\staged\transcendence_shadow_probe.pack"
$InstalledPack = Join-Path $GameRoot "data\transcendence_shadow_probe.pack"
foreach ($Path in @($StagedPack, $InstalledPack)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required shadow pack is missing: $Path"
    }
}
$StagedSha = Get-Sha256 $StagedPack
$InstalledSha = Get-Sha256 $InstalledPack
if ($StagedSha -ne $InstalledSha) {
    throw "Installed shadow pack does not match the staged build. Reinstall the shadow pack before starting."
}

$SessionManifest = [ordered]@{
    schema_version = 1
    prepared_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    runtime_log = $RuntimeLog
    runtime_log_cleared = (-not (Test-Path -LiteralPath $RuntimeLog))
    previous_runtime_log = $Archived
    staged_shadow_pack_sha256 = $StagedSha
    installed_shadow_pack_sha256 = $InstalledSha
    active_mod_list_modified = $false
    wh3_save_modified = $false
    expected_runtime_markers = @(
        "TRANS_PROBE|1|RUNTIME_BEGIN|probe_kind=shadow|runtime=campaign",
        "TRANS_BATTLE|1|RUNTIME_BEGIN|probe_kind=battle_replay_shadow|runtime=battle"
    )
}
$ManifestPath = Join-Path $SessionRoot ("combined_session_" + $Timestamp + ".json")
$SessionManifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ManifestPath -Encoding UTF8
Copy-Item -LiteralPath $ManifestPath -Destination (Join-Path $SessionRoot "latest.json") -Force

Write-Host "" 
Write-Host "COMBINED SESSION READY" -ForegroundColor Green
Write-Host "Append-only runtime log cleared: $RuntimeLog"
Write-Host "Shadow pack SHA-256: $InstalledSha"
Write-Host "Session manifest: $ManifestPath"
Write-Host "" 
Write-Host "The launcher mod list was not changed." -ForegroundColor Yellow
Write-Host "Enable only the Transcendence shadow pack before launching WH3."

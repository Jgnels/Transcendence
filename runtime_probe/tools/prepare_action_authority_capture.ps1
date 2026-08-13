#requires -Version 5.1
[CmdletBinding(SupportsShouldProcess=$true)]
param(
    [string]$RepoRoot = "",
    [switch]$Force
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
    $Python = Get-Command python -ErrorAction SilentlyContinue
    $Prefix = @()
    if (-not $Python) { $Python = Get-Command py -ErrorAction SilentlyContinue; if ($Python) { $Prefix = @("-3") } }
    if (-not $Python) { throw "Python 3 was not found." }
    return [pscustomobject]@{ Command = $Python.Source; Prefix = $Prefix }
}
function Confirm-Explicit([string]$Message) {
    if ($Force) { return $true }
    return (Read-Host "$Message Type YES to continue") -ceq "YES"
}

$MachineManifestPath = Join-Path $RepoRoot "local_inputs\machine_profiles\gaming_laptop_private.json"
if (-not (Test-Path -LiteralPath $MachineManifestPath -PathType Leaf)) { throw "Private machine manifest not found: $MachineManifestPath" }
$MachineManifest = Get-Content -LiteralPath $MachineManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$GameRoot = [string]$MachineManifest.game.install_path
if (-not $GameRoot -or -not (Test-Path -LiteralPath $GameRoot -PathType Container)) { throw "WH3 installation path is missing or invalid." }
$GameData = Join-Path $GameRoot "data"

$Python = Get-PythonCommand
$DistRoot = Join-Path $RepoRoot "dist\runtime_probe_action_authority"
if (Test-Path -LiteralPath $DistRoot) { Remove-Item -LiteralPath $DistRoot -Recurse -Force }
& $Python.Command @($Python.Prefix) (Join-Path $RepoRoot "runtime_probe\tools\build_probe_packs.py") --repo-root $RepoRoot --output $DistRoot | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Deterministic probe build failed with exit code $LASTEXITCODE." }

$BuildManifestPath = Join-Path $DistRoot "probe_build_manifest.json"
$BuildManifest = Get-Content -LiteralPath $BuildManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$Matches = @($BuildManifest.packs | Where-Object { $_.probe_kind -eq "action_authority" })
if ($Matches.Count -ne 1) { throw "Expected exactly one action-authority pack in the build manifest." }
$Build = $Matches[0]
$PackName = [string]$Build.pack_name
$BuiltPack = Join-Path $DistRoot $PackName
$BuiltSha = Get-Sha256 $BuiltPack
if ($BuiltSha -ne [string]$Build.pack_sha256) { throw "Built action-authority pack hash mismatch." }

$LocalRoot = Join-Path $RepoRoot "local_inputs\runtime_probe\action_authority"
$StageRoot = Join-Path $LocalRoot "staged"
$SessionRoot = Join-Path $LocalRoot "sessions"
$BackupRoot = Join-Path $LocalRoot "backups"
New-Item -ItemType Directory -Force -Path $StageRoot, $SessionRoot, $BackupRoot | Out-Null
$StagedPack = Join-Path $StageRoot $PackName
Copy-Item -LiteralPath $BuiltPack -Destination $StagedPack -Force
if ((Get-Sha256 $StagedPack) -ne $BuiltSha) { throw "Staged action-authority pack hash mismatch." }

if (-not (Confirm-Explicit "Install the read-only action-authority probe into WH3 data. The script will not enable it in the launcher or modify saves.")) { throw "Preparation cancelled." }
$InstalledPack = Join-Path $GameData $PackName
$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$BackupPath = $null
$PreviousSha = $null
if (Test-Path -LiteralPath $InstalledPack -PathType Leaf) {
    $PreviousSha = Get-Sha256 $InstalledPack
    $BackupPath = Join-Path $BackupRoot ($Timestamp + "_" + $PackName)
    Copy-Item -LiteralPath $InstalledPack -Destination $BackupPath -Force
}
if ($PSCmdlet.ShouldProcess($InstalledPack, "Install read-only action-authority probe")) {
    Copy-Item -LiteralPath $StagedPack -Destination $InstalledPack -Force
}
$InstalledSha = Get-Sha256 $InstalledPack
if ($InstalledSha -ne $BuiltSha) { throw "Installed action-authority pack hash mismatch." }

$RuntimeLog = Join-Path $GameRoot "transcendence_runtime_log.txt"
$ArchivedRuntimeLog = $null
if (Test-Path -LiteralPath $RuntimeLog -PathType Leaf) {
    $ArchivePath = Join-Path $BackupRoot ($Timestamp + "_transcendence_runtime_log.txt")
    Copy-Item -LiteralPath $RuntimeLog -Destination $ArchivePath -Force
    $ArchivedRuntimeLog = [ordered]@{ path = $ArchivePath; sha256 = Get-Sha256 $ArchivePath; size_bytes = [int64](Get-Item -LiteralPath $ArchivePath).Length }
    Remove-Item -LiteralPath $RuntimeLog -Force
}

$Manifest = [ordered]@{
    schema_version = 1
    capture_kind = "action_authority"
    prepared_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    runtime_log = $RuntimeLog
    runtime_log_cleared = (-not (Test-Path -LiteralPath $RuntimeLog))
    previous_runtime_log = $ArchivedRuntimeLog
    pack_name = $PackName
    staged_pack_sha256 = $BuiltSha
    installed_pack_sha256 = $InstalledSha
    previous_installed_pack_sha256 = $PreviousSha
    installed_pack_backup = $BackupPath
    active_mod_list_modified = $false
    wh3_save_modified = $false
    project_orders_enabled = $false
    expected_marker = "TRANS_ACTION|1|PACK_LOADED|probe_kind=action_authority_shadow"
}
$ManifestPath = Join-Path $SessionRoot ("prepared_" + $Timestamp + ".json")
$Manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ManifestPath -Encoding UTF8
Copy-Item -LiteralPath $ManifestPath -Destination (Join-Path $SessionRoot "latest.json") -Force

Write-Host "`nACTION-AUTHORITY CAPTURE PREPARED" -ForegroundColor Green
Write-Host "Pack SHA-256: $InstalledSha"
Write-Host "Prepared manifest: $ManifestPath"
Write-Host "Runtime log cleared: $RuntimeLog"
Write-Host "The launcher mod list was not changed." -ForegroundColor Yellow
Write-Host "Enable only $PackName, fight one ordinary single-player battle, issue normal player commands, exit WH3, then run collect_action_authority_capture.ps1." -ForegroundColor Yellow

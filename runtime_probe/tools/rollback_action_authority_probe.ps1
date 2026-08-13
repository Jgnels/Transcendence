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

$ManifestPath = Join-Path $RepoRoot "local_inputs\runtime_probe\action_authority\sessions\latest.json"
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) { throw "Prepared action-authority manifest missing: $ManifestPath" }
$Manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($Manifest.capture_kind -ne "action_authority") { throw "Unexpected capture kind in manifest." }
$InstalledPack = Join-Path (Split-Path -Parent ([string]$Manifest.runtime_log)) ("data\" + [string]$Manifest.pack_name)
$ExpectedCurrent = [string]$Manifest.installed_pack_sha256
if (Test-Path -LiteralPath $InstalledPack -PathType Leaf) {
    $Current = Get-Sha256 $InstalledPack
    if (-not $Force -and $Current -ne $ExpectedCurrent) {
        throw "Installed action-authority pack changed after preparation. Refusing rollback without -Force."
    }
}
$Backup = [string]$Manifest.installed_pack_backup
$PreviousSha = [string]$Manifest.previous_installed_pack_sha256
if (-not [string]::IsNullOrWhiteSpace($Backup)) {
    if (-not (Test-Path -LiteralPath $Backup -PathType Leaf)) { throw "Recorded pack backup is missing: $Backup" }
    if (-not [string]::IsNullOrWhiteSpace($PreviousSha) -and (Get-Sha256 $Backup) -ne $PreviousSha) { throw "Recorded pack backup hash mismatch." }
    if ($PSCmdlet.ShouldProcess($InstalledPack, "Restore prior action-authority pack")) { Copy-Item -LiteralPath $Backup -Destination $InstalledPack -Force }
}
elseif (Test-Path -LiteralPath $InstalledPack -PathType Leaf) {
    if ($PSCmdlet.ShouldProcess($InstalledPack, "Remove action-authority pack installed by preparation")) { Remove-Item -LiteralPath $InstalledPack -Force }
}
Write-Host "`nACTION-AUTHORITY PROBE ROLLBACK COMPLETE" -ForegroundColor Green
Write-Host "The active mod list and saves were not modified." -ForegroundColor Yellow

[CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact="High")]
param(
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$LatestManifest = Join-Path $RepoRoot "local_inputs\runtime_probe\installations\latest.json"
if (-not (Test-Path -LiteralPath $LatestManifest -PathType Leaf)) {
    throw "No probe installation manifest found: $LatestManifest"
}
$Manifest = Get-Content -LiteralPath $LatestManifest -Raw | ConvertFrom-Json

foreach ($Pack in $Manifest.packs) {
    $Destination = [string]$Pack.destination
    if (Test-Path -LiteralPath $Destination -PathType Leaf) {
        $CurrentSha = Get-Sha256 $Destination
        if ($CurrentSha -ne [string]$Pack.installed_sha256 -and -not $Force) {
            throw "Refusing to remove changed file $Destination. Use -Force only after inspecting it."
        }
        if ($PSCmdlet.ShouldProcess($Destination, "Remove Transcendence probe pack")) {
            Remove-Item -LiteralPath $Destination -Force
        }
    }

    $BackupPath = [string]$Pack.backup_path
    if ($BackupPath -and (Test-Path -LiteralPath $BackupPath -PathType Leaf)) {
        if ($PSCmdlet.ShouldProcess($Destination, "Restore pre-existing file")) {
            Copy-Item -LiteralPath $BackupPath -Destination $Destination -Force
        }
        if ([string]$Pack.previous_sha256) {
            $RestoredSha = Get-Sha256 $Destination
            if ($RestoredSha -ne [string]$Pack.previous_sha256) {
                throw "Restored file hash mismatch for $Destination."
            }
        }
    }
}

Write-Host "Probe pack rollback completed." -ForegroundColor Green
Write-Host "The script did not edit the launcher's active-mod configuration."
Write-Host "Any inert persistence key already saved remains in that save but has no effect without the pack."

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("Write", "Reload")]
    [string]$Phase
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$EvidencePhase = if ($Phase -eq "Write") { "persistence_write" } else { "persistence_reload" }

& powershell.exe -NoProfile -ExecutionPolicy Bypass `
    -File (Join-Path $PSScriptRoot "collect_probe_logs.ps1") `
    -EvidencePhase $EvidencePhase
if ($LASTEXITCODE -ne 0) {
    throw "Persistence $Phase evidence collection failed with exit code $LASTEXITCODE."
}

if ($Phase -eq "Reload") {
    Write-Host ""
    Write-Host "Both phases should now exist. Running strict persistence verification..." -ForegroundColor Cyan
    & powershell.exe -NoProfile -ExecutionPolicy Bypass `
        -File (Join-Path $PSScriptRoot "verify_persistence_roundtrip.ps1")
    if ($LASTEXITCODE -ne 0) {
        throw "Persistence verification failed with exit code $LASTEXITCODE."
    }
}

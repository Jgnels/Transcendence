[CmdletBinding()]
param(
    [string]$ExpectedPersistenceSha256 = "71bf96e4fca54d16e323f5eef9766a6098c6ea4b9416b33aa012317d5f682bd2"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$StateRoot = Join-Path $RepoRoot "local_inputs\runtime_probe\persistence_roundtrip"
$WriteStatePath = Join-Path $StateRoot "write.json"
$ReloadStatePath = Join-Path $StateRoot "reload.json"

foreach ($Required in @($WriteStatePath, $ReloadStatePath)) {
    if (-not (Test-Path -LiteralPath $Required -PathType Leaf)) {
        throw "Missing persistence phase state: $Required"
    }
}

$WriteState = Get-Content -LiteralPath $WriteStatePath -Raw | ConvertFrom-Json
$ReloadState = Get-Content -LiteralPath $ReloadStatePath -Raw | ConvertFrom-Json

$Python = Get-Command python -ErrorAction SilentlyContinue
$PythonArgs = @()
if (-not $Python) {
    $Python = Get-Command py -ErrorAction SilentlyContinue
    if ($Python) { $PythonArgs = @("-3") }
}
if (-not $Python) {
    throw "Python 3 was not found."
}

$OutputPath = Join-Path $StateRoot "verification.json"
& $Python.Source @PythonArgs `
    (Join-Path $PSScriptRoot "verify_persistence_roundtrip.py") `
    ([string]$WriteState.log_path) `
    ([string]$ReloadState.log_path) `
    --evidence-manifest ([string]$WriteState.evidence_manifest_path) `
    --evidence-manifest ([string]$ReloadState.evidence_manifest_path) `
    --expected-pack-sha256 $ExpectedPersistenceSha256 `
    --output $OutputPath
if ($LASTEXITCODE -ne 0) {
    throw "Persistence verifier failed with exit code $LASTEXITCODE."
}

$Result = Get-Content -LiteralPath $OutputPath -Raw | ConvertFrom-Json
if ([string]$Result.status -ne "REPLICATED") {
    throw "Persistence round trip is not replicated. Review $OutputPath"
}

Write-Host ""
Write-Host "PERSISTENCE ROUND TRIP REPLICATED" -ForegroundColor Green
Write-Host "Verification: $OutputPath"
Write-Host "Result digest: $($Result.result_digest)"

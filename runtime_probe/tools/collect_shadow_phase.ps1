[CmdletBinding()]
param(
    [string]$ProfilePath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
if (-not $ProfilePath) {
    $ProfilePath = Join-Path $RepoRoot "synthetic_lab\profiles\vanilla_8_1_1.json"
}
if (-not (Test-Path -LiteralPath $ProfilePath -PathType Leaf)) {
    throw "Profile not found: $ProfilePath"
}

& powershell.exe -NoProfile -ExecutionPolicy Bypass `
    -File (Join-Path $PSScriptRoot "collect_probe_logs.ps1") `
    -EvidencePhase shadow
if ($LASTEXITCODE -ne 0) {
    throw "Shadow evidence collection failed with exit code $LASTEXITCODE."
}

$EvidenceParent = Join-Path $RepoRoot "local_inputs\logs\wh3"
$Latest = Get-ChildItem -LiteralPath $EvidenceParent -Directory -Filter "probe_*" |
    Sort-Object LastWriteTimeUtc -Descending |
    Select-Object -First 1
if (-not $Latest) {
    throw "No evidence folder was found under $EvidenceParent."
}

$ManifestPath = Join-Path $Latest.FullName "evidence_manifest.json"
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    throw "Evidence manifest missing: $ManifestPath"
}
$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
if ([string]$Manifest.evidence_phase -ne "shadow") {
    throw "Latest evidence folder is not a shadow collection."
}
if (@($Manifest.unexpected_loaded_probe_kinds).Count -ne 0) {
    throw "Unexpected probe kind loaded during shadow collection."
}
if (@($Manifest.loaded_probe_kinds).Count -ne 1 -or [string]$Manifest.loaded_probe_kinds[0] -ne "shadow") {
    throw "Shadow probe was not the only loaded Transcendence probe."
}

$LogPaths = @($Manifest.logs | ForEach-Object { [string]$_.private_copy })
if ($LogPaths.Count -ne 1) {
    throw "Expected exactly one shadow log."
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

$OutputPath = Join-Path $Latest.FullName "shadow_assignment.json"
& $Python.Source @PythonArgs `
    (Join-Path $PSScriptRoot "run_shadow_assignment.py") `
    @LogPaths `
    --profile $ProfilePath `
    --output $OutputPath
if ($LASTEXITCODE -ne 0) {
    throw "Shadow assignment pipeline failed with exit code $LASTEXITCODE."
}

Write-Host ""
Write-Host "SHADOW EVIDENCE AND OBJECTIVE PROPOSAL CREATED" -ForegroundColor Green
Write-Host "Evidence folder: $($Latest.FullName)"
Write-Host "Upload these files:" -ForegroundColor Yellow
Write-Host "  $ManifestPath"
Write-Host "  $(Join-Path $Latest.FullName 'probe_summary.json')"
Write-Host "  $($LogPaths[0])"
Write-Host "  $OutputPath"
Write-Host ""
Write-Host "No campaign order was issued." -ForegroundColor Green

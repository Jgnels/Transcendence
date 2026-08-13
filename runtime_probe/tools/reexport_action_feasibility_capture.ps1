#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [string]$ExpectedRawLogSha256 = "b4f8c4ca9c285018772d50a4eda92f34572f742dd97967bca8229b0a6b3ce951",
    [string]$ExpectedPackSha256 = "3acf60520b60f87f8c18e13532512324cb7a539626996ce19897fad94cf2d25d"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    if ([string]::IsNullOrWhiteSpace($PSScriptRoot)) { throw "Supply -RepoRoot explicitly." }
    $RepoRoot = Join-Path $PSScriptRoot "..\.."
}
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
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

if ($ExpectedRawLogSha256 -notmatch '^[0-9a-f]{64}$') { throw "ExpectedRawLogSha256 must be lowercase SHA-256." }
if ($ExpectedPackSha256 -notmatch '^[0-9a-f]{64}$') { throw "ExpectedPackSha256 must be lowercase SHA-256." }

Write-Host "`n==> Locating the exact preserved v0.1S private capture" -ForegroundColor Cyan
$CaptureRoot = Join-Path $RepoRoot "local_inputs\runtime_probe\action_authority\captures"
if (-not (Test-Path -LiteralPath $CaptureRoot -PathType Container)) {
    throw "No preserved action-authority captures were found: $CaptureRoot"
}
$Matches = @()
Get-ChildItem -LiteralPath $CaptureRoot -Directory | Sort-Object LastWriteTimeUtc -Descending | ForEach-Object {
    $Raw = Join-Path $_.FullName "action_authority_runtime_log.txt"
    $Prepared = Join-Path $_.FullName "prepared_manifest.json"
    if ((Test-Path -LiteralPath $Raw -PathType Leaf) -and (Test-Path -LiteralPath $Prepared -PathType Leaf)) {
        if ((Get-Sha256 $Raw) -eq $ExpectedRawLogSha256) {
            $Matches += [pscustomobject]@{ Directory = $_.FullName; Raw = $Raw; Prepared = $Prepared }
        }
    }
}
if ($Matches.Count -eq 0) {
    throw "The exact preserved raw log was not found. Expected SHA-256: $ExpectedRawLogSha256"
}
$Source = $Matches[0]
Write-Host "    Exact raw-log identity found; private path will not be exported." -ForegroundColor Green

$Prepared = Get-Content -LiteralPath $Source.Prepared -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]$Prepared.installed_pack_sha256 -ne $ExpectedPackSha256) {
    throw "Preserved prepared-manifest pack hash does not match the v0.1R probe."
}
if ([bool]$Prepared.project_orders_enabled) { throw "Preserved manifest claims project orders were enabled." }
if ([bool]$Prepared.active_mod_list_modified) { throw "Preserved manifest claims the preparer changed the active mod list." }
if ([bool]$Prepared.wh3_save_modified) { throw "Preserved manifest claims the preparer changed a save." }

Write-Host "`n==> Building a public-safe detailed feasibility-window export" -ForegroundColor Cyan
$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$PrivateOutputRoot = Join-Path $RepoRoot ("local_inputs\runtime_probe\action_authority\reexports\reexport_" + $Timestamp)
$ExportRoot = Join-Path $RepoRoot "local_inputs\runtime_probe\exports"
$Stage = Join-Path $PrivateOutputRoot "public_export"
New-Item -ItemType Directory -Force -Path $PrivateOutputRoot, $ExportRoot, $Stage | Out-Null

$Python = Get-PythonCommand
$WindowsPath = Join-Path $Stage "action_feasibility_windows.json"
& $Python.Command @($Python.Prefix) `
    (Join-Path $RepoRoot "runtime_probe\tools\export_action_feasibility_windows.py") `
    $Source.Raw $Source.Prepared `
    --expected-raw-log-sha256 $ExpectedRawLogSha256 `
    --expected-pack-sha256 $ExpectedPackSha256 `
    --output $WindowsPath | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Detailed action-feasibility export failed with exit code $LASTEXITCODE." }

$WindowsDocument = Get-Content -LiteralPath $WindowsPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]$WindowsDocument.authority -ne "NO_ORDERS") { throw "Detailed export lost NO_ORDERS authority." }
if ([int]$WindowsDocument.project_issue_attempt_count -ne 0) { throw "Detailed export claimed project issue attempts." }
if ([int]$WindowsDocument.direct_acknowledgement_count -ne 0) { throw "Detailed export claimed acknowledgements." }
if ([bool]$WindowsDocument.raw_log_in_export) { throw "Detailed export attempted to include the raw log." }

$PublicManifest = [ordered]@{
    schema_version = 1
    capture_kind = "action_feasibility_window_reexport"
    created_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    source_public_capture_sha256 = "a1c03ec12a4c2b70945311fc57b54f978fcca892a37b12d46a5daa6f22ebf579"
    source_raw_log_sha256 = $ExpectedRawLogSha256
    source_raw_log_in_export = $false
    installed_pack_sha256 = $ExpectedPackSha256
    action_feasibility_windows_sha256 = Get-Sha256 $WindowsPath
    window_count = [int]$WindowsDocument.window_count
    sample_count = [int]$WindowsDocument.sample_count
    authority = "NO_ORDERS"
    project_issue_attempt_count = 0
    direct_acknowledgement_count = 0
    personal_paths_in_export = $false
}
$ManifestPath = Join-Path $Stage "public_reexport_manifest.json"
$PublicManifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ManifestPath -Encoding UTF8

$CombinedText = (Get-Content -LiteralPath $WindowsPath, $ManifestPath -Raw -Encoding UTF8) -join "`n"
$ProfileEscaped = [Regex]::Escape($env:USERPROFILE.TrimEnd('\'))
if ($CombinedText -match $ProfileEscaped) { throw "Public re-export contains the owner profile path." }
if ($CombinedText -match '(?i)[A-Z]:\\Users\\') { throw "Public re-export contains a Windows user path." }
if ($CombinedText -match '(?i)steamapps\\common') { throw "Public re-export contains a game-install path." }

$ZipPath = Join-Path $ExportRoot ("Transcendence_ActionFeasibilityWindows_" + $Timestamp + ".zip")
Compress-Archive -Path (Join-Path $Stage "*") -DestinationPath $ZipPath -CompressionLevel Optimal

Write-Host "`nACTION-FEASIBILITY RE-EXPORT COMPLETE" -ForegroundColor Green
Write-Host "Windows: $($WindowsDocument.window_count)"
Write-Host "Samples: $($WindowsDocument.sample_count)"
Write-Host "Public-safe ZIP: $ZipPath"
Write-Host "ZIP SHA-256: $(Get-Sha256 $ZipPath)"
Write-Host "No WH3 run, pack installation, save change, mod-list change, or project order occurred." -ForegroundColor Yellow
Write-Host "Upload only the ZIP shown above." -ForegroundColor Yellow

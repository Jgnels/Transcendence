[CmdletBinding()]
param(
    [string]$RpfmRoot = '',
    [string]$SteamRoot = '',
    [string]$ServerUrl = 'ws://127.0.0.1:45127/ws'
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Acquire = Join-Path $PSScriptRoot 'Acquire-NativeCAIInputs.ps1'
$Export = Join-Path $PSScriptRoot 'Export-NativeCAIRows-RpfmServer.ps1'
$Bundle = Join-Path $PSScriptRoot 'Build-NativeCAIInputBundle.ps1'

foreach ($required in @($Acquire, $Export, $Bundle)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required acquisition tool is missing: $required"
    }
}

Write-Host '=== Transcendence Native CAI reconciliation acquisition ==='
Write-Host 'This workflow is read-only with respect to WH3 and Workshop content.'
Write-Host 'RPFM 5.x must already be open with Warhammer 3 configured.'
Write-Host ''

$acquireArgs = @{}
if ($RpfmRoot) { $acquireArgs['RpfmRoot'] = $RpfmRoot }
if ($SteamRoot) { $acquireArgs['SteamRoot'] = $SteamRoot }

Write-Host '[1/3] Discovering/hash-binding local schema and target Workshop packs...'
& $Acquire @acquireArgs
if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { throw "Acquire-NativeCAIInputs.ps1 exited with code $LASTEXITCODE" }

Write-Host ''
Write-Host '[2/3] Asking RPFM to extract target vanilla/mod CAI DB evidence read-only...'
try {
    & $Export -ServerUrl $ServerUrl
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { throw "Export-NativeCAIRows-RpfmServer.ps1 exited with code $LASTEXITCODE" }
} catch {
    $inputRoot = Join-Path $RepoRoot 'local_inputs\native_cai_reconciliation'
    Write-Host ''
    Write-Warning 'RPFM export did not complete. Do not launch WH3 and do not edit any packs.'
    Write-Warning "The discovery evidence is still useful. Preserve/upload: $inputRoot\acquisition_manifest.json and ACQUISITION_SUMMARY.txt"
    throw
}

Write-Host ''
Write-Host '[3/3] Building one compact private owner-input ZIP (raw .pack files excluded)...'
& $Bundle
if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { throw "Build-NativeCAIInputBundle.ps1 exited with code $LASTEXITCODE" }

Write-Host ''
Write-Host 'COMPLETE. Upload the generated Transcendence_NativeCAI_OwnerInputs_*.zip to the Transcendence chat.'

[CmdletBinding()]
param(
    [string]$OutputZip = ''
)
$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$InputRoot = Join-Path $RepoRoot 'local_inputs\native_cai_reconciliation'
if (-not (Test-Path -LiteralPath $InputRoot)) { throw "No acquisition directory exists at $InputRoot" }
if (-not $OutputZip) {
    $stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
    $OutputZip = Join-Path (Split-Path -Parent $RepoRoot) "Transcendence_NativeCAI_OwnerInputs_$stamp.zip"
}

# Never package raw .pack files. Exact pack identities are already captured in
# acquisition_manifest.json; row evidence is extracted separately and is sufficient
# for the reconciliation handoff. This keeps owner uploads well below platform limits.
$staging = Join-Path $env:TEMP ('trans_native_cai_bundle_' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $staging | Out-Null
try {
    foreach ($file in Get-ChildItem -LiteralPath $InputRoot -File -Recurse) {
        $relative = $file.FullName.Substring($InputRoot.Length).TrimStart([char[]]'\/')
        $lower = $relative.ToLowerInvariant()
        if ($lower.EndsWith('.pack')) { continue }
        $dest = Join-Path $staging $relative
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
        Copy-Item -LiteralPath $file.FullName -Destination $dest -Force
    }
    $hashLines = @()
    foreach ($file in Get-ChildItem -LiteralPath $staging -File -Recurse | Sort-Object FullName) {
        $relative = $file.FullName.Substring($staging.Length).TrimStart([char[]]'\/') -replace '\\','/'
        $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash.ToLowerInvariant()
        $hashLines += "$hash  $relative"
    }
    $hashLines | Set-Content -LiteralPath (Join-Path $staging 'SHA256SUMS.txt') -Encoding UTF8
    if (Test-Path -LiteralPath $OutputZip) { Remove-Item -LiteralPath $OutputZip -Force }
    Compress-Archive -Path (Join-Path $staging '*') -DestinationPath $OutputZip -CompressionLevel Optimal
    Write-Host "Created private owner-input bundle: $OutputZip"
} finally {
    Remove-Item -LiteralPath $staging -Recurse -Force -ErrorAction SilentlyContinue
}

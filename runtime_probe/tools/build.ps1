[CmdletBinding()]
param(
    [string]$OutputDirectory = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $RepoRoot "dist\runtime_probe"
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

& $Python.Source @PythonArgs -m unittest discover `
    -s (Join-Path $RepoRoot "runtime_probe\tests") `
    -p "test_*.py" `
    -v
if ($LASTEXITCODE -ne 0) {
    throw "Runtime-probe tests failed with exit code $LASTEXITCODE."
}

& $Python.Source @PythonArgs `
    (Join-Path $RepoRoot "runtime_probe\tools\build_probe_packs.py") `
    --repo-root $RepoRoot `
    --output $OutputDirectory
if ($LASTEXITCODE -ne 0) {
    throw "Probe pack build failed with exit code $LASTEXITCODE."
}

Write-Host "Probe packs built under $OutputDirectory" -ForegroundColor Green

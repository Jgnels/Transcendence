$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) { $Python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $Python) { throw "Python 3 was not found." }

if ($Python.Name -eq "py.exe" -or $Python.Name -eq "py") {
    & $Python.Source -3 (Join-Path $PSScriptRoot "validate_repository.py")
} else {
    & $Python.Source (Join-Path $PSScriptRoot "validate_repository.py")
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

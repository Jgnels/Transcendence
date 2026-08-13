param(
    [string]$Prepared = "",
    [switch]$AttestPassiveProtocol
)

$ErrorActionPreference = "Stop"
$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ScriptDirectory "collect_native_churn_capture.py"

if (-not (Test-Path -LiteralPath $PythonScript -PathType Leaf)) {
    throw "Missing Python collection script: $PythonScript"
}

$PythonArgs = @($PythonScript)
if ($Prepared -ne "") {
    $PythonArgs += @("--prepared", $Prepared)
}
if ($AttestPassiveProtocol) {
    $PythonArgs += "--owner-protocol-attested"
}

$Python = Get-Command python.exe -ErrorAction SilentlyContinue
if ($null -ne $Python) {
    & $Python.Source @PythonArgs
    exit $LASTEXITCODE
}

$PyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
if ($null -ne $PyLauncher) {
    & $PyLauncher.Source -3 @PythonArgs
    exit $LASTEXITCODE
}

throw "Python 3 was not found. Install Python 3 or make python.exe/py.exe available on PATH."

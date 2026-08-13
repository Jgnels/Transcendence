param([string]$GameRoot = "")
$ErrorActionPreference = "Stop"
$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ScriptDirectory "prepare_native_diagnostic_capture.py"
$ArgsList = @($PythonScript)
if ($GameRoot -ne "") { $ArgsList += @("--game-root", $GameRoot) }
$Python = Get-Command python.exe -ErrorAction SilentlyContinue
if ($null -ne $Python) { & $Python.Source @ArgsList; exit $LASTEXITCODE }
$Py = Get-Command py.exe -ErrorAction SilentlyContinue
if ($null -ne $Py) { & $Py.Source -3 @ArgsList; exit $LASTEXITCODE }
throw "Python 3 was not found."

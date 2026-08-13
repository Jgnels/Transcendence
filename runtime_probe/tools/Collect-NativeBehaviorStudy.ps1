param([string]$Prepared = "")
$ErrorActionPreference = "Stop"
$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ScriptDirectory "collect_native_behavior_study.py"
$ArgsList = @($PythonScript)
if ($Prepared -ne "") { $ArgsList += @("--prepared", $Prepared) }
$Python = Get-Command python.exe -ErrorAction SilentlyContinue
if ($null -ne $Python) { & $Python.Source @ArgsList; exit $LASTEXITCODE }
$Py = Get-Command py.exe -ErrorAction SilentlyContinue
if ($null -ne $Py) { & $Py.Source -3 @ArgsList; exit $LASTEXITCODE }
throw "Python 3 was not found."

param([string]$GameRoot = "", [string]$SfoPackPath = "")
$ErrorActionPreference = "Stop"
$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ScriptDirectory "prepare_native_sfo_behavior_benchmark.py"
$ArgsList = @($PythonScript)
if ($GameRoot -ne "") { $ArgsList += @("--game-root", $GameRoot) }
if ($SfoPackPath -ne "") { $ArgsList += @("--sfo-pack-path", $SfoPackPath) }
$Python = Get-Command python.exe -ErrorAction SilentlyContinue
if ($null -ne $Python) { & $Python.Source @ArgsList; exit $LASTEXITCODE }
$Py = Get-Command py.exe -ErrorAction SilentlyContinue
if ($null -ne $Py) { & $Py.Source -3 @ArgsList; exit $LASTEXITCODE }
throw "Python 3 was not found."

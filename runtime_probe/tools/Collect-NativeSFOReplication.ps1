$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Get-Command python.exe -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py.exe -ErrorAction Stop }
Write-Host "Collecting v0.2Q Stage-A fresh SFO replication with the frozen v0.2P evaluator."
& $python.Source (Join-Path $here "collect_native_sfo_behavior_benchmark.py") @args

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Get-Command python.exe -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py.exe -ErrorAction Stop }
Write-Host "v0.2Q Stage-A fresh SFO replication (uses the frozen v0.2P benchmark profile/instrument)."
& $python.Source (Join-Path $here "prepare_native_sfo_behavior_benchmark.py") @args

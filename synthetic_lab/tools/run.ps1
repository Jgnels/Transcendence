param(
    [Parameter(Position=0)]
    [ValidateSet("test", "smoke", "tier1", "tier2", "tier3", "tier4", "tier4r", "tier4r-trace", "tier4r-shadow", "tier4r-adversary", "tier4r-assignment", "assignment-matrix", "tier4r-schedule", "schedule-matrix", "action-authority-matrix", "battle4-action-authority", "tier4r-feasibility", "feasibility-matrix", "audit-mods")]
    [string]$Command = "test",
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$RemainingArgs
)

$ErrorActionPreference = "Stop"
$LabRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = $LabRoot

$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
    $Python = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $Python) {
    throw "Python 3 was not found. Install Python 3 or add it to PATH."
}

$BaseArgs = @("-m", "transcendence_lab.cli")
if ($Python.Name -eq "py.exe" -or $Python.Name -eq "py") {
    $BaseArgs = @("-3") + $BaseArgs
}

switch ($Command) {
    "test" { & $Python.Source @BaseArgs test @RemainingArgs }
    "smoke" {
        $Output = Join-Path (Split-Path -Parent $LabRoot) "local_inputs/generated/synthetic_lab_smoke.json"
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Output) | Out-Null
        & $Python.Source @BaseArgs smoke --output $Output @RemainingArgs
    }
    "tier1" { & $Python.Source @BaseArgs tier1 @RemainingArgs }
    "tier2" { & $Python.Source @BaseArgs tier2 @RemainingArgs }
    "tier3" { & $Python.Source @BaseArgs tier3 @RemainingArgs }
    "tier4" { & $Python.Source @BaseArgs tier4 @RemainingArgs }
    "tier4r" { & $Python.Source @BaseArgs tier4r @RemainingArgs }
    "tier4r-trace" { & $Python.Source @BaseArgs tier4r-trace @RemainingArgs }
    "tier4r-shadow" { & $Python.Source @BaseArgs tier4r-shadow @RemainingArgs }
    "tier4r-adversary" { & $Python.Source @BaseArgs tier4r-adversary @RemainingArgs }
    "tier4r-assignment" { & $Python.Source @BaseArgs tier4r-assignment @RemainingArgs }
    "assignment-matrix" { & $Python.Source @BaseArgs assignment-matrix @RemainingArgs }
    "tier4r-schedule" { & $Python.Source @BaseArgs tier4r-schedule @RemainingArgs }
    "schedule-matrix" { & $Python.Source @BaseArgs schedule-matrix @RemainingArgs }
    "action-authority-matrix" { & $Python.Source @BaseArgs action-authority-matrix @RemainingArgs }
    "battle4-action-authority" { & $Python.Source @BaseArgs battle4-action-authority @RemainingArgs }
    "tier4r-feasibility" { & $Python.Source @BaseArgs tier4r-feasibility @RemainingArgs }
    "feasibility-matrix" { & $Python.Source @BaseArgs feasibility-matrix @RemainingArgs }
    "audit-mods" { & $Python.Source @BaseArgs audit-mods @RemainingArgs }
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

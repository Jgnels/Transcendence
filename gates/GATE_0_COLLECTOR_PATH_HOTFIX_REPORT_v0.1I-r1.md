# Gate 0 Collector Path Hotfix — v0.1I-r1

## Classification

- Defect class: local tooling lifecycle / Windows PowerShell initialization
- Evidence label before correction: `OBSERVED_FAILURE`
- Runtime evidence at risk: none; the WH3 log remains available in the game folder
- Game, save, Workshop, and active-mod mutation: none

## Failure

`collect_campaign_battle.ps1` resolved its default repository path inside the `param` block using `$PSScriptRoot`. On the owner's Windows PowerShell invocation, that automatic variable was empty while parameter defaults were evaluated, so `Join-Path` failed before collection began.

## Correction

- `RepoRoot` now defaults to an empty string.
- Repository discovery occurs after script initialization.
- An explicit error requests `-RepoRoot` only if PowerShell still cannot provide the script directory.
- The same latent defect was corrected in `collect_campaign_shadow.ps1`.
- A regression test rejects `$PSScriptRoot` use in collector parameter defaults.

## Owner impact

The live campaign and battle session does not need to be repeated. After applying the hotfix, rerunning the collector consumes the existing `lua_mod_log.txt` and produces the intended evidence ZIP.

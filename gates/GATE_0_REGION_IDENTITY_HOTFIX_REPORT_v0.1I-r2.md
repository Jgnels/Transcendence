# Gate 0 — Live Region Identity Hotfix Report v0.1I-r2

## Result

The narrow region-identity defect exposed by the first consolidated owner log is corrected offline. The combined live gate remains open because the preserved summary proves four canonical campaign snapshots, not five, and downstream battle parsing did not execute after the campaign pipeline stopped.

## Preserved failure

- owner collection timestamp: `2026-07-30T01:04:21Z`;
- parsed shadow event count: 182;
- complete canonical snapshots: turns `4, 5, 6, 7`;
- controlled armies: three per snapshot;
- owned regions: five, five, five, then six;
- player-visible regions: sixteen, sixteen, sixteen, then eighteen;
- failure: `duplicate region id: wh3_main_combi_region_altdorf`;
- failure layer: runtime-log-to-SyntheticLab scenario adapter;
- SyntheticLab duplicate-identity contract: correct and unchanged.

## Root cause

WH3's player-visible region interface legitimately included Altdorf even though the controlled-faction owned-region interface had already emitted Altdorf. The adapter appended interface records directly instead of reconciling stable entity identity.

## Correction

`build_shadow_scenario` now:

1. indexes region observations by stable WH3 region key;
2. treats owned and visible records as two views of one entity;
3. gives the richer owned record deterministic precedence;
4. records the number of resolved cross-view overlaps;
5. rejects duplicate records from the same source;
6. rejects conflicting owners rather than guessing;
7. preserves the strict downstream no-duplicate scenario contract.

No probe Lua, pack content, WH3 installation, save, active mod list, or remote repository state changed. The combined shadow pack hash remains unchanged.

## Tests

Two new regressions cover:

- owned/visible overlap coalescing with owned garrison data retained;
- conflicting owner rejection.

The next owner action is reprocessing the preserved log with the corrected adapter. The already-fought battle should not be repeated unless the recovered evidence proves that its records were not retained.

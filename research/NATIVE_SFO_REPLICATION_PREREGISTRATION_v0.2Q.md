# v0.2Q — Native/SFO temporal replication preregistration

## Purpose

Resolve whether the v0.2P SFO aggregate territorial reversal elevation is reproducible or was substantially driven by campaign composition. This is a research-only replication. It does not authorize gameplay orders or DB changes.

## Stage A — fresh SFO replicate

Use the exact same SFO/profile/instrument contract as v0.2P:

- Workshop 2792731173
- `sfo_grimhammer_3_main.pack` SHA-256 `ae20a0a08037aa3ebcbe7461d2589fc28dc15a5fe5d9ca4c0a9d0ff0a26da603`
- exact diagnostic probe and no extra mods
- new disposable Karl Franz / Reikland Immortal Empires campaign
- Legendary campaign / Very Hard battle
- unrestricted normal play; autoresolve allowed
- at least 11 consecutive Reikland turn-start markers / 10 complete AI cycles
- unchanged v0.2N temporal and recovery thresholds

Frozen Stage-A interpretation:

1. `<20` territorial eligible windows → insufficient exposure; repeat/extend SFO only.
2. `>=20` and repeated territorial force signal >0 → special-policy/causal review first; no SFO-row copying.
3. `>=20`, repeated=0 and candidate rate `>0.317073` → SFO aggregate elevation replicated; proceed to Stage B fresh vanilla replication.
4. `>=20`, repeated=0 and candidate rate `<=0.317073` → original SFO elevation not independently replicated; stop the row-ablation path.

No Stage-A outcome alone earns a row ablation.

## Stage B — conditional fresh vanilla replicate

Run only if Stage A returns `SFO_ELEVATION_REPLICATED`.

Profile-level separation requires the ordinal condition:

`min(SFO_run1_rate, SFO_run2_rate) > max(VANILLA_run1_rate, VANILLA_run2_rate)`

A pooled shared-faction composition guard is also required. Factions must contribute at least one eligible territorial window in at least one campaign of each profile. At least 20 pooled shared-faction eligible windows are required per profile, and pooled shared-faction SFO rate must exceed pooled shared-faction vanilla rate. Otherwise mechanistic nomination remains blocked as composition-unresolved.

Even if both checks pass, the result earns mechanism-selection review only. It does not authorize SFO-row copying, application DB mutation, or a project-owned planner.

## Recovery

Recovery is deprioritized because both existing campaigns are below the frozen positive signal threshold: vanilla 0.157895, SFO 0.142857. Continue recording it opportunistically; do not request extra owner runs solely for recovery unless a future cohort crosses the pre-existing threshold.

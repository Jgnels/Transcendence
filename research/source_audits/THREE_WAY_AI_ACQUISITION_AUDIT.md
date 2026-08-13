# Three-Way AI Acquisition Audit — v0.1B

**Audit date:** 2026-07-29  
**Game baseline:** vanilla WH3 v8.1.1 build 48122.4194776  
**Evidence policy:** table/file membership is `OBSERVED`; behavior inferred only from names is `HYPOTHESIS`; behavior read from Lua state-mutation calls is `SUPPORTED` but still not proof that every path executes in every campaign.

## Sources frozen

| Source | Workshop ID | Artifact | Bytes | SHA-256 | Role |
|---|---:|---|---:|---|---|
| DeepWar AI | 2978779730 | owner-supplied PFH5 pack | 266,882 | `f02bd8b5a70f899a8b4827af41da3231c71a7f595c06442177ec70f3fd407d50` | reference environment |
| Hecleas AI Overhaul | 2905096541 | owner-supplied PFH5 pack | 560,184 | `5945102b4eac8ed73065bcc054d935f878d4ffd2b4af191ed4a15b0c31abedf8` | reference environment |
| SFO: Grimhammer III extracted audit | 2792731173 | owner-supplied DB/script/text ZIP | 3,723,908 | `0119959f7999844bc49b47bd41d53110ad9a83b6f89478e1bf2199b8c65a828f` | optional compatibility profile |

Raw artifacts remain outside Git. The repository contains only hashes, paths, classifications, and project-owned reports.

## Observed scope

### DeepWar

- 18 pack entries, of which 15 are DB table files.
- 14 files are in direct CAI table families; one is campaign difficulty handicap data.
- Concentrated on construction templates, personality budgets/income, strategic components, task generators, domains, and CAI variables.
- No Lua scripts were present in the supplied pack.

**Interpretation:** DeepWar is the narrowest and most native-CAI-focused of the three supplied artifacts. That does not prove its choices are superior, but it makes it a useful reference for parameterized strategic behavior with relatively little unrelated game-system surface.

### Hecleas

- 31 pack entries, of which 28 are DB table files.
- Direct CAI coverage includes decision policies, task management, strategic components, personality variables, budgets, income allocation, construction, campaign AI manager behavior, and military generator ratios.
- It additionally modifies multiple diplomacy families, cultural relations, empire rivalry, and two autoresolve families.
- No Lua scripts were present in the supplied pack.

**Interpretation:** Hecleas is broader than DeepWar and reaches diplomacy and autoresolve as well as strategic CAI. Its greater surface creates more opportunity for holistic behavior changes and more conflict risk.

### SFO extracted audit

- 709 extracted files: 612 DB files, 43 Lua scripts, and 54 localization files.
- 338 distinct DB table families.
- 12 DB files fall into direct native-CAI families, with additional difficulty/potential, battle personality, autoresolve, cultural-relations, and campaign-variable changes.
- 20 of 43 scripts contain at least one detected direct state-mutation call; 23 are mechanic/UI scripts under the conservative pattern classifier.
- SFO's dominant footprint is the environment in which AI acts: units, buildings, effects, recruitment, faction mechanics, technologies, battle data, economy, and caps.

**Interpretation:** SFO is a total environment profile, not a single AI implementation. Some apparent AI performance can arise from changed incentives, mechanic bypasses, direct bonuses, scripted recovery, or challenge-generation events rather than improved planning.

## Confirmed scripted mechanisms in the supplied SFO source

The audit found supported examples of:

- AI Bretonnian characters receiving vow progression by rank rather than solving the player-facing vow process.
- Human-only Bretonnian peasant-economy penalties, producing asymmetric mechanic handling.
- scripted horde re-emergence with a chance gate and placement selected near a human faction's high-ranked general;
- direct AI Skaven region transfer and treasury support when repopulating ruins;
- direct diplomacy mutation in the Empire/High Elf intrigue extension;
- effect-bundle application, character spawning, teleports, and other bounded campaign-state interventions;
- effectively removed ordinary additional-army upkeep in the supplied supply-lines script.

These mechanisms must be labeled as `MECHANIC_BYPASS`, `DIRECT_BONUS`, `SCRIPTED_RECOVERY`, `PLAYER_PROXIMITY_CHALLENGE`, or another explicit fairness class rather than being reported as intelligence.

## Overlap and conflict surface

| Pair | Shared table families |
|---|---:|
| DeepWar ↔ Hecleas | 10 |
| DeepWar ↔ SFO | 2 |
| Hecleas ↔ SFO | 5 |
| Shared by all three | 1 |

The table family shared by all three is:

- `cai_task_management_system_task_generator_groups_generators_junctions_tables`

DeepWar and Hecleas also overlap in construction templates, personality budget and income allocation, strategic components, multiple task-generator variable families, and `cai_variables_tables`. Loading both is therefore not a clean additive combination. Row-level conflicts remain `UNVERIFIED` until pinned schemas decode primary keys and values.

## Acquisition decisions

| Source | Decision | Reason |
|---|---|---|
| DeepWar | `REFERENCE_ONLY` | strong native-CAI comparison; no license/source permission established for code/data reuse |
| Hecleas | `REFERENCE_ONLY` | broad strategic/diplomatic comparison; overlapping tables and no reuse permission established |
| SFO | `OPTIONAL_PROFILE_ONLY` | primary owner environment but too broad and update-sensitive to become a core dependency |

No third-party row or script is copied into Transcendence. Useful mechanisms are restated as project-owned hypotheses and tested through project-owned contracts.

## Experiments promoted from the audit

1. **Task-generator ablation:** compare objective quality with parameter families inspired separately by DeepWar and Hecleas.
2. **Budget allocation sensitivity:** measure army availability, concentration, and recovery without conflating extra resources with better planning.
3. **Diplomacy layer isolation:** evaluate Hecleas-style diplomacy families independently from strategic movement.
4. **Mechanic-bypass ledger:** every SFO-specific AI accommodation must state whether it bypasses a player mechanic, grants resources, creates units, transfers territory, or changes planner inputs.
5. **Conflict guard:** no runtime profile may enable two row-writing compatibility layers for the same table family without an explicit merged profile.
6. **Unknown-version fallback:** changed pack hashes default to shadow-only or generic fallback until recertified.

## Remaining uncertainty

- DB row semantics and exact value differences need pinned WH3 schemas.
- No supplied source proves control over ordinary battle AI orders.
- No live campaign comparison has yet measured behavior under vanilla, DeepWar, Hecleas, or SFO.
- SFO's full original pack hash was not supplied; the frozen hash identifies only the extracted audit ZIP.

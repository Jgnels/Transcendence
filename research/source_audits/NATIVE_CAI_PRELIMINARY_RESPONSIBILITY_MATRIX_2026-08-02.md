# Native CAI Reconciliation — Preliminary Responsibility Matrix

**Status:** PRELIMINARY. This is not gate closure.  
**Reason:** primary CA sources establish several native responsibilities, but exact 8.1 rows and mod deltas are still pending owner-local exports.

| Responsibility | Preliminary disposition | Evidence state / reason |
|---|---|---|
| native task generation | `ALREADY_NATIVE` | CA explicitly documents generation and multiple generator contribution |
| same-target/type batching | `ALREADY_NATIVE` | CA explicitly documents batching during allocation |
| task-to-army pairing | `ALREADY_NATIVE` | CA explicitly says tasks and armies are paired during allocation |
| turn-distance-aware priority | `ALREADY_NATIVE` | CA documents distance-in-turns priority modification before assignment |
| stance-aware movement cost in priority | `ALREADY_NATIVE` | CA documents tunneling/forced-march consideration |
| recruitment-aware resourcing | `ALREADY_NATIVE` | CA documents recruiting when no sufficient force exists and recruitment-time/distance inputs |
| Patch 8.1 turn-dependent priority | `ALREADY_NATIVE` behavior / `UNAVAILABLE_OR_UNVERIFIED` exposure | 8.1 behavior is official; exact modder surface unknown |
| v0.2E explicit front/pressure/rival/fairness metrics | `PROJECT_SHOULD_MEASURE` | independent evaluation remains useful; no controller need shown |
| v0.2F bounded portfolio | `PROJECT_SHOULD_MEASURE` | native owns task priority; project representation useful for coverage diagnosis |
| v0.2F critical overflow | `PROJECT_SHOULD_MEASURE` | useful metric for dropped urgent fronts; native equivalent unproven |
| v0.2F aggression veto | `PROJECT_SHOULD_MEASURE` | useful overextension/suicidality metric; controller necessity unproven |
| v0.2G deterministic geometric allocator | `PROJECT_SHOULD_MEASURE` | application use is disfavored because native uses richer movement/strength/recruitment information |
| v0.2G recovery protection | `PROJECT_SHOULD_MEASURE` | native recovery policy unverified; project threshold uncalibrated |
| v0.2G one-army reserve | `PROJECT_SHOULD_MEASURE` | native reserve policy unverified; floor=1 uncalibrated |
| v0.2G exclusive assignment | `PROJECT_SHOULD_MEASURE` | native exclusivity `UNKNOWN_ENGINE_INTERNAL`; no need to control yet |
| v0.2G 2–4 turn commitment | `PROJECT_SHOULD_MEASURE` | uncalibrated project hypothesis; native memory `UNKNOWN_ENGINE_INTERNAL` |
| v0.2G 0.15 reassignment margin | `PROJECT_SHOULD_MEASURE` | uncalibrated project hypothesis; native hysteresis `UNKNOWN_ENGINE_INTERNAL` |
| v0.2H query/capability catalog | `PROJECT_SHOULD_MEASURE` | durable research/certification infrastructure; assignment coupling should be removed later only under a separate implementation gate |
| v0.2H authority firewall | `PROJECT_SHOULD_MEASURE` | project safety/evidence infrastructure, not native planner replacement |
| v0.2I assignment-derived bridge | `UNAVAILABLE_OR_UNVERIFIED` and `PAUSED` | historical transport evidence preserved; no current architecture need to continue it |
| native DB corrections | `TUNABLE_NATIVE` candidate | exact rows/keys/deltas pending schema and export reconciliation |
| bounded diplomacy/rival scripts | `SCRIPT_CORRECTABLE` candidate only | must be justified by a measured native gap; existing prior art is not proof of coordinated blocs |

## Promotion rule

No `PROJECT_MUST_OWN` disposition is justified yet. A responsibility can receive that label only after the gate's native-first falsification ladder fails on a preregistered observable requirement.

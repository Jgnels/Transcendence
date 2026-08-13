# Gate 0 Segment — Campaign Strategic/Theater Priority Portfolio v0.2F

## Result

**CLOSED OFFLINE.** v0.2F converts the frozen v0.2E observer-safe campaign challenge envelope into a deterministic bounded strategic/theater priority portfolio while preserving `NO_ORDERS` and application `PROHIBITED`.

## Implemented

- front stabilization and siege-relief coverage priorities;
- field-force recovery protection;
- coherent visible-rival containment without coordination claims;
- fragmented-pressure aggregation rather than war-count reward;
- strategic reserve and low-pressure consolidation;
- six-record portfolio bound;
- explicit critical overflow preserving all omitted critical source IDs;
- one-aggressive-priority channel;
- crisis and total-force-recovery aggression veto;
- stale/forged v0.2E challenge rejection;
- CLI, smoke integration, deterministic frozen artifacts, and runtime-surface safety tests.

## Adversarial matrix

12/12 scenarios pass and 6/6 metamorphic checks pass. Coverage includes low pressure, coherent rival, fragmented rivals, exposed front, covered siege, mixed recovery/defense, all-force recovery, seven-critical-front overflow, visible nonwar assets, partial rival, coherent-rival-plus-crisis, and bounded many-front pressure.

Metamorphic checks: hidden enemy injection, player→NPC relabel, input order, coordinate translation, uniform strength scaling, and an extra empty war edge.

## Observed and synthetic result

Observed Reikland turns 4–6 remain `CONSOLIDATE_AND_RESERVE`; turn 7 becomes `COHERENT_RIVAL_CONTAINMENT` only when the frozen visible Marienburg evidence appears. The synthetic late-game case remains `CRISIS_STABILIZATION` and simultaneously preserves siege-relief coverage, recovering-force capacity, and strategic reserve while new aggressive commitment is vetoed.

## Performance and regression

- SyntheticLab: 126 tests passed.
- Runtime Probe: 141 tests passed.
- Total direct tests: 267.
- 500-asset portfolio evaluation repeated 10 times with one digest; mean ~0.0640 s, max ~0.0957 s in the build environment.

## Frozen identities

- portfolio result digest: `13bd4e418a4056e570a656c6821ee002412c8e3d90f32d61ba2cf333538c5c22`;
- portfolio artifact SHA-256: `108bc667a676af3311c453ce24332677b3b53c38ae1de94e893b59ffc16cb0e0`;
- matrix result digest: `e1c1b8408e3b405bbedbcef01d1802e10206a71c38a9264337aa8cdb62959125`;
- matrix artifact SHA-256: `01558a39ec7631a3e1eae77af1d208f019909b81d4a6214b832c7bbd15d1d13b`;
- scenario suite SHA-256: `5279fa12c29dbbb67015cde4cdb613c66ed25086f67a46ae026c32586b9319b7`.

## Defects found and corrected during the gate

- Directly assigning armies from a campaign snapshot would have skipped global priority arbitration and allowed local assignments to starve strategic obligations; v0.2F inserts a bounded project-owned portfolio before assignment.
- Treating each war edge as an independent pressure objective could multiply aggression without visible hostile evidence; fragmented pressure is aggregated and an empty-war-edge metamorphic test is invariant.
- More critical front obligations than the six-record budget could have been silently dropped; `CRITICAL_STRATEGIC_OVERFLOW` preserves 100% of critical source IDs.
- A coherent visible rival could otherwise retain an aggressive channel during an exposed-front crisis; crisis and total-force recovery now veto new aggressive commitment.
- Recovery could be counted as available offensive capacity; all-force recovery now blocks new aggressive commitment and mixed recovery remains explicitly protected.
- A stale or forged v0.2E challenge envelope could otherwise be rebound to a different scenario; exact recomputation is required.
- The initial overflow diagnostic undercounted unselected noncritical candidates because overflow source records were subtracted from the wrong population; the metric now counts actual noncritical candidates not directly selected, with a frozen regression fixture.

## Still unverified

Army-to-theater assignment, multi-turn commitment persistence, campaign path feasibility, command authority, acknowledgement, execution, causal outcomes, economy/recruitment recovery, diplomacy/blocs, SFO longitudinal strategy, and owner enjoyment.

## Next gate

Build deterministic theater-to-army assignment with exclusivity, recovery/reserve protection, resource-conflict disclosure, and a temporal commitment lifecycle that prevents strategic thrashing. Keep it offline and `NO_ORDERS` until a separately frozen campaign action-authority requirement genuinely justifies live work.

# Gate 0 Segment — Campaign Strategic Feasibility and Action Authority v0.2H

## Result

**CLOSED OFFLINE.** v0.2H converts v0.2G shadow assignments into deterministic, bounded, read-only query plans and freezes the campaign action-authority boundary without issuing or enabling campaign orders.

## Implemented

- exact v0.2G force-allocation digest and source-scenario binding;
- stable actor binding requirements for character CQI and military-force CQI;
- documentation-derived query catalog for actor lookup, active stance, point reachability, settlement reachability, long-horizon reachability, and siege context;
- explicit separation of documented query availability from owner-runtime observation;
- region-to-settlement reachability without attack-target promotion;
- faction-centroid point reachability without character/settlement/attack-target promotion;
- bounded observation-packet schema and fail-closed adjudicator;
- stale-turn, foreign-query, duplicate/cardinality, malformed-result, and authority-promotion rejection;
- explicit prohibited mutation-surface inventory;
- CLI/smoke integration, adversarial matrix, frozen cross-evidence artifact, and runtime-surface static checks.

## Preserved Reikland result

Turns 4–6 have no v0.2G force assignment and therefore generate no feasibility query plan. Turn 7 generates one historical query plan for `force:65`, character CQI `120`, force CQI `65`, current default stance, and the observer-safe Marienburg visible-asset centroid. It contains eight unobserved read-only query records. It does **not** select a Marienburg army or settlement and does not claim the centroid is an attack target.

## Adversarial matrix

5/5 query-plan cases and 5/5 metamorphic checks pass. Synthetic observation adjudication preserves `PROHIBITED` application authority, no execution, and no causal outcome even when every query is supplied as observed. Stale-turn, foreign-query, and authority-promotion attacks fail closed.

Coverage includes exact region/settlement queries, faction-centroid point-only behavior, siege context without assault-legality promotion, missing-stance abstention, reserve capacity with no invented destination, hidden-enemy invariance, player-label invariance, input-order invariance, coordinate translation, and uniform strength scaling. Direct regression is 150/150 SyntheticLab plus 145/145 Runtime Probe tests. The complete matrix repeated 20 times with one digest (mean 0.0363 s, max 0.0421 s in the build environment).

## Documented interface audit

WH3 model-hierarchy documentation exposes read/query surfaces for character/force CQI lookup and point/settlement reachability, including stance-specific and long-horizon variants. Military-force state exposes active stance and stance activation eligibility. Region and garrison interfaces expose settlement resolution and siege context. The episodic/campaign-manager side separately exposes movement/attack and other model-mutating surfaces. v0.2H preserves that separation and imports no runtime adapter.

## Still unverified

Owner-build execution of these campaign queries, exact query behavior under SFO, route geometry, zones of control, interception, post-query staleness, stance transition semantics, settlement assault/occupation legality, movement/attack issue, command acceptance, acknowledgement, execution, causal strategic outcomes, and owner experience.

## Next gate

Prepare one batched **read-only campaign feasibility observation** for the next suitable campaign state rather than recreating historical turn 7. The live packet must evaluate only v0.2H-generated query IDs for current shadow assignments and must contain no mutation call. A later, separately authorized sandbox would still be required before any campaign order can be issued.

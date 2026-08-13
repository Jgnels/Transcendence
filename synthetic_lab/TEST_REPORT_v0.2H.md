# SyntheticLab Test Report v0.2H

- 150/150 direct SyntheticLab tests pass.
- Frozen campaign strategic-feasibility envelope reproduces current implementation exactly and byte-for-byte across repeated CLI generation.
- 5/5 strategic-feasibility adversarial cases pass.
- 5/5 metamorphic checks pass: hidden-enemy injection, player-label relabel, input order, coordinate translation, and uniform strength scaling.
- Synthetic observation adjudication observes every planned query while retaining `NO_ORDERS`, application `PROHIBITED`, and no acknowledgement/execution/causal-outcome promotion.
- Forged authority, stale-turn, and foreign-query observation packets fail closed.
- Faction-centroid targets remain point-only and cannot become character, settlement, or attack targets.
- Region targets may expose the exact region settlement interface for documented reachability queries without promoting a concrete attack target.
- Ambiguous `GARRISON_RESIDENCE_SCRIPT_INTERFACE.can_assault` remains catalogued but is not used as generic actor-target attack legality.
- Each plan has a bounded unique query set; historical preserved v0.2G evidence contains one turn-7 plan with 8 planned queries and zero live query results.
- The complete 5-case/5-metamorphic matrix repeated 20 times with one output digest; mean 0.0363 s, min 0.0333 s, max 0.0421 s in the build environment.

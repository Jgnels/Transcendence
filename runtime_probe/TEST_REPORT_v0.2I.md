## v0.2I-r2 parser-contract hotfix addendum

Target direct regression count: **304** = 150 SyntheticLab + 155 Runtime Probe. New coverage requires every static event emitted by the dedicated campaign-feasibility Lua to be accepted by the shared parser and verifies a synthetic campaign-feasibility session containing both r1 diagnostic events can be summarized. The game-side feasibility pack must remain byte-identical to r1 (`86843cb3bbed02ddb99f90fe084b45ca784fc0e5e70d03dfea99cab613b2236d`).

# Runtime Probe Test Report v0.2I

## v0.2I-r1 hotfix addendum

Target regression count is now **152 Runtime Probe tests** (plus 150 SyntheticLab = 302 direct tests). New coverage freezes the idle-map timer correction: real UI timer required, old model-time feasibility poll forbidden, immediate poll required, one-shot poll telemetry required, and the preparation artifact must match the rebuilt dedicated probe. The first owner-runtime v0.2I attempt is preserved as a limiting result rather than silently discarded.

- Direct Runtime Probe regression: **151/151 PASS**.
- New coverage verifies the campaign-feasibility pack is nonmutating and first-tick capable; current-plan/request generation is deterministic; a complete synthetic live packet reconstructs and adjudicates through the exact saved plan; foreign query IDs fail closed; and SFO environment capture accepts one explicitly named decorated feasibility-probe entry.
- Full pack builder now produces six deterministic uncompressed PFH5 probe packs; the historical five remain unchanged in purpose.
- Dedicated campaign-feasibility pack SHA-256 at this source state: `ccc5b6d5d73386d0814e2f89e02720abdf26772ed4af739bf4c4bea72ee4deea`.

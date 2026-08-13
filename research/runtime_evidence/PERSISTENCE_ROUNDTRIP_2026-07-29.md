# Gate 0 Persistence Round-Trip Report v0.1G

**Date:** 2026-07-29  
**Evidence:** `REPLICATED`

## Result

A single project-owned namespaced integer survived a real WH3 save/reload cycle in a disposable pure-vanilla Karl Franz Immortal Empires campaign.

The exact persistence pack was used in both phases:

`71bf96e4fca54d16e323f5eef9766a6098c6ea4b9416b33aa012317d5f682bd2`

### Write phase

- new game: `true`;
- multiplayer: `false`;
- previous value found: `false`;
- transition: `0 → 1`;
- raw log SHA-256: `9625cec56ff01c33422f340dbb66eda1c2de2067e793c107f677e173b779eb69`;
- evidence manifest SHA-256: `423b4da078a1bcae54cbad62301c84ee901c1e2c9d7e2a05cb77d03e9a05695b`.

### Reload phase

- new game: `false`;
- multiplayer: `false`;
- previous value found: `true`;
- transition: `1 → 2`;
- raw log SHA-256: `97e0be11a777dd43c2cfa65f69406422a0a7a3ba4a7ff71b3aced723c1782a46`;
- evidence manifest SHA-256: `01ca50da36e137853dd29ac960ceeb545e4aa1fd19658ae708c8421fc567807c`.

Both sessions were persistence-only, used the same campaign and faction, had successful loader entrypoints, contained one state record, and reported no capability failure.

## Verifier

Owner-exported verifier result digest:

`6b9445f51d106558b1dd23e808ef4e3b9554c130ac92f7fa7672d68fc2f5e3da`

v0.1G re-verification result digest using uploaded filenames:

`e824800620a019a760772e8b219b89d9dd4eca5185ba9b56623481393da82d0c`

Stable semantic digest:

`b996cc93f07275bc8d36fa428baa5e055ee03ba19bebc113175beedf048198bb`

The different transport result digest exposed a filename-sensitivity defect. v0.1G preserves the transport digest for traceability and adds a semantic digest that excludes uploaded filenames while retaining evidence hashes, pack identity, timestamps, collection identifiers, states, checks, and warnings.

## Capability promotion

Promoted:

- one project-owned namespaced integer can be written and recovered across save/reload in the tested environment: `CONTROL`, evidence `REPLICATED`;
- exact-pack two-phase persistence verification: `CONTROL`.

Not promoted:

- arbitrary save-state modification;
- migration safety across future key schemas;
- compatibility with valued saves;
- campaign order authority;
- objective persistence design;
- SFO compatibility.

## Gate effect

The Gate 0 disposable-save persistence segment is closed. The whole Gate 0 remains open for expanded planner observations, rollback proof, private baseline completion, campaign influence/control, battle feasibility, UI capability, and SFO certification.

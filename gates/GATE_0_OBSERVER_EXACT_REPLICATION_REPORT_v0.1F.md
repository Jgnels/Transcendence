# Gate 0 Exact Observer Replication Report — v0.1F

## Segment result

**Closed:** strict exact-pack campaign observer replication.

**Gate 0 remains open:** save/reload persistence, expanded observation fields, private baseline completion, campaign/battle/UI capability probes, and owner-experience artifacts remain.

## Exact inputs

| Input | SHA-256 |
|---|---|
| corrected observer pack | `0c1dd8940a697a2d840876f08092ba02f988170e90c5f77b6f934ac15c79f173` |
| exact run 1 raw log | `c12afd4fce48708990e251ba271cb877b07f3163749960d68cadb9eed51f925c` |
| exact run 1 evidence manifest | `46f04d7789173395256fee3fe02f059a825f837786553db4fcfa0272fc9e6d07` |
| exact run 1 uploaded summary | `f605b42a2207b6f4f73a6c4a03c608322fac96f8d965ac4381517b837d502e46` |
| exact run 2 raw log | `c12afd4fce48708990e251ba271cb877b07f3163749960d68cadb9eed51f925c` |
| exact run 2 evidence manifest | `7bd09032bf545ed9743398b1ef7d138dcddf613f9a72d506a44d856b2f3bc9dc` |
| exact run 2 uploaded summary | `556ce4e8334d13fd3e8a6471b45e7d1d9129c87818dd22af1c9cbc2c332aeac4` |

The private raw logs and path-bearing manifests remain outside Git.

## Replication result

Both collections were fresh pure-vanilla Karl Franz Immortal Empires turn-1 sessions. Both produced:

- one valid observer session;
- 55 structured records;
- two complete snapshots;
- zero capability failures;
- zero within-snapshot duplicate defects;
- eight expected cross-snapshot re-observations;
- successful filename-matched loader entrypoints;
- the same first-tick/local-turn-start lifecycle delta;
- `LOCAL_FACTION_TURN_START` as canonical planner timing.

The two 10,224-byte raw logs are byte-identical:

`c12afd4fce48708990e251ba271cb877b07f3163749960d68cadb9eed51f925c`

Shared semantic digest:

`947d9aa1815485a7ba844d79b20e680ea8e36ed5eeb108a8fc5692e7e2bfb6f7`

Strict verifier digest:

`4bd1ad7bf39e086fa26d1dad3265da1a487db437b4d51b2d5715a4a2203326f`

Evidence label: `REPLICATED`.

## Defect found and corrected

The v0.1E verifier treated different raw hashes as evidence of independent sessions. That assumption is invalid for deterministic probes: two genuinely separate runs may produce identical bytes.

v0.1F establishes independence through distinct evidence collections:

- different collection timestamps;
- different evidence-manifest hashes;
- different derived collection identifiers;
- each manifest binding to the supplied raw log hash.

Byte identity is now reported as a deterministic replication result rather than a failure.

## Capability promotions

Retained/promoted as `OBSERVE` with `REPLICATED` evidence:

- script-only campaign pack loading;
- project `ModLog` output;
- first-tick callback;
- local-faction-turn-start observation;
- local army and region enumeration;
- game-interface-filtered foreign character and region enumeration.

Not promoted:

- saved-value persistence;
- campaign objective or order authority;
- order acknowledgement or outcome;
- campaign influence/control;
- battle observation/control;
- UI authority;
- gameplay or AI improvement.

## Persistence preparation

The next probe remains separate and opt-in. v0.1F strengthens it with:

- `WRITE` versus `RELOAD` phase labels;
- campaign, faction, new-game, multiplayer, turn, and key-version fields;
- an exact-pack two-phase verifier;
- collection-manifest binding;
- isolated-session checks;
- required chain `0 → 1 → 2`;
- one-command phase collection and final verification helpers.

New persistence pack SHA-256:

`71bf96e4fca54d16e323f5eef9766a6098c6ea4b9416b33aa012317d5f682bd2`

The observer pack is unchanged.

## Smallest unavoidable next task

Use a disposable pure-vanilla campaign:

1. install and enable only the v0.1F persistence probe;
2. start a fresh Karl Franz campaign and reach first tick;
3. manually save the campaign, exit, and collect `WRITE` evidence;
4. restart WH3 and load that exact save;
5. exit after first tick and collect `RELOAD` evidence;
6. run the strict verifier.

No valued save should be opened while the persistence pack is enabled.

# Observer Replication Evidence — 2026-07-29

## Status

`SUPPORTED_CROSS_REVISION`

Two independent pure-vanilla Karl Franz Immortal Empires sessions produced the same semantic observer result. The second run also verified the inert filename-matched loader entrypoint.

This does **not** yet satisfy the stricter Reality Gate requirement for two clean sessions using the exact same observer pack hash:

- run 1 used `33f3f9cf43441470348e28e4ea03e5091ac47dd8ae99e17ba2ab2662d9db7abd` (v0.1C);
- run 2 used `0c1dd8940a697a2d840876f08092ba02f988170e90c5f77b6f934ac15c79f173` (v0.1D).

The source change between them was limited to the inert filename-matched loader entrypoint, but pack identity is still different and the acceptance rule is not weakened.

## Frozen private-input hashes

| Artifact | Run 1 | Run 2 |
|---|---|---|
| raw `lua_mod_log.txt` | `ddf462130e6551c034ddd5e79dfc916fba0a133cfa0cf6ef715e6df7afd1f9f7` | `c12afd4fce48708990e251ba271cb877b07f3163749960d68cadb9eed51f925c` |
| evidence manifest | `96e388d0013ca182113e89598d99efdaae3b79fe789e8da1e0b70ff0ab73b165` | `46f04d7789173395256fee3fe02f059a825f837786553db4fcfa0272fc9e6d07` |
| uploaded parser summary | `5177ee7ba8db6214e3cd605d035e73912e2708679e72f2b3b9ee60a197d51a6b` | `f605b42a2207b6f4f73a6c4a03c608322fac96f8d965ac4381517b837d502e46` |
| observer pack | `33f3f9cf43441470348e28e4ea03e5091ac47dd8ae99e17ba2ab2662d9db7abd` | `0c1dd8940a697a2d840876f08092ba02f988170e90c5f77b6f934ac15c79f173` |

Raw logs, manifests, used-mod files, and local paths remain outside Git.

## Shared semantic result

Both sessions contained:

- campaign `wh3_main_combi`;
- local faction `wh_main_emp_empire`;
- turn 1;
- one observer session;
- 55 structured records;
- two snapshots;
- zero capability failures;
- zero within-snapshot duplicates;
- eight expected cross-snapshot re-observations;
- the same first-tick versus local-turn-start visibility delta;
- the same canonical planner phase: `LOCAL_FACTION_TURN_START`.

Shared semantic digest:

```text
947d9aa1815485a7ba844d79b20e680ea8e36ed5eeb108a8fc5692e7e2bfb6f7
```

Cross-run verifier digest:

```text
1470cd524f3c24a44d7232b96d25646c26eda5bbb675a1af7490edeee428f0c5
```

## Defect found

The v0.1D `result_digest` included source filenames and structured-record line positions. Upload renaming and unrelated loader output could therefore change the digest even when every `TRANS_PROBE` record was semantically identical.

v0.1E preserves the positional result digest for evidence traceability and adds a separate `semantic_digest` that removes:

- source filename;
- session start line;
- snapshot begin and end lines;
- digest fields themselves.

This permits honest semantic comparison without discarding raw evidence identity.

## Loader result

Run 1 reported the filename-matched function as missing. Run 2 reported:

```text
Executing mod function transcendence_observer_probe()
transcendence_observer_probe() executed successfully
```

The v0.1D loader correction is therefore `OBSERVED`.

## Capability result

| Capability | Result |
|---|---|
| observer behavior across semantically equivalent revisions | SUPPORTED |
| corrected loader entrypoint | OBSERVED |
| two sessions using exact same pack hash | UNVERIFIED |
| saved-value persistence through save/reload | UNVERIFIED |
| campaign objective/order authority | UNVERIFIED |
| acknowledgement or outcome control | UNVERIFIED |

## Smallest remaining observer task

Run the unchanged observer pack with SHA-256:

```text
0c1dd8940a697a2d840876f08092ba02f988170e90c5f77b6f934ac15c79f173
```

one more time in a fresh pure-vanilla Karl Franz campaign. The v0.1E collector records the installed pack hash directly, so that run and run 2 can close strict same-pack replication.

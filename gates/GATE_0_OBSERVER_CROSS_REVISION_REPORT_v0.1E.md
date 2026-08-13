# Gate 0 Observer Cross-Revision Segment Report — v0.1E

## Segment result

**Closed:** independent observer behavior consistency across v0.1C and v0.1D, plus live verification of the v0.1D loader entrypoint.

**Still open:** strict Reality Gate observer replication requires two clean sessions using the exact same installed observer pack SHA-256. Only one session currently exists for the corrected v0.1D hash.

Gate 0 overall remains open.

## Inputs

| Input | SHA-256 |
|---|---|
| run 1 raw log | `ddf462130e6551c034ddd5e79dfc916fba0a133cfa0cf6ef715e6df7afd1f9f7` |
| run 1 evidence manifest | `96e388d0013ca182113e89598d99efdaae3b79fe789e8da1e0b70ff0ab73b165` |
| run 1 uploaded summary | `5177ee7ba8db6214e3cd605d035e73912e2708679e72f2b3b9ee60a197d51a6b` |
| run 2 raw log | `c12afd4fce48708990e251ba271cb877b07f3163749960d68cadb9eed51f925c` |
| run 2 evidence manifest | `46f04d7789173395256fee3fe02f059a825f837786553db4fcfa0272fc9e6d07` |
| run 2 uploaded summary | `f605b42a2207b6f4f73a6c4a03c608322fac96f8d965ac4381517b837d502e46` |

The raw inputs remain outside Git.

## Repeated observations

Both runs produced:

- one valid observer session;
- 55 structured records;
- two complete snapshots;
- zero capability failures;
- zero within-snapshot duplicate defects;
- eight expected cross-snapshot re-observations;
- identical visible-entity and local-entity counts;
- the same lifecycle delta;
- `LOCAL_FACTION_TURN_START` as canonical planner timing.

Shared semantic digest:

`947d9aa1815485a7ba844d79b20e680ea8e36ed5eeb108a8fc5692e7e2bfb6f7`

Cross-run verifier digest:

`1470cd524f3c24a44d7232b96d25646c26eda5bbb675a1af7490edeee428f0c5`

## Pack revisions

| Run | Pack SHA-256 | Loader result |
|---|---|---|
| 1 | `33f3f9cf43441470348e28e4ea03e5091ac47dd8ae99e17ba2ab2662d9db7abd` | filename-matched entrypoint missing |
| 2 | `0c1dd8940a697a2d840876f08092ba02f988170e90c5f77b6f934ac15c79f173` | filename-matched entrypoint executed successfully |

The source difference is intentionally inert, but exact pack identity differs. The segment is therefore `SUPPORTED_CROSS_REVISION`, not `REPLICATED`.

## Defect corrected

The prior parser's single digest included source filename and record line positions. A log upload rename or unrelated loader line could change it without changing any structured observation.

v0.1E adds:

- transport-sensitive `result_digest`;
- transport-invariant `semantic_digest`;
- exact-pack replication verifier;
- evidence-manifest v2 installed-pack hashes;
- staged-versus-installed hash agreement;
- used-mod and latest-install-manifest hashes.

## Authority result

No new game authority is claimed. The evidence proves observation only.

Still unverified:

- saved-value persistence;
- campaign objective or order authority;
- acknowledgement or outcome observation;
- campaign influence/control;
- battle observation or control;
- UI authority.

## Smallest remaining live step

Apply v0.1E, install the unchanged observer pack, verify its SHA-256 is:

`0c1dd8940a697a2d840876f08092ba02f988170e90c5f77b6f934ac15c79f173`

and perform one additional fresh pure-vanilla Karl Franz turn-1 run. The resulting evidence-manifest v2 will directly record the installed hash. Run 2 plus that new run can then close strict exact-pack observer replication.

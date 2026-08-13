# Runtime Probe Test Report — v0.1F

## Result

All offline tests passed.

- SyntheticLab tests: **18/18**
- Runtime-probe tests: **20/20**
- Total: **38/38**

## New regression coverage

v0.1F adds tests proving that:

- byte-identical deterministic observer logs can satisfy replication when collection evidence is distinct;
- reusing one collection manifest twice does not prove independence;
- an evidence manifest must bind to the supplied raw log hash;
- exact observer pack identity remains mandatory;
- a fresh isolated persistence `WRITE 0→1` followed by `RELOAD 1→2` passes;
- a non-fresh write phase is rejected.

## Actual owner evidence

The exact-pack observer verifier ran twice against the two owner collections and produced byte-identical verifier output.

- status: `REPLICATED`
- observer pack: `0c1dd8940a697a2d840876f08092ba02f988170e90c5f77b6f934ac15c79f173`
- shared raw log: `c12afd4fce48708990e251ba271cb877b07f3163749960d68cadb9eed51f925c`
- shared semantic digest: `947d9aa1815485a7ba844d79b20e680ea8e36ed5eeb108a8fc5692e7e2bfb6f7`
- verifier result digest: `4bd1ad7bf39e086fa26d1dad3265da1a487db437b4d51b2d5715a4a2203326f6`
- serialized verifier SHA-256: `973b4008170aac421bc1e1cbe7513ed0b8167a8dc9fb863e80c394b403bfa816`

## Deterministic pack builds

Two independent builds were byte-identical.

| Artifact | SHA-256 |
|---|---|
| observer pack | `0c1dd8940a697a2d840876f08092ba02f988170e90c5f77b6f934ac15c79f173` |
| persistence pack | `71bf96e4fca54d16e323f5eef9766a6098c6ea4b9416b33aa012317d5f682bd2` |
| serialized build manifest | `4ca6df69c6a4d5f854ec7fca17a8ebea480c5f3deb61f7944c3a05d42441577f` |
| aggregate build result digest | `19a9ff274cd5656e3c056c74d52246f9a03b4aecfaa2ea2dac534fc732f6a960` |

## Performance

Construction environment:

| Operation | Elapsed | Maximum RSS |
|---|---:|---:|
| 20 runtime tests | 0.53 s | 110,796 KB |
| 18 SyntheticLab tests | 0.64 s | 111,452 KB |
| probe build 1 | 0.52 s | 110,336 KB |
| probe build 2 | 0.53 s | 110,428 KB |

## Defects corrected

1. **False independence requirement:** v0.1E rejected byte-identical logs because it required different raw hashes. v0.1F verifies distinct collection identities instead.
2. **Installed-versus-active ambiguity:** collector schema v3 records probe kinds actually loaded in the log.
3. **Weak persistence chain:** persistence records now include phase and environment fields; the verifier requires a fresh write, same-environment reload, and exact `0→1→2` chain.
4. **Persistence installation instructions:** installation manifests and terminal output are now mode-specific rather than always telling the owner to enable the observer.

## Remaining limitation

The new PowerShell persistence collection wrappers could not be executed against Windows/WH3 in the construction container. Their project logic is covered by Python tests and will be exercised by the owner-machine apply and persistence run. No live persistence capability is claimed yet.

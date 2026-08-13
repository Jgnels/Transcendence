# Runtime Probe Test Report — v0.1E

## Scope

Integrate the second real WH3 observer session, distinguish semantic observation consistency from exact-pack replication, harden evidence manifests, and preserve the unchanged read-only observer pack.

## Runtime evidence imported

- run 1 raw log SHA-256: `ddf462130e6551c034ddd5e79dfc916fba0a133cfa0cf6ef715e6df7afd1f9f7`;
- run 2 raw log SHA-256: `c12afd4fce48708990e251ba271cb877b07f3163749960d68cadb9eed51f925c`;
- run 2 summary SHA-256: `f605b42a2207b6f4f73a6c4a03c608322fac96f8d965ac4381517b837d502e46`;
- run 2 evidence-manifest SHA-256: `46f04d7789173395256fee3fe02f059a825f837786553db4fcfa0272fc9e6d07`;
- shared semantic digest: `947d9aa1815485a7ba844d79b20e680ea8e36ed5eeb108a8fc5692e7e2bfb6f7`;
- cross-run verifier digest: `1470cd524f3c24a44d7232b96d25646c26eda5bbb675a1af7490edeee428f0c5`.

## Findings

1. Both sessions produced the same 55 structured observer records and the same canonical lifecycle result.
2. The v0.1D filename-matched loader entrypoint executed successfully in the second run.
3. The sessions used different pack hashes, so the result is `SUPPORTED_CROSS_REVISION`, not strict `REPLICATED`.
4. The prior result digest was transport-sensitive. Filename and unrelated line-position changes could alter it without changing observer semantics.

## Defects corrected

- Added a semantic digest that excludes source filename and structured-record line positions.
- Added a verifier that refuses to promote exact replication without matching installed pack hashes.
- Enhanced evidence-manifest collection with installed/staged pack hashes, used-mod evidence, and latest installation-manifest hash.
- Preserved the transport-sensitive digest for raw evidence traceability.

## Tests

- all 18 SyntheticLab tests;
- 15 runtime-probe tests;
- semantic-digest invariance under filename and non-probe line changes;
- exact-pack identity required for strict replication;
- same verified pack accepted as replicated;
- deterministic pack build and PFH5 parsing;
- observer mutation boundary;
- persistence mutation boundary;
- malformed/private/out-of-order log rejection.

## Deterministic pack outputs

The Lua sources are unchanged from v0.1D:

- observer source SHA-256: `07c28ed752011994f82a8ee5213a095744f491c9f435c426c37ba9546c711736`;
- observer pack SHA-256: `0c1dd8940a697a2d840876f08092ba02f988170e90c5f77b6f934ac15c79f173`;
- persistence source SHA-256: `c6815efa8a2df87b9df57c7a8ac516bb027c92d5cdc47afc184218b4b28a891e`;
- persistence pack SHA-256: `7f46f5594c9fc633109d147062b93dac397738016464f651d72c2cd5f134a82f`;
- aggregate build result digest: `46e3f6cf831f1d56fdda8937156ad7adceece8bf684756ab04a003ffea49fabc`;
- build-manifest SHA-256: `4915d7f4d0c84b1ba0029f8558e2a1350985b7c754e4a96d10ea5e1f06bbf53e`.

Two independent builds were byte-identical.

## Performance

- deterministic build run 1: 3.03 seconds;
- deterministic build run 2: 2.86 seconds;
- integrated validation run 1: 8.79 seconds;
- integrated validation run 2: 8.60 seconds;
- 85 repository files were hashed and verified;
- all 33 tests passed in both integrated validation runs.

## Remaining limitations

- one additional run of exact observer pack hash `0c1dd...` is required;
- save/reload persistence remains unverified;
- required Army Objective Assignment observations remain incomplete;
- no gameplay order, acknowledgement, outcome, campaign control, or battle control is established.

# Runtime Probe Test Report — v0.1D

## Scope

Integrate the first real WH3 observer session, correct evidence interpretation defects, and preserve deterministic pack construction.

## Runtime evidence imported

- raw private `lua_mod_log.txt` SHA-256: `ddf462130e6551c034ddd5e79dfc916fba0a133cfa0cf6ef715e6df7afd1f9f7`;
- original v0.1C summary SHA-256: `5177ee7ba8db6214e3cd605d035e73912e2708679e72f2b3b9ee60a197d51a6b`;
- evidence-manifest SHA-256: `96e388d0013ca182113e89598d99efdaae3b79fe789e8da1e0b70ff0ab73b165`;
- v0.1D parser result digest: `4391fed3eb2a87244e558797625eabdad0f8a4672a7f4073b6305cf271ce4f27`.

## Defects corrected

1. **Cross-snapshot re-observation mislabeled as duplication.**
   The v0.1C parser reported eight duplicate events because stable entities appeared in two different snapshots. v0.1D scopes duplicate detection to one logical snapshot and tracks cross-snapshot repeats separately.

2. **Unstable lifecycle phase treated as potentially canonical.**
   The first-tick snapshot exposed 10 foreign characters and 9 regions; local-faction turn start exposed 13 and 11. The planner timing contract now accepts only `LOCAL_FACTION_TURN_START`.

3. **Generic mod-loader warning.**
   WH3 attempted to invoke a function matching each probe filename. Both scripts now provide an inert filename-matched entrypoint while retaining lifecycle registration at load time.

## Tests

- all 18 SyntheticLab tests;
- previous 10 runtime-probe tests;
- cross-snapshot repeat classification;
- lifecycle delta and canonical timing selection;
- filename-matched loader entrypoints.

## Result

- 18 SyntheticLab tests passed;
- 12 runtime-probe tests passed;
- 30 total tests passed;
- real observer log reparsed successfully;
- true within-snapshot duplicate count: 0;
- expected cross-snapshot repeat count: 8;
- no capability failures.

## Deterministic build outputs

- observer source SHA-256: `07c28ed752011994f82a8ee5213a095744f491c9f435c426c37ba9546c711736`;
- observer pack SHA-256: `0c1dd8940a697a2d840876f08092ba02f988170e90c5f77b6f934ac15c79f173`;
- persistence source SHA-256: `c6815efa8a2df87b9df57c7a8ac516bb027c92d5cdc47afc184218b4b28a891e`;
- persistence pack SHA-256: `7f46f5594c9fc633109d147062b93dac397738016464f651d72c2cd5f134a82f`;
- aggregate build result digest: `46e3f6cf831f1d56fdda8937156ad7adceece8bf684756ab04a003ffea49fabc`;
- build-manifest file SHA-256: `4915d7f4d0c84b1ba0029f8558e2a1350985b7c754e4a96d10ea5e1f06bbf53e`.

Two independent builds were byte-identical.

## Build performance

- run 1: 0.53 seconds, 110,340 KB maximum RSS;
- run 2: 0.51 seconds, 110,404 KB maximum RSS.

## Repeated integrated validation

- validation run 1: 1.64 seconds, 110,996 KB maximum RSS;
- validation run 2: 1.65 seconds, 111,336 KB maximum RSS;
- 79 repository files were hashed and verified in each run;
- all 30 tests passed in each run.

## Remaining limitations

- the corrected loader entrypoint still needs one live verification;
- only one independent observer session exists;
- save/reload persistence remains unverified;
- required Army Objective Assignment observations remain incomplete;
- no gameplay order, acknowledgement, outcome, campaign control, or battle control is established.

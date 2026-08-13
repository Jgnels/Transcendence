# Gate 0 — Action Authority Live Observation Report v0.1S

## Decision

**Ordinary-battle live observation gate: CLOSED.**  
**Authority: `NO_ORDERS`.**  
**Repeat capture required for this gate: NO.**

## Source

- Exact public-safe capture ZIP SHA-256: `a1c03ec12a4c2b70945311fc57b54f978fcca892a37b12d46a5daa6f22ebf579`.
- Exact action-authority pack SHA-256: `3acf60520b60f87f8c18e13532512324cb7a539626996ce19897fad94cf2d25d`.
- Private raw-log SHA-256: `b4f8c4ca9c285018772d50a4eda92f34572f742dd97967bca8229b0a6b3ce951`.
- Private raw-log size: 732,081 bytes.
- Raw log, personal paths, and game artifacts are excluded from the repository.

## Observed result

- one complete ordinary single-player battle session;
- 13 local unit identities;
- 130 selection events;
- 89 game command events;
- 89 action windows;
- 89 selection-bound windows and zero unbound windows;
- 1,287 read-only samples;
- 1,249 reachability `QUERY_TRUE`, 38 `QUERY_FALSE`, zero unavailable;
- 739 movement observations;
- 189 ordered-position matches;
- 443 current-target matches;
- one routing observation and one control-loss observation;
- 45 subsequent-command closes, 43 timeout closes, and one routed close;
- zero project issue attempts;
- zero direct acknowledgements.

## Capability adjudication

Promoted to scoped `OBSERVED`:

- ordinary-battle local selection events;
- selected-unit command-window binding;
- read-only action-state sampling;
- point reachability query availability;
- ordered-position and current-target state matching;
- movement, routing, control-loss, and interruption visibility.

Remain `UNVERIFIED` or rejected:

- command origin;
- direct acknowledgement;
- route completion and formation feasibility;
- leaving-battle and shattered state for this capture;
- project issue, execution, or outcome;
- tactical superiority or casualty improvement;
- broader SFO and battle-type generalization.

## Defect corrected

Two repository/tooling defects were exposed. First, the schema-1 public export did not include a sanitized prepared-session attestation. The exact owner-run verifier result is valid and closes this gate, but preparation checks cannot be independently replayed from the three public documents alone.

v0.1S upgrades future collector exports to schema 2 with a hash-bound, path-free preparation attestation. Second, Windows PowerShell 5.1 emitted the public manifest as UTF-8 with a BOM, while repository JSON validation accepted only BOM-free UTF-8. Validation now decodes `utf-8-sig` while preserving exact evidence bytes. Neither correction requires repeating the completed capture.

## Validation

- Adjudication contract: `ACTION_AUTHORITY_LIVE_ADJUDICATION_V1`.
- Adjudication result digest: `bc4a579e7277507c56b815eccfda9a7049308c7a3a916faea4bc6c2d38af6d49`.
- SyntheticLab tests: 56 passed.
- Runtime Probe tests: 73 passed.
- Total tests: 129 passed.
- Canonical repository hashes: 239 validated.
- Complete validation repeated: twice from the sealed tree.
- Evidence reproduction: byte-identical across two independent builds.

## Remaining uncertainty

The capture establishes read-only observability, not an executable action channel. The safe next repository work is a bounded feasibility envelope that consumes observed query availability while retaining path, formation, issue, acknowledgement, execution, and outcome as unverified.

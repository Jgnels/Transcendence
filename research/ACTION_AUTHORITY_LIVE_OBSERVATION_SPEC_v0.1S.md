# Action Authority Live Observation Specification v0.1S

## Purpose

Adjudicate one exact-pack ordinary single-player battle capture without promoting state correlation into command origin, acknowledgement, causal execution, or outcome.

## Authority

- Runtime authority: `NO_ORDERS`.
- Capture status: `OBSERVED_READ_ONLY_ACTION_AUTHORITY`.
- Adjudication status: `OBSERVED_READ_ONLY_ACTION_AUTHORITY_CALIBRATED`.
- Project issue attempts: exactly zero.
- Direct acknowledgements: exactly zero.
- Outcome attribution: `UNVERIFIED_NOT_ATTRIBUTED`.

## Frozen source identity

- Public-safe ZIP SHA-256: `a1c03ec12a4c2b70945311fc57b54f978fcca892a37b12d46a5daa6f22ebf579`.
- Exact pack SHA-256: `3acf60520b60f87f8c18e13532512324cb7a539626996ce19897fad94cf2d25d`.
- Private raw-log SHA-256: `b4f8c4ca9c285018772d50a4eda92f34572f742dd97967bca8229b0a6b3ce951`.
- Private raw-log size: 732,081 bytes.
- Raw log in repository: false.

## Required public packet checks

The adjudicator must fail closed unless:

1. the ZIP contains exactly the supported schema member set;
2. paths are unique, relative, and traversal-free;
3. manifest hashes match the exact summary and verification bytes;
4. capture, verification, and manifest authority are `NO_ORDERS`;
5. the exact pinned pack hash is consistent across the packet;
6. one complete session exists and required capabilities have no failures;
7. project issue attempts and direct acknowledgements are zero everywhere;
8. bound plus unbound windows equal total windows;
9. command events equal action windows;
10. reachability counts equal sample count;
11. close-reason counts equal window count;
12. summary and verification counts agree;
13. the verification result digest recomputes exactly;
14. the raw log is explicitly excluded from the public packet.

## Observed promotions

The capture may promote only the following scoped capabilities:

- ordinary-battle local selection callbacks;
- contemporaneous selected-unit binding for observed command windows;
- read-only post-command state sampling;
- point-in-time reachability query availability;
- ordered-position and current-target state matching;
- movement, routing, control-loss, and interruption visibility.

Zero-count states remain `UNVERIFIED`, including leaving-battle and shattered state in this capture.

## Forbidden promotions

The following claims remain rejected or unverified regardless of count:

- player-versus-script command origin;
- Transcendence issue attempt;
- direct acknowledgement or acceptance;
- route completion, path safety, formation feasibility, or arrival;
- project-caused execution;
- project-caused tactical outcome or casualty reduction;
- broad SFO, siege, reinforcement, faction, monster, or flying-unit generalization.

## Schema-1 limiting result and schema-2 correction

The v0.1R schema-1 public packet includes the prepared-manifest hash but not a public prepared-session document. Preparation checks are therefore preserved through the owner-run verifier output, not independently replayable from public files.

Future collector exports use public manifest schema 2 and include a sanitized `public_preparation_attestation.json` containing:

- capture kind and preparation time;
- pack name and exact staged/installed hashes;
- runtime-log-cleared flag;
- active-mod-list, save, and project-order nonmutation flags.

The attestation excludes runtime-log paths, game paths, backup paths, user identity, and other private fields.

## Completion

The gate closes when the exact capture adjudicates deterministically, tampering fails closed, schema-2 attestation is regression-tested, documentation preserves every claim boundary, generated evidence reproduces byte-for-byte, and the complete repository suites pass repeatedly.

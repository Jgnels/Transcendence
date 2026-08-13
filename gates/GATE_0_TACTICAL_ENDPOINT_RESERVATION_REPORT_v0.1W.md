# Gate 0 Report — v0.1W Tactical Endpoint Reservation

## Gate decision

**Closed offline.**

v0.1W adds deterministic simultaneous endpoint reservation above v0.1V guarded packets.

## Battle 4 result

- 34 nonready guarded packets;
- 0 ready packets;
- 0 reservations;
- 0 endpoint conflicts;
- eight slice-level exact solver invocations;
- authority `NO_ORDERS`.

No Battle 4 candidate has candidate-level `QUERY_TRUE` evidence, so the correct output is zero reservations.

## Synthetic matrix

- 14/14 scenarios passed;
- 3/3 metamorphic checks passed;
- exact collision, alternative endpoint, three-way conflict, priority preemption, nonready exclusion, malformed authority, duplicate plan identity, nonfinite coordinates, and explicit 20-packet fallback covered;
- endpoint separation held for every selected set.

## Exact evidence

- Battle 4 reservation file SHA-256: `e14f2f241aa7ef3daccc470b39d929312ca794fe48b0b22f1be2597516f53d77`.
- Battle 4 reservation result digest: `9c4c4943ee30a74c478537cb9779a755303febff318bc86882ec8ff106f4cf7d`.
- Matrix file SHA-256: `daa81774b4806b1b4cd93df51d3d01bde7a13b76c56de06f1bcd7256d6e3cbf8`.
- Matrix result digest: `7f8a5610c259f7f77a67939e9d45d71846e8963ebc541bb2513b416bedc0ef67`.
- Suite SHA-256: `fabc24ffe4e0f8b7dabb38a869ef1b81c59f7168f98b0591efbf4e0038317981`.
- Seed: `20260730`.

## Remaining uncertainty

Endpoint reservations do not establish routes, route crossings, formation footprints, collision safety, command legality, acknowledgement, execution, or tactical benefit.

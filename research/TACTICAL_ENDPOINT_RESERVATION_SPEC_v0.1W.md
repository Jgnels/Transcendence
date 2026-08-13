# Tactical Endpoint Reservation Specification v0.1W

## Purpose

Resolve simultaneous endpoint conflicts among guarded, point-supported shadow packets without issuing orders or pretending to model routes or formations.

## Contracts

- `TACTICAL_ENDPOINT_RESERVATION_V1`
- `TACTICAL_ENDPOINT_RESERVATION_SET_V1`
- `TACTICAL_ENDPOINT_RESERVATION_TRAJECTORY_V1`

## Endpoint contract

- one endpoint may be reserved per ready packet;
- one ready packet may contribute at most one reservation;
- selected endpoints must be separated by at least 12 metres horizontally;
- 12 metres is a project-owned development bound, not a measured unit footprint;
- endpoint separation does not evaluate route crossing, terrain, formation width, collision, safe arrival, or command legality.

## Optimization

Within 16 ready packets, deterministic branch-and-bound maximizes a severity-dominant, utility-preserving objective and uses candidate rank as the canonical within-packet preference.

Above 16 ready packets or after the explicit search-node budget is exhausted, the solver uses a deterministic greedy fallback and marks optimality `UNVERIFIED_FALLBACK`.

Tie-breaking uses packet identity and candidate rank. It does not use coordinate-derived candidate hashes, preserving uniform-translation invariance.

## Authority

Reservations are `SHADOW_ENDPOINT_RESERVED_NOT_ISSUED`. Application authority is `PROHIBITED`; route, formation, command legality, acknowledgement, execution, and outcome remain unverified.

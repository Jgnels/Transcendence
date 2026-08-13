# Tactical Feasibility Envelope Specification — v0.1T

## Purpose

Convert canonical `NO_ORDERS` temporal plans into bounded candidate-point evidence requests without pretending that a point query is a route, formation, legal order, acknowledgement, execution, or outcome.

## Contracts

- `TACTICAL_FEASIBILITY_ENVELOPE_V1`
- `TACTICAL_FEASIBILITY_ENVELOPE_TRAJECTORY_V1`
- `TACTICAL_FEASIBILITY_CAPABILITY_PROFILE_V1`
- `TACTICAL_POINT_QUERY_EVIDENCE_V1`
- `ACTION_FEASIBILITY_WINDOW_EXPORT_V1`
- `ACTION_FEASIBILITY_REEXPORT_VERIFICATION_V1`

## Inputs

The envelope accepts only canonical visibility-safe tactical state and a canonical v0.1Q temporal schedule whose contracts, authority, digests, source identities, times, and active plans reconcile exactly. Stale, forged, authority-altered, or source-substituted inputs fail closed.

## Candidate generation

Each active abstract plan generates no more than three deterministic candidate points. Candidate construction is role- and objective-specific:

- extraction, evacuation, disengagement, ranged repositioning, pursuit termination, and reform use visible-threat egress geometry;
- frontline relief, reserve commitment, and rout containment use a bounded subject-support standoff;
- selective pursuit uses a bounded approach toward a visible routing target.

Maximum abstract displacement is 120 metres. Straight-line geometry is only a query proposal and ranking aid.

## Evidence classifications

- `QUERY_READY_NOT_OBSERVED`: candidates exist but no exact candidate query result is available.
- `POINT_QUERY_SUPPORTED_ONLY`: at least one exact candidate returned `QUERY_TRUE`.
- `POINT_QUERY_REJECTED`: every exact candidate returned `QUERY_FALSE`.
- `POINT_QUERY_UNAVAILABLE`: the interface was unavailable for every exact candidate.
- mixed evidence remains explicitly mixed and cannot become route feasibility.

A `QUERY_FALSE` result vetoes only the exact queried point. A `QUERY_TRUE` result supports only that point at that observation instant.

## Prohibited promotions

The envelope must never infer or emit:

- a complete route;
- formation-width or collision feasibility;
- safe arrival or action completion;
- command availability or legality;
- order issue, acceptance, or acknowledgement;
- execution causality;
- tactical outcome improvement.

## Aggregate live calibration

The v0.1S raw profile proves that the interface returned values in one ordinary battle. v0.1U later showed that only explicit nonzero Move callback points qualify: 191 true and zero valid false samples. Raw non-point zero-vector results remain frozen historical telemetry and may not be assigned to Battle 4 or any generated candidate point.

## Detailed no-replay re-export

The owner-machine workflow locates the exact preserved raw log by SHA-256, verifies the exact probe pack and nonmutation preparation manifest, and emits a public-safe ZIP containing detailed command windows and a hash-bound public manifest. Raw lines, private paths, usernames, backups, and issue/acknowledgement claims are forbidden.

## Gate evidence

- 15 deterministic synthetic scenarios;
- 3 metamorphic checks;
- Battle 4 envelope over eight frozen slices;
- v0.1S aggregate capability profile;
- strict fixture for detailed re-export and tamper rejection;
- repeated full repository validation and byte-identical artifact reproduction.

## Authority

`NO_ORDERS`. This specification prepares evidence and candidate queries only.

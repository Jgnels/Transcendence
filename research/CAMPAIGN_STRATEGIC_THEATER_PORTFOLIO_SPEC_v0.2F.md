# Campaign Strategic/Theater Priority Portfolio Specification v0.2F

## Purpose

Convert the observer-safe v0.2E strategic-challenge envelope into a bounded set of strategic priorities before any army assignment or campaign action authority exists.

## Contract

`CAMPAIGN_STRATEGIC_THEATER_PRIORITY_PORTFOLIO_V1`

Inputs are a canonical campaign scenario plus its exact v0.2E challenge envelope. If an envelope is supplied, it must byte-semantically match a fresh evaluation of that scenario or the portfolio fails closed.

## Priority classes

- `RELIEVE_SIEGED_EXPOSED_FRONT`
- `MAINTAIN_SIEGE_RELIEF_COVERAGE`
- `STABILIZE_EXPOSED_FRONT`
- `MAINTAIN_THREATENED_FRONT_COVERAGE`
- `PROTECT_RECOVERING_FIELD_FORCE`
- `CONTAIN_COHERENT_VISIBLE_RIVAL`
- `MANAGE_FRAGMENTED_VISIBLE_PRESSURE`
- `TRACK_SINGLE_VISIBLE_RIVAL`
- `PRESERVE_STRATEGIC_RESERVE`
- `CONSOLIDATE_LOW_PRESSURE_POSITION`
- `CRITICAL_STRATEGIC_OVERFLOW`

The first four are front obligations; recovery and reserve protect strategic capacity; rival records preserve pressure awareness without inferring coordination; low-pressure consolidation prevents invented aggression.

## Bounded arbitration

At most six top-level records are selected. If more than six critical sources exist, five are selected directly and the sixth record is a critical-overflow record containing every omitted source portfolio ID. Critical-source coverage must remain 1.0.

## Aggression boundary

At most one aggressive-priority channel may be active. A local crisis/exposed front or a state in which every controlled field army is below the frozen recovery threshold disables new aggressive commitment. Rival-awareness priorities may remain present but do not enter `selected_aggressive_priorities` while vetoed.

## Authority

The layer is `NO_ORDERS`; application is `PROHIBITED`. It does not map priorities to armies, reserve destinations, routes, stances, settlements, targets, commands, acknowledgements, execution, or outcomes.

## Evidence limits

The six-record budget and one-aggressive-channel cap are project-owned engineering constraints. Observed campaign evidence remains early vanilla Reikland turns 4–7; the late-game reference remains synthetic. Economy, recruitment, diplomacy, native CAI intent, SFO longitudinal strategy, and campaign enjoyment are outside this gate.

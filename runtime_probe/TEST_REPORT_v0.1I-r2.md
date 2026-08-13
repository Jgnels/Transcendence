# Runtime Probe Test Report v0.1I-r2

## Scope

Correct the live region-identity defect without changing the combined read-only probe pack.

## Added preserved fixtures

- `shadow_log_owned_visible_overlap_valid.txt`
- `shadow_log_owned_visible_owner_conflict_invalid.txt`

The first reproduces the real WH3 condition in which Altdorf appears through both the owned-region and player-visible-region interfaces. The second preserves an adversarial conflicting-owner case.

## Added regressions

- owned and visible records for one stable region coalesce to one scenario entity;
- the richer owned record deterministically retains precedence;
- the overlap count is reported;
- same-key owner conflicts fail closed.

## Deterministic overlap result

- scenario result digest: `f02fac48257a84282e5f2f68031fd2aad547d892c934cc92fbbcd9c9a25d8cee`
- report-file SHA-256: `b9bfa0d9b6fe31ee6afa70377ddd76b703f53f7991ca7fde1c57b2488e01d8ca`
- resolved overlap count: `1`
- retained record source: `OWN`
- retained garrison source: `OBSERVED_OR_OWN_UNIT_COUNT_FALLBACK`

## Pack identity

No Lua source or pack manifest changed.

- observer: `0c1dd8940a697a2d840876f08092ba02f988170e90c5f77b6f934ac15c79f173`
- persistence: `71bf96e4fca54d16e323f5eef9766a6098c6ea4b9416b33aa012317d5f682bd2`
- combined shadow: `c23b8187dde9e0f162b1564b47910714501b9d088b756cb95dfe16cad470b551`
- build result digest: `2b18a01f5b9c75100de50dda59774ae5d265352f29594b29941dce4534da4550`

## Validation

Two final complete validation runs are required after the canonical hash manifest is refreshed. The expected suite is:

- 18 SyntheticLab tests;
- 42 runtime-probe tests;
- 60 total tests;
- 127 canonical repository files.

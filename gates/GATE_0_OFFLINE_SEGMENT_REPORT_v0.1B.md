# Gate 0 Offline Segment Report — v0.1B

## Segment result

**Closed:** offline lab construction, source acquisition audit, optional-profile boundary, and shadow vertical-slice contract.

**Gate 0 overall:** still open.

## Inputs

- repository head: `16c4fa0d5290822a9fcba150b4dffcc8152f1b52`;
- DeepWar pack SHA-256: `f02bd8b5a70f899a8b4827af41da3231c71a7f595c06442177ec70f3fd407d50`;
- Hecleas pack SHA-256: `5945102b4eac8ed73065bcc054d935f878d4ffd2b4af191ed4a15b0c31abedf8`;
- SFO extracted audit ZIP SHA-256: `0119959f7999844bc49b47bd41d53110ad9a83b6f89478e1bf2199b8c65a828f`;
- owner-observed vanilla version/build: `8.1.1 / 48122.4194776`.

## Implemented

- Tier 0–4 SyntheticLab reference implementation;
- observer-safe hidden-information filter;
- deterministic Army Objective Assignment with explanations and alternatives;
- operational and ensemble surrogates;
- tactical contract surrogate;
- PFH5 audit-only parser;
- extracted ZIP source audit;
- three-way table-overlap/conflict report;
- vanilla/SFO/DeepWar/Hecleas profile boundaries;
- acceptance specification and failure fixtures.

## Tests

- 18/18 automated tests passed.
- Tier 0–4 smoke run passed twice with byte-identical output.
- Actual supplied DeepWar/Hecleas/SFO audit ran twice with byte-identical output.
- Repeated same-input/seed runs produced identical digests.
- Test suite completed in 0.57 seconds; smoke runs in 0.54–0.58 seconds; source audits in 0.92–0.95 seconds in the construction environment.

## Defects prevented or corrected

1. **SFO hard dependency:** corrected to an optional profile.
2. **Synthetic evidence overclaim:** Tier 2–4 labels now prohibit WH3 performance claims.
3. **Hidden-information leakage:** planner receives observer-filtered enemy armies only.
4. **Blind mod combination:** overlapping table families are reported as conflict risk.
5. **Pack parser overreach:** unsupported pack formats/dependency cases fail closed.
6. **Difficulty-as-intelligence ambiguity:** fairness classes distinguish bonuses, bypasses, interventions, and planning.

## Capability promotions

- Offline contract validation: `CONTROL`.
- Hidden-information filtering: `CONTROL`.
- Deterministic objective assignment: `CONTROL`.
- PFH5 entry/hash audit for supported packs: `CONTROL`.
- WH3 runtime observation and action capabilities: remain `UNVERIFIED`.

## Smallest unavoidable next live task

On the owner's gaming PC:

1. clone/pull the repository;
2. run the PowerShell test and smoke commands;
3. pin RPFM and WH3 schema revisions;
4. generate the local install/mod manifest;
5. build and load a minimal vanilla observation-only pack.

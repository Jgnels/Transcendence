# Segmented Log Recovery Adjudication — v0.1J

**Evidence label:** `LIMITING_RESULT`

## Input

- Owner recovery ZIP SHA-256: `a7cf62686eceb539ca36cb9f549e21f0542fc521ffbd4da8bf1e7aa529e6f13b`
- Recovery inventory session cutoff: `2026-07-29T23:34:29Z`
- Derived adjudication file SHA-256: `0460147691e52c452db3596c24e5b39c0504e9709abbe36708e604c8b879aad8`
- Derived result digest: `53b63402cdb9380f40624eb14bc5c83f60d66d1bcfa9c65937dfb5259efc2119`

## Result

- Current-session campaign turns recovered: `4, 5, 6, 7`
- Current-session early turns recovered: none
- Current-session `TRANS_BATTLE` records: `0`
- Current-session completed battles: `0`
- Fixture `TRANS_BATTLE` records excluded: `72`
- Fixture completed battles excluded: `2`

The apparent battle recovery came from deterministic fixture files embedded in prior project ZIPs, not from owner gameplay. Historical observer and persistence logs were also excluded from the current combined session.

## Interpretation

The owner manually fought multiple battles, but no battle telemetry survived in the recovered current-session sources. This is a telemetry-design failure, not evidence that no battles occurred. No replay, fixture, or historical log may be promoted as a substitute for the lost live evidence.

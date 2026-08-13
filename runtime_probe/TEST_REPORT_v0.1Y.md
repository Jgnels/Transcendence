# Runtime Probe Test Report — v0.1Y

## Scope

SFO-only environment capture, append-log checkpointing, current battle-marker compatibility, privacy-safe combined export, and one-session continuity verification.

## Added coverage

- strict `used_mods.txt` and Valve VDF parsing;
- exact SFO Workshop item resolution and full-pack hashing;
- exact two-pack load-order acceptance and extra-mod rejection;
- append-prefix checkpoint validation and tamper rejection;
- recognition of current `battle_replay_shadow` plus historical `battle_shadow`;
- path-free public export and local-only raw/checkpoint preservation;
- deterministic campaign → battle → campaign → battle → campaign fixture;
- frozen preparation-control artifact reproduction.

## Result

89 Runtime Probe tests passed. Combined with 73 SyntheticLab tests, the v0.1Y repository passes 162 tests before owner-machine live observation.

# Capability Matrix

All entries begin as `UNVERIFIED`.

| Area | Required behavior | Status | Evidence | Next probe |
|---|---|---:|---|---|
| Campaign | enumerate factions, armies, regions and wars | UNVERIFIED | none frozen | minimal campaign script |
| Campaign | persist project state through save/reload | UNVERIFIED | none frozen | saved-value round trip |
| Campaign | issue or influence army objectives | UNVERIFIED | none frozen | API/source audit + probe |
| Campaign | influence recruitment/economy priorities | UNVERIFIED | none frozen | DB/script probe |
| Battle | observe units and battle state | UNVERIFIED | docs only, not local test | generated-battle probe |
| Battle | command player/AI units in ordinary battles | UNVERIFIED | none | strict feasibility probe |
| Battle | command units in generated/scripted battles | UNVERIFIED | docs suggest controller path | generated-battle probe |
| UI | expose settings and Why inspector | UNVERIFIED | docs only | minimal UI component |
| Tooling | build a valid SFO-compatible pack | UNVERIFIED | none frozen | clean pack smoke test |
| Logging | collect release-build script logs | UNVERIFIED | docs only | enable logging and verify |
| Multiplayer | deterministic and desync-safe execution | OUT_OF_SCOPE_INITIAL | personal single-player target | revisit only if requested |

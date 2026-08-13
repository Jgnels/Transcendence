# WH3 Ordinary-Battle Telemetry API Audit — v0.1I

## Question

Can one normal campaign battle provide useful tactical evidence without granting Transcendence battle-order authority?

## Primary sources inspected

- WH3 Battle object documentation: `https://chadvandy.github.io/tw_modding_resources/WH3/battle/battle.html`
- WH3 Battle Manager documentation: `https://chadvandy.github.io/tw_modding_resources/WH3/battle/battle_manager.html`
- WH3 Battle Hierarchy documentation: `https://chadvandy.github.io/tw_modding_resources/WH3/battle/battle_hierarchy.html`
- WH3 Battle Unit documentation: `https://chadvandy.github.io/tw_modding_resources/WH3/battle/battle_unit.html`
- WH3 Battle Core documentation: `https://chadvandy.github.io/tw_modding_resources/WH3/battle/core.html`
- WH3 Generated Battle documentation: `https://chadvandy.github.io/tw_modding_resources/WH3/battle/generated_battle.html`

Access date: 2026-07-29.

## Findings

### 1. Ordinary battle state is queryable

The battle object exposes the alliance hierarchy, local alliance/army, campaign origin, battle type, time, phase-adjacent state, and outcome/winner queries. The hierarchy is alliances → armies → units and is 1-based.

The documentation recommends the battle manager over a raw battle object. The battle manager provides the battle interface plus phase callbacks, timed callbacks, and synchronized repeating processes.

### 2. Query and control are distinct

A battle-unit object supports state queries. Issuing unit orders requires a battle unitcontroller or a higher-level framework that owns one. The v0.1I source deliberately never creates a unitcontroller and never calls generated-army direct commands.

This is the core authority boundary:

```text
battle hierarchy + unit queries → observation
unitcontroller/generated-army commands → control
```

The current gate uses only the first path.

### 3. Useful tactical fields are documented

The battle-unit interface documents enough state to support descriptive telemetry for:

- unit identity/type/class and control status;
- current and ordered position/bearing/width;
- movement, fast movement, and idle state;
- men alive, hit-point fraction, kills, and ammunition;
- melee engagement and missile pressure;
- morale/routing/shattered/fatigue state;
- left/right/rear flank threats;
- current target;
- visibility to a specified alliance.

Not every method is guaranteed to behave uniformly for every unit class or battle type. The runtime source therefore guards individual calls and preserves explicit capability failures.

### 4. Visibility can be enforced before foreign records

`unit:is_visible_to_alliance(local_alliance)` provides a game-computed line-of-sight boundary. v0.1I checks it before emitting foreign static or dynamic unit records. Hidden enemy units may increment an aggregate hidden count, but receive no unit ID, type, position, health, target, or other identifying state.

### 5. Command traffic may be observable, but is not acknowledgement

Battle event listeners can expose command-related context. This can support descriptive command mix and timing. It does not prove:

- the command was accepted;
- the intended unit executed it;
- the command completed;
- the command caused a battle outcome.

The report therefore records command events while explicitly denying acknowledgement or success authority.

### 6. Generated-battle control is a different path

The generated-battle framework exposes generated armies and unitcontrollers with direct commands. That is relevant to a later control-feasibility experiment but does not prove that a normal campaign battle can be safely or comprehensively controlled. v0.1I does not invoke it.

## v0.1I design

The combined shadow pack contains campaign and battle scripts. The battle script:

- uses an existing `bm` when present and otherwise attempts one battle-manager construction;
- emits battle start metadata;
- traverses the hierarchy with a 240-unit cap;
- records one-second alliance aggregates;
- records three-second detailed unit samples and additional phase samples;
- records selection and command events where contexts support them;
- records completion and outcome;
- emits foreign unit data only while visible;
- never creates a unitcontroller or issues an order.

## Evidence classification

| Claim | Status |
|---|---|
| Project-owned battle source is statically read-only | SUPPORTED |
| Deterministic parser/report/verifier works on fixtures | CONTROL |
| Ordinary WH3 campaign battles load this exact script | UNVERIFIED |
| Every documented field works in WH3 8.1.1 | UNVERIFIED |
| Telemetry overhead is acceptable | UNVERIFIED |
| Battle command traffic can be observed | UNVERIFIED |
| Transcendence can command ordinary-battle units | UNVERIFIED |
| One battle proves tactical quality | INVALIDATED |

## Live acceptance

One manually fought ordinary campaign battle is sufficient to establish interface feasibility only when:

- the exact combined pack is loaded;
- `BATTLE_START` and `BATTLE_COMPLETE` are present;
- local and at least one visible enemy unit are observed;
- multiple samples exist;
- no hidden foreign identifying record appears;
- no capability failure invalidates the required minimum;
- the report confirms no controllers/orders/save/speed/visibility/damage mutation;
- the combined log remains within the 30 MB guardrail.

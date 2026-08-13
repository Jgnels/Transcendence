# Gate 0 Tactical Contract Adversarial Hardening Report — v0.1N

## Decision

**Offline tactical-contract hardening segment: CLOSED.**

v0.1N strengthens the v0.1M planner-development boundary without adding runtime authority. Malformed tactical observations now fail closed, local collapse cannot be masked by an enemy rout cascade, and advisory lifecycle accounting uses stable opportunity identity.

## Canonical base

- Owner-validated release: `v0.1M Tactical Decision Opportunities`.
- Owner-machine result: 34 SyntheticLab tests, 60 Runtime Probe tests, 94 total tests, and 177 canonical hashes.
- Public repository head remains `16c4fa0d5290822a9fcba150b4dffcc8152f1b52`; remote state was not modified.
- v0.1M frozen artifacts remain historical and are not overwritten.

## Defects found and corrected

### F-N001 — permissive observation coercion

**Classification:** `CONTROL_OFFLINE` defect; potential visibility and decision-integrity boundary failure.

Boolean strings such as `"false"`, impossible health/model/ammunition values, non-finite geometry, inconsistent model fractions, invalid visibility labels, and malformed target sentinels could survive validation or be silently normalized downstream.

**Correction:** `BATTLE_TRACE_TACTICAL_INPUT_V2` performs strict type, range, consistency, identity, timing, and visibility validation before tactical-state construction. Eighteen preserved invalid fixtures now fail closed.

### F-N002 — enemy rout masked local collapse

**Classification:** `CONTROL_OFFLINE` state-machine defect.

The v0.1M local state could return a recovery label because the enemy was routing even when the local force remained in crisis or collapse.

**Correction:** local force condition is now independent from the global tactical phase. The adversarial simultaneous-collapse case preserves local-collapse response while separately representing enemy rout/terminal progress.

### F-N003 — slice IDs inflated advisory churn

**Classification:** `CONTROL_OFFLINE` lifecycle-metric defect.

Per-slice opportunity IDs were compared as though they were persistent tactical concerns. A priority continuing into the next slice was counted as retired and newly created, inflating Battle 4 transitions from 50.

**Correction:** a stable `opportunity_key` tracks lifecycle continuity while `opportunity_id` remains a per-slice evaluation instance. Corrected output reports 28 transitions and 11 continued priorities. The comparison to 397 owner commands remains `REFERENCE_ONLY_NOT_CAUSAL`.

### F-N004 — validator ignored files under ignored-name ancestors

**Classification:** `CONTROL_OFFLINE` repository-validation defect.

The repository validator compared ignored names against absolute path components. A checkout beneath a directory named `tmp`, `build`, `dist`, or another ignored token could therefore produce an empty tracked-file set and a misleading manifest result.

**Correction:** ignored-directory filtering now applies only to paths relative to the repository root. A regression copies the validator beneath a `tmp` ancestor, proves ordinary files remain tracked, and proves an internal `dist/` file remains excluded.


## Adversarial result

- Suite seed: `20260730`.
- Invalid-input cases: 18/18 passed.
- Metamorphic cases: 6/6 passed.
- Total: 24/24 passed.
- Report result digest: `96d7287377172712ad440abaabc4160ada3fb9d083bdae33bbbb2a179f01900c`.
- Report file SHA-256: `5685acbe05b974274d31ee08c43c26c0739b225ffe02d2792d4e8faf888dc07c`.

## Deterministic outputs

| Artifact | Result digest | File SHA-256 |
|---|---|---|
| v0.1N tactical-state trajectory | `1170fb399d9d90e597bc7d83cbb67034e6597782d0c2911f9929a61d355fc3f0` | `829ad9df240939797bf1f00fee18341045129ac7b8e04c80deed44a632ac0fa3` |
| v0.1N decision opportunities | `e8b7d65c605956a759cc80972df5adb12c70aed9aa9d76374fd2daf521c0426a` | `00f125d4b48c07ea180c216678cc108245845090042948bb7f49ef7c3fdc407f` |
| v0.1N adversarial report | `96d7287377172712ad440abaabc4160ada3fb9d083bdae33bbbb2a179f01900c` | `5685acbe05b974274d31ee08c43c26c0739b225ffe02d2792d4e8faf888dc07c` |

Two independent rebuilds produced identical bytes for all three artifacts.

## Validation

- SyntheticLab: 37 tests passed.
- Runtime Probe: 61 tests passed.
- Total: 98 tests passed.
- Canonical files: 184.
- The final `SHA256SUMS.txt` digest is recorded by the release installer manifest after packaging.

## Claims

Promoted:

- strict tactical-input rejection is `CONTROL_OFFLINE` and regression-covered;
- the 24-case adversarial suite is deterministic and passed twice;
- local condition and tactical phase are distinct deterministic contracts;
- advisory lifecycle accounting is stable across slices.

Still unverified:

- tactical-quality improvement;
- causal casualty reduction;
- live command issue, acceptance, acknowledgement, or success;
- terrain/pathfinding feasibility;
- ordinary-live, SFO, siege, ambush, reinforcement, other-faction, and unit-scale generalization.

## Authority and safety

`NO_ORDERS`. No WH3 installation, game file, save, Workshop content, active mod list, runtime behavior, or remote GitHub state was modified.

## Smallest next step

Continue offline with heterogeneous tactical-state fixtures and planner-baseline comparisons where public-safe evidence is available. Defer live action authority and the next owner WH3 session until it can batch append-log continuity, vanilla/SFO compatibility, and broad observation needs.

# Gate 0 — Native CAI Behavior Observation Detector v0.2J

**Date:** 2026-08-02  
**Gate status:** `OFFLINE_PREPARATION_CLOSED`  
**Evidence:** `SUPPORTED_OFFLINE`  
**Authority:** `NO_ORDERS`  
**Application:** `PROHIBITED`

## Gate question

Can Transcendence measure the native-CAI failure modes that remain unresolved after row-level reconciliation **without** reinstating v0.2G as the strategic controller or pretending movement reveals engine-internal task state?

**Answer:** yes, for observable trajectory proxies; no, for engine-internal assignment exclusivity, task memory, or hysteresis.

## Implemented

- `synthetic_lab/transcendence_lab/native_behavior.py`
- `synthetic_lab/transcendence_lab/native_behavior_matrix.py`
- `synthetic_lab/scenarios/native_cai_behavior_adversarial_matrix_v0.2J.json`
- `synthetic_lab/results/native_cai_behavior_adversarial_matrix_v0.2J.json`
- CLI commands `native-behavior` and `native-behavior-matrix`

The detector measures threatened-front coverage/response latency, observed recovering-army offensive engagements, a home-zone buffer proxy, stationary-position proxy, and directional retarget/reversal proxies.

## Adversarial result

**9/9 cases pass.**

Important false-positive hardening performed during development:

1. A naive directional reversal rule was rejected because a newly appearing local crisis can legitimately reverse movement. The final detector separates crisis-driven retargeting from unexplained reversal.
2. Recovery misuse originally risked reading replenishment from a same-turn/post-battle snapshot. The final event contract requires actor replenishment measured at engagement time.
3. The reserve signal was narrowed from any healthy force outside a threatened front to a healthy, unengaged **home-zone** buffer proxy and remains explicitly noncausal.
4. A threatened front that disappears before observed coverage is distinguished from a right-censored threat still open at trace end.

## Authority / overclaim checks

The detector fails closed when trace authority is not `NO_ORDERS / PROHIBITED` or when an unsupported event type such as `NATIVE_TASK_ASSIGNMENT` is supplied.

Runtime structural regression confirms the module imports no process/socket/OS-control adapter and exposes no order-issuing function.

The output explicitly keeps:

- assignment exclusivity `UNAVAILABLE_FROM_TRAJECTORY_ONLY`;
- native assignment memory `UNAVAILABLE`;
- native hysteresis `UNAVAILABLE`;
- internal task visibility `UNAVAILABLE`.

## Regression

- **155/155 SyntheticLab tests pass**.
- **160/160 Runtime Probe tests pass** after the new no-runtime/order-adapter structural regression.
- Total direct regression: **315/315**.

Repository hash validation is sealed separately after the final manifest is regenerated.

## Architecture consequence

This gate strengthens, rather than weakens, the post-review architecture. v0.2G no longer needs application authority in order to test the hypotheses that originally justified it. Recovery misuse, front response, buffer capacity, and churn can be measured against native trajectories first.

The v0.2G 2/4-turn commitment windows and 0.15 reassignment margin remain **uncalibrated project hypotheses** and are not imported as native-failure thresholds by v0.2J.

## Remaining uncertainty / next gate

No current owner-runtime trace satisfying this new contract exists yet. The next task is therefore **observation acquisition design**, not a WH3 run and not a controller:

1. determine which required fields can be captured read-only while preserving the project's visibility/fairness boundary;
2. make incomplete visibility explicit rather than treating partial foreign-army data as complete faction state;
3. prepare exact collector/export/verifier and matched vanilla/SFO cohort before asking the owner to launch WH3;
4. only then preregister pass/fail thresholds for a real native-first ablation.

No owner action is required by v0.2J itself.

# SyntheticLab Test Report — v0.2N

Date: 2026-08-03

Command:

`PYTHONPATH=synthetic_lab python -m transcendence_lab.cli test`

Result: **179/179 PASS**.

v0.2N-specific coverage includes:

- privileged/application-ineligible trace enforcement;
- rejection of old traces lacking declared battle-participant telemetry;
- damaged-army attacker-side recovery re-entry signal;
- defender-side exclusion from the offensive numerator;
- recovery exposure insufficiency;
- battle exclusion from temporal windows;
- context-change exclusion;
- >=120-degree reversal threshold;
- non-overlapping repeated reversal requirement;
- exact region A→B→A→B→A detection;
- positive signal limited to causal review + narrow native-row ablation;
- deterministic threshold digest/result behavior.

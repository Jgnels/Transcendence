# SyntheticLab Test Report v0.2G

- 138/138 direct SyntheticLab tests pass.
- Frozen strategic force-allocation artifact reproduces current implementation exactly.
- 8/8 assignment adversarial cases pass.
- 6/6 temporal commitment adversarial cases pass.
- 7/7 metamorphic checks pass.
- Critical overflow expands back to exact source obligations; shortage is disclosed rather than erased.
- Recovery protection blocks noncritical use and permits only an explicitly labeled critical override.
- Actor exclusivity and strategic-reserve protection are enforced.
- Small geometric changes do not churn actors; material reassignment waits for the 4-turn review window and 0.15 score margin.
- Disappearing priorities retire with no causal credit; turn gaps reset continuity.
- 500-asset assignment evaluation repeated 10 times with one output digest; mean 0.1212 s, min 0.1134 s, max 0.1610 s in the build environment. Each run selected 6 assignments, retained 1.0 critical coverage, and had zero double-booked actors.

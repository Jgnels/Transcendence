# Runtime Probe Test Report v0.2E

- date: 2026-08-01
- command: `python -m unittest discover -s runtime_probe/tests -v`
- result: **139/139 PASS**
- baseline v0.2D: 137 tests
- v0.2E additions: 2 tests
- measured suite runtime in the Linux validation environment: 0.600 seconds (`time` wall clock 1.95 seconds)

v0.2E adds no runtime behavior. The two new regressions prove:

1. the campaign-challenge module imports no runtime/order execution surface, exposes no order-issue/apply adapter, does not import `runtime_probe`, and keeps application authority `PROHIBITED`;
2. the adversarial matrix preserves `NO_ORDERS`, hidden-enemy invariance, and player-vs-NPC label invariance.

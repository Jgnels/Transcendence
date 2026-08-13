# Runtime Probe Test Report v0.2D

- date: 2026-08-01
- command: `python -m unittest discover -s runtime_probe/tests -v`
- result: **137/137 PASS**
- baseline v0.2C: 135 tests
- v0.2D additions: 2 tests

v0.2D adds no runtime behavior. The two new regressions prove:

1. the offline policy module imports no runtime/order execution adapter and defines/calls no `issue_order`, `execute_order`, `send_order`, or `apply_order` surface;
2. the known Ubersreik/Marienburg/Chaos runtime-identity alias is preserved as explicit provenance while each separate display identity remains intact.

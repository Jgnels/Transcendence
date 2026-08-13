# Runtime Probe Test Report — v0.2O

Date: 2026-08-03

Command:

`PYTHONPATH=synthetic_lab python -m unittest discover -s runtime_probe/tests -p 'test_*.py' -v`

Result: **195/195 PASS**.

v0.2O-specific coverage includes:

- exact two-pack SFO + diagnostic-probe profile binding;
- rejection of SFO Workshop pack hash drift;
- rejection of extra active mods in the matched SFO profile;
- thin Windows owner wrappers delegating to tested Python implementations;
- public-safe owner-kit construction with no SFO `.pack` bytes;
- unchanged read-only privileged diagnostic behavior-study instrument.

# Runtime Probe Test Report — v0.2N

Date: 2026-08-03

Command:

`PYTHONPATH=synthetic_lab python -m unittest discover -s runtime_probe/tests -p 'test_*.py' -v`

Result: **191/191 PASS**.

v0.2N-specific coverage includes:

- complete pending-battle participant parsing;
- incomplete battle sequence rejection path;
- documented pending-battle cache method presence in the read-only Lua probe;
- preservation of the `rebels` pseudo-faction crash fix;
- no campaign/battle mutation surface in the diagnostic probe;
- thin PowerShell owner wrappers;
- exact frozen-threshold digest binding in the owner kit;
- fresh behavior-study preparation/profile binding;
- 11-turn synthetic confirmatory owner workflow;
- public-safe confirmatory ZIP export.

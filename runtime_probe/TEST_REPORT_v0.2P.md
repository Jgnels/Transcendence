# Runtime Probe Test Report — v0.2P

Date: 2026-08-04

Command:

`PYTHONPATH=synthetic_lab python -m unittest discover -s runtime_probe/tests -p 'test_*.py' -v`

Result: **196/196 PASS**.

v0.2P-specific coverage includes:

- exact SFO + diagnostic-probe two-pack binding and SFO SHA-256 drift rejection;
- extra-mod rejection;
- thin PowerShell owner wrappers;
- standalone v0.2P owner-kit construction containing the frozen mechanistic/decision artifacts while excluding every `.pack` byte;
- unchanged game-side diagnostic probe authority and application-ineligible research boundary.

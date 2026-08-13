# Runtime Probe Test Report — v0.2L Native Visible Directional Churn

**Date:** 2026-08-02

Full Runtime Probe regression: **180/180 PASS**.

The v0.2L runtime batch adapter consumes the existing read-only shadow log. It discovers sufficiently observed player-visible foreign factions, builds the v0.2K partial trace, and applies the frozen v0.2L churn evaluator.

The existing five-turn fixture and historical owner turns 4–7 both produce zero eligible primary windows. They remain insufficient-exposure limiting results rather than negative evidence about native hysteresis.

Owner-harness regressions additionally verify:

- VANILLA accepts only the shadow probe and rejects an extra mod;
- SFO binds exactly one Workshop 2792731173 pack plus the probe and rejects an extra mod;
- SFO pack mutation after preregistration fails closed;
- a prelaunch-deferred local probe may materialize after launch without relaxing the non-probe profile;
- a non-attested passive protocol is nonconfirmatory;
- matched VANILLA/SFO comparison is descriptive only and mismatched campaign protocol is rejected;
- preparation archives the prior runtime log and binds the staged/installed probe;
- collection emits only the five public-safe evidence files;
- Steam default-library autodiscovery is covered;
- the deterministic standalone owner kit is raw-pack-free/private-path-free and byte-identical across rebuilds;
- extracted standalone kits have been exercised end-to-end for both fake VANILLA and fake SFO profiles through preparation, synthetic 12-turn collection, verification and five-file public upload packaging;
- PowerShell owner wrappers are minimal Python launchers without `Invoke-Expression`, `Start-Process`, ordered-hash construction, or `-replace` parsing logic;
- no v0.2L owner tool contains an order/application surface or imports the v0.2G assignment/commitment stack.

Authority remains `NO_ORDERS`; application remains `PROHIBITED`.

# Gate 0 — Frozen Personal Baseline and Capability Truth

## Purpose

Create a reproducible private baseline of the owner's real WH3 environments and prove what the project can observe, influence, and control before implementing live gameplay authority.

## Exit criteria

### Baseline manifest
- [ ] Exact WH3 Steam branch, game version, build ID, and executable/file hashes recorded. *(version/build observed; branch and file hashes remain)*
- [ ] Exact SFO original pack filename, full-pack hash, and update metadata recorded. *(extracted audit ZIP hash recorded only)*
- [ ] DLC/content ownership relevant to the baseline recorded.
- [x] Exact captured vanilla campaign and battle settings recorded.
- [ ] Exact active mod list, versions, load order, and hashes recorded.
- [x] Baseline model distinguishes vanilla, SFO-only, and personal-stack profiles.
- [x] No proprietary or personal binary is committed to Git.

### Owner-experience corpus
- [ ] At least one early Karl Franz save or reproducible start.
- [ ] At least one late Karl Franz save where challenge has collapsed.
- [x] At least one difficult field-battle replay/save. *(Battle of Eilhart replay frozen by SHA-256; owner identifies it as the messy representative fight)*
- [ ] At least one siege or settlement-battle example.
- [x] Short owner notes explaining what was enjoyable or defective in each artifact. *(Battle 4 is representative of an intense messy fight; earlier decisive battles were low-casualty cleanups)*
- [x] Private-artifact policy and ignored local storage are defined.

### Toolchain
- [ ] RPFM executable and WH3 schema revisions pinned.
- [x] One-command offline static/test validation exists.
- [x] One-command deterministic script-only probe-pack build exists. *(WH3 load observed once)*
- [x] Minimal vanilla pack loads and emits observer records. *(two independent exact-pack runs; corrected loader entrypoint succeeded in both)*
- [x] Logging can be enabled, captured, hashed, and parsed.
- [ ] Rollback/remove instructions are proven.


### Live-probe preparation
- [x] Read-only observer pack source exists.
- [x] Persistence behavior is isolated in a separate opt-in pack.
- [x] Expanded shadow-input behavior is isolated in a third read-only pack.
- [x] Deterministic PFH5 pack builder and round-trip tests exist.
- [x] Structured log parser rejects private, malformed, and out-of-order records.
- [x] Explicit install, evidence collection, and hash-guarded rollback scripts exist.
- [x] Observer pack run completed twice in pure vanilla WH3 using the exact same pack hash. *(two independent corrected-pack collections; byte-identical logs; verifier digest `4bd1ad7bf39e086fa26d1dad3265da1a487db437b4d51b2d5715a4a2203326f`)*
- [x] Persistence round trip completed on a disposable save. *(exact pack; isolated `WRITE 0→1` and same-save `RELOAD 1→2`; verifier semantic digest `b996cc93f07275bc8d36fa428baa5e055ee03ba19bebc113175beedf048198bb`)*
- [x] Combined campaign-and-battle shadow source, parsers, collector, and verifier prepared offline. *(one exact read-only pack; five-turn campaign and two ordinary-battle acceptance contract; region identity, cross-runtime append logging, force eligibility, proxy scale, and garrison regressions covered)*

### Capability probes
- [x] Campaign observation probe. *(core identity/position/visibility fields observed; required-field expansion remains)*
- [x] Save/reload state probe. *(one namespaced project integer; `REPLICATED`; no broader save-authority claim)*
- [ ] Campaign influence/control probe.
- [ ] Generated/scripted battle controller probe.
- [x] Ordinary-battle feasibility result. *(exact Battle of Eilhart replay; complete read-only session; local and visible-enemy unit queries and command traffic observed)*
- [ ] UI/settings/logging probe.
- [ ] Every runtime claim classified with evidence and reproduction steps.

### Lab design
- [x] SyntheticLab Tier 0–4 contracts defined and implemented.
- [x] Rich/ensemble/tactical labs are separated from runtime.
- [x] Scenario manifests, deterministic seeds, input/result digests, and output schemas exist.
- [x] Simulator-fidelity claims remain hypotheses until calibrated.
- [x] DeepWar/Hecleas/SFO acquisition audits and table-overlap report exist.

### First vertical slice
- [x] Shadow-mode Army Objective Assignment design accepted.
- [x] Required WH3 observations proven available or design revised. *(campaign turns 4–7 plus exact dense Battle 4 replay; semantic defects and sampling defects corrected; direct selection callbacks preserved as a limiting result)*
- [x] Acceptance metrics, invariants, and failure fixtures frozen.

## Offline segment result

The foundation, exact observer, persistence, campaign-input, ordinary-replay observation, dense Battle 4 telemetry, and Tier 4R calibration segments are closed. The corrected exact replay pass is `OBSERVED_DENSE_SELECTION_LIMITING_RESULT`: callback continuity, dense interval coverage, stable identity, visibility-safe unit telemetry, and bounded state-matching inference are observed. Direct selection callbacks emitted no replay events and remain a documented limiting result.

No further Battle 4 playback is required. v0.1M established the first `NO_ORDERS` tactical-state and decision-opportunity framework; v0.1N hardened its contracts; v0.1O added heterogeneous portfolio baselines; v0.1P added deterministic objective assignment and conflict resolution; and v0.1Q adds bounded temporal lifecycle, cancellation, review, cooldown, and continuity-reset semantics. The next offline step is a strict read-only action-authority and feasibility evidence packet. A later owner session should batch append-log continuity, controllability, acknowledgement, interruption, and vanilla/SFO compatibility evidence rather than isolate another narrow test.

Rollback proof, remaining private baseline details, SFO certification, and actual order-authority sandboxes remain open.

## Stop conditions

Stop only for missing local artifacts, live WH3 observation, local compilation/packaging, or a genuinely non-inferable owner decision.

## Gate report

Record exact inputs, hashes, tool revisions, tests, defects, capability promotions/rejections, and the smallest remaining live step.

## v0.1Y SFO combined-session preparation segment

- [x] Exact SFO/WH3/probe/load-order owner preflight contract.
- [x] Append-log checkpoint watcher and prefix-chain verifier.
- [x] Current battle-probe marker compatibility.
- [x] Path-free public SFO export with private raw/checkpoint preservation.
- [x] Deterministic five-turn/two-battle control artifact.
- [ ] One uninterrupted owner-machine SFO session with five turn starts, two manually fought battles, and campaign return after each.

The offline segment is closed. Live SFO continuity, compatibility, and performance evidence remain open.

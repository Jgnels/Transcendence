# Gate 0 — Frozen Personal Baseline and Capability Truth

## Purpose

Create a reproducible, private baseline of the owner's real WH3/SFO environment and prove what the project can observe, influence and control before implementing gameplay intelligence.

## Exit criteria

### Baseline manifest
- [ ] Exact WH3 Steam branch, game version, build ID and executable/file hashes recorded.
- [ ] Exact SFO Workshop item, local pack filename, file hash and update metadata recorded.
- [ ] DLC/content ownership relevant to the baseline recorded.
- [ ] Exact campaign and battle settings recorded.
- [ ] Exact mod list, versions, load order and hashes recorded.
- [ ] The baseline distinguishes SFO-only from the owner's full mod stack.
- [ ] No proprietary or personal binary is committed to Git.

### Owner-experience corpus
- [ ] At least one early Karl Franz save or reproducible start.
- [ ] At least one late Karl Franz save where challenge has collapsed.
- [ ] At least one difficult field-battle replay/save.
- [ ] At least one siege or settlement-battle example.
- [ ] Short owner notes explaining what was enjoyable or defective in each artifact.
- [ ] All private artifacts live under ignored local storage with manifests/hashes in Git.

### Toolchain
- [ ] RPFM/schema/tool revisions pinned.
- [ ] One-command static validation exists.
- [ ] One-command pack build exists.
- [ ] Minimal pack loads without script errors.
- [ ] Logging can be enabled and captured.
- [ ] Rollback/remove instructions are proven.

### Capability probes
- [ ] Campaign observation probe.
- [ ] Save/reload state probe.
- [ ] Campaign influence/control probe.
- [ ] Generated/scripted battle controller probe.
- [ ] Ordinary-battle feasibility result.
- [ ] UI/settings/logging probe.
- [ ] Every claim classified with evidence and reproduction steps.

### Lab design
- [ ] Synthetic Lab v0 contract defined.
- [ ] Rich Lab variants are separated from runtime.
- [ ] Scenario manifest, deterministic seeds, fixture hashes and output schema defined.
- [ ] Simulator-fidelity claims remain hypotheses until calibrated.

### First vertical slice
- [ ] Shadow-mode Army Objective Assignment design accepted.
- [ ] Required observations proven available or the design revised.
- [ ] Acceptance metrics and failure fixtures frozen.

## Stop conditions

Stop only for missing local artifacts, live WH3 observation, local compilation/packaging, or a genuinely non-inferable owner decision.

## Gate report

Record exact inputs, hashes, tool revisions, tests, defects, capability promotions/rejections and the smallest remaining live step.

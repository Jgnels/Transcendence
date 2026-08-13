# Owner Intake Checklist — Remaining Gate 0 Inputs

## Already captured

- pure-vanilla v8.1.1 build 48122.4194776 settings screenshots;
- DeepWar AI pack;
- Hecleas AI Overhaul pack;
- extracted SFO DB/script/text audit bundle;
- owner confirmation that the captured settings were vanilla;
- successful laptop setup, including frozen local copies of SFO, DeepWar, and Hecleas;
- private and sanitized laptop machine manifests;
- RPFM fingerprint and WH3 executable metadata in private local storage;
- deterministic observer/persistence probe package prepared offline.

## Immediate next input

1. **Pure-vanilla observer run**
   - apply v0.1C;
   - run `runtime_probe/tools/prepare_live_probe.ps1 -InstallObserver`;
   - enable only the observer pack in the launcher;
   - start a fresh vanilla Karl Franz Immortal Empires campaign;
   - reach the first interactive turn and exit;
   - run `runtime_probe/tools/collect_probe_logs.ps1`;
   - repeat once before any persistence or intervention test.

2. **Sanitized machine manifest**
   - preserve the private manifest locally;
   - share only `local_inputs/generated/gaming_laptop_sanitized.json` for canonical hash/version import.

3. **Disposable persistence test**
   - run only after the observer result is clean;
   - use a throwaway campaign save;
   - save, exit, reload once, and collect both logs.

## Later Gate 0 inputs

- Steam branch and DLC/content ownership;
- exact active mod list and load order for vanilla, SFO-only, and personal-stack profiles;
- new campaign checkpoints near turns 1, 10–15, 25–35, 50, 75–100, 125–150, and the first turn challenge noticeably collapses;
- one difficult field battle, one bad-AI example, and one siege/settlement battle;
- short owner notes explaining what was enjoyable or defective.

## Privacy and copyright

Keep saves, replays, Workshop packs, CA assets, and personal logs under ignored `local_inputs/`. Commit only project-owned code, hashes, metadata, lawful derived fixtures, and observations.

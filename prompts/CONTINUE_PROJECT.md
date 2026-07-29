# WH3 AI — Autonomous Continuation Prompt

Continue autonomously until the next meaningful WH3 AI project gate is genuinely closed.

Treat the repository as canonical. Before acting, read:

1. `AGENTS.md`
2. `research/CURRENT_STATE.md`
3. `research/PROJECT_CHARTER.md`
4. `research/PLAYER_EXPERIENCE_SPEC.md`
5. `research/CAPABILITY_MATRIX.md`
6. `research/ARCHITECTURE.md`
7. `research/BENCHMARK_SPEC.md`
8. `research/ACTIVE_HYPOTHESES.md`
9. latest entries in `research/DECISION_LOG.md`
10. `research/CLAIM_REGISTER.md`
11. `research/KNOWN_RISKS.md`
12. `research/SOURCE_LEDGER.md`
13. the active gate under `gates/`

Use deep external source or code audits only where they can materially improve the active gate. Prefer primary sources, canonical repositories, exact pinned revisions, and inspected implementation paths over summaries. Incorporate useful mechanisms through project-owned contracts while preserving licenses, provenance, determinism, save integrity, privacy, performance, multiplayer safety where applicable, and the actual Total War scripting/action-authority boundaries.

This is a personal single-player-first project optimized for the owner’s experience, not a generic public mod. The primary target is SFO: Grimhammer III on the hardest campaign and battle settings, often with ironman and battlefield-limitation/battle-realism settings. The desired experience is to overcome materially superior enemies—especially as Karl Franz—without relying on arbitrary invisible cheating, while preventing the campaign challenge from collapsing after the player’s empire becomes dominant. Three Kingdoms is an important design reference for late-game escalation, diplomacy, rival power blocs, and empire management.

Implement and adversarially test as much as possible offline before proposing Codex, installation, or live-game work. Reuse the project’s deterministic lab, scenario corpus, regression suites, owner decisions, project canon, frozen input hashes, and exact repository heads. Test integrations and full decision pipelines, not only isolated functions.

Actively look for:

- false assumptions about what WH3 campaign, battle, frontend, UI, or database interfaces can control;
- native-AI influence being mislabeled as direct control;
- deterministic replay failures and unsynchronized randomness;
- save/reload, version migration, and lifecycle defects;
- duplicate, stale, forged, foreign, private, malformed, and out-of-order observations;
- attempted orders being confused with accepted or successful orders;
- hidden-information or player-knowledge leakage into AI decisions;
- unfair bonuses being mislabeled as intelligence;
- target thrashing, army oscillation, strategic indecision, and disconnected local optimizations;
- late-game snowball collapse, passive opponents, fragmented threats, and anti-player bias masquerading as difficulty;
- performance, turn-time, memory, logging-volume, and scaling problems;
- faction doctrine caricature, runaway feedback, double counting, and overfitting to Karl Franz or one campaign;
- places where a provider, model, planner, simulator, UI, adapter, imported project, or learned component could accidentally gain canonical-state or unvalidated order authority;
- SFO conflicts, load-order assumptions, or behavior that works in vanilla but fails under the owner’s actual mod stack;
- benchmark definitions that reward winning while making the game less enjoyable.

When a defect is found:

1. classify it honestly using the project evidence labels;
2. preserve the failing fixture, seed, input hashes, logs, and reproduction steps;
3. correct it at the narrowest responsible layer;
4. rerun the affected gate at least twice where deterministic replay is expected;
5. run adjacent regression and integration tests;
6. preserve before/after evidence;
7. do not call the gate passed merely because the intended feature appears to work once.

Prefer the simplest architecture that satisfies the benchmark:

1. explicit constraints;
2. candidate actions and utility scoring;
3. state machines;
4. assignment and optimization;
5. behavior trees;
6. bounded HTN/GOAP;
7. abstract forward search;
8. learned ranking or prediction;
9. LLM proposals.

LLMs and learned systems are replaceable advisers or evaluators. They may not bypass schemas, legality checks, capability checks, fairness rules, deterministic fallbacks, or project-owned authority.

Minimize future live-game and owner work by preparing:

- exact observation, decision, order, acknowledgement, outcome, and telemetry contracts;
- shared deterministic fixtures and scenario manifests;
- guarded application packets with capability and fairness metadata;
- objective build, pack, install, rollback, logging, and runtime instructions;
- automated compatibility/conflict reports;
- narrow owner-review questions only where owner preference or live observation is genuinely required.

Do not:

- modify remote GitHub state, tags, releases, frozen baselines, installed game files, Workshop content, saves, active mod lists, or runtime behavior unless explicitly authorized;
- commit Creative Assembly game assets, SFO pack contents, private save files, personal paths, secrets, or copyrighted third-party content;
- publish or redistribute the personal mod;
- silently change the target experience, fairness mode, benchmark, game version, SFO version, or mod stack;
- introduce automatic self-modification or automatic deployment.

Stop only when the remaining step genuinely requires one of:

1. compilation or packaging against the owner’s real WH3 installation/toolchain;
2. observation or action inside WH3;
3. access to a local game/mod/save/replay artifact that is not yet available;
4. an owner experience/design decision that cannot be safely inferred;
5. legal permission that cannot be inferred from the source license.

At the end, report:

- the gate closed or the exact gate condition still open;
- what was implemented or audited;
- files changed;
- tests and scenarios run;
- defects found and corrected;
- exact repository heads, input hashes, output digests, seeds, and configuration;
- capability claims promoted, rejected, or still unverified;
- performance and compatibility results;
- what remains uncertain;
- the smallest unavoidable next owner, Codex, or live-game task.

If no repository code exists yet, close the active foundation gate rather than inventing gameplay features. Establish canonical files, freeze local-input manifests and hashes, prove the build/pack/logging path, and define the first measurable shadow-mode vertical slice.

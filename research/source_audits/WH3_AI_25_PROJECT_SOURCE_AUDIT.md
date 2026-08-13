# WH3 AI — 25-Project Source Audit and Acquisition Plan

**Date:** 2026-07-28  
**Scope:** First-pass source-level architecture audit of representative critical paths in 25 relevant projects.  
**Important limitation:** This is not a claim that every line in every repository was audited. It is a code-informed acquisition audit intended to decide what deserves a deeper file-by-file review or prototype.

## Explicit exclusions

Per the project owner’s instruction, the following six Workshop examples are **not counted** among the 25 audited projects:

- Workshop item `2978779730`
- Workshop item `2905096541`
- Workshop item `2799316652`
- Workshop item `3428755738`
- Workshop item `2846183349`
- Workshop item `2792395073`

Treat them as external player-facing benchmarks and behavioral references. Their observable features can inform benchmark scenarios, but no source-reuse assumption should be made.

# Executive conclusion

The best WH3 AI project should **not** be one monolithic “brain,” and it should not begin with an LLM trying to play the game end to end.

The strongest practical design is:

```text
WH3 / Pack / Script adapters
        ↓
Canonical observation snapshot
        ↓
Strategic director
  ├─ diplomacy
  ├─ economy/construction
  ├─ research/recruitment
  ├─ wars/objectives
  └─ theaters/resource allocation
        ↓
Operational army director
  ├─ army roles
  ├─ target assignment
  ├─ staging/reinforcement
  ├─ recovery
  └─ composition/siege policy
        ↓
Tactical commander (only where script control is proven)
  ├─ formation/deployment
  ├─ target matching
  ├─ reserve/flank policy
  └─ ability/pursuit/capture policy
        ↓
Validated orders or bounded policy interventions
        ↓
Telemetry, outcome evaluation, regression tests
```

The project should use four different acquisition modes:

1. **Direct foundation:** RPFM, schemas, permissively licensed WH3 helpers.
2. **Algorithm ports:** small, tested kernels such as candidate-action utility, assignment, HTN or reactive execution.
3. **Architecture transfer:** mature RTS/4X systems whose engine/runtime is incompatible.
4. **Benchmark/test inspiration:** research environments and headless scenario systems.

## Highest-value acquisitions

### Adopt or wrap first
1. RPFM + RPFM Schemas
2. Warhammer 3 TypeScript Framework, after hardening
3. WH3 Mod Manager conflict-analysis concepts
4. VCO/CBAC event and policy patterns

### Prototype early
1. Wesnoth-style candidate-action utility core
2. DCT-style theater/commander model
3. OpenRA-style squad/army role state machines
4. Stratega-style abstract forward model
5. TotalWarSimulator-derived battle lab

### Study, do not make runtime dependencies
1. OpenRA
2. FreeOrion
3. VCMI
4. UAlbertaBot
5. microRTS/Gym-µRTS
6. Widelands
7. Warzone 2100

# Source audit

## 1. Rusted PackFile Manager (RPFM)

**Repository:** https://github.com/Frodo45127/rpfm  
**Pinned revision inspected:** `cd255a4405f5cc052df3a5809b3aced5717496f5`  
**License status:** `MIT`  
**Primary layer:** WH3 build/data/tooling  
**Acquisition decision:** `VENDOR_OR_WRAP`  
**Priority:** `P0`

### Representative source paths inspected
- `rpfm_lib/src/files/pack/mod.rs`
- `rpfm_extensions/src/diagnostics/pack.rs`
- `rpfm_ui/src/packedfile_views/table/`

### Source-level finding
Implements Total War PackFile decoding/encoding, dependency metadata, lazy loading, compression, DB/Loc handling and diagnostics. The pack module also contains explicit handling hooks for siege-AI map hints.

### Concrete value to this project
Use as the authoritative pack/schema/diagnostic foundation or invoke its headless/server capabilities. Do not write a new pack parser or table editor.

### Risks / limits
Large Rust/Qt codebase; pin schema and game build; keep runtime AI independent from the authoring tool.

## 2. RPFM Schemas

**Repository:** https://github.com/Frodo45127/rpfm-schemas  
**Pinned revision inspected:** `d12f59cb6de106d205f51b81739951adbc840c49`  
**License status:** `MIT`  
**Primary layer:** WH3 schema/version data  
**Acquisition decision:** `VENDOR_OR_WRAP`  
**Priority:** `P0`

### Representative source paths inspected
- `patches.ron`
- `schemas/`

### Source-level finding
Versioned schema and patch data used to decode Total War database tables.

### Concrete value to this project
Pin as a submodule/artifact and record the schema revision used for every generated pack and benchmark.

### Risks / limits
Schemas can lag a new game patch; build a compatibility gate rather than silently generating with stale definitions.

## 3. Warhammer 3 TypeScript Framework

**Repository:** https://github.com/admiralnelson/warhammer3-typescript-framework  
**Pinned revision inspected:** `b8b4f647d6abd657fd6e7d528c8cd3022990244f`  
**License status:** `MIT`  
**Primary layer:** WH3 campaign scripting  
**Acquisition decision:** `VENDOR_OR_WRAP`  
**Priority:** `P0/P1`

### Representative source paths inspected
- `template/campaign/mod/_MyProjectUtils.ts`
- `template/campaign/mod/MyProjectCharacter.ts`
- `template/campaign/mod/MyProjectCommonUserInterface.ts`

### Source-level finding
Provides TypeScript-to-Lua structure, logging, saved-value wrappers, first-tick helpers, engine-synchronized random helpers, timer/listener abstractions and typed campaign code organization.

### Concrete value to this project
Strong starting toolchain for compile-time safety. Fork minimally, add generated WH3 interface declarations, strict lint rules, deterministic-random guardrails and testable pure-domain modules.

### Risks / limits
Types are incomplete and transpilation adds another failure layer. Never let wrapper types imply an engine capability that has not been tested.

## 4. Knights of the Round Belly — TypeScript

**Repository:** https://github.com/admiralnelson/knights-of-round-belly-typescript  
**Pinned revision inspected:** `f2a4fe2d355fe5f4d2b4c281763e6d7632eb7e82`  
**License status:** `VERIFY_AT_PIN`  
**Primary layer:** WH3 production TypeScript mod  
**Acquisition decision:** `IDEAS_ONLY`  
**Priority:** `P1`

### Representative source paths inspected
- `campaign/mod/KnightsOfRoundBelly.ts`
- `campaign/mod/KnightsOfRoundBellyOgreSpawner.ts`
- `campaign/mod/_KnightsOfRoundBellyUtils.ts`

### Source-level finding
A real mod built on the TypeScript approach, with namespaced modules, typed data maps, event listeners, faction/region data, AI-specific branches and campaign mutations.

### Concrete value to this project
Use as evidence that the toolchain can support a nontrivial campaign mod and as a corpus for build/layout conventions.

### Risks / limits
Content-specific global data and large monolithic files are examples to improve, not copy. Verify license before reuse.

## 5. Dynamic Disasters

**Repository:** https://github.com/Frodo45127/tww3_dynamic_disasters  
**Pinned revision inspected:** `c9ccec4dd3c7bdfce57366b5b44a90936d93cc21`  
**License status:** `LICENSE_REVIEW_REQUIRED`  
**Primary layer:** WH3 modular campaign framework  
**Acquisition decision:** `PORT_ALGORITHM`  
**Priority:** `P0/P1`

### Representative source paths inspected
- `script/campaign/mod/dynamic_disasters.lua`
- `script/campaign/dynamic_disasters/`

### Source-level finding
Manager with mandatory module contracts, default settings, persistent staged state, MCT integration, dynamic file discovery, protected loading with pcall, per-module validation and error isolation.

### Concrete value to this project
Port the plugin contract, module validation, staged lifecycle, save wrapper and fail-soft loading into faction doctrines, strategic policies and scenario modules.

### Risks / limits
No repository LICENSE found in this pass; concepts are safe to study, direct copying requires owner/license review.

## 6. Victory Conditions Overhaul Framework

**Repository:** https://github.com/msolefonte/vco-framework  
**Pinned revision inspected:** `13a3e48ee0614e6b6be7e42abf288ce27ccdceb1`  
**License status:** `Apache-2.0`  
**Primary layer:** WH3 faction/objective framework  
**Acquisition decision:** `COPY_OK`  
**Priority:** `P1`

### Representative source paths inspected
- `src/script/campaign/mod/vco-listeners.lua`

### Source-level finding
Uses first-tick registration, event-specific listeners, model traversal, saved counters and faction-specific objective evaluators.

### Concrete value to this project
Adapt its clean event-to-check-to-state-update shape for strategic objective evaluators and faction policy modules.

### Risks / limits
It is an objective framework, not a general AI. Avoid conflating mission completion checks with planning.

## 7. Cost-based Army Caps (CBAC)

**Repository:** https://github.com/msolefonte/tww3-cbac  
**Pinned revision inspected:** `719fbbda4190fe66558c693e6e6c7e0f9947bd9c`  
**License status:** `Apache-2.0`  
**Primary layer:** WH3 AI policy intervention  
**Acquisition decision:** `COPY_OK`  
**Priority:** `P0/P1`

### Representative source paths inspected
- `src/script/campaign/mod/cbac-ai.lua`
- `src/script/campaign/mod/cbac-sl.lua`

### Source-level finding
At FactionTurnStart, inspects AI armies, caches a recruitment-cost pool, detects policy violations, replaces units and reimburses the faction. It demonstrates indirect control around CA's opaque planner.

### Concrete value to this project
Use its bounded policy-enforcement pattern for composition constraints, emergency corrections and post-planner safeguards.

### Risks / limits
One path uses math.random rather than the engine RNG; audit determinism before reuse. Replacing units is corrective intervention, not genuine strategic reasoning.

## 8. Warhammer 3 Mod Manager

**Repository:** https://github.com/Shazbot/WH3-Mod-Manager  
**Pinned revision inspected:** `68305199591939931a508b4f87bc252154d2da13`  
**License status:** `MIT`  
**Primary layer:** Compatibility and pack inspection  
**Acquisition decision:** `VENDOR_OR_WRAP`  
**Priority:** `P0/P1`

### Representative source paths inspected
- `src/packFileSerializer.ts`
- `src/components/CompatScreen.tsx`
- `src/nodeExecutor.ts`
- `test/`

### Source-level finding
Parses packs, displays DB data, computes load-order overwrite/compatibility information and has a testable Electron/TypeScript codebase.

### Concrete value to this project
Reuse or invoke its conflict-analysis ideas to create CI that reports table/script collisions against a benchmark mod list.

### Risks / limits
Desktop application concerns should not leak into runtime. Prefer a small library/CLI boundary or generated compatibility report.

## 9. Consul Scriptum

**Repository:** https://github.com/solon-the-wise/consul-scriptum  
**Pinned revision inspected:** `PIN_DURING_ACQUISITION`  
**License status:** `GPL-3.0`  
**Primary layer:** Total War live scripting/debugging  
**Acquisition decision:** `IDEAS_ONLY`  
**Priority:** `P1`

### Representative source paths inspected
- `script runner/console implementation`
- `script object lifecycle and event-handler maps`

### Source-level finding
Open-source in-game scripting console for earlier Total War titles, using protected dynamic script execution and lifecycle-oriented script objects.

### Concrete value to this project
Study its interactive console, hot-run workflow, command history, pcall isolation and start/stop script lifecycle for a WH3 developer harness.

### Risks / limits
Not a WH3 implementation and GPL-3.0. Reimplement behavior cleanly unless the whole relevant component is license-compatible.

## 10. Total War Simulator / Total War: AI

**Repository:** https://github.com/MichelangeloConserva/TotalWarSimulator  
**Pinned revision inspected:** `98e37e86c6f1c121643b2a961fba04f12a836342`  
**License status:** `MIT`  
**Primary layer:** Offline battle simulator  
**Acquisition decision:** `VENDOR_OR_WRAP`  
**Priority:** `P0/P1`

### Representative source paths inspected
- `Assets/Scripts/Simpler/CUnit.cs`
- `Assets/Scripts/Restart/CUnitNew.cs`
- `Assets/`

### Source-level finding
Unity battle simulator with unit paths, formation-slot assignment, combat-state transitions, melee/ranged/cavalry mechanics and an AI-research goal.

### Concrete value to this project
Fork as a starting surrogate battle lab or extract formation/assignment experiments. Use it to test algorithms before expensive WH3 runs.

### Risks / limits
Unity 2019-era simplified physics and mechanics differ greatly from WH3. It must be calibrated against telemetry and never treated as a faithful forward model without validation.

## 11. Stratega

**Repository:** https://github.com/GAIGResearch/Stratega  
**Pinned revision inspected:** `c9e94295397cd3b0cff91b269a1f12e0a8b28494`  
**License status:** `VERIFY_AT_PIN`  
**Primary layer:** General RTS/TBS forward-model research  
**Acquisition decision:** `VENDOR_OR_WRAP`  
**Priority:** `P0/P1`

### Representative source paths inspected
- `src/stratega/include/Stratega/ForwardModel/ForwardModel.h`
- `src/stratega/src/ForwardModel/RTSForwardModel.cpp`
- `src/stratega/include/Stratega/ForwardModel/ActionSpace.h`

### Source-level finding
Separates state, legal action generation, action assignment, conditions/effects and state advancement; explicitly supports reduced forward models for search/training.

### Concrete value to this project
Best reference for a project-owned abstract campaign/battle forward model and action-space contract used by search and offline evaluation.

### Risks / limits
C++ research environment is not a WH3 runtime dependency. Port abstractions and test against real telemetry.

## 12. OpenRA

**Repository:** https://github.com/OpenRA/OpenRA  
**Pinned revision inspected:** `c3f5e3ace2e960db64a21da041dba7fb1d9765c4`  
**License status:** `GPL-3.0-or-later`  
**Primary layer:** Production RTS AI architecture  
**Acquisition decision:** `IDEAS_ONLY`  
**Priority:** `P0`

### Representative source paths inspected
- `OpenRA.Mods.Common/Traits/BotModules/SquadManagerBotModule.cs`
- `OpenRA.Mods.Common/Traits/BotModules/Squads/Squad.cs`
- `OpenRA.Mods.Common/Traits/BotModules/Squads/States/GroundStates.cs`
- `OpenRA.Mods.Common/Traits/BotModules/UnitBuilderBotModule.cs`

### Source-level finding
Data-driven bot modules, squad role assignment, staggered update intervals, target filters, visibility checks, path-aware target reachability, attack/defense states and saveable bot data.

### Concrete value to this project
Adopt the modular bot-manager shape, update staggering, explicit squad roles, state machines and debug-state visibility.

### Risks / limits
GPL and engine-specific C#. Use patterns unless project licensing deliberately accommodates direct reuse.

## 13. UAlbertaBot

**Repository:** https://github.com/davechurchill/ualbertabot  
**Pinned revision inspected:** `558899d8793456f4a6ec4196efbb5235552e24db`  
**License status:** `VERIFY_AT_PIN`  
**Primary layer:** Competitive RTS bot  
**Acquisition decision:** `PORT_ALGORITHM`  
**Priority:** `P0/P1`

### Representative source paths inspected
- `UAlbertaBot/Source/GameCommander.cpp`
- `UAlbertaBot/Source/StrategyManager.cpp`
- `UAlbertaBot/Source/CombatCommander.cpp`
- `UAlbertaBot/Source/ProductionManager.cpp`
- `UAlbertaBot/Source/Squad.cpp`
- `UAlbertaBot/Source/BOSSManager.cpp`

### Source-level finding
Thin top-level commander delegates to strategy, production, combat, scouting and squad systems; includes build-order search and combat simulation components.

### Concrete value to this project
Use its manager boundaries and explicit command pipeline as a strong template for strategic, operational and tactical decomposition.

### Risks / limits
StarCraft/BWAPI assumptions and high-APM economy differ from Total War. Port interfaces and algorithms selectively.

## 14. python-sc2

**Repository:** https://github.com/BurnySc2/python-sc2  
**Pinned revision inspected:** `81d66110cb0aa57cc7c2895dad207775e496fbd1`  
**License status:** `MIT`  
**Primary layer:** RTS observation/action adapter  
**Acquisition decision:** `PORT_ALGORITHM`  
**Priority:** `P1`

### Representative source paths inspected
- `sc2/bot_ai.py`
- `sc2/bot_ai_internal.py`
- `sc2/units.py`
- `sc2/cache.py`
- `examples/competitive/bot.py`

### Source-level finding
Normalizes game observations into a bot API, separates public and internal lifecycle logic, caches expensive queries, and supports reproducible example agents.

### Concrete value to this project
Model the WH3 adapter and immutable snapshot API after this separation: engine details at the edge, clean domain queries and orders in the core.

### Risks / limits
SC2 has a supported external API; WH3 does not expose an equivalent full observation/order protocol.

## 15. microRTS

**Repository:** https://github.com/santiontanon/microrts  
**Pinned revision inspected:** `PIN_DURING_ACQUISITION`  
**License status:** `VERIFY_AT_PIN`  
**Primary layer:** Deterministic RTS search testbed  
**Acquisition decision:** `BENCHMARK_ONLY`  
**Priority:** `P1`

### Representative source paths inspected
- `src/rts/GameState.java`
- `src/rts/PlayerAction.java`
- `src/rts/UnitAction.java`
- `src/ai/abstraction/`
- `src/ai/mcts/`

### Source-level finding
Purpose-built compact RTS research environment with hard-coded rush policies, minimax/Monte Carlo/MCTS variants, action abstraction and explicit computation budgets.

### Concrete value to this project
Use as a controlled algorithm bake-off environment and a reference for budgeted search, action abstraction and tournament evaluation.

### Risks / limits
Tiny grid RTS dynamics are far removed from WH3 formations, morale, terrain, spells and campaign state.

## 16. Gym-µRTS

**Repository:** https://github.com/vwxyzjn/gym-microrts  
**Pinned revision inspected:** `PIN_DURING_ACQUISITION`  
**License status:** `VERIFY_AT_PIN`  
**Primary layer:** RL environment and action masking  
**Acquisition decision:** `BENCHMARK_ONLY`  
**Priority:** `P2`

### Representative source paths inspected
- `gym_microrts/`
- `experiments/`
- `action-mask and vector environment implementation`

### Source-level finding
Defines structured observation planes, multi-discrete actions, legal-action masking, vectorized environments and affordable full-game RTS RL experiments.

### Concrete value to this project
Borrow action-mask, curriculum, vector-evaluation and reproducible-training ideas for the offline surrogate—not for direct WH3 runtime control.

### Risks / limits
Reward hacking, simulator mismatch and large validation burden. Do not make RL a prerequisite for the first competent release.

## 17. VCMI Nullkiller AI

**Repository:** https://github.com/vcmi/vcmi  
**Pinned revision inspected:** `24579d36addd8e169e794f9fe5060f29c8c2e1cf`  
**License status:** `GPL-2.0-or-later`  
**Primary layer:** Turn-based campaign-map AI  
**Acquisition decision:** `IDEAS_ONLY`  
**Priority:** `P0/P1`

### Representative source paths inspected
- `AI/Nullkiller2/AIGateway.h`
- `AI/Nullkiller2/`
- `docs/developers/AI.md`
- `test/vcai/`

### Source-level finding
A dedicated AI subsystem with gateway boundary, goal/resource logic and mock-based tests for campaign-map decisions.

### Concrete value to this project
Study danger assessment, goal decomposition, hero/army tasking and the use of mocks to test strategic logic without launching the game.

### Risks / limits
Heroes III rules and GPL licensing. Transfer architecture, not code.

## 18. FreeOrion AI

**Repository:** https://github.com/freeorion/freeorion  
**Pinned revision inspected:** `5bd515c2f5237991e39406a699b8a36747bbaf29`  
**License status:** `GPL-2.0`  
**Primary layer:** Persistent 4X strategic AI  
**Acquisition decision:** `IDEAS_ONLY`  
**Priority:** `P0`

### Representative source paths inspected
- `default/python/AI/AIstate.py`
- `default/python/AI/FreeOrionAI.py`
- `default/python/AI/generate_orders.py`
- `default/python/AI/PriorityAI.py`
- `default/python/AI/DiplomaticCorp.py`
- `default/python/AI/fleet_orders.py`
- `default/python/AI/savegame_codec/`

### Source-level finding
Persistent AI state, priority calculation, diplomacy, research/production, exploration, fleet mission assignment, order generation and explicit savegame codecs.

### Concrete value to this project
Excellent model for campaign-phase decomposition, persisted strategic state and separating priority formation from order emission.

### Risks / limits
Turn-based space-4X abstractions and GPL; patterns only.

## 19. The Battle for Wesnoth AI

**Repository:** https://github.com/wesnoth/wesnoth  
**Pinned revision inspected:** `e1e8d55f6ff482d9d6e615136dca61615180452d`  
**License status:** `GPL-2.0-or-later`  
**Primary layer:** Explainable candidate-action AI  
**Acquisition decision:** `IDEAS_ONLY`  
**Priority:** `P0`

### Representative source paths inspected
- `src/ai/composite/rca.cpp`
- `src/ai/default/stage_rca.cpp`
- `data/core/macros/ai_candidate_actions.cfg`
- `src/ai/lua/engine_lua.cpp`
- `data/ai/micro_ais/mai-defs/`

### Source-level finding
Candidate actions evaluate applicability and score before execution; Lua extension and focused micro-AIs support regroup, protect and recruiting behavior.

### Concrete value to this project
Adopt candidate-action/utility evaluation as the default explainable decision kernel and use focused micro-policies rather than one giant planner.

### Risks / limits
Hex turn-based combat and GPL. Transfer design and tests, not implementation.

## 20. Widelands AI

**Repository:** https://github.com/widelands/widelands  
**Pinned revision inspected:** `7c5655c2243068b7af96bdba855e74476a817092`  
**License status:** `GPL-2.0`  
**Primary layer:** Long-horizon economy/logistics AI  
**Acquisition decision:** `IDEAS_ONLY`  
**Priority:** `P1`

### Representative source paths inspected
- `src/ai/computer_player.h`
- `src/ai/defaultai.h`
- `src/ai/`

### Source-level finding
Production-game AI focused on construction, resources, logistics, expansion and military interaction under long time horizons.

### Concrete value to this project
Mine for bottleneck detection, construction prioritization, resource reservation and periodic work scheduling relevant to WH3 economy/building policy.

### Risks / limits
Economic network mechanics are unlike WH3 province slots; GPL.

## 21. Warzone 2100 SemperFi AI

**Repository:** https://github.com/Warzone2100/warzone2100  
**Pinned revision inspected:** `e192d36abc687522184ecd9cc7b8862eafefcf5b`  
**License status:** `GPL-2.0-or-later`  
**Primary layer:** Event-driven scripted RTS AI  
**Acquisition decision:** `IDEAS_ONLY`  
**Priority:** `P1`

### Representative source paths inspected
- `data/mp/multiplay/skirmish/semperfi.js`
- `data/mp/multiplay/skirmish/semperfi_includes/events.js`
- `data/mp/multiplay/skirmish/semperfi_includes/build.js`
- `doc/Scripting.md`

### Source-level finding
Script-level skirmish AI split into event handling, build/economy logic and combat behavior.

### Concrete value to this project
Useful analogue for a Lua/JS event-driven AI living above an engine-owned simulation, particularly scheduling and modular script layout.

### Risks / limits
Full skirmish scripting API is richer than WH3’s general campaign/battle surfaces; GPL.

## 22. DCS Dynamic Campaign Tools (DCT)

**Repository:** https://github.com/jtoppins/dct  
**Pinned revision inspected:** `bb75e190160e8925d51ef81c23b8594376971c36`  
**License status:** `LGPL-3.0`  
**Primary layer:** Persistent theater/commander system  
**Acquisition decision:** `PORT_ALGORITHM`  
**Priority:** `P0/P1`

### Representative source paths inspected
- `src/dct/Theater.lua`
- `src/dct/ai/Commander.lua`
- `src/dct/systems/tickets.lua`
- `src/dct/settings/`
- `src/dct/ui/`

### Source-level finding
Persistent theater object, AI commander, asset/template systems, ticket/resource system, settings and UI around a Lua-scripted military campaign.

### Concrete value to this project
Strong conceptual match for WH3 theaters, strategic objectives, asset assignment and bounded resource accounting.

### Risks / limits
DCS mission API and real-time theater assumptions differ; LGPL obligations require care if code is ported.

## 23. Fluid HTN

**Repository:** https://github.com/ptrefall/fluid-hierarchical-task-network  
**Pinned revision inspected:** `e67af264cfdf240053f392d4e0e6c620c454eb97`  
**License status:** `MIT`  
**Primary layer:** Hierarchical planning  
**Acquisition decision:** `PORT_ALGORITHM`  
**Priority:** `P1`

### Representative source paths inspected
- `Fluid-HTN/Planners/Planner.cs`
- `Fluid-HTN/BaseDomainBuilder.cs`
- `Fluid-HTN/Contexts/BaseContext.cs`
- `Fluid-HTN.UnitTests/`

### Source-level finding
Tested HTN decomposition with explicit contexts, conditions, effects, planner state and domain builders.

### Concrete value to this project
Port a minimal deterministic HTN kernel only for decisions that genuinely benefit from multi-step decomposition, such as invasion preparation or siege continuation.

### Risks / limits
Do not use HTN for every choice. Runtime is C#, so Lua port and property tests are required.

## 24. BehaviorTree.CPP

**Repository:** https://github.com/BehaviorTree/BehaviorTree.CPP  
**Pinned revision inspected:** `879522c75cce5e67f3dd7b5591bcb96eb3557a42`  
**License status:** `MIT`  
**Primary layer:** Reactive execution and debugging  
**Acquisition decision:** `PORT_ALGORITHM`  
**Priority:** `P1`

### Representative source paths inspected
- `include/behaviortree_cpp/bt_factory.h`
- `include/behaviortree_cpp/tree_node.h`
- `include/behaviortree_cpp/xml_parsing.h`
- `examples/ex03_sqlite_log.cpp`

### Source-level finding
Factory-registered nodes, typed ports/blackboards, runtime tree loading, reactive/asynchronous execution and logging examples.

### Concrete value to this project
Borrow node contracts, blackboard typing, cancellation and trace tooling for tactical execution plans; implement a small Lua-native subset.

### Risks / limits
A full C++ library cannot run in normal WH3 Lua. Avoid recreating a huge generic editor before proving need.

## 25. Beyond All Reason — headless testing corpus

**Repository:** https://github.com/beyond-all-reason/Beyond-All-Reason  
**Pinned revision inspected:** `d706b5c6aec96c0d0cf25a692ee41b1da18981d3`  
**License status:** `VERIFY_PER_COMPONENT`  
**Primary layer:** Large-scale RTS testing  
**Acquisition decision:** `IDEAS_ONLY`  
**Priority:** `P2`

### Representative source paths inspected
- `tools/headless_testing/startscript_barb_smoke.txt`
- `tools/StartScripts/`
- `singleplayer/scenarios/`

### Source-level finding
Repository includes headless smoke scripts, deterministic start scripts and scenario content used to exercise AI/game behavior.

### Concrete value to this project
Emulate the scenario-as-code and smoke-test workflow even though WH3 itself may require UI-driven runs.

### Risks / limits
AI implementation is spread across Spring/BAR components; verify component licenses and canonical AI upstream before any copying.



# Recommended acquisition decision

## Copy/adapt candidates
Subject to exact-file review and notices:

- RPFM integration/API use
- RPFM schema pinning
- Warhammer 3 TypeScript framework utilities
- VCO event/check structure
- CBAC bounded policy enforcement
- Fluid HTN concepts or a small port
- BehaviorTree.CPP concepts or a small port

## Architecture-only references
Because of engine mismatch, copyleft, or excessive integration size:

- OpenRA
- UAlbertaBot
- VCMI
- FreeOrion
- Wesnoth
- Widelands
- Warzone 2100
- DCT unless isolated LGPL-compatible reuse is selected

## Research/benchmark references

- TotalWarSimulator
- Stratega
- microRTS
- Gym-µRTS
- Beyond All Reason testing corpus

# Do-not-reinvent list

Do not write from scratch unless a concrete incompatibility is proven:

- PackFile parsing/writing
- WH3 DB schema decoding
- generic conflict/load-order detection
- a generic behavior-tree editor
- a large general-purpose HTN framework
- generic replay/telemetry storage
- generic assignment/Hungarian/min-cost-flow algorithms
- generic parameter-search infrastructure
- a full RL environment before a calibrated simulator exists

# What this project must own

- capability matrix for WH3;
- canonical observation and decision schemas;
- faction doctrine model;
- strategic theater model;
- army-role and objective-assignment semantics;
- fairness modes;
- validation/fallback rules;
- explainable scoring and decision traces;
- benchmark corpus and metrics;
- telemetry-to-surrogate calibration;
- game-version adapters;
- integration, compatibility and player-facing behavior.

# Required second-pass audits before copying code

For every `COPY_OK`, `VENDOR_OR_WRAP`, or `PORT_ALGORITHM` candidate:

1. pin a tag/commit;
2. archive license and notices;
3. inspect all transitive files to be copied;
4. enumerate external dependencies;
5. identify global state/threading/randomness;
6. run upstream tests;
7. write equivalent project fixtures;
8. record copied lines/files and local modifications;
9. scan packaged artifacts for accidental upstream contamination;
10. approve through an ADR.

# WH3 Native Campaign AI — Primary-Source Fact Freeze

**Date:** 2026-08-02  
**Scope:** facts established from Creative Assembly material relevant to the Native CAI Reconciliation gate.  
**Important:** numeric values disclosed in 2025 beta material are historical/beta evidence unless current 8.1 rows independently confirm them.

## Current 8.1 fact: turn-dependent task prioritisation exists

Creative Assembly Patch 8.1 (2026-07-09) states that it added a mechanism controlling Campaign AI priorities depending on turns elapsed since campaign start. CA says it used the mechanism to de-prioritise some late-game defensive tasks and slightly increase priority for tasks targeting enemy forces.

Source:
- https://community.creative-assembly.com/total-war/total-war-warhammer/blogs/101-total-war-warhammer-iii-patch-8-1-release-notes

**Established:** native Campaign AI task priority can be modulated by campaign turn/progression in current 8.1 behavior.  
**Not established:** the exact DB table, field, variable, or script exposure. That remains `UNVERIFIED` until schema/row reconciliation.

Patch 8.1 also explicitly lists residual clumping/standoff cases, including bordering end-game factions, simultaneous end-game scenarios, and situations involving similarly matched autoresolve strength. Therefore 8.1 is not evidence that late-game strategic behavior is solved.

## Shipped/native architecture fact: generation, allocation and batching exist

Creative Assembly Hotfix 6.3.4 describes Campaign AI task processing as two steps: generation and allocation. Multiple task generators can contribute to one task. During allocation, tasks and armies are paired, followed by additional batching; CA defines batching as combining tasks with the same type and target. CA also describes a sufficient-strength prerequisite for assignment against stronger enemies and recruitment/disbanding responses when a force is too weak.

Source:
- https://community.creative-assembly.com/total-war/total-war-warhammer/forums/7-patch-notes-amp-announcements/threads/11820-total-war-warhammer-iii-hotfix-6-3-4

**Established at responsibility level:**
- native task generation;
- multiple generator contribution;
- task/army pairing during allocation;
- same-type/same-target batching;
- force-strength gating relevant to assignment;
- recruitment/disbanding can participate when strength is insufficient.

**Not established:** native assignment exclusivity, explicit reserve preservation, recovery protection, cross-turn plan memory, hysteresis, or project-style critical overflow.

## Shipped/beta-described fact: threat and strength are distinct systems

Creative Assembly's 2025 Campaign AI Part 2 describes distinct threat and strength scales. Threat feeds deal evaluation, diplomatic attitude and task generation. Strength evaluation considers units, experience, bonuses and stances; when a task is evaluated, CA says owned forces are evaluated to find a force that can be resourced against the target, with strength ratio important and recruitment needed when no sufficient force is available.

Source:
- https://community.creative-assembly.com/total-war/total-war-warhammer/blogs/69%20style%3Dbutton

**Established at mechanism/responsibility level:** threat evaluation influences multiple strategic systems; strength evaluation and force selection are materially richer than the project v0.2G geometric scorer.

**Historical numeric caveat:** the player threat/strength multipliers and exact distance floors shown in that beta are not automatically current 8.1 values.

## Shipped/beta-described fact: distance is measured in turns and is stance-aware

The same CA Part 2 source says task priority is modified by target distance before assignment to a resource; distance is measured in turns, incorporates movement extents and, where appropriate, stances such as tunneling/forced march. A newly hired army additionally includes recruitment-region distance and recruitment time.

This establishes a concrete information disadvantage for v0.2G's application allocator: its `hypot(dx,dy)/movement` reference cannot be assumed to outperform native selection because it omits route/stance/recruitment information CA says native uses.

## Shipped/beta-described fact: foreign-threat query system and influence map exist

Creative Assembly's Campaign AI Part 1 describes two mechanisms for detecting foreign threats: a query system and an influence map representing force range and strength of interaction with map assets. CA also describes a query bug where agents were being treated in ways that over-triggered defensive behavior.

Source:
- https://community.creative-assembly.com/total-war/total-war-warhammer/blogs/65Abonne

**Established:** native foreign-threat sensing is not equivalent to Transcendence's simple geometric front proxy.  
**Not established:** exact public schema names for either internal subsystem.

## Research consequences

These facts are sufficient to reject a default assumption that Transcendence must own strategic task generation or army allocation. They are **not** sufficient to prove native CAI satisfies the project's experience goals. The reconciliation gate therefore measures native behavior, decodes public tuning surfaces, and only promotes project control after a specific native failure survives native tuning and narrower correction.

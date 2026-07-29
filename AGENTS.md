# AGENTS.md — WH3 AI Project Constitution

## Mission

Build the strongest practical, enjoyable, explainable and maintainable AI/gameplay enhancement possible for the owner's personal Total War: WARHAMMER III experience, centered on SFO: Grimhammer III.

## Canonical authority

Repository state overrides chat memory. Read the research files and active gate before changing architecture.

## Capability labels

Every game interaction must be classified as `CONTROL`, `INFLUENCE`, `OBSERVE`, `UNAVAILABLE`, or `UNVERIFIED`.

Do not label a database tweak or scripted correction as a replacement for Creative Assembly's internal AI.

## Core invariants

- Project-owned canonical state.
- Observation, belief, objective, candidate action, selected order, acknowledgement and outcome are distinct.
- Any model or LLM is replaceable and bounded.
- All orders require legality, capability, fairness and budget validation.
- Deterministic fallbacks exist.
- Raw evidence is preserved.
- Runtime and offline research remain separate.
- Third-party code and assets require provenance and license records.
- Creative Assembly, SFO, saves and personal artifacts stay out of Git.

## Engineering preference

Use the simplest system that passes the benchmark: constraints → utility → state machines → assignment → behavior trees → HTN/search → learning → LLM proposals.

## Completion

A gate passes only with preserved evidence, repeated tests where appropriate, regression coverage, hashes/configuration and an explicit statement of remaining uncertainty.

# Decision Log

## 2026-07-28 — D001: Two-layer agent instructions

**Decision:** Keep durable rules in `AGENTS.md` and repository research files. Use `prompts/CONTINUE_PROJECT.md` as the reusable autonomous continuation request.

**Reason:** A large kickoff prompt is good at establishing architecture but becomes stale and inefficient once the repository contains canonical truth.

## 2026-07-28 — D002: Personal SFO-first product

**Decision:** Optimize first for the owner's private SFO single-player experience rather than a generic public Workshop mod.

**Reason:** This permits tighter benchmarks, sharper experience goals and controlled compatibility scope.

## 2026-07-28 — D003: Gate 0 before gameplay AI

**Decision:** Freeze the actual install/mod/settings/save baseline and capability truth before implementing AI behavior.

**Reason:** WH3 exposes uneven scripting authority, and SFO changes broad campaign and battle systems. Building against assumptions would create expensive architectural rework.

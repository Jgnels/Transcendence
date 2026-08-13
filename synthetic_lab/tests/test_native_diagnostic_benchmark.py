from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from transcendence_lab.native_diagnostic_benchmark import (
    RESULT_CONTRACT,
    analyze_sfo_benchmark,
    benchmark_spec_digest,
    stratify_temporal_trace,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
VANILLA_REFERENCE = REPO_ROOT / "research/runtime_evidence/NATIVE_BEHAVIOR_STUDY_VANILLA_REFERENCE_v0.2O_2026-08-03.json"


def force(cqi: int, x: float, *, region: str = "r") -> dict:
    return {
        "force_cqi": cqi,
        "x": x,
        "y": 0.0,
        "average_unit_health_pct": 100.0,
        "force_strength": 1000.0,
        "unit_count": 20,
        "stance": "MILITARY_FORCE_ACTIVE_STANCE_TYPE_DEFAULT",
        "region": region,
    }


def snapshot(index: int, subject: dict, *, regions: tuple[str, ...]) -> dict:
    return {
        "forces": [copy.deepcopy(subject)],
        "wars": [{"enemy": "enemy"}],
        "regions": [{"region": region} for region in regions],
        "begin_event_index": index,
        "end_event_index": index + 9,
    }


def trace(*, territorial: bool = True, turns: int = 23) -> dict:
    observations = []
    region_set = ("home",) if territorial else ()
    for turn in range(1, turns + 1):
        x = 0.0 if turn % 2 else 10.0
        subject = force(1, x)
        base = turn * 100
        observations.append({
            "turn": turn,
            "faction": "ai",
            "start": snapshot(base, subject, regions=region_set),
            "end": snapshot(base + 80, subject, regions=region_set),
        })
    return {
        "contract": "NATIVE_CAI_PRIVILEGED_DIAGNOSTIC_PARSED_TRACE_V2",
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "research_visibility": "PRIVILEGED_OMNISCIENT_DIAGNOSTIC",
        "application_eligible": False,
        "battle_participant_telemetry_declared": True,
        "observations": observations,
        "battle_sequences": [],
        "incomplete_battle_sequences": [],
    }


class NativeDiagnosticBenchmarkTests(unittest.TestCase):
    def test_population_stratification_keeps_nonterritorial_separate(self) -> None:
        territorial = stratify_temporal_trace(trace(territorial=True))
        nonterritorial = stratify_temporal_trace(trace(territorial=False))
        self.assertGreaterEqual(territorial["territorial"]["eligible_windows"], 20)
        self.assertEqual(territorial["nonterritorial"]["eligible_windows"], 0)
        self.assertGreaterEqual(nonterritorial["nonterritorial"]["eligible_windows"], 20)
        self.assertEqual(nonterritorial["territorial"]["eligible_windows"], 0)

    def test_sfo_benchmark_can_flag_repeated_territorial_signal_without_authority_change(self) -> None:
        reference = json.loads(VANILLA_REFERENCE.read_text(encoding="utf-8"))
        result = analyze_sfo_benchmark(trace(territorial=True), reference)
        self.assertEqual(result["contract"], RESULT_CONTRACT)
        self.assertEqual(result["benchmark_spec_digest"], benchmark_spec_digest())
        self.assertEqual(result["primary_territorial_temporal_status"], "REPEATED_TERRITORIAL_REVERSAL_SIGNAL_OBSERVED")
        self.assertFalse(result["application_eligible"])
        self.assertEqual(result["authority"], "NO_ORDERS")
        self.assertEqual(result["application_authority"], "PROHIBITED")
        self.assertNotIn("ISSUE", result["architecture_action"])

    def test_vanilla_reference_identity_is_fail_closed(self) -> None:
        reference = json.loads(VANILLA_REFERENCE.read_text(encoding="utf-8"))
        reference["source_bundle"]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            analyze_sfo_benchmark(trace(territorial=True), reference)


class NativeSfoMechanisticPrecommitTests(unittest.TestCase):
    def test_vanilla_cluster_reference_matches_frozen_sensitivity_envelope(self) -> None:
        from transcendence_lab.native_sfo_mechanistic import VANILLA_TERRITORIAL_LOO_MAX, VANILLA_TERRITORIAL_LOO_MIN
        path = REPO_ROOT / "research/runtime_evidence/NATIVE_VANILLA_TERRITORIAL_CLUSTER_REFERENCE_v0.2P_2026-08-04.json"
        obj = json.loads(path.read_text(encoding="utf-8"))
        cluster = obj["cluster_diagnostics"]
        self.assertEqual(cluster["eligible_windows"], 48)
        self.assertEqual(cluster["reversal_candidates"], 13)
        self.assertEqual(cluster["leave_one_faction_out"]["rate_min"], VANILLA_TERRITORIAL_LOO_MIN)
        self.assertEqual(cluster["leave_one_faction_out"]["rate_max"], VANILLA_TERRITORIAL_LOO_MAX)
        self.assertEqual(len(cluster["candidate_windows"]), 13)
        self.assertIn("NO_P_VALUE_AUTHORIZED", cluster["interpretation"])

    def test_sfo_registry_proves_captured_priority_only_footprint_direction(self) -> None:
        path = REPO_ROOT / "research/native_cai/SFO_NATIVE_CAI_MECHANISTIC_REGISTRY_v0.2P_2026-08-04.json"
        obj = json.loads(path.read_text(encoding="utf-8"))
        footprint = obj["captured_sfo_cai_footprint"]
        self.assertFalse(footprint["allocator_table"]["direct_sfo_allocator_override_observed"])
        self.assertEqual(footprint["allocator_table"]["changed_rows"], 0)
        task = footprint["task_priority_table"]
        self.assertEqual(task["rows_carried"], 93)
        self.assertEqual(task["changed_priority_rows"], 88)
        self.assertEqual(task["priority_increases"], 88)
        self.assertEqual(task["priority_decreases"], 0)
        self.assertEqual(task["distinct_generator_groups_changed"], 30)

    def test_post_sfo_temporal_branches_are_direction_aware_and_fail_closed(self) -> None:
        from transcendence_lab.native_sfo_mechanistic import choose_temporal_branch
        insufficient = choose_temporal_branch(19, 0, 0)
        self.assertEqual(insufficient["branch"], "INSUFFICIENT_EXPOSURE")
        improvement = choose_temporal_branch(100, 20, 0)
        self.assertEqual(improvement["branch"], "LOWER_THAN_VANILLA_CLUSTER_ENVELOPE")
        self.assertIn("REPLICATION", improvement["action"])
        within = choose_temporal_branch(100, 27, 0)
        self.assertEqual(within["branch"], "WITHIN_VANILLA_CLUSTER_ENVELOPE")
        worsening = choose_temporal_branch(100, 40, 0)
        self.assertEqual(worsening["branch"], "HIGHER_THAN_VANILLA_CLUSTER_ENVELOPE")
        self.assertIn("DO_NOT_COPY", worsening["mechanistic_nomination"])
        repeated = choose_temporal_branch(100, 10, 1)
        self.assertEqual(repeated["branch"], "REPEATED_TERRITORIAL_SIGNAL")
        self.assertIn("DO_NOT_COPY", repeated["mechanistic_nomination"])

    def test_recovery_branch_cannot_nominate_direct_sfo_allocator_rows(self) -> None:
        from transcendence_lab.native_sfo_mechanistic import choose_recovery_branch
        positive = choose_recovery_branch(20, 5)
        self.assertEqual(positive["branch"], "SFO_RECOVERY_POSITIVE_SIGNAL")
        self.assertIn("DIRECT_SFO_ALLOCATOR_ATTRIBUTION_NOT_ELIGIBLE", positive["mechanistic_nomination"])
        negative = choose_recovery_branch(20, 3)
        self.assertEqual(negative["branch"], "SFO_RECOVERY_NO_PREREGISTERED_SIGNAL")
        self.assertEqual(negative["mechanistic_nomination"], "NONE")

    def test_static_mechanistic_artifacts_rebuild_deterministically_from_canonical_rows(self) -> None:
        from transcendence_lab.native_sfo_mechanistic import build_ablation_candidate_registry, build_sfo_mechanistic_registry, post_sfo_decision_table
        row_diff = json.loads((REPO_ROOT / "research/native_cai/NATIVE_CAI_ROW_DIFFS_2026-08-02.json").read_text(encoding="utf-8"))
        mechanism = build_sfo_mechanistic_registry(row_diff)
        ablation = build_ablation_candidate_registry(mechanism)
        decision = post_sfo_decision_table()
        self.assertEqual(mechanism, json.loads((REPO_ROOT / "research/native_cai/SFO_NATIVE_CAI_MECHANISTIC_REGISTRY_v0.2P_2026-08-04.json").read_text(encoding="utf-8")))
        self.assertEqual(ablation, json.loads((REPO_ROOT / "research/native_cai/NATIVE_CAI_ABLATION_CANDIDATE_REGISTRY_v0.2P_2026-08-04.json").read_text(encoding="utf-8")))
        self.assertEqual(decision, json.loads((REPO_ROOT / "research/native_cai/SFO_POST_BENCHMARK_DECISION_TABLE_v0.2P_2026-08-04.json").read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()

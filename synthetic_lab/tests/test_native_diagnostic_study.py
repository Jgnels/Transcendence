from __future__ import annotations

import copy
import unittest

from transcendence_lab.native_diagnostic_study import (
    NativeDiagnosticStudyError,
    analyze_native_diagnostic_behavior_study,
    frozen_thresholds_digest,
)


def force(cqi: int, x: float, y: float = 0.0, *, health: float = 100.0, strength: float = 1000.0,
          units: int = 20, stance: str = "MILITARY_FORCE_ACTIVE_STANCE_TYPE_DEFAULT", region: str = "r") -> dict:
    return {
        "force_cqi": cqi,
        "x": x,
        "y": y,
        "average_unit_health_pct": health,
        "force_strength": strength,
        "unit_count": units,
        "stance": stance,
        "region": region,
    }


def snapshot(index: int, *forces: dict, wars: tuple[str, ...] = (), regions: tuple[str, ...] = ("home",)) -> dict:
    return {
        "forces": list(forces),
        "wars": [{"enemy": enemy} for enemy in wars],
        "regions": [{"region": region} for region in regions],
        "begin_event_index": index,
        "end_event_index": index + 9,
    }


def observation(turn: int, faction: str, subject: dict, *, wars: tuple[str, ...] = (), regions: tuple[str, ...] = ("home",)) -> dict:
    base = turn * 100
    return {
        "turn": turn,
        "faction": faction,
        "start": snapshot(base, copy.deepcopy(subject), wars=wars, regions=regions),
        "end": snapshot(base + 80, copy.deepcopy(subject), wars=wars, regions=regions),
    }


def trace(observations: list[dict], battles: list[dict] | None = None) -> dict:
    return {
        "contract": "NATIVE_CAI_PRIVILEGED_DIAGNOSTIC_PARSED_TRACE_V2",
        "authority": "NO_ORDERS",
        "application_authority": "PROHIBITED",
        "research_visibility": "PRIVILEGED_OMNISCIENT_DIAGNOSTIC",
        "application_eligible": False,
        "battle_participant_telemetry_declared": True,
        "observations": observations,
        "battle_sequences": battles or [],
        "incomplete_battle_sequences": [],
    }


def battle(seq: int, turn: int, event_index: int, faction: str, force_cqi: int, side: str) -> dict:
    return {
        "battle_sequence": seq,
        "turn": turn,
        "begin_event_index": event_index,
        "participants": [{"faction": faction, "force_cqi": force_cqi, "side": side}],
        "complete": True,
    }


class NativeDiagnosticStudyTests(unittest.TestCase):
    def test_research_boundary_and_threshold_digest_are_deterministic(self) -> None:
        rows = [observation(turn, "ai", force(1, turn * 10.0)) for turn in range(1, 5)]
        first = analyze_native_diagnostic_behavior_study(trace(rows))
        second = analyze_native_diagnostic_behavior_study(copy.deepcopy(trace(rows)))
        self.assertEqual(first, second)
        self.assertEqual(first["frozen_thresholds_digest"], frozen_thresholds_digest())
        self.assertFalse(first["application_eligible"])
        self.assertEqual(first["authority"], "NO_ORDERS")
        self.assertEqual(first["application_authority"], "PROHIBITED")

    def test_old_no_battle_channel_trace_is_structurally_nonconfirmatory(self) -> None:
        raw = trace([observation(1, "ai", force(1, 0))])
        raw["battle_participant_telemetry_declared"] = False
        with self.assertRaises(NativeDiagnosticStudyError):
            analyze_native_diagnostic_behavior_study(raw)

    def test_privileged_study_refuses_application_eligible_trace(self) -> None:
        raw = trace([])
        raw["application_eligible"] = True
        with self.assertRaises(NativeDiagnosticStudyError):
            analyze_native_diagnostic_behavior_study(raw)

    def test_recovering_attacker_side_reentry_can_trigger_preregistered_signal(self) -> None:
        rows = []
        battles = []
        for turn in range(1, 11):
            subject = force(100 + turn, 0, health=50)
            rows.append(observation(turn, "ai", subject))
            if turn in (1, 2):
                battles.append(battle(turn, turn, turn * 100 + 50, "ai", 100 + turn, "ATTACKER"))
        result = analyze_native_diagnostic_behavior_study(trace(rows, battles))
        self.assertEqual(result["metrics"]["recovering_army_turn_count"], 10)
        self.assertEqual(result["metrics"]["recovering_attacker_side_army_turn_count"], 2)
        self.assertEqual(result["metrics"]["recovering_attacker_side_rate"], 0.2)
        self.assertEqual(result["recovery_status"], "RECOVERING_ATTACKER_SIDE_REENTRY_SIGNAL_OBSERVED")

    def test_recovering_defender_is_not_promoted_to_offensive_reentry(self) -> None:
        rows = []
        battles = []
        for turn in range(1, 11):
            subject = force(200 + turn, 0, health=50)
            rows.append(observation(turn, "ai", subject))
            if turn in (1, 2, 3):
                battles.append(battle(turn, turn, turn * 100 + 50, "ai", 200 + turn, "DEFENDER"))
        result = analyze_native_diagnostic_behavior_study(trace(rows, battles))
        self.assertEqual(result["metrics"]["recovering_defender_side_army_turn_count"], 3)
        self.assertEqual(result["metrics"]["recovering_attacker_side_army_turn_count"], 0)
        self.assertEqual(result["recovery_status"], "NO_PREREGISTERED_RECOVERY_SIGNAL_IN_COHORT")

    def test_recovery_endpoint_requires_exposure(self) -> None:
        rows = [observation(turn, "ai", force(300 + turn, 0, health=50)) for turn in range(1, 5)]
        result = analyze_native_diagnostic_behavior_study(trace(rows))
        self.assertEqual(result["recovery_status"], "INSUFFICIENT_RECOVERY_EXPOSURE")

    def test_repeated_battle_free_stable_context_reversal_triggers_temporal_signal(self) -> None:
        rows = []
        for turn in range(1, 24):
            x = 0.0 if turn % 2 else 10.0
            rows.append(observation(turn, "ai", force(1, x), wars=("enemy",), regions=("home",)))
        result = analyze_native_diagnostic_behavior_study(trace(rows))
        self.assertGreaterEqual(result["metrics"]["eligible_battle_free_stable_context_directional_windows"], 20)
        self.assertGreaterEqual(result["metrics"]["heading_reversal_candidate_count"], 2)
        self.assertEqual(result["temporal_status"], "REPEATED_BATTLE_FREE_REVERSAL_SIGNAL_OBSERVED")
        self.assertGreaterEqual(result["metrics"]["exact_region_ababa_signal_count"], 0)

    def test_overlapping_reversal_windows_do_not_satisfy_repeated_signal(self) -> None:
        rows = [observation(turn, "ai", force(1, 0 if turn % 2 else 10), wars=("enemy",)) for turn in range(1, 5)]
        result = analyze_native_diagnostic_behavior_study(trace(rows))
        self.assertEqual(result["metrics"]["heading_reversal_candidate_count"], 2)
        self.assertEqual(result["metrics"]["repeated_reversal_force_count"], 0)

    def test_battle_participation_excludes_heading_reversal_window(self) -> None:
        rows = [
            observation(1, "ai", force(1, 0)),
            observation(2, "ai", force(1, 10)),
            observation(3, "ai", force(1, 0)),
        ]
        battles = [battle(1, 2, 250, "ai", 1, "ATTACKER")]
        result = analyze_native_diagnostic_behavior_study(trace(rows, battles))
        self.assertEqual(result["metrics"]["eligible_battle_free_stable_context_directional_windows"], 0)
        self.assertEqual(result["metrics"]["heading_reversal_candidate_count"], 0)

    def test_context_change_excludes_heading_reversal_window(self) -> None:
        rows = [
            observation(1, "ai", force(1, 0), wars=("enemy",)),
            observation(2, "ai", force(1, 10), wars=("enemy", "new_enemy")),
            observation(3, "ai", force(1, 0), wars=("enemy",)),
        ]
        result = analyze_native_diagnostic_behavior_study(trace(rows))
        self.assertEqual(result["metrics"]["eligible_battle_free_stable_context_directional_windows"], 0)

    def test_exact_region_ababa_is_high_specificity_descriptive_signal(self) -> None:
        rows = []
        for turn, (x, region) in enumerate(((0, "A"), (10, "B"), (0, "A"), (10, "B"), (0, "A")), 1):
            rows.append(observation(turn, "ai", force(1, x, region=region), wars=("enemy",)))
        result = analyze_native_diagnostic_behavior_study(trace(rows))
        self.assertEqual(result["metrics"]["exact_region_ababa_signal_count"], 1)
        self.assertEqual(result["exact_region_ababa_signals"][0]["regions"], ["A", "B", "A", "B", "A"])
        self.assertEqual(result["temporal_status"], "INSUFFICIENT_TEMPORAL_EXPOSURE")

    def test_positive_signal_never_authorizes_project_planner(self) -> None:
        rows = [observation(turn, "ai", force(1, 0 if turn % 2 else 10), wars=("enemy",)) for turn in range(1, 24)]
        result = analyze_native_diagnostic_behavior_study(trace(rows))
        self.assertEqual(result["architecture_action_if_positive"], "CAUSAL_REVIEW_THEN_NARROW_NATIVE_ROW_ABLATION_ONLY")
        self.assertNotIn("PLANNER", result["architecture_action_if_positive"])


if __name__ == "__main__":
    unittest.main()

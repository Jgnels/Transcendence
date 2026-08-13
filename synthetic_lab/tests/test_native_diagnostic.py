from __future__ import annotations

import copy
import unittest

from transcendence_lab.native_diagnostic import NativeDiagnosticError, analyze_native_diagnostic_exposure


def force(cqi: int, x: int, y: int, health: float = 100.0) -> dict:
    return {"force_cqi": cqi, "x": x, "y": y, "average_unit_health_pct": health}


def snapshot(*forces: dict) -> dict:
    return {"forces": list(forces), "regions": [], "wars": []}


class NativeDiagnosticTests(unittest.TestCase):
    def _trace(self) -> dict:
        observations = []
        # 25 faction-turns, 3 stable forces each = 75 matched pairs; one force moves every turn.
        for turn in range(1, 26):
            x0 = turn - 1
            x1 = turn
            if turn % 3 == 0:
                # occasional reversal in the synthetic stream; descriptive only.
                x1 = x0 - 1
            observations.append({
                "turn": turn,
                "faction": "ai",
                "start": snapshot(force(1, x0, 0), force(2, 5, 5), force(3, 9, 9)),
                "end": snapshot(force(1, x1, 0), force(2, 5, 5), force(3, 9, 9)),
            })
        return {
            "contract": "NATIVE_CAI_PRIVILEGED_DIAGNOSTIC_TRACE_V1",
            "authority": "NO_ORDERS",
            "application_authority": "PROHIBITED",
            "research_visibility": "PRIVILEGED_OMNISCIENT_DIAGNOSTIC",
            "application_eligible": False,
            "observations": observations,
        }

    def test_exposure_qualification_is_deterministic_and_research_only(self) -> None:
        first = analyze_native_diagnostic_exposure(self._trace())
        second = analyze_native_diagnostic_exposure(copy.deepcopy(self._trace()))
        self.assertEqual(first, second)
        self.assertFalse(first["application_eligible"])
        self.assertEqual(first["authority"], "NO_ORDERS")
        self.assertEqual(first["application_authority"], "PROHIBITED")
        self.assertEqual(first["purpose"], "INSTRUMENTATION_EXPOSURE_QUALIFICATION_ONLY")
        self.assertEqual(first["metrics"]["paired_faction_turn_count"], 25)
        self.assertEqual(first["metrics"]["matched_force_turn_pairs"], 75)
        self.assertGreaterEqual(first["metrics"]["moved_force_turn_pairs"], 10)
        self.assertEqual(first["qualification_status"], "QUALIFIED_FOR_FUTURE_PREREGISTERED_DIAGNOSTIC_STUDY")

    def test_privileged_trace_can_never_be_application_eligible(self) -> None:
        trace = self._trace()
        trace["application_eligible"] = True
        with self.assertRaises(NativeDiagnosticError):
            analyze_native_diagnostic_exposure(trace)

    def test_absence_at_endpoint_is_not_promoted_to_lifecycle_claim(self) -> None:
        trace = self._trace()
        trace["observations"][0]["end"]["forces"] = trace["observations"][0]["end"]["forces"][1:]
        result = analyze_native_diagnostic_exposure(trace)
        self.assertEqual(result["metrics"]["start_force_absent_at_turn_end_count"], 1)
        self.assertIn("not labeled destroyed", result["interpretation_limits"][3])


if __name__ == "__main__":
    unittest.main()

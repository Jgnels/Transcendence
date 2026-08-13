from __future__ import annotations

import unittest

from transcendence_lab.native_sfo_causal_review import build_causal_review, replication_policy


def cluster(rate, rows, windows=None, loo_min=None, loo_max=None, max_share=None):
    eligible = sum(r[1] for r in rows)
    candidates = sum(r[2] for r in rows)
    return {
        "eligible_windows": eligible,
        "reversal_candidates": candidates,
        "reversal_candidate_rate": rate,
        "faction_rows": [
            {"faction": f, "eligible_windows": e, "reversal_candidates": c, "reversal_candidate_rate": None if e == 0 else round(c/e,6)}
            for f,e,c in rows
        ],
        "candidate_windows": windows or [],
        "leave_one_faction_out": {"rate_min": loo_min, "rate_max": loo_max},
        "candidate_concentration": {"max_faction_candidate_share": max_share},
    }


class NativeSfoCausalReviewTests(unittest.TestCase):
    def test_composition_direction_reversal_blocks_ablation(self):
        sfo = {
            "result_digest": "sfo",
            "precommitted_post_sfo_decision": {
                "decision_table_digest": "d",
                "temporal": {"branch": "HIGHER_THAN_VANILLA_CLUSTER_ENVELOPE", "action": "REPLICATE"},
            },
            "territorial_cluster_diagnostics": cluster(
                0.5,
                [("shared", 2, 0), ("sfo_only", 8, 5)],
                loo_min=0.4,
                loo_max=0.6,
                max_share=1.0,
            ),
        }
        vanilla = {
            "reference_digest": "v",
            "cluster_diagnostics": cluster(0.25, [("shared", 4, 2), ("van_only", 4, 0)]),
        }
        out = build_causal_review(sfo, vanilla)
        self.assertTrue(out["campaign_composition_review"]["direction_reversal_under_shared_faction_restriction"])
        self.assertFalse(out["adjudication"]["native_row_ablation_earned"])
        self.assertEqual(out["adjudication"]["causal_attribution_status"], "BLOCKED_BY_CAMPAIGN_COMPOSITION_INSTABILITY")
        self.assertFalse(out["application_eligible"])

    def test_candidate_geometry_counts_are_descriptive(self):
        sfo = {
            "result_digest": "sfo",
            "precommitted_post_sfo_decision": {"decision_table_digest": "d", "temporal": {}},
            "territorial_cluster_diagnostics": cluster(
                0.5,
                [("a", 2, 2)],
                windows=[
                    {"regions": ["A","B","A"]},
                    {"regions": ["A","A","A"]},
                ],
                loo_min=None,
                loo_max=None,
                max_share=1.0,
            ),
        }
        vanilla = {
            "reference_digest": "v",
            "cluster_diagnostics": cluster(
                0.0,
                [("a", 2, 0)],
                windows=[{"regions": ["A","B","C"]}],
            ),
        }
        out = build_causal_review(sfo, vanilla)
        self.assertEqual(out["candidate_geometry_review"]["sfo_candidate_shape_counts"]["ABA_REGION"], 1)
        self.assertEqual(out["candidate_geometry_review"]["sfo_candidate_shape_counts"]["SAME_REGION"], 1)
        self.assertEqual(out["candidate_geometry_review"]["vanilla_candidate_shape_counts"]["THREE_REGIONS"], 1)

    def test_replication_policy_stages_sfo_before_vanilla(self):
        out = replication_policy()
        self.assertTrue(out["stage_a_fresh_sfo_replication"]["run_first"])
        self.assertIn("Stage A", out["stage_b_fresh_vanilla_replication"]["run_only_if"])
        self.assertFalse(out["application_eligible"])
        self.assertEqual(out["authority"], "NO_ORDERS")


if __name__ == "__main__":
    unittest.main()

class NativeSfoReplicationStageATests(unittest.TestCase):
    def _result(self, eligible, repeated, rate):
        return {"result_digest":"x","temporal_stratification":{"territorial":{
            "eligible_windows":eligible,"repeated_reversal_force_count":repeated,"reversal_candidate_rate":rate
        }}}

    def test_elevated_replication_requires_fresh_vanilla(self):
        from transcendence_lab.native_sfo_causal_review import adjudicate_sfo_replication_stage_a
        out=adjudicate_sfo_replication_stage_a(self._result(40,0,0.40))
        self.assertEqual(out["branch"],"SFO_ELEVATION_REPLICATED")
        self.assertTrue(out["fresh_vanilla_replication_required"])
        self.assertFalse(out["native_row_ablation_earned"])

    def test_nonreplication_stops_row_path(self):
        from transcendence_lab.native_sfo_causal_review import adjudicate_sfo_replication_stage_a
        out=adjudicate_sfo_replication_stage_a(self._result(40,0,0.30))
        self.assertEqual(out["branch"],"SFO_ELEVATION_NOT_REPLICATED")
        self.assertFalse(out["fresh_vanilla_replication_required"])

    def test_repeated_signal_routes_to_causal_review(self):
        from transcendence_lab.native_sfo_causal_review import adjudicate_sfo_replication_stage_a
        out=adjudicate_sfo_replication_stage_a(self._result(40,1,0.10))
        self.assertEqual(out["branch"],"SFO_REPLICATION_REPEATED_TERRITORIAL_SIGNAL")
        self.assertFalse(out["fresh_vanilla_replication_required"])

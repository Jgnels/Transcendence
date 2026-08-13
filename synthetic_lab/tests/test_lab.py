from __future__ import annotations

import copy
import json
import os
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
import sys
sys.path.insert(0, str(ROOT))

from transcendence_lab.battle import run_battle
from transcendence_lab.campaign import run_campaign
from transcendence_lab.canonical import digest, read_json
from transcendence_lab.contracts import ContractError, validate_campaign_scenario, visible_scenario
from transcendence_lab.decision import assign_objectives
from transcendence_lab.ensemble import run_ensemble
from transcendence_lab.mod_audit import PackFormatError, audit_extracted_zip, audit_pack, compare_audits, parse_pfh5_index
from transcendence_lab.observed_battle import derive_reality_regressions, validate_observed_battle_corpus
from transcendence_lab.battle_trace import (
    BattleTraceCorpusError,
    derive_tactical_trace_benchmarks,
    validate_battle_trace_slices,
)
from transcendence_lab.battle_shadow import run_trace_shadow_evaluator
from transcendence_lab.tactical_state import build_tactical_state_trajectory
from transcendence_lab.tactical_adversary import run_tactical_adversarial_suite
from transcendence_lab.tactical_baselines import run_tactical_baseline_matrix
from transcendence_lab.tactical_portfolio import (
    build_tactical_priority_portfolio,
    build_trace_priority_portfolios,
)
from transcendence_lab.tactical_assignment import (
    build_tactical_objective_assignment,
    build_trace_objective_assignments,
)
from transcendence_lab.tactical_assignment_matrix import run_tactical_assignment_matrix
from transcendence_lab.tactical_schedule import (
    TacticalScheduleError,
    build_tactical_temporal_schedule,
    build_trace_tactical_temporal_schedule,
)
from transcendence_lab.tactical_schedule_matrix import run_tactical_schedule_matrix
from transcendence_lab.action_authority import (
    ActionAuthorityError,
    build_action_authority_matrix,
    build_action_authority_packet,
    build_battle4_authority_boundary_report,
)
from transcendence_lab.tactical_state import build_tactical_state
from transcendence_lab.tactical_feasibility import (
    TacticalFeasibilityError,
    build_live_feasibility_capability_profile,
    build_semantic_feasibility_capability_profile,
    build_point_query_evidence,
    build_tactical_feasibility_envelope,
    build_trace_tactical_feasibility_envelope,
)
from transcendence_lab.tactical_feasibility_matrix import run_tactical_feasibility_matrix
from transcendence_lab.tactical_guarded import (
    TacticalGuardedActionError,
    build_guarded_action_packet_set,
    build_trace_guarded_action_packets,
    validate_guarded_action_packet_set,
)
from transcendence_lab.tactical_guarded_matrix import run_tactical_guarded_matrix
from transcendence_lab.tactical_reservation import (
    build_endpoint_reservations,
    build_trace_endpoint_reservations,
)
from transcendence_lab.tactical_reservation_matrix import run_tactical_reservation_matrix
from transcendence_lab.tactical_pipeline_audit import run_tactical_pipeline_audit
from transcendence_lab.replay_visual_calibration import (
    ReplayVisualCalibrationError,
    build_dual_replay_calibration,
    validate_replay_visual_alignment,
)
from transcendence_lab.defeat_visual_preparation import (
    DefeatVisualPreparationError,
    build_chaos_defeat_capture_readiness,
    validate_chaos_defeat_visual_preparation,
)
from transcendence_lab.chaos_replay_adjudication import (
    ChaosReplayAdjudicationError,
    build_chaos_replay_divergence_calibration,
    validate_chaos_replay_stream_capture,
    validate_chaos_unit_findings,
)
from transcendence_lab.tactical_policy import (
    TacticalPolicyError,
    build_cross_corpus_policy_envelope,
    evaluate_tactical_policy,
    validate_cross_corpus_policy_envelope,
)
from transcendence_lab.tactical_policy_matrix import run_tactical_policy_matrix
from transcendence_lab.campaign_challenge import (
    CampaignChallengeError,
    build_campaign_challenge_envelope,
    evaluate_campaign_snapshot,
    semantic_snapshot_metrics,
)
from transcendence_lab.campaign_challenge_matrix import run_campaign_challenge_matrix
from transcendence_lab.strategic_portfolio import (
    StrategicPortfolioError,
    build_cross_evidence_strategic_theater_portfolio,
    build_strategic_theater_portfolio,
    semantic_portfolio_metrics,
)
from transcendence_lab.strategic_portfolio_matrix import run_strategic_portfolio_matrix
from transcendence_lab.strategic_assignment import (
    StrategicAssignmentError,
    build_cross_evidence_theater_to_army_assignment,
    build_theater_to_army_assignment,
)
from transcendence_lab.strategic_commitment import (
    build_cross_evidence_campaign_force_allocation,
    build_strategic_temporal_commitment,
)
from transcendence_lab.strategic_assignment_matrix import run_strategic_assignment_commitment_matrix
from transcendence_lab.strategic_feasibility import (
    PROHIBITED_MUTATION_SURFACES,
    StrategicFeasibilityError,
    adjudicate_campaign_strategic_feasibility_observation,
    build_campaign_strategic_feasibility_plan,
    build_cross_evidence_campaign_strategic_feasibility,
    build_observation_packet_template,
)
from transcendence_lab.strategic_feasibility_matrix import run_strategic_feasibility_matrix
from transcendence_lab.native_behavior import (
    NativeBehaviorError,
    analyze_native_behavior_trace,
)
from transcendence_lab.native_behavior_matrix import run_native_behavior_adversarial_matrix
from transcendence_lab.native_visible_behavior import (
    NativeVisibleBehaviorError,
    analyze_player_visible_native_trace,
)
from transcendence_lab.native_churn import (
    analyze_visible_directional_churn,
    compare_visible_directional_churn_cohorts,
)
from transcendence_lab.native_churn_matrix import run_native_churn_adversarial_matrix


class LabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = read_json(ROOT / "profiles" / "vanilla_8_1_1.json")
        cls.campaign = read_json(ROOT / "scenarios" / "tier2_late_game_pressure.json")
        cls.battle = read_json(ROOT / "scenarios" / "tier4_outnumbered_empire.json")
        cls.observed_battle = read_json(ROOT / "corpora" / "battle4_eilhart_observed_v1.json")
        cls.observed_battle_dense = read_json(ROOT / "corpora" / "battle4_eilhart_observed_dense_v2.json")
        cls.battle_trace_slices = read_json(ROOT / "corpora" / "battle4_eilhart_trace_slices_v1.json")
        cls.tactical_adversarial_suite = read_json(
            ROOT / "scenarios" / "tactical_contract_adversarial_suite_v0.1N.json"
        )
        cls.tactical_baseline_suite = read_json(
            ROOT / "scenarios" / "tactical_baseline_matrix_v0.1O.json"
        )
        cls.tactical_assignment_suite = read_json(
            ROOT / "scenarios" / "tactical_assignment_matrix_v0.1P.json"
        )
        cls.tactical_schedule_suite = read_json(
            ROOT / "scenarios" / "tactical_schedule_matrix_v0.1Q.json"
        )
        cls.action_authority_suite = read_json(
            ROOT / "scenarios" / "action_authority_matrix_v0.1R.json"
        )
        cls.tactical_feasibility_suite = read_json(
            ROOT / "scenarios" / "tactical_feasibility_matrix_v0.1T.json"
        )
        cls.tactical_guarded_suite = read_json(
            ROOT / "scenarios" / "tactical_guarded_action_matrix_v0.1V.json"
        )
        cls.tactical_reservation_suite = read_json(
            ROOT / "scenarios" / "tactical_endpoint_reservation_matrix_v0.1W.json"
        )
        cls.tactical_pipeline_audit_suite = read_json(
            ROOT / "scenarios" / "tactical_pipeline_adversarial_scaling_v0.1X.json"
        )
        cls.sfo_visual_alignment = read_json(
            ROOT / "corpora" / "sfo_reikland_dual_replay_visual_alignment_v0.2A.json"
        )
        cls.sfo_ubersreik_dense = read_json(
            ROOT / "corpora" / "sfo_ubersreik_observed_dense_v0.2A.json"
        )
        cls.sfo_marienburg_dense = read_json(
            ROOT / "corpora" / "sfo_marienburg_observed_dense_v0.2A.json"
        )
        cls.sfo_chaos_defeat_visual = read_json(
            ROOT / "corpora" / "sfo_chaos_defeat_visual_preparation_v0.2B.json"
        )
        cls.sfo_chaos_stream_capture = read_json(
            REPO_ROOT / "runtime_probe" / "fixtures" / "sfo_chaos_replay_stream_capture_v0.2C.json"
        )
        cls.sfo_chaos_stream_dense = read_json(
            ROOT / "corpora" / "sfo_chaos_replay_stream_observed_dense_v0.2C.json"
        )
        cls.sfo_chaos_unit_findings = read_json(
            REPO_ROOT / "runtime_probe" / "fixtures" / "sfo_chaos_replay_unit_findings_v0.2C.json"
        )
        cls.sfo_dual_replay_calibration = read_json(
            REPO_ROOT / "research" / "runtime_evidence" / "SFO_REIKLAND_DUAL_REPLAY_TACTICAL_CALIBRATION_v0.2A.json"
        )
        cls.sfo_chaos_replay_calibration = read_json(
            REPO_ROOT / "research" / "runtime_evidence" / "SFO_REIKLAND_CHAOS_REPLAY_DIVERGENCE_CALIBRATION_v0.2C.json"
        )
        cls.v02d_policy = read_json(
            REPO_ROOT / "research" / "runtime_evidence" / "REIKLAND_CROSS_CORPUS_TACTICAL_POLICY_ENVELOPE_v0.2D.json"
        )
        cls.v02d_policy_suite = read_json(
            ROOT / "scenarios" / "tactical_policy_adversarial_matrix_v0.2D.json"
        )
        cls.v02e_campaign_report = read_json(
            REPO_ROOT / "research" / "runtime_evidence" / "CAMPAIGN_TURNS_4_7_REPROCESS_v0.1J.json"
        )
        cls.v02e_campaign_suite = read_json(
            ROOT / "scenarios" / "campaign_challenge_adversarial_matrix_v0.2E.json"
        )
        cls.v02e_campaign_envelope = read_json(
            REPO_ROOT / "research" / "runtime_evidence" / "REIKLAND_CAMPAIGN_STRATEGIC_CHALLENGE_ENVELOPE_v0.2E.json"
        )
        cls.v02e_campaign_matrix = read_json(
            ROOT / "results" / "campaign_challenge_adversarial_matrix_v0.2E.json"
        )
        cls.v02f_portfolio_suite = read_json(
            ROOT / "scenarios" / "campaign_strategic_theater_portfolio_adversarial_matrix_v0.2F.json"
        )
        cls.v02f_portfolio_matrix = read_json(
            ROOT / "results" / "campaign_strategic_theater_portfolio_adversarial_matrix_v0.2F.json"
        )
        cls.v02j_native_behavior_suite = read_json(
            ROOT / "scenarios" / "native_cai_behavior_adversarial_matrix_v0.2J.json"
        )
        cls.v02j_native_behavior_matrix = read_json(
            ROOT / "results" / "native_cai_behavior_adversarial_matrix_v0.2J.json"
        )
        cls.v02l_native_churn_suite = read_json(
            ROOT / "scenarios" / "native_cai_visible_churn_adversarial_matrix_v0.2L.json"
        )
        cls.v02l_native_churn_matrix = read_json(
            ROOT / "results" / "native_cai_visible_churn_adversarial_matrix_v0.2L.json"
        )
        cls.v02f_portfolio_envelope = read_json(
            REPO_ROOT / "research" / "runtime_evidence" / "REIKLAND_CAMPAIGN_STRATEGIC_THEATER_PORTFOLIO_v0.2F.json"
        )
        cls.v02g_assignment_suite = read_json(
            ROOT / "scenarios" / "campaign_theater_assignment_commitment_adversarial_matrix_v0.2G.json"
        )
        cls.v02g_assignment_matrix = read_json(
            ROOT / "results" / "campaign_theater_assignment_commitment_adversarial_matrix_v0.2G.json"
        )
        cls.v02g_force_allocation = read_json(
            REPO_ROOT / "research" / "runtime_evidence" / "REIKLAND_CAMPAIGN_STRATEGIC_FORCE_ALLOCATION_v0.2G.json"
        )
        cls.v02h_feasibility_suite = read_json(
            ROOT / "scenarios" / "campaign_strategic_feasibility_adversarial_matrix_v0.2H.json"
        )
        cls.v02h_feasibility_matrix = read_json(
            ROOT / "results" / "campaign_strategic_feasibility_adversarial_matrix_v0.2H.json"
        )
        cls.v02h_feasibility_envelope = read_json(
            REPO_ROOT / "research" / "runtime_evidence" / "REIKLAND_CAMPAIGN_STRATEGIC_FEASIBILITY_ENVELOPE_v0.2H.json"
        )

    def test_canonical_digest_order_independent(self) -> None:
        self.assertEqual(digest({"a": 1, "b": 2}), digest({"b": 2, "a": 1}))

    def test_campaign_contract_validates(self) -> None:
        validated = validate_campaign_scenario(self.campaign)
        self.assertEqual(validated["scenario_id"], self.campaign["scenario_id"])

    def test_prohibited_private_field_rejected(self) -> None:
        bad = json.loads(json.dumps(self.campaign))
        bad["local_path"] = "synthetic-private-fixture"
        with self.assertRaises(ContractError):
            validate_campaign_scenario(bad)

    def test_hidden_army_filtered(self) -> None:
        visible = visible_scenario(self.campaign, "rival_bloc")
        ids = {army["id"] for army in visible["armies"]}
        self.assertNotIn("player_hidden", ids)
        self.assertIn("player_1", ids)


    def test_duplicate_army_id_rejected(self) -> None:
        bad = json.loads(json.dumps(self.campaign))
        bad["armies"].append(dict(bad["armies"][0]))
        with self.assertRaises(ContractError):
            validate_campaign_scenario(bad)

    def test_target_capacity_respected(self) -> None:
        result = assign_objectives(self.campaign, self.profile)
        counts = {}
        for item in result["assignments"]:
            target = item["objective"]["target_id"]
            if target is not None:
                counts[target] = counts.get(target, 0) + 1
        self.assertTrue(all(count <= self.profile["target_capacity"] for count in counts.values()))

    def test_tier1_deterministic(self) -> None:
        first = assign_objectives(self.campaign, self.profile)
        second = assign_objectives(self.campaign, self.profile)
        self.assertEqual(first, second)
        self.assertTrue(first["assignments"])
        self.assertTrue(all(item["rationale"] for item in first["assignments"]))

    def test_tier1_exactly_one_assignment_per_controlled_army(self) -> None:
        result = assign_objectives(self.campaign, self.profile)
        controlled = sum(1 for army in self.campaign["armies"] if army["faction"] == self.campaign["controlled_faction"])
        self.assertEqual(len(result["assignments"]), controlled)
        self.assertEqual(len({item["army_id"] for item in result["assignments"]}), controlled)

    def test_tier1_no_hidden_target_leakage(self) -> None:
        result = assign_objectives(self.campaign, self.profile)
        targets = {item["objective"]["target_id"] for item in result["assignments"]}
        self.assertNotIn("player_hidden", targets)

    def test_tier2_deterministic_same_seed(self) -> None:
        first = run_campaign(self.campaign, self.profile, 10, 101)
        second = run_campaign(self.campaign, self.profile, 10, 101)
        self.assertEqual(first, second)

    def test_tier2_seed_can_change_trajectory(self) -> None:
        first = run_campaign(self.campaign, self.profile, 20, 101)
        second = run_campaign(self.campaign, self.profile, 20, 999)
        self.assertNotEqual(first["result_digest"], second["result_digest"])

    def test_tier3_distribution(self) -> None:
        result = run_ensemble(self.campaign, self.profile, 8, [1, 2, 3, 4, 5])
        self.assertEqual(result["tier"], 3)
        self.assertIn("objective_churn_rate", result["distributions"])
        self.assertEqual(len(result["run_digests"]), 5)

    def test_tier4_deterministic(self) -> None:
        first = run_battle(self.battle, 101)
        second = run_battle(self.battle, 101)
        self.assertEqual(first, second)
        self.assertEqual(first["fidelity_label"], "UNCALIBRATED_TACTICAL_SURROGATE")


    def test_tier4r_observed_battle_corpus_is_valid_and_deterministic(self) -> None:
        validated = validate_observed_battle_corpus(self.observed_battle)
        first = derive_reality_regressions(validated)
        second = derive_reality_regressions(self.observed_battle)
        self.assertEqual(first, second)
        self.assertEqual(first["tier"], "4R")
        self.assertTrue(all(first["checks"].values()))
        self.assertTrue(first["stress_cases"]["endangered_commanders"])
        self.assertTrue(first["stress_cases"]["collapsed_frontline"])
        self.assertTrue(first["stress_cases"]["units_without_terminal_state"])

    def test_tier4r_contains_no_private_replay_or_log(self) -> None:
        source = self.observed_battle["source"]
        self.assertFalse(source["raw_replay_committed"])
        self.assertFalse(source["raw_log_committed"])
        serialized = json.dumps(self.observed_battle).lower()
        self.assertNotIn("c:\\users", serialized)
        self.assertNotIn(".replay", serialized)


    def test_tier4r_dense_battle_corpus_is_valid(self) -> None:
        validated = validate_observed_battle_corpus(self.observed_battle_dense)
        battle = validated["battle"]
        self.assertTrue(battle["sampling"]["time_series_metrics_valid"])
        self.assertEqual(battle["sampling"]["quality"], "DENSE_INTERVAL_COVERAGE")
        self.assertEqual(battle["sampling"]["observed_detail_samples"], 249)
        self.assertEqual(battle["identity_reconciliation"]["canonical_unit_count"], 37)
        self.assertEqual(battle["identity_reconciliation"]["identity_alias_count"], 0)
        self.assertEqual(battle["command_analysis"]["command_event_count"], 397)
        self.assertEqual(
            battle["inferred_command_attribution"]["status"],
            "INFERRED_NOT_ACKNOWLEDGED",
        )

    def test_tier4r_trace_slices_are_visibility_safe_and_deterministic(self) -> None:
        validated = validate_battle_trace_slices(self.battle_trace_slices)
        first = derive_tactical_trace_benchmarks(
            self.observed_battle_dense,
            validated,
        )
        second = derive_tactical_trace_benchmarks(
            self.observed_battle_dense,
            self.battle_trace_slices,
        )
        self.assertEqual(first, second)
        self.assertTrue(all(first["contracts"].values()))
        self.assertEqual(
            [item["slice_id"] for item in first["milestones"]],
            [
                "deployment_complete",
                "first_contact",
                "local_melee_commitment",
                "local_crisis",
                "enemy_break",
                "enemy_rout_majority",
                "victory_countdown",
                "battle_complete",
            ],
        )
        self.assertEqual(first["milestones"][0]["time_ms"], 128800)
        self.assertEqual(first["milestones"][3]["time_ms"], 402100)
        self.assertEqual(first["milestones"][5]["time_ms"], 555100)
        self.assertEqual(first["milestones"][6]["time_ms"], 730700)
        self.assertTrue(first["stress_cases"]["endangered_characters"])
        self.assertTrue(first["stress_cases"]["collapsed_frontline"])
        self.assertTrue(first["stress_cases"]["cavalry_overextension"])
        self.assertTrue(first["stress_cases"]["artillery_overrun"])

    def test_tier4r_trace_slices_contain_no_private_artifacts(self) -> None:
        serialized = json.dumps(self.battle_trace_slices).lower()
        self.assertNotIn("c:\\\\users", serialized)
        self.assertNotIn(".replay", serialized)
        self.assertFalse(self.battle_trace_slices["source"]["raw_replay_committed"])
        self.assertFalse(self.battle_trace_slices["source"]["raw_log_committed"])


    def test_tier4r_shadow_evaluator_is_deterministic_and_read_only(self) -> None:
        first = run_trace_shadow_evaluator(self.battle_trace_slices)
        second = run_trace_shadow_evaluator(self.battle_trace_slices)
        self.assertEqual(first, second)
        self.assertEqual(first["authority"], "NO_ORDERS")
        self.assertEqual(first["evidence_status"], "HYPOTHESIS")
        by_slice = {item["slice_id"]: item for item in first["evaluations"]}
        self.assertEqual(
            by_slice["deployment_complete"]["posture"],
            "DEPLOYMENT_AND_INFORMATION",
        )
        self.assertEqual(by_slice["first_contact"]["posture"], "RANGED_CONTACT")
        self.assertEqual(
            by_slice["local_crisis"]["posture"],
            "CRISIS_STABILIZATION",
        )
        self.assertEqual(
            by_slice["enemy_rout_majority"]["posture"],
            "TERMINATE_WITH_PRESERVATION",
        )
        serialized = json.dumps(first)
        self.assertNotIn('"orders"', serialized)
        self.assertTrue(
            by_slice["local_crisis"]["local_preservation_priorities"]
        )

    def test_tactical_state_trajectory_is_deterministic_and_visibility_safe(self) -> None:
        first = build_tactical_state_trajectory(self.battle_trace_slices)
        second = build_tactical_state_trajectory(self.battle_trace_slices)
        self.assertEqual(first, second)
        self.assertEqual(first["authority"], "NO_ORDERS")
        self.assertEqual(first["evidence_status"], "DERIVED_FROM_OBSERVED_INPUT")
        self.assertEqual(first["trajectory_contract"], "TACTICAL_STATE_TRAJECTORY_V2")
        self.assertEqual(first["input_validation_contract"], "BATTLE_TRACE_TACTICAL_INPUT_V2")
        for state in first["states"]:
            self.assertFalse(state["observation_scope"]["terrain_pathfinding_available"])
            for unit in state["units"]:
                if not unit["observed"]["local_alliance"]:
                    self.assertEqual(
                        unit["observed"]["visibility_source"],
                        "VISIBLE_TO_LOCAL_ALLIANCE",
                    )

    def test_tactical_state_distinguishes_crisis_recovery_and_terminal(self) -> None:
        trajectory = build_tactical_state_trajectory(self.battle_trace_slices)
        by_slice = {item["slice_id"]: item for item in trajectory["states"]}
        self.assertEqual(
            by_slice["local_crisis"]["battle_state"]["local_stability_state"],
            "LOCAL_CRISIS",
        )
        self.assertEqual(
            by_slice["enemy_rout_majority"]["battle_state"][
                "local_stability_state"
            ],
            "LOCAL_CRISIS",
        )
        self.assertEqual(
            by_slice["enemy_rout_majority"]["battle_state"][
                "tactical_phase_state"
            ],
            "RECOVERY_REQUIRED",
        )
        self.assertEqual(
            by_slice["battle_complete"]["battle_state"]["local_stability_state"],
            "TERMINAL",
        )
        self.assertNotIn(
            "IRREVERSIBLE_COLLAPSE",
            [
                item["battle_state"]["local_stability_state"]
                for item in trajectory["states"]
            ],
        )

    def test_tactical_state_role_policies_are_not_one_threshold(self) -> None:
        trajectory = build_tactical_state_trajectory(self.battle_trace_slices)
        policies = trajectory["role_policies"]
        self.assertGreater(
            policies["commander"]["preserve_hp"],
            policies["frontline"]["preserve_hp"],
        )
        self.assertGreater(
            policies["artillery"]["preserve_models"],
            policies["frontline"]["preserve_models"],
        )
        self.assertGreater(
            policies["ranged"]["asset_base"],
            policies["frontline"]["asset_base"],
        )

    def test_tactical_decision_opportunities_are_guarded_counterfactuals(self) -> None:
        result = run_trace_shadow_evaluator(
            self.battle_trace_slices, self.observed_battle_dense
        )
        opportunities = [
            opportunity
            for evaluation in result["evaluations"]
            for opportunity in evaluation["selected_decision_opportunities"]
        ]
        self.assertTrue(opportunities)
        for opportunity in opportunities:
            self.assertEqual(opportunity["counterfactual_status"], "UNVERIFIED")
            self.assertEqual(opportunity["authority"], "ADVISORY_ONLY")
            self.assertTrue(opportunity["opportunity_key"])
            self.assertTrue(opportunity["confidence"]["limitations"])
            self.assertTrue(
                all(
                    alternative["status"] == "PROPOSED_NOT_EXECUTED"
                    for alternative in opportunity["proposed_alternatives"]
                )
            )
        serialized = json.dumps(result).lower()
        self.assertNotIn('"orders"', serialized)
        self.assertIn("pathfinding", serialized)

    def test_pursuit_termination_begins_after_visible_rout_cascade(self) -> None:
        result = run_trace_shadow_evaluator(
            self.battle_trace_slices, self.observed_battle_dense
        )
        by_slice = {item["slice_id"]: item for item in result["evaluations"]}
        first_contact_types = {
            item["opportunity_type"]
            for item in by_slice["first_contact"]["selected_decision_opportunities"]
        }
        rout_types = {
            item["opportunity_type"]
            for item in by_slice["enemy_rout_majority"][
                "selected_decision_opportunities"
            ]
        }
        self.assertNotIn("PURSUIT_TERMINATION_WINDOW", first_contact_types)
        self.assertIn("PURSUIT_TERMINATION_WINDOW", rout_types)

    def test_command_budget_is_bounded_and_reference_only(self) -> None:
        result = run_trace_shadow_evaluator(
            self.battle_trace_slices, self.observed_battle_dense
        )
        budget = result["command_budget_analysis"]
        self.assertEqual(budget["observed_owner_command_event_reference"], 397)
        self.assertEqual(budget["comparison_status"], "REFERENCE_ONLY_NOT_CAUSAL")
        self.assertLess(budget["advisory_transition_to_owner_command_ratio"], 0.10)
        self.assertEqual(budget["advisory_priority_transition_count"], 28)
        self.assertGreater(budget["continued_advisory_priority_count"], 0)
        self.assertEqual(
            budget["lifecycle_identity"],
            "STABLE_OPPORTUNITY_KEY_NOT_SLICE_INSTANCE_ID",
        )
        self.assertLessEqual(budget["maximum_selected_in_one_slice"], 6)
        self.assertEqual(budget["minimum_critical_opportunity_coverage"], 1.0)

    def test_loss_prevention_diagnoses_do_not_claim_causal_improvement(self) -> None:
        result = run_trace_shadow_evaluator(
            self.battle_trace_slices, self.observed_battle_dense
        )
        diagnoses = result["loss_prevention_diagnoses"]
        self.assertTrue(diagnoses)
        self.assertTrue(
            any(
                item["preventability_assessment"]
                == "PLAUSIBLY_PREVENTABLE_SEVERITY"
                for item in diagnoses
            )
        )
        self.assertTrue(
            any(
                item["preventability_assessment"]
                == "INSUFFICIENT_EVIDENCE_OF_PREVENTABLE_SEVERITY"
                for item in diagnoses
            )
        )
        for item in diagnoses:
            self.assertEqual(item["counterfactual_status"], "UNVERIFIED")
            self.assertIn(
                "accepted and executed intervention telemetry",
                item["required_future_evidence"],
            )

    def test_v01m_artifacts_remain_frozen_historical_evidence(self) -> None:
        state = read_json(
            ROOT.parent
            / "research"
            / "runtime_evidence"
            / "BATTLE4_EILHART_TACTICAL_STATE_TRAJECTORY_v0.1M.json"
        )
        decisions = read_json(
            ROOT.parent
            / "research"
            / "runtime_evidence"
            / "BATTLE4_EILHART_TACTICAL_DECISION_OPPORTUNITIES_v0.1M.json"
        )
        self.assertEqual(state["trajectory_contract"], "TACTICAL_STATE_TRAJECTORY_V1")
        self.assertEqual(
            state["result_digest"],
            "cec345739fc6d4231b88f2cfb6814082ab0be970530da704f3b36d881f63cbb5",
        )
        self.assertEqual(
            decisions["result_digest"],
            "5af29dc6a23af6e82c8288ab321f1a06d1bb9583c8ddfea39b2c6f501d80670b",
        )

    def test_v01n_tactical_state_artifact_matches_current_implementation(self) -> None:
        expected = read_json(
            ROOT.parent
            / "research"
            / "runtime_evidence"
            / "BATTLE4_EILHART_TACTICAL_STATE_TRAJECTORY_v0.1N.json"
        )
        actual = build_tactical_state_trajectory(self.battle_trace_slices)
        self.assertEqual(actual, expected)

    def test_v01n_decision_opportunity_artifact_matches_current_implementation(self) -> None:
        expected = read_json(
            ROOT.parent
            / "research"
            / "runtime_evidence"
            / "BATTLE4_EILHART_TACTICAL_DECISION_OPPORTUNITIES_v0.1N.json"
        )
        actual = run_trace_shadow_evaluator(
            self.battle_trace_slices, self.observed_battle_dense
        )
        self.assertEqual(actual, expected)

    def test_v01n_adversarial_suite_passes_and_matches_artifact(self) -> None:
        first = run_tactical_adversarial_suite(
            self.battle_trace_slices, self.tactical_adversarial_suite
        )
        second = run_tactical_adversarial_suite(
            self.battle_trace_slices, self.tactical_adversarial_suite
        )
        expected = read_json(
            ROOT.parent
            / "research"
            / "runtime_evidence"
            / "TACTICAL_CONTRACT_ADVERSARIAL_REPORT_v0.1N.json"
        )
        self.assertEqual(first, second)
        self.assertEqual(first, expected)
        self.assertTrue(first["summary"]["all_passed"])
        self.assertEqual(first["summary"]["total_case_count"], 24)

    def test_v01o_priority_portfolio_artifact_matches_current_implementation(self) -> None:
        first = build_trace_priority_portfolios(self.battle_trace_slices)
        second = build_trace_priority_portfolios(self.battle_trace_slices)
        expected = read_json(
            ROOT.parent
            / "research"
            / "runtime_evidence"
            / "BATTLE4_EILHART_TACTICAL_PRIORITY_PORTFOLIOS_v0.1O.json"
        )
        self.assertEqual(first, second)
        self.assertEqual(first, expected)
        self.assertEqual(first["authority"], "NO_ORDERS")
        self.assertEqual(first["summary"]["minimum_critical_source_coverage"], 1.0)
        self.assertLessEqual(first["summary"]["maximum_selected_in_one_slice"], 6)
        self.assertEqual(first["summary"]["candidate_opportunity_count"], 44)
        self.assertEqual(first["summary"]["grouped_priority_count"], 25)

    def test_v01o_heterogeneous_baseline_matrix_is_deterministic(self) -> None:
        first = run_tactical_baseline_matrix(
            self.battle_trace_slices, self.tactical_baseline_suite
        )
        second = run_tactical_baseline_matrix(
            self.battle_trace_slices, self.tactical_baseline_suite
        )
        expected = read_json(
            ROOT.parent
            / "research"
            / "runtime_evidence"
            / "TACTICAL_BASELINE_MATRIX_REPORT_v0.1O.json"
        )
        self.assertEqual(first, second)
        self.assertEqual(first, expected)
        self.assertEqual(first["authority"], "NO_ORDERS")
        self.assertEqual(first["scenario_count"], 16)
        self.assertEqual(first["gate_measurements"]["state_contract_pass_count"], 16)
        self.assertEqual(
            first["gate_measurements"]["role_aware_scenario_pass_count"], 16
        )
        self.assertEqual(
            first["gate_measurements"]["role_aware_required_intent_recall"], 1.0
        )
        self.assertTrue(first["gate_measurements"]["all_outputs_no_orders"])

    def test_v01o_portfolio_fixes_critical_starvation(self) -> None:
        result = run_tactical_baseline_matrix(
            self.battle_trace_slices, self.tactical_baseline_suite
        )
        by_id = {item["scenario_id"]: item for item in result["scenario_results"]}
        saturated = by_id["critical_saturation_batching"]
        portfolio = saturated["policies"]["ROLE_AWARE_PORTFOLIO_V1"]
        legacy = saturated["policies"]["LEGACY_ROLE_AWARE_V2"]
        self.assertTrue(portfolio["contract"]["passed"])
        self.assertFalse(legacy["contract"]["passed"])
        self.assertEqual(portfolio["diagnostics"]["critical_source_coverage"], 1.0)
        self.assertEqual(legacy["diagnostics"]["critical_source_coverage"], 0.666667)
        self.assertEqual(portfolio["diagnostics"]["grouped_priority_count"], 6)

        overflow = by_id["critical_group_overflow_disclosed"]
        portfolio = overflow["policies"]["ROLE_AWARE_PORTFOLIO_V1"]
        legacy = overflow["policies"]["LEGACY_ROLE_AWARE_V2"]
        self.assertTrue(portfolio["contract"]["passed"])
        self.assertTrue(portfolio["diagnostics"]["critical_overflow_used"])
        self.assertEqual(portfolio["diagnostics"]["critical_source_coverage"], 1.0)
        self.assertEqual(legacy["diagnostics"]["critical_source_coverage"], 0.6)
        self.assertIn(
            "REVIEW_CRITICAL_OVERFLOW", portfolio["contract"]["selected_intents"]
        )

    def test_v01o_scale_equivalence_and_baseline_disagreement_are_explicit(self) -> None:
        result = run_tactical_baseline_matrix(
            self.battle_trace_slices, self.tactical_baseline_suite
        )
        self.assertEqual(result["gate_measurements"]["equivalence_check_count"], 1)
        self.assertEqual(
            result["gate_measurements"]["equivalence_check_pass_count"], 1
        )
        summaries = {item["policy_id"]: item for item in result["policy_summary"]}
        self.assertEqual(
            summaries["ROLE_AWARE_PORTFOLIO_V1"]["scenario_contract_pass_count"],
            16,
        )
        self.assertEqual(
            summaries["LEGACY_ROLE_AWARE_V2"]["scenario_contract_pass_count"],
            14,
        )
        self.assertLess(
            summaries["UNIFORM_DANGER_045"]["required_intent_recall"], 0.40
        )
        self.assertIn(
            "not evidence of battle outcomes",
            summaries["ROLE_AWARE_PORTFOLIO_V1"]["interpretation"],
        )

    def test_v01p_objective_assignment_artifact_matches_current_implementation(self) -> None:
        first = build_trace_objective_assignments(self.battle_trace_slices)
        second = build_trace_objective_assignments(self.battle_trace_slices)
        expected = read_json(
            ROOT.parent
            / "research"
            / "runtime_evidence"
            / "BATTLE4_EILHART_TACTICAL_OBJECTIVE_ASSIGNMENTS_v0.1P.json"
        )
        self.assertEqual(first, second)
        self.assertEqual(first, expected)
        self.assertEqual(first["authority"], "NO_ORDERS")
        self.assertEqual(first["summary"]["double_booked_actor_count"], 0)
        self.assertEqual(first["summary"]["objective_count"], 50)
        self.assertEqual(first["summary"]["assignment_count"], 34)
        self.assertEqual(first["summary"]["unassignable_objective_count"], 12)
        self.assertEqual(first["summary"]["resource_conflict_unfilled_count"], 4)

    def test_v01p_assignment_matrix_is_deterministic_and_matches_artifact(self) -> None:
        first = run_tactical_assignment_matrix(
            self.battle_trace_slices,
            self.tactical_baseline_suite,
            self.tactical_assignment_suite,
        )
        second = run_tactical_assignment_matrix(
            self.battle_trace_slices,
            self.tactical_baseline_suite,
            self.tactical_assignment_suite,
        )
        expected = read_json(
            ROOT.parent
            / "research"
            / "runtime_evidence"
            / "TACTICAL_ASSIGNMENT_MATRIX_REPORT_v0.1P.json"
        )
        self.assertEqual(first, second)
        self.assertEqual(first, expected)
        self.assertEqual(first["scenario_count"], 12)
        self.assertEqual(first["metamorphic_check_count"], 3)
        self.assertTrue(first["gate_measurements"]["all_scenarios_passed"])
        self.assertTrue(
            first["gate_measurements"]["all_metamorphic_checks_passed"]
        )
        self.assertEqual(first["gate_measurements"]["double_booked_actor_count"], 0)
        self.assertTrue(first["gate_measurements"]["all_outputs_no_orders"])

    def test_v01p_conflicts_and_uncontrollable_subjects_remain_explicit(self) -> None:
        result = run_tactical_assignment_matrix(
            self.battle_trace_slices,
            self.tactical_baseline_suite,
            self.tactical_assignment_suite,
        )
        by_id = {item["scenario_id"]: item for item in result["scenario_results"]}
        overflow = by_id["critical_overflow_resolves_single_actor_conflict"][
            "assignment"
        ]
        objectives = {item["objective_id"]: item for item in overflow["objectives"]}
        self.assertEqual(
            objectives["CONTAIN_LOCAL_ROUT:BATTLE"]["assigned_actor_unit_id"],
            "1:u1008",
        )
        self.assertEqual(
            objectives["RELIEVE:1:u1003"]["unfilled_reason"],
            "RESOURCE_CONFLICT_WITH_HIGHER_VALUE_OBJECTIVE",
        )
        self.assertEqual(
            objectives["SELF:1:u1001"]["unfilled_reason"],
            "SUBJECT_NOT_CONTROLLABLE",
        )
        self.assertEqual(overflow["double_booked_actor_count"], 0)

    def test_v01p_assignment_is_order_and_translation_invariant(self) -> None:
        result = run_tactical_assignment_matrix(
            self.battle_trace_slices,
            self.tactical_baseline_suite,
            self.tactical_assignment_suite,
        )
        checks = {item["check_id"]: item for item in result["metamorphic_results"]}
        self.assertTrue(checks["unit_order_independence"]["passed"])
        self.assertTrue(checks["portfolio_order_independence"]["passed"])
        self.assertTrue(checks["coordinate_translation_invariance"]["passed"])
        for check in checks.values():
            self.assertEqual(
                check["baseline_semantic_digest"],
                check["transformed_semantic_digest"],
            )

    def test_v01p_rejects_forged_or_stale_portfolio(self) -> None:
        local_crisis = next(
            item
            for item in self.battle_trace_slices["slices"]
            if item["slice_id"] == "local_crisis"
        )
        state = build_tactical_state(local_crisis)
        portfolio = build_tactical_priority_portfolio(state)

        forged = copy.deepcopy(portfolio)
        priority = forged["selected_priorities"][0]
        priority["source_opportunity_ids"][0] = "forged:source:opportunity"
        priority.pop("result_digest", None)
        priority["result_digest"] = digest(priority)
        forged.pop("result_digest", None)
        forged["result_digest"] = digest(forged)
        with self.assertRaisesRegex(
            ValueError, "source opportunity set differs from canonical portfolio"
        ):
            build_tactical_objective_assignment(state, forged)

        stale = copy.deepcopy(portfolio)
        stale["source_tactical_state_digest"] = "0" * 64
        stale.pop("result_digest", None)
        stale["result_digest"] = digest(stale)
        with self.assertRaisesRegex(
            ValueError, "source tactical-state digest mismatch"
        ):
            build_tactical_objective_assignment(state, stale)


    def test_v01q_temporal_schedule_artifact_matches_current_implementation(self) -> None:
        first = build_trace_tactical_temporal_schedule(self.battle_trace_slices)
        second = build_trace_tactical_temporal_schedule(self.battle_trace_slices)
        expected = read_json(
            ROOT.parent
            / "research"
            / "runtime_evidence"
            / "BATTLE4_EILHART_TACTICAL_TEMPORAL_SCHEDULE_v0.1Q.json"
        )
        self.assertEqual(first, second)
        self.assertEqual(first, expected)
        self.assertEqual(first["authority"], "NO_ORDERS")
        self.assertEqual(first["summary"]["raw_assignment_count"], 34)
        self.assertEqual(first["summary"]["plan_start_count"], 34)
        self.assertEqual(first["summary"]["plan_continue_count"], 0)
        self.assertEqual(first["summary"]["continuity_reset_count"], 18)
        self.assertEqual(first["summary"]["double_booked_active_actor_count"], 0)

    def test_v01q_schedule_matrix_is_deterministic_and_matches_artifact(self) -> None:
        first = run_tactical_schedule_matrix(
            self.battle_trace_slices,
            self.tactical_baseline_suite,
            self.tactical_schedule_suite,
        )
        second = run_tactical_schedule_matrix(
            self.battle_trace_slices,
            self.tactical_baseline_suite,
            self.tactical_schedule_suite,
        )
        expected = read_json(
            ROOT.parent
            / "research"
            / "runtime_evidence"
            / "TACTICAL_TEMPORAL_SCHEDULE_MATRIX_REPORT_v0.1Q.json"
        )
        self.assertEqual(first, second)
        self.assertEqual(first, expected)
        self.assertEqual(first["scenario_count"], 12)
        self.assertEqual(first["scenario_pass_count"], 12)
        self.assertEqual(first["metamorphic_check_count"], 3)
        self.assertEqual(first["metamorphic_pass_count"], 3)
        self.assertTrue(first["gate_measurements"]["all_outputs_no_orders"])
        self.assertEqual(
            first["gate_measurements"]["double_booked_active_actor_count"], 0
        )

    def test_v01q_temporal_lifecycle_prevents_thrashing_and_preserves_overrides(self) -> None:
        result = run_tactical_schedule_matrix(
            self.battle_trace_slices,
            self.tactical_baseline_suite,
            self.tactical_schedule_suite,
        )
        by_id = {item["scenario_id"]: item for item in result["scenario_results"]}

        retained = by_id["minimum_commitment_retains_prior_actor"]["schedule"]
        retained_step = retained["schedule_slices"][1]
        self.assertEqual(
            retained_step["active_plans"][0]["actor_unit_id"], "1:u1014"
        )
        self.assertEqual(
            retained_step["blocked_assignments"][0]["reason"],
            "MINIMUM_COMMITMENT_RETAINS_PRIOR_ACTOR",
        )

        cooldown = by_id["same_action_cooldown_blocks_thrashing"]["schedule"]
        self.assertEqual(
            cooldown["schedule_slices"][2]["blocked_assignments"][0]["reason"],
            "SAME_ACTION_COOLDOWN",
        )
        critical = by_id["critical_action_overrides_cooldown"]["schedule"]
        event_types = {
            event["event_type"] for event in critical["schedule_slices"][2]["events"]
        }
        self.assertIn("PLAN_COOLDOWN_OVERRIDDEN_CRITICAL", event_types)

    def test_v01q_schedule_rejects_forged_assignment_and_nonincreasing_time(self) -> None:
        local_crisis = next(
            item
            for item in self.battle_trace_slices["slices"]
            if item["slice_id"] == "local_crisis"
        )
        state = build_tactical_state(local_crisis)
        assignment = build_tactical_objective_assignment(state)
        forged = copy.deepcopy(assignment)
        forged["authority"] = "CONTROL"
        forged.pop("result_digest", None)
        forged["result_digest"] = digest(forged)
        with self.assertRaisesRegex(
            TacticalScheduleError, "must retain NO_ORDERS authority"
        ):
            build_tactical_temporal_schedule(
                [state], [forged], source_id="forged", evidence_status="CONTROL_SYNTHETIC"
            )

        with self.assertRaisesRegex(
            TacticalScheduleError, "strictly increasing"
        ):
            build_tactical_temporal_schedule(
                [state, state],
                [assignment, assignment],
                source_id="duplicate-time",
                evidence_status="CONTROL_SYNTHETIC",
            )

    def test_v01q_transition_envelope_makes_no_execution_or_numeric_prediction(self) -> None:
        result = build_trace_tactical_temporal_schedule(self.battle_trace_slices)
        plans = [
            plan
            for schedule_slice in result["schedule_slices"]
            for plan in schedule_slice["active_plans"]
        ]
        self.assertTrue(plans)
        for plan in plans:
            envelope = plan["transition_envelope"]
            self.assertIsNone(envelope["predicted_position"])
            self.assertIsNone(envelope["predicted_casualties"])
            self.assertIsNone(envelope["predicted_success_probability"])
            self.assertFalse(envelope["terrain_pathfinding_available"])
            self.assertFalse(envelope["formation_feasibility_available"])
            self.assertEqual(plan["status"], "ABSTRACT_SCHEDULED_NOT_ISSUED")
            self.assertEqual(plan["authority"], "NO_ORDERS")
        for schedule_slice in result["schedule_slices"]:
            for event in schedule_slice["events"]:
                self.assertEqual(event["causal_attribution"], "NOT_ESTABLISHED")

    def test_strict_trace_validator_rejects_boolean_string(self) -> None:
        bad = json.loads(json.dumps(self.battle_trace_slices))
        bad["slices"][0]["units"][0]["local_alliance"] = "false"
        with self.assertRaisesRegex(BattleTraceCorpusError, "local_alliance must be boolean"):
            validate_battle_trace_slices(bad)

    def test_terminal_slice_emits_no_actionable_decision_window(self) -> None:
        result = run_trace_shadow_evaluator(
            self.battle_trace_slices, self.observed_battle_dense
        )
        complete = next(
            item for item in result["evaluations"] if item["slice_id"] == "battle_complete"
        )
        self.assertEqual(complete["local_stability_state"], "TERMINAL")
        self.assertEqual(complete["selected_decision_opportunities"], [])
        self.assertEqual(complete["command_budget"]["candidate_opportunity_count"], 0)

    def _write_test_pack(self, path: Path) -> None:
        entries = [
            ("db\\cai_variables_tables\\fixture", b"abc"),
            ("notes.rpfm_reserved", b"{}"),
        ]
        timestamp = 123
        index_parts = []
        for name, blob in entries:
            index_parts.append(struct.pack("<I", len(blob)) + b"\x00" + name.encode("utf-8") + b"\x00")
        index = b"".join(index_parts)
        header = b"PFH5" + struct.pack("<6I", 3, 0, 0, len(entries), len(index), timestamp)
        path.write_bytes(header + index + b"".join(blob for _, blob in entries))

    def test_pfh5_pack_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            pack = Path(temp) / "fixture.pack"
            self._write_test_pack(pack)
            parsed = parse_pfh5_index(pack)
            self.assertEqual(parsed["file_count"], 2)
            audit = audit_pack(pack, "fixture")
            self.assertEqual(audit["table_families"], ["cai_variables_tables"])
            self.assertEqual(audit["tables"][0]["classification"], "DIRECT_NATIVE_CAI")


    def test_pfh5_rejects_compressed_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            pack = Path(temp) / "compressed.pack"
            name = "db\\cai_variables_tables\\fixture"
            blob = b"abc"
            index = struct.pack("<I", len(blob)) + b"\x01" + name.encode("utf-8") + b"\x00"
            header = b"PFH5" + struct.pack("<6I", 3, 0, 0, 1, len(index), 123)
            pack.write_bytes(header + index + blob)
            with self.assertRaises(PackFormatError):
                parse_pfh5_index(pack)

    def test_pfh5_rejects_wrong_magic(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            pack = Path(temp) / "bad.pack"
            pack.write_bytes(b"not a pack")
            with self.assertRaises(PackFormatError):
                parse_pfh5_index(pack)

    def test_extracted_zip_script_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "audit.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("root/db/cai_variables_tables/data", b"binary")
                archive.writestr("root/script/campaign/mod/test.lua", "core:add_listener('x','FactionTurnStart',true,function() cm:treasury_mod('a', 1) end,true)")
            audit = audit_extracted_zip(path, "zip_fixture")
            self.assertEqual(audit["table_family_count"], 1)
            self.assertEqual(audit["script_count"], 1)
            self.assertEqual(audit["scripts"][0]["classification"], "SCRIPTED_STATE_INTERVENTION")

    def test_compare_audits_flags_shared_tables(self) -> None:
        a = {"source_id": "a", "table_families": ["cai_variables_tables", "x"]}
        b = {"source_id": "b", "table_families": ["cai_variables_tables", "y"]}
        result = compare_audits([a, b])
        self.assertEqual(result["pairwise"][0]["overlap_count"], 1)
        self.assertEqual(result["potential_conflicts"][0]["table_family"], "cai_variables_tables")


    def test_v01r_action_authority_matrix_is_deterministic(self) -> None:
        first = build_action_authority_matrix(self.action_authority_suite)
        second = build_action_authority_matrix(self.action_authority_suite)
        self.assertEqual(first, second)
        self.assertEqual(first["scenario_count"], 12)
        self.assertEqual(first["passed_count"], 12)
        self.assertEqual(first["failed_count"], 0)
        self.assertEqual(first["authority"], "NO_ORDERS")

    def test_v01r_command_observation_never_becomes_acknowledgement(self) -> None:
        scenario = next(
            item for item in self.action_authority_suite["scenarios"]
            if item["scenario_id"] == "owner_move_state_match"
        )
        packet = build_action_authority_packet(scenario["observation"])
        self.assertEqual(packet["project_issue_status"], "NOT_ATTEMPTED")
        self.assertEqual(packet["direct_acknowledgement_status"], "UNAVAILABLE_NOT_OBSERVED")
        self.assertEqual(packet["acknowledgement_claim"], "NOT_ACKNOWLEDGED")
        self.assertEqual(
            packet["execution_status"],
            "OBSERVED_STATE_MATCH_NOT_CAUSALLY_ATTRIBUTED",
        )
        self.assertEqual(packet["outcome_attribution"], "UNVERIFIED_NOT_ATTRIBUTED")

    def test_v01r_forbids_project_issue_and_hidden_target(self) -> None:
        for scenario_id in (
            "forbid_project_issue_attempt",
            "forbid_fabricated_direct_ack",
            "forbid_hidden_target_identity",
        ):
            scenario = next(
                item for item in self.action_authority_suite["scenarios"]
                if item["scenario_id"] == scenario_id
            )
            with self.assertRaises(ActionAuthorityError):
                build_action_authority_packet(scenario["observation"])

    def test_v01r_battle4_boundary_preserves_limiting_result(self) -> None:
        schedule = read_json(
            ROOT.parent / "research" / "runtime_evidence" /
            "BATTLE4_EILHART_TACTICAL_TEMPORAL_SCHEDULE_v0.1Q.json"
        )
        report = build_battle4_authority_boundary_report(
            self.observed_battle_dense,
            schedule,
        )
        self.assertEqual(report["command_event_count"], 397)
        self.assertEqual(report["direct_selection_attributed_command_count"], 0)
        self.assertEqual(report["candidate_inferred_attribution_count"], 302)
        self.assertEqual(report["inferred_attribution_status"], "INFERRED_NOT_ACKNOWLEDGED")
        self.assertEqual(report["project_issue_attempt_count"], 0)
        self.assertEqual(report["direct_acknowledgement_count"], 0)
        self.assertEqual(report["reachability_query_count"], 0)

    def test_v01r_action_authority_artifacts_match_current_implementation(self) -> None:
        boundary_path = REPO_ROOT / "research/runtime_evidence/BATTLE4_EILHART_ACTION_AUTHORITY_BOUNDARY_v0.1R.json"
        matrix_path = REPO_ROOT / "research/runtime_evidence/ACTION_AUTHORITY_MATRIX_REPORT_v0.1R.json"
        template_path = REPO_ROOT / "research/runtime_evidence/ACTION_AUTHORITY_LIVE_CAPTURE_PACKET_TEMPLATE_v0.1R.json"
        fixture_path = REPO_ROOT / "research/runtime_evidence/ACTION_AUTHORITY_CAPTURE_VERIFICATION_FIXTURE_v0.1R.json"
        boundary = json.loads(boundary_path.read_text(encoding="utf-8"))
        matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
        template = json.loads(template_path.read_text(encoding="utf-8"))
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        self.assertEqual(
            boundary,
            build_battle4_authority_boundary_report(
                self.observed_battle_dense,
                json.loads((REPO_ROOT / "research/runtime_evidence/BATTLE4_EILHART_TACTICAL_TEMPORAL_SCHEDULE_v0.1Q.json").read_text(encoding="utf-8")),
            ),
        )
        self.assertEqual(matrix, build_action_authority_matrix(self.action_authority_suite))
        payload = dict(template)
        claimed = payload.pop("result_digest")
        self.assertEqual(claimed, digest(payload))
        self.assertEqual(template["authority"], "NO_ORDERS")
        self.assertEqual(template["fixed_v0_1r_values"]["direct_acknowledgement"], "UNAVAILABLE_NOT_OBSERVED")
        self.assertEqual(fixture["status"], "CONTROL_FIXTURE_READ_ONLY_ACTION_AUTHORITY")
        self.assertTrue(all(fixture["checks"].values()))


    def test_v01t_feasibility_matrix_is_deterministic_and_matches_artifact(self) -> None:
        first = run_tactical_feasibility_matrix(
            self.battle_trace_slices,
            self.tactical_baseline_suite,
            self.tactical_feasibility_suite,
        )
        second = run_tactical_feasibility_matrix(
            self.battle_trace_slices,
            self.tactical_baseline_suite,
            self.tactical_feasibility_suite,
        )
        frozen = read_json(
            REPO_ROOT / "research/runtime_evidence/TACTICAL_FEASIBILITY_MATRIX_REPORT_v0.1T.json"
        )
        self.assertEqual(first, second)
        self.assertEqual(first, frozen)
        self.assertEqual(first["scenario_pass_count"], 15)
        self.assertEqual(first["metamorphic_pass_count"], 3)
        self.assertEqual(first["authority"], "NO_ORDERS")

    def test_v01t_battle4_feasibility_envelope_is_query_ready_not_observed(self) -> None:
        live = read_json(
            REPO_ROOT / "research/runtime_evidence/ACTION_AUTHORITY_LIVE_CAPTURE_ADJUDICATION_v0.1S.json"
        )
        profile = build_live_feasibility_capability_profile(live)
        result = build_trace_tactical_feasibility_envelope(
            self.battle_trace_slices, capability_profile=profile
        )
        frozen = read_json(
            REPO_ROOT / "research/runtime_evidence/BATTLE4_EILHART_TACTICAL_FEASIBILITY_ENVELOPE_v0.1T.json"
        )
        self.assertEqual(result, frozen)
        self.assertEqual(result["summary"]["active_plan_envelope_count"], 34)
        self.assertEqual(result["summary"]["candidate_point_count"], 102)
        self.assertEqual(result["summary"]["point_query_supported_plan_count"], 0)
        self.assertEqual(result["summary"]["query_ready_unobserved_plan_count"], 34)

    def test_v01t_query_true_never_promotes_route_ack_execution_or_outcome(self) -> None:
        state_trajectory = build_tactical_state_trajectory(self.battle_trace_slices)
        schedule_trajectory = build_trace_tactical_temporal_schedule(self.battle_trace_slices)
        state = state_trajectory["states"][2]
        schedule = schedule_trajectory["schedule_slices"][2]
        initial = build_tactical_feasibility_envelope(state, schedule)
        candidate_ids = [
            candidate["candidate_id"]
            for plan in initial["plan_envelopes"]
            for candidate in plan["candidate_points"]
        ]
        evidence = build_point_query_evidence(
            state,
            schedule,
            [{"candidate_id": item, "query_result": "QUERY_TRUE"} for item in candidate_ids],
            evidence_source="CONTROL_SYNTHETIC_FIXTURE",
        )
        result = build_tactical_feasibility_envelope(
            state, schedule, point_query_evidence=evidence
        )
        self.assertTrue(result["plan_envelopes"])
        for plan in result["plan_envelopes"]:
            self.assertEqual(plan["feasibility_class"], "POINT_QUERY_SUPPORTED_ONLY")
            self.assertEqual(plan["project_issue_status"], "NOT_ATTEMPTED")
            self.assertEqual(
                plan["direct_acknowledgement_status"],
                "UNAVAILABLE_NOT_OBSERVED",
            )
            for candidate in plan["candidate_points"]:
                self.assertEqual(candidate["route_completion_status"], "UNVERIFIED")
                self.assertEqual(candidate["formation_feasibility_status"], "UNVERIFIED")
                self.assertEqual(candidate["execution_status"], "NOT_ISSUED")
                self.assertEqual(candidate["outcome_status"], "UNVERIFIED_NOT_ATTRIBUTED")

    def test_v01t_forged_stale_and_authority_altered_query_evidence_fail_closed(self) -> None:
        state_trajectory = build_tactical_state_trajectory(self.battle_trace_slices)
        schedule_trajectory = build_trace_tactical_temporal_schedule(self.battle_trace_slices)
        state = state_trajectory["states"][2]
        schedule = schedule_trajectory["schedule_slices"][2]
        initial = build_tactical_feasibility_envelope(state, schedule)
        candidate_id = initial["plan_envelopes"][0]["candidate_points"][0]["candidate_id"]
        evidence = build_point_query_evidence(
            state, schedule,
            [{"candidate_id": candidate_id, "query_result": "QUERY_TRUE"}],
            evidence_source="CONTROL_SYNTHETIC_FIXTURE",
        )
        variants = []
        forged = copy.deepcopy(evidence)
        forged["candidate_results"][0]["candidate_id"] = "f" * 64
        forged.pop("result_digest")
        forged["result_digest"] = digest(forged)
        variants.append(forged)
        stale = copy.deepcopy(evidence)
        stale["source_tactical_state_digest"] = "0" * 64
        stale.pop("result_digest")
        stale["result_digest"] = digest(stale)
        variants.append(stale)
        authority = copy.deepcopy(evidence)
        authority["authority"] = "CONTROL"
        authority.pop("result_digest")
        authority["result_digest"] = digest(authority)
        variants.append(authority)
        for variant in variants:
            with self.assertRaises(TacticalFeasibilityError):
                build_tactical_feasibility_envelope(
                    state, schedule, point_query_evidence=variant
                )

    def test_v01t_live_capability_profile_is_aggregate_only(self) -> None:
        live = read_json(
            REPO_ROOT / "research/runtime_evidence/ACTION_AUTHORITY_LIVE_CAPTURE_ADJUDICATION_v0.1S.json"
        )
        profile = build_live_feasibility_capability_profile(live)
        frozen = read_json(
            REPO_ROOT / "research/runtime_evidence/ACTION_AUTHORITY_LIVE_FEASIBILITY_CAPABILITY_PROFILE_v0.1T.json"
        )
        self.assertEqual(profile, frozen)
        self.assertEqual(profile["point_reachability"]["classification"], "OBSERVED")
        self.assertEqual(profile["point_reachability"]["availability_rate"], 1.0)
        self.assertTrue(
            any("does not identify feasibility" in item for item in profile["applicability_limits"])
        )

    def test_v01u_semantic_capability_profile_matches_live_calibration(self) -> None:
        calibration = read_json(
            REPO_ROOT / "research/runtime_evidence/ACTION_FEASIBILITY_SEMANTIC_CALIBRATION_v0.1U.json"
        )
        profile = build_semantic_feasibility_capability_profile(calibration)
        frozen = read_json(
            REPO_ROOT / "research/runtime_evidence/ACTION_FEASIBILITY_SEMANTIC_CAPABILITY_PROFILE_v0.1U.json"
        )
        self.assertEqual(profile, frozen)
        self.assertEqual(profile["point_reachability"]["query_true"], 191)
        self.assertEqual(profile["point_reachability"]["query_false"], 0)
        self.assertEqual(
            profile["point_reachability"]["valid_false_result_status"],
            "UNVERIFIED_NONE_OBSERVED",
        )

    def test_v01u_semantic_profile_does_not_promote_battle4_candidates(self) -> None:
        calibration = read_json(
            REPO_ROOT / "research/runtime_evidence/ACTION_FEASIBILITY_SEMANTIC_CALIBRATION_v0.1U.json"
        )
        profile = build_semantic_feasibility_capability_profile(calibration)
        result = build_trace_tactical_feasibility_envelope(
            self.battle_trace_slices, capability_profile=profile
        )
        frozen = read_json(
            REPO_ROOT / "research/runtime_evidence/BATTLE4_EILHART_TACTICAL_FEASIBILITY_ENVELOPE_v0.1U.json"
        )
        self.assertEqual(result, frozen)
        self.assertEqual(result["summary"]["active_plan_envelope_count"], 34)
        self.assertEqual(result["summary"]["candidate_point_count"], 102)
        self.assertEqual(result["summary"]["point_query_supported_plan_count"], 0)
        self.assertEqual(result["summary"]["point_query_rejected_plan_count"], 0)
        self.assertEqual(result["summary"]["query_ready_unobserved_plan_count"], 34)

    def test_v01u_semantic_profile_rejects_sentinel_false_as_point_evidence(self) -> None:
        calibration = read_json(
            REPO_ROOT / "research/runtime_evidence/ACTION_FEASIBILITY_SEMANTIC_CALIBRATION_v0.1U.json"
        )
        forged = copy.deepcopy(calibration)
        forged["qualified_explicit_point_reachability_counts"]["QUERY_TRUE"] -= 1
        forged["qualified_explicit_point_reachability_counts"]["QUERY_FALSE"] += 1
        forged["explicit_point_observation"]["query_true"] -= 1
        forged["explicit_point_observation"]["query_false"] += 1
        forged.pop("result_digest")
        forged["result_digest"] = digest(forged)
        with self.assertRaises(TacticalFeasibilityError):
            build_semantic_feasibility_capability_profile(forged)

    def test_v01v_guarded_action_artifact_matches_current_implementation(self) -> None:
        profile = read_json(
            REPO_ROOT / "research/runtime_evidence/ACTION_FEASIBILITY_SEMANTIC_CAPABILITY_PROFILE_v0.1U.json"
        )
        result = build_trace_guarded_action_packets(
            self.battle_trace_slices, capability_profile=profile
        )
        frozen = read_json(
            REPO_ROOT / "research/runtime_evidence/BATTLE4_EILHART_GUARDED_ACTION_PACKETS_v0.1V.json"
        )
        self.assertEqual(result, frozen)
        self.assertEqual(result["summary"]["packet_count"], 34)
        self.assertEqual(result["summary"]["ready_packet_count"], 0)
        self.assertEqual(result["summary"]["deferred_packet_count"], 34)
        self.assertEqual(result["authority"], "NO_ORDERS")
        self.assertEqual(result["application_authority"], "PROHIBITED")

    def test_v01v_guarded_action_matrix_is_deterministic(self) -> None:
        first = run_tactical_guarded_matrix(
            self.battle_trace_slices,
            self.tactical_baseline_suite,
            self.tactical_feasibility_suite,
            self.tactical_guarded_suite,
        )
        second = run_tactical_guarded_matrix(
            self.battle_trace_slices,
            self.tactical_baseline_suite,
            self.tactical_feasibility_suite,
            self.tactical_guarded_suite,
        )
        frozen = read_json(
            REPO_ROOT / "research/runtime_evidence/TACTICAL_GUARDED_ACTION_MATRIX_REPORT_v0.1V.json"
        )
        self.assertEqual(first, second)
        self.assertEqual(first, frozen)
        self.assertEqual(first["scenario_pass_count"], 15)
        self.assertEqual(first["metamorphic_pass_count"], 3)

    def test_v01v_duplicate_feasibility_plan_identity_fails_closed(self) -> None:
        from transcendence_lab.tactical_feasibility_matrix import _build_state_schedule
        scenario = next(
            item
            for item in self.tactical_feasibility_suite["scenarios"]
            if item["scenario_id"] == "commander_candidate_points_are_query_ready"
        )
        state, schedule = _build_state_schedule(
            self.battle_trace_slices, self.tactical_baseline_suite, scenario
        )
        envelope = build_tactical_feasibility_envelope(state, schedule)
        self.assertGreater(len(envelope["plan_envelopes"]), 0)
        forged = copy.deepcopy(envelope)
        forged["plan_envelopes"].append(copy.deepcopy(forged["plan_envelopes"][0]))
        forged["plan_envelope_count"] = len(forged["plan_envelopes"])
        forged["candidate_point_count"] = sum(
            item["candidate_count"] for item in forged["plan_envelopes"]
        )
        forged.pop("result_digest")
        forged["result_digest"] = digest(forged)
        with self.assertRaises(TacticalGuardedActionError):
            build_guarded_action_packet_set(state, schedule, forged)

    def test_v01v_packet_identity_and_actor_exclusivity_fail_closed(self) -> None:
        from transcendence_lab.tactical_reservation_matrix import _packet_set

        packet_set = _packet_set([
            {
                "packet_key": "alpha",
                "severity": "HIGH",
                "utility": 0.8,
                "points": [[0.0, 0.0, 10.0]],
                "readiness": "READY",
            },
            {
                "packet_key": "beta",
                "severity": "MEDIUM",
                "utility": 0.7,
                "points": [[20.0, 0.0, 10.0]],
                "readiness": "READY",
            },
        ])

        forged_identity = copy.deepcopy(packet_set)
        forged_identity["packets"][0]["packet_id"] = "f" * 64
        forged_identity["packets"][0].pop("result_digest")
        forged_identity["packets"][0]["result_digest"] = digest(forged_identity["packets"][0])
        forged_identity.pop("result_digest")
        forged_identity["result_digest"] = digest(forged_identity)
        with self.assertRaises(TacticalGuardedActionError):
            validate_guarded_action_packet_set(forged_identity)

        duplicate_actor = copy.deepcopy(packet_set)
        duplicate_actor["packets"][1]["actor_unit_id"] = duplicate_actor["packets"][0]["actor_unit_id"]
        duplicate_actor["packets"][1].pop("result_digest")
        duplicate_actor["packets"][1]["result_digest"] = digest(duplicate_actor["packets"][1])
        duplicate_actor.pop("result_digest")
        duplicate_actor["result_digest"] = digest(duplicate_actor)
        with self.assertRaises(TacticalGuardedActionError):
            validate_guarded_action_packet_set(duplicate_actor)

    def test_v01w_endpoint_reservation_artifact_abstains_on_battle4(self) -> None:
        profile = read_json(
            REPO_ROOT / "research/runtime_evidence/ACTION_FEASIBILITY_SEMANTIC_CAPABILITY_PROFILE_v0.1U.json"
        )
        result = build_trace_endpoint_reservations(
            self.battle_trace_slices, capability_profile=profile
        )
        frozen = read_json(
            REPO_ROOT / "research/runtime_evidence/BATTLE4_EILHART_ENDPOINT_RESERVATIONS_v0.1W.json"
        )
        self.assertEqual(result, frozen)
        self.assertEqual(result["summary"]["ready_packet_count"], 0)
        self.assertEqual(result["summary"]["reservation_count"], 0)
        self.assertEqual(result["summary"]["nonready_packet_count"], 34)

    def test_v01w_endpoint_reservation_matrix_is_deterministic(self) -> None:
        first = run_tactical_reservation_matrix(self.tactical_reservation_suite)
        second = run_tactical_reservation_matrix(self.tactical_reservation_suite)
        frozen = read_json(
            REPO_ROOT / "research/runtime_evidence/TACTICAL_ENDPOINT_RESERVATION_MATRIX_REPORT_v0.1W.json"
        )
        self.assertEqual(first, second)
        self.assertEqual(first, frozen)
        self.assertEqual(first["scenario_pass_count"], 14)
        self.assertEqual(first["metamorphic_pass_count"], 3)
        fallback = next(
            item for item in first["scenarios"]
            if item["scenario_id"] == "packet_limit_fallback_is_explicit"
        )
        self.assertEqual(
            fallback["solver_mode"],
            "DETERMINISTIC_GREEDY_PACKET_LIMIT_FALLBACK",
        )

    def test_v01w_reservations_never_claim_route_or_execution(self) -> None:
        from transcendence_lab.tactical_reservation_matrix import _packet_set
        packet_set = _packet_set([
            {
                "packet_key": "alpha",
                "severity": "HIGH",
                "utility": 0.8,
                "points": [[0.0, 0.0, 0.0]],
                "readiness": "READY",
                "objective_type": "RELIEVE_FRONTLINE",
            },
            {
                "packet_key": "beta",
                "severity": "MEDIUM",
                "utility": 0.7,
                "points": [[20.0, 0.0, 0.0]],
                "readiness": "READY",
                "objective_type": "COMMIT_RESERVE",
            },
        ])
        result = build_endpoint_reservations(packet_set)
        self.assertEqual(result["reservation_count"], 2)
        self.assertGreaterEqual(
            result["minimum_selected_endpoint_separation_m"],
            result["minimum_endpoint_separation_m"],
        )
        for reservation in result["reservations"]:
            self.assertEqual(reservation["route_status"], "UNVERIFIED")
            self.assertEqual(reservation["execution_status"], "NOT_ISSUED")
            self.assertEqual(reservation["authority"], "NO_ORDERS")

    def test_v01x_pipeline_audit_matches_frozen_report(self) -> None:
        result = run_tactical_pipeline_audit(
            self.battle_trace_slices,
            self.tactical_baseline_suite,
            self.tactical_feasibility_suite,
            self.tactical_pipeline_audit_suite,
        )
        frozen = read_json(
            REPO_ROOT / "research/runtime_evidence/TACTICAL_PIPELINE_ADVERSARIAL_SCALING_REPORT_v0.1X.json"
        )
        self.assertEqual(result, frozen)
        self.assertTrue(result["all_cases_passed"])
        self.assertEqual(result["case_pass_count"], 256)
        self.assertEqual(result["scale_pass_count"], 12)
        self.assertTrue(
            result["defect_regressions"]["duplicate_plan_identity_collapse"]["regression_passed"]
        )
        self.assertTrue(
            result["defect_regressions"]["coordinate_hash_tie_break"]["regression_passed"]
        )

    def test_v01x_pipeline_audit_is_reproducible_and_scales_to_160_packets(self) -> None:
        first = run_tactical_pipeline_audit(
            self.battle_trace_slices,
            self.tactical_baseline_suite,
            self.tactical_feasibility_suite,
            self.tactical_pipeline_audit_suite,
        )
        second = run_tactical_pipeline_audit(
            self.battle_trace_slices,
            self.tactical_baseline_suite,
            self.tactical_feasibility_suite,
            self.tactical_pipeline_audit_suite,
        )
        self.assertEqual(first["result_digest"], second["result_digest"])
        self.assertEqual(first["summary"]["maximum_scale_packet_count"], 160)
        self.assertEqual(first["authority"], "NO_ORDERS")
        self.assertEqual(first["application_authority"], "PROHIBITED")


    def test_v01z_sfo_three_battle_calibration_digest_is_frozen(self) -> None:
        corpus = read_json(
            ROOT / "corpora" / "sfo_reikland_three_battle_calibration_v0.1Z.json"
        )
        payload = copy.deepcopy(corpus)
        claimed = payload.pop("result_digest")
        self.assertEqual(
            claimed,
            "3ee62a00a87121f8cfd763153f46a0855b83ff4475737db7794510b700542d3e",
        )
        self.assertEqual(claimed, digest(payload))
        self.assertEqual(
            corpus["source_fixture_digest"],
            "beffac065a5e8021c8c4ad1bee5c5d207724651f7c47f0a62bc7166859098a10",
        )

    def test_v01z_sfo_three_battle_calibration_aggregates_exact_observations(self) -> None:
        corpus = read_json(
            ROOT / "corpora" / "sfo_reikland_three_battle_calibration_v0.1Z.json"
        )
        episodes = corpus["episodes"]
        self.assertEqual([item["battle_index"] for item in episodes], [1, 2, 3])
        self.assertTrue(all(item["battle_type"] == "land_normal" for item in episodes))
        self.assertTrue(all(item["from_campaign"] == "true" for item in episodes))
        self.assertTrue(all(item["time_series_metrics_valid"] for item in episodes))
        self.assertEqual(sum(item["command_events"] for item in episodes), 683)
        self.assertEqual(sum(item["selection_events"] for item in episodes), 1025)
        self.assertEqual(sum(item["detail_samples"] for item in episodes), 698)
        self.assertEqual(sum(item["canonical_unit_count"] for item in episodes), 80)
        self.assertEqual(
            sum(item["alliance_aggregate_records"] for item in episodes),
            4000,
        )

    def test_v01z_sfo_three_battle_calibration_preserves_authority_boundary(self) -> None:
        corpus = read_json(
            ROOT / "corpora" / "sfo_reikland_three_battle_calibration_v0.1Z.json"
        )
        joined = json.dumps(corpus, sort_keys=True).lower()
        self.assertEqual(corpus["evidence_status"], "OBSERVED")
        self.assertIn("not acknowledgements", joined)
        self.assertIn("not an optimal-policy label", joined)
        self.assertIn("do not establish siege", joined)
        self.assertNotIn('"order_acknowledgement": "observed"', joined)
        self.assertNotIn('"tactical_superiority": "observed"', joined)
        self.assertNotIn('"execution_causality": "observed"', joined)

    def _resign_visual_alignment(self, value: dict) -> dict:
        value.pop("result_digest", None)
        value["result_digest"] = digest(value)
        return value

    def test_v02a_visual_alignment_contract_is_frozen_and_private_safe(self) -> None:
        validated = validate_replay_visual_alignment(self.sfo_visual_alignment)
        self.assertEqual(
            validated["result_digest"],
            "ff763fa5ade5de8bae7f465a54017e07bd7263c09765a0da9c1dde0d3ac32783",
        )
        serialized = json.dumps(validated, sort_keys=True).lower()
        self.assertNotIn("c:\\users", serialized)
        self.assertNotIn('"video_bytes"', serialized)
        self.assertNotIn('"replay_bytes"', serialized)
        self.assertTrue(all(not video["committed"] for battle in validated["battles"] for video in battle["video_artifacts"]))

    def test_v02a_dual_replay_calibration_is_deterministic_and_matches_artifact(self) -> None:
        dense = {
            "ubersreik": self.sfo_ubersreik_dense,
            "marienburg": self.sfo_marienburg_dense,
        }
        first = build_dual_replay_calibration(self.sfo_visual_alignment, dense)
        second = build_dual_replay_calibration(copy.deepcopy(self.sfo_visual_alignment), copy.deepcopy(dense))
        frozen = read_json(REPO_ROOT / "research" / "runtime_evidence" / "SFO_REIKLAND_DUAL_REPLAY_TACTICAL_CALIBRATION_v0.2A.json")
        self.assertEqual(first, second)
        self.assertEqual(first, frozen)
        self.assertEqual(first["result_digest"], "364431a064ef1f15bc6ab7da4417b688d882ac7f2035be753728d9d75870565e")

    def test_v02a_dual_replay_calibration_extracts_exact_contrast(self) -> None:
        result = build_dual_replay_calibration(
            self.sfo_visual_alignment,
            {"ubersreik": self.sfo_ubersreik_dense, "marienburg": self.sfo_marienburg_dense},
        )
        battles = {item["battle_id"]: item for item in result["battles"]}
        self.assertEqual(battles["ubersreik"]["outcome"]["visual_grade"], "DECISIVE_VICTORY")
        self.assertEqual(battles["marienburg"]["outcome"]["visual_grade"], "PYRRHIC_VICTORY")
        self.assertEqual(battles["ubersreik"]["telemetry"]["initial_local_units_observed"], 3)
        self.assertEqual(battles["ubersreik"]["telemetry"]["local_units"], 16)
        self.assertEqual(battles["marienburg"]["telemetry"]["initial_local_units_observed"], 1)
        self.assertEqual(battles["marienburg"]["telemetry"]["local_units"], 20)
        self.assertEqual(battles["ubersreik"]["telemetry"]["role_summary"]["cavalry"]["casualties_observed_lower_bound"], 4)
        self.assertEqual(battles["marienburg"]["telemetry"]["role_summary"]["frontline"]["casualties_observed_lower_bound"], 536)
        self.assertGreater(result["cross_battle_contrast"]["local_casualty_lower_bound_ratio_marienburg_to_ubersreik"], 2.3)

    def test_v02a_identity_provenance_does_not_rewrite_runtime_identity(self) -> None:
        result = build_dual_replay_calibration(
            self.sfo_visual_alignment,
            {"ubersreik": self.sfo_ubersreik_dense, "marienburg": self.sfo_marienburg_dense},
        )
        self.assertEqual({item["visual_title"] for item in result["battles"]}, {"Battle of Ubersreik", "Battle of Marienburg"})
        self.assertEqual({item["runtime_identity"] for item in result["battles"]}, {"Battle of Eilhart — Reikland vs Empire Secessionists"})
        self.assertTrue(all(item["identity_resolution"] == "VISUAL_TITLE_FOR_DISPLAY_RUNTIME_IDENTITY_RETAINED" for item in result["battles"]))

    def test_v02a_visual_alignment_rejects_private_path(self) -> None:
        bad = copy.deepcopy(self.sfo_visual_alignment)
        bad["battles"][0]["video_artifacts"][0]["video_path"] = "C:\\Users\\owner\\video.mp4"
        self._resign_visual_alignment(bad)
        with self.assertRaises(ReplayVisualCalibrationError):
            validate_replay_visual_alignment(bad)

    def test_v02a_visual_alignment_rejects_acknowledgement_promotion(self) -> None:
        bad = copy.deepcopy(self.sfo_visual_alignment)
        bad["battles"][0]["visual_facts"][0]["claim_status"] = "ACKNOWLEDGED"
        self._resign_visual_alignment(bad)
        with self.assertRaises(ReplayVisualCalibrationError):
            validate_replay_visual_alignment(bad)

    def test_v02a_visual_alignment_rejects_overlapping_telemetry_phases(self) -> None:
        bad = copy.deepcopy(self.sfo_visual_alignment)
        bad["battles"][0]["phase_windows"][1]["telemetry_start_ms"] = 200000
        self._resign_visual_alignment(bad)
        with self.assertRaises(ReplayVisualCalibrationError):
            validate_replay_visual_alignment(bad)

    def test_v02a_calibration_rejects_foreign_replay_corpus(self) -> None:
        bad_dense = copy.deepcopy(self.sfo_ubersreik_dense)
        bad_dense["source"]["replay_sha256"] = "0" * 64
        with self.assertRaises(ReplayVisualCalibrationError):
            build_dual_replay_calibration(
                self.sfo_visual_alignment,
                {"ubersreik": bad_dense, "marienburg": self.sfo_marienburg_dense},
            )

    def test_v02a_calibration_preserves_no_order_and_no_optimality_boundary(self) -> None:
        result = build_dual_replay_calibration(
            self.sfo_visual_alignment,
            {"ubersreik": self.sfo_ubersreik_dense, "marienburg": self.sfo_marienburg_dense},
        )
        joined = json.dumps(result, sort_keys=True).lower()
        self.assertEqual(result["authority"], "NO_ORDERS")
        self.assertIn("not acknowledgements", joined)
        self.assertIn("not optimal-policy labels", joined)
        self.assertIn("not proof", joined)
        self.assertNotIn('"order_acknowledgement": "observed"', joined)
        self.assertNotIn('"tactical_superiority": "observed"', joined)

    def _resign_chaos_defeat_visual(self, value: dict) -> dict:
        value.pop("result_digest", None)
        value["result_digest"] = digest(value)
        return value

    def test_v02b_chaos_defeat_visual_preparation_is_frozen_and_private_safe(self) -> None:
        validated = validate_chaos_defeat_visual_preparation(self.sfo_chaos_defeat_visual)
        self.assertEqual(
            validated["result_digest"],
            "33147a76c6499694b9ae1623dd8698deb5c83a8eb77b9435a8451a64a12d54ab",
        )
        self.assertEqual(
            validated["replay"]["sha256"],
            "28d780d02f2af07fe16fe4a24a27cd37f41bdb870d485f11949d5ed63f838cb5",
        )
        self.assertEqual(validated["replay"]["size_bytes"], 86067)
        self.assertFalse(validated["replay"]["committed"])
        self.assertFalse(validated["visual_artifact"]["committed"])
        serialized = json.dumps(validated, sort_keys=True).lower()
        self.assertNotIn("c:\\users", serialized)
        self.assertNotIn('"video_bytes"', serialized)
        self.assertNotIn('"replay_bytes"', serialized)

    def test_v02b_chaos_defeat_readiness_is_deterministic_and_matches_artifact(self) -> None:
        first = build_chaos_defeat_capture_readiness(self.sfo_chaos_defeat_visual)
        second = build_chaos_defeat_capture_readiness(copy.deepcopy(self.sfo_chaos_defeat_visual))
        frozen = read_json(
            REPO_ROOT / "research" / "runtime_evidence" / "SFO_REIKLAND_CHAOS_DEFEAT_CAPTURE_READINESS_v0.2B.json"
        )
        self.assertEqual(first, second)
        self.assertEqual(first, frozen)
        self.assertEqual(
            first["result_digest"],
            "8ffd0b9d0b7f4b2599db7ea6b870af279dfd07eb1405dede4ad53a8b9fc28d8f",
        )
        self.assertEqual(first["status"], "READY_FOR_EXACT_READ_ONLY_DENSE_CAPTURE")
        self.assertEqual(first["authority"], "NO_ORDERS")

    def test_v02b_chaos_defeat_outcome_remains_owner_attested(self) -> None:
        result = build_chaos_defeat_capture_readiness(self.sfo_chaos_defeat_visual)
        self.assertEqual(result["visual_outcome"]["evidence_label"], "OWNER_ATTESTED")
        self.assertFalse(result["visual_outcome"]["result_screen_observed"])
        self.assertEqual(result["visual_outcome"]["grade"], "UNVERIFIED")
        joined = json.dumps(result, sort_keys=True).lower()
        self.assertIn("claims_withheld_until_capture", joined)
        self.assertNotIn('"tactical_superiority": "observed"', joined)

    def test_v02b_chaos_defeat_rejects_private_path_and_acknowledgement_promotion(self) -> None:
        bad_path = copy.deepcopy(self.sfo_chaos_defeat_visual)
        bad_path["visual_artifact"]["video_path"] = "C:\\Users\\owner\\chaos.mkv"
        self._resign_chaos_defeat_visual(bad_path)
        with self.assertRaises(DefeatVisualPreparationError):
            validate_chaos_defeat_visual_preparation(bad_path)

        bad_claim = copy.deepcopy(self.sfo_chaos_defeat_visual)
        bad_claim["bounded_hypotheses"][0]["claim_status"] = "ACKNOWLEDGED"
        self._resign_chaos_defeat_visual(bad_claim)
        with self.assertRaises(DefeatVisualPreparationError):
            validate_chaos_defeat_visual_preparation(bad_claim)

    def test_v02b_chaos_defeat_rejects_phase_overlap_and_replay_tamper(self) -> None:
        overlap = copy.deepcopy(self.sfo_chaos_defeat_visual)
        overlap["visual_phase_windows"][1]["recording_start_ms"] = 47000
        self._resign_chaos_defeat_visual(overlap)
        with self.assertRaises(DefeatVisualPreparationError):
            validate_chaos_defeat_visual_preparation(overlap)

        tampered = copy.deepcopy(self.sfo_chaos_defeat_visual)
        tampered["replay"]["sha256"] = "0" * 64
        self._resign_chaos_defeat_visual(tampered)
        with self.assertRaises(DefeatVisualPreparationError):
            validate_chaos_defeat_visual_preparation(tampered)

    def _resign_chaos_replay_capture(self, value: dict) -> dict:
        value.pop("result_digest", None)
        value["result_digest"] = digest(value)
        return value

    def _resign_chaos_unit_findings(self, value: dict) -> dict:
        value.pop("result_digest", None)
        value["result_digest"] = digest(value)
        return value

    def test_v02c_chaos_replay_capture_is_frozen_nonterminal_and_private_safe(self) -> None:
        validated = validate_chaos_replay_stream_capture(self.sfo_chaos_stream_capture)
        self.assertEqual(validated["evidence_label"], "LIMITING_RESULT")
        self.assertFalse(validated["capture"]["battle_complete_marker_observed"])
        self.assertEqual(validated["capture"]["completed_battle_count"], 0)
        self.assertEqual(validated["outcome_provenance"]["replayed_simulation"]["status"], "UNVERIFIED_NONTERMINAL")
        serialized = json.dumps(validated, sort_keys=True).lower()
        self.assertNotIn("c:\\users", serialized)
        self.assertNotIn('"raw_log"', serialized)
        self.assertNotIn('"replay_bytes"', serialized)

    def test_v02c_chaos_unit_findings_are_exact_and_nonterminal(self) -> None:
        validated = validate_chaos_unit_findings(
            self.sfo_chaos_unit_findings, self.sfo_chaos_stream_capture
        )
        self.assertEqual(validated["battle"]["unit_count"], 23)
        self.assertEqual(validated["battle"]["first_engagement_time_ms"], 49400)
        self.assertTrue(all(not unit["terminal_state_observed"] for unit in validated["battle"]["units"]))

    def test_v02c_chaos_replay_calibration_is_deterministic_and_matches_artifact(self) -> None:
        first = build_chaos_replay_divergence_calibration(
            self.sfo_chaos_stream_capture, self.sfo_chaos_stream_dense, self.sfo_chaos_unit_findings
        )
        second = build_chaos_replay_divergence_calibration(
            copy.deepcopy(self.sfo_chaos_stream_capture),
            copy.deepcopy(self.sfo_chaos_stream_dense),
            copy.deepcopy(self.sfo_chaos_unit_findings),
        )
        frozen = read_json(
            REPO_ROOT / "research" / "runtime_evidence" / "SFO_REIKLAND_CHAOS_REPLAY_DIVERGENCE_CALIBRATION_v0.2C.json"
        )
        self.assertEqual(first, second)
        self.assertEqual(first, frozen)
        self.assertEqual(first["result_digest"], "a69f2ed4e09034dc79ac5462aefa7f9c949c09a33a3e4e843e4a8cdecddcaab4")
        self.assertEqual(first["status"], "CLOSED_LIMITING_RESULT_REPLAY_DIVERGENCE")
        self.assertEqual(first["authority"], "NO_ORDERS")

    def test_v02c_chaos_replay_refines_reserve_and_rejects_terminal_learning(self) -> None:
        result = build_chaos_replay_divergence_calibration(
            self.sfo_chaos_stream_capture, self.sfo_chaos_stream_dense, self.sfo_chaos_unit_findings
        )
        hypotheses = {item["hypothesis_id"]: item for item in result["hypothesis_adjudication"]}
        self.assertEqual(hypotheses["no_protected_reserve"]["status"], "REFINED")
        self.assertEqual(hypotheses["terminal_defeat_reproduced_by_replay"]["status"], "INVALIDATED")
        self.assertEqual(result["last_observed_snapshot"]["interpretation"], "NONTERMINAL_SNAPSHOT_NOT_OUTCOME")
        self.assertEqual(result["lifecycle_adjudication"]["victorious_alliance"], "UNVERIFIED")

    def test_v02c_chaos_replay_rejects_tamper_private_paths_and_ack_promotion(self) -> None:
        bad_capture = copy.deepcopy(self.sfo_chaos_stream_capture)
        bad_capture["source"]["raw_log_path"] = "synthetic-private-fixture"
        self._resign_chaos_replay_capture(bad_capture)
        with self.assertRaises(ChaosReplayAdjudicationError):
            validate_chaos_replay_stream_capture(bad_capture)

        bad_unit = copy.deepcopy(self.sfo_chaos_unit_findings)
        bad_unit["battle"]["units"][0]["terminal_state_observed"] = True
        self._resign_chaos_unit_findings(bad_unit)
        with self.assertRaises(ChaosReplayAdjudicationError):
            validate_chaos_unit_findings(bad_unit, self.sfo_chaos_stream_capture)

        bad_claim = copy.deepcopy(self.sfo_chaos_stream_capture)
        bad_claim["authority"] = "ACKNOWLEDGED"
        self._resign_chaos_replay_capture(bad_claim)
        with self.assertRaises(ChaosReplayAdjudicationError):
            validate_chaos_replay_stream_capture(bad_claim)



    def _build_v02d_policy(self) -> dict:
        return build_cross_corpus_policy_envelope(
            {
                "eilhart": self.observed_battle_dense,
                "ubersreik": self.sfo_ubersreik_dense,
                "marienburg": self.sfo_marienburg_dense,
                "chaos": self.sfo_chaos_stream_dense,
            },
            self.sfo_dual_replay_calibration,
            self.sfo_chaos_replay_calibration,
        )

    def test_v02d_cross_corpus_policy_is_deterministic_and_matches_artifact(self) -> None:
        first = self._build_v02d_policy()
        second = self._build_v02d_policy()
        self.assertEqual(first, second)
        self.assertEqual(first, self.v02d_policy)
        validate_cross_corpus_policy_envelope(first)

    def test_v02d_policy_preserves_exact_four_corpus_provenance(self) -> None:
        policy = self.v02d_policy
        self.assertEqual(
            policy["source_provenance"]["dense_result_digests"],
            {
                "chaos": "4d84f49ec1782d29e872eff6674e93af089c3290a765b5d20c95b815ee70cea4",
                "eilhart": "442e187638c4d2b3457910efdbb50d13f16fd27a8391e7ac9bd2d6aaed47c33d",
                "marienburg": "058f10ad125b554d3d63a0c1f768ed58ef8a9818473c2aebf515ac1458f957c0",
                "ubersreik": "a93340421c1c7a0623f21381d6d83de209299276e93c418ed193adb65ca8a5ec",
            },
        )
        by_id = {item["battle_id"]: item for item in policy["battle_summaries"]}
        self.assertEqual(by_id["ubersreik"]["identity"]["display_identity"], "Battle of Ubersreik")
        self.assertEqual(by_id["marienburg"]["identity"]["display_identity"], "Battle of Marienburg")
        self.assertEqual(by_id["chaos"]["identity"]["display_identity"], "An Ogre's Folly")
        self.assertTrue(policy["identity_provenance_boundary"]["silent_identity_reconciliation_prohibited"])
        self.assertEqual(
            policy["identity_provenance_boundary"]["known_runtime_identity_alias_cohort"],
            ["ubersreik", "marienburg", "chaos"],
        )

    def test_v02d_policy_rules_separate_multi_corpus_support_from_hypothesis(self) -> None:
        rules = {item["rule_id"]: item for item in self.v02d_policy["policy_rules"]}
        self.assertEqual(rules["victory_grade_cost_separation"]["status"], "SUPPORTED_MULTI_CORPUS")
        self.assertEqual(rules["severe_asset_loss_ratio_guard"]["status"], "SUPPORTED_MULTI_CORPUS")
        self.assertEqual(rules["target_concentration_review"]["status"], "HYPOTHESIS_SINGLE_CORPUS")
        self.assertEqual(rules["target_concentration_review"]["supporting_battles"], ["chaos"])

    def test_v02d_nonterminal_observation_cannot_promote_outcome(self) -> None:
        chaos = next(item for item in self.v02d_policy["battle_summaries"] if item["battle_id"] == "chaos")
        self.assertFalse(chaos["natural_completion_observed"])
        self.assertEqual(chaos["outcome_grade"], "UNVERIFIED_NONTERMINAL")
        scenario = next(item for item in self.v02d_policy_suite["scenarios"] if item["scenario_id"] == "nonterminal_replay_exhaustion_abstains_outcome")
        result = evaluate_tactical_policy(self.v02d_policy, scenario["snapshot"])
        self.assertEqual(result["terminal_outcome_label"], "UNVERIFIED_NONTERMINAL")
        self.assertIn("NO_TERMINAL_OUTCOME_LEARNING_FROM_NONTERMINAL_STATE", result["abstentions"])

    def test_v02d_rejects_foreign_dense_corpus_and_authority_promotion(self) -> None:
        foreign = copy.deepcopy(self.sfo_chaos_stream_dense)
        foreign["result_digest"] = "0" * 64
        with self.assertRaises(TacticalPolicyError):
            build_cross_corpus_policy_envelope(
                {
                    "eilhart": self.observed_battle_dense,
                    "ubersreik": self.sfo_ubersreik_dense,
                    "marienburg": self.sfo_marienburg_dense,
                    "chaos": foreign,
                },
                self.sfo_dual_replay_calibration,
                self.sfo_chaos_replay_calibration,
            )
        snapshot = copy.deepcopy(self.v02d_policy_suite["scenarios"][0]["snapshot"])
        snapshot["authority"] = "CONTROL"
        with self.assertRaises(TacticalPolicyError):
            evaluate_tactical_policy(self.v02d_policy, snapshot)

    def test_v02d_policy_matrix_passes_all_contracts_and_matches_artifact(self) -> None:
        first = run_tactical_policy_matrix(self.v02d_policy, self.v02d_policy_suite)
        second = run_tactical_policy_matrix(self.v02d_policy, self.v02d_policy_suite)
        frozen = read_json(ROOT / "results" / "tactical_policy_adversarial_matrix_v0.2D.json")
        self.assertEqual(first, second)
        self.assertEqual(first, frozen)
        self.assertEqual(first["passed_case_count"], first["scenario_count"])
        self.assertEqual(first["metamorphic_pass_count"], first["metamorphic_check_count"])

    def test_v02d_severe_asset_threshold_is_ratio_based(self) -> None:
        base = next(item for item in self.v02d_policy_suite["scenarios"] if item["scenario_id"] == "elite_cavalry_half_loss_triggers_preservation")["snapshot"]
        scaled = copy.deepcopy(base)
        scaled["snapshot_id"] = "scaled-ratio"
        scaled["local_assets"][0]["initial_models"] *= 100
        scaled["local_assets"][0]["casualties_observed_lower_bound"] *= 100
        a = evaluate_tactical_policy(self.v02d_policy, base)
        b = evaluate_tactical_policy(self.v02d_policy, scaled)
        self.assertEqual([item["review_id"] for item in a["reviews"]], [item["review_id"] for item in b["reviews"]])
        below = copy.deepcopy(base)
        below["snapshot_id"] = "below-ratio"
        below["local_assets"][0]["initial_models"] = 1000
        below["local_assets"][0]["casualties_observed_lower_bound"] = 499
        c = evaluate_tactical_policy(self.v02d_policy, below)
        self.assertNotIn("HIGH_VALUE_ASSET_PRESERVATION_REVIEW", [item["review_id"] for item in c["reviews"]])

    def test_v02d_simultaneous_terminal_and_local_crisis_keeps_preservation_first(self) -> None:
        scenario = next(item for item in self.v02d_policy_suite["scenarios"] if item["scenario_id"] == "simultaneous_terminal_and_local_crisis_preserves_first")
        output = evaluate_tactical_policy(self.v02d_policy, scenario["snapshot"])
        self.assertEqual(output["priority_ordering"], "PRESERVATION_FIRST_EVEN_WITH_TERMINAL_EVIDENCE")
        self.assertEqual(output["reviews"][0]["review_id"], "HIGH_VALUE_ASSET_PRESERVATION_REVIEW")
        self.assertIn("NO_NEW_HIGH_COMMITMENT_AFTER_TERMINAL_EVIDENCE", output["abstentions"])

    def test_v02d_policy_evaluator_scales_to_500_assets_deterministically(self) -> None:
        snapshot = copy.deepcopy(self.v02d_policy_suite["scenarios"][0]["snapshot"])
        snapshot["snapshot_id"] = "scale-500"
        snapshot["local_assets"] = [
            {
                "asset_id": f"asset-{index:03d}",
                "initial_models": 100,
                "casualties_observed_lower_bound": 60 if index % 17 == 0 else 10,
                "high_value": index % 17 == 0,
                "commander": index % 101 == 0,
                "routing": index % 101 == 0,
                "hitpoints_fraction": 0.2 if index % 101 == 0 else 0.9,
            }
            for index in range(500)
        ]
        first = evaluate_tactical_policy(self.v02d_policy, snapshot)
        second = evaluate_tactical_policy(self.v02d_policy, snapshot)
        self.assertEqual(first, second)
        self.assertLessEqual(first["review_count"], 500 * 2)
        self.assertFalse(first["project_orders_emitted"])

    def test_v02d_policy_artifacts_are_private_safe_and_noncausal(self) -> None:
        serialized = json.dumps(
            {
                "policy": self.v02d_policy,
                "suite": self.v02d_policy_suite,
                "report": read_json(ROOT / "results" / "tactical_policy_adversarial_matrix_v0.2D.json"),
            },
            sort_keys=True,
        ).lower()
        self.assertNotIn("c:\\\\users", serialized)
        self.assertNotIn("/mnt/", serialized)
        self.assertNotIn('"raw_log"', serialized)
        self.assertNotIn('"replay_bytes"', serialized)
        self.assertEqual(self.v02d_policy["authority"], "NO_ORDERS")
        self.assertEqual(self.v02d_policy["application_authority"], "PROHIBITED")

    def test_v02e_campaign_challenge_artifacts_match_current_implementation(self) -> None:
        envelope = build_campaign_challenge_envelope(self.v02e_campaign_report, self.campaign)
        matrix = run_campaign_challenge_matrix(self.v02e_campaign_suite)
        self.assertEqual(envelope, self.v02e_campaign_envelope)
        self.assertEqual(matrix, self.v02e_campaign_matrix)
        self.assertEqual(envelope["result_digest"], "4cbc5cb253b5cc16966807e889e4c05354a284100cd8f237b90b493281bc9423")
        self.assertEqual(matrix["result_digest"], "4acfa02699cd9f78eace303889d2b7bba274b82b65582b2ea21f3cd70690e3df")

    def test_v02e_campaign_challenge_observed_envelope_is_deterministic(self) -> None:
        first = build_campaign_challenge_envelope(self.v02e_campaign_report, self.campaign)
        second = build_campaign_challenge_envelope(self.v02e_campaign_report, self.campaign)
        self.assertEqual(first, second)
        self.assertEqual(first["authority"], "NO_ORDERS")
        self.assertEqual(first["application_authority"], "PROHIBITED")
        self.assertEqual([item["turn"] for item in first["observed_turns"]], [4, 5, 6, 7])
        self.assertEqual(first["observed_turns"][3]["rival_structure"], "COHERENT_VISIBLE_RIVAL_CANDIDATE")
        self.assertEqual(first["synthetic_late_game_reference"]["scenario_id"], "tier2_late_game_pressure_v1")

    def test_v02e_campaign_challenge_hidden_enemy_and_player_label_are_semantically_invariant(self) -> None:
        base = copy.deepcopy(self.v02e_campaign_suite["metamorphic_base"])
        hidden = copy.deepcopy(base)
        hidden["scenario_id"] += ":hidden-test"
        hidden["armies"].append({
            "id": "hidden-test",
            "faction": "player_empire",
            "strength": 999999.0,
            "x": 0.0,
            "y": 0.0,
            "movement": 99.0,
            "replenishment": 1.0,
            "visible_to": [],
        })
        renamed = copy.deepcopy(base)
        renamed["scenario_id"] += ":renamed-test"
        for army in renamed["armies"]:
            if army["faction"] == "player_empire":
                army["faction"] = "npc_empire"
            army["visible_to"] = ["npc_empire" if value == "player_empire" else value for value in army["visible_to"]]
        for region in renamed["regions"]:
            if region["owner"] == "player_empire":
                region["owner"] = "npc_empire"
        renamed["wars"] = [["npc_empire" if value == "player_empire" else value for value in war] for war in renamed["wars"]]
        baseline = semantic_snapshot_metrics(evaluate_campaign_snapshot(base))
        self.assertEqual(semantic_snapshot_metrics(evaluate_campaign_snapshot(hidden)), baseline)
        self.assertEqual(semantic_snapshot_metrics(evaluate_campaign_snapshot(renamed)), baseline)

    def test_v02e_campaign_challenge_matrix_passes_all_cases(self) -> None:
        result = run_campaign_challenge_matrix(self.v02e_campaign_suite)
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["passed_case_count"], result["case_count"])
        self.assertEqual(result["metamorphic_pass_count"], result["metamorphic_check_count"])
        self.assertGreaterEqual(result["case_count"], 8)
        self.assertGreaterEqual(result["metamorphic_check_count"], 5)

    def test_v02e_campaign_challenge_does_not_reward_war_count_as_coherence(self) -> None:
        case = next(item for item in self.v02e_campaign_suite["cases"] if item["case_id"] == "three_way_fragmentation_is_not_rewarded_as_coherence")
        result = evaluate_campaign_snapshot(case["scenario"])
        self.assertEqual(result["rival_structure"], "FRAGMENTED_VISIBLE_PRESSURE")
        self.assertEqual(result["metrics"]["at_war_faction_count"], 3)
        self.assertNotIn("anti_player_bias_score", result["metrics"])
        self.assertEqual(result["unavailable_dimensions"]["anti_player_bias"], "REQUIRES_TARGETING_HISTORY_AND_NONPLAYER_COUNTERFACTUALS")

    def test_v02e_campaign_challenge_colocation_is_not_coordination_claim(self) -> None:
        case = next(item for item in self.v02e_campaign_suite["cases"] if item["case_id"] == "coherent_visible_rival_is_separate_from_front_coverage")
        result = evaluate_campaign_snapshot(case["scenario"])
        front = result["fronts"][0]
        self.assertTrue(front["colocated_same_faction_pressure"])
        self.assertEqual(front["coordination_claim"], "NOT_INFERRED_FROM_COLOCATION")

    def test_v02e_campaign_challenge_rejects_authority_promotion(self) -> None:
        bad = copy.deepcopy(self.v02e_campaign_report)
        bad["authority"]["game_orders_emitted"] = True
        with self.assertRaises(CampaignChallengeError):
            build_campaign_challenge_envelope(bad, self.campaign)

    def test_v02e_campaign_challenge_recovery_threshold_is_advisory_and_ratio_safe(self) -> None:
        case = next(item for item in self.v02e_campaign_suite["cases"] if item["case_id"] == "recovery_load_is_reported_without_claiming_recovery_capacity")
        result = evaluate_campaign_snapshot(case["scenario"])
        self.assertEqual(result["metrics"]["controlled_recovery_strength_fraction"], 1.0)
        self.assertEqual(result["engineering_thresholds"]["status"], "PROJECT_OWNED_BENCHMARK_THRESHOLDS_NOT_EMPIRICAL_TRUTH")
        self.assertIn("REQUIRES_ECONOMY_RECRUITMENT", result["unavailable_dimensions"]["recovery_capacity"])

    def test_v02e_campaign_challenge_scales_to_500_assets_deterministically(self) -> None:
        scenario = {
            "schema_version": 1,
            "scenario_id": "v02e_scale_500_assets",
            "turn": 140,
            "controlled_faction": "rival_bloc",
            "wars": [["rival_bloc", "enemy_a"], ["rival_bloc", "enemy_b"]],
            "armies": [],
            "regions": [],
        }
        for index in range(250):
            faction = "rival_bloc" if index < 100 else ("enemy_a" if index % 2 == 0 else "enemy_b")
            scenario["armies"].append({
                "id": f"army_{index:03d}",
                "faction": faction,
                "strength": 50.0 + (index % 20),
                "x": float(index % 50),
                "y": float(index // 50),
                "movement": 5.0,
                "replenishment": 0.8,
                "visible_to": ["rival_bloc"] if faction != "rival_bloc" else ["rival_bloc"],
            })
        for index in range(250):
            owner = "rival_bloc" if index < 100 else ("enemy_a" if index % 2 == 0 else "enemy_b")
            scenario["regions"].append({
                "id": f"region_{index:03d}",
                "owner": owner,
                "x": float(index % 50),
                "y": float(10 + index // 50),
                "value": 0.5 + (index % 5) * 0.1,
                "threat": 0.1,
                "under_siege": False,
                "garrison_strength": 40.0,
            })
        first = evaluate_campaign_snapshot(scenario)
        second = evaluate_campaign_snapshot(copy.deepcopy(scenario))
        self.assertEqual(first, second)
        self.assertEqual(first["metrics"]["controlled_army_count"], 100)
        self.assertEqual(first["metrics"]["visible_hostile_army_count"], 150)

    def test_v02e_campaign_challenge_input_order_translation_and_strength_scale_invariance(self) -> None:
        result = run_campaign_challenge_matrix(self.v02e_campaign_suite)
        checks = {item["check_id"]: item for item in result["metamorphic_checks"]}
        for name in ("input_order", "coordinate_translation", "uniform_strength_scale"):
            self.assertTrue(checks[name]["passed"])

    def test_v02f_portfolio_artifacts_match_current_implementation(self) -> None:
        envelope = build_cross_evidence_strategic_theater_portfolio(
            self.v02e_campaign_report, self.campaign, self.v02e_campaign_envelope
        )
        matrix = run_strategic_portfolio_matrix(self.v02f_portfolio_suite)
        self.assertEqual(envelope, self.v02f_portfolio_envelope)
        self.assertEqual(matrix, self.v02f_portfolio_matrix)
        self.assertEqual(envelope["result_digest"], "13bd4e418a4056e570a656c6821ee002412c8e3d90f32d61ba2cf333538c5c22")
        self.assertEqual(matrix["result_digest"], "e1c1b8408e3b405bbedbcef01d1802e10206a71c38a9264337aa8cdb62959125")

    def test_v02f_portfolio_is_deterministic_and_no_orders(self) -> None:
        base = self.v02f_portfolio_suite["metamorphic_base"]
        first = build_strategic_theater_portfolio(base)
        second = build_strategic_theater_portfolio(copy.deepcopy(base))
        self.assertEqual(first, second)
        self.assertEqual(first["authority"], "NO_ORDERS")
        self.assertEqual(first["application_authority"], "PROHIBITED")
        self.assertEqual(first["portfolio_constraints"]["force_assignment_status"], "NOT_PERFORMED")

    def test_v02f_portfolio_front_crisis_vetoes_aggressive_commitment(self) -> None:
        case = next(item for item in self.v02f_portfolio_suite["cases"] if item["case_id"] == "coherent_rival_awareness_does_not_override_front_crisis_veto")
        result = build_strategic_theater_portfolio(case["scenario"])
        selected = {item["priority_type"] for item in result["selected_priorities"]}
        self.assertIn("CONTAIN_COHERENT_VISIBLE_RIVAL", selected)
        self.assertFalse(result["portfolio_constraints"]["aggressive_commitment_allowed"])
        self.assertEqual(result["selected_aggressive_priorities"], [])

    def test_v02f_portfolio_critical_overflow_preserves_all_sources(self) -> None:
        case = next(item for item in self.v02f_portfolio_suite["cases"] if item["case_id"] == "critical_front_overflow_preserves_all_sources")
        result = build_strategic_theater_portfolio(case["scenario"])
        self.assertEqual(result["metrics"]["selected_priority_count"], 6)
        self.assertEqual(result["metrics"]["critical_source_count"], 7)
        self.assertEqual(result["metrics"]["critical_source_coverage"], 1.0)
        self.assertIsNotNone(result["critical_overflow"])
        self.assertEqual(result["critical_overflow"]["evidence"]["source_count"], 2)
        self.assertEqual(result["metrics"]["unselected_noncritical_count"], 1)

    def test_v02f_portfolio_fragmented_wars_are_aggregated(self) -> None:
        case = next(item for item in self.v02f_portfolio_suite["cases"] if item["case_id"] == "fragmented_pressure_is_aggregated_not_one_aggression_per_war")
        result = build_strategic_theater_portfolio(case["scenario"])
        types = [item["priority_type"] for item in result["selected_priorities"]]
        self.assertEqual(types.count("MANAGE_FRAGMENTED_VISIBLE_PRESSURE"), 1)
        self.assertNotIn("CONTAIN_COHERENT_VISIBLE_RIVAL", types)
        self.assertFalse(result["portfolio_constraints"]["war_count_rewarded"])

    def test_v02f_portfolio_all_recovery_vetoes_aggression(self) -> None:
        case = next(item for item in self.v02f_portfolio_suite["cases"] if item["case_id"] == "all_recovering_force_vetoes_new_aggression")
        result = build_strategic_theater_portfolio(case["scenario"])
        self.assertTrue(result["portfolio_constraints"]["all_controlled_armies_recovering"])
        self.assertFalse(result["portfolio_constraints"]["aggressive_commitment_allowed"])
        self.assertIn("PROTECT_RECOVERING_FIELD_FORCE", [item["priority_type"] for item in result["selected_priorities"]])

    def test_v02f_portfolio_rejects_forged_or_stale_challenge(self) -> None:
        scenario = copy.deepcopy(self.v02f_portfolio_suite["metamorphic_base"])
        challenge = evaluate_campaign_snapshot(scenario)
        forged = copy.deepcopy(challenge)
        forged["pressure_class"] = "LOW_VISIBLE_PRESSURE"
        forged.pop("result_digest")
        forged["result_digest"] = digest(forged)
        with self.assertRaises(StrategicPortfolioError):
            build_strategic_theater_portfolio(scenario, forged)

    def test_v02f_portfolio_matrix_passes_all_cases_and_metamorphics(self) -> None:
        result = run_strategic_portfolio_matrix(self.v02f_portfolio_suite)
        self.assertEqual(result["scenario_pass_count"], result["scenario_count"])
        self.assertEqual(result["scenario_count"], 12)
        self.assertEqual(result["metamorphic_pass_count"], 6)
        checks = {item["check_id"]: item["passed"] for item in result["metamorphic_checks"]}
        for name in ("hidden_enemy_injection", "player_label_to_npc_label", "input_order", "coordinate_translation", "uniform_strength_scale", "empty_war_edge"):
            self.assertTrue(checks[name])

    def test_v02f_observed_turns_transition_only_when_visible_evidence_changes(self) -> None:
        turns = self.v02f_portfolio_envelope["observed_turns"]
        self.assertEqual([item["turn"] for item in turns], [4, 5, 6, 7])
        self.assertEqual([item["strategic_posture"] for item in turns[:3]], ["CONSOLIDATE_AND_RESERVE"] * 3)
        self.assertEqual(turns[3]["strategic_posture"], "COHERENT_RIVAL_CONTAINMENT")
        self.assertEqual([item["priority_type"] for item in turns[3]["selected_aggressive_priorities"]], ["CONTAIN_COHERENT_VISIBLE_RIVAL"])

    def test_v02f_synthetic_late_game_preserves_crisis_recovery_and_reserve(self) -> None:
        late = self.v02f_portfolio_envelope["synthetic_late_game_reference"]
        types = {item["priority_type"] for item in late["selected_priorities"]}
        self.assertEqual(late["strategic_posture"], "CRISIS_STABILIZATION")
        self.assertIn("MAINTAIN_SIEGE_RELIEF_COVERAGE", types)
        self.assertIn("PROTECT_RECOVERING_FIELD_FORCE", types)
        self.assertIn("PRESERVE_STRATEGIC_RESERVE", types)
        self.assertFalse(late["portfolio_constraints"]["aggressive_commitment_allowed"])

    def test_v02f_portfolio_scales_to_500_assets_deterministically(self) -> None:
        scenario = {
            "schema_version": 1, "scenario_id": "v02f_scale_500", "turn": 150,
            "controlled_faction": "rival_bloc", "wars": [["rival_bloc", "enemy"]],
            "armies": [], "regions": [],
        }
        for index in range(250):
            faction = "rival_bloc" if index < 125 else "enemy"
            scenario["armies"].append({
                "id": f"a{index}", "faction": faction, "strength": 50.0 + index % 10,
                "x": float(index % 50), "y": float(index // 50), "movement": 5.0,
                "replenishment": 0.8, "visible_to": ["rival_bloc"],
            })
        for index in range(250):
            owner = "rival_bloc" if index < 125 else "enemy"
            scenario["regions"].append({
                "id": f"r{index}", "owner": owner, "x": float(index % 50),
                "y": float(10 + index // 50), "value": 1.0, "threat": 0.0,
                "under_siege": False, "garrison_strength": 50.0,
            })
        first = build_strategic_theater_portfolio(scenario)
        second = build_strategic_theater_portfolio(copy.deepcopy(scenario))
        self.assertEqual(first, second)
        self.assertLessEqual(first["metrics"]["selected_priority_count"], 6)
        self.assertEqual(first["metrics"]["critical_source_coverage"], 1.0)


    def test_v02g_force_allocation_artifacts_match_current_implementation(self) -> None:
        allocation = build_cross_evidence_campaign_force_allocation(
            self.v02e_campaign_report,
            self.campaign,
            self.v02e_campaign_envelope,
            self.v02f_portfolio_envelope,
        )
        matrix = run_strategic_assignment_commitment_matrix(self.v02g_assignment_suite)
        self.assertEqual(allocation, self.v02g_force_allocation)
        self.assertEqual(matrix, self.v02g_assignment_matrix)
        self.assertEqual(allocation["result_digest"], "1ea40164577d918e349bd7f2873c0afb4a24ecf98f0e437c244f0ada12ea9f72")
        self.assertEqual(matrix["result_digest"], "61fa5cc91ba3c4a6f96c4e43f3613b01e6b484e606192c3039b33134f821e353")

    def test_v02g_matrix_passes_assignments_temporal_and_metamorphics(self) -> None:
        result = run_strategic_assignment_commitment_matrix(self.v02g_assignment_suite)
        self.assertEqual(result["assignment_pass_count"], result["assignment_case_count"])
        self.assertEqual(result["assignment_case_count"], 8)
        self.assertEqual(result["temporal_pass_count"], result["temporal_case_count"])
        self.assertEqual(result["temporal_case_count"], 6)
        self.assertEqual(result["metamorphic_pass_count"], 7)
        self.assertTrue(all(item["passed"] for item in result["metamorphic_checks"]))

    def test_v02g_recovery_override_is_explicit_and_not_silent(self) -> None:
        case = next(item for item in self.v02g_assignment_suite["assignment_cases"] if item["case_id"] == "critical_front_can_explicitly_override_recovery_lock")
        result = build_theater_to_army_assignment(case["scenario"])
        self.assertEqual(result["metrics"]["recovery_override_count"], 1)
        self.assertEqual(result["assignments"][0]["recovery_override"], True)
        self.assertEqual(result["recovery_protections"][0]["protection_status"], "RECOVERY_PROTECTION_OVERRIDDEN_BY_CRITICAL")
        self.assertEqual(result["authority"], "NO_ORDERS")
        self.assertEqual(result["application_authority"], "PROHIBITED")

    def test_v02g_critical_overflow_expands_exact_sources_and_discloses_shortage(self) -> None:
        case = next(item for item in self.v02g_assignment_suite["assignment_cases"] if item["case_id"] == "critical_overflow_is_expanded_and_resource_shortage_is_explicit")
        result = build_theater_to_army_assignment(case["scenario"])
        self.assertEqual(result["metrics"]["critical_force_priority_count"], 7)
        self.assertEqual(result["metrics"]["assignment_count"], 3)
        self.assertEqual(len([item for item in result["unfilled_priorities"] if item["severity"] == "CRITICAL"]), 4)
        self.assertEqual(sum(1 for item in result["effective_priorities"] if item["via_critical_overflow"]), 2)
        self.assertEqual(result["metrics"]["double_booked_actor_count"], 0)

    def test_v02g_equal_candidate_tie_break_is_deterministic(self) -> None:
        case = next(item for item in self.v02g_assignment_suite["assignment_cases"] if item["case_id"] == "equal_candidate_scores_are_deterministically_tied")
        first = build_theater_to_army_assignment(case["scenario"])
        second = build_theater_to_army_assignment(copy.deepcopy(case["scenario"]))
        self.assertEqual(first, second)
        front = next(item for item in first["assignments"] if item["priority_type"] == "MAINTAIN_SIEGE_RELIEF_COVERAGE")
        self.assertEqual(front["actor_id"], "a1")

    def test_v02g_rejects_forged_or_stale_strategic_portfolio(self) -> None:
        scenario = copy.deepcopy(self.v02g_assignment_suite["metamorphic_assignment_base"])
        portfolio = build_strategic_theater_portfolio(scenario)
        forged = copy.deepcopy(portfolio)
        forged["strategic_posture"] = "CONSOLIDATE_AND_RESERVE"
        forged.pop("result_digest", None)
        forged["result_digest"] = digest(forged)
        with self.assertRaises(StrategicAssignmentError):
            build_theater_to_army_assignment(scenario, strategic_portfolio=forged)

    def test_v02g_observed_reikland_assignment_is_limiting_not_multi_army_proof(self) -> None:
        observed = self.v02g_force_allocation["assignment_envelope"]["observed_assignments"]
        self.assertEqual([item["turn"] for item in observed], [4, 5, 6, 7])
        self.assertEqual([item["metrics"]["assignment_count"] for item in observed], [0, 0, 0, 1])
        self.assertEqual(observed[3]["assignments"][0]["priority_type"], "CONTAIN_COHERENT_VISIBLE_RIVAL")
        self.assertEqual(observed[3]["assignments"][0]["actor_id"], "force:65")
        self.assertIn("only one controlled field army", self.v02g_force_allocation["calibration_limits"][0])

    def test_v02g_synthetic_late_game_preserves_relief_recovery_and_reserve(self) -> None:
        late = self.v02g_force_allocation["assignment_envelope"]["synthetic_late_game_assignment"]
        by_type = {item["priority_type"]: item for item in late["assignments"]}
        self.assertIn("MAINTAIN_SIEGE_RELIEF_COVERAGE", by_type)
        self.assertIn("PRESERVE_STRATEGIC_RESERVE", by_type)
        self.assertEqual(late["metrics"]["recovery_protection_count"], 1)
        self.assertIn(("TRACK_SINGLE_VISIBLE_RIVAL", "AGGRESSIVE_COMMITMENT_VETO"), [(item["priority_type"], item["reason"]) for item in late["unfilled_priorities"]])
        self.assertEqual(late["metrics"]["double_booked_actor_count"], 0)

    def test_v02g_temporal_anti_thrashing_retains_actor_until_review(self) -> None:
        case = next(item for item in self.v02g_assignment_suite["temporal_cases"] if item["case_id"] == "small_geometry_change_does_not_churn_existing_commitment")
        result = build_strategic_temporal_commitment(case["scenarios"])
        reasons = [item["reason"] for item in result["events"]]
        self.assertIn("ANTI_THRASH_RETAIN_EXISTING_ACTOR", reasons)
        self.assertTrue(all(item["metrics"]["double_booked_actor_count"] == 0 for item in result["schedule_slices"]))

    def test_v02g_temporal_review_can_reassign_after_material_margin(self) -> None:
        case = next(item for item in self.v02g_assignment_suite["temporal_cases"] if item["case_id"] == "material_better_actor_waits_until_review_window")
        result = build_strategic_temporal_commitment(case["scenarios"])
        reassign = [item for item in result["events"] if item["event_type"] == "REASSIGN_AFTER_REVIEW"]
        self.assertEqual(len(reassign), 1)
        self.assertEqual(reassign[0]["turn"], 5)

    def test_v02g_temporal_recovery_retirement_and_gap_are_noncausal(self) -> None:
        by_id = {item["case_id"]: item for item in self.v02g_assignment_suite["temporal_cases"]}
        recovery = build_strategic_temporal_commitment(by_id["actor_entering_recovery_cancels_noncritical_commitment"]["scenarios"])
        retirement = build_strategic_temporal_commitment(by_id["disappearing_priority_is_retired_without_causal_credit"]["scenarios"])
        gap = build_strategic_temporal_commitment(by_id["turn_gap_resets_commitment_continuity"]["scenarios"])
        self.assertIn("ACTOR_ENTERED_RECOVERY_PROTECTION", [item["reason"] for item in recovery["events"]])
        self.assertTrue(any("NO_CAUSAL_CREDIT" in item["reason"] for item in retirement["events"]))
        self.assertIn("CONTINUITY_RESET", [item["event_type"] for item in gap["events"]])

    def test_v02g_assignment_scales_to_500_assets_deterministically(self) -> None:
        scenario = {
            "schema_version": 1, "scenario_id": "v02g_scale_500", "turn": 180,
            "controlled_faction": "ai", "wars": [["ai", "enemy"]], "armies": [], "regions": [],
        }
        for index in range(250):
            faction = "ai" if index < 125 else "enemy"
            scenario["armies"].append({
                "id": f"a{index}", "faction": faction, "strength": 50.0 + index % 10,
                "x": float(index % 50), "y": float(index // 50), "movement": 5.0,
                "replenishment": 0.8, "visible_to": ["ai"],
            })
        for index in range(250):
            owner = "ai" if index < 125 else "enemy"
            scenario["regions"].append({
                "id": f"r{index}", "owner": owner, "x": float(index % 50),
                "y": float(10 + index // 50), "value": 1.0, "threat": 0.0,
                "under_siege": False, "garrison_strength": 50.0,
            })
        first = build_theater_to_army_assignment(scenario)
        second = build_theater_to_army_assignment(copy.deepcopy(scenario))
        self.assertEqual(first, second)
        self.assertEqual(first["metrics"]["double_booked_actor_count"], 0)
        self.assertLessEqual(first["metrics"]["assignment_count"], first["metrics"]["eligible_controlled_army_count"])


    def test_v02h_feasibility_artifacts_match_current_implementation(self) -> None:
        envelope = build_cross_evidence_campaign_strategic_feasibility(
            self.v02e_campaign_report, self.v02g_force_allocation
        )
        matrix = run_strategic_feasibility_matrix(self.v02h_feasibility_suite)
        self.assertEqual(envelope, self.v02h_feasibility_envelope)
        self.assertEqual(matrix, self.v02h_feasibility_matrix)
        self.assertEqual(envelope["result_digest"], "b6519eb75d141642a925f919f20fe1cf7300655b40300660dd1aabf8a873f553")
        self.assertEqual(matrix["result_digest"], "08614e2a7e292b495ecb93a54375bc7782b7e7b7a02502d1c4e8a56d59f07cea")

    def test_v02h_observed_turn7_plan_is_exactly_one_unobserved_faction_centroid_plan(self) -> None:
        envelope = self.v02h_feasibility_envelope
        self.assertEqual(envelope["turns_without_force_assignment"], [4, 5, 6])
        self.assertEqual(envelope["metrics"]["observed_assignment_plan_count"], 1)
        self.assertEqual(envelope["metrics"]["live_query_result_count"], 0)
        plan = envelope["observed_feasibility_plans"][0]
        self.assertEqual(plan["actor"]["character_cqi"], 120)
        self.assertEqual(plan["actor"]["force_cqi"], 65)
        self.assertEqual(plan["target_boundary"]["assignment_target_kind"], "FACTION")
        self.assertFalse(plan["target_boundary"]["faction_centroid_is_attack_target"])
        self.assertEqual(plan["query_count"], 8)
        self.assertTrue(all(item["result_status"] == "UNOBSERVED_QUERY_NOT_RUN" for item in plan["queries"]))

    def test_v02h_region_target_can_resolve_settlement_without_attack_promotion(self) -> None:
        case = next(item for item in self.v02h_feasibility_suite["cases"] if item["case_id"] == "region_target_exposes_point_and_settlement_queries")
        assignment = next(item for item in build_theater_to_army_assignment(case["scenario"])["assignments"] if item["priority_type"] == case["priority_type"])
        plan = build_campaign_strategic_feasibility_plan(case["scenario"], assignment)
        keys = {item["query_key"] for item in plan["queries"]}
        self.assertIn("SETTLEMENT_REACHABLE_THIS_TURN", keys)
        self.assertIn("SETTLEMENT_EVER_REACHABLE", keys)
        self.assertTrue(plan["target_boundary"]["settlement_interface_query_permitted"])
        self.assertFalse(plan["target_boundary"]["settlement_target_promoted"])
        self.assertFalse(plan["target_boundary"]["concrete_attack_target_promoted"])
        self.assertNotIn("GARRISON_CAN_ASSAULT", keys)

    def test_v02h_faction_centroid_never_becomes_character_or_settlement_target(self) -> None:
        case = next(item for item in self.v02h_feasibility_suite["cases"] if item["case_id"] == "faction_centroid_is_point_only_not_attack_target")
        assignment = next(item for item in build_theater_to_army_assignment(case["scenario"])["assignments"] if item["priority_type"] == case["priority_type"])
        plan = build_campaign_strategic_feasibility_plan(case["scenario"], assignment)
        keys = {item["query_key"] for item in plan["queries"]}
        self.assertIn("POSITION_REACHABLE_THIS_TURN", keys)
        self.assertNotIn("SETTLEMENT_REACHABLE_THIS_TURN", keys)
        self.assertFalse(plan["target_boundary"]["settlement_interface_query_permitted"])
        self.assertFalse(plan["target_boundary"]["settlement_target_promoted"])
        self.assertFalse(plan["target_boundary"]["faction_centroid_is_attack_target"])

    def test_v02h_missing_stance_does_not_invent_stance_specific_reachability(self) -> None:
        case = next(item for item in self.v02h_feasibility_suite["cases"] if item["case_id"] == "missing_stance_does_not_invent_stance_specific_query")
        assignment = next(item for item in build_theater_to_army_assignment(case["scenario"])["assignments"] if item["priority_type"] == case["priority_type"])
        plan = build_campaign_strategic_feasibility_plan(case["scenario"], assignment)
        keys = {item["query_key"] for item in plan["queries"]}
        self.assertNotIn("POSITION_REACHABLE_THIS_TURN_IN_STANCE", keys)
        self.assertNotIn("SETTLEMENT_REACHABLE_THIS_TURN_IN_STANCE", keys)
        self.assertIn("FORCE_ACTIVE_STANCE", keys)

    def test_v02h_observed_query_results_do_not_grant_application_or_causality(self) -> None:
        case = next(item for item in self.v02h_feasibility_suite["cases"] if item["case_id"] == "faction_centroid_is_point_only_not_attack_target")
        assignment = next(item for item in build_theater_to_army_assignment(case["scenario"])["assignments"] if item["priority_type"] == case["priority_type"])
        plan = build_campaign_strategic_feasibility_plan(case["scenario"], assignment)
        packet = build_observation_packet_template(plan)
        for item in packet["results"]:
            item["observed"] = True
            item["value"] = "MILITARY_FORCE_ACTIVE_STANCE_TYPE_DEFAULT" if item["query_key"] == "FORCE_ACTIVE_STANCE" else True
        packet.pop("result_digest")
        packet["result_digest"] = digest(packet)
        result = adjudicate_campaign_strategic_feasibility_observation(plan, packet)
        self.assertEqual(result["application_authority"], "PROHIBITED")
        self.assertFalse(result["capability_boundary"]["orders_emitted"])
        self.assertFalse(result["capability_boundary"]["execution_observed"])
        self.assertFalse(result["capability_boundary"]["causal_outcome_observed"])
        self.assertTrue(all(item["action_legality"] == "NOT_ESTABLISHED" for item in result["queries"]))

    def test_v02h_observation_rejects_stale_and_foreign_query_packets(self) -> None:
        plan = self.v02h_feasibility_envelope["observed_feasibility_plans"][0]
        packet = build_observation_packet_template(plan)
        stale = copy.deepcopy(packet)
        stale["turn"] += 1
        stale.pop("result_digest")
        stale["result_digest"] = digest(stale)
        with self.assertRaises(StrategicFeasibilityError):
            adjudicate_campaign_strategic_feasibility_observation(plan, stale)
        foreign = copy.deepcopy(packet)
        foreign["results"][0]["query_id"] = "0" * 64
        foreign.pop("result_digest")
        foreign["result_digest"] = digest(foreign)
        with self.assertRaises(StrategicFeasibilityError):
            adjudicate_campaign_strategic_feasibility_observation(plan, foreign)

    def test_v02h_rejects_forged_assignment_authority(self) -> None:
        case = next(item for item in self.v02h_feasibility_suite["cases"] if item["case_id"] == "faction_centroid_is_point_only_not_attack_target")
        assignment = next(item for item in build_theater_to_army_assignment(case["scenario"])["assignments"] if item["priority_type"] == case["priority_type"])
        forged = copy.deepcopy(assignment)
        forged["application_authority"] = "ALLOWED"
        forged.pop("result_digest")
        forged["result_digest"] = digest(forged)
        with self.assertRaises(StrategicFeasibilityError):
            build_campaign_strategic_feasibility_plan(case["scenario"], forged)

    def test_v02h_matrix_passes_cases_metamorphics_observation_and_tamper_checks(self) -> None:
        result = run_strategic_feasibility_matrix(self.v02h_feasibility_suite)
        self.assertTrue(result["passed"])
        self.assertEqual(result["case_pass_count"], 5)
        self.assertEqual(result["metamorphic_pass_count"], 5)
        self.assertTrue(all(result["synthetic_observation_checks"].values()))
        self.assertTrue(all(result["tamper_checks"].values()))

    def test_v02h_ambiguous_garrison_assault_surface_is_catalogued_but_not_planned(self) -> None:
        catalog = {item["query_key"]: item for item in self.v02h_feasibility_envelope["documented_query_catalog"]}
        self.assertEqual(catalog["GARRISON_CAN_ASSAULT"]["classification"], "DOCUMENTED_AMBIGUOUS_CONTEXT_NOT_PROMOTED")
        planned = {item["query_key"] for plan in self.v02h_feasibility_envelope["observed_feasibility_plans"] for item in plan["queries"]}
        self.assertNotIn("GARRISON_CAN_ASSAULT", planned)

    def test_v02h_query_plan_is_bounded_and_deterministic(self) -> None:
        for case in self.v02h_feasibility_suite["cases"]:
            assignment = next(item for item in build_theater_to_army_assignment(case["scenario"])["assignments"] if item["priority_type"] == case["priority_type"])
            first = build_campaign_strategic_feasibility_plan(case["scenario"], assignment)
            second = build_campaign_strategic_feasibility_plan(copy.deepcopy(case["scenario"]), copy.deepcopy(assignment))
            self.assertEqual(first, second)
            self.assertLessEqual(first["query_count"], 13)
            self.assertEqual(len({item["query_id"] for item in first["queries"]}), first["query_count"])

    def test_v02h_mutation_surface_catalog_is_explicit_and_application_remains_prohibited(self) -> None:
        self.assertIn("cm:attack", PROHIBITED_MUTATION_SURFACES)
        self.assertIn("cm:move_to", PROHIBITED_MUTATION_SURFACES)
        self.assertIn("cm:force_character_force_into_stance", PROHIBITED_MUTATION_SURFACES)
        self.assertEqual(self.v02h_feasibility_envelope["application_authority"], "PROHIBITED")
        self.assertEqual(self.v02h_feasibility_envelope["metrics"]["campaign_orders_emitted"], 0)

    def test_v02j_native_behavior_matrix_is_deterministic_and_passes(self) -> None:
        first = run_native_behavior_adversarial_matrix(self.v02j_native_behavior_suite)
        second = run_native_behavior_adversarial_matrix(copy.deepcopy(self.v02j_native_behavior_suite))
        self.assertEqual(first, second)
        self.assertEqual(first, self.v02j_native_behavior_matrix)
        self.assertTrue(first["all_passed"])
        self.assertEqual(first["pass_count"], 9)

    def test_v02j_recovery_misuse_requires_observed_offensive_engagement(self) -> None:
        case = next(
            item for item in self.v02j_native_behavior_suite["cases"]
            if item["case_id"] == "recovering_offensive_engagement_is_measured"
        )
        result = analyze_native_behavior_trace(case["trace"])
        self.assertEqual(result["metrics"]["recovering_army_offensive_engagement_count"], 1)
        self.assertEqual(result["metrics"]["recovering_army_offensive_engagement_rate"], 1.0)
        self.assertIn("requires an observed engagement event", result["interpretation_limits"][2])

    def test_v02j_crisis_retarget_does_not_false_positive_as_thrashing(self) -> None:
        case = next(
            item for item in self.v02j_native_behavior_suite["cases"]
            if item["case_id"] == "new_local_crisis_explains_directional_retarget"
        )
        result = analyze_native_behavior_trace(case["trace"])
        self.assertEqual(result["metrics"]["unexplained_directional_reversal_proxy_count"], 0)
        self.assertEqual(result["metrics"]["context_explained_retarget_proxy_count"], 1)

    def test_v02j_assignment_exclusivity_remains_unavailable(self) -> None:
        case = self.v02j_native_behavior_suite["cases"][0]
        result = analyze_native_behavior_trace(case["trace"])
        self.assertEqual(result["assignment_exclusivity_visibility"], "UNAVAILABLE_FROM_TRAJECTORY_ONLY")
        self.assertEqual(result["native_assignment_memory_visibility"], "UNAVAILABLE")
        self.assertEqual(result["native_hysteresis_visibility"], "UNAVAILABLE")

    def test_v02j_authority_and_event_contract_fail_closed(self) -> None:
        case = copy.deepcopy(self.v02j_native_behavior_suite["cases"][0]["trace"])
        case["authority"] = "ISSUE_ORDERS"
        with self.assertRaises(NativeBehaviorError):
            analyze_native_behavior_trace(case)

        bad_event = copy.deepcopy(
            next(
                item for item in self.v02j_native_behavior_suite["cases"]
                if item["case_id"] == "recovering_offensive_engagement_is_measured"
            )["trace"]
        )
        bad_event["observations"][0]["events"][0]["event_type"] = "NATIVE_TASK_ASSIGNMENT"
        with self.assertRaises(NativeBehaviorError):
            analyze_native_behavior_trace(bad_event)


    def test_v02k_player_visible_partial_trace_refuses_full_faction_metrics(self) -> None:
        trace = {
            "contract": "NATIVE_CAI_PLAYER_VISIBLE_PARTIAL_TRACE_V1",
            "authority": "NO_ORDERS",
            "application_authority": "PROHIBITED",
            "foreign_visibility_source": "WH3_PLAYER_FILTERED_LISTS",
            "observer_faction": "human",
            "observed_ai_faction": "ai",
            "frames": [
                {"turn": 1, "visible_armies": [{"id": "ai1", "faction": "ai", "x": 0, "y": 0}], "visible_regions": []},
                {"turn": 2, "visible_armies": [{"id": "ai1", "faction": "ai", "x": 1, "y": 0}], "visible_regions": []},
            ],
        }
        result = analyze_player_visible_native_trace(trace)
        self.assertEqual(result["observation_scope"], "PLAYER_VISIBLE_PARTIAL_FOREIGN_AI")
        self.assertEqual(result["availability"]["front_coverage"], "UNAVAILABLE_INCOMPLETE_FOREIGN_FACTION_VISIBILITY")
        self.assertEqual(result["availability"]["recovery_misuse"], "UNAVAILABLE_NO_SAFE_FOREIGN_REPLENISHMENT_AT_ENGAGEMENT")
        self.assertEqual(result["availability"]["reserve_adequacy"], "UNAVAILABLE_INCOMPLETE_FOREIGN_FACTION_VISIBILITY")
        self.assertEqual(result["availability"]["assignment_exclusivity"], "UNAVAILABLE_FROM_TRAJECTORY_ONLY")
        self.assertEqual(result["metrics"]["unanchored_movement_intervals"], 1)

    def test_v02k_visible_anchor_change_is_candidate_not_task_churn(self) -> None:
        trace = {
            "contract": "NATIVE_CAI_PLAYER_VISIBLE_PARTIAL_TRACE_V1",
            "authority": "NO_ORDERS",
            "application_authority": "PROHIBITED",
            "foreign_visibility_source": "WH3_PLAYER_FILTERED_LISTS",
            "observer_faction": "human",
            "observed_ai_faction": "ai",
            "frames": [
                {"turn": 1, "visible_armies": [{"id": "ai1", "faction": "ai", "x": 0, "y": 0}], "visible_regions": [{"id": "left", "owner": "human", "x": -10, "y": 0}, {"id": "right", "owner": "human", "x": 10, "y": 0}]},
                {"turn": 2, "visible_armies": [{"id": "ai1", "faction": "ai", "x": 3, "y": 0}], "visible_regions": [{"id": "left", "owner": "human", "x": -10, "y": 0}, {"id": "right", "owner": "human", "x": 10, "y": 0}]},
                {"turn": 3, "visible_armies": [{"id": "ai1", "faction": "ai", "x": 0, "y": 0}], "visible_regions": [{"id": "left", "owner": "human", "x": -10, "y": 0}, {"id": "right", "owner": "human", "x": 10, "y": 0}]},
            ],
        }
        result = analyze_player_visible_native_trace(trace)
        self.assertEqual(result["metrics"]["visible_anchor_direction_change_candidate_count"], 1)
        candidate = result["visible_anchor_direction_change_candidates"][0]
        self.assertEqual(candidate["classification"], "VISIBLE_ANCHOR_DIRECTION_CHANGE_CANDIDATE_NOT_TASK_CHURN")
        self.assertTrue(candidate["prior_anchor_still_player_visible"])
        self.assertEqual(result["availability"]["native_hysteresis"], "UNAVAILABLE")

    def test_v02k_visibility_loss_is_right_censored_not_destroyed(self) -> None:
        trace = {
            "contract": "NATIVE_CAI_PLAYER_VISIBLE_PARTIAL_TRACE_V1",
            "authority": "NO_ORDERS",
            "application_authority": "PROHIBITED",
            "foreign_visibility_source": "WH3_PLAYER_FILTERED_LISTS",
            "observer_faction": "human",
            "observed_ai_faction": "ai",
            "frames": [
                {"turn": 1, "visible_armies": [{"id": "ai1", "faction": "ai", "x": 0, "y": 0}], "visible_regions": []},
                {"turn": 2, "visible_armies": [], "visible_regions": []},
            ],
        }
        result = analyze_player_visible_native_trace(trace)
        self.assertEqual(result["metrics"]["visibility_loss_count"], 1)
        self.assertEqual(result["visibility_losses"][0]["classification"], "LEFT_PLAYER_VISIBLE_SET_RIGHT_CENSORED_NOT_DEATH")
        self.assertIn("right-censored", result["interpretation_limits"][1])

    def test_v02k_partial_trace_fails_closed_on_privileged_or_empty_target_scope(self) -> None:
        base = {
            "contract": "NATIVE_CAI_PLAYER_VISIBLE_PARTIAL_TRACE_V1",
            "authority": "NO_ORDERS",
            "application_authority": "PROHIBITED",
            "foreign_visibility_source": "WH3_PLAYER_FILTERED_LISTS",
            "observer_faction": "human",
            "observed_ai_faction": "ai",
            "frames": [
                {"turn": 1, "visible_armies": [{"id": "ai1", "faction": "ai", "x": 0, "y": 0}], "visible_regions": []},
                {"turn": 2, "visible_armies": [{"id": "ai1", "faction": "ai", "x": 0, "y": 0}], "visible_regions": []},
            ],
        }
        privileged = copy.deepcopy(base)
        privileged["foreign_visibility_source"] = "ALL_FACTION_FORCES"
        with self.assertRaises(NativeVisibleBehaviorError):
            analyze_player_visible_native_trace(privileged)
        absent = copy.deepcopy(base)
        for frame in absent["frames"]:
            frame["visible_armies"] = []
        with self.assertRaises(NativeVisibleBehaviorError):
            analyze_player_visible_native_trace(absent)

    def test_v02l_native_visible_churn_adversarial_matrix_is_frozen_and_passes(self) -> None:
        first = run_native_churn_adversarial_matrix(self.v02l_native_churn_suite)
        second = run_native_churn_adversarial_matrix(copy.deepcopy(self.v02l_native_churn_suite))
        self.assertEqual(first, second)
        self.assertEqual(first, self.v02l_native_churn_matrix)
        self.assertTrue(first["all_passed"])
        self.assertEqual(first["case_count"], 9)
        self.assertEqual(first["pass_count"], 9)

    def test_v02l_clean_repeated_oscillation_requires_two_nonoverlapping_episodes(self) -> None:
        case = next(item for item in self.v02l_native_churn_suite["cases"] if item["case_id"] == "repeated_clean_region_oscillation")
        result = analyze_visible_directional_churn(case["trace"])
        self.assertEqual(result["metrics"]["oscillation_candidate_count"], 4)
        self.assertEqual(result["metrics"]["repeated_oscillation_cluster_count"], 1)
        cluster = result["repeated_oscillation_clusters"][0]
        self.assertEqual(cluster["nonoverlapping_episode_count"], 2)
        self.assertEqual(cluster["classification"], "REPEATED_STABLE_CONTEXT_REGION_OSCILLATION_CLUSTER")
        self.assertEqual(cluster["causal_status"], "REQUIRES_REVIEW_HIDDEN_CONTEXT_REMAINS_UNOBSERVED")
        self.assertEqual(result["availability"]["native_hysteresis"], "UNAVAILABLE_ENGINE_INTERNAL")
        self.assertEqual(result["application_authority"], "PROHIBITED")

    def test_v02l_single_aba_cannot_trigger_primary_signal(self) -> None:
        case = next(item for item in self.v02l_native_churn_suite["cases"] if item["case_id"] == "single_aba_is_candidate_not_primary_signal")
        result = analyze_visible_directional_churn(case["trace"] )
        self.assertEqual(result["metrics"]["oscillation_candidate_count"], 1)
        self.assertEqual(result["metrics"]["repeated_oscillation_cluster_count"], 0)
        self.assertEqual(result["status"], "NO_REPEATED_SIGNAL_OBSERVED_NOT_PROOF_OF_NATIVE_HYSTERESIS")

    def test_v02l_translation_and_input_order_do_not_change_semantic_churn_result(self) -> None:
        case = next(item for item in self.v02l_native_churn_suite["cases"] if item["case_id"] == "repeated_clean_region_oscillation")
        original = copy.deepcopy(case["trace"] )
        transformed = copy.deepcopy(original)
        for frame in transformed["frames"]:
            frame["visible_armies"].reverse()
            frame["visible_regions"].reverse()
            for army in frame["visible_armies"]:
                army["x"] += 113.0
                army["y"] -= 47.0
            for region in frame["visible_regions"]:
                region["x"] += 113.0
                region["y"] -= 47.0
        left = analyze_visible_directional_churn(original)
        right = analyze_visible_directional_churn(transformed)
        self.assertEqual(left, right)

    def test_v02l_cohort_comparison_is_descriptive_and_cannot_earn_project_planner(self) -> None:
        positive = next(item for item in self.v02l_native_churn_suite["cases"] if item["case_id"] == "repeated_clean_region_oscillation")["trace"]
        negative = next(item for item in self.v02l_native_churn_suite["cases"] if item["case_id"] == "one_direction_is_not_churn")["trace"]
        result = compare_visible_directional_churn_cohorts([
            {"run_id": "vanilla-1", "profile": "VANILLA", "trace": positive},
            {"run_id": "sfo-1", "profile": "SFO", "trace": negative},
        ])
        self.assertEqual(result["comparison_status"], "DESCRIPTIVE_ONLY_NO_CAUSAL_OR_SIGNIFICANCE_CLAIM")
        self.assertEqual(result["profiles"]["VANILLA"]["repeated_oscillation_cluster_count"], 1)
        self.assertEqual(result["profiles"]["SFO"]["repeated_oscillation_cluster_count"], 0)
        self.assertIn("cannot justify project-owned strategic planning", result["decision_rule"]["project_planner_not_earned_when"] )
        self.assertEqual(result["authority"], "NO_ORDERS")
        self.assertEqual(result["application_authority"], "PROHIBITED")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import argparse
import json
import sys
import unittest
from pathlib import Path

from .battle import run_battle
from .campaign import run_campaign
from .canonical import read_json, write_json
from .contracts import validate_campaign_scenario
from .decision import assign_objectives
from .ensemble import run_ensemble
from .mod_audit import audit_extracted_zip, audit_pack, compare_audits
from .observed_battle import derive_reality_regressions
from .battle_trace import derive_tactical_trace_benchmarks
from .battle_shadow import run_trace_shadow_evaluator
from .tactical_adversary import run_tactical_adversarial_suite
from .tactical_assignment import build_trace_objective_assignments
from .tactical_assignment_matrix import run_tactical_assignment_matrix
from .tactical_schedule import build_trace_tactical_temporal_schedule
from .tactical_schedule_matrix import run_tactical_schedule_matrix
from .action_authority import build_action_authority_matrix, build_battle4_authority_boundary_report
from .tactical_feasibility import (
    build_live_feasibility_capability_profile,
    build_trace_tactical_feasibility_envelope,
)
from .tactical_feasibility_matrix import run_tactical_feasibility_matrix
from .tactical_guarded import build_trace_guarded_action_packets
from .tactical_guarded_matrix import run_tactical_guarded_matrix
from .tactical_reservation import build_trace_endpoint_reservations
from .tactical_reservation_matrix import run_tactical_reservation_matrix
from .tactical_pipeline_audit import run_tactical_pipeline_audit
from .replay_visual_calibration import build_dual_replay_calibration
from .defeat_visual_preparation import build_chaos_defeat_capture_readiness
from .chaos_replay_adjudication import build_chaos_replay_divergence_calibration
from .tactical_policy import build_cross_corpus_policy_envelope
from .tactical_policy_matrix import run_tactical_policy_matrix
from .campaign_challenge import build_campaign_challenge_envelope, evaluate_campaign_snapshot
from .campaign_challenge_matrix import run_campaign_challenge_matrix
from .strategic_portfolio import build_cross_evidence_strategic_theater_portfolio, build_strategic_theater_portfolio
from .strategic_portfolio_matrix import run_strategic_portfolio_matrix
from .strategic_assignment import build_theater_to_army_assignment
from .strategic_commitment import (
    build_cross_evidence_campaign_force_allocation,
    build_strategic_temporal_commitment,
)
from .strategic_assignment_matrix import run_strategic_assignment_commitment_matrix
from .strategic_feasibility import build_cross_evidence_campaign_strategic_feasibility
from .strategic_feasibility_matrix import run_strategic_feasibility_matrix
from .native_behavior import analyze_native_behavior_trace
from .native_behavior_matrix import run_native_behavior_adversarial_matrix


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_profile(path: str | None) -> dict:
    return read_json(path or _root() / "profiles" / "vanilla_8_1_1.json")


def _emit(value: dict, output: str | None) -> None:
    if output:
        write_json(output, value)
    print(json.dumps(value, indent=2, sort_keys=True))


def command_validate(args: argparse.Namespace) -> None:
    result = validate_campaign_scenario(read_json(args.scenario))
    _emit({"valid": True, "scenario_id": result["scenario_id"]}, args.output)


def command_tier1(args: argparse.Namespace) -> None:
    _emit(assign_objectives(read_json(args.scenario), _load_profile(args.profile)), args.output)


def command_tier2(args: argparse.Namespace) -> None:
    _emit(run_campaign(read_json(args.scenario), _load_profile(args.profile), args.turns, args.seed), args.output)


def command_tier3(args: argparse.Namespace) -> None:
    seeds = [int(item) for item in args.seeds.split(",") if item.strip()]
    _emit(run_ensemble(read_json(args.scenario), _load_profile(args.profile), args.turns, seeds), args.output)


def command_tier4(args: argparse.Namespace) -> None:
    _emit(run_battle(read_json(args.scenario), args.seed), args.output)


def command_tier4r(args: argparse.Namespace) -> None:
    _emit(derive_reality_regressions(read_json(args.corpus)), args.output)


def command_tier4r_trace(args: argparse.Namespace) -> None:
    _emit(
        derive_tactical_trace_benchmarks(
            read_json(args.corpus),
            read_json(args.trace_slices),
        ),
        args.output,
    )


def command_tier4r_shadow(args: argparse.Namespace) -> None:
    dense_corpus = read_json(args.dense_corpus) if args.dense_corpus else None
    _emit(
        run_trace_shadow_evaluator(read_json(args.trace_slices), dense_corpus),
        args.output,
    )



def command_tier4r_adversary(args: argparse.Namespace) -> None:
    _emit(
        run_tactical_adversarial_suite(
            read_json(args.trace_slices),
            read_json(args.suite),
        ),
        args.output,
    )


def command_tier4r_assignment(args: argparse.Namespace) -> None:
    _emit(
        build_trace_objective_assignments(read_json(args.trace_slices)),
        args.output,
    )


def command_assignment_matrix(args: argparse.Namespace) -> None:
    _emit(
        run_tactical_assignment_matrix(
            read_json(args.trace_slices),
            read_json(args.baseline_suite),
            read_json(args.assignment_suite),
        ),
        args.output,
    )


def command_tier4r_schedule(args: argparse.Namespace) -> None:
    _emit(
        build_trace_tactical_temporal_schedule(read_json(args.trace_slices)),
        args.output,
    )


def command_schedule_matrix(args: argparse.Namespace) -> None:
    _emit(
        run_tactical_schedule_matrix(
            read_json(args.trace_slices),
            read_json(args.baseline_suite),
            read_json(args.schedule_suite),
        ),
        args.output,
    )


def command_action_authority_matrix(args: argparse.Namespace) -> None:
    _emit(build_action_authority_matrix(read_json(args.suite)), args.output)


def command_battle4_action_authority(args: argparse.Namespace) -> None:
    _emit(
        build_battle4_authority_boundary_report(
            read_json(args.dense_corpus),
            read_json(args.temporal_schedule),
        ),
        args.output,
    )




def command_tier4r_feasibility(args: argparse.Namespace) -> None:
    capability_profile = None
    if args.live_adjudication:
        capability_profile = build_live_feasibility_capability_profile(
            read_json(args.live_adjudication)
        )
    _emit(
        build_trace_tactical_feasibility_envelope(
            read_json(args.trace_slices),
            capability_profile=capability_profile,
        ),
        args.output,
    )


def command_feasibility_matrix(args: argparse.Namespace) -> None:
    _emit(
        run_tactical_feasibility_matrix(
            read_json(args.trace_slices),
            read_json(args.baseline_suite),
            read_json(args.feasibility_suite),
        ),
        args.output,
    )


def command_tier4r_guarded(args: argparse.Namespace) -> None:
    capability_profile = read_json(args.semantic_capability_profile) if args.semantic_capability_profile else None
    _emit(
        build_trace_guarded_action_packets(
            read_json(args.trace_slices),
            capability_profile=capability_profile,
        ),
        args.output,
    )


def command_guarded_matrix(args: argparse.Namespace) -> None:
    _emit(
        run_tactical_guarded_matrix(
            read_json(args.trace_slices),
            read_json(args.baseline_suite),
            read_json(args.feasibility_suite),
            read_json(args.guarded_suite),
        ),
        args.output,
    )


def command_tier4r_reservations(args: argparse.Namespace) -> None:
    capability_profile = read_json(args.semantic_capability_profile) if args.semantic_capability_profile else None
    _emit(
        build_trace_endpoint_reservations(
            read_json(args.trace_slices),
            capability_profile=capability_profile,
        ),
        args.output,
    )


def command_reservation_matrix(args: argparse.Namespace) -> None:
    _emit(run_tactical_reservation_matrix(read_json(args.suite)), args.output)


def command_pipeline_audit(args: argparse.Namespace) -> None:
    _emit(
        run_tactical_pipeline_audit(
            read_json(args.trace_slices),
            read_json(args.baseline_suite),
            read_json(args.feasibility_suite),
            read_json(args.audit_suite),
        ),
        args.output,
    )


def command_sfo_dual_replay_calibration(args: argparse.Namespace) -> None:
    _emit(
        build_dual_replay_calibration(
            read_json(args.visual_alignment),
            {
                "ubersreik": read_json(args.ubersreik_dense),
                "marienburg": read_json(args.marienburg_dense),
            },
        ),
        args.output,
    )


def command_sfo_chaos_defeat_preparation(args: argparse.Namespace) -> None:
    _emit(
        build_chaos_defeat_capture_readiness(read_json(args.visual_preparation)),
        args.output,
    )


def command_sfo_chaos_replay_adjudication(args: argparse.Namespace) -> None:
    _emit(
        build_chaos_replay_divergence_calibration(
            read_json(args.capture),
            read_json(args.dense_corpus),
            read_json(args.unit_findings),
        ),
        args.output,
    )


def command_cross_corpus_policy(args: argparse.Namespace) -> None:
    _emit(
        build_cross_corpus_policy_envelope(
            {
                "eilhart": read_json(args.eilhart_dense),
                "ubersreik": read_json(args.ubersreik_dense),
                "marienburg": read_json(args.marienburg_dense),
                "chaos": read_json(args.chaos_dense),
            },
            read_json(args.dual_replay_calibration),
            read_json(args.chaos_replay_calibration),
        ),
        args.output,
    )


def command_policy_matrix(args: argparse.Namespace) -> None:
    _emit(
        run_tactical_policy_matrix(
            read_json(args.policy),
            read_json(args.suite),
        ),
        args.output,
    )



def command_campaign_challenge(args: argparse.Namespace) -> None:
    if args.observed_report:
        _emit(
            build_campaign_challenge_envelope(
                read_json(args.observed_report),
                read_json(args.scenario),
            ),
            args.output,
        )
    else:
        _emit(evaluate_campaign_snapshot(read_json(args.scenario)), args.output)


def command_campaign_challenge_matrix(args: argparse.Namespace) -> None:
    _emit(run_campaign_challenge_matrix(read_json(args.suite)), args.output)


def command_strategic_portfolio(args: argparse.Namespace) -> None:
    if args.observed_report and args.challenge_envelope:
        _emit(
            build_cross_evidence_strategic_theater_portfolio(
                read_json(args.observed_report),
                read_json(args.scenario),
                read_json(args.challenge_envelope),
            ),
            args.output,
        )
    else:
        challenge = read_json(args.challenge_envelope) if args.challenge_envelope else None
        _emit(build_strategic_theater_portfolio(read_json(args.scenario), challenge), args.output)


def command_strategic_portfolio_matrix(args: argparse.Namespace) -> None:
    _emit(run_strategic_portfolio_matrix(read_json(args.suite)), args.output)


def command_strategic_assignment(args: argparse.Namespace) -> None:
    challenge = read_json(args.challenge_envelope) if args.challenge_envelope else None
    portfolio = read_json(args.strategic_portfolio) if args.strategic_portfolio else None
    _emit(build_theater_to_army_assignment(read_json(args.scenario), challenge, portfolio), args.output)


def command_strategic_commitment(args: argparse.Namespace) -> None:
    payload = read_json(args.sequence)
    scenarios = payload["scenarios"] if isinstance(payload, dict) and "scenarios" in payload else payload
    _emit(build_strategic_temporal_commitment(scenarios), args.output)


def command_strategic_force_allocation(args: argparse.Namespace) -> None:
    _emit(
        build_cross_evidence_campaign_force_allocation(
            read_json(args.observed_report),
            read_json(args.late_game_scenario),
            read_json(args.challenge_envelope),
            read_json(args.strategic_portfolio),
        ),
        args.output,
    )


def command_strategic_assignment_matrix(args: argparse.Namespace) -> None:
    _emit(run_strategic_assignment_commitment_matrix(read_json(args.suite)), args.output)

def command_strategic_feasibility(args: argparse.Namespace) -> None:
    _emit(
        build_cross_evidence_campaign_strategic_feasibility(
            read_json(args.observed_report),
            read_json(args.force_allocation),
        ),
        args.output,
    )


def command_strategic_feasibility_matrix(args: argparse.Namespace) -> None:
    _emit(run_strategic_feasibility_matrix(read_json(args.suite)), args.output)

def command_audit(args: argparse.Namespace) -> None:
    audits = []
    for spec in args.pack:
        source_id, path = spec.split("=", 1)
        audits.append(audit_pack(path, source_id))
    for spec in args.extracted_zip:
        source_id, path = spec.split("=", 1)
        audits.append(audit_extracted_zip(path, source_id))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for audit in audits:
        write_json(output_dir / f"{audit['source_id']}_audit.json", audit)
    comparison = compare_audits(audits)
    write_json(output_dir / "comparison.json", comparison)
    _emit(comparison, None)


def command_smoke(args: argparse.Namespace) -> None:
    root = _root()
    profile = read_json(root / "profiles" / "vanilla_8_1_1.json")
    campaign = read_json(root / "scenarios" / "tier2_late_game_pressure.json")
    battle = read_json(root / "scenarios" / "tier4_outnumbered_empire.json")
    observed = read_json(root / "corpora" / "battle4_eilhart_observed_v1.json")
    observed_dense = read_json(root / "corpora" / "battle4_eilhart_observed_dense_v2.json")
    trace_slices = read_json(root / "corpora" / "battle4_eilhart_trace_slices_v1.json")
    cross_corpus_policy = build_cross_corpus_policy_envelope(
        {
            "eilhart": observed_dense,
            "ubersreik": read_json(root / "corpora" / "sfo_ubersreik_observed_dense_v0.2A.json"),
            "marienburg": read_json(root / "corpora" / "sfo_marienburg_observed_dense_v0.2A.json"),
            "chaos": read_json(root / "corpora" / "sfo_chaos_replay_stream_observed_dense_v0.2C.json"),
        },
        read_json(root.parent / "research" / "runtime_evidence" / "SFO_REIKLAND_DUAL_REPLAY_TACTICAL_CALIBRATION_v0.2A.json"),
        read_json(root.parent / "research" / "runtime_evidence" / "SFO_REIKLAND_CHAOS_REPLAY_DIVERGENCE_CALIBRATION_v0.2C.json"),
    )
    campaign_challenge_envelope = build_campaign_challenge_envelope(
        read_json(root.parent / "research" / "runtime_evidence" / "CAMPAIGN_TURNS_4_7_REPROCESS_v0.1J.json"),
        campaign,
    )
    strategic_portfolio_envelope = build_cross_evidence_strategic_theater_portfolio(
        read_json(root.parent / "research" / "runtime_evidence" / "CAMPAIGN_TURNS_4_7_REPROCESS_v0.1J.json"),
        campaign,
        campaign_challenge_envelope,
    )
    strategic_force_allocation = build_cross_evidence_campaign_force_allocation(
        read_json(root.parent / "research" / "runtime_evidence" / "CAMPAIGN_TURNS_4_7_REPROCESS_v0.1J.json"),
        campaign,
        campaign_challenge_envelope,
        strategic_portfolio_envelope,
    )
    result = {
        "campaign_challenge": campaign_challenge_envelope,
        "campaign_challenge_matrix": run_campaign_challenge_matrix(
            read_json(root / "scenarios" / "campaign_challenge_adversarial_matrix_v0.2E.json")
        ),
        "strategic_portfolio": strategic_portfolio_envelope,
        "strategic_portfolio_matrix": run_strategic_portfolio_matrix(
            read_json(root / "scenarios" / "campaign_strategic_theater_portfolio_adversarial_matrix_v0.2F.json")
        ),
        "strategic_force_allocation": strategic_force_allocation,
        "strategic_assignment_commitment_matrix": run_strategic_assignment_commitment_matrix(
            read_json(root / "scenarios" / "campaign_theater_assignment_commitment_adversarial_matrix_v0.2G.json")
        ),
        "strategic_feasibility": build_cross_evidence_campaign_strategic_feasibility(
            read_json(root.parent / "research" / "runtime_evidence" / "CAMPAIGN_TURNS_4_7_REPROCESS_v0.1J.json"),
            strategic_force_allocation,
        ),
        "strategic_feasibility_matrix": run_strategic_feasibility_matrix(
            read_json(root / "scenarios" / "campaign_strategic_feasibility_adversarial_matrix_v0.2H.json")
        ),
        "tier1": assign_objectives(campaign, profile),
        "tier2": run_campaign(campaign, profile, turns=8, seed=101),
        "tier3": run_ensemble(campaign, profile, turns=8, seeds=[101, 102, 103, 104, 105]),
        "tier4": run_battle(battle, seed=101),
        "tier4r": derive_reality_regressions(observed),
        "tier4r_dense": derive_reality_regressions(observed_dense),
        "tier4r_trace": derive_tactical_trace_benchmarks(observed_dense, trace_slices),
        "tier4r_shadow": run_trace_shadow_evaluator(trace_slices, observed_dense),
        "tier4r_adversary": run_tactical_adversarial_suite(
            trace_slices,
            read_json(root / "scenarios" / "tactical_contract_adversarial_suite_v0.1N.json"),
        ),
        "tier4r_assignment": build_trace_objective_assignments(trace_slices),
        "assignment_matrix": run_tactical_assignment_matrix(
            trace_slices,
            read_json(root / "scenarios" / "tactical_baseline_matrix_v0.1O.json"),
            read_json(root / "scenarios" / "tactical_assignment_matrix_v0.1P.json"),
        ),
        "tier4r_schedule": build_trace_tactical_temporal_schedule(trace_slices),
        "schedule_matrix": run_tactical_schedule_matrix(
            trace_slices,
            read_json(root / "scenarios" / "tactical_baseline_matrix_v0.1O.json"),
            read_json(root / "scenarios" / "tactical_schedule_matrix_v0.1Q.json"),
        ),
        "action_authority_matrix": build_action_authority_matrix(
            read_json(root / "scenarios" / "action_authority_matrix_v0.1R.json")
        ),
        "battle4_action_authority": build_battle4_authority_boundary_report(
            observed_dense,
            read_json(root.parent / "research" / "runtime_evidence" / "BATTLE4_EILHART_TACTICAL_TEMPORAL_SCHEDULE_v0.1Q.json"),
        ),
        "tier4r_feasibility": build_trace_tactical_feasibility_envelope(
            trace_slices,
            capability_profile=build_live_feasibility_capability_profile(
                read_json(root.parent / "research" / "runtime_evidence" / "ACTION_AUTHORITY_LIVE_CAPTURE_ADJUDICATION_v0.1S.json")
            ),
        ),
        "feasibility_matrix": run_tactical_feasibility_matrix(
            trace_slices,
            read_json(root / "scenarios" / "tactical_baseline_matrix_v0.1O.json"),
            read_json(root / "scenarios" / "tactical_feasibility_matrix_v0.1T.json"),
        ),
        "tier4r_guarded": build_trace_guarded_action_packets(
            trace_slices,
            capability_profile=read_json(root.parent / "research" / "runtime_evidence" / "ACTION_FEASIBILITY_SEMANTIC_CAPABILITY_PROFILE_v0.1U.json"),
        ),
        "guarded_matrix": run_tactical_guarded_matrix(
            trace_slices,
            read_json(root / "scenarios" / "tactical_baseline_matrix_v0.1O.json"),
            read_json(root / "scenarios" / "tactical_feasibility_matrix_v0.1T.json"),
            read_json(root / "scenarios" / "tactical_guarded_action_matrix_v0.1V.json"),
        ),
        "tier4r_reservations": build_trace_endpoint_reservations(
            trace_slices,
            capability_profile=read_json(root.parent / "research" / "runtime_evidence" / "ACTION_FEASIBILITY_SEMANTIC_CAPABILITY_PROFILE_v0.1U.json"),
        ),
        "reservation_matrix": run_tactical_reservation_matrix(
            read_json(root / "scenarios" / "tactical_endpoint_reservation_matrix_v0.1W.json")
        ),
        "sfo_dual_replay_calibration": build_dual_replay_calibration(
            read_json(root / "corpora" / "sfo_reikland_dual_replay_visual_alignment_v0.2A.json"),
            {
                "ubersreik": read_json(root / "corpora" / "sfo_ubersreik_observed_dense_v0.2A.json"),
                "marienburg": read_json(root / "corpora" / "sfo_marienburg_observed_dense_v0.2A.json"),
            },
        ),
        "sfo_chaos_defeat_preparation": build_chaos_defeat_capture_readiness(
            read_json(root / "corpora" / "sfo_chaos_defeat_visual_preparation_v0.2B.json")
        ),
        "sfo_chaos_replay_adjudication": build_chaos_replay_divergence_calibration(
            read_json(root.parent / "runtime_probe" / "fixtures" / "sfo_chaos_replay_stream_capture_v0.2C.json"),
            read_json(root / "corpora" / "sfo_chaos_replay_stream_observed_dense_v0.2C.json"),
            read_json(root.parent / "runtime_probe" / "fixtures" / "sfo_chaos_replay_unit_findings_v0.2C.json"),
        ),
        "pipeline_audit": run_tactical_pipeline_audit(
            trace_slices,
            read_json(root / "scenarios" / "tactical_baseline_matrix_v0.1O.json"),
            read_json(root / "scenarios" / "tactical_feasibility_matrix_v0.1T.json"),
            read_json(root / "scenarios" / "tactical_pipeline_adversarial_scaling_v0.1X.json"),
        ),
        "cross_corpus_policy": cross_corpus_policy,
        "policy_matrix": run_tactical_policy_matrix(
            cross_corpus_policy,
            read_json(root / "scenarios" / "tactical_policy_adversarial_matrix_v0.2D.json"),
        ),
    }
    _emit(result, args.output)


def command_native_behavior(args: argparse.Namespace) -> None:
    _emit(analyze_native_behavior_trace(read_json(args.trace)), args.output)


def command_native_behavior_matrix(args: argparse.Namespace) -> None:
    _emit(run_native_behavior_adversarial_matrix(read_json(args.suite)), args.output)


def command_test(args: argparse.Namespace) -> None:
    suite = unittest.defaultTestLoader.discover(str(_root() / "tests"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Transcendence SyntheticLab")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("scenario")
    validate.add_argument("--output")
    validate.set_defaults(func=command_validate)

    for name, handler in (("tier1", command_tier1), ("tier2", command_tier2)):
        item = sub.add_parser(name)
        item.add_argument("scenario")
        item.add_argument("--profile")
        item.add_argument("--output")
        if name == "tier2":
            item.add_argument("--turns", type=int, default=20)
            item.add_argument("--seed", type=int, default=101)
        item.set_defaults(func=handler)

    tier3 = sub.add_parser("tier3")
    tier3.add_argument("scenario")
    tier3.add_argument("--profile")
    tier3.add_argument("--turns", type=int, default=20)
    tier3.add_argument("--seeds", default="101,102,103,104,105")
    tier3.add_argument("--output")
    tier3.set_defaults(func=command_tier3)

    tier4 = sub.add_parser("tier4")
    tier4.add_argument("scenario")
    tier4.add_argument("--seed", type=int, default=101)
    tier4.add_argument("--output")
    tier4.set_defaults(func=command_tier4)

    tier4r = sub.add_parser("tier4r")
    tier4r.add_argument("corpus")
    tier4r.add_argument("--output")
    tier4r.set_defaults(func=command_tier4r)

    tier4r_trace = sub.add_parser("tier4r-trace")
    tier4r_trace.add_argument("corpus")
    tier4r_trace.add_argument("trace_slices")
    tier4r_trace.add_argument("--output")
    tier4r_trace.set_defaults(func=command_tier4r_trace)

    tier4r_shadow = sub.add_parser("tier4r-shadow")
    tier4r_shadow.add_argument("trace_slices")
    tier4r_shadow.add_argument("--dense-corpus")
    tier4r_shadow.add_argument("--output")
    tier4r_shadow.set_defaults(func=command_tier4r_shadow)

    tier4r_adversary = sub.add_parser("tier4r-adversary")
    tier4r_adversary.add_argument("trace_slices")
    tier4r_adversary.add_argument("suite")
    tier4r_adversary.add_argument("--output")
    tier4r_adversary.set_defaults(func=command_tier4r_adversary)

    tier4r_assignment = sub.add_parser("tier4r-assignment")
    tier4r_assignment.add_argument("trace_slices")
    tier4r_assignment.add_argument("--output")
    tier4r_assignment.set_defaults(func=command_tier4r_assignment)

    assignment_matrix = sub.add_parser("assignment-matrix")
    assignment_matrix.add_argument("trace_slices")
    assignment_matrix.add_argument("baseline_suite")
    assignment_matrix.add_argument("assignment_suite")
    assignment_matrix.add_argument("--output")
    assignment_matrix.set_defaults(func=command_assignment_matrix)

    tier4r_schedule = sub.add_parser("tier4r-schedule")
    tier4r_schedule.add_argument("trace_slices")
    tier4r_schedule.add_argument("--output")
    tier4r_schedule.set_defaults(func=command_tier4r_schedule)

    schedule_matrix = sub.add_parser("schedule-matrix")
    schedule_matrix.add_argument("trace_slices")
    schedule_matrix.add_argument("baseline_suite")
    schedule_matrix.add_argument("schedule_suite")
    schedule_matrix.add_argument("--output")
    schedule_matrix.set_defaults(func=command_schedule_matrix)

    authority_matrix = sub.add_parser("action-authority-matrix")
    authority_matrix.add_argument("suite")
    authority_matrix.add_argument("--output")
    authority_matrix.set_defaults(func=command_action_authority_matrix)

    battle4_authority = sub.add_parser("battle4-action-authority")
    battle4_authority.add_argument("dense_corpus")
    battle4_authority.add_argument("temporal_schedule")
    battle4_authority.add_argument("--output")
    battle4_authority.set_defaults(func=command_battle4_action_authority)


    tier4r_feasibility = sub.add_parser("tier4r-feasibility")
    tier4r_feasibility.add_argument("trace_slices")
    tier4r_feasibility.add_argument("--live-adjudication")
    tier4r_feasibility.add_argument("--output")
    tier4r_feasibility.set_defaults(func=command_tier4r_feasibility)

    feasibility_matrix = sub.add_parser("feasibility-matrix")
    feasibility_matrix.add_argument("trace_slices")
    feasibility_matrix.add_argument("baseline_suite")
    feasibility_matrix.add_argument("feasibility_suite")
    feasibility_matrix.add_argument("--output")
    feasibility_matrix.set_defaults(func=command_feasibility_matrix)

    tier4r_guarded = sub.add_parser("tier4r-guarded")
    tier4r_guarded.add_argument("trace_slices")
    tier4r_guarded.add_argument("--semantic-capability-profile")
    tier4r_guarded.add_argument("--output")
    tier4r_guarded.set_defaults(func=command_tier4r_guarded)

    guarded_matrix = sub.add_parser("guarded-matrix")
    guarded_matrix.add_argument("trace_slices")
    guarded_matrix.add_argument("baseline_suite")
    guarded_matrix.add_argument("feasibility_suite")
    guarded_matrix.add_argument("guarded_suite")
    guarded_matrix.add_argument("--output")
    guarded_matrix.set_defaults(func=command_guarded_matrix)

    tier4r_reservations = sub.add_parser("tier4r-reservations")
    tier4r_reservations.add_argument("trace_slices")
    tier4r_reservations.add_argument("--semantic-capability-profile")
    tier4r_reservations.add_argument("--output")
    tier4r_reservations.set_defaults(func=command_tier4r_reservations)

    reservation_matrix = sub.add_parser("reservation-matrix")
    reservation_matrix.add_argument("suite")
    reservation_matrix.add_argument("--output")
    reservation_matrix.set_defaults(func=command_reservation_matrix)

    pipeline_audit = sub.add_parser("pipeline-audit")
    pipeline_audit.add_argument("trace_slices")
    pipeline_audit.add_argument("baseline_suite")
    pipeline_audit.add_argument("feasibility_suite")
    pipeline_audit.add_argument("audit_suite")
    pipeline_audit.add_argument("--output")
    pipeline_audit.set_defaults(func=command_pipeline_audit)


    dual_replay = sub.add_parser("sfo-dual-replay-calibration")
    dual_replay.add_argument("visual_alignment")
    dual_replay.add_argument("ubersreik_dense")
    dual_replay.add_argument("marienburg_dense")
    dual_replay.add_argument("--output")
    dual_replay.set_defaults(func=command_sfo_dual_replay_calibration)

    chaos_defeat = sub.add_parser("sfo-chaos-defeat-preparation")
    chaos_defeat.add_argument("visual_preparation")
    chaos_defeat.add_argument("--output")
    chaos_defeat.set_defaults(func=command_sfo_chaos_defeat_preparation)

    chaos_replay = sub.add_parser("sfo-chaos-replay-adjudication")
    chaos_replay.add_argument("capture")
    chaos_replay.add_argument("dense_corpus")
    chaos_replay.add_argument("unit_findings")
    chaos_replay.add_argument("--output")
    chaos_replay.set_defaults(func=command_sfo_chaos_replay_adjudication)

    cross_policy = sub.add_parser("cross-corpus-policy")
    cross_policy.add_argument("eilhart_dense")
    cross_policy.add_argument("ubersreik_dense")
    cross_policy.add_argument("marienburg_dense")
    cross_policy.add_argument("chaos_dense")
    cross_policy.add_argument("dual_replay_calibration")
    cross_policy.add_argument("chaos_replay_calibration")
    cross_policy.add_argument("--output")
    cross_policy.set_defaults(func=command_cross_corpus_policy)

    policy_matrix = sub.add_parser("policy-matrix")
    policy_matrix.add_argument("policy")
    policy_matrix.add_argument("suite")
    policy_matrix.add_argument("--output")
    policy_matrix.set_defaults(func=command_policy_matrix)

    campaign_challenge = sub.add_parser("campaign-challenge")
    campaign_challenge.add_argument("scenario")
    campaign_challenge.add_argument("--observed-report")
    campaign_challenge.add_argument("--output")
    campaign_challenge.set_defaults(func=command_campaign_challenge)

    campaign_challenge_matrix = sub.add_parser("campaign-challenge-matrix")
    campaign_challenge_matrix.add_argument("suite")
    campaign_challenge_matrix.add_argument("--output")
    campaign_challenge_matrix.set_defaults(func=command_campaign_challenge_matrix)

    strategic_portfolio = sub.add_parser("strategic-portfolio")
    strategic_portfolio.add_argument("scenario")
    strategic_portfolio.add_argument("--observed-report")
    strategic_portfolio.add_argument("--challenge-envelope")
    strategic_portfolio.add_argument("--output")
    strategic_portfolio.set_defaults(func=command_strategic_portfolio)

    strategic_portfolio_matrix = sub.add_parser("strategic-portfolio-matrix")
    strategic_portfolio_matrix.add_argument("suite")
    strategic_portfolio_matrix.add_argument("--output")
    strategic_portfolio_matrix.set_defaults(func=command_strategic_portfolio_matrix)

    strategic_assignment = sub.add_parser("strategic-assignment")
    strategic_assignment.add_argument("scenario")
    strategic_assignment.add_argument("--challenge-envelope")
    strategic_assignment.add_argument("--strategic-portfolio")
    strategic_assignment.add_argument("--output")
    strategic_assignment.set_defaults(func=command_strategic_assignment)

    strategic_commitment = sub.add_parser("strategic-commitment")
    strategic_commitment.add_argument("sequence")
    strategic_commitment.add_argument("--output")
    strategic_commitment.set_defaults(func=command_strategic_commitment)

    strategic_force_allocation = sub.add_parser("strategic-force-allocation")
    strategic_force_allocation.add_argument("observed_report")
    strategic_force_allocation.add_argument("late_game_scenario")
    strategic_force_allocation.add_argument("challenge_envelope")
    strategic_force_allocation.add_argument("strategic_portfolio")
    strategic_force_allocation.add_argument("--output")
    strategic_force_allocation.set_defaults(func=command_strategic_force_allocation)

    strategic_assignment_matrix = sub.add_parser("strategic-assignment-matrix")
    strategic_assignment_matrix.add_argument("suite")
    strategic_assignment_matrix.add_argument("--output")
    strategic_assignment_matrix.set_defaults(func=command_strategic_assignment_matrix)

    strategic_feasibility = sub.add_parser("strategic-feasibility")
    strategic_feasibility.add_argument("observed_report")
    strategic_feasibility.add_argument("force_allocation")
    strategic_feasibility.add_argument("--output")
    strategic_feasibility.set_defaults(func=command_strategic_feasibility)

    strategic_feasibility_matrix = sub.add_parser("strategic-feasibility-matrix")
    strategic_feasibility_matrix.add_argument("suite")
    strategic_feasibility_matrix.add_argument("--output")
    strategic_feasibility_matrix.set_defaults(func=command_strategic_feasibility_matrix)

    native_behavior = sub.add_parser("native-behavior")
    native_behavior.add_argument("trace")
    native_behavior.add_argument("--output")
    native_behavior.set_defaults(func=command_native_behavior)

    native_behavior_matrix = sub.add_parser("native-behavior-matrix")
    native_behavior_matrix.add_argument("suite")
    native_behavior_matrix.add_argument("--output")
    native_behavior_matrix.set_defaults(func=command_native_behavior_matrix)

    audit = sub.add_parser("audit-mods")
    audit.add_argument("--pack", action="append", default=[], help="source_id=path")
    audit.add_argument("--extracted-zip", action="append", default=[], help="source_id=path")
    audit.add_argument("--output-dir", required=True)
    audit.set_defaults(func=command_audit)

    smoke = sub.add_parser("smoke")
    smoke.add_argument("--output")
    smoke.set_defaults(func=command_smoke)

    test = sub.add_parser("test")
    test.set_defaults(func=command_test)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

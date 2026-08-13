from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from parse_battle_log import (
    BattleEvent,
    BattleLogError,
    canonical_json,
    parse_battle_logs,
    stable_unit_id,
    validate_battle_events,
)


def _bool(value: str | None) -> bool:
    return value == "true"


def _float(value: str | None, default: float = -1.0) -> float:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _int(value: str | None, default: int = -1) -> int:
    try:
        return int(float(value)) if value is not None else default
    except (TypeError, ValueError):
        return default


def _round(value: float | None, digits: int = 6) -> float | None:
    return None if value is None else round(value, digits)


def _canonical_target_id(value: str | None) -> str:
    if not value or value in {"none", "hidden", "null"}:
        return value or "none"
    if ":u" in value and value.count(":") == 1:
        return value
    parts = value.split(":")
    if len(parts) >= 2 and parts[-1] not in {"?", "", "-1"}:
        return f"{parts[0]}:u{parts[-1]}"
    return value


def _role(unit_class: str, unit_type: str, is_commander: bool) -> str:
    if is_commander or unit_class == "com":
        return "commander"
    if unit_class.startswith("art"):
        return "artillery"
    if unit_class.startswith("cav"):
        return "cavalry"
    if unit_class in {"inf_mis", "inf_ranged"}:
        return "ranged"
    if unit_class.startswith("inf"):
        return "frontline"
    if "engineer" in unit_type or "wizard" in unit_type:
        return "specialist"
    return "other"


def _median(values: list[int]) -> float | None:
    return float(statistics.median(values)) if values else None


def _percentile(values: list[int], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _distance(first: dict[str, str], second: dict[str, str], prefix: str = "position") -> float | None:
    ax = _float(first.get(f"{prefix}_x"), math.nan)
    az = _float(first.get(f"{prefix}_z"), math.nan)
    bx = _float(second.get(f"{prefix}_x"), math.nan)
    bz = _float(second.get(f"{prefix}_z"), math.nan)
    if any(math.isnan(value) for value in (ax, az, bx, bz)):
        return None
    return math.hypot(bx - ax, bz - az)




def _path_distance(samples: list[dict[str, str]], prefix: str = "position") -> float | None:
    if len(samples) < 2:
        return 0.0 if samples else None
    total = 0.0
    observed = False
    for first, second in zip(samples, samples[1:]):
        value = _distance(first, second, prefix)
        if value is not None:
            total += value
            observed = True
    return total if observed else None


def _duration_profile(samples: list[dict[str, str]], end_time_ms: int) -> dict[str, object]:
    """Integrate boolean state over sampled intervals. Valid only for dense sampling."""
    ordered = sorted(samples, key=lambda item: _int(item.get("time_ms")))
    flags = (
        "moving", "moving_fast", "idle", "in_melee", "under_missile_attack",
        "wavering", "routing", "shattered", "rampaging",
        "left_flank_threatened", "right_flank_threatened", "rear_flank_threatened",
    )
    durations = {flag: 0 for flag in flags}
    fatigue = Counter()
    target_switches = 0
    prior_target: str | None = None
    total_ms = 0
    for index, sample in enumerate(ordered):
        start = _int(sample.get("time_ms"))
        stop = (
            _int(ordered[index + 1].get("time_ms"))
            if index + 1 < len(ordered)
            else end_time_ms
        )
        interval = max(0, stop - start)
        total_ms += interval
        for flag in flags:
            if _bool(sample.get(flag)):
                durations[flag] += interval
        fatigue[sample.get("fatigue", "unknown")] += interval
        target = _canonical_target_id(sample.get("current_target_id"))
        if target not in {"none", "hidden", "null", ""}:
            if prior_target is not None and target != prior_target:
                target_switches += 1
            prior_target = target
    return {
        "observed_duration_ms": total_ms,
        "state_duration_ms": dict(sorted(durations.items())),
        "state_duration_ratio": {
            key: _round(value / total_ms) if total_ms else None
            for key, value in sorted(durations.items())
        },
        "fatigue_duration_ms": dict(sorted(fatigue.items())),
        "target_switch_count": target_switches,
    }


def _nearest_state(samples: list[dict[str, str]], time_ms: int, before: bool) -> dict[str, str] | None:
    eligible = [
        sample for sample in samples
        if (_int(sample.get("time_ms")) <= time_ms if before else _int(sample.get("time_ms")) >= time_ms)
    ]
    if not eligible:
        return None
    return max(eligible, key=lambda item: _int(item.get("time_ms"))) if before else min(eligible, key=lambda item: _int(item.get("time_ms")))


def _infer_command_units(
    commands: list[BattleEvent],
    states: dict[str, list[dict[str, str]]],
    static: dict[str, dict[str, Any]],
    *,
    enabled: bool,
    window_ms: int = 4500,
) -> dict[str, object]:
    """Bounded heuristic attribution. Never promoted as an observed acknowledgement."""
    if not enabled:
        return {
            "status": "WITHHELD_SPARSE_SAMPLING",
            "window_ms": window_ms,
            "inferred_command_count": 0,
            "high_confidence_count": 0,
            "records": [],
        }
    records: list[dict[str, object]] = []
    high = 0
    for event in commands:
        if event.fields.get("selected_unit_ids", "").strip():
            continue
        command = event.fields.get("command", "unknown")
        command_time = _int(event.fields.get("time_ms"))
        target = _canonical_target_id(event.fields.get("target_unit_id"))
        destination = {
            "position_x": event.fields.get("position_x", "-1"),
            "position_z": event.fields.get("position_z", "-1"),
        }
        candidates: list[dict[str, object]] = []
        for unit_id, unit_samples in states.items():
            info = static.get(unit_id, {}).get("fields", {})
            if not _bool(info.get("local_alliance")):
                continue
            before = _nearest_state(unit_samples, command_time, True)
            after = _nearest_state(unit_samples, command_time, False)
            if before is None or after is None:
                continue
            if command_time - _int(before.get("time_ms")) > window_ms or _int(after.get("time_ms")) - command_time > window_ms:
                continue
            score = 0.0
            reasons: list[str] = []
            if command == "Attack Unit" and target not in {"none", "hidden", "null", ""}:
                after_target = _canonical_target_id(after.get("current_target_id"))
                if after_target == target:
                    score += 1.0
                    reasons.append("post_sample_target_matches")
            if command.startswith("Move"):
                bx = _float(before.get("ordered_position_x"), math.nan)
                bz = _float(before.get("ordered_position_z"), math.nan)
                ax = _float(after.get("ordered_position_x"), math.nan)
                az = _float(after.get("ordered_position_z"), math.nan)
                dx = _float(destination.get("position_x"), math.nan)
                dz = _float(destination.get("position_z"), math.nan)
                if not any(math.isnan(v) for v in (bx, bz, ax, az, dx, dz)):
                    changed = math.hypot(ax - bx, az - bz)
                    destination_error = math.hypot(ax - dx, az - dz)
                    if changed >= 2.0:
                        score += min(0.6, changed / 100.0)
                        reasons.append("ordered_position_changed")
                    if destination_error <= 25.0:
                        score += 0.6
                        reasons.append("ordered_position_near_command")
            if command == "Special Ability":
                ability = event.fields.get("string1", "")
                owned = info.get("owned_non_passive_abilities", "")
                if ability and ability in owned:
                    score += 0.8
                    reasons.append("unit_owns_ability")
            if score > 0:
                candidates.append({
                    "stable_unit_id": unit_id,
                    "unit_type": info.get("unit_type", "unknown"),
                    "score": _round(score, 3),
                    "reasons": reasons,
                })
        candidates.sort(key=lambda item: (-float(item["score"] or 0), str(item["stable_unit_id"])))
        confidence = "NONE"
        if candidates:
            best = float(candidates[0]["score"] or 0)
            runner_up = float(candidates[1]["score"] or 0) if len(candidates) > 1 else 0.0
            if best >= 0.9 and best - runner_up >= 0.25:
                confidence = "HIGH"
                high += 1
            elif best >= 0.6:
                confidence = "MEDIUM"
            else:
                confidence = "LOW"
        if candidates:
            records.append({
                "command_index": _int(event.fields.get("command_index")),
                "time_ms": command_time,
                "command": command,
                "target_unit_id": target,
                "confidence": confidence,
                "candidates": candidates[:5],
            })
    return {
        "status": "INFERRED_NOT_ACKNOWLEDGED",
        "window_ms": window_ms,
        "inferred_command_count": len(records),
        "high_confidence_count": high,
        "records": records,
    }


def _merge_static(
    static_events: list[BattleEvent],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, object]]]:
    units: dict[str, dict[str, Any]] = {}
    conflicts: list[dict[str, object]] = []
    identity_fields = (
        "alliance_index",
        "local_alliance",
        "unit_type",
        "unit_class",
        "initial_men",
        "starting_ammo",
    )
    for event in static_events:
        key = stable_unit_id(event.fields)
        existing = units.get(key)
        if existing is None:
            units[key] = {
                "stable_unit_id": key,
                "fields": dict(event.fields),
                "raw_unit_ids": [event.fields["unit_id"]],
                "first_seen_time_ms": _int(event.fields.get("time_ms")),
                "last_static_time_ms": _int(event.fields.get("time_ms")),
            }
            continue
        existing["raw_unit_ids"].append(event.fields["unit_id"])
        existing["last_static_time_ms"] = max(
            int(existing["last_static_time_ms"]), _int(event.fields.get("time_ms"))
        )
        for field in identity_fields:
            prior = existing["fields"].get(field)
            current = event.fields.get(field)
            if prior not in {None, "", "unknown", "-1"} and current not in {
                None,
                "",
                "unknown",
                "-1",
            } and prior != current:
                conflicts.append(
                    {
                        "stable_unit_id": key,
                        "field": field,
                        "first": prior,
                        "later": current,
                        "source_line": event.line_number,
                    }
                )
        # Prefer richer later values only when the original was unavailable.
        for field, value in event.fields.items():
            if existing["fields"].get(field) in {None, "", "unknown", "-1"}:
                existing["fields"][field] = value
    for item in units.values():
        item["raw_unit_ids"] = sorted(set(item["raw_unit_ids"]))
    return units, conflicts


def _sampling_analysis(
    events: list[BattleEvent], duration_ms: int, declared_detail_ms: int
) -> dict[str, object]:
    begins = [event for event in events if event.event == "SAMPLE_BEGIN"]
    samples = [
        {
            "sample_index": _int(event.fields.get("sample_index")),
            "time_ms": _int(event.fields.get("time_ms")),
            "reason": event.fields.get("reason", "unknown"),
            "scheduler_source": event.fields.get("scheduler_source", "unknown"),
        }
        for event in begins
    ]
    unique_times = sorted({item["time_ms"] for item in samples if item["time_ms"] >= 0})
    gaps = [right - left for left, right in zip(unique_times, unique_times[1:])]
    interval_samples = [
        item
        for item in samples
        if item["reason"].startswith("INTERVAL")
        or item["reason"].startswith("TIMER")
    ]
    expected = (
        max(1, math.floor(max(0, duration_ms) / declared_detail_ms) + 1)
        if declared_detail_ms > 0 and duration_ms >= 0
        else None
    )
    coverage = len(unique_times) / expected if expected else None
    max_gap = max(gaps) if gaps else None
    dense = bool(
        expected
        and len(interval_samples) >= max(2, math.floor(expected * 0.5))
        and max_gap is not None
        and max_gap <= declared_detail_ms * 3
    )
    if dense:
        quality = "DENSE_INTERVAL_COVERAGE"
    elif interval_samples:
        quality = "PARTIAL_INTERVAL_COVERAGE"
    else:
        quality = "SPARSE_PHASE_ONLY"
    return {
        "declared_detail_interval_ms": declared_detail_ms,
        "expected_detail_samples": expected,
        "observed_detail_samples": len(samples),
        "observed_interval_samples": len(interval_samples),
        "unique_sample_times": unique_times,
        "coverage_ratio": _round(coverage),
        "maximum_sample_gap_ms": max_gap,
        "quality": quality,
        "time_series_metrics_valid": dense,
        "samples": samples,
    }


def _command_analysis(
    commands: list[BattleEvent], static: dict[str, dict[str, Any]], duration_ms: int
) -> dict[str, object]:
    command_counts = Counter(event.fields.get("command", "unknown") for event in commands)
    times = sorted(_int(event.fields.get("time_ms")) for event in commands)
    intervals = [right - left for left, right in zip(times, times[1:]) if right >= left]
    selected_count = sum(
        1 for event in commands if event.fields.get("selected_unit_ids", "").strip()
    )
    target_counts: Counter[str] = Counter()
    ability_counts: Counter[str] = Counter()
    ability_timeline: list[dict[str, object]] = []
    buckets: dict[int, Counter[str]] = defaultdict(Counter)
    for event in commands:
        command = event.fields.get("command", "unknown")
        time_ms = _int(event.fields.get("time_ms"))
        bucket = max(0, time_ms // 30000)
        buckets[bucket][command] += 1
        target = _canonical_target_id(event.fields.get("target_unit_id"))
        if target not in {"none", "hidden", "null", ""}:
            target_counts[target] += 1
        if command == "Special Ability":
            ability = event.fields.get("string1", "unknown")
            ability_counts[ability] += 1
            ability_timeline.append({"time_ms": time_ms, "ability": ability})

    target_details = []
    for target, count in target_counts.most_common():
        info = static.get(target, {}).get("fields", {})
        target_details.append(
            {
                "stable_unit_id": target,
                "unit_type": info.get("unit_type", "unknown"),
                "unit_class": info.get("unit_class", "unknown"),
                "command_count": count,
            }
        )
    attack_target_total = sum(target_counts.values())
    top_share = (
        target_details[0]["command_count"] / attack_target_total
        if target_details and attack_target_total
        else None
    )
    burst_intervals = [value for value in intervals if value <= 500]
    command_buckets = [
        {
            "start_ms": bucket * 30000,
            "end_ms": min(duration_ms, (bucket + 1) * 30000),
            "total": sum(counts.values()),
            "counts": dict(sorted(counts.items())),
        }
        for bucket, counts in sorted(buckets.items())
    ]
    return {
        "command_event_count": len(commands),
        "command_counts": dict(sorted(command_counts.items())),
        "selection_attributed_command_count": selected_count,
        "selection_attribution_ratio": _round(selected_count / len(commands)) if commands else None,
        "mean_command_interval_ms": _round(sum(intervals) / len(intervals), 3) if intervals else None,
        "median_command_interval_ms": _round(_median(intervals), 3),
        "p90_command_interval_ms": _round(_percentile(intervals, 0.9), 3),
        "sub_500ms_interval_count": len(burst_intervals),
        "targeted_command_count": attack_target_total,
        "top_target_share": _round(top_share),
        "targets": target_details,
        "special_ability_counts": dict(sorted(ability_counts.items())),
        "special_ability_timeline": ability_timeline,
        "thirty_second_buckets": command_buckets,
    }


def build_battle_report(events: list[BattleEvent]) -> dict[str, object]:
    sessions = validate_battle_events(events)
    battle_reports: list[dict[str, object]] = []

    for battle_index, session in enumerate(sessions, 1):
        session_events: list[BattleEvent] = session["events"]
        static_events = [event for event in session_events if event.event == "UNIT_STATIC"]
        static, identity_conflicts = _merge_static(static_events)
        states: dict[str, list[dict[str, str]]] = defaultdict(list)
        aggregates: dict[int, list[dict[str, str]]] = defaultdict(list)
        commands: list[BattleEvent] = []
        phases: list[dict[str, object]] = []
        selections = 0
        sample_ends: list[dict[str, object]] = []
        heartbeats: list[dict[str, object]] = []

        for event in session_events:
            if event.event == "UNIT_STATE":
                states[stable_unit_id(event.fields)].append(event.fields)
            elif event.event == "ALLIANCE_AGGREGATE":
                aggregates[_int(event.fields.get("alliance_index"))].append(event.fields)
            elif event.event == "COMMAND":
                commands.append(event)
            elif event.event == "PHASE":
                phases.append(
                    {
                        "phase": event.fields.get("phase", "unknown"),
                        "time_ms": _int(event.fields.get("time_ms")),
                    }
                )
            elif event.event == "SELECTION":
                selections += 1
            elif event.event == "SAMPLE_END":
                sample_ends.append(
                    {
                        key: (_int(value) if key in {
                            "time_ms", "sample_index", "observed_units", "hidden_enemy_units", "total_units_seen_by_hierarchy"
                        } else value)
                        for key, value in event.fields.items()
                    }
                )
            elif event.event == "SAMPLER_HEARTBEAT":
                heartbeats.append(
                    {
                        key: (_int(value) if key.endswith("_count") or key.endswith("_ms") else value)
                        for key, value in event.fields.items()
                    }
                )

        start: BattleEvent | None = session.get("battle_start")
        complete: BattleEvent | None = session.get("battle_complete")
        pack_loaded = next(
            (event for event in session_events if event.event == "PACK_LOADED"), None
        )
        duration_ms = _int(complete.fields.get("time_ms")) if complete else max(
            (_int(event.fields.get("time_ms")) for event in session_events), default=-1
        )
        declared_detail_ms = _int(
            (pack_loaded.fields.get("sample_interval_ms") if pack_loaded else None), 3000
        )
        sampling = _sampling_analysis(session_events, duration_ms, declared_detail_ms)
        time_series_valid = bool(sampling["time_series_metrics_valid"])

        unit_metrics: list[dict[str, object]] = []
        first_engagement_times: list[int] = []
        complete_time = duration_ms
        for unit_id in sorted(states):
            samples = sorted(states[unit_id], key=lambda item: _int(item.get("time_ms")))
            first = samples[0]
            last = samples[-1]
            sample_count = len(samples)
            info = static.get(unit_id, {"fields": {}, "raw_unit_ids": []})
            fields = info["fields"]
            engaged = [sample for sample in samples if _bool(sample.get("in_melee"))]
            under_fire = [sample for sample in samples if _bool(sample.get("under_missile_attack"))]
            idle = [sample for sample in samples if _bool(sample.get("idle"))]
            flank = [
                sample
                for sample in samples
                if any(
                    _bool(sample.get(key))
                    for key in (
                        "left_flank_threatened",
                        "right_flank_threatened",
                        "rear_flank_threatened",
                    )
                )
            ]
            routing = [sample for sample in samples if _bool(sample.get("routing"))]
            starting_ammo = _int(fields.get("starting_ammo"))
            first_engagement = min(
                (
                    _int(sample.get("time_ms"))
                    for sample in samples
                    if _bool(sample.get("in_melee"))
                    or _int(sample.get("kills"), 0) > 0
                    or (
                        starting_ammo >= 0
                        and _int(sample.get("ammo"), starting_ammo) < starting_ammo
                    )
                ),
                default=-1,
            )
            if first_engagement >= 0:
                first_engagement_times.append(first_engagement)

            initial_men = _int(fields.get("initial_men"))
            min_men = min((_int(sample.get("men_alive")) for sample in samples), default=-1)
            final_men = _int(last.get("men_alive"))
            terminal_observed = complete_time >= 0 and _int(last.get("time_ms")) == complete_time
            casualty_lower_bound = (
                max(0, initial_men - min_men)
                if initial_men >= 0 and min_men >= 0
                else None
            )
            casualty_exact = (
                max(0, initial_men - final_men)
                if terminal_observed and initial_men >= 0 and final_men >= 0
                else None
            )
            min_ammo = min((_int(sample.get("ammo")) for sample in samples), default=-1)
            unit_type = fields.get("unit_type", "unknown")
            unit_class = fields.get("unit_class", "unknown")
            is_commander = _bool(fields.get("is_commander"))
            sparse_ratios = {
                "idle_sample_ratio": round(len(idle) / sample_count, 6),
                "melee_sample_ratio": round(len(engaged) / sample_count, 6),
                "missile_pressure_sample_ratio": round(len(under_fire) / sample_count, 6),
                "flank_threat_sample_ratio": round(len(flank) / sample_count, 6),
                "routing_sample_ratio": round(len(routing) / sample_count, 6),
            }
            unit_metrics.append(
                {
                    "stable_unit_id": unit_id,
                    "raw_unit_ids": info.get("raw_unit_ids", []),
                    "identity_alias_count": max(0, len(info.get("raw_unit_ids", [])) - 1),
                    "local_alliance": _bool(last.get("local_alliance")),
                    "alliance_index": _int(last.get("alliance_index")),
                    "unit_type": unit_type,
                    "unit_class": unit_class,
                    "role": _role(unit_class, unit_type, is_commander),
                    "is_commander": is_commander,
                    "sample_count": sample_count,
                    "first_observed_time_ms": _int(first.get("time_ms")),
                    "last_observed_time_ms": _int(last.get("time_ms")),
                    "terminal_state_observed": terminal_observed,
                    "initial_men": initial_men,
                    "minimum_observed_men": min_men,
                    "last_observed_men": final_men,
                    "casualties_observed_lower_bound": casualty_lower_bound,
                    "casualties_exact_if_terminal": casualty_exact,
                    "initial_hitpoints_fraction": _float(first.get("hitpoints_fraction")),
                    "last_observed_hitpoints_fraction": _float(last.get("hitpoints_fraction")),
                    "kills_observed_max": max(
                        (_int(sample.get("kills"), 0) for sample in samples), default=0
                    ),
                    "starting_ammo": starting_ammo,
                    "minimum_observed_ammo": min_ammo,
                    "ammo_spent_observed_lower_bound": (
                        max(0, starting_ammo - min_ammo)
                        if starting_ammo >= 0 and min_ammo >= 0
                        else None
                    ),
                    "distance_travelled_observed_m": (
                        _round(_path_distance(samples), 3) if time_series_valid else None
                    ),
                    "ordered_path_change_observed_m": (
                        _round(_path_distance(samples, "ordered_position"), 3) if time_series_valid else None
                    ),
                    "time_series_metrics": (
                        {**sparse_ratios, **_duration_profile(samples, complete_time)}
                        if time_series_valid else None
                    ),
                    "sparse_sample_ratios_untrusted": (
                        None if time_series_valid else sparse_ratios
                    ),
                    "first_engagement_time_ms": (
                        first_engagement if time_series_valid else None
                    ),
                    "first_routing_time_ms": (
                        min((_int(sample.get("time_ms")) for sample in routing), default=-1)
                        if time_series_valid
                        else None
                    ),
                    "last_strategic_value_proxy": _float(last.get("strategic_value_proxy")),
                    "last_observed_flags": {
                        "moving": _bool(last.get("moving")),
                        "idle": _bool(last.get("idle")),
                        "in_melee": _bool(last.get("in_melee")),
                        "under_missile_attack": _bool(last.get("under_missile_attack")),
                        "wavering": _bool(last.get("wavering")),
                        "routing": _bool(last.get("routing")),
                        "shattered": _bool(last.get("shattered")),
                        "rampaging": _bool(last.get("rampaging")),
                        "fatigue": last.get("fatigue", "unknown"),
                    },
                    "last_position": {
                        "x": _float(last.get("position_x")),
                        "y": _float(last.get("position_y")),
                        "z": _float(last.get("position_z")),
                    },
                }
            )

        command_analysis = _command_analysis(commands, static, duration_ms)
        inferred_command_attribution = _infer_command_units(
            commands, states, static, enabled=time_series_valid
        )
        local_units = [item for item in unit_metrics if item["local_alliance"]]
        visible_enemy_units = [item for item in unit_metrics if not item["local_alliance"]]
        terminal_units = [item for item in unit_metrics if item["terminal_state_observed"]]
        local_terminal = [item for item in local_units if item["terminal_state_observed"]]
        enemy_terminal = [item for item in visible_enemy_units if item["terminal_state_observed"]]

        # Deployment displacement uses the first and Deployed-phase samples where available.
        deployed_time = next(
            (int(item["time_ms"]) for item in phases if item["phase"] == "Deployed"),
            None,
        )
        deployment_movements: list[dict[str, object]] = []
        if deployed_time is not None:
            for unit_id, unit_samples in sorted(states.items()):
                local_samples = sorted(unit_samples, key=lambda item: _int(item.get("time_ms")))
                if not local_samples or not _bool(local_samples[-1].get("local_alliance")):
                    continue
                initial = local_samples[0]
                deployed = next(
                    (sample for sample in local_samples if _int(sample.get("time_ms")) == deployed_time),
                    None,
                )
                if deployed is None:
                    continue
                info = static.get(unit_id, {}).get("fields", {})
                deployment_movements.append(
                    {
                        "stable_unit_id": unit_id,
                        "unit_type": info.get("unit_type", "unknown"),
                        "role": _role(
                            info.get("unit_class", "unknown"),
                            info.get("unit_type", "unknown"),
                            _bool(info.get("is_commander")),
                        ),
                        "displacement_m": _round(_distance(initial, deployed), 3),
                        "initial_ordered_width": _float(initial.get("ordered_width")),
                        "deployed_ordered_width": _float(deployed.get("ordered_width")),
                    }
                )

        aggregate_timeline = {
            str(alliance): [
                {
                    key: (
                        _int(value)
                        if key in {
                            "time_ms", "aggregate_index", "alliance_index", "observed_units",
                            "men_alive", "kills", "ammo", "units_in_melee",
                            "units_under_missile_attack", "units_routing", "units_wavering",
                            "units_shattered", "units_idle", "units_moving",
                            "units_flank_threatened", "hidden_enemy_units", "hierarchy_unit_total"
                        }
                        else (_float(value) if key == "strategic_value_proxy" else value)
                    )
                    for key, value in item.items()
                }
                for item in sorted(items, key=lambda value: _int(value.get("time_ms")))
            ]
            for alliance, items in sorted(aggregates.items())
        }

        identity_aliases = sum(
            max(0, len(item.get("raw_unit_ids", [])) - 1) for item in static.values()
        )
        local_casualty_lower_bound = sum(
            int(item["casualties_observed_lower_bound"] or 0) for item in local_units
        )
        enemy_casualty_lower_bound = sum(
            int(item["casualties_observed_lower_bound"] or 0)
            for item in visible_enemy_units
        )
        local_kills_max_sum = sum(int(item["kills_observed_max"]) for item in local_units)
        battle_reports.append(
            {
                "battle_index": battle_index,
                "complete": bool(session["complete"]),
                "source_schema": session["schema"],
                "metadata": dict(sorted(start.fields.items())) if start else {},
                "result": dict(sorted(complete.fields.items())) if complete else {},
                "duration_ms": duration_ms,
                "phases": phases,
                "capability_failures": sorted(set(session["capability_failures"])),
                "optional_unavailable": sorted(set(session.get("optional_unavailable", []))),
                "sampling": sampling,
                "visibility_samples": sample_ends,
                "sampler_heartbeats": heartbeats,
                "identity": {
                    "raw_unit_static_count": len(static_events),
                    "canonical_unit_count": len(static),
                    "identity_alias_count": identity_aliases,
                    "identity_conflicts": identity_conflicts,
                },
                "unit_counts": {
                    "local_canonical": len(local_units),
                    "visible_enemy_canonical": len(visible_enemy_units),
                    "terminal_observed": len(terminal_units),
                    "local_terminal_observed": len(local_terminal),
                    "visible_enemy_terminal_observed": len(enemy_terminal),
                },
                "selection_event_count": selections,
                "commands": command_analysis,
                "inferred_command_attribution": inferred_command_attribution,
                "deployment_movements": deployment_movements,
                "aggregate_timeline": aggregate_timeline,
                "outcome_metrics": {
                    "local_casualties_observed_lower_bound": local_casualty_lower_bound,
                    "visible_enemy_casualties_observed_lower_bound": enemy_casualty_lower_bound,
                    "local_kills_observed_max_sum": local_kills_max_sum,
                    "local_terminal_coverage_ratio": _round(
                        len(local_terminal) / len(local_units) if local_units else None
                    ),
                    "visible_enemy_terminal_coverage_ratio": _round(
                        len(enemy_terminal) / len(visible_enemy_units)
                        if visible_enemy_units
                        else None
                    ),
                    "exact_total_casualties_available": (
                        len(local_terminal) == len(local_units)
                        and len(enemy_terminal) == len(visible_enemy_units)
                    ),
                },
                "first_engagement_time_ms": (
                    min(first_engagement_times, default=-1)
                    if time_series_valid
                    else None
                ),
                "unit_metrics": unit_metrics,
                "aggregate_sample_counts": {
                    str(alliance): len(items) for alliance, items in sorted(aggregates.items())
                },
                "interpretation_status": {
                    "terminal_outcome": (
                        "OBSERVED" if session["complete"] else "UNVERIFIED_INCOMPLETE_SESSION"
                    ),
                    "unit_identity": "RECONCILED" if not identity_conflicts else "CONFLICT",
                    "command_timestamps": "OBSERVED",
                    "command_unit_attribution": (
                        "OBSERVED" if command_analysis["selection_attribution_ratio"] == 1.0
                        else ("INFERRED" if inferred_command_attribution["inferred_command_count"] > 0 else "UNVERIFIED")
                    ),
                    "time_series_tactics": (
                        "OBSERVED" if time_series_valid else "INVALIDATED_BY_SPARSE_SAMPLING"
                    ),
                },
            }
        )

    result: dict[str, object] = {
        "schema_version": 2,
        "mode": "BATTLE_OBSERVATION_NO_ORDERS",
        "evidence_label": (
            "HYPOTHESIS" if not all(report["complete"] for report in battle_reports) else "OBSERVED"
        ),
        "battle_count": len(battle_reports),
        "completed_battle_count": sum(1 for report in battle_reports if report["complete"]),
        "battle_reports": battle_reports,
        "authority": {
            "unitcontrollers_created": False,
            "orders_emitted": False,
            "battle_speed_modified": False,
            "save_values_written": False,
            "visibility_modified": False,
        },
        "interpretation_limits": [
            "Strategic value is an engine proxy, not a published recruitment-cost valuation.",
            "Visible-enemy metrics are incomplete whenever line of sight hides units.",
            "Casualty totals are lower bounds unless every canonical unit has a terminal observation.",
            "Time-series metrics are withheld when interval sampling coverage is inadequate.",
            "A single battle cannot establish tactical-AI quality or causal command effectiveness.",
            "Command events describe command traffic observed by WH3, not acceptance or success acknowledgements.",
        ],
    }
    result["result_digest"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a read-only WH3 battle telemetry report.")
    parser.add_argument("logs", type=Path, nargs="+")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = build_battle_report(parse_battle_logs(args.logs))
    except BattleLogError as error:
        parser.error(str(error))
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

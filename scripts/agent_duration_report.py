#!/usr/bin/env python3
"""Bounded content-free reports for validated duration-study run records."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from agent_contracts import load_json
from agent_duration_study import DurationStudyError, validate_run_record


MAX_DISCOVERED_RECORDS = 5_000
MAX_DISPLAYED_RECORDS = 500


def discover_run_paths(inputs: Iterable[Path]) -> list[Path]:
    discovered: dict[Path, None] = {}
    for raw_path in inputs:
        path = raw_path.resolve()
        if path.is_file():
            candidates = [path]
        elif path.is_dir():
            candidates = sorted(item.resolve() for item in path.glob("*.json") if item.is_file())
        else:
            raise DurationStudyError(f"run report input does not exist: {raw_path}")
        for candidate in candidates:
            discovered[candidate] = None
            if len(discovered) > MAX_DISCOVERED_RECORDS:
                raise DurationStudyError(
                    f"run report discovery exceeds the {MAX_DISCOVERED_RECORDS} record cap"
                )
    if not discovered:
        raise DurationStudyError("run report input contains no JSON records")
    return list(discovered)


def load_run_records(inputs: Iterable[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    run_ids: set[str] = set()
    for path in discover_run_paths(inputs):
        value = load_json(path)
        if not isinstance(value, dict):
            raise DurationStudyError(f"run record root must be an object: {path}")
        validate_run_record(value)
        run_id = value["run_id"]
        if run_id in run_ids:
            raise DurationStudyError(f"duplicate run ID in report inputs: {run_id}")
        run_ids.add(run_id)
        records.append(value)
    return sorted(
        records,
        key=lambda item: (
            item["landmarks"]["T0"]["wall_time"],
            item["run_id"],
        ),
    )


def _quality_population(record: dict[str, Any]) -> str:
    quality_pass = record["outcome"]["quality_pass"]
    if quality_pass is True:
        return "quality-pass"
    if quality_pass is False:
        return "quality-fail"
    return "quality-unknown"


def _reported_duration(record: dict[str, Any]) -> dict[str, Any]:
    population = _quality_population(record)
    durations = record["durations_ms"]
    if population == "quality-pass":
        if "user_result" not in durations:
            raise DurationStudyError("quality-pass run has no user-result duration")
        return {
            "role": "quality-pass-user-result",
            "milliseconds": durations["user_result"],
        }
    return {
        "role": "failed-terminal" if population == "quality-fail" else "unknown-terminal",
        "milliseconds": durations["terminal_wall"],
    }


def _evaluator_score(evaluator: dict[str, Any]) -> dict[str, Any] | None:
    score = evaluator.get("score")
    if isinstance(score, dict):
        return dict(score)
    checks = evaluator["checks"]
    if not checks:
        return None
    passed = sum(item["status"] == "pass" for item in checks)
    return {
        "resolution": "aggregate-check",
        "passed": passed,
        "total": len(checks),
        "ratio": round(passed / len(checks), 6),
        "public_passed": 0,
        "public_total": 0,
        "hidden_passed": 0,
        "hidden_total": 0,
        "failed_check_ids": [
            item["check_id"] for item in checks if item["status"] == "fail"
        ],
        "all_checks_required": True,
    }


def _sample(record: dict[str, Any]) -> dict[str, Any]:
    participant = record["participants"][0]
    runtime = participant["runtime_identity"]
    outcome = record["outcome"]
    evaluator = record["diagnostics"]["evaluator"]
    return {
        "run_id": record["run_id"],
        "block_id": record["block_id"],
        "case": {
            "case_id": record["case"]["case_id"],
            "revision": record["case"]["revision"],
            "family": record["case"]["family"],
            "size": record["case"]["size"],
            "profile_id": record["case"]["profile_id"],
        },
        "configuration": {
            "configuration_id": record["configuration"]["configuration_id"],
            "relation": record["configuration"]["relation"],
            "participants_actual": record["configuration"]["participants_actual"],
            "workers_actual": record["configuration"]["workers_actual"],
        },
        "provider": runtime["provider"],
        "model_identity": dict(participant["model_identity"]),
        "generation_settings": [dict(item) for item in participant["generation_settings"]],
        "runtime": {
            "cli_version": runtime["cli_version"],
            "execution_surface": runtime["execution_surface"],
            "image_digest": record["environment"]["image_digest"],
        },
        "observed_at": record["landmarks"]["T0"]["wall_time"],
        "durations_ms": {
            key: record["durations_ms"][key]
            for key in (
                "provision",
                "first_artifact_latency",
                "online_validation",
                "user_result",
                "terminal_wall",
                "aggregate_worker",
            )
            if key in record["durations_ms"]
        },
        "reported_duration": _reported_duration(record),
        "outcome": {
            "infrastructure": outcome["infrastructure"],
            "artifact": outcome["artifact"],
            "online_acceptance": outcome["online_acceptance"],
            "offline_score": outcome["offline_score"],
            "quality_pass": outcome["quality_pass"],
            "quality_basis": outcome["quality_basis"],
            "failure_class": outcome["failure_class"],
        },
        "quality_population": _quality_population(record),
        "quality_score": _evaluator_score(evaluator),
        "evidence_state": "single-observation",
        "coverage": {
            "first_artifact_resolution": record["coverage"]["first_artifact_resolution"],
            "synthesis_resolution": record["coverage"]["synthesis_resolution"],
            "evaluator_status": evaluator["status"],
            "evaluator_check_count": len(evaluator["checks"]),
        },
    }


def build_raw_sample_report(
    records: list[dict[str, Any]],
    *,
    case_id: str | None = None,
    provider: str | None = None,
    quality: str = "all",
    limit: int = 50,
) -> dict[str, Any]:
    if quality not in {"all", "pass", "fail", "unknown"}:
        raise DurationStudyError("run report quality filter is invalid")
    if limit < 1 or limit > MAX_DISPLAYED_RECORDS:
        raise DurationStudyError(
            f"run report limit must be between 1 and {MAX_DISPLAYED_RECORDS}"
        )
    samples = [_sample(record) for record in records]
    matched = [
        sample
        for sample in samples
        if (case_id is None or sample["case"]["case_id"] == case_id)
        and (provider is None or sample["provider"] == provider)
        and (
            quality == "all"
            or sample["quality_population"] == f"quality-{quality}"
        )
    ]
    displayed = matched[:limit]
    population_counts = {
        name: sum(sample["quality_population"] == name for sample in matched)
        for name in ("quality-pass", "quality-fail", "quality-unknown")
    }
    infrastructure_counts = {
        status: sum(sample["outcome"]["infrastructure"] == status for sample in matched)
        for status in ("success", "failure", "timeout", "cancelled", "invalid")
    }
    return {
        "schema_version": 1,
        "report_kind": "raw-sample-inventory",
        "aggregation": "none",
        "selection_rule_generated": False,
        "filters": {
            "case_id": case_id,
            "provider": provider,
            "quality": quality,
        },
        "counts": {
            "validated_records": len(records),
            "matched_records": len(matched),
            "displayed_records": len(displayed),
            "quality_population": population_counts,
            "infrastructure": infrastructure_counts,
        },
        "truncated": len(displayed) < len(matched),
        "samples": displayed,
    }


def _setting_label(sample: dict[str, Any]) -> str:
    settings = sample["generation_settings"]
    if not settings:
        return "none"
    return ",".join(
        f"{item['key']}={item['requested_value']}/{item['status']}" for item in settings
    )


def render_raw_sample_table(report: dict[str, Any]) -> str:
    headers = (
        "RUN",
        "CASE",
        "CFG",
        "PROVIDER",
        "MODEL",
        "REQUEST/STATUS",
        "DURATION",
        "ONLINE",
        "SCORE",
        "FAILED CRITERIA",
        "QUALITY",
    )
    rows: list[tuple[str, ...]] = []
    for sample in report["samples"]:
        identity = sample["model_identity"]
        model = identity.get("requested_alias", "unspecified")
        duration = sample["reported_duration"]
        score = sample["quality_score"]
        if score is None:
            score_label = "unavailable"
            failed_label = "-"
        else:
            score_label = f"{score['passed']}/{score['total']} ({score['ratio'] * 100:.1f}%)"
            if score["resolution"] == "criterion":
                score_label += f" hidden={score['hidden_passed']}/{score['hidden_total']}"
            else:
                score_label += " aggregate"
            failed_label = ",".join(score["failed_check_ids"]) or "-"
        rows.append(
            (
                sample["run_id"],
                sample["case"]["case_id"],
                sample["configuration"]["configuration_id"],
                sample["provider"],
                f"{model}/{identity['identity_confidence']}",
                _setting_label(sample),
                f"{duration['milliseconds']:.3f}ms {duration['role']}",
                sample["outcome"]["online_acceptance"],
                score_label,
                failed_label,
                sample["quality_population"],
            )
        )
    widths = [len(value) for value in headers]
    for row in rows:
        widths = [max(width, len(value)) for width, value in zip(widths, row)]

    def format_row(row: tuple[str, ...]) -> str:
        return "  ".join(value.ljust(width) for value, width in zip(row, widths)).rstrip()

    lines = [format_row(headers), format_row(tuple("-" * width for width in widths))]
    lines.extend(format_row(row) for row in rows)
    counts = report["counts"]
    populations = counts["quality_population"]
    lines.append(
        "counts: "
        f"matched={counts['matched_records']} displayed={counts['displayed_records']} "
        f"pass={populations['quality-pass']} fail={populations['quality-fail']} "
        f"unknown={populations['quality-unknown']} truncated={str(report['truncated']).lower()}"
    )
    lines.append("aggregation: none; evidence state: single-observation per row")
    return "\n".join(lines)

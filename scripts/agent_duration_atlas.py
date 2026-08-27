#!/usr/bin/env python3
"""Build a deterministic, provider-free duration atlas from validated runs.

The aggregate is observational evidence, not a router.  A complete primary
stratum is the combination of a series stratum and one nested case stratum;
case nesting preserves within-case repeats separately from between-case
variation.  This module never invokes a provider and never infers an applied
generation setting from a requested value.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import statistics
import sys
import tempfile
from typing import Any, Callable, Iterable, Mapping, Sequence

from agent_contracts import ContractValidationError, load_json, validate
from agent_duration_study import (
    DurationStudyError,
    ROOT,
    canonical_json_digest,
    validate_run_record,
)


ATLAS_SCHEMA_VERSION = 2
RUN_SCHEMA_VERSION = 2
ATLAS_SCHEMA = (
    ROOT / "experiments" / "multi-agent-duration" / "schemas" / "atlas.schema.json"
)
HARD_RECORD_LIMIT = 5_000
HARD_BYTE_LIMIT = 512 * 1024 * 1024
DEFAULT_MAX_INPUT_BYTES = 64 * 1024 * 1024
DEFAULT_MAX_OUTPUT_BYTES = 32 * 1024 * 1024
DURATION_KEYS = (
    "provision",
    "dispatch_delay",
    "first_artifact_latency",
    "required_workers_ready",
    "worker_terminal_span",
    "synthesis_tail",
    "online_validation",
    "post_validation_tail",
    "user_result",
    "terminal_wall",
    "aggregate_worker",
    "worker_active_union",
    "offline_scoring",
)
QUALITY_POPULATIONS = ("quality-pass", "quality-fail", "quality-unknown")
CENSORING_STATES = (
    "complete-terminal",
    "right-censored",
    "administratively-censored",
)
FIRST_ARTIFACT_RESOLUTIONS = (
    "progress-envelope",
    "not-observed",
    "not-applicable",
    "unknown",
)


class AtlasError(DurationStudyError):
    """Raised when atlas input or output cannot be handled safely."""


def _bounded_positive(value: int, *, label: str, upper: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > upper:
        raise AtlasError(f"{label} must be between 1 and {upper}")
    return value


def discover_run_paths(inputs: Iterable[Path], *, max_records: int) -> list[Path]:
    """Discover only direct JSON files and enforce the count cap before loading."""

    _bounded_positive(max_records, label="max-records", upper=HARD_RECORD_LIMIT)
    discovered: dict[Path, None] = {}
    for raw_path in inputs:
        path = raw_path.resolve()
        if path.is_file():
            candidates = [path]
        elif path.is_dir():
            candidates = sorted(
                candidate.resolve()
                for candidate in path.glob("*.json")
                if candidate.is_file()
            )
        else:
            raise AtlasError(f"atlas input does not exist: {raw_path}")
        for candidate in candidates:
            discovered[candidate] = None
            if len(discovered) > max_records:
                raise AtlasError("atlas input exceeds max-records before loading")
    if not discovered:
        raise AtlasError("atlas input contains no JSON run records")
    return sorted(discovered)


def load_run_records_bounded(
    inputs: Iterable[Path],
    *,
    max_records: int,
    max_input_bytes: int,
) -> tuple[list[dict[str, Any]], int]:
    """Load schema-v2 runs under explicit count and actual-byte caps."""

    _bounded_positive(max_input_bytes, label="max-input-bytes", upper=HARD_BYTE_LIMIT)
    paths = discover_run_paths(inputs, max_records=max_records)
    total_bytes = 0
    records: list[dict[str, Any]] = []
    run_ids: set[str] = set()
    for path in paths:
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise AtlasError(f"cannot read atlas input: {path}") from exc
        total_bytes += len(raw)
        if total_bytes > max_input_bytes:
            raise AtlasError("atlas input exceeds max-input-bytes while loading")
        try:
            value = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AtlasError(f"cannot decode atlas run record: {path}") from exc
        if not isinstance(value, dict):
            raise AtlasError("atlas run record root must be an object")
        if value.get("schema_version") != RUN_SCHEMA_VERSION:
            raise AtlasError("atlas input uses an unknown run schema version")
        validate_run_record(value)
        run_id = value["run_id"]
        if run_id in run_ids:
            raise AtlasError("atlas input contains duplicate run IDs")
        run_ids.add(run_id)
        records.append(value)
    return records, total_bytes


def _model_identity(identity: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "identity_confidence": identity["identity_confidence"],
        "requested_source": identity["requested_source"],
    }
    for key in ("resolved_id", "requested_alias", "snapshot_hint"):
        if key in identity:
            result[key] = identity[key]
    return result


def _generation_setting(setting: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "namespace": setting["namespace"],
        "key": setting["key"],
        "requested_value": setting["requested_value"],
        "status": setting["status"],
    }
    # This is intentionally conditional. Requested-only evidence is never
    # promoted to an applied value by the aggregate layer.
    if setting["status"] == "applied":
        result["applied_value"] = setting["applied_value"]
    return result


def _participant_stratum(participant: Mapping[str, Any]) -> dict[str, Any]:
    runtime = participant["runtime_identity"]
    settings = sorted(
        (_generation_setting(item) for item in participant["generation_settings"]),
        key=lambda item: (item["namespace"], item["key"]),
    )
    result: dict[str, Any] = {
        "role": participant["role"],
        "provider": runtime["provider"],
        "model_identity": _model_identity(participant["model_identity"]),
        "generation_settings": settings,
        "cli_name": runtime["cli_name"],
        "cli_version": runtime["cli_version"],
        "cli_source": runtime["cli_source"],
        "execution_surface": runtime["execution_surface"],
        "permission_mode": runtime["permission_mode"],
    }
    if "image_digest" in runtime:
        result["runtime_image_digest"] = runtime["image_digest"]
    return result


def _profile_stratum(record: Mapping[str, Any]) -> dict[str, Any]:
    case = record["case"]
    return {
        "source_type": case["source_type"],
        "family": case["family"],
        "size": case["size"],
        "profile_id": case["profile_id"],
    }


def _configuration_stratum(record: Mapping[str, Any]) -> dict[str, Any]:
    configuration = record["configuration"]
    return {
        key: configuration[key]
        for key in (
            "configuration_id",
            "relation",
            "participant_plan",
            "participants_actual",
            "workers_actual",
            "peak_concurrent",
            "nested_delegation",
            "independence_policy",
            "lane",
        )
    }


def _environment_stratum(record: Mapping[str, Any]) -> dict[str, Any]:
    environment = record["environment"]
    return {
        key: environment[key]
        for key in (
            "image_digest",
            "machine_class",
            "session_context",
            "repository_cache",
            "dependency_cache",
            "docker_cache",
            "provider_prompt_cache",
            "compaction",
            "competing_load",
            "timezone",
        )
    }


def _series_stratum(record: Mapping[str, Any]) -> dict[str, Any]:
    participants = sorted(
        (_participant_stratum(item) for item in record["participants"]),
        key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True),
    )
    return {
        "study_id": record["study_id"],
        "profile": _profile_stratum(record),
        "configuration": _configuration_stratum(record),
        "participants": participants,
        "environment": _environment_stratum(record),
    }


def _case_identity(record: Mapping[str, Any]) -> dict[str, Any]:
    case = record["case"]
    snapshot = record["snapshot"]
    return {
        "case_id": case["case_id"],
        "revision": case["revision"],
        "capsule_digest": case["capsule_digest"],
        "strong_online_oracle": case["strong_online_oracle"],
        "snapshot": {
            "base_sha": snapshot["base_sha"],
            "bundle_digest": snapshot["bundle_digest"],
            "instruction_set_digest": snapshot["instruction_set_digest"],
        },
    }


def _quality_population(record: Mapping[str, Any]) -> str:
    quality = record["outcome"]["quality_pass"]
    if quality is True:
        return "quality-pass"
    if quality is False:
        return "quality-fail"
    return "quality-unknown"


def _censoring(record: Mapping[str, Any]) -> dict[str, Any]:
    infrastructure = record["outcome"]["infrastructure"]
    if infrastructure == "timeout" or record["outcome"]["failure_class"] == "timeout-cap":
        status = "right-censored"
    elif infrastructure == "cancelled":
        status = "administratively-censored"
    else:
        status = "complete-terminal"
    return {
        "status": status,
        "safety_cap_ms": record["limits"]["wall_clock_ms"],
        "observed_terminal_ms": record["durations_ms"]["terminal_wall"],
    }


def _first_artifact(record: Mapping[str, Any]) -> dict[str, Any]:
    resolution = record["coverage"]["first_artifact_resolution"]
    result: dict[str, Any] = {"resolution": resolution}
    duration = record["durations_ms"].get("first_artifact_latency")
    if resolution == "progress-envelope":
        if duration is None:
            raise AtlasError("progress-envelope run has no first-artifact duration")
        result["milliseconds"] = duration
    elif duration is not None:
        raise AtlasError("unobserved first artifact cannot have a duration")
    return result


def _evaluator_score(record: Mapping[str, Any]) -> dict[str, Any] | None:
    evaluator = record["diagnostics"]["evaluator"]
    declared = evaluator.get("score")
    if isinstance(declared, dict):
        return copy.deepcopy(declared)
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


def _sample(record: Mapping[str, Any], run_digest: str) -> dict[str, Any]:
    environment = record["environment"]
    evaluator = record["diagnostics"]["evaluator"]
    return {
        "run_id": record["run_id"],
        "run_digest": run_digest,
        # The aggregate catalog digest is run provenance, not case identity.
        # Adding an unrelated family changes it without changing this case.
        "catalog_digest": record["case"]["catalog_digest"],
        # Recipe/harness metadata may advance while the visible immutable
        # bundle, base commit, instructions, capsule, and case revision do not.
        "fixture_revision": record["snapshot"]["fixture_revision"],
        "block_id": record["block_id"],
        "observed_at": record["landmarks"]["T0"]["wall_time"],
        "quality_population": _quality_population(record),
        "censoring": _censoring(record),
        "first_artifact": _first_artifact(record),
        "durations_ms": {
            key: record["durations_ms"][key]
            for key in DURATION_KEYS
            if key in record["durations_ms"]
        },
        "outcome": {
            key: record["outcome"][key]
            for key in (
                "infrastructure",
                "artifact",
                "online_acceptance",
                "offline_score",
                "quality_basis",
                "failure_class",
            )
        },
        "quality_evidence": {
            "evaluator_status": evaluator["status"],
            "check_count": len(evaluator["checks"]),
            "score": _evaluator_score(record),
        },
        "covariates": {
            key: environment[key]
            for key in (
                "machine_class",
                "session_context",
                "repository_cache",
                "dependency_cache",
                "docker_cache",
                "provider_prompt_cache",
                "compaction",
                "competing_load",
                "timezone",
            )
        },
    }


def _counts(samples: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "runs": len(samples),
        "observation_blocks": len({item["block_id"] for item in samples}),
        "quality_population": {
            population: sum(item["quality_population"] == population for item in samples)
            for population in QUALITY_POPULATIONS
        },
        "censoring": {
            status: sum(item["censoring"]["status"] == status for item in samples)
            for status in CENSORING_STATES
        },
        "first_artifact_resolution": {
            resolution: sum(
                item["first_artifact"]["resolution"] == resolution for item in samples
            )
            for resolution in FIRST_ARTIFACT_RESOLUTIONS
        },
    }


def _view_value(view_id: str, sample: Mapping[str, Any]) -> float | int | None:
    if view_id == "quality-pass-user-result":
        return (
            sample["durations_ms"].get("user_result")
            if sample["quality_population"] == "quality-pass"
            else None
        )
    if view_id == "quality-fail-terminal":
        return (
            sample["durations_ms"]["terminal_wall"]
            if sample["quality_population"] == "quality-fail"
            else None
        )
    if view_id == "quality-unknown-terminal":
        return (
            sample["durations_ms"]["terminal_wall"]
            if sample["quality_population"] == "quality-unknown"
            else None
        )
    if view_id == "censored-terminal":
        return (
            sample["durations_ms"]["terminal_wall"]
            if sample["censoring"]["status"] != "complete-terminal"
            else None
        )
    if view_id == "first-artifact-progress":
        return sample["first_artifact"].get("milliseconds")
    raise AtlasError("unknown duration view")


def _duration_views(samples: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for view_id in (
        "quality-pass-user-result",
        "quality-fail-terminal",
        "quality-unknown-terminal",
        "censored-terminal",
        "first-artifact-progress",
    ):
        points = [
            {"run_id": sample["run_id"], "milliseconds": value}
            for sample in samples
            if (value := _view_value(view_id, sample)) is not None
        ]
        if not points:
            continue
        view: dict[str, Any] = {"view_id": view_id, "points": points}
        if len(points) >= 2:
            values = [item["milliseconds"] for item in points]
            view["observed_range_ms"] = {
                "minimum": min(values),
                "maximum": max(values),
            }
        result.append(view)
    return result


def _case_aware_summaries(cases: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Summarize only views repeated within every one of multiple cases.

    Two observations are the mathematical minimum for a within-case range and
    two cases are the minimum for a between-case range.  Meeting that structural
    guard does *not* characterize a family; promotion remains study-specific.
    """

    if len(cases) < 2:
        return []
    summaries: list[dict[str, Any]] = []
    for view_id in (
        "quality-pass-user-result",
        "quality-fail-terminal",
        "quality-unknown-terminal",
        "censored-terminal",
        "first-artifact-progress",
    ):
        case_values: list[tuple[Mapping[str, Any], list[float | int]]] = []
        for case in cases:
            view = next(
                (item for item in case["duration_views"] if item["view_id"] == view_id),
                None,
            )
            if view is None or len(view["points"]) < 2:
                case_values = []
                break
            case_values.append(
                (case, [point["milliseconds"] for point in view["points"]])
            )
        if len(case_values) != len(cases):
            continue
        medians = [
            {
                "case_id": case["primary_stratum"]["case"]["case_id"],
                "revision": case["primary_stratum"]["case"]["revision"],
                "milliseconds": statistics.median(values),
            }
            for case, values in case_values
        ]
        median_values = [item["milliseconds"] for item in medians]
        summaries.append(
            {
                "view_id": view_id,
                "method": "equal-case-observed-medians-v1",
                "case_median_points_ms": medians,
                "between_case_observed_range_ms": {
                    "minimum": min(median_values),
                    "maximum": max(median_values),
                },
                "within_case_observed_ranges_ms": [
                    {
                        "case_id": case["primary_stratum"]["case"]["case_id"],
                        "revision": case["primary_stratum"]["case"]["revision"],
                        "minimum": min(values),
                        "maximum": max(values),
                    }
                    for case, values in case_values
                ],
            }
        )
    return summaries


def _window(samples: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    observed = sorted(item["observed_at"] for item in samples)
    return {"first_observed_at": observed[0], "last_observed_at": observed[-1]}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _validate_records(records: Sequence[dict[str, Any]]) -> list[tuple[dict[str, Any], str]]:
    seen_run_ids: set[str] = set()
    case_fingerprints: dict[tuple[str, int], str] = {}
    prepared: list[tuple[dict[str, Any], str]] = []
    for record in records:
        if record.get("schema_version") != RUN_SCHEMA_VERSION:
            raise AtlasError("atlas input uses an unknown run schema version")
        validate_run_record(record)
        run_id = record["run_id"]
        if run_id in seen_run_ids:
            raise AtlasError("atlas input contains duplicate run IDs")
        seen_run_ids.add(run_id)
        case_identity = _case_identity(record)
        case_key = (case_identity["case_id"], case_identity["revision"])
        fingerprint = canonical_json_digest(
            {
                "case": case_identity,
                "profile": _profile_stratum(record),
            }
        )
        previous = case_fingerprints.get(case_key)
        if previous is not None and previous != fingerprint:
            raise AtlasError("one case revision resolves to conflicting identities")
        case_fingerprints[case_key] = fingerprint
        prepared.append((record, canonical_json_digest(record)))
    return prepared


def build_atlas(
    records: Sequence[dict[str, Any]],
    *,
    max_records: int,
    max_input_bytes: int = DEFAULT_MAX_INPUT_BYTES,
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> dict[str, Any]:
    """Build a deterministic nested aggregate and enforce all finite caps."""

    _bounded_positive(max_records, label="max-records", upper=HARD_RECORD_LIMIT)
    _bounded_positive(max_input_bytes, label="max-input-bytes", upper=HARD_BYTE_LIMIT)
    _bounded_positive(max_output_bytes, label="max-output-bytes", upper=HARD_BYTE_LIMIT)
    if not records:
        raise AtlasError("atlas requires at least one validated run record")
    if len(records) > max_records:
        raise AtlasError("atlas records exceed max-records before aggregation")
    canonical_input_bytes = sum(len(_canonical_bytes(record)) for record in records)
    if canonical_input_bytes > max_input_bytes:
        raise AtlasError("canonical atlas input exceeds max-input-bytes")

    prepared = _validate_records(records)
    grouped: dict[str, dict[str, Any]] = {}
    source_runs: list[dict[str, str]] = []
    for record, run_digest in prepared:
        source_runs.append({"run_id": record["run_id"], "run_digest": run_digest})
        series_stratum = _series_stratum(record)
        series_id = canonical_json_digest(series_stratum)
        series = grouped.setdefault(
            series_id,
            {"series_stratum": series_stratum, "case_groups": {}},
        )
        case_identity = _case_identity(record)
        primary_stratum = {**copy.deepcopy(series_stratum), "case": case_identity}
        stratum_id = canonical_json_digest(primary_stratum)
        case_group = series["case_groups"].setdefault(
            stratum_id,
            {"primary_stratum": primary_stratum, "samples": []},
        )
        case_group["samples"].append(_sample(record, run_digest))

    series_output: list[dict[str, Any]] = []
    for series_id in sorted(grouped):
        grouped_series = grouped[series_id]
        cases: list[dict[str, Any]] = []
        for stratum_id in sorted(grouped_series["case_groups"]):
            raw_case = grouped_series["case_groups"][stratum_id]
            samples = sorted(
                raw_case["samples"],
                key=lambda item: (item["observed_at"], item["run_id"]),
            )
            cases.append(
                {
                    "stratum_id": stratum_id,
                    "primary_stratum": raw_case["primary_stratum"],
                    "evidence_state": (
                        "single-observation" if len(samples) == 1 else "same-case-repeat"
                    ),
                    "counts": _counts(samples),
                    "observation_window": _window(samples),
                    "duration_views": _duration_views(samples),
                    "samples": samples,
                }
            )
        all_samples = [sample for case in cases for sample in case["samples"]]
        summaries = _case_aware_summaries(cases)
        if len(cases) == 1:
            series_evidence = cases[0]["evidence_state"]
        else:
            series_evidence = "family-provisional"
        series_output.append(
            {
                "series_id": series_id,
                "series_stratum": grouped_series["series_stratum"],
                "evidence_state": series_evidence,
                "characterization": {
                    "status": "not-assessed",
                    "reason": "study-specific-precision-and-coverage-criteria-unavailable",
                },
                "case_aware_summary_status": (
                    "available" if summaries else "insufficient-repeat-structure"
                ),
                "counts": {**_counts(all_samples), "case_strata": len(cases)},
                "observation_window": _window(all_samples),
                "cases": cases,
                "case_aware_summaries": summaries,
            }
        )

    source_runs.sort(key=lambda item: item["run_id"])
    all_samples = [sample for series in series_output for case in series["cases"] for sample in case["samples"]]
    case_count = sum(len(series["cases"]) for series in series_output)
    atlas = {
        "schema_version": ATLAS_SCHEMA_VERSION,
        "aggregate_kind": "deterministic-duration-atlas",
        "aggregation_method": "case-nested-observed-v2",
        "source": {
            "run_schema_version": RUN_SCHEMA_VERSION,
            "record_count": len(records),
            "canonical_record_bytes": canonical_input_bytes,
            "run_set_digest": canonical_json_digest(source_runs),
            "runs": source_runs,
            "observation_window": _window(all_samples),
        },
        "safety_caps": {
            "role": "hard-resource-cap",
            "max_records": max_records,
            "max_input_bytes": max_input_bytes,
            "max_output_bytes": max_output_bytes,
            "max_output_entities": max_records * 3,
        },
        "counts": {
            "series": len(series_output),
            "case_strata": case_count,
            "samples": len(records),
            "output_entities": len(series_output) + case_count + len(records),
        },
        "series": series_output,
    }
    validate_atlas(atlas)
    if len(encode_atlas(atlas)) > max_output_bytes:
        raise AtlasError("atlas output exceeds max-output-bytes before writing")
    return atlas


def _load_atlas_schema() -> dict[str, Any]:
    schema = load_json(ATLAS_SCHEMA)
    if not isinstance(schema, dict):
        raise AtlasError("atlas schema root must be an object")
    return schema


def validate_atlas(atlas: Mapping[str, Any]) -> None:
    if atlas.get("schema_version") != ATLAS_SCHEMA_VERSION:
        raise AtlasError("unknown atlas schema version")
    try:
        validate(atlas, _load_atlas_schema())
    except ContractValidationError as exc:
        raise AtlasError("atlas schema validation failed") from exc
    counts = atlas["counts"]
    series_items = atlas["series"]
    case_items = [case for series in series_items for case in series["cases"]]
    samples = [sample for case in case_items for sample in case["samples"]]
    expected_counts = {
        "series": len(series_items),
        "case_strata": len(case_items),
        "samples": len(samples),
        "output_entities": len(series_items) + len(case_items) + len(samples),
    }
    if counts != expected_counts:
        raise AtlasError("atlas aggregate counts are not canonical")
    if counts["samples"] != atlas["source"]["record_count"]:
        raise AtlasError("atlas sample and source record counts disagree")
    if counts["output_entities"] > atlas["safety_caps"]["max_output_entities"]:
        raise AtlasError("atlas output entity count exceeds its declared cap")
    if len(atlas["source"]["runs"]) != atlas["source"]["record_count"]:
        raise AtlasError("atlas source digest inventory count disagrees")
    if canonical_json_digest(atlas["source"]["runs"]) != atlas["source"]["run_set_digest"]:
        raise AtlasError("atlas source run-set digest is not canonical")
    source_pairs = {
        (item["run_id"], item["run_digest"]) for item in atlas["source"]["runs"]
    }
    sample_pairs = {(item["run_id"], item["run_digest"]) for item in samples}
    if source_pairs != sample_pairs or len(source_pairs) != len(samples):
        raise AtlasError("atlas samples do not match the source digest inventory")
    if atlas["source"]["observation_window"] != _window(samples):
        raise AtlasError("atlas source observation window is not canonical")
    for series in series_items:
        if series["series_id"] != canonical_json_digest(series["series_stratum"]):
            raise AtlasError("atlas series ID is not canonical")
        if series["evidence_state"] == "family-characterized":
            raise AtlasError("aggregate cannot self-promote a series to characterized")
        series_samples = [sample for case in series["cases"] for sample in case["samples"]]
        expected_series_counts = {
            **_counts(series_samples),
            "case_strata": len(series["cases"]),
        }
        if series["counts"] != expected_series_counts:
            raise AtlasError("atlas series counts are not canonical")
        if series["observation_window"] != _window(series_samples):
            raise AtlasError("atlas series observation window is not canonical")
        expected_series_state = (
            series["cases"][0]["evidence_state"]
            if len(series["cases"]) == 1
            else "family-provisional"
        )
        if series["evidence_state"] != expected_series_state:
            raise AtlasError("atlas series evidence state is not canonical")
        for case in series["cases"]:
            if case["stratum_id"] != canonical_json_digest(case["primary_stratum"]):
                raise AtlasError("atlas case stratum ID is not canonical")
            expected_series_stratum = {
                key: value
                for key, value in case["primary_stratum"].items()
                if key != "case"
            }
            if expected_series_stratum != series["series_stratum"]:
                raise AtlasError("atlas case and series strata disagree")
            case_samples = case["samples"]
            if case["counts"] != _counts(case_samples):
                raise AtlasError("atlas case counts are not canonical")
            expected_case_state = (
                "single-observation" if len(case_samples) == 1 else "same-case-repeat"
            )
            if case["evidence_state"] != expected_case_state:
                raise AtlasError("atlas case evidence state is not canonical")
            if case["observation_window"] != _window(case_samples):
                raise AtlasError("atlas case observation window is not canonical")
            if case["duration_views"] != _duration_views(case_samples):
                raise AtlasError("atlas case duration views are not canonical")
            for sample in case["samples"]:
                first_artifact = sample["first_artifact"]
                if first_artifact["resolution"] == "progress-envelope":
                    if "milliseconds" not in first_artifact:
                        raise AtlasError("observed first artifact has no duration")
                elif "milliseconds" in first_artifact:
                    raise AtlasError("missing first artifact contains an inferred duration")
                evidence = sample["quality_evidence"]
                score = evidence["score"]
                if score is None:
                    if evidence["check_count"] != 0:
                        raise AtlasError("quality checks are present without a content-free score")
                else:
                    if score["total"] != evidence["check_count"]:
                        raise AtlasError("quality score total disagrees with check count")
                    if score["passed"] > score["total"]:
                        raise AtlasError("quality score passed count exceeds total")
                    if score["ratio"] != round(score["passed"] / score["total"], 6):
                        raise AtlasError("quality score ratio is not canonical")
                    if evidence["evaluator_status"] == "pass" and score["ratio"] != 1:
                        raise AtlasError("passing evaluator has a partial quality score")
                    if evidence["evaluator_status"] == "fail" and not score["failed_check_ids"]:
                        raise AtlasError("failing evaluator has no failed criterion IDs")
                for participant in case["primary_stratum"]["participants"]:
                    for setting in participant["generation_settings"]:
                        if setting["status"] != "applied" and "applied_value" in setting:
                            raise AtlasError("requested-only setting was promoted to applied")
        expected_summaries = _case_aware_summaries(series["cases"])
        if series["case_aware_summaries"] != expected_summaries:
            raise AtlasError("atlas case-aware summaries are not canonical")
        expected_summary_status = (
            "available" if expected_summaries else "insufficient-repeat-structure"
        )
        if series["case_aware_summary_status"] != expected_summary_status:
            raise AtlasError("atlas case-aware summary status is not canonical")


def encode_atlas(atlas: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(atlas, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def atomic_write_atlas(
    path: Path,
    atlas: Mapping[str, Any],
    *,
    max_output_bytes: int,
    replace: Callable[[Path, Path], Any] = os.replace,
) -> None:
    """Atomically replace a derived atlas after schema and byte-cap checks."""

    _bounded_positive(max_output_bytes, label="max-output-bytes", upper=HARD_BYTE_LIMIT)
    validate_atlas(atlas)
    encoded = encode_atlas(atlas)
    if len(encoded) > max_output_bytes:
        raise AtlasError("atlas output exceeds max-output-bytes before writing")
    if path.exists() and not path.is_file():
        raise AtlasError("atlas output path exists and is not a file")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        replace(temporary, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _cap_argument(label: str, upper: int) -> Callable[[str], int]:
    def parse(raw: str) -> int:
        try:
            value = int(raw)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"{label} must be an integer") from exc
        if value < 1 or value > upper:
            raise argparse.ArgumentTypeError(f"{label} must be between 1 and {upper}")
        return value

    return parse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help="run JSON files or directories")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--max-records",
        type=_cap_argument("max-records", HARD_RECORD_LIMIT),
        required=True,
    )
    parser.add_argument(
        "--max-input-bytes",
        type=_cap_argument("max-input-bytes", HARD_BYTE_LIMIT),
        default=DEFAULT_MAX_INPUT_BYTES,
    )
    parser.add_argument(
        "--max-output-bytes",
        type=_cap_argument("max-output-bytes", HARD_BYTE_LIMIT),
        default=DEFAULT_MAX_OUTPUT_BYTES,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        records, _actual_input_bytes = load_run_records_bounded(
            args.inputs,
            max_records=args.max_records,
            max_input_bytes=args.max_input_bytes,
        )
        atlas = build_atlas(
            records,
            max_records=args.max_records,
            max_input_bytes=args.max_input_bytes,
            max_output_bytes=args.max_output_bytes,
        )
        atomic_write_atlas(
            args.output,
            atlas,
            max_output_bytes=args.max_output_bytes,
        )
    except (AtlasError, DurationStudyError, ContractValidationError, OSError) as exc:
        print(f"duration atlas build failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

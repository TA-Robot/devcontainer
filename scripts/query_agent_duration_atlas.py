#!/usr/bin/env python3
"""Deterministically query a validated duration atlas under context-safe caps.

The query surface performs exact equality filtering and bounded rendering only.
It does not interpolate unmeasured cells, estimate bands, rank configurations,
or produce routing recommendations.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass, field
import json
from pathlib import Path
import sys
from typing import Any, Callable, Mapping, Sequence

from agent_contracts import ContractValidationError
from agent_duration_atlas import AtlasError, validate_atlas


QUERY_SCHEMA_VERSION = 1
HARD_MAX_ROWS = 1_000
HARD_MAX_OUTPUT_BYTES = 32 * 1024 * 1024
HARD_MAX_ATLAS_BYTES = 512 * 1024 * 1024
MODES = ("summary", "compare", "curve", "coverage", "audit", "explain")
FORMATS = ("json", "markdown")
SETTING_STATUSES = ("applied", "rejected", "not-advertised", "unknown")
CURVE_AXES = ("participants-actual", "workers-actual", "peak-concurrent")
COMPARE_AXES = (
    "case",
    "relation",
    "participant-plan",
    "participant-role",
    "topology",
    "provider",
    "requested-model",
    "identity-confidence",
    "setting-applied-value",
    "cli-version",
    "cli-source",
    "execution-surface",
    "permission-mode",
    "nested-delegation",
    "lane",
    "study",
    "environment",
)
ENVIRONMENT_FILTERS = {
    "image_digest": "image_digest",
    "machine_class": "machine_class",
    "session_context": "session_context",
    "repository_cache": "repository_cache",
    "dependency_cache": "dependency_cache",
    "docker_cache": "docker_cache",
    "provider_prompt_cache": "provider_prompt_cache",
    "compaction": "compaction",
    "competing_load": "competing_load",
    "timezone": "timezone",
}


class AtlasQueryError(ValueError):
    """Raised when a query cannot be validated or rendered within its caps."""


@dataclass(frozen=True)
class QueryFilters:
    source_type: str | None = None
    family: str | None = None
    size: str | None = None
    profile: str | None = None
    case_id: str | None = None
    case_revision: int | None = None
    configuration_id: str | None = None
    relation: str | None = None
    participant_plan: str | None = None
    participants_actual: int | None = None
    workers_actual: int | None = None
    peak_concurrent: int | None = None
    nested_delegation: str | None = None
    independence_policy: str | None = None
    lane: str | None = None
    participant_role: str | None = None
    provider: str | None = None
    requested_model: str | None = None
    resolved_model: str | None = None
    identity_confidence: str | None = None
    setting_namespace: str | None = None
    setting_key: str | None = None
    setting_status: str | None = None
    setting_requested_value: Any | None = None
    setting_applied_value: Any | None = None
    cli_name: str | None = None
    cli_version: str | None = None
    cli_source: str | None = None
    execution_surface: str | None = None
    permission_mode: str | None = None
    runtime_image_digest: str | None = None
    study: str | None = None
    environment: Mapping[str, str] = field(default_factory=dict)


def load_atlas(path: Path) -> dict[str, Any]:
    """Load one atlas under a hard input-size bound and fail closed on schema."""

    try:
        size = path.stat().st_size
    except OSError as exc:
        raise AtlasQueryError(f"cannot stat duration atlas: {path}") from exc
    if size < 1 or size > HARD_MAX_ATLAS_BYTES:
        raise AtlasQueryError("duration atlas file is empty or exceeds the hard byte cap")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise AtlasQueryError(f"cannot read duration atlas: {path}") from exc
    if len(raw) > HARD_MAX_ATLAS_BYTES:
        raise AtlasQueryError("duration atlas exceeds the hard byte cap while reading")
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AtlasQueryError("duration atlas is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise AtlasQueryError("duration atlas root must be an object")
    try:
        validate_atlas(value)
    except (AtlasError, ContractValidationError, KeyError, TypeError, ValueError) as exc:
        raise AtlasQueryError("duration atlas schema or semantics are invalid") from exc
    return value


def _setting_matches(setting: Mapping[str, Any], filters: QueryFilters) -> bool:
    if filters.setting_namespace is not None and setting["namespace"] != filters.setting_namespace:
        return False
    if filters.setting_key is not None and setting["key"] != filters.setting_key:
        return False
    if filters.setting_status is not None and setting["status"] != filters.setting_status:
        return False
    if (
        filters.setting_requested_value is not None
        and setting["requested_value"] != filters.setting_requested_value
    ):
        return False
    if filters.setting_applied_value is not None:
        # Presence is part of the predicate. Unknown/requested-only settings do
        # not match even when their requested value equals the applied query.
        if "applied_value" not in setting:
            return False
        if setting["applied_value"] != filters.setting_applied_value:
            return False
    return True


def _participant_filters_active(filters: QueryFilters) -> bool:
    return any(
        value is not None
        for value in (
            filters.provider,
            filters.participant_role,
            filters.requested_model,
            filters.resolved_model,
            filters.identity_confidence,
            filters.setting_namespace,
            filters.setting_key,
            filters.setting_status,
            filters.setting_requested_value,
            filters.setting_applied_value,
            filters.cli_name,
            filters.cli_version,
            filters.cli_source,
            filters.execution_surface,
            filters.permission_mode,
            filters.runtime_image_digest,
        )
    )


def _participant_matches(participant: Mapping[str, Any], filters: QueryFilters) -> bool:
    identity = participant["model_identity"]
    if filters.participant_role is not None and participant["role"] != filters.participant_role:
        return False
    if filters.provider is not None and participant["provider"] != filters.provider:
        return False
    if (
        filters.requested_model is not None
        and identity.get("requested_alias") != filters.requested_model
    ):
        return False
    if filters.resolved_model is not None and identity.get("resolved_id") != filters.resolved_model:
        return False
    if (
        filters.identity_confidence is not None
        and identity["identity_confidence"] != filters.identity_confidence
    ):
        return False
    if filters.cli_name is not None and participant["cli_name"] != filters.cli_name:
        return False
    if filters.cli_version is not None and participant["cli_version"] != filters.cli_version:
        return False
    if filters.cli_source is not None and participant["cli_source"] != filters.cli_source:
        return False
    if (
        filters.execution_surface is not None
        and participant["execution_surface"] != filters.execution_surface
    ):
        return False
    if (
        filters.permission_mode is not None
        and participant["permission_mode"] != filters.permission_mode
    ):
        return False
    if (
        filters.runtime_image_digest is not None
        and participant.get("runtime_image_digest") != filters.runtime_image_digest
    ):
        return False
    setting_active = any(
        value is not None
        for value in (
            filters.setting_namespace,
            filters.setting_key,
            filters.setting_status,
            filters.setting_requested_value,
            filters.setting_applied_value,
        )
    )
    if setting_active and not any(
        _setting_matches(setting, filters) for setting in participant["generation_settings"]
    ):
        return False
    return True


def _case_matches(case: Mapping[str, Any], filters: QueryFilters) -> bool:
    stratum = case["primary_stratum"]
    profile = stratum["profile"]
    case_identity = stratum["case"]
    configuration = stratum["configuration"]
    direct_checks = (
        (filters.source_type, profile["source_type"]),
        (filters.family, profile["family"]),
        (filters.size, profile["size"]),
        (filters.profile, profile["profile_id"]),
        (filters.case_id, case_identity["case_id"]),
        (filters.case_revision, case_identity["revision"]),
        (filters.configuration_id, configuration["configuration_id"]),
        (filters.relation, configuration["relation"]),
        (filters.participant_plan, configuration["participant_plan"]),
        (filters.participants_actual, configuration["participants_actual"]),
        (filters.workers_actual, configuration["workers_actual"]),
        (filters.peak_concurrent, configuration["peak_concurrent"]),
        (filters.nested_delegation, configuration["nested_delegation"]),
        (filters.independence_policy, configuration["independence_policy"]),
        (filters.lane, configuration["lane"]),
        (filters.study, stratum["study_id"]),
    )
    if any(expected is not None and expected != actual for expected, actual in direct_checks):
        return False
    environment = stratum["environment"]
    if any(environment.get(key) != value for key, value in filters.environment.items()):
        return False
    if _participant_filters_active(filters) and not any(
        _participant_matches(participant, filters) for participant in stratum["participants"]
    ):
        return False
    return True


def _cells(atlas: Mapping[str, Any]) -> list[tuple[Mapping[str, Any], Mapping[str, Any]]]:
    return sorted(
        (
            (series, case)
            for series in atlas["series"]
            for case in series["cases"]
        ),
        key=lambda item: (item[0]["series_id"], item[1]["stratum_id"]),
    )


def _matched_cells(
    atlas: Mapping[str, Any], filters: QueryFilters
) -> list[tuple[Mapping[str, Any], Mapping[str, Any]]]:
    return [item for item in _cells(atlas) if _case_matches(item[1], filters)]


def _observed_representation(view: Mapping[str, Any]) -> dict[str, Any]:
    points = view["points"]
    if len(points) == 1:
        return {
            "representation": "raw-point",
            "milliseconds": points[0]["milliseconds"],
            "observation_count": 1,
        }
    observed_range = view["observed_range_ms"]
    return {
        "representation": "observed-range",
        "minimum_ms": observed_range["minimum"],
        "maximum_ms": observed_range["maximum"],
        "observation_count": len(points),
    }


def _raw_metric_representation(
    samples: Sequence[Mapping[str, Any]], metric: str
) -> dict[str, Any] | None:
    values = [sample["durations_ms"][metric] for sample in samples if metric in sample["durations_ms"]]
    if not values:
        return None
    if len(values) == 1:
        return {
            "representation": "raw-point",
            "milliseconds": values[0],
            "observation_count": 1,
        }
    return {
        "representation": "observed-range",
        "minimum_ms": min(values),
        "maximum_ms": max(values),
        "observation_count": len(values),
    }


def _numeric_representation(values: Sequence[float | int]) -> dict[str, Any] | None:
    if not values:
        return None
    if len(values) == 1:
        return {
            "representation": "raw-point",
            "value": values[0],
            "observation_count": 1,
        }
    return {
        "representation": "observed-range",
        "minimum": min(values),
        "maximum": max(values),
        "observation_count": len(values),
    }


def _compact_quality_evidence(samples: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    evidence = [sample["quality_evidence"] for sample in samples]
    scores = [item["score"] for item in evidence if item["score"] is not None]
    criterion_scores = [item for item in scores if item["resolution"] == "criterion"]
    aggregate_scores = [item for item in scores if item["resolution"] == "aggregate-check"]
    failed_counts: dict[str, int] = {}
    for score in scores:
        for check_id in score["failed_check_ids"]:
            failed_counts[check_id] = failed_counts.get(check_id, 0) + 1
    result: dict[str, Any] = {
        "evaluator_status": {
            status: sum(item["evaluator_status"] == status for item in evidence)
            for status in ("pass", "fail", "not-run", "infrastructure-failure")
        },
        "check_count": _numeric_representation([item["check_count"] for item in evidence]),
        "score_availability": {
            "available": len(scores),
            "unavailable": len(evidence) - len(scores),
        },
        "score_resolution": {
            "criterion": sum(item["resolution"] == "criterion" for item in scores),
            "aggregate-check": sum(item["resolution"] == "aggregate-check" for item in scores),
        },
        "failed_criteria": {
            "unique_check_ids": sorted(failed_counts),
            "by_check_id": [
                {"check_id": check_id, "sample_count": failed_counts[check_id]}
                for check_id in sorted(failed_counts)
            ],
            "samples_with_failed_criteria": sum(
                bool(item["failed_check_ids"]) for item in scores
            ),
        },
    }
    if criterion_scores:
        result["criterion_score"] = {
            "ratio": _numeric_representation([item["ratio"] for item in criterion_scores]),
            "passed": _numeric_representation([item["passed"] for item in criterion_scores]),
            "total": _numeric_representation([item["total"] for item in criterion_scores]),
            "public_passed": _numeric_representation(
                [item["public_passed"] for item in criterion_scores]
            ),
            "public_total": _numeric_representation(
                [item["public_total"] for item in criterion_scores]
            ),
            "hidden_passed": _numeric_representation(
                [item["hidden_passed"] for item in criterion_scores]
            ),
            "hidden_total": _numeric_representation(
                [item["hidden_total"] for item in criterion_scores]
            ),
        }
    if aggregate_scores:
        result["aggregate_check_score"] = {
            "ratio": _numeric_representation([item["ratio"] for item in aggregate_scores]),
            "passed": _numeric_representation([item["passed"] for item in aggregate_scores]),
            "total": _numeric_representation([item["total"] for item in aggregate_scores]),
        }
    return result


def _compact_participant(participant: Mapping[str, Any]) -> dict[str, Any]:
    result = {
        "role": participant["role"],
        "provider": participant["provider"],
        "model_identity": copy.deepcopy(participant["model_identity"]),
        "generation_settings": copy.deepcopy(participant["generation_settings"]),
        "cli_name": participant["cli_name"],
        "cli_version": participant["cli_version"],
        "cli_source": participant["cli_source"],
        "execution_surface": participant["execution_surface"],
        "permission_mode": participant["permission_mode"],
    }
    if "runtime_image_digest" in participant:
        result["runtime_image_digest"] = participant["runtime_image_digest"]
    return result


def _validate_filters(filters: QueryFilters) -> None:
    if filters.case_revision is not None and filters.case_revision < 1:
        raise AtlasQueryError("case-revision must be positive")
    if filters.participants_actual is not None and filters.participants_actual < 1:
        raise AtlasQueryError("participants-actual must be positive")
    for value, label in (
        (filters.workers_actual, "workers-actual"),
        (filters.peak_concurrent, "peak-concurrent"),
    ):
        if value is not None and value < 0:
            raise AtlasQueryError(f"{label} must be non-negative")
    unknown_environment = set(filters.environment) - set(ENVIRONMENT_FILTERS.values())
    if unknown_environment:
        raise AtlasQueryError("query contains an unknown environment filter")
    if (
        filters.setting_applied_value is not None
        and filters.setting_status not in {None, "applied"}
    ):
        raise AtlasQueryError("setting-applied-value contradicts the requested setting status")


def _compact_row(
    series: Mapping[str, Any],
    case: Mapping[str, Any],
) -> dict[str, Any]:
    stratum = case["primary_stratum"]
    durations = {
        view["view_id"]: _observed_representation(view)
        for view in case["duration_views"]
    }
    aggregate_worker = _raw_metric_representation(case["samples"], "aggregate_worker")
    if aggregate_worker is not None:
        durations["aggregate-worker-observed"] = aggregate_worker
    safety_caps = sorted({sample["censoring"]["safety_cap_ms"] for sample in case["samples"]})
    return {
        "series_id": series["series_id"],
        "stratum_id": case["stratum_id"],
        "profile": copy.deepcopy(stratum["profile"]),
        "case": {
            "case_id": stratum["case"]["case_id"],
            "revision": stratum["case"]["revision"],
        },
        "configuration": copy.deepcopy(stratum["configuration"]),
        "participants": [_compact_participant(item) for item in stratum["participants"]],
        "environment": copy.deepcopy(stratum["environment"]),
        "study_id": stratum["study_id"],
        "durations": durations,
        "evidence": {
            "case_state": case["evidence_state"],
            "series_state": series["evidence_state"],
            "characterization": copy.deepcopy(series["characterization"]),
            "observation_window": copy.deepcopy(case["observation_window"]),
            "case_strata_in_series": series["counts"]["case_strata"],
            "run_count": case["counts"]["runs"],
            "quality_population": copy.deepcopy(case["counts"]["quality_population"]),
            "first_artifact_resolution": copy.deepcopy(
                case["counts"]["first_artifact_resolution"]
            ),
            "quality_evidence": _compact_quality_evidence(case["samples"]),
        },
        "censoring": {
            "counts": copy.deepcopy(case["counts"]["censoring"]),
            "safety_caps_ms": safety_caps,
        },
        "freshness": {
            "status": "unknown",
            "reason": "atlas-schema-has-no-stale-annotation",
        },
    }


def _audit_row(series: Mapping[str, Any], case: Mapping[str, Any]) -> dict[str, Any]:
    stratum = case["primary_stratum"]
    study_id = stratum["study_id"]
    return {
        "series_id": series["series_id"],
        "stratum_id": case["stratum_id"],
        "case_id": stratum["case"]["case_id"],
        "case_revision": stratum["case"]["revision"],
        "study_id": study_id,
        "detail_reference": f"docs/agents/duration-atlas/studies/{study_id}.md",
        "reference_status": "not-verified",
        "source_runs": [
            {"run_id": sample["run_id"], "run_digest": sample["run_digest"]}
            for sample in case["samples"]
        ],
    }


def _dimension_values(case: Mapping[str, Any]) -> dict[str, list[Any]]:
    stratum = case["primary_stratum"]
    configuration = stratum["configuration"]
    values: dict[str, list[Any]] = {
        "source-type": [stratum["profile"]["source_type"]],
        "family": [stratum["profile"]["family"]],
        "size": [stratum["profile"]["size"]],
        "profile": [stratum["profile"]["profile_id"]],
        "case": [stratum["case"]["case_id"]],
        "case-revision": [stratum["case"]["revision"]],
        "configuration": [configuration["configuration_id"]],
        "relation": [configuration["relation"]],
        "participant-plan": [configuration["participant_plan"]],
        "participants-actual": [configuration["participants_actual"]],
        "workers-actual": [configuration["workers_actual"]],
        "peak-concurrent": [configuration["peak_concurrent"]],
        "nested-delegation": [configuration["nested_delegation"]],
        "independence-policy": [configuration["independence_policy"]],
        "lane": [configuration["lane"]],
        "study": [stratum["study_id"]],
    }
    for key, value in stratum["environment"].items():
        values[f"environment.{key.replace('_', '-')}"] = [value]
    participant_dimensions = {
        "participant-role": [],
        "provider": [],
        "requested-model": [],
        "resolved-model": [],
        "identity-confidence": [],
        "cli-name": [],
        "cli-version": [],
        "cli-source": [],
        "execution-surface": [],
        "permission-mode": [],
        "runtime-image-digest": [],
        "setting-namespace": [],
        "setting-key": [],
        "setting-requested-value": [],
        "setting-status": [],
        "setting-applied-value": [],
    }
    for participant in stratum["participants"]:
        identity = participant["model_identity"]
        participant_dimensions["participant-role"].append(participant["role"])
        participant_dimensions["provider"].append(participant["provider"])
        if "requested_alias" in identity:
            participant_dimensions["requested-model"].append(identity["requested_alias"])
        if "resolved_id" in identity:
            participant_dimensions["resolved-model"].append(identity["resolved_id"])
        participant_dimensions["identity-confidence"].append(identity["identity_confidence"])
        participant_dimensions["cli-name"].append(participant["cli_name"])
        participant_dimensions["cli-version"].append(participant["cli_version"])
        participant_dimensions["cli-source"].append(participant["cli_source"])
        participant_dimensions["execution-surface"].append(participant["execution_surface"])
        participant_dimensions["permission-mode"].append(participant["permission_mode"])
        if "runtime_image_digest" in participant:
            participant_dimensions["runtime-image-digest"].append(
                participant["runtime_image_digest"]
            )
        for setting in participant["generation_settings"]:
            participant_dimensions["setting-namespace"].append(setting["namespace"])
            participant_dimensions["setting-key"].append(setting["key"])
            participant_dimensions["setting-requested-value"].append(
                setting["requested_value"]
            )
            participant_dimensions["setting-status"].append(setting["status"])
            if "applied_value" in setting:
                participant_dimensions["setting-applied-value"].append(
                    setting["applied_value"]
                )
    values.update(participant_dimensions)
    return values


def _value_key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _coverage_rows(
    cells: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]]
) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str], tuple[Any, int]] = {}
    for _series, case in cells:
        for dimension, values in _dimension_values(case).items():
            for value in {_value_key(item): item for item in values}.values():
                key = (dimension, _value_key(value))
                previous = counts.get(key)
                counts[key] = (value, 1 if previous is None else previous[1] + 1)
    return [
        {"dimension": dimension, "value": value, "case_strata": count}
        for (dimension, _encoded), (value, count) in sorted(counts.items())
    ]


def _refinement_hints(
    cells: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]]
) -> list[dict[str, Any]]:
    coverage = _coverage_rows(cells)
    by_dimension: dict[str, list[Any]] = {}
    for item in coverage:
        by_dimension.setdefault(item["dimension"], []).append(item["value"])
    return [
        {
            "filter": _filter_option(dimension),
            "available_values": sorted(values, key=_value_key),
        }
        for dimension, values in sorted(by_dimension.items())
        if len(values) > 1
    ]


def _filter_option(dimension: str) -> str:
    aliases = {
        "case": "--case-id",
        "case-revision": "--case-revision",
        "configuration": "--configuration-id",
    }
    if dimension in aliases:
        return aliases[dimension]
    if dimension.startswith("environment."):
        return f"--{dimension.removeprefix('environment.')}"
    return f"--{dimension}"


def _curve_coordinate(case: Mapping[str, Any], axis: str) -> int:
    key = axis.replace("-", "_")
    return case["primary_stratum"]["configuration"][key]


def _filters_payload(filters: QueryFilters) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for name in (
        "source_type",
        "family",
        "size",
        "profile",
        "case_id",
        "case_revision",
        "configuration_id",
        "relation",
        "participant_plan",
        "participants_actual",
        "workers_actual",
        "peak_concurrent",
        "nested_delegation",
        "independence_policy",
        "lane",
        "participant_role",
        "provider",
        "requested_model",
        "resolved_model",
        "identity_confidence",
        "setting_namespace",
        "setting_key",
        "setting_status",
        "setting_requested_value",
        "setting_applied_value",
        "cli_name",
        "cli_version",
        "cli_source",
        "execution_surface",
        "permission_mode",
        "runtime_image_digest",
        "study",
    ):
        value = getattr(filters, name)
        if value is not None:
            payload[name] = value
    if filters.environment:
        payload["environment"] = dict(sorted(filters.environment.items()))
    return payload


def build_query_result(
    atlas: Mapping[str, Any],
    *,
    mode: str,
    filters: QueryFilters,
    max_rows: int,
    max_output_bytes: int,
    compare_by: Sequence[str] = (),
    curve_by: str = "workers-actual",
    output_format: str = "json",
) -> dict[str, Any]:
    """Build and byte-fit one compact result without returning the atlas body."""

    if mode not in MODES:
        raise AtlasQueryError("unknown query mode")
    if output_format not in FORMATS:
        raise AtlasQueryError("unknown query output format")
    if isinstance(max_rows, bool) or not isinstance(max_rows, int) or not 1 <= max_rows <= HARD_MAX_ROWS:
        raise AtlasQueryError(f"max-rows must be between 1 and {HARD_MAX_ROWS}")
    if (
        isinstance(max_output_bytes, bool)
        or not isinstance(max_output_bytes, int)
        or not 1 <= max_output_bytes <= HARD_MAX_OUTPUT_BYTES
    ):
        raise AtlasQueryError(
            f"max-output-bytes must be between 1 and {HARD_MAX_OUTPUT_BYTES}"
        )
    if curve_by not in CURVE_AXES:
        raise AtlasQueryError("unknown curve axis")
    if any(item not in COMPARE_AXES for item in compare_by):
        raise AtlasQueryError("unknown comparison axis")
    _validate_filters(filters)
    try:
        validate_atlas(atlas)
    except (AtlasError, ContractValidationError, KeyError, TypeError, ValueError) as exc:
        raise AtlasQueryError("duration atlas schema or semantics are invalid") from exc

    all_cells = _cells(atlas)
    matched = _matched_cells(atlas, filters)
    result: dict[str, Any] = {
        "schema_version": QUERY_SCHEMA_VERSION,
        "query_kind": "bounded-duration-atlas-query",
        "mode": mode,
        "status": "measured" if matched else "unmeasured",
        "atlas": {
            "schema_version": atlas["schema_version"],
            "source_run_set_digest": atlas["source"]["run_set_digest"],
        },
        "filters": _filters_payload(filters),
        "limits": {
            "role": "context-safety-cap",
            "max_rows": max_rows,
            "max_output_bytes": max_output_bytes,
        },
        "match": {
            "case_strata": len(matched),
            "displayed_rows": 0,
        },
        "truncation": {"truncated": False, "reasons": []},
        "refinement_hints": [],
        "rows": [],
    }

    if mode == "explain":
        result["status"] = "references"
        result["detail_references"] = [
            "temp/multi-agent-duration-atlas/05-sampling-and-analysis.md",
            "temp/multi-agent-duration-atlas/11-skill-delivery-and-context-budget.md",
        ]
    elif not matched:
        result["status"] = "unmeasured"
        result["refinement_hints"] = _refinement_hints(all_cells)
        result["measured_identifiers_only"] = True
        result["rows"] = _coverage_rows(all_cells)
    elif mode == "summary" and len(matched) != 1:
        result["status"] = "refine"
        result["refinement_hints"] = _refinement_hints(matched)
    elif mode == "coverage":
        result["rows"] = _coverage_rows(matched)
        result["coverage"] = {
            "duration_values_included": False,
            "freshness": {
                "status": "unknown",
                "reason": "atlas-schema-has-no-stale-annotation",
            },
            "quality_population": {
                key: sum(case["counts"]["quality_population"][key] for _series, case in matched)
                for key in ("quality-pass", "quality-fail", "quality-unknown")
            },
            "censoring": {
                key: sum(case["counts"]["censoring"][key] for _series, case in matched)
                for key in (
                    "complete-terminal",
                    "right-censored",
                    "administratively-censored",
                )
            },
            "first_artifact_resolution": {
                key: sum(
                    case["counts"]["first_artifact_resolution"][key]
                    for _series, case in matched
                )
                for key in ("progress-envelope", "not-observed", "not-applicable", "unknown")
            },
            "quality_evidence": _compact_quality_evidence(
                [sample for _series, case in matched for sample in case["samples"]]
            ),
        }
    elif mode == "audit":
        result["rows"] = [_audit_row(series, case) for series, case in matched]
    else:
        rows = [_compact_row(series, case) for series, case in matched]
        if mode == "curve":
            for row, (_series, case) in zip(rows, matched):
                row["curve"] = {
                    "axis": curve_by,
                    "observed_coordinate": _curve_coordinate(case, curve_by),
                    "interpolation": "none",
                }
            rows.sort(
                key=lambda row: (
                    row["curve"]["observed_coordinate"],
                    row["series_id"],
                    row["stratum_id"],
                )
            )
            result["curve_axis"] = curve_by
        if mode == "compare":
            result["comparison_axes"] = list(compare_by) or ["explicit-primary-strata"]
        result["rows"] = rows

    if len(result["rows"]) > max_rows:
        result["rows"] = result["rows"][:max_rows]
        result["truncation"] = {"truncated": True, "reasons": ["max-rows"]}
        result["refinement_hints"] = _refinement_hints(matched)
    result["match"]["displayed_rows"] = len(result["rows"])
    return _fit_output(result, output_format=output_format, max_output_bytes=max_output_bytes)


def _json_bytes(result: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _duration_label(value: Mapping[str, Any] | None) -> str:
    if value is None:
        return "unavailable"
    if value["representation"] == "raw-point":
        return f"{value['milliseconds']:.3f}ms (raw point)"
    return (
        f"{value['minimum_ms']:.3f}..{value['maximum_ms']:.3f}ms "
        f"(observed range, n={value['observation_count']})"
    )


def _participant_label(participants: Sequence[Mapping[str, Any]]) -> str:
    labels: list[str] = []
    for participant in participants:
        identity = participant["model_identity"]
        model = identity.get("resolved_id") or identity.get("requested_alias") or "unspecified"
        settings = ",".join(
            f"{item['key']}="
            + (
                str(item["applied_value"])
                if "applied_value" in item
                else f"requested:{item['requested_value']}/{item['status']}"
            )
            for item in participant["generation_settings"]
        ) or "no-setting"
        labels.append(
            f"{participant['provider']}:{model}/{identity['identity_confidence']} {settings}"
        )
    return _markdown_cell("; ".join(labels))


def _markdown_cell(value: Any) -> str:
    return (
        str(value)
        .replace("\r", " ")
        .replace("\n", " ")
        .replace("|", "\\|")
    )


def _quality_evidence_label(evidence: Mapping[str, Any]) -> str:
    statuses = evidence["evaluator_status"]
    availability = evidence["score_availability"]
    failed = evidence["failed_criteria"]["unique_check_ids"]
    return (
        f"evaluator pass={statuses['pass']} fail={statuses['fail']} "
        f"not-run={statuses['not-run']}; score available={availability['available']} "
        f"unavailable={availability['unavailable']}; failed={','.join(failed) or '-'}"
    )


def render_markdown(result: Mapping[str, Any]) -> str:
    lines = [
        "# Duration atlas query",
        "",
        f"- status: `{result['status']}`",
        f"- mode: `{result['mode']}`",
        f"- matched case strata: {result['match']['case_strata']}",
        f"- displayed rows: {result['match']['displayed_rows']}",
        f"- truncated: `{str(result['truncation']['truncated']).lower()}`",
    ]
    if result.get("rows"):
        lines.extend(
            [
                "",
                "| Case / profile | Configuration | Runtime | Quality-pass user result | "
                "First artifact | Censoring | Evidence |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for row in result["rows"]:
            if "dimension" in row:
                lines.append(
                    f"| `{row['dimension']}` | "
                    f"`{_markdown_cell(json.dumps(row['value'], ensure_ascii=False))}` "
                    f"| case-strata={row['case_strata']} | - | - | - | coverage identifier |"
                )
                continue
            if "detail_reference" in row:
                lines.append(
                    f"| `{row['case_id']}@{row['case_revision']}` | audit | `{row['study_id']}` "
                    f"| - | - | - | `{row['detail_reference']}` |"
                )
                continue
            profile = row["profile"]
            configuration = row["configuration"]
            pass_duration = row["durations"].get("quality-pass-user-result")
            first_artifact = row["durations"].get("first-artifact-progress")
            censoring = row["censoring"]["counts"]
            lines.append(
                "| "
                f"`{row['case']['case_id']}@{row['case']['revision']}` "
                f"{profile['family']}/{profile['size']}/{profile['profile_id']} | "
                f"{configuration['relation']} workers={configuration['workers_actual']} | "
                f"{_participant_label(row['participants'])} | "
                f"{_duration_label(pass_duration)} | "
                f"{_duration_label(first_artifact)}; resolution="
                f"{json.dumps(row['evidence']['first_artifact_resolution'], sort_keys=True)} | "
                f"right={censoring['right-censored']} admin={censoring['administratively-censored']} "
                f"caps={row['censoring']['safety_caps_ms']} | "
                f"{row['evidence']['case_state']}; "
                f"{_quality_evidence_label(row['evidence']['quality_evidence'])}; "
                f"freshness={row['freshness']['status']} |"
            )
    if result.get("coverage"):
        coverage = result["coverage"]
        lines.extend(
            [
                "",
                f"Quality populations: `{json.dumps(coverage['quality_population'], sort_keys=True)}`",
                "",
                f"Censoring: `{json.dumps(coverage['censoring'], sort_keys=True)}`",
                "",
                "First-artifact resolution: "
                f"`{json.dumps(coverage['first_artifact_resolution'], sort_keys=True)}`",
                "",
                "Quality evidence: "
                f"`{json.dumps(coverage['quality_evidence'], sort_keys=True)}`",
            ]
        )
    if result.get("detail_references"):
        lines.extend(["", "Detail references:"])
        lines.extend(f"- `{item}`" for item in result["detail_references"])
    if result.get("refinement_hints"):
        lines.extend(["", "Refinement hints:"])
        for hint in result["refinement_hints"]:
            values = ", ".join(
                json.dumps(item, ensure_ascii=False) for item in hint["available_values"]
            )
            lines.append(f"- `{hint['filter']}`: {values}")
    if result["status"] == "unmeasured":
        lines.extend(["", "No exact measured stratum matched; no duration was interpolated."])
    lines.extend(["", "Observed evidence only; no decision policy was generated."])
    return "\n".join(lines) + "\n"


def _render_bytes(result: Mapping[str, Any], output_format: str) -> bytes:
    if output_format == "json":
        return _json_bytes(result)
    return render_markdown(result).encode("utf-8")


def _fit_output(
    result: dict[str, Any],
    *,
    output_format: str,
    max_output_bytes: int,
) -> dict[str, Any]:
    """Remove whole bounded units until the chosen rendering fits."""

    fitted = copy.deepcopy(result)
    while len(_render_bytes(fitted, output_format)) > max_output_bytes:
        if fitted["refinement_hints"]:
            fitted["refinement_hints"].pop()
        elif fitted["rows"]:
            fitted["rows"].pop()
            fitted["match"]["displayed_rows"] = len(fitted["rows"])
        elif fitted.get("detail_references"):
            fitted["detail_references"].pop()
        else:
            raise AtlasQueryError(
                "max-output-bytes is too small for the minimal explicit query result"
            )
        fitted["truncation"]["truncated"] = True
        if "max-output-bytes" not in fitted["truncation"]["reasons"]:
            fitted["truncation"]["reasons"].append("max-output-bytes")
    return fitted


def encode_result(result: Mapping[str, Any], output_format: str) -> bytes:
    if output_format not in FORMATS:
        raise AtlasQueryError("unknown query output format")
    return _render_bytes(result, output_format)


def _positive_argument(label: str, upper: int) -> Callable[[str], int]:
    def parse(raw: str) -> int:
        try:
            value = int(raw)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"{label} must be an integer") from exc
        if value < 1 or value > upper:
            raise argparse.ArgumentTypeError(f"{label} must be between 1 and {upper}")
        return value

    return parse


def _scalar(raw: str) -> Any:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        value = raw
    if value is None or isinstance(value, (list, dict)):
        raise argparse.ArgumentTypeError("setting value must be a string, number, or boolean")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("atlas", type=Path)
    parser.add_argument("--mode", choices=MODES, default="summary")
    parser.add_argument("--format", choices=FORMATS, default="json")
    parser.add_argument(
        "--max-rows",
        type=_positive_argument("max-rows", HARD_MAX_ROWS),
        required=True,
    )
    parser.add_argument(
        "--max-output-bytes",
        type=_positive_argument("max-output-bytes", HARD_MAX_OUTPUT_BYTES),
        required=True,
    )
    parser.add_argument("--family")
    parser.add_argument("--source-type")
    parser.add_argument("--size", choices=("S", "M", "L"))
    parser.add_argument("--profile")
    parser.add_argument("--case-id")
    parser.add_argument("--case-revision", type=int)
    parser.add_argument("--configuration-id")
    parser.add_argument("--relation")
    parser.add_argument("--participant-plan")
    parser.add_argument("--participants-actual", type=int)
    parser.add_argument("--workers-actual", type=int)
    parser.add_argument("--peak-concurrent", type=int)
    parser.add_argument("--nested-delegation")
    parser.add_argument("--independence-policy")
    parser.add_argument("--lane")
    parser.add_argument("--participant-role")
    parser.add_argument("--provider")
    parser.add_argument("--requested-model")
    parser.add_argument("--resolved-model")
    parser.add_argument("--identity-confidence")
    parser.add_argument("--setting-namespace")
    parser.add_argument("--setting-key")
    parser.add_argument("--setting-status", choices=SETTING_STATUSES)
    parser.add_argument("--setting-requested-value", type=_scalar)
    parser.add_argument("--setting-applied-value", type=_scalar)
    parser.add_argument("--cli-name")
    parser.add_argument("--cli-version")
    parser.add_argument("--cli-source")
    parser.add_argument("--execution-surface")
    parser.add_argument("--permission-mode")
    parser.add_argument("--runtime-image-digest")
    parser.add_argument("--study")
    parser.add_argument("--image-digest")
    parser.add_argument("--machine-class")
    parser.add_argument("--session-context")
    parser.add_argument("--repository-cache")
    parser.add_argument("--dependency-cache")
    parser.add_argument("--docker-cache")
    parser.add_argument("--provider-prompt-cache")
    parser.add_argument("--compaction")
    parser.add_argument("--competing-load")
    parser.add_argument("--timezone")
    parser.add_argument("--compare-by", action="append", choices=COMPARE_AXES, default=[])
    parser.add_argument("--curve-by", choices=CURVE_AXES, default="workers-actual")
    return parser


def _filters_from_args(args: argparse.Namespace) -> QueryFilters:
    environment = {
        target: getattr(args, source)
        for source, target in ENVIRONMENT_FILTERS.items()
        if getattr(args, source) is not None
    }
    return QueryFilters(
        source_type=args.source_type,
        family=args.family,
        size=args.size,
        profile=args.profile,
        case_id=args.case_id,
        case_revision=args.case_revision,
        configuration_id=args.configuration_id,
        relation=args.relation,
        participant_plan=args.participant_plan,
        participants_actual=args.participants_actual,
        workers_actual=args.workers_actual,
        peak_concurrent=args.peak_concurrent,
        nested_delegation=args.nested_delegation,
        independence_policy=args.independence_policy,
        lane=args.lane,
        participant_role=args.participant_role,
        provider=args.provider,
        requested_model=args.requested_model,
        resolved_model=args.resolved_model,
        identity_confidence=args.identity_confidence,
        setting_namespace=args.setting_namespace,
        setting_key=args.setting_key,
        setting_status=args.setting_status,
        setting_requested_value=args.setting_requested_value,
        setting_applied_value=args.setting_applied_value,
        cli_name=args.cli_name,
        cli_version=args.cli_version,
        cli_source=args.cli_source,
        execution_surface=args.execution_surface,
        permission_mode=args.permission_mode,
        runtime_image_digest=args.runtime_image_digest,
        study=args.study,
        environment=environment,
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        atlas = load_atlas(args.atlas)
        result = build_query_result(
            atlas,
            mode=args.mode,
            filters=_filters_from_args(args),
            max_rows=args.max_rows,
            max_output_bytes=args.max_output_bytes,
            compare_by=args.compare_by,
            curve_by=args.curve_by,
            output_format=args.format,
        )
        encoded = encode_result(result, args.format)
        if len(encoded) > args.max_output_bytes:
            raise AtlasQueryError("query output exceeds max-output-bytes")
        sys.stdout.buffer.write(encoded)
    except (AtlasQueryError, AtlasError, ContractValidationError, OSError) as exc:
        print(f"duration atlas query failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Build deterministic, provider-free, finite C0 duration batch manifests."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
import re
from typing import Any, Iterable

from agent_contracts import ContractValidationError, load_json
from agent_duration_batch import PROVIDER_EFFORTS
from agent_duration_study import (
    DurationStudyError,
    ROOT,
    canonical_json_digest,
    validate_case_catalog_record,
    validate_record,
)


DEFAULT_CATALOG = ROOT / "experiments" / "multi-agent-duration" / "catalog" / "cases.json"
HARD_MAX_RUNS = 36
SIZE_ORDER = ("S", "M", "L")
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
PURPOSE_PREFIX = "finite explicit C0 observations"


@dataclass(frozen=True)
class Series:
    provider: str
    model: str
    effort: str


def _require_identifier(value: str, label: str) -> None:
    if ID.fullmatch(value) is None:
        raise DurationStudyError(f"{label} must match the batch identifier contract")


def _stable_key(seed: int, *parts: str) -> str:
    encoded = "\x00".join((str(seed), *parts)).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _rotate(values: list[Any], offset: int) -> list[Any]:
    if not values:
        return []
    chosen = offset % len(values)
    return [*values[chosen:], *values[:chosen]]


def _case_interleave(cases: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    """Round-robin S/M/L after a seeded size rotation and stable in-size ordering."""

    by_size: dict[str, list[dict[str, Any]]] = {size: [] for size in SIZE_ORDER}
    for case in cases:
        by_size[case["size"]].append(case)
    for size in SIZE_ORDER:
        by_size[size].sort(
            key=lambda item: (
                _stable_key(seed, size, item["case_id"]),
                item["case_id"],
            )
        )
    size_cycle = _rotate(list(SIZE_ORDER), seed)
    output: list[dict[str, Any]] = []
    index = 0
    while any(index < len(by_size[size]) for size in size_cycle):
        for size in size_cycle:
            if index < len(by_size[size]):
                output.append(by_size[size][index])
        index += 1
    return output


def _validated_series(series: Iterable[Series]) -> list[Series]:
    values = list(series)
    if not values:
        raise DurationStudyError("at least one explicit provider/model/effort series is required")
    seen: set[Series] = set()
    for item in values:
        if item.provider not in PROVIDER_EFFORTS:
            raise DurationStudyError(f"unknown duration provider: {item.provider}")
        _require_identifier(item.model, "model")
        if item.effort not in PROVIDER_EFFORTS[item.provider]:
            raise DurationStudyError(
                f"effort is unsupported by provider surface: {item.provider}/{item.effort}"
            )
        if item in seen:
            raise DurationStudyError(
                f"duplicate explicit series: {item.provider}/{item.model}/{item.effort}"
            )
        seen.add(item)
    return values


def _selected_cases(
    catalog: dict[str, Any],
    *,
    case_ids: Iterable[str],
    families: Iterable[str],
    sizes: Iterable[str],
) -> list[dict[str, Any]]:
    requested_cases = set(case_ids)
    requested_families = set(families)
    requested_sizes = set(sizes)
    if not (requested_cases or requested_families or requested_sizes):
        raise DurationStudyError(
            "at least one explicit case, family, or size filter is required; refusing implicit full catalog"
        )
    cases = [entry["case"] for entry in catalog["entries"]]
    known_cases = {case["case_id"] for case in cases}
    known_families = {case["family"] for case in cases}
    unknown_cases = sorted(requested_cases - known_cases)
    unknown_families = sorted(requested_families - known_families)
    unknown_sizes = sorted(requested_sizes - set(SIZE_ORDER))
    if unknown_cases:
        raise DurationStudyError(f"unknown case filter: {', '.join(unknown_cases)}")
    if unknown_families:
        raise DurationStudyError(f"unknown family filter: {', '.join(unknown_families)}")
    if unknown_sizes:
        raise DurationStudyError(f"unknown size filter: {', '.join(unknown_sizes)}")
    selected = [
        case
        for case in cases
        if (not requested_cases or case["case_id"] in requested_cases)
        and (not requested_families or case["family"] in requested_families)
        and (not requested_sizes or case["size"] in requested_sizes)
    ]
    if not selected:
        raise DurationStudyError("duration case filters have an empty intersection")
    return selected


def _run_id(
    *,
    batch_id: str,
    study_id: str,
    block_id: str,
    case_id: str,
    series: Series,
    repetition: int,
    order: int,
) -> str:
    digest = _stable_key(
        0,
        batch_id,
        study_id,
        block_id,
        case_id,
        series.provider,
        series.model,
        series.effort,
        str(repetition),
    )[:16]
    return f"run-{order:03d}-{digest}"


def plan_batch(
    catalog: dict[str, Any],
    *,
    batch_id: str,
    study_id: str,
    block_id: str,
    series: Iterable[Series],
    case_ids: Iterable[str] = (),
    families: Iterable[str] = (),
    sizes: Iterable[str] = (),
    rotation_seed: int,
    repeat: int,
    max_runs: int,
    deadline_seconds: float,
    timeout_seconds: float,
    evaluator_timeout_seconds: float,
    output_bytes_cap: int,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Return one validated batch manifest without contacting a provider."""

    validate_case_catalog_record(catalog)
    for value, label in (
        (batch_id, "batch_id"),
        (study_id, "study_id"),
        (block_id, "block_id"),
    ):
        _require_identifier(value, label)
    if (
        not isinstance(rotation_seed, int)
        or isinstance(rotation_seed, bool)
        or not 0 <= rotation_seed <= 2**63 - 1
    ):
        raise DurationStudyError("rotation_seed must be an unsigned 63-bit integer")
    if not isinstance(repeat, int) or isinstance(repeat, bool) or repeat < 1:
        raise DurationStudyError("repeat must be an explicit positive integer")
    if not isinstance(max_runs, int) or isinstance(max_runs, bool) or not 1 <= max_runs <= HARD_MAX_RUNS:
        raise DurationStudyError(f"max_runs must be between 1 and {HARD_MAX_RUNS}")
    for value, label, upper in (
        (deadline_seconds, "deadline_seconds", 604800),
        (timeout_seconds, "timeout_seconds", 3600),
        (evaluator_timeout_seconds, "evaluator_timeout_seconds", 300),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value <= 0
            or value > upper
        ):
            raise DurationStudyError(f"{label} must be > 0 and <= {upper}")
    if deadline_seconds < timeout_seconds + evaluator_timeout_seconds:
        raise DurationStudyError(
            "deadline_seconds cannot fit one declared provider plus evaluator timeout budget"
        )
    if (
        not isinstance(output_bytes_cap, int)
        or isinstance(output_bytes_cap, bool)
        or not 1024 <= output_bytes_cap <= 67108864
    ):
        raise DurationStudyError("output_bytes_cap must be between 1024 and 67108864")

    explicit_series = _validated_series(series)
    selected = _selected_cases(
        catalog,
        case_ids=case_ids,
        families=families,
        sizes=sizes,
    )
    planned_count = len(selected) * len(explicit_series) * repeat
    if planned_count > HARD_MAX_RUNS:
        raise DurationStudyError(
            f"planned run count {planned_count} exceeds hard C0 planner cap {HARD_MAX_RUNS}"
        )
    if planned_count > max_runs:
        raise DurationStudyError(
            f"planned run count {planned_count} exceeds explicit max_runs {max_runs}"
        )

    entries: list[dict[str, Any]] = []
    for repetition in range(1, repeat + 1):
        ordered_cases = _case_interleave(selected, rotation_seed + repetition - 1)
        for case_index, case in enumerate(ordered_cases):
            ordered_series = _rotate(
                explicit_series,
                rotation_seed + repetition - 1 + case_index,
            )
            for item in ordered_series:
                order = len(entries) + 1
                entries.append(
                    {
                        "order": order,
                        "run_id": _run_id(
                            batch_id=batch_id,
                            study_id=study_id,
                            block_id=block_id,
                            case_id=case["case_id"],
                            series=item,
                            repetition=repetition,
                            order=order,
                        ),
                        "block_id": block_id,
                        "case_id": case["case_id"],
                        "provider": item.provider,
                        "model": item.model,
                        "effort": item.effort,
                        "timeout_seconds": timeout_seconds,
                        "evaluator_timeout_seconds": evaluator_timeout_seconds,
                        "output_bytes_cap": output_bytes_cap,
                    }
                )

    run_ids = [entry["run_id"] for entry in entries]
    if len(run_ids) != len(set(run_ids)):
        raise DurationStudyError("deterministic planner produced duplicate run IDs")
    manifest = {
        "schema_version": 1,
        "batch_id": batch_id,
        "study_id": study_id,
        "catalog_digest": canonical_json_digest(catalog),
        "created_at": created_at or catalog["published_at"],
        "purpose": (
            f"{PURPOSE_PREFIX}; repeat={repeat}; rotation-seed={rotation_seed}; "
            "no routing recommendation or default winner"
        ),
        "safety": {
            "max_runs": max_runs,
            "deadline_seconds": deadline_seconds,
            "concurrency": 1,
            "automatic_retry": False,
            "continue_after_quality_fail": True,
        },
        "entries": entries,
    }
    try:
        validate_record("batch", manifest)
    except ContractValidationError as exc:
        raise DurationStudyError(f"planned batch violates batch schema: {exc}") from exc
    return manifest


def plan_batch_from_catalog(
    catalog_path: Path,
    **kwargs: Any,
) -> dict[str, Any]:
    catalog = load_json(catalog_path)
    if not isinstance(catalog, dict):
        raise DurationStudyError("duration catalog root must be an object")
    return plan_batch(catalog, **kwargs)


__all__ = [
    "DEFAULT_CATALOG",
    "HARD_MAX_RUNS",
    "Series",
    "plan_batch",
    "plan_batch_from_catalog",
]

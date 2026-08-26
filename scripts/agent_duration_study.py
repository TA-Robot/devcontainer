#!/usr/bin/env python3
"""Dependency-free contracts and deterministic clocks for duration studies."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from agent_contracts import ContractValidationError, load_json, validate


ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "experiments" / "multi-agent-duration" / "schemas"
SCHEMA_PATHS = {
    "study": SCHEMA_DIR / "study.schema.json",
    "case": SCHEMA_DIR / "case.schema.json",
    "case-catalog": SCHEMA_DIR / "case-catalog.schema.json",
    "capability": SCHEMA_DIR / "capability.schema.json",
    "fixture": SCHEMA_DIR / "fixture.schema.json",
    "run": SCHEMA_DIR / "run.schema.json",
}
LANDMARK_NAMES = (
    "P0",
    "P1",
    "T0",
    "T1",
    "T2",
    "T3",
    "T4",
    "V0",
    "V1",
    "T6",
    "S0",
    "S1",
    "TX",
)
MISSING_EVENT_STATUSES = {"not-applicable", "not-observed", "unknown"}


class DurationStudyError(ValueError):
    """Raised when a duration-study record is semantically invalid."""


class EventClock(Protocol):
    def snapshot(self) -> tuple[str, int]:
        """Return a UTC timestamp and monotonic nanoseconds for one event."""


def utc_timestamp(value: datetime) -> str:
    normalized = value.astimezone(timezone.utc)
    return normalized.isoformat(timespec="milliseconds").replace("+00:00", "Z")


class SystemClock:
    def snapshot(self) -> tuple[str, int]:
        return utc_timestamp(datetime.now(timezone.utc)), time.monotonic_ns()


class FakeClock:
    """A deterministic wall/monotonic clock that never sleeps."""

    def __init__(
        self,
        *,
        wall_start: datetime | None = None,
        monotonic_start_ns: int = 1_000_000_000,
    ) -> None:
        self.wall_start = wall_start or datetime(2026, 1, 1, tzinfo=timezone.utc)
        if self.wall_start.tzinfo is None:
            raise DurationStudyError("fake wall clock must be timezone-aware")
        if monotonic_start_ns < 0:
            raise DurationStudyError("fake monotonic clock must be non-negative")
        self.monotonic_start_ns = monotonic_start_ns
        self.monotonic_ns = monotonic_start_ns

    def advance_ms(self, milliseconds: int) -> None:
        if milliseconds < 0:
            raise DurationStudyError("fake clock cannot move backwards")
        self.monotonic_ns += milliseconds * 1_000_000

    def snapshot(self) -> tuple[str, int]:
        elapsed = self.monotonic_ns - self.monotonic_start_ns
        wall = self.wall_start + timedelta(microseconds=elapsed / 1_000)
        return utc_timestamp(wall), self.monotonic_ns


def event(clock: EventClock, *, provenance: str = "observed") -> dict[str, Any]:
    wall_time, monotonic_ns = clock.snapshot()
    return {
        "status": "observed",
        "wall_time": wall_time,
        "monotonic_ns": monotonic_ns,
        "provenance": provenance,
    }


def missing_event(status: str, *, provenance: str = "declared-by-harness") -> dict[str, str]:
    if status not in MISSING_EVENT_STATUSES:
        raise DurationStudyError(f"invalid missing event status: {status}")
    return {"status": status, "provenance": provenance}


def observed_ns(value: dict[str, Any] | None) -> int | None:
    if not isinstance(value, dict) or value.get("status") != "observed":
        return None
    monotonic_ns = value.get("monotonic_ns")
    if not isinstance(monotonic_ns, int) or isinstance(monotonic_ns, bool):
        raise DurationStudyError("observed event is missing integer monotonic_ns")
    return monotonic_ns


def elapsed_ms(start_ns: int, finish_ns: int, label: str) -> float:
    if finish_ns < start_ns:
        raise DurationStudyError(f"{label} has negative duration")
    return round((finish_ns - start_ns) / 1_000_000, 3)


def _landmark_ns(record: dict[str, Any], name: str) -> int | None:
    return observed_ns(record.get("landmarks", {}).get(name))


def _worker_intervals(record: dict[str, Any]) -> list[tuple[int, int]] | None:
    intervals: list[tuple[int, int]] = []
    for worker in record.get("workers", []):
        start_ns = observed_ns(worker.get("start"))
        stop_ns = observed_ns(worker.get("stop"))
        if start_ns is None or stop_ns is None:
            return None
        if stop_ns < start_ns:
            raise DurationStudyError(f"worker {worker.get('worker_id', '<unknown>')} stops before start")
        intervals.append((start_ns, stop_ns))
    return intervals


def interval_union_ms(intervals: list[tuple[int, int]]) -> float:
    nonempty = sorted((start, stop) for start, stop in intervals if stop > start)
    if not nonempty:
        return 0.0
    merged: list[list[int]] = []
    for start, stop in nonempty:
        if not merged or start > merged[-1][1]:
            merged.append([start, stop])
        else:
            merged[-1][1] = max(merged[-1][1], stop)
    total_ns = sum(stop - start for start, stop in merged)
    return round(total_ns / 1_000_000, 3)


def peak_concurrency(intervals: list[tuple[int, int]]) -> int:
    changes: list[tuple[int, int]] = []
    for start, stop in intervals:
        if stop <= start:
            continue
        changes.append((start, 1))
        changes.append((stop, -1))
    active = 0
    peak = 0
    for _, delta in sorted(changes, key=lambda item: (item[0], 0 if item[1] < 0 else 1)):
        active += delta
        if active < 0:
            raise DurationStudyError("worker concurrency became negative")
        peak = max(peak, active)
    return peak


def observed_peak_concurrency(workers: list[dict[str, Any]]) -> int:
    """Compute peak starts/stops even when a worker has no observed stop."""

    changes: list[tuple[int, int]] = []
    for worker in workers:
        start_ns = observed_ns(worker.get("start"))
        if start_ns is None:
            continue
        changes.append((start_ns, 1))
        stop_ns = observed_ns(worker.get("stop"))
        if stop_ns is not None:
            if stop_ns < start_ns:
                raise DurationStudyError(f"worker {worker.get('worker_id')} stops before start")
            if stop_ns > start_ns:
                changes.append((stop_ns, -1))
            else:
                changes.pop()
    active = 0
    peak = 0
    for _, delta in sorted(changes, key=lambda item: (item[0], 0 if item[1] < 0 else 1)):
        active += delta
        if active < 0:
            raise DurationStudyError("observed worker concurrency became negative")
        peak = max(peak, active)
    return peak


def derive_durations(record: dict[str, Any]) -> dict[str, float]:
    """Derive only durations whose required observed events exist."""

    values: dict[str, float] = {}

    def add(name: str, start: str, finish: str) -> None:
        start_ns = _landmark_ns(record, start)
        finish_ns = _landmark_ns(record, finish)
        if start_ns is not None and finish_ns is not None:
            values[name] = elapsed_ms(start_ns, finish_ns, name)

    add("provision", "P0", "P1")
    add("dispatch_delay", "T0", "T1")
    add("first_artifact_latency", "T0", "T2")
    add("required_workers_ready", "T0", "T3")
    add("synthesis_tail", "T3", "T4")
    add("online_validation", "V0", "V1")
    add("post_validation_tail", "V1", "T6")
    add("user_result", "T0", "T6")
    add("terminal_wall", "T0", "TX")
    add("offline_scoring", "S0", "S1")

    intervals = _worker_intervals(record)
    if intervals is not None:
        values["aggregate_worker"] = round(
            sum(stop - start for start, stop in intervals) / 1_000_000,
            3,
        )
        values["worker_active_union"] = interval_union_ms(intervals)
        if intervals:
            first_start = min(start for start, _ in intervals)
            last_stop = max(stop for _, stop in intervals)
            values["worker_terminal_span"] = elapsed_ms(
                first_start,
                last_stop,
                "worker_terminal_span",
            )

    if "terminal_wall" not in values:
        raise DurationStudyError("T0 and TX must be observed to derive terminal_wall")
    return values


def canonical_quality_pass(
    *,
    online_acceptance: str,
    offline_score: str,
    strong_online_oracle: bool,
) -> tuple[bool | None, str]:
    """Apply the canonical quality-conditioned population rule."""

    if online_acceptance == "fail":
        return False, "online-fail"
    if offline_score in {"pass", "fail"}:
        return offline_score == "pass", "offline-score"
    if strong_online_oracle and online_acceptance == "pass":
        return True, "strong-online-oracle"
    return None, "unavailable"


def load_schema(kind: str) -> dict[str, Any]:
    if kind not in SCHEMA_PATHS:
        raise DurationStudyError(f"unknown duration-study schema: {kind}")
    schema = load_json(SCHEMA_PATHS[kind])
    if not isinstance(schema, dict):
        raise DurationStudyError(f"schema root must be an object: {SCHEMA_PATHS[kind]}")
    return schema


def content_digest(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def canonical_json_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return content_digest(encoded)


def validate_case_catalog_record(
    record: dict[str, Any],
    *,
    repository_root: Path = ROOT,
) -> None:
    validate(record, load_schema("case-catalog"))
    case_ids: list[str] = []
    recipe_ids: list[str] = []
    capsule_paths: list[str] = []
    resolved_root = repository_root.resolve()
    for entry in record["entries"]:
        case = entry["case"]
        validate_record("case", case)
        fixture = entry["fixture"]
        case_id = case["case_id"]
        if fixture["case_id"] != case_id:
            raise DurationStudyError(f"fixture case_id does not match case: {case_id}")
        if case["source_type"] != "fixture":
            raise DurationStudyError(f"catalog fixture entry must use fixture source_type: {case_id}")
        if not case["strong_online_oracle"]:
            raise DurationStudyError(
                f"initial calibration fixture requires a strong online oracle: {case_id}"
            )

        raw_capsule_path = fixture["capsule_path"]
        capsule_path = Path(raw_capsule_path)
        if capsule_path.is_absolute() or ".." in capsule_path.parts:
            raise DurationStudyError(f"unsafe capsule path for {case_id}: {raw_capsule_path}")
        resolved_capsule = (resolved_root / capsule_path).resolve()
        try:
            resolved_capsule.relative_to(resolved_root)
        except ValueError as exc:
            raise DurationStudyError(f"capsule escapes repository root: {case_id}") from exc
        if not resolved_capsule.is_file():
            raise DurationStudyError(f"capsule does not exist for {case_id}: {raw_capsule_path}")
        actual_capsule_digest = content_digest(resolved_capsule.read_bytes())
        if case["capsule_digest"] != actual_capsule_digest:
            raise DurationStudyError(
                f"capsule digest mismatch for {case_id}: expected {actual_capsule_digest}"
            )
        hidden_targets = fixture["hidden_validation_targets"]
        hidden_check_ids = [item["check_id"] for item in hidden_targets]
        hidden_test_targets = [item["test_target"] for item in hidden_targets]
        if len(hidden_check_ids) != len(set(hidden_check_ids)):
            raise DurationStudyError(f"hidden check IDs must be unique for {case_id}")
        if len(hidden_test_targets) != len(set(hidden_test_targets)):
            raise DurationStudyError(f"hidden test targets must be unique for {case_id}")

        case_ids.append(case_id)
        recipe_ids.append(fixture["recipe_id"])
        capsule_paths.append(raw_capsule_path)

    if len(case_ids) != len(set(case_ids)):
        raise DurationStudyError("case catalog IDs must be unique")
    if len(recipe_ids) != len(set(recipe_ids)):
        raise DurationStudyError("fixture recipe IDs must be unique")
    if len(capsule_paths) != len(set(capsule_paths)):
        raise DurationStudyError("fixture capsule paths must be unique")


def _validate_relative_manifest_path(raw_path: str, label: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise DurationStudyError(f"unsafe fixture {label} path: {raw_path}")
    return path


def validate_fixture_record(record: dict[str, Any]) -> None:
    validate(record, load_schema("fixture"))
    paths = {
        key: _validate_relative_manifest_path(value, key)
        for key, value in record["paths"].items()
    }
    if paths["workspace"] != Path("workspace"):
        raise DurationStudyError("fixture workspace path must be exactly 'workspace'")
    for label in ("bundle", "hidden_evaluator"):
        if paths["workspace"] == paths[label] or paths["workspace"] in paths[label].parents:
            raise DurationStudyError(f"fixture {label} must remain outside the agent workspace")

    workspace_files = record["workspace_files"]
    if workspace_files != sorted(workspace_files):
        raise DurationStudyError("fixture workspace file inventory must be sorted")
    for raw_path in workspace_files:
        path = _validate_relative_manifest_path(raw_path, "workspace file")
        if path.parts[0] == ".git":
            raise DurationStudyError("fixture workspace inventory must not expose Git internals")

    initial_oracle = record["initial_oracle"]
    checks = [*initial_oracle["workspace_checks"], *initial_oracle["hidden_checks"]]
    check_ids = [item["check_id"] for item in checks]
    if len(check_ids) != len(set(check_ids)):
        raise DurationStudyError("fixture oracle check IDs must be unique")
    expected_hidden_ids = [
        item["check_id"] for item in record["execution_contract"]["hidden_validation_targets"]
    ]
    observed_hidden_ids = [item["check_id"] for item in initial_oracle["hidden_checks"]]
    if observed_hidden_ids != expected_hidden_ids:
        raise DurationStudyError("fixture hidden oracle checks do not match the execution contract")
    for check in checks:
        expected_status = "pass" if check["exit_code"] == 0 else "fail"
        if check["status"] != expected_status:
            raise DurationStudyError("fixture check status disagrees with exit_code")
    expected_observed = "pass" if all(item["status"] == "pass" for item in checks) else "fail"
    if initial_oracle["observed"] != expected_observed:
        raise DurationStudyError("fixture initial oracle summary disagrees with checks")
    if initial_oracle["observed"] != "fail":
        raise DurationStudyError("seeded calibration fixture must initially fail its oracle")


def _validate_utc_timestamps(record: dict[str, Any]) -> None:
    for name, value in record.get("landmarks", {}).items():
        if value.get("status") != "observed":
            continue
        raw = value["wall_time"]
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            raise DurationStudyError(f"landmark {name} has invalid UTC timestamp") from exc
        if parsed.utcoffset() != timedelta(0):
            raise DurationStudyError(f"landmark {name} must use UTC")


def _validate_provenance(record: dict[str, Any]) -> None:
    owners: dict[str, str] = {}
    for category, pointers in record["field_provenance"].items():
        for pointer in pointers:
            previous = owners.get(pointer)
            if previous is not None:
                raise DurationStudyError(
                    f"field provenance pointer {pointer!r} appears in {previous} and {category}"
                )
            owners[pointer] = category


def _validate_model_and_settings(
    model_identity: dict[str, Any],
    settings: list[dict[str, Any]],
) -> None:
    confidence = model_identity["identity_confidence"]
    if confidence != "exact" and "resolved_id" in model_identity:
        raise DurationStudyError("resolved_id requires exact model identity confidence")
    setting_keys = [(setting["namespace"], setting["key"]) for setting in settings]
    if len(setting_keys) != len(set(setting_keys)):
        raise DurationStudyError("generation setting keys must be unique")
    for setting in settings:
        if setting["status"] != "applied" and "applied_value" in setting:
            raise DurationStudyError("only an applied setting may contain applied_value")


def _validate_capability_record(record: dict[str, Any]) -> None:
    validate(record, load_schema("capability"))
    _validate_model_and_settings(record["model_identity"], record["setting_probes"])

    if record["observed_at"] != record["runtime_identity"]["observed_at"]:
        raise DurationStudyError("capability and runtime observation timestamps must match")

    commands = record["probe"]["commands"]
    command_ids = [item["command_id"] for item in commands]
    if len(command_ids) != len(set(command_ids)):
        raise DurationStudyError("capability probe command IDs must be unique")
    for command in commands:
        status = command["status"]
        exit_code = command.get("exit_code")
        if status == "observed" and exit_code != 0:
            raise DurationStudyError("an observed probe command requires exit_code 0")
        if status == "failed" and (exit_code is None or exit_code == 0):
            raise DurationStudyError("a failed probe command requires a nonzero exit_code")
        if status in {"unavailable", "timed-out"} and exit_code is not None:
            raise DurationStudyError(f"a {status} probe command cannot have an exit_code")

    probe = record["probe"]
    metadata_requested = probe["provider_metadata_request_attempted"]
    if metadata_requested != (probe["metadata_scope"] == "provider-current"):
        raise DurationStudyError("provider metadata request flag disagrees with metadata_scope")
    if probe["mode"] == "passive-cli":
        if probe["generation_request_performed"]:
            raise DurationStudyError("a passive capability probe cannot perform generation")
        if record["setting_probes"]:
            raise DurationStudyError("a passive capability probe cannot claim applied settings")
        if record["coverage"]["setting_application"] != "not-observed":
            raise DurationStudyError("passive setting application coverage must be not-observed")
        if record["runtime_identity"]["execution_surface"] != "capability-probe":
            raise DurationStudyError("a passive probe must use the capability-probe surface")

    inventory = record["model_inventory"]
    inventory_ids = [item["model_id"] for item in inventory]
    if len(inventory_ids) != len(set(inventory_ids)):
        raise DurationStudyError("model inventory IDs must be unique")
    defaults = [item for item in inventory if item["catalog_status"] == "advertised-default"]
    if len(defaults) > 1:
        raise DurationStudyError("model inventory can advertise at most one default")
    for item in inventory:
        if item["identity_confidence"] == "catalog-id-with-snapshot":
            if "snapshot_hint" not in item:
                raise DurationStudyError("catalog snapshot confidence requires snapshot_hint")
        elif "snapshot_hint" in item:
            raise DurationStudyError("snapshot_hint requires catalog-id-with-snapshot confidence")

    model_identity = record["model_identity"]
    if defaults and model_identity["identity_confidence"] == "alias-only":
        if model_identity["requested_alias"] != defaults[0]["model_id"]:
            raise DurationStudyError("runtime default identity disagrees with advertised default")

    surfaces = record["setting_surfaces"]
    surface_keys = [
        (item["namespace"], item["key"], item.get("model_selector")) for item in surfaces
    ]
    if len(surface_keys) != len(set(surface_keys)):
        raise DurationStudyError("setting surface keys must be unique per model selector")
    inventory_id_set = set(inventory_ids)
    for surface in surfaces:
        selector = surface.get("model_selector")
        if selector is not None and selector not in inventory_id_set:
            raise DurationStudyError(f"setting surface references unknown model: {selector}")
        advertised_values = surface.get("advertised_values")
        default_value = surface.get("default_value")
        if surface["advertisement"] == "enumerated":
            if not advertised_values:
                raise DurationStudyError("enumerated setting surface requires advertised_values")
            if default_value is not None and default_value not in advertised_values:
                raise DurationStudyError("setting default_value must be one of advertised_values")
        elif advertised_values is not None or default_value is not None:
            raise DurationStudyError(
                "only an enumerated setting surface may contain advertised/default values"
            )

    coverage = record["coverage"]
    if inventory and coverage["model_inventory"] in {"not-observed", "unknown"}:
        raise DurationStudyError("observed model inventory cannot have missing coverage")
    if not inventory and coverage["model_inventory"] in {"exact", "partial"}:
        raise DurationStudyError("model inventory coverage requires at least one model")
    if surfaces and coverage["setting_advertisement"] in {"not-observed", "unknown"}:
        raise DurationStudyError("observed setting surfaces cannot have missing coverage")
    if not surfaces and coverage["setting_advertisement"] in {"exact", "partial"}:
        raise DurationStudyError("setting advertisement coverage requires a surface")
    if record["setting_probes"] and coverage["setting_application"] in {
        "not-observed",
        "unknown",
    }:
        raise DurationStudyError("setting probes cannot have missing application coverage")
    if not record["setting_probes"] and coverage["setting_application"] in {
        "exact",
        "partial",
    }:
        raise DurationStudyError("setting application coverage requires an actual probe")


def validate_run_record(record: dict[str, Any]) -> None:
    validate(record, load_schema("run"))
    _validate_utc_timestamps(record)
    _validate_provenance(record)

    expected_durations = derive_durations(record)
    if record["durations_ms"] != expected_durations:
        raise DurationStudyError(
            "durations_ms does not match observed events: "
            f"expected {expected_durations!r}, got {record['durations_ms']!r}"
        )

    expected_quality, expected_basis = canonical_quality_pass(
        online_acceptance=record["outcome"]["online_acceptance"],
        offline_score=record["outcome"]["offline_score"],
        strong_online_oracle=record["case"]["strong_online_oracle"],
    )
    if record["outcome"]["quality_pass"] != expected_quality:
        raise DurationStudyError("outcome.quality_pass does not match canonical quality rule")
    if record["outcome"]["quality_basis"] != expected_basis:
        raise DurationStudyError("outcome.quality_basis does not match canonical quality rule")

    participant_ids = [item["participant_id"] for item in record["participants"]]
    if len(participant_ids) != len(set(participant_ids)):
        raise DurationStudyError("participant IDs must be unique")
    for participant in record["participants"]:
        _validate_model_and_settings(
            participant["model_identity"],
            participant["generation_settings"],
        )
    worker_ids = [item["worker_id"] for item in record["workers"]]
    if len(worker_ids) != len(set(worker_ids)):
        raise DurationStudyError("worker IDs must be unique")
    for worker in record["workers"]:
        parent = worker.get("parent_worker_id")
        if parent == worker["worker_id"]:
            raise DurationStudyError("worker cannot be its own parent")
        if parent is not None and parent not in worker_ids:
            raise DurationStudyError(f"worker parent is not tracked: {parent}")

    configuration = record["configuration"]
    if configuration["participants_actual"] != len(record["participants"]):
        raise DurationStudyError("participants_actual does not match participants")
    if configuration["workers_actual"] != len(record["workers"]):
        raise DurationStudyError("workers_actual does not match workers")

    intervals = _worker_intervals(record)
    if intervals is not None and configuration["peak_concurrent"] != peak_concurrency(intervals):
        raise DurationStudyError("peak_concurrent does not match worker intervals")

    t3_ns = _landmark_ns(record, "T3")
    required_stops = [
        observed_ns(worker["stop"])
        for worker in record["workers"]
        if worker["required_for_result"]
    ]
    if t3_ns is not None and required_stops and all(value is not None for value in required_stops):
        if t3_ns < max(value for value in required_stops if value is not None):
            raise DurationStudyError("T3 precedes a required worker stop")

    t6_ns = _landmark_ns(record, "T6")
    tx_ns = _landmark_ns(record, "TX")
    if t6_ns is not None and tx_ns is not None and tx_ns < t6_ns:
        raise DurationStudyError("TX precedes user result T6")
    if record["outcome"]["infrastructure"] == "success" and t6_ns is None:
        raise DurationStudyError("successful run requires observed T6")

    if record["outcome"]["online_acceptance"] == "pass" and record["outcome"]["artifact"] != "valid":
        raise DurationStudyError("online acceptance pass requires a valid artifact")
    if record["outcome"]["quality_pass"] is True and record["outcome"]["artifact"] != "valid":
        raise DurationStudyError("quality pass requires a valid artifact")
    offline_score = record["outcome"]["offline_score"]
    if offline_score in {"pass", "fail", "partial"}:
        if _landmark_ns(record, "S0") is None or _landmark_ns(record, "S1") is None:
            raise DurationStudyError("offline score requires observed S0 and S1")
        if record["quality"]["evaluator_id"] is None:
            raise DurationStudyError("offline score requires evaluator_id")
    if offline_score == "not-run":
        if _landmark_ns(record, "S0") is not None or _landmark_ns(record, "S1") is not None:
            raise DurationStudyError("offline score not-run cannot have observed S0/S1")
        if record["quality"]["metrics"]:
            raise DurationStudyError("offline score not-run cannot have quality metrics")

    nested = record["coverage"]["nested_worker_detected"]
    nested_policy = configuration["nested_delegation"]
    worker_tree = record["coverage"]["worker_tree"]
    if nested and nested_policy == "disabled":
        raise DurationStudyError("nested worker detected while nested delegation is disabled")
    if nested_policy == "detected-untracked" and (not nested or worker_tree != "lower-bound"):
        raise DurationStudyError("untracked nested delegation requires lower-bound coverage")

    expected_first_artifact = record["landmarks"].get(
        "T2", {"status": "not-observed"}
    )["status"]
    if expected_first_artifact == "observed":
        expected_first_artifact = "progress-envelope"
    if record["coverage"]["first_artifact_resolution"] != expected_first_artifact:
        raise DurationStudyError("first artifact coverage does not match T2")

    expected_synthesis = record["landmarks"].get(
        "T4", {"status": "not-observed"}
    )["status"]
    if expected_synthesis == "observed":
        expected_synthesis = "explicit-envelope"
    if record["coverage"]["synthesis_resolution"] != expected_synthesis:
        raise DurationStudyError("synthesis coverage does not match T4")

    expected_landmarks = [
        name
        for name in LANDMARK_NAMES
        if record["landmarks"].get(name, {}).get("status") == "observed"
    ]
    if record["coverage"]["clock_landmarks"] != expected_landmarks:
        raise DurationStudyError("clock landmark coverage is not canonical")

    if intervals is None:
        expected_worker_tree = "untracked"
    elif nested_policy == "detected-untracked":
        expected_worker_tree = "lower-bound"
    else:
        expected_worker_tree = "exact"
    if worker_tree != expected_worker_tree:
        raise DurationStudyError("worker tree coverage does not match observed worker intervals")

    diagnostics = record["diagnostics"]
    provider = diagnostics["provider"]
    provider_names = [item["name"] for item in provider["event_counts"]]
    if len(provider_names) != len(set(provider_names)):
        raise DurationStudyError("provider event diagnostic names must be unique")
    item_names = [item["name"] for item in provider["item_type_counts"]]
    if len(item_names) != len(set(item_names)):
        raise DurationStudyError("provider item diagnostic names must be unique")

    expected_provider_status = {
        "success": "success",
        "failure": "failure",
        "timeout": "timeout",
    }.get(record["outcome"]["infrastructure"])
    if expected_provider_status is not None and provider["status"] != expected_provider_status:
        raise DurationStudyError("provider diagnostic status disagrees with run infrastructure")
    if provider["sandbox_preflight"]["image_digest"] != record["environment"]["image_digest"]:
        raise DurationStudyError("sandbox preflight image differs from the run environment")
    for participant in record["participants"]:
        runtime_image = participant["runtime_identity"].get("image_digest")
        if runtime_image is not None and runtime_image != record["environment"]["image_digest"]:
            raise DurationStudyError("participant runtime image differs from the run environment")

    evaluator = diagnostics["evaluator"]
    check_ids = [item["check_id"] for item in evaluator["checks"]]
    if len(check_ids) != len(set(check_ids)):
        raise DurationStudyError("evaluator diagnostic check IDs must be unique")
    for check in evaluator["checks"]:
        expected_status = "pass" if check["exit_code"] == 0 else "fail"
        if check["status"] != expected_status:
            raise DurationStudyError("evaluator check status disagrees with exit_code")
    score = evaluator.get("score")
    if score is not None:
        checks = evaluator["checks"]
        if not checks:
            raise DurationStudyError("evaluator score requires checks")
        if score["total"] != len(checks):
            raise DurationStudyError("evaluator score total disagrees with checks")
        passed = sum(item["status"] == "pass" for item in checks)
        if score["passed"] != passed:
            raise DurationStudyError("evaluator score passed count disagrees with checks")
        if score["ratio"] != round(passed / len(checks), 6):
            raise DurationStudyError("evaluator score ratio disagrees with checks")
        failed_ids = [item["check_id"] for item in checks if item["status"] == "fail"]
        if score["failed_check_ids"] != failed_ids:
            raise DurationStudyError("evaluator failed check IDs are not canonical")
        if score["resolution"] == "criterion":
            if any("scope" not in item for item in checks):
                raise DurationStudyError("criterion score requires scoped checks")
            public = [item for item in checks if item["scope"] == "public"]
            hidden = [item for item in checks if item["scope"] == "hidden"]
            expected_scope_counts = (
                sum(item["status"] == "pass" for item in public),
                len(public),
                sum(item["status"] == "pass" for item in hidden),
                len(hidden),
            )
            observed_scope_counts = (
                score["public_passed"],
                score["public_total"],
                score["hidden_passed"],
                score["hidden_total"],
            )
            if observed_scope_counts != expected_scope_counts:
                raise DurationStudyError("evaluator score scope counts disagree with checks")
        elif (
            score["public_passed"]
            or score["public_total"]
            or score["hidden_passed"]
            or score["hidden_total"]
        ):
            raise DurationStudyError("aggregate evaluator score cannot claim scope counts")
    if evaluator["status"] == "pass":
        if not evaluator["checks"] or any(item["status"] != "pass" for item in evaluator["checks"]):
            raise DurationStudyError("passing evaluator requires passing checks")
    elif evaluator["status"] == "fail":
        if not any(item["status"] == "fail" for item in evaluator["checks"]):
            raise DurationStudyError("failing evaluator requires at least one failed check")
    elif evaluator["status"] == "not-run":
        if (
            evaluator["evaluator_id"] is not None
            or evaluator["isolation_profile"] != "not-run"
            or evaluator["image_digest"] is not None
            or evaluator["checks"]
        ):
            raise DurationStudyError("not-run evaluator cannot claim runtime evidence")
    if evaluator["image_digest"] is not None:
        if evaluator["image_digest"] != record["environment"]["image_digest"]:
            raise DurationStudyError("evaluator image differs from the run environment")

    acceptance = record["outcome"]["online_acceptance"]
    expected_evaluator_status = {"pass": "pass", "fail": "fail"}.get(acceptance)
    if expected_evaluator_status is not None and evaluator["status"] != expected_evaluator_status:
        raise DurationStudyError("online acceptance disagrees with evaluator diagnostics")
    if acceptance == "unavailable" and evaluator["status"] not in {
        "not-run",
        "infrastructure-failure",
    }:
        raise DurationStudyError("unavailable acceptance has contradictory evaluator evidence")


def validate_record(kind: str, record: dict[str, Any]) -> None:
    if kind == "run":
        validate_run_record(record)
        return
    if kind == "capability":
        _validate_capability_record(record)
        return
    if kind == "case-catalog":
        validate_case_catalog_record(record)
        return
    if kind == "fixture":
        validate_fixture_record(record)
        return
    validate(record, load_schema(kind))
    if kind == "study":
        reporting = record["reporting"]
        if reporting["typical_quantile_low"] >= reporting["typical_quantile_high"]:
            raise DurationStudyError("study typical quantile low must be less than high")


def _make_private_directory(path: Path) -> None:
    if path.exists():
        if not path.is_dir():
            raise DurationStudyError(f"output parent is not a directory: {path}")
        return
    path.mkdir(mode=0o700, parents=True)


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Atomically create one immutable private JSON record without overwriting."""

    _make_private_directory(path.parent)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise DurationStudyError(f"refusing to overwrite immutable run record: {path}") from exc
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


class RunRecorder:
    def __init__(self, base_record: dict[str, Any], clock: EventClock) -> None:
        self.record = copy.deepcopy(base_record)
        self.clock = clock
        self.record["landmarks"] = {}
        self.record["workers"] = []
        self.record["dialogue_exchanges"] = []

    def mark_landmark(self, name: str, *, status: str = "observed") -> None:
        if name not in LANDMARK_NAMES:
            raise DurationStudyError(f"unknown landmark: {name}")
        if name in self.record["landmarks"]:
            raise DurationStudyError(f"landmark already recorded: {name}")
        self.record["landmarks"][name] = (
            event(self.clock) if status == "observed" else missing_event(status)
        )

    def start_worker(
        self,
        worker_id: str,
        *,
        role: str,
        provider: str = "fixture",
        required_for_result: bool = True,
        parent_worker_id: str | None = None,
    ) -> None:
        if any(item["worker_id"] == worker_id for item in self.record["workers"]):
            raise DurationStudyError(f"worker already exists: {worker_id}")
        worker: dict[str, Any] = {
            "worker_id": worker_id,
            "role": role,
            "provider": provider,
            "required_for_result": required_for_result,
            "start": event(self.clock),
            "stop": missing_event("not-observed"),
        }
        if parent_worker_id is not None:
            worker["parent_worker_id"] = parent_worker_id
        self.record["workers"].append(worker)

    def stop_worker(self, worker_id: str, *, status: str = "observed") -> None:
        for worker in self.record["workers"]:
            if worker["worker_id"] != worker_id:
                continue
            if worker["stop"]["status"] != "not-observed":
                raise DurationStudyError(f"worker already stopped: {worker_id}")
            worker["stop"] = event(self.clock) if status == "observed" else missing_event(status)
            return
        raise DurationStudyError(f"unknown worker: {worker_id}")

    def admit_exchange(self, exchange_id: str, *, role: str, recipient: str) -> None:
        if any(item["exchange_id"] == exchange_id for item in self.record["dialogue_exchanges"]):
            raise DurationStudyError(f"dialogue exchange already exists: {exchange_id}")
        self.record["dialogue_exchanges"].append(
            {
                "exchange_id": exchange_id,
                "role": role,
                "recipient": recipient,
                "admitted": event(self.clock),
                "dispatched": missing_event("not-observed"),
                "returned": missing_event("not-observed"),
                "claim_count": 0,
                "evidence_count": 0,
                "test_count": 0,
                "state_change_count": 0,
                "unresolved_crux_count": 0,
                "stop_reason": "pending",
            }
        )

    def dispatch_exchange(self, exchange_id: str) -> None:
        exchange = self._exchange(exchange_id)
        if exchange["dispatched"]["status"] != "not-observed":
            raise DurationStudyError(f"dialogue exchange already dispatched: {exchange_id}")
        exchange["dispatched"] = event(self.clock)

    def return_exchange(
        self,
        exchange_id: str,
        *,
        claim_count: int,
        evidence_count: int,
        test_count: int,
        state_change_count: int,
        unresolved_crux_count: int,
        stop_reason: str,
    ) -> None:
        exchange = self._exchange(exchange_id)
        if exchange["returned"]["status"] != "not-observed":
            raise DurationStudyError(f"dialogue exchange already returned: {exchange_id}")
        for name, value in (
            ("claim_count", claim_count),
            ("evidence_count", evidence_count),
            ("test_count", test_count),
            ("state_change_count", state_change_count),
            ("unresolved_crux_count", unresolved_crux_count),
        ):
            if value < 0:
                raise DurationStudyError(f"{name} must be non-negative")
            exchange[name] = value
        exchange["stop_reason"] = stop_reason
        exchange["returned"] = event(self.clock)

    def _exchange(self, exchange_id: str) -> dict[str, Any]:
        for exchange in self.record["dialogue_exchanges"]:
            if exchange["exchange_id"] == exchange_id:
                return exchange
        raise DurationStudyError(f"unknown dialogue exchange: {exchange_id}")

    def finalize(
        self,
        *,
        outcome: dict[str, Any],
        quality: dict[str, Any],
        diagnostics: dict[str, Any],
        nested_worker_detected: bool = False,
    ) -> dict[str, Any]:
        record = copy.deepcopy(self.record)
        intervals = _worker_intervals(record)
        configuration = record["configuration"]
        configuration["participants_actual"] = len(record["participants"])
        configuration["workers_actual"] = len(record["workers"])
        configuration["peak_concurrent"] = observed_peak_concurrency(record["workers"])

        quality_pass, quality_basis = canonical_quality_pass(
            online_acceptance=outcome["online_acceptance"],
            offline_score=outcome["offline_score"],
            strong_online_oracle=record["case"]["strong_online_oracle"],
        )
        outcome = copy.deepcopy(outcome)
        outcome["quality_pass"] = quality_pass
        outcome["quality_basis"] = quality_basis
        record["outcome"] = outcome
        record["quality"] = copy.deepcopy(quality)
        record["diagnostics"] = copy.deepcopy(diagnostics)

        t2_status = record["landmarks"].get("T2", {"status": "not-observed"})["status"]
        t4_status = record["landmarks"].get("T4", {"status": "not-observed"})["status"]
        if intervals is None:
            worker_tree = "untracked"
        elif nested_worker_detected:
            worker_tree = "lower-bound"
        else:
            worker_tree = "exact"
        record["coverage"] = {
            "duration_catalog_version": 1,
            "clock_landmarks": [
                name
                for name in LANDMARK_NAMES
                if record["landmarks"].get(name, {}).get("status") == "observed"
            ],
            "first_artifact_resolution": (
                "progress-envelope" if t2_status == "observed" else t2_status
            ),
            "synthesis_resolution": (
                "explicit-envelope" if t4_status == "observed" else t4_status
            ),
            "worker_tree": worker_tree,
            "nested_worker_detected": nested_worker_detected,
        }
        record["durations_ms"] = derive_durations(record)

        unknown_paths: list[str] = []
        for index, participant in enumerate(record["participants"]):
            identity = participant["model_identity"]
            if identity["identity_confidence"] in {"default-unspecified", "unknown"}:
                unknown_paths.append(f"/participants/{index}/model_identity")
            for setting_index, setting in enumerate(participant["generation_settings"]):
                if setting["status"] == "unknown":
                    unknown_paths.append(
                        f"/participants/{index}/generation_settings/{setting_index}/applied_value"
                    )
        evaluated_paths = []
        if diagnostics["evaluator"]["status"] in {"pass", "fail"}:
            evaluated_paths.extend(["/diagnostics/evaluator", "/outcome/online_acceptance"])
        if outcome["offline_score"] not in {"not-run", "unavailable"}:
            evaluated_paths.extend(["/outcome/offline_score", "/quality"])
        record["field_provenance"] = {
            "observed": [
                "/landmarks",
                "/workers",
                "/dialogue_exchanges",
                "/diagnostics/provider",
            ],
            "declared_by_harness": [
                "/case",
                "/snapshot",
                "/configuration/relation",
                "/environment",
                "/limits",
            ],
            "derived": [
                "/durations_ms",
                "/configuration/participants_actual",
                "/configuration/workers_actual",
                "/configuration/peak_concurrent",
                "/outcome/quality_pass",
                "/outcome/quality_basis",
                "/coverage",
            ],
            "evaluated": evaluated_paths,
            "unknown": unknown_paths,
        }
        validate_run_record(record)
        return record


def _fixture_runtime(observed_at: str) -> dict[str, Any]:
    return {
        "provider": "fixture",
        "cli_name": "duration-fixture",
        "cli_version": "1",
        "cli_source": "fixture",
        "image_digest": f"sha256:{'0' * 64}",
        "execution_surface": "fixture",
        "permission_mode": "automatic",
        "observed_at": observed_at,
    }


def _fixture_participant(participant_id: str, role: str, observed_at: str) -> dict[str, Any]:
    return {
        "participant_id": participant_id,
        "role": role,
        "model_identity": {
            "requested_alias": "fixture-model",
            "requested_source": "flag",
            "resolved_id": "fixture-model-v1",
            "identity_confidence": "exact",
            "snapshot_hint": "deterministic",
        },
        "generation_settings": [
            {
                "namespace": "fixture.reasoning",
                "key": "effort",
                "requested_value": "deterministic",
                "status": "applied",
                "applied_value": "deterministic",
            }
        ],
        "runtime_identity": _fixture_runtime(observed_at),
    }


def _fake_base(scenario: str, *, delegated: bool, nested_untracked: bool = False) -> dict[str, Any]:
    observed_at = "2026-01-01T00:00:00.000Z"
    participants = [_fixture_participant("primary", "orchestrator", observed_at)]
    if delegated:
        participants.append(_fixture_participant("worker-1", "investigator", observed_at))
    return {
        "schema_version": 2,
        "study_id": "duration-atlas-fixture",
        "run_id": f"fixture-{scenario}",
        "block_id": "fixture-block",
        "case": {
            "case_id": "F03-S-fixture",
            "revision": 1,
            "catalog_digest": f"sha256:{'1' * 64}",
            "capsule_digest": f"sha256:{'2' * 64}",
            "source_type": "fixture",
            "family": "failing-test-diagnosis",
            "size": "S",
            "profile_id": "S-local-deterministic-python",
            "strong_online_oracle": True,
        },
        "snapshot": {
            "base_sha": "0" * 40,
            "bundle_digest": f"sha256:{'3' * 64}",
            "fixture_revision": "fixture-v1",
            "instruction_set_digest": f"sha256:{'4' * 64}",
        },
        "configuration": {
            "configuration_id": "C1" if delegated else "C0",
            "relation": "bounded-delegation" if delegated else "primary-only",
            "participant_plan": "primary-investigator" if delegated else "primary-only",
            "participants_actual": len(participants),
            "workers_actual": 1 if delegated else 0,
            "peak_concurrent": 1 if delegated else 0,
            "nested_delegation": "detected-untracked" if nested_untracked else "disabled",
            "independence_policy": "fresh-context",
            "lane": "read",
        },
        "participants": participants,
        "environment": {
            "image_digest": f"sha256:{'0' * 64}",
            "machine_class": "deterministic-fixture",
            "session_context": "fresh",
            "repository_cache": "not-applicable",
            "dependency_cache": "not-applicable",
            "docker_cache": "not-applicable",
            "provider_prompt_cache": "not-applicable",
            "compaction": "not-applicable",
            "competing_load": "none-observed",
            "timezone": "UTC",
        },
        "limits": {
            "wall_clock_ms": 60_000,
            "role": "safety-censoring-cap",
            "retry_policy": "none",
        },
        "correlation": {
            "episode_ids": [],
            "agentctl_job_ids": [],
            "attempt_ids": [],
        },
    }


def _fake_diagnostics(scenario: str) -> dict[str, Any]:
    provider_status = (
        "timeout"
        if scenario == "timeout"
        else "failure"
        if scenario == "provider-failure"
        else "success"
    )
    provider_exit = 124 if scenario == "timeout" else 1 if scenario == "provider-failure" else 0
    evaluator_ran = provider_status == "success"
    digest = f"sha256:{'0' * 64}"
    return {
        "provider": {
            "status": provider_status,
            "exit_code": provider_exit,
            "terminal_wall_ms": 30.0 if scenario == "timeout" else 10.0,
            "output_cap_bytes": 1024,
            "output_bytes": 0,
            "stderr_bytes": 0,
            "workspace_changed_path_count": 1 if evaluator_ran else 0,
            "event_counts": (
                [{"name": "turn.completed", "count": 1}] if evaluator_ran else []
            ),
            "item_type_counts": [],
            "invalid_event_lines": 0,
            "final_message_observed": evaluator_ran,
            "usage": {},
            "generation_request_performed": False,
            "prompt_persisted": False,
            "raw_output_persisted": False,
            "raw_stderr_persisted": False,
            "credential_path_persisted": False,
            "nested_delegation": "not-applicable",
            "task_network": "not-applicable",
            "sandbox_preflight": {
                "status": "pass",
                "image_digest": digest,
                "profile_digest": digest,
                "workspace_write": "observed",
                "unrelated_read": "denied",
                "command_network": "denied",
                "generation_request_performed": False,
            },
        },
        "evaluator": {
            "status": "pass" if evaluator_ran else "not-run",
            "evaluator_id": "fixture-online-v1" if evaluator_ran else None,
            "isolation_profile": "network-disabled-read-only-container" if evaluator_ran else "not-run",
            "image_digest": digest if evaluator_ran else None,
            "credential_mounts": False,
            "control_bundle_mounted": False,
            "checks": (
                [
                    {
                        "check_id": "fixture-online-v1",
                        "status": "pass",
                        "exit_code": 0,
                        "duration_ms": 1.0,
                    }
                ]
                if evaluator_ran
                else []
            ),
        },
    }


def build_fake_run(scenario: str) -> dict[str, Any]:
    if scenario not in {
        "delegated-complete",
        "solo-complete",
        "missing-progress",
        "timeout",
        "provider-failure",
        "nested-untracked",
    }:
        raise DurationStudyError(f"unknown fake scenario: {scenario}")

    delegated = scenario in {"delegated-complete", "timeout", "nested-untracked"}
    nested_untracked = scenario == "nested-untracked"
    clock = FakeClock()
    recorder = RunRecorder(
        _fake_base(scenario, delegated=delegated, nested_untracked=nested_untracked),
        clock,
    )

    recorder.mark_landmark("P0")
    clock.advance_ms(5)
    recorder.mark_landmark("P1")
    recorder.mark_landmark("T0")
    clock.advance_ms(2)
    recorder.mark_landmark("T1")

    if scenario in {"timeout", "provider-failure"}:
        if delegated:
            recorder.start_worker("worker-1", role="investigator")
        recorder.mark_landmark("T2", status="not-observed")
        recorder.mark_landmark("T3", status="not-observed")
        recorder.mark_landmark("T4", status="not-observed")
        recorder.mark_landmark("V0", status="not-observed")
        recorder.mark_landmark("V1", status="not-observed")
        recorder.mark_landmark("T6", status="not-observed")
        clock.advance_ms(30 if scenario == "timeout" else 10)
        recorder.mark_landmark("TX")
        recorder.mark_landmark("S0", status="not-applicable")
        recorder.mark_landmark("S1", status="not-applicable")
        return recorder.finalize(
            outcome={
                "infrastructure": "timeout" if scenario == "timeout" else "failure",
                "artifact": "missing",
                "online_acceptance": "unavailable",
                "offline_score": "not-run",
                "failure_class": "timeout-cap" if scenario == "timeout" else "provider-refusal",
                "stop_reason": "safety-cap" if scenario == "timeout" else "provider-failure",
            },
            quality={"evaluator_id": None, "metrics": []},
            diagnostics=_fake_diagnostics(scenario),
        )

    if delegated:
        recorder.start_worker("worker-1", role="investigator")
    clock.advance_ms(4)
    if scenario == "missing-progress":
        recorder.mark_landmark("T2", status="not-observed")
    else:
        recorder.mark_landmark("T2")

    if delegated:
        recorder.admit_exchange("exchange-1", role="investigator", recipient="primary")
        clock.advance_ms(1)
        recorder.dispatch_exchange("exchange-1")
        clock.advance_ms(3)
        recorder.return_exchange(
            "exchange-1",
            claim_count=1,
            evidence_count=1,
            test_count=1,
            state_change_count=1,
            unresolved_crux_count=0,
            stop_reason="evidence-returned",
        )
        clock.advance_ms(2)
        recorder.stop_worker("worker-1")
        recorder.mark_landmark("T3")
        clock.advance_ms(3)
        recorder.mark_landmark("T4")
    else:
        recorder.mark_landmark("T3", status="not-applicable")
        recorder.mark_landmark("T4", status="not-applicable")

    recorder.mark_landmark("V0")
    clock.advance_ms(5 if delegated else 7)
    recorder.mark_landmark("V1")
    clock.advance_ms(1)
    recorder.mark_landmark("T6")
    recorder.mark_landmark("TX")

    offline_score = "not-run" if scenario == "solo-complete" else "pass"
    if offline_score == "not-run":
        recorder.mark_landmark("S0", status="not-applicable")
        recorder.mark_landmark("S1", status="not-applicable")
        quality = {"evaluator_id": None, "metrics": []}
    else:
        clock.advance_ms(2)
        recorder.mark_landmark("S0")
        clock.advance_ms(1)
        recorder.mark_landmark("S1")
        quality = {
            "evaluator_id": "fixture-diagnosis-v1",
            "metrics": [
                {"name": "fixture-score", "value": 1, "provenance": "evaluated"}
            ],
        }

    return recorder.finalize(
        outcome={
            "infrastructure": "success",
            "artifact": "valid",
            "online_acceptance": "pass",
            "offline_score": offline_score,
            "failure_class": "nested-worker-untracked" if nested_untracked else None,
            "stop_reason": "result-ready",
        },
        quality=quality,
        diagnostics=_fake_diagnostics(scenario),
        nested_worker_detected=nested_untracked,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    fake = subparsers.add_parser("fake-run", help="write one deterministic no-provider run")
    fake.add_argument(
        "--scenario",
        required=True,
        choices=(
            "delegated-complete",
            "solo-complete",
            "missing-progress",
            "timeout",
            "provider-failure",
            "nested-untracked",
        ),
    )
    fake.add_argument("--output-dir", type=Path, required=True)
    fake.add_argument("--print-record", action="store_true")

    capability = subparsers.add_parser(
        "probe-capability",
        help="record version/help/catalog evidence without a generation request",
    )
    capability.add_argument("--provider", choices=("codex", "claude", "grok"), required=True)
    capability.add_argument("--binary", help="provider executable; defaults to the provider name")
    capability.add_argument(
        "--cli-source",
        choices=("container-image", "host-sync", "fixture", "unknown"),
        default="unknown",
    )
    capability.add_argument(
        "--environment-kind",
        choices=("host", "devcontainer", "fixture", "unknown"),
        default="unknown",
    )
    capability.add_argument("--image-digest")
    capability.add_argument("--timeout-seconds", type=float, default=15.0)
    capability.add_argument(
        "--offline-only",
        action="store_true",
        help="avoid provider metadata calls; Codex uses its bundled catalog",
    )
    capability.add_argument("--capability-id")
    capability.add_argument("--output-dir", type=Path, required=True)
    capability.add_argument("--print-record", action="store_true")

    fixture = subparsers.add_parser(
        "build-fixture",
        help="materialize one isolated deterministic case repository",
    )
    fixture.add_argument("--case-id", required=True)
    fixture.add_argument(
        "--catalog",
        type=Path,
        default=ROOT / "experiments" / "multi-agent-duration" / "catalog" / "cases.json",
    )
    fixture.add_argument("--fixture-id")
    fixture.add_argument("--output-dir", type=Path, required=True)
    fixture.add_argument("--print-manifest", action="store_true")

    evaluate = subparsers.add_parser(
        "evaluate-fixture",
        help="run trusted calibration checks; live artifacts require an isolated evaluator",
    )
    evaluate.add_argument("fixture_dir", type=Path)
    evaluate.add_argument(
        "--trusted-calibration",
        action="store_true",
        help="acknowledge host execution is only for checked-in fixture calibration",
    )

    isolated_evaluate = subparsers.add_parser(
        "evaluate-fixture-isolated",
        help="evaluate an agent artifact in a network-disabled read-only container",
    )
    isolated_evaluate.add_argument("fixture_dir", type=Path)
    isolated_evaluate.add_argument("--image", required=True)
    isolated_evaluate.add_argument("--docker-bin", default="docker")
    isolated_evaluate.add_argument("--timeout-seconds", type=float, default=30)

    codex_sandbox = subparsers.add_parser(
        "probe-codex-sandbox",
        help="verify the no-generation Codex workspace-only permission profile",
    )
    codex_sandbox.add_argument("fixture_dir", type=Path)
    codex_sandbox.add_argument("--image", required=True)
    codex_sandbox.add_argument("--docker-bin", default="docker")
    codex_sandbox.add_argument("--timeout-seconds", type=float, default=30)

    codex_live = subparsers.add_parser(
        "run-codex-fixture",
        help="run exactly one isolated primary-only Codex fixture turn",
    )
    codex_live.add_argument("fixture_dir", type=Path)
    codex_live.add_argument("--image", required=True)
    codex_live.add_argument("--model", required=True)
    codex_live.add_argument(
        "--effort",
        required=True,
        choices=("low", "medium", "high", "xhigh", "max", "ultra"),
    )
    codex_live.add_argument("--auth-file", type=Path, default=Path.home() / ".codex" / "auth.json")
    codex_live.add_argument("--docker-bin", default="docker")
    codex_live.add_argument("--timeout-seconds", type=float, default=900)
    codex_live.add_argument("--output-bytes-cap", type=int, default=8 * 1024 * 1024)
    codex_live.add_argument(
        "--confirm-live-provider",
        action="store_true",
        help="explicitly authorize one provider generation request",
    )

    codex_study = subparsers.add_parser(
        "run-codex-study",
        help="run and immutably record one isolated Codex sample plus hidden evaluation",
    )
    codex_study.add_argument("--case-id", required=True)
    codex_study.add_argument("--output-dir", type=Path, required=True)
    codex_study.add_argument("--image", required=True)
    codex_study.add_argument("--model", required=True)
    codex_study.add_argument(
        "--effort",
        required=True,
        choices=("low", "medium", "high", "xhigh", "max", "ultra"),
    )
    codex_study.add_argument("--study-id", default="duration-atlas-wave1")
    codex_study.add_argument("--block-id", default="codex-primary-calibration")
    codex_study.add_argument("--run-id")
    codex_study.add_argument(
        "--auth-file",
        type=Path,
        default=Path.home() / ".codex" / "auth.json",
    )
    codex_study.add_argument("--docker-bin", default="docker")
    codex_study.add_argument("--timeout-seconds", type=float, default=900)
    codex_study.add_argument("--evaluator-timeout-seconds", type=float, default=30)
    codex_study.add_argument("--output-bytes-cap", type=int, default=8 * 1024 * 1024)
    codex_study.add_argument(
        "--confirm-live-provider",
        action="store_true",
        help="explicitly authorize exactly one provider generation request",
    )

    provider_study = subparsers.add_parser(
        "run-provider-study",
        help=(
            "run and immutably record one isolated Codex, Claude, or Grok sample "
            "plus criterion-level evaluation"
        ),
    )
    provider_study.add_argument("--provider", required=True, choices=("codex", "claude", "grok"))
    provider_study.add_argument("--case-id", required=True)
    provider_study.add_argument("--output-dir", type=Path, required=True)
    provider_study.add_argument("--image", required=True)
    provider_study.add_argument("--model", required=True)
    provider_study.add_argument(
        "--effort",
        required=True,
        choices=("low", "medium", "high", "xhigh", "max", "ultra"),
    )
    provider_study.add_argument("--study-id", default="duration-atlas-wave1")
    provider_study.add_argument("--block-id")
    provider_study.add_argument("--run-id")
    provider_study.add_argument(
        "--auth-file",
        type=Path,
        help="provider credential JSON; defaults to the provider's standard user path",
    )
    provider_study.add_argument(
        "--provider-binary",
        type=Path,
        help="optional read-only host-synced Grok executable",
    )
    provider_study.add_argument("--docker-bin", default="docker")
    provider_study.add_argument("--timeout-seconds", type=float, default=900)
    provider_study.add_argument("--evaluator-timeout-seconds", type=float, default=30)
    provider_study.add_argument("--output-bytes-cap", type=int, default=8 * 1024 * 1024)
    provider_study.add_argument(
        "--confirm-live-provider",
        action="store_true",
        help="explicitly authorize exactly one provider generation request",
    )

    report_runs = subparsers.add_parser(
        "report-runs",
        help="show bounded raw samples without producing a typical band or routing rule",
    )
    report_runs.add_argument("inputs", nargs="+", type=Path)
    report_runs.add_argument("--format", choices=("table", "json"), default="table")
    report_runs.add_argument("--case-id")
    report_runs.add_argument("--provider", choices=("codex", "claude", "grok", "fixture"))
    report_runs.add_argument(
        "--quality",
        choices=("all", "pass", "fail", "unknown"),
        default="all",
    )
    report_runs.add_argument("--limit", type=int, default=50)

    validate_command = subparsers.add_parser("validate", help="validate one study record")
    validate_command.add_argument("--kind", choices=tuple(SCHEMA_PATHS), required=True)
    validate_command.add_argument("path", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "fake-run":
            record = build_fake_run(args.scenario)
            output = args.output_dir.resolve() / f"{record['run_id']}.json"
            atomic_write_json(output, record)
            if args.print_record:
                print(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print(
                    json.dumps(
                        {
                            "status": "written",
                            "scenario": args.scenario,
                            "run_id": record["run_id"],
                            "path": str(output),
                        },
                        sort_keys=True,
                    )
                )
            return 0

        if args.command == "probe-capability":
            from agent_duration_capability import probe_capability

            record = probe_capability(
                args.provider,
                binary=args.binary,
                cli_source=args.cli_source,
                environment_kind=args.environment_kind,
                image_digest=args.image_digest,
                timeout_seconds=args.timeout_seconds,
                offline_only=args.offline_only,
                capability_id=args.capability_id,
            )
            output = args.output_dir.resolve() / f"{record['capability_id']}.json"
            atomic_write_json(output, record)
            if args.print_record:
                print(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print(
                    json.dumps(
                        {
                            "status": "written",
                            "provider": args.provider,
                            "capability_id": record["capability_id"],
                            "path": str(output),
                            "generation_request_performed": False,
                        },
                        sort_keys=True,
                    )
                )
            return 0

        if args.command == "build-fixture":
            from agent_duration_fixtures import build_fixture

            manifest = build_fixture(
                args.case_id,
                args.output_dir.resolve(),
                catalog_path=args.catalog.resolve(),
                fixture_id=args.fixture_id,
            )
            if args.print_manifest:
                print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print(
                    json.dumps(
                        {
                            "status": "built",
                            "fixture_id": manifest["fixture_id"],
                            "case_id": manifest["case"]["case_id"],
                            "path": str(args.output_dir.resolve()),
                            "initial_oracle": manifest["initial_oracle"]["observed"],
                        },
                        sort_keys=True,
                    )
                )
            return 0

        if args.command == "evaluate-fixture":
            from agent_duration_fixtures import evaluate_fixture

            if not args.trusted_calibration:
                raise DurationStudyError(
                    "refusing host evaluation without --trusted-calibration; "
                    "live artifacts require a network-disabled evaluator container"
                )
            result = evaluate_fixture(args.fixture_dir.resolve())
            print(json.dumps(result, sort_keys=True))
            return 0 if result["status"] == "pass" else 1

        if args.command == "evaluate-fixture-isolated":
            from agent_duration_fixtures import evaluate_fixture_isolated

            result = evaluate_fixture_isolated(
                args.fixture_dir.resolve(),
                image=args.image,
                docker_bin=args.docker_bin,
                timeout_seconds=args.timeout_seconds,
            )
            print(json.dumps(result, sort_keys=True))
            return 0 if result["status"] == "pass" else 1

        if args.command == "probe-codex-sandbox":
            from agent_duration_live import probe_codex_agent_sandbox

            result = probe_codex_agent_sandbox(
                args.fixture_dir.resolve(),
                image=args.image,
                docker_bin=args.docker_bin,
                timeout_seconds=args.timeout_seconds,
            )
            print(json.dumps(result, sort_keys=True))
            return 0

        if args.command == "run-codex-fixture":
            from agent_duration_live import run_codex_fixture

            result = run_codex_fixture(
                args.fixture_dir.resolve(),
                image=args.image,
                model=args.model,
                effort=args.effort,
                auth_file=args.auth_file.resolve(),
                live_generation_authorized=args.confirm_live_provider,
                docker_bin=args.docker_bin,
                timeout_seconds=args.timeout_seconds,
                output_bytes_cap=args.output_bytes_cap,
            )
            print(json.dumps(result, sort_keys=True))
            return 0 if result["infrastructure"] == "success" else 1

        if args.command == "run-codex-study":
            from agent_duration_live import run_codex_study_once

            record, path = run_codex_study_once(
                args.case_id,
                args.output_dir,
                image=args.image,
                model=args.model,
                effort=args.effort,
                auth_file=args.auth_file.resolve(),
                live_generation_authorized=args.confirm_live_provider,
                study_id=args.study_id,
                block_id=args.block_id,
                run_id=args.run_id,
                docker_bin=args.docker_bin,
                timeout_seconds=args.timeout_seconds,
                evaluator_timeout_seconds=args.evaluator_timeout_seconds,
                output_bytes_cap=args.output_bytes_cap,
            )
            print(
                json.dumps(
                    {
                        "status": "written",
                        "run_id": record["run_id"],
                        "path": str(path),
                        "infrastructure": record["outcome"]["infrastructure"],
                        "online_acceptance": record["outcome"]["online_acceptance"],
                        "quality_pass": record["outcome"]["quality_pass"],
                        "terminal_wall_ms": record["durations_ms"]["terminal_wall"],
                        "provider_wall_ms": record["diagnostics"]["provider"][
                            "terminal_wall_ms"
                        ],
                    },
                    sort_keys=True,
                )
            )
            return 0 if record["outcome"]["quality_pass"] is True else 1

        if args.command == "run-provider-study":
            from agent_duration_live import run_provider_study_once

            auth_defaults = {
                "codex": Path.home() / ".codex" / "auth.json",
                "claude": Path.home() / ".claude" / ".credentials.json",
                "grok": Path.home() / ".grok" / "auth.json",
            }
            auth_file = (args.auth_file or auth_defaults[args.provider]).resolve()
            provider_binary = (
                args.provider_binary.resolve() if args.provider_binary is not None else None
            )
            record, path = run_provider_study_once(
                args.provider,
                args.case_id,
                args.output_dir,
                image=args.image,
                model=args.model,
                effort=args.effort,
                auth_file=auth_file,
                live_generation_authorized=args.confirm_live_provider,
                study_id=args.study_id,
                block_id=args.block_id,
                run_id=args.run_id,
                docker_bin=args.docker_bin,
                timeout_seconds=args.timeout_seconds,
                evaluator_timeout_seconds=args.evaluator_timeout_seconds,
                output_bytes_cap=args.output_bytes_cap,
                provider_binary=provider_binary,
            )
            print(
                json.dumps(
                    {
                        "status": "written",
                        "provider": args.provider,
                        "run_id": record["run_id"],
                        "path": str(path),
                        "infrastructure": record["outcome"]["infrastructure"],
                        "online_acceptance": record["outcome"]["online_acceptance"],
                        "quality_pass": record["outcome"]["quality_pass"],
                        "terminal_wall_ms": record["durations_ms"]["terminal_wall"],
                        "provider_wall_ms": record["diagnostics"]["provider"][
                            "terminal_wall_ms"
                        ],
                    },
                    sort_keys=True,
                )
            )
            return 0 if record["outcome"]["quality_pass"] is True else 1

        if args.command == "report-runs":
            from agent_duration_report import (
                build_raw_sample_report,
                load_run_records,
                render_raw_sample_table,
            )

            report = build_raw_sample_report(
                load_run_records(args.inputs),
                case_id=args.case_id,
                provider=args.provider,
                quality=args.quality,
                limit=args.limit,
            )
            if args.format == "json":
                print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print(render_raw_sample_table(report))
            return 0

        record = load_json(args.path)
        if not isinstance(record, dict):
            raise DurationStudyError("record root must be an object")
        validate_record(args.kind, record)
        print(json.dumps({"status": "valid", "kind": args.kind, "path": str(args.path)}))
        return 0
    except (ContractValidationError, DurationStudyError, OSError) as exc:
        parser.exit(2, f"agent-duration-study: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())

"""Preflight and execute explicit finite duration-study batches without retries."""

from __future__ import annotations

from pathlib import Path
import time
from typing import Any, Callable

from agent_contracts import load_json
from agent_duration_fixtures import DEFAULT_CATALOG
from agent_duration_study import (
    DurationStudyError,
    canonical_json_digest,
    validate_case_catalog_record,
    validate_record,
    validate_run_record,
)


PROVIDER_EFFORTS = {
    "codex": {"low", "medium", "high", "xhigh", "max", "ultra"},
    "claude": {"low", "medium", "high", "xhigh", "max"},
    "grok": {"medium", "high", "xhigh", "max"},
}


def load_and_validate_batch(
    path: Path,
    *,
    catalog_path: Path = DEFAULT_CATALOG,
) -> dict[str, Any]:
    batch = load_json(path)
    if not isinstance(batch, dict):
        raise DurationStudyError("duration batch root must be an object")
    validate_record("batch", batch)
    catalog = load_json(catalog_path)
    if not isinstance(catalog, dict):
        raise DurationStudyError("duration catalog root must be an object")
    validate_case_catalog_record(catalog)
    if batch["catalog_digest"] != canonical_json_digest(catalog):
        raise DurationStudyError("duration batch catalog digest is stale")
    entries = batch["entries"]
    if len(entries) > batch["safety"]["max_runs"]:
        raise DurationStudyError("duration batch entries exceed its declared max_runs")
    orders = [entry["order"] for entry in entries]
    if sorted(orders) != list(range(1, len(entries) + 1)):
        raise DurationStudyError("duration batch order must be contiguous from one")
    run_ids = [entry["run_id"] for entry in entries]
    if len(run_ids) != len(set(run_ids)):
        raise DurationStudyError("duration batch run IDs must be unique")
    case_ids = {entry["case"]["case_id"] for entry in catalog["entries"]}
    for entry in entries:
        if entry["case_id"] not in case_ids:
            raise DurationStudyError(f"duration batch case is absent from catalog: {entry['case_id']}")
        if entry["effort"] not in PROVIDER_EFFORTS[entry["provider"]]:
            raise DurationStudyError(
                f"duration batch effort is unsupported by provider surface: "
                f"{entry['provider']}/{entry['effort']}"
            )
    return batch


def _validate_existing_run(
    path: Path,
    entry: dict[str, Any],
    *,
    study_id: str,
    catalog_digest: str,
    artifact_retention: str,
) -> dict[str, Any]:
    value = load_json(path)
    if not isinstance(value, dict):
        raise DurationStudyError(f"existing duration run root must be an object: {path}")
    validate_run_record(value)
    if value["run_id"] != entry["run_id"] or value["case"]["case_id"] != entry["case_id"]:
        raise DurationStudyError(f"existing duration run does not match batch entry: {path}")
    if value["study_id"] != study_id or value["block_id"] != entry["block_id"]:
        raise DurationStudyError(f"existing duration run study/block does not match batch entry: {path}")
    if value["case"]["catalog_digest"] != catalog_digest:
        raise DurationStudyError(f"existing duration run catalog does not match batch entry: {path}")
    if (
        value["configuration"]["relation"] != "primary-only"
        or value["configuration"]["participants_actual"] != 1
        or value["configuration"]["workers_actual"] != 0
    ):
        raise DurationStudyError(f"existing duration run relation does not match batch entry: {path}")
    participant = value["participants"][0]
    if participant["runtime_identity"]["provider"] != entry["provider"]:
        raise DurationStudyError(f"existing duration run provider does not match batch entry: {path}")
    if participant["model_identity"].get("requested_alias") != entry["model"]:
        raise DurationStudyError(f"existing duration run model does not match batch entry: {path}")
    requested_settings = {
        item["requested_value"] for item in participant["generation_settings"]
    }
    if entry["effort"] not in requested_settings:
        raise DurationStudyError(f"existing duration run effort does not match batch entry: {path}")
    retained = "artifact_snapshot" in value
    if retained != (artifact_retention == "task-artifacts"):
        raise DurationStudyError(
            f"existing duration run artifact retention does not match batch entry: {path}"
        )
    return value


def execute_batch(
    batch: dict[str, Any],
    *,
    output_dir: Path,
    image: str,
    auth_files: dict[str, Path],
    live_generation_authorized: bool,
    execute: bool,
    docker_bin: str = "docker",
    grok_binary: Path | None = None,
    run_once: Callable[..., tuple[dict[str, Any], Path]] | None = None,
    monotonic: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    """Execute at most the explicit entries once, stopping on infrastructure failure."""

    if execute and not live_generation_authorized:
        raise DurationStudyError("live duration batch requires explicit generation authorization")
    if run_once is None:
        from agent_duration_live import run_provider_study_once

        run_once = run_provider_study_once
    output_dir = output_dir.resolve()
    started = monotonic()
    deadline = started + batch["safety"]["deadline_seconds"]
    observations: list[dict[str, Any]] = []
    stop_reason = "completed" if execute else "dry-run"
    for entry in sorted(batch["entries"], key=lambda item: item["order"]):
        record_path = output_dir / f"{entry['run_id']}.json"
        if record_path.exists():
            record = _validate_existing_run(
                record_path,
                entry,
                study_id=batch["study_id"],
                catalog_digest=batch["catalog_digest"],
                artifact_retention=batch["safety"].get(
                    "artifact_retention", "content-free-only"
                ),
            )
            observations.append(
                {
                    "run_id": entry["run_id"],
                    "status": "existing",
                    "quality_pass": record["outcome"]["quality_pass"],
                }
            )
            continue
        if not execute:
            observations.append({"run_id": entry["run_id"], "status": "planned"})
            continue
        remaining_seconds = deadline - monotonic()
        declared_run_budget = (
            entry["timeout_seconds"] + entry["evaluator_timeout_seconds"]
        )
        if remaining_seconds < declared_run_budget:
            stop_reason = "deadline"
            break
        provider = entry["provider"]
        if provider not in auth_files:
            raise DurationStudyError(f"duration batch auth source is missing: {provider}")
        record, path = run_once(
            provider,
            entry["case_id"],
            output_dir,
            image=image,
            model=entry["model"],
            effort=entry["effort"],
            auth_file=auth_files[provider].resolve(),
            live_generation_authorized=True,
            study_id=batch["study_id"],
            block_id=entry["block_id"],
            run_id=entry["run_id"],
            docker_bin=docker_bin,
            timeout_seconds=entry["timeout_seconds"],
            evaluator_timeout_seconds=entry["evaluator_timeout_seconds"],
            output_bytes_cap=entry["output_bytes_cap"],
            provider_binary=grok_binary if provider == "grok" else None,
            artifact_retention=batch["safety"].get(
                "artifact_retention", "content-free-only"
            ),
        )
        if path.resolve() != record_path.resolve():
            raise DurationStudyError("live duration runner returned an unexpected record path")
        observations.append(
            {
                "run_id": entry["run_id"],
                "status": "observed",
                "infrastructure": record["outcome"]["infrastructure"],
                "quality_pass": record["outcome"]["quality_pass"],
            }
        )
        if record["outcome"]["infrastructure"] != "success":
            stop_reason = "infrastructure-failure"
            break
    return {
        "batch_id": batch["batch_id"],
        "execute": execute,
        "stop_reason": stop_reason,
        "entries": len(batch["entries"]),
        "observations": observations,
        "remaining": len(batch["entries"]) - len(observations),
    }


__all__ = ["execute_batch", "load_and_validate_batch"]

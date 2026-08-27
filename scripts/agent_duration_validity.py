#!/usr/bin/env python3
"""Validate and apply revision-aware effort-quality inference gates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

from agent_contracts import ContractValidationError, load_json, validate
from agent_duration_study import (
    DurationStudyError,
    ROOT,
    canonical_json_digest,
    validate_case_catalog_record,
)


DEFAULT_VALIDITY = (
    ROOT / "experiments" / "multi-agent-duration" / "validity" / "effort-quality.json"
)
DEFAULT_CATALOG = (
    ROOT / "experiments" / "multi-agent-duration" / "catalog" / "cases.json"
)
VALIDITY_SCHEMA = (
    ROOT / "experiments" / "multi-agent-duration" / "schemas" / "validity.schema.json"
)


class ValidityError(DurationStudyError):
    """Raised when inference-validity evidence is inconsistent or incomplete."""


def _load_object(path: Path, label: str) -> dict[str, Any]:
    value = load_json(path)
    if not isinstance(value, dict):
        raise ValidityError(f"{label} root must be an object")
    return value


def validate_validity_record(
    record: Mapping[str, Any],
    *,
    catalog: Mapping[str, Any] | None = None,
) -> None:
    schema = _load_object(VALIDITY_SCHEMA, "validity schema")
    validate(record, schema)

    entries = record["entries"]
    keys = [(item["case_id"], item["case_revision"]) for item in entries]
    if len(keys) != len(set(keys)):
        raise ValidityError("validity case/revision pairs must be unique")

    expected_use = {
        "eligible": "eligible-after-observation-gates",
        "conditional": "conditional-only",
        "ineligible": "excluded",
    }
    for item in entries:
        if item["inference_use"] != expected_use[item["design_status"]]:
            raise ValidityError("validity design status disagrees with inference use")
        if item["design_status"] == "eligible":
            if item["task_contract_visibility"] != "complete":
                raise ValidityError("eligible case requires a complete visible task contract")
            if item["oracle_alignment"] in {"lexical-proxy", "overfit", "unknown"}:
                raise ValidityError("eligible case requires a semantically aligned oracle")
            if item["solution_space_calibration"] == "unverified":
                raise ValidityError("eligible case requires calibrated solution-space evidence")

    if catalog is None:
        return
    validate_case_catalog_record(dict(catalog))
    catalog_ref = record["catalog"]
    if catalog_ref["catalog_id"] != catalog["catalog_id"]:
        raise ValidityError("validity catalog ID does not match the supplied catalog")
    if catalog_ref["revision"] != catalog["revision"]:
        raise ValidityError("validity catalog revision does not match the supplied catalog")
    if catalog_ref["digest"] != canonical_json_digest(catalog):
        raise ValidityError("validity catalog digest does not match the supplied catalog")

    current = {item["case"]["case_id"]: item["case"]["revision"] for item in catalog["entries"]}
    for case_id, revision in keys:
        current_revision = current.get(case_id)
        if current_revision is None:
            raise ValidityError(f"validity references an unknown case: {case_id}")
        if revision > current_revision:
            raise ValidityError(f"validity references a future case revision: {case_id}")


def load_validated_validity(
    path: Path = DEFAULT_VALIDITY,
    *,
    catalog_path: Path = DEFAULT_CATALOG,
) -> dict[str, Any]:
    record = _load_object(path.resolve(), "validity record")
    catalog = _load_object(catalog_path.resolve(), "case catalog")
    validate_validity_record(record, catalog=catalog)
    return record


def validity_index(record: Mapping[str, Any]) -> dict[tuple[str, int], Mapping[str, Any]]:
    return {
        (item["case_id"], item["case_revision"]): item
        for item in record["entries"]
    }


def classify_observation(
    entry: Mapping[str, Any] | None,
    *,
    quality_population: str,
    artifact_retention: str,
    artifact_completeness: str = "not-retained",
    artifact_available: bool = False,
) -> dict[str, str]:
    """Classify one quality observation without promoting missing evidence."""

    if entry is None:
        return {"status": "not-audited", "reason": "case-revision-not-audited"}
    if entry["design_status"] == "ineligible":
        return {"status": "excluded", "reason": "case-design-ineligible"}
    if quality_population == "quality-unknown":
        return {"status": "excluded", "reason": "quality-unobserved"}
    if entry["design_status"] == "conditional":
        return {"status": "conditional", "reason": "case-design-conditional"}
    requirement = entry["artifact_retention_requirement"]
    artifact_required = requirement == "required-for-all-quality" or (
        requirement == "required-for-fail-adjudication"
        and quality_population == "quality-fail"
    )
    if artifact_required and artifact_retention != "task-artifacts":
        return {"status": "conditional", "reason": "task-artifact-not-retained"}
    if artifact_required and artifact_completeness != "complete":
        return {"status": "conditional", "reason": "task-artifact-partial"}
    if artifact_required and not artifact_available:
        return {"status": "conditional", "reason": "task-artifact-missing"}
    return {"status": "eligible", "reason": "case-and-observation-gates-pass"}


def summarize_case_validity(
    case: Mapping[str, Any],
    validity: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Summarize case/observation gates while leaving comparison gates open."""

    identity = case["primary_stratum"]["case"]
    if validity is None:
        entry = None
        policy: Mapping[str, Any] | None = None
    else:
        entry = validity_index(validity).get((identity["case_id"], identity["revision"]))
        policy = validity["policy"]
    observations: list[dict[str, Any]] = []
    for sample in case["samples"]:
        auditability = sample.get(
            "artifact_auditability",
            {
                "retention": "content-free-only",
                "completeness": "not-retained",
                "file_count": 0,
                "total_bytes": 0,
            },
        )
        classification = classify_observation(
            entry,
            quality_population=sample["quality_population"],
            artifact_retention=auditability["retention"],
            artifact_completeness=auditability["completeness"],
            artifact_available=(
                auditability["file_count"] > 0
                and sample["outcome"]["artifact"] == "valid"
            ),
        )
        observations.append(
            {
                "run_id": sample["run_id"],
                "status": classification["status"],
                "reason": classification["reason"],
                "artifact_retention": auditability["retention"],
                "artifact_completeness": auditability["completeness"],
                "artifact_file_count": auditability["file_count"],
                "outcome_artifact": sample["outcome"]["artifact"],
            }
        )
    status_counts = {
        status: sum(item["status"] == status for item in observations)
        for status in ("eligible", "conditional", "excluded", "not-audited")
    }
    observation_reason_codes = list(
        dict.fromkeys(
            item["reason"]
            for item in observations
            if item["status"] != "eligible"
        )
    )
    if entry is None:
        use = "not-audited"
        design_status = "not-audited"
        reason_codes = ["case-revision-not-audited"]
    elif entry["design_status"] == "ineligible":
        use = "excluded"
        design_status = entry["design_status"]
        reason_codes = [*entry["reason_codes"], *observation_reason_codes]
    elif not (status_counts["eligible"] or status_counts["conditional"]):
        use = "excluded"
        design_status = entry["design_status"]
        reason_codes = [
            *entry["reason_codes"],
            *observation_reason_codes,
            "no-observed-quality",
        ]
    elif entry["design_status"] == "conditional" or status_counts["conditional"]:
        use = "conditional-only"
        design_status = entry["design_status"]
        reason_codes = [*entry["reason_codes"], *observation_reason_codes]
    elif status_counts["eligible"]:
        use = "eligible-pending-comparison-gates"
        design_status = entry["design_status"]
        reason_codes = [*entry["reason_codes"], *observation_reason_codes]
    else:
        use = "excluded"
        design_status = entry["design_status"]
        reason_codes = [*entry["reason_codes"], "no-observed-quality"]
    reason_codes = list(dict.fromkeys(reason_codes))
    return {
        "scope": "case-and-observation-gates",
        "design_status": design_status,
        "effort_quality_use": use,
        "observation_status_counts": status_counts,
        "reason_codes": reason_codes,
        "comparison_gate_status": "not-evaluated",
        "comparison_gates": (
            list(policy["comparison_gates"]) if policy is not None else []
        ),
        "observations": observations,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validity", type=Path, default=DEFAULT_VALIDITY)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        record = load_validated_validity(args.validity, catalog_path=args.catalog)
    except (ContractValidationError, DurationStudyError, OSError, ValueError) as exc:
        print(f"duration validity validation failed: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "status": "pass",
                "validity_id": record["validity_id"],
                "entries": len(record["entries"]),
                "catalog_digest": record["catalog"]["digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

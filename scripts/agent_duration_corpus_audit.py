#!/usr/bin/env python3
"""Finite, provider-free calibration audit for the duration-study case corpus.

This module deliberately has no dependency on a provider runner.  It builds the
checked-in disposable fixtures, installs private calibration variants, and runs
only their deterministic evaluators.  The public ``audit_catalog`` entry point
accepts a runner so control-plane behavior can be tested without touching disk
or starting subprocesses.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import sys
import tempfile
import time
from typing import Any, Callable, Mapping, Protocol, Sequence

from agent_contracts import load_json
from agent_duration_fixtures import (
    DEFAULT_CATALOG,
    _install_known_good_for_test,
    _install_mutant_for_test,
    _install_valid_alternative_for_test,
    _recipe_for_case,
    build_fixture,
    evaluate_fixture,
    evaluate_fixture_isolated,
)
from agent_duration_study import (
    DurationStudyError,
    ROOT,
    atomic_write_json,
    content_digest,
)


MAX_CATALOG_CASES = 512
FIXED_AUDIT_TIME = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
FAILURE_POLICIES = ("fail-fast", "continue")


class CorpusAuditError(DurationStudyError):
    """Raised when an audit cannot safely be configured or selected."""


class AuditSafetyError(CorpusAuditError):
    """Raised before execution when the requested case bound is exceeded."""


@dataclass(frozen=True)
class EvaluationOutcome:
    """The only evaluator facts needed by the content-free audit engine."""

    status: str
    failed_check_ids: frozenset[str]


class CorpusAuditRunner(Protocol):
    """Dependency boundary between the control plane and fixture execution."""

    def capsule_digest_matches(self, entry: Mapping[str, Any]) -> bool: ...

    def declared_mutants(
        self, entry: Mapping[str, Any]
    ) -> Mapping[str, Sequence[str]]: ...

    def declared_valid_alternatives(self, entry: Mapping[str, Any]) -> Sequence[str]: ...

    def build(self, entry: Mapping[str, Any]) -> Any: ...

    def initial_failed(self, artifact: Any) -> bool: ...

    def install_known_good(self, entry: Mapping[str, Any], artifact: Any) -> None: ...

    def install_mutant(
        self, entry: Mapping[str, Any], mutant_id: str, artifact: Any
    ) -> None: ...

    def install_valid_alternative(
        self, entry: Mapping[str, Any], alternative_id: str, artifact: Any
    ) -> None: ...

    def evaluate(self, artifact: Any) -> EvaluationOutcome: ...

    def snapshot_key(self, artifact: Any) -> Any: ...


@dataclass(frozen=True)
class FixtureArtifact:
    directory: Path
    manifest: dict[str, Any]


class FixtureAuditRunner:
    """Run checked-in calibration fixtures without invoking an AI provider."""

    def __init__(
        self,
        catalog: Mapping[str, Any],
        work_root: Path,
        *,
        repository_root: Path = ROOT,
        isolated_image: str | None = None,
        docker_bin: str = "docker",
        evaluator_timeout_seconds: float = 30.0,
    ) -> None:
        if isolated_image is not None and not isolated_image:
            raise CorpusAuditError("isolated evaluator image must not be empty")
        if (
            not math.isfinite(evaluator_timeout_seconds)
            or evaluator_timeout_seconds <= 0
            or evaluator_timeout_seconds > 300
        ):
            raise CorpusAuditError(
                "evaluator timeout must be greater than zero and at most 300 seconds"
            )
        self._catalog = catalog
        self._work_root = work_root
        self._repository_root = repository_root.resolve()
        self._isolated_image = isolated_image
        self._docker_bin = docker_bin
        self._evaluator_timeout_seconds = evaluator_timeout_seconds
        self._catalog_paths: dict[str, Path] = {}
        self._artifact_counter = 0

    def capsule_digest_matches(self, entry: Mapping[str, Any]) -> bool:
        case = entry["case"]
        fixture = entry["fixture"]
        raw_path = fixture["capsule_path"]
        capsule = Path(raw_path)
        if capsule.is_absolute() or ".." in capsule.parts:
            return False
        resolved = (self._repository_root / capsule).resolve()
        try:
            resolved.relative_to(self._repository_root)
        except ValueError:
            return False
        if not resolved.is_file():
            return False
        return content_digest(resolved.read_bytes()) == case["capsule_digest"]

    def declared_mutants(
        self, entry: Mapping[str, Any]
    ) -> Mapping[str, Sequence[str]]:
        case_id = entry["case"]["case_id"]
        recipe_id = entry["fixture"]["recipe_id"]
        recipe = _recipe_for_case(case_id, recipe_id)
        mutants = recipe.get("mutants")
        if not isinstance(mutants, dict) or not mutants:
            raise CorpusAuditError("fixture recipe must declare at least one mutant")
        declared: dict[str, tuple[str, ...]] = {}
        for mutant_id in sorted(mutants):
            mutant = mutants[mutant_id]
            expected = mutant.get("expected_failed_check_ids") if isinstance(mutant, dict) else None
            if (
                not isinstance(mutant_id, str)
                or SAFE_ID.fullmatch(mutant_id) is None
                or not isinstance(expected, list)
                or not expected
                or not all(isinstance(item, str) and item for item in expected)
            ):
                raise CorpusAuditError("fixture recipe mutant declaration is invalid")
            declared[mutant_id] = tuple(expected)
        return declared

    def declared_valid_alternatives(self, entry: Mapping[str, Any]) -> Sequence[str]:
        case_id = entry["case"]["case_id"]
        recipe_id = entry["fixture"]["recipe_id"]
        recipe = _recipe_for_case(case_id, recipe_id)
        alternatives = recipe.get("valid_alternatives", {})
        if not isinstance(alternatives, dict):
            raise CorpusAuditError("fixture valid alternatives declaration is invalid")
        declared: list[str] = []
        for alternative_id in sorted(alternatives):
            alternative = alternatives[alternative_id]
            files = alternative.get("files") if isinstance(alternative, dict) else None
            if (
                not isinstance(alternative_id, str)
                or SAFE_ID.fullmatch(alternative_id) is None
                or not isinstance(files, dict)
                or not files
            ):
                raise CorpusAuditError("fixture valid alternative declaration is invalid")
            declared.append(alternative_id)
        return declared

    def _catalog_path(self, entry: Mapping[str, Any]) -> Path:
        case_id = entry["case"]["case_id"]
        existing = self._catalog_paths.get(case_id)
        if existing is not None:
            return existing
        case_root = self._work_root / f"case-{len(self._catalog_paths) + 1:03d}"
        case_root.mkdir(mode=0o700, parents=True)
        path = case_root / "catalog.json"
        fragment = {
            "schema_version": self._catalog["schema_version"],
            "catalog_id": self._catalog["catalog_id"],
            "revision": self._catalog["revision"],
            "published_at": self._catalog["published_at"],
            "entries": [copy.deepcopy(entry)],
        }
        path.write_text(
            json.dumps(fragment, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        path.chmod(0o600)
        self._catalog_paths[case_id] = path
        return path

    def build(self, entry: Mapping[str, Any]) -> FixtureArtifact:
        self._artifact_counter += 1
        directory = self._work_root / f"fixture-{self._artifact_counter:04d}"
        manifest = build_fixture(
            entry["case"]["case_id"],
            directory,
            catalog_path=self._catalog_path(entry),
            fixture_id=f"corpus-audit-{self._artifact_counter:04d}",
            now=FIXED_AUDIT_TIME,
        )
        return FixtureArtifact(directory=directory, manifest=manifest)

    def initial_failed(self, artifact: FixtureArtifact) -> bool:
        oracle = artifact.manifest.get("initial_oracle")
        return (
            isinstance(oracle, dict)
            and oracle.get("expected") == "fail"
            and oracle.get("observed") == "fail"
            and self.evaluate(artifact).status == "fail"
        )

    def install_known_good(
        self, entry: Mapping[str, Any], artifact: FixtureArtifact
    ) -> None:
        _install_known_good_for_test(
            entry["case"]["case_id"], artifact.directory / "workspace"
        )

    def install_mutant(
        self,
        entry: Mapping[str, Any],
        mutant_id: str,
        artifact: FixtureArtifact,
    ) -> None:
        _install_mutant_for_test(
            entry["case"]["case_id"],
            mutant_id,
            artifact.directory / "workspace",
        )

    def install_valid_alternative(
        self,
        entry: Mapping[str, Any],
        alternative_id: str,
        artifact: FixtureArtifact,
    ) -> None:
        _install_valid_alternative_for_test(
            entry["case"]["case_id"],
            alternative_id,
            artifact.directory / "workspace",
        )

    def evaluate(self, artifact: FixtureArtifact) -> EvaluationOutcome:
        if self._isolated_image is None:
            result = evaluate_fixture(artifact.directory)
        else:
            result = evaluate_fixture_isolated(
                artifact.directory,
                image=self._isolated_image,
                docker_bin=self._docker_bin,
                timeout_seconds=self._evaluator_timeout_seconds,
            )
        score = result.get("score")
        failed = score.get("failed_check_ids") if isinstance(score, dict) else None
        if result.get("status") not in {"pass", "fail"} or not isinstance(failed, list):
            raise CorpusAuditError("fixture evaluator returned an invalid result")
        if not all(isinstance(item, str) and item for item in failed):
            raise CorpusAuditError("fixture evaluator returned invalid failed check IDs")
        return EvaluationOutcome(result["status"], frozenset(failed))

    def snapshot_key(self, artifact: FixtureArtifact) -> Any:
        return copy.deepcopy(
            {
                "snapshot": artifact.manifest.get("snapshot"),
                "workspace_files": artifact.manifest.get("workspace_files"),
            }
        )


def _duration_ms(started_ns: int, clock_ns: Callable[[], int]) -> float:
    return round(max(0, clock_ns() - started_ns) / 1_000_000, 3)


def _check(
    check_id: str,
    operation: Callable[[], bool],
    *,
    clock_ns: Callable[[], int],
) -> tuple[dict[str, Any], bool]:
    started_ns = clock_ns()
    try:
        passed = operation() is True
    except Exception:  # The content-free result intentionally suppresses fixture details.
        passed = False
    return (
        {
            "check_id": check_id,
            "status": "pass" if passed else "fail",
            "duration_ms": _duration_ms(started_ns, clock_ns),
        },
        passed,
    )


def _catalog_entries(catalog: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    entries = catalog.get("entries")
    if not isinstance(entries, list) or not entries or len(entries) > MAX_CATALOG_CASES:
        raise CorpusAuditError("catalog entries must be a non-empty bounded array")
    for key in ("schema_version", "catalog_id", "revision", "published_at"):
        if key not in catalog:
            raise CorpusAuditError("catalog header is incomplete")

    result: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise CorpusAuditError("catalog entry must be an object")
        case = entry.get("case")
        fixture = entry.get("fixture")
        if not isinstance(case, dict) or not isinstance(fixture, dict):
            raise CorpusAuditError("catalog entry case and fixture must be objects")
        case_id = case.get("case_id")
        family = case.get("family")
        if (
            not isinstance(case_id, str)
            or SAFE_ID.fullmatch(case_id) is None
            or not isinstance(family, str)
            or not family
            or fixture.get("case_id") != case_id
            or not isinstance(fixture.get("recipe_id"), str)
            or not isinstance(fixture.get("capsule_path"), str)
            or SHA256.fullmatch(case.get("capsule_digest", "")) is None
        ):
            raise CorpusAuditError("catalog entry identity is invalid")
        if case_id in seen:
            raise CorpusAuditError("catalog case IDs must be unique")
        seen.add(case_id)
        result.append(entry)
    return result


def select_catalog_entries(
    catalog: Mapping[str, Any],
    *,
    families: Sequence[str] = (),
    case_ids: Sequence[str] = (),
) -> list[Mapping[str, Any]]:
    """Select deterministically and reject misspelled filters instead of doing no work."""

    entries = _catalog_entries(catalog)
    family_filter = set(families)
    case_filter = set(case_ids)
    available_families = {entry["case"]["family"] for entry in entries}
    available_cases = {entry["case"]["case_id"] for entry in entries}
    if not family_filter.issubset(available_families):
        raise CorpusAuditError("family filter does not exist in the catalog")
    if not case_filter.issubset(available_cases):
        raise CorpusAuditError("case filter does not exist in the catalog")
    selected = [
        entry
        for entry in entries
        if (not family_filter or entry["case"]["family"] in family_filter)
        and (not case_filter or entry["case"]["case_id"] in case_filter)
    ]
    if not selected:
        raise CorpusAuditError("catalog filters select no cases")
    return sorted(selected, key=lambda entry: entry["case"]["case_id"])


def _audit_case(
    entry: Mapping[str, Any],
    runner: CorpusAuditRunner,
    *,
    failure_policy: str,
    clock_ns: Callable[[], int],
) -> dict[str, Any]:
    started_ns = clock_ns()
    checks: list[dict[str, Any]] = []
    valid_alternative_results: list[dict[str, Any]] = []
    mutant_results: list[dict[str, Any]] = []
    case_failed = False

    def add_check(check_id: str, operation: Callable[[], bool]) -> bool:
        nonlocal case_failed
        result, passed = _check(check_id, operation, clock_ns=clock_ns)
        checks.append(result)
        case_failed = case_failed or not passed
        return passed

    if not add_check("capsule-digest", lambda: runner.capsule_digest_matches(entry)):
        return _case_result(
            entry, checks, valid_alternative_results, mutant_results, started_ns, clock_ns
        )

    declared: Mapping[str, Sequence[str]] = {}
    declared_valid_alternatives: Sequence[str] = ()

    def load_declarations() -> bool:
        nonlocal declared, declared_valid_alternatives
        declared = runner.declared_mutants(entry)
        declared_valid_alternatives = runner.declared_valid_alternatives(entry)
        return bool(declared)

    if not add_check("recipe-registry", load_declarations):
        return _case_result(
            entry, checks, valid_alternative_results, mutant_results, started_ns, clock_ns
        )

    initial_artifact: Any = None
    initial_snapshot_key: Any = None

    def build_initial() -> bool:
        nonlocal initial_artifact, initial_snapshot_key
        initial_artifact = runner.build(entry)
        if not runner.initial_failed(initial_artifact):
            return False
        initial_snapshot_key = copy.deepcopy(runner.snapshot_key(initial_artifact))
        return True

    if not add_check("initial-fail", build_initial):
        return _case_result(
            entry, checks, valid_alternative_results, mutant_results, started_ns, clock_ns
        )

    def known_good_passes() -> bool:
        runner.install_known_good(entry, initial_artifact)
        return runner.evaluate(initial_artifact).status == "pass"

    known_good_ok = add_check("known-good-full-pass", known_good_passes)
    if not known_good_ok and failure_policy == "fail-fast":
        return _case_result(
            entry, checks, valid_alternative_results, mutant_results, started_ns, clock_ns
        )

    for alternative_id in declared_valid_alternatives:
        alternative_started_ns = clock_ns()

        def valid_alternative_passes() -> bool:
            artifact = runner.build(entry)
            runner.install_valid_alternative(entry, alternative_id, artifact)
            return runner.evaluate(artifact).status == "pass"

        alternative_check, alternative_passed = _check(
            "valid-alternative-full-pass",
            valid_alternative_passes,
            clock_ns=clock_ns,
        )
        case_failed = case_failed or not alternative_passed
        valid_alternative_results.append(
            {
                "alternative_id": alternative_id,
                "status": "pass" if alternative_passed else "fail",
                "duration_ms": _duration_ms(alternative_started_ns, clock_ns),
                "checks": [alternative_check],
            }
        )
        if not alternative_passed and failure_policy == "fail-fast":
            return _case_result(
                entry,
                checks,
                valid_alternative_results,
                mutant_results,
                started_ns,
                clock_ns,
                case_failed,
            )

    def snapshot_reproduces() -> bool:
        reproduced = runner.build(entry)
        return (
            runner.initial_failed(reproduced)
            and initial_snapshot_key == runner.snapshot_key(reproduced)
        )

    snapshot_ok = add_check("snapshot-reproducibility", snapshot_reproduces)
    if not snapshot_ok and failure_policy == "fail-fast":
        return _case_result(
            entry, checks, valid_alternative_results, mutant_results, started_ns, clock_ns
        )

    for mutant_id in sorted(declared):
        mutant_started_ns = clock_ns()
        mutant_checks: list[dict[str, Any]] = []
        evaluation: EvaluationOutcome | None = None

        def mutant_rejected() -> bool:
            nonlocal evaluation
            artifact = runner.build(entry)
            runner.install_mutant(entry, mutant_id, artifact)
            evaluation = runner.evaluate(artifact)
            return evaluation.status == "fail"

        rejected_result, rejected = _check(
            "mutant-rejected", mutant_rejected, clock_ns=clock_ns
        )
        mutant_checks.append(rejected_result)

        def expected_failures_observed() -> bool:
            return evaluation is not None and set(declared[mutant_id]).issubset(
                evaluation.failed_check_ids
            )

        expected_result, expected_observed = _check(
            "expected-failed-checks-subset",
            expected_failures_observed,
            clock_ns=clock_ns,
        )
        mutant_checks.append(expected_result)
        mutant_passed = rejected and expected_observed
        case_failed = case_failed or not mutant_passed
        mutant_results.append(
            {
                "mutant_id": mutant_id,
                "status": "pass" if mutant_passed else "fail",
                "duration_ms": _duration_ms(mutant_started_ns, clock_ns),
                "checks": mutant_checks,
            }
        )
        if not mutant_passed and failure_policy == "fail-fast":
            break

    return _case_result(
        entry,
        checks,
        valid_alternative_results,
        mutant_results,
        started_ns,
        clock_ns,
        case_failed,
    )


def _case_result(
    entry: Mapping[str, Any],
    checks: list[dict[str, Any]],
    valid_alternatives: list[dict[str, Any]],
    mutants: list[dict[str, Any]],
    started_ns: int,
    clock_ns: Callable[[], int],
    failed: bool | None = None,
) -> dict[str, Any]:
    if failed is None:
        failed = (
            any(item["status"] != "pass" for item in checks)
            or any(item["status"] != "pass" for item in valid_alternatives)
            or any(item["status"] != "pass" for item in mutants)
        )
    return {
        "case_id": entry["case"]["case_id"],
        "family": entry["case"]["family"],
        "status": "fail" if failed else "pass",
        "duration_ms": _duration_ms(started_ns, clock_ns),
        "checks": checks,
        "valid_alternatives": valid_alternatives,
        "mutants": mutants,
    }


def audit_catalog(
    catalog: Mapping[str, Any],
    runner: CorpusAuditRunner,
    *,
    families: Sequence[str] = (),
    case_ids: Sequence[str] = (),
    max_cases: int,
    failure_policy: str,
    clock_ns: Callable[[], int] = time.monotonic_ns,
) -> dict[str, Any]:
    """Audit a bounded selection and return content-free calibration status.

    The safety cap is checked after filtering but before any runner method is
    called.  ``fail-fast`` stops at the first failed check or mutant; ``continue``
    finishes the remaining independent checks and selected cases.
    """

    if failure_policy not in FAILURE_POLICIES:
        raise CorpusAuditError("failure policy must be fail-fast or continue")
    if isinstance(max_cases, bool) or not isinstance(max_cases, int):
        raise AuditSafetyError("max-cases must be an integer")
    if max_cases < 1 or max_cases > MAX_CATALOG_CASES:
        raise AuditSafetyError(f"max-cases must be between 1 and {MAX_CATALOG_CASES}")

    selected = select_catalog_entries(catalog, families=families, case_ids=case_ids)
    if len(selected) > max_cases:
        raise AuditSafetyError("selected case count exceeds max-cases before execution")

    started_ns = clock_ns()
    case_results: list[dict[str, Any]] = []
    for entry in selected:
        result = _audit_case(
            entry,
            runner,
            failure_policy=failure_policy,
            clock_ns=clock_ns,
        )
        case_results.append(result)
        if result["status"] == "fail" and failure_policy == "fail-fast":
            break

    passed = len(case_results) == len(selected) and all(
        item["status"] == "pass" for item in case_results
    )
    return {
        "schema_version": 1,
        "status": "pass" if passed else "fail",
        "duration_ms": _duration_ms(started_ns, clock_ns),
        "cases": case_results,
    }


def _positive_case_cap(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if value < 1 or value > MAX_CATALOG_CASES:
        raise argparse.ArgumentTypeError(f"must be between 1 and {MAX_CATALOG_CASES}")
    return value


def _bounded_timeout(raw: str) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if not math.isfinite(value) or value <= 0 or value > 300:
        raise argparse.ArgumentTypeError("must be greater than zero and at most 300")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument(
        "--family",
        action="append",
        default=[],
        help="audit one family; repeat to select more than one",
    )
    parser.add_argument(
        "--case-id",
        action="append",
        default=[],
        help="audit one case ID; repeat to select more than one",
    )
    parser.add_argument(
        "--max-cases",
        type=_positive_case_cap,
        required=True,
        help="explicit pre-execution safety cap for the filtered selection",
    )
    policy = parser.add_mutually_exclusive_group(required=True)
    policy.add_argument("--fail-fast", action="store_true")
    policy.add_argument("--continue-on-failure", action="store_true")
    parser.add_argument(
        "--isolated-image",
        help="run fixture evaluators in the existing network-disabled image",
    )
    parser.add_argument("--docker-bin", default="docker")
    parser.add_argument(
        "--evaluator-timeout-seconds",
        type=_bounded_timeout,
        default=30.0,
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="atomically create a private JSON audit record instead of printing all case details",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        catalog = load_json(args.catalog)
        if not isinstance(catalog, dict):
            raise CorpusAuditError("catalog root must be an object")
        with tempfile.TemporaryDirectory(prefix="duration-corpus-audit-") as raw_temp:
            runner = FixtureAuditRunner(
                catalog,
                Path(raw_temp),
                isolated_image=args.isolated_image,
                docker_bin=args.docker_bin,
                evaluator_timeout_seconds=args.evaluator_timeout_seconds,
            )
            result = audit_catalog(
                catalog,
                runner,
                families=args.family,
                case_ids=args.case_id,
                max_cases=args.max_cases,
                failure_policy=("fail-fast" if args.fail_fast else "continue"),
            )
    except (CorpusAuditError, DurationStudyError, OSError, ValueError) as exc:
        print(f"corpus audit configuration failed: {exc}", file=sys.stderr)
        return 2
    if args.output is None:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        atomic_write_json(args.output.resolve(), result)
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "cases": len(result["cases"]),
                    "passed": sum(item["status"] == "pass" for item in result["cases"]),
                    "output": str(args.output.resolve()),
                },
                sort_keys=True,
            )
        )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

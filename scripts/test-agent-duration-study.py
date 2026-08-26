#!/usr/bin/env python3

from __future__ import annotations

import copy
import json
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
CLI = SCRIPT_DIR / "agent-duration-study"
sys.path.insert(0, str(SCRIPT_DIR))

from agent_contracts import ContractValidationError  # noqa: E402
from agent_duration_study import (  # noqa: E402
    DurationStudyError,
    atomic_write_json,
    build_fake_run,
    canonical_quality_pass,
    derive_durations,
    interval_union_ms,
    load_schema,
    peak_concurrency,
    validate_record,
    validate_run_record,
)


class AgentDurationStudyTests(unittest.TestCase):
    def valid_study(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "study_id": "duration-atlas-fixture",
            "revision": 1,
            "created_at": "2026-01-01T00:00:00.000Z",
            "execution_mode": "explicit-finite-batch",
            "planning_resolution_ms": 1_000,
            "relative_precision_target": 0.2,
            "coverage_target": {
                "profile_ids": ["S-local-deterministic-python"],
                "observation_block_classes": ["same-case", "between-case"],
            },
            "limits": {
                "wall_clock_batch_ms": 60_000,
                "hard_sample_cap": 8,
                "max_concurrency": 1,
                "role": "runaway-safety-cap",
            },
            "reporting": {
                "typical_population": "quality-pass-user-result",
                "typical_quantile_low": 0.1,
                "typical_quantile_high": 0.9,
            },
        }

    def valid_case(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "case_id": "F03-S-fixture",
            "revision": 1,
            "capsule_digest": f"sha256:{'1' * 64}",
            "source_type": "fixture",
            "family": "failing-test-diagnosis",
            "size": "S",
            "profile_id": "S-local-deterministic-python",
            "descriptors": {
                "context_surface": "single-module",
                "artifact_surface": "answer-and-test",
                "coupling": "local",
                "validation_depth": ["unit"],
                "environment_setup": "none",
                "failure_distance": "local",
                "statefulness": "stateless",
                "language_toolchain": ["python"],
            },
            "ambiguity": "exact",
            "oracle_strength": "deterministic",
            "decomposability": "serial",
            "artifact_type": "answer",
            "strong_online_oracle": True,
        }

    def valid_capability(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "capability_id": "fixture-cli-v1",
            "observed_at": "2026-01-01T00:00:00.000Z",
            "model_identity": {
                "requested_alias": "fixture-model",
                "requested_source": "flag",
                "resolved_id": "fixture-model-v1",
                "identity_confidence": "exact",
            },
            "runtime_identity": {
                "provider": "fixture",
                "cli_name": "duration-fixture",
                "cli_version": "1",
                "cli_source": "fixture",
                "execution_surface": "fixture",
                "permission_mode": "automatic",
                "observed_at": "2026-01-01T00:00:00.000Z",
            },
            "setting_probes": [
                {
                    "namespace": "fixture.reasoning",
                    "key": "effort",
                    "requested_value": "deterministic",
                    "status": "applied",
                    "applied_value": "deterministic",
                }
            ],
            "surfaces": {
                "progress_artifact": "observed",
                "synthesis_envelope": "observed",
                "permission_mode": "automatic",
            },
        }

    def test_all_checked_in_schemas_are_valid_json_objects(self) -> None:
        for kind in ("study", "case", "capability", "run"):
            with self.subTest(kind=kind):
                schema = load_schema(kind)
                self.assertEqual(schema["type"], "object")
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_study_case_and_capability_contracts(self) -> None:
        validate_record("study", self.valid_study())
        validate_record("case", self.valid_case())
        validate_record("capability", self.valid_capability())

        invalid_study = self.valid_study()
        invalid_study["reporting"]["typical_quantile_low"] = 0.95  # type: ignore[index]
        with self.assertRaises(DurationStudyError):
            validate_record("study", invalid_study)

        invalid_capability = self.valid_capability()
        invalid_capability["setting_probes"][0].pop("applied_value")  # type: ignore[index,union-attr]
        with self.assertRaises(ContractValidationError):
            validate_record("capability", invalid_capability)

        unknown_with_applied = self.valid_capability()
        unknown_with_applied["setting_probes"][0]["status"] = "unknown"  # type: ignore[index]
        with self.assertRaises(DurationStudyError):
            validate_record("capability", unknown_with_applied)

    def test_every_fake_scenario_is_schema_and_semantically_valid(self) -> None:
        for scenario in (
            "delegated-complete",
            "solo-complete",
            "missing-progress",
            "timeout",
            "provider-failure",
            "nested-untracked",
        ):
            with self.subTest(scenario=scenario):
                validate_run_record(build_fake_run(scenario))

    def test_solo_online_validation_does_not_depend_on_synthesis(self) -> None:
        record = build_fake_run("solo-complete")
        self.assertEqual(record["landmarks"]["T3"]["status"], "not-applicable")
        self.assertEqual(record["landmarks"]["T4"]["status"], "not-applicable")
        self.assertEqual(record["durations_ms"]["online_validation"], 7.0)
        self.assertNotIn("synthesis_tail", record["durations_ms"])
        self.assertEqual(record["durations_ms"]["aggregate_worker"], 0.0)
        self.assertTrue(record["outcome"]["quality_pass"])
        self.assertEqual(record["outcome"]["quality_basis"], "strong-online-oracle")

    def test_missing_progress_is_not_filled_from_final_result(self) -> None:
        record = build_fake_run("missing-progress")
        self.assertEqual(record["coverage"]["first_artifact_resolution"], "not-observed")
        self.assertNotIn("first_artifact_latency", record["durations_ms"])
        self.assertIn("user_result", record["durations_ms"])

    def test_timeout_keeps_terminal_wait_without_claiming_a_result(self) -> None:
        record = build_fake_run("timeout")
        self.assertEqual(record["outcome"]["infrastructure"], "timeout")
        self.assertEqual(record["durations_ms"]["terminal_wall"], 32.0)
        self.assertNotIn("user_result", record["durations_ms"])
        self.assertNotIn("aggregate_worker", record["durations_ms"])
        self.assertEqual(record["configuration"]["peak_concurrent"], 1)
        self.assertEqual(record["coverage"]["worker_tree"], "untracked")
        self.assertIsNone(record["outcome"]["quality_pass"])

    def test_provider_failure_remains_a_failed_timed_sample(self) -> None:
        record = build_fake_run("provider-failure")
        self.assertEqual(record["outcome"]["infrastructure"], "failure")
        self.assertEqual(record["outcome"]["failure_class"], "provider-refusal")
        self.assertEqual(record["durations_ms"]["terminal_wall"], 12.0)
        self.assertNotIn("user_result", record["durations_ms"])

    def test_nested_untracked_worker_time_is_explicitly_a_lower_bound(self) -> None:
        record = build_fake_run("nested-untracked")
        self.assertTrue(record["coverage"]["nested_worker_detected"])
        self.assertEqual(record["coverage"]["worker_tree"], "lower-bound")
        self.assertEqual(record["outcome"]["failure_class"], "nested-worker-untracked")

    def test_canonical_quality_population(self) -> None:
        cases = (
            ("fail", "pass", True, (False, "online-fail")),
            ("unavailable", "pass", False, (True, "offline-score")),
            ("pass", "fail", True, (False, "offline-score")),
            ("pass", "not-run", True, (True, "strong-online-oracle")),
            ("pass", "not-run", False, (None, "unavailable")),
            ("partial", "partial", True, (None, "unavailable")),
        )
        for online, offline, strong, expected in cases:
            with self.subTest(online=online, offline=offline, strong=strong):
                self.assertEqual(
                    canonical_quality_pass(
                        online_acceptance=online,
                        offline_score=offline,
                        strong_online_oracle=strong,
                    ),
                    expected,
                )

    def test_worker_slot_time_and_active_union_are_not_flattened(self) -> None:
        intervals = [(0, 10_000_000), (5_000_000, 15_000_000)]
        self.assertEqual(interval_union_ms(intervals), 15.0)
        self.assertEqual(peak_concurrency(intervals), 2)
        self.assertEqual(sum(stop - start for start, stop in intervals) / 1_000_000, 20.0)

    def test_negative_clock_and_tampered_derived_value_are_rejected(self) -> None:
        record = build_fake_run("delegated-complete")
        tampered = copy.deepcopy(record)
        tampered["durations_ms"]["user_result"] += 1
        with self.assertRaises(DurationStudyError):
            validate_run_record(tampered)

        backwards = copy.deepcopy(record)
        backwards["landmarks"]["T1"]["monotonic_ns"] = (
            backwards["landmarks"]["T0"]["monotonic_ns"] - 1
        )
        with self.assertRaises(DurationStudyError):
            derive_durations(backwards)

    def test_tampered_coverage_and_offline_score_boundary_are_rejected(self) -> None:
        record = build_fake_run("delegated-complete")
        bad_coverage = copy.deepcopy(record)
        bad_coverage["coverage"]["first_artifact_resolution"] = "not-observed"
        with self.assertRaises(DurationStudyError):
            validate_run_record(bad_coverage)

        missing_score_clock = copy.deepcopy(record)
        missing_score_clock["landmarks"]["S0"] = {
            "status": "not-observed",
            "provenance": "declared-by-harness",
        }
        missing_score_clock["landmarks"]["S1"] = {
            "status": "not-observed",
            "provenance": "declared-by-harness",
        }
        missing_score_clock["durations_ms"] = derive_durations(missing_score_clock)
        missing_score_clock["coverage"]["clock_landmarks"] = [
            item
            for item in missing_score_clock["coverage"]["clock_landmarks"]
            if item not in {"S0", "S1"}
        ]
        with self.assertRaises(DurationStudyError):
            validate_run_record(missing_score_clock)

    def test_schema_rejects_content_and_duplicate_correlation(self) -> None:
        record = build_fake_run("delegated-complete")
        content_leak = copy.deepcopy(record)
        content_leak["prompt"] = "do not persist this"
        with self.assertRaises(ContractValidationError):
            validate_run_record(content_leak)

        duplicate = copy.deepcopy(record)
        duplicate["correlation"]["episode_ids"] = ["episode-1", "episode-1"]
        with self.assertRaises(ContractValidationError):
            validate_run_record(duplicate)

    def test_atomic_run_record_is_private_and_immutable(self) -> None:
        record = build_fake_run("solo-complete")
        with tempfile.TemporaryDirectory(prefix="duration-study-write-") as raw_temp:
            path = Path(raw_temp) / "runs" / "fixture-solo-complete.json"
            atomic_write_json(path, record)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), record)
            with self.assertRaises(DurationStudyError):
                atomic_write_json(path, record)
            self.assertEqual([item.name for item in path.parent.iterdir()], [path.name])

    def test_cli_writes_and_validates_a_fake_record(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-study-cli-") as raw_temp:
            output_dir = Path(raw_temp) / "runs"
            result = subprocess.run(
                [
                    str(CLI),
                    "fake-run",
                    "--scenario",
                    "delegated-complete",
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = json.loads(result.stdout)
            record_path = Path(summary["path"])
            self.assertTrue(record_path.is_file())

            validation = subprocess.run(
                [str(CLI), "validate", "--kind", "run", str(record_path)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)
            self.assertEqual(json.loads(validation.stdout)["status"], "valid")

            repeated = subprocess.run(
                [
                    str(CLI),
                    "fake-run",
                    "--scenario",
                    "delegated-complete",
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(repeated.returncode, 2)
            self.assertIn("refusing to overwrite immutable run record", repeated.stderr)


if __name__ == "__main__":
    unittest.main()

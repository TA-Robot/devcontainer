#!/usr/bin/env python3

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT_DIR = Path(__file__).resolve().parent
CLI = SCRIPT_DIR / "query-agent-duration-atlas"
sys.path.insert(0, str(SCRIPT_DIR))

from agent_duration_atlas import build_atlas, encode_atlas  # noqa: E402
from agent_duration_study import build_fake_run  # noqa: E402
from query_agent_duration_atlas import (  # noqa: E402
    AtlasQueryError,
    QueryFilters,
    build_query_result,
    encode_result,
    render_markdown,
)


def clone_run(record: dict[str, object], run_id: str) -> dict[str, object]:
    result = copy.deepcopy(record)
    result["run_id"] = run_id
    return result


def atlas_from(records: list[dict[str, object]]) -> dict[str, object]:
    return build_atlas(  # type: ignore[arg-type]
        records,
        max_records=len(records),
        max_input_bytes=8 * 1024 * 1024,
        max_output_bytes=8 * 1024 * 1024,
    )


def criterion_failure_run(record: dict[str, object], run_id: str) -> dict[str, object]:
    failed = clone_run(record, run_id)
    outcome = failed["outcome"]  # type: ignore[index]
    outcome.update(
        {
            "online_acceptance": "fail",
            "quality_pass": False,
            "quality_basis": "online-fail",
            "failure_class": "online-validation-failed",
        }
    )
    evaluator = failed["diagnostics"]["evaluator"]  # type: ignore[index]
    evaluator["status"] = "fail"
    evaluator["checks"][0].update(
        {"check_id": "hidden-contract", "scope": "hidden", "status": "fail", "exit_code": 1}
    )
    evaluator["score"] = {
        "resolution": "criterion",
        "passed": 0,
        "total": 1,
        "ratio": 0.0,
        "public_passed": 0,
        "public_total": 0,
        "hidden_passed": 0,
        "hidden_total": 1,
        "failed_check_ids": ["hidden-contract"],
        "all_checks_required": True,
    }
    return failed


class AgentDurationAtlasQueryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = build_fake_run("solo-complete")
        self.atlas = atlas_from([self.base])

    def query(
        self,
        atlas: dict[str, object] | None = None,
        *,
        mode: str = "summary",
        filters: QueryFilters | None = None,
        max_rows: int = 10,
        max_output_bytes: int = 64 * 1024,
        output_format: str = "json",
        compare_by: tuple[str, ...] = (),
        curve_by: str = "workers-actual",
    ) -> dict[str, object]:
        return build_query_result(  # type: ignore[arg-type]
            atlas or self.atlas,
            mode=mode,
            filters=filters or QueryFilters(),
            max_rows=max_rows,
            max_output_bytes=max_output_bytes,
            output_format=output_format,
            compare_by=compare_by,
            curve_by=curve_by,
        )

    def test_exact_primary_stratum_filter_returns_one_compact_row(self) -> None:
        result = self.query(
            filters=QueryFilters(
                family="failing-test-diagnosis",
                size="S",
                profile="S-local-deterministic-python",
                case_id="F03-S-fixture",
                case_revision=1,
                configuration_id="C0",
                relation="primary-only",
                participant_plan="primary-only",
                nested_delegation="disabled",
                independence_policy="fresh-context",
                lane="read",
                participant_role="orchestrator",
                provider="fixture",
                requested_model="fixture-model",
                resolved_model="fixture-model-v1",
                identity_confidence="exact",
                setting_namespace="fixture.reasoning",
                setting_key="effort",
                setting_status="applied",
                setting_applied_value="deterministic",
                cli_name="duration-fixture",
                cli_version="1",
                cli_source="fixture",
                execution_surface="fixture",
                permission_mode="automatic",
                study="duration-atlas-fixture",
                environment={
                    "image_digest": "sha256:" + "0" * 64,
                    "session_context": "fresh",
                    "dependency_cache": "not-applicable",
                },
            )
        )
        self.assertEqual(result["status"], "measured")
        self.assertEqual(result["match"], {"case_strata": 1, "displayed_rows": 1})
        row = result["rows"][0]
        self.assertEqual(row["case"], {"case_id": "F03-S-fixture", "revision": 1})
        self.assertIn("quality-pass-user-result", row["durations"])
        self.assertNotIn("samples", row)
        self.assertNotIn("source", row)
        self.assertEqual(row["freshness"]["status"], "unknown")

    def test_partial_summary_returns_refinement_dimensions_not_duration_rows(self) -> None:
        other = clone_run(self.base, "other-cli")
        other["participants"][0]["runtime_identity"]["cli_version"] = "2"  # type: ignore[index]
        other["participants"][0]["runtime_identity"]["permission_mode"] = "approval-gated"  # type: ignore[index]
        atlas = atlas_from([self.base, other])
        result = self.query(
            atlas,
            filters=QueryFilters(family="failing-test-diagnosis"),
        )
        self.assertEqual(result["status"], "refine")
        self.assertEqual(result["rows"], [])
        hints = {item["filter"] for item in result["refinement_hints"]}
        self.assertIn("--cli-version", hints)
        self.assertIn("--permission-mode", hints)
        self.assertNotIn("durations", result)

    def test_invalid_or_contradictory_filter_bounds_fail_closed(self) -> None:
        with self.assertRaisesRegex(AtlasQueryError, "case-revision"):
            self.query(filters=QueryFilters(case_revision=0))
        with self.assertRaisesRegex(AtlasQueryError, "workers-actual"):
            self.query(filters=QueryFilters(workers_actual=-1))
        with self.assertRaisesRegex(AtlasQueryError, "unknown environment"):
            self.query(filters=QueryFilters(environment={"typo_cache": "warm"}))
        with self.assertRaisesRegex(AtlasQueryError, "contradicts"):
            self.query(
                filters=QueryFilters(
                    setting_status="unknown",
                    setting_applied_value="medium",
                )
            )

    def test_no_exact_match_is_unmeasured_without_interpolation(self) -> None:
        result = self.query(filters=QueryFilters(provider="codex"))
        self.assertEqual(result["status"], "unmeasured")
        self.assertEqual(result["match"]["case_strata"], 0)
        self.assertTrue(result["rows"])
        self.assertTrue(all("dimension" in row and "durations" not in row for row in result["rows"]))
        serialized = json.dumps(result, sort_keys=True)
        self.assertNotIn("estimated", serialized)
        self.assertNotIn("nearest", serialized)

    def test_applied_value_filter_excludes_requested_only_unknown_setting(self) -> None:
        applied = clone_run(self.base, "applied")
        unknown = clone_run(self.base, "requested-only")
        setting = unknown["participants"][0]["generation_settings"][0]  # type: ignore[index]
        setting["status"] = "unknown"
        setting.pop("applied_value")
        atlas = atlas_from([applied, unknown])

        applied_result = self.query(
            atlas,
            filters=QueryFilters(
                setting_key="effort",
                setting_applied_value="deterministic",
            ),
        )
        self.assertEqual(applied_result["match"]["case_strata"], 1)
        self.assertEqual(
            applied_result["rows"][0]["participants"][0]["generation_settings"][0]["status"],
            "applied",
        )

        unknown_result = self.query(
            atlas,
            filters=QueryFilters(setting_key="effort", setting_status="unknown"),
        )
        self.assertEqual(unknown_result["match"]["case_strata"], 1)
        unknown_output = unknown_result["rows"][0]["participants"][0]["generation_settings"][0]
        self.assertEqual(unknown_output["status"], "unknown")
        self.assertNotIn("applied_value", unknown_output)

    def test_missing_progress_remains_not_observed_without_first_artifact_duration(self) -> None:
        atlas = atlas_from([build_fake_run("missing-progress")])
        result = self.query(atlas)
        row = result["rows"][0]
        self.assertNotIn("first-artifact-progress", row["durations"])
        self.assertEqual(
            row["evidence"]["first_artifact_resolution"],
            {
                "progress-envelope": 0,
                "not-observed": 1,
                "not-applicable": 0,
                "unknown": 0,
            },
        )

    def test_timeout_censoring_and_declared_cap_are_preserved(self) -> None:
        timeout = build_fake_run("timeout")
        atlas = atlas_from([timeout])
        result = self.query(atlas)
        row = result["rows"][0]
        self.assertEqual(row["evidence"]["quality_population"]["quality-unknown"], 1)
        self.assertEqual(row["censoring"]["counts"]["right-censored"], 1)
        self.assertEqual(row["censoring"]["safety_caps_ms"], [60_000])
        self.assertIn("censored-terminal", row["durations"])
        quality = row["evidence"]["quality_evidence"]
        self.assertEqual(quality["evaluator_status"]["not-run"], 1)
        self.assertEqual(quality["score_availability"]["unavailable"], 1)

    def test_selected_quality_score_and_failed_criteria_are_compactly_preserved(self) -> None:
        failed = criterion_failure_run(self.base, "criterion-failure")
        atlas = atlas_from([failed])
        result = self.query(atlas)
        quality = result["rows"][0]["evidence"]["quality_evidence"]
        self.assertEqual(quality["evaluator_status"]["fail"], 1)
        self.assertEqual(quality["check_count"]["value"], 1)
        self.assertEqual(quality["score_availability"], {"available": 1, "unavailable": 0})
        self.assertEqual(quality["criterion_score"]["ratio"]["value"], 0.0)
        self.assertEqual(quality["failed_criteria"]["unique_check_ids"], ["hidden-contract"])
        self.assertEqual(
            quality["failed_criteria"]["by_check_id"],
            [{"check_id": "hidden-contract", "sample_count": 1}],
        )

    def test_compare_row_cap_and_output_byte_cap_are_explicit(self) -> None:
        records: list[dict[str, object]] = []
        for index in range(5):
            record = clone_run(self.base, f"cli-{index}")
            record["participants"][0]["runtime_identity"]["cli_version"] = str(index)  # type: ignore[index]
            records.append(record)
        atlas = atlas_from(records)
        row_limited = self.query(
            atlas,
            mode="compare",
            max_rows=2,
            compare_by=("cli-version",),
        )
        self.assertEqual(len(row_limited["rows"]), 2)
        self.assertTrue(row_limited["truncation"]["truncated"])
        self.assertIn("max-rows", row_limited["truncation"]["reasons"])

        byte_limited = self.query(
            atlas,
            mode="compare",
            max_rows=5,
            max_output_bytes=2600,
            compare_by=("cli-version",),
        )
        encoded = encode_result(byte_limited, "json")
        self.assertLessEqual(len(encoded), 2600)
        self.assertTrue(byte_limited["truncation"]["truncated"])
        self.assertIn("max-output-bytes", byte_limited["truncation"]["reasons"])

    def test_query_and_markdown_rendering_are_deterministic_and_bounded(self) -> None:
        first = self.query(output_format="markdown", max_output_bytes=16 * 1024)
        second = self.query(output_format="markdown", max_output_bytes=16 * 1024)
        self.assertEqual(first, second)
        first_markdown = render_markdown(first)
        self.assertEqual(first_markdown, render_markdown(second))
        self.assertLessEqual(len(first_markdown.encode("utf-8")), 16 * 1024)
        self.assertIn("raw point", first_markdown)
        self.assertIn("/status:applied/applied:", first_markdown)
        self.assertNotIn("recommended configuration", first_markdown)

        requested_only = copy.deepcopy(self.base)
        setting = requested_only["participants"][0]["generation_settings"][0]
        setting["status"] = "unknown"
        setting.pop("applied_value")
        markdown = render_markdown(
            self.query(atlas_from([requested_only]), output_format="markdown")
        )
        self.assertIn("/status:unknown/applied:-", markdown)

    def test_coverage_is_identifier_only_and_preserves_missingness_counts(self) -> None:
        records = [self.base, build_fake_run("missing-progress"), build_fake_run("timeout")]
        records[1]["run_id"] = "coverage-missing"
        records[2]["run_id"] = "coverage-timeout"
        atlas = atlas_from(records)
        result = self.query(atlas, mode="coverage", max_rows=100)
        self.assertFalse(result["coverage"]["duration_values_included"])
        self.assertGreater(result["coverage"]["first_artifact_resolution"]["not-observed"], 0)
        self.assertGreater(result["coverage"]["censoring"]["right-censored"], 0)
        self.assertTrue(all("durations" not in row for row in result["rows"]))
        serialized = json.dumps(result, sort_keys=True)
        self.assertNotIn("run_digest", serialized)

    def test_curve_returns_only_observed_coordinates_without_interpolation(self) -> None:
        delegated = build_fake_run("delegated-complete")
        delegated["run_id"] = "curve-delegated"
        atlas = atlas_from([self.base, delegated])
        result = self.query(atlas, mode="curve", curve_by="workers-actual")
        coordinates = [row["curve"]["observed_coordinate"] for row in result["rows"]]
        self.assertEqual(coordinates, [0, 1])
        self.assertTrue(all(row["curve"]["interpolation"] == "none" for row in result["rows"]))
        serialized = json.dumps(result, sort_keys=True)
        self.assertNotIn("winner", serialized)
        self.assertNotIn("ranking", serialized)

    def test_unknown_atlas_schema_fails_closed(self) -> None:
        unknown = copy.deepcopy(self.atlas)
        unknown["schema_version"] = 999
        with self.assertRaises(AtlasQueryError):
            self.query(unknown)

    def test_cli_requires_both_caps_and_emits_json_or_markdown(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-atlas-query-cli-") as raw_temp:
            atlas_path = Path(raw_temp) / "atlas.json"
            atlas_path.write_bytes(encode_atlas(self.atlas))
            missing_caps = subprocess.run(
                [sys.executable, str(CLI), str(atlas_path)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(missing_caps.returncode, 2)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    str(atlas_path),
                    "--max-rows",
                    "1",
                    "--max-output-bytes",
                    "16384",
                    "--provider",
                    "fixture",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["status"], "measured")
            markdown = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    str(atlas_path),
                    "--max-rows",
                    "1",
                    "--max-output-bytes",
                    "16384",
                    "--format",
                    "markdown",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(markdown.returncode, 0, markdown.stderr)
            self.assertIn("# Duration atlas query", markdown.stdout)


if __name__ == "__main__":
    unittest.main()

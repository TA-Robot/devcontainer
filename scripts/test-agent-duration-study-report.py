#!/usr/bin/env python3

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
CLI = SCRIPT_DIR / "report-agent-duration-study"
CATALOG_PATH = ROOT / "experiments" / "multi-agent-duration" / "catalog" / "cases.json"
sys.path.insert(0, str(SCRIPT_DIR))

from agent_contracts import load_json  # noqa: E402
from agent_duration_atlas import AtlasError, build_atlas, encode_atlas  # noqa: E402
from agent_duration_study import build_fake_run, canonical_json_digest  # noqa: E402
from agent_duration_study_report import (  # noqa: E402
    StudyReportError,
    atomic_write_study_report,
    build_study_report,
    load_validated_atlas,
)


MATCHED_CASE_ID = "F03-S-PY-001"


class AgentDurationStudyReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_json(CATALOG_PATH)

    def matched_run(self, scenario: str = "solo-complete") -> dict[str, object]:
        record = build_fake_run(scenario)
        catalog_case = next(
            entry["case"]
            for entry in self.catalog["entries"]
            if entry["case"]["case_id"] == MATCHED_CASE_ID
        )
        for key in (
            "case_id",
            "revision",
            "capsule_digest",
            "source_type",
            "family",
            "size",
            "profile_id",
            "strong_online_oracle",
        ):
            record["case"][key] = catalog_case[key]
        record["case"]["catalog_digest"] = canonical_json_digest(self.catalog)
        return record

    def atlas(self, records: list[dict[str, object]]) -> dict[str, object]:
        return build_atlas(  # type: ignore[arg-type]
            records,
            max_records=len(records),
            max_input_bytes=8 * 1024 * 1024,
            max_output_bytes=8 * 1024 * 1024,
        )

    def report(self, atlas: dict[str, object], **overrides) -> str:
        arguments = {
            "catalog": self.catalog,
            "max_series": 20,
            "max_cases": 40,
            "max_output_bytes": 2 * 1024 * 1024,
        }
        arguments.update(overrides)
        return build_study_report(atlas, **arguments)  # type: ignore[arg-type]

    def fail_run(self, record: dict[str, object], run_id: str) -> dict[str, object]:
        failed = copy.deepcopy(record)
        failed["run_id"] = run_id
        failed["outcome"].update(  # type: ignore[union-attr]
            {
                "online_acceptance": "fail",
                "quality_pass": False,
                "quality_basis": "online-fail",
                "failure_class": "online-validation-failed",
            }
        )
        evaluator = failed["diagnostics"]["evaluator"]  # type: ignore[index]
        evaluator["status"] = "fail"
        evaluator["checks"][0].update({"status": "fail", "exit_code": 1})
        return failed

    def test_report_contains_exact_strata_coverage_provenance_and_no_decision_claim(self) -> None:
        atlas = self.atlas([self.matched_run()])
        report = self.report(atlas)
        self.assertIn("# Agent Duration Study Report", report)
        self.assertIn("## Methodology", report)
        self.assertIn("## Observation window and provenance", report)
        self.assertIn(atlas["source"]["run_set_digest"], report)  # type: ignore[index]
        self.assertIn("## Exact environment", report)
        self.assertIn('"machine_class": "deterministic-fixture"', report)
        self.assertIn('"resolved_id": "fixture-model-v1"', report)
        self.assertIn('"requested_value": "deterministic"', report)
        self.assertIn('"applied_value": "deterministic"', report)
        self.assertIn('"execution_surface": "fixture"', report)
        self.assertIn("Observed supplied-catalog cells: 1 / 36", report)
        self.assertIn("Unmeasured supplied-catalog cells: 35 / 36", report)
        self.assertIn("Digest compatibility: exact", report)
        self.assertIn("## Limitations", report)
        self.assertIn("aggregate-check; 1/1", report)
        self.assertNotIn("fixture-online-v1", report)
        for forbidden in ("winner", "recommendation", "selection", "band"):
            self.assertNotIn(forbidden, report.lower())

    def test_single_observation_is_a_raw_point_and_requested_only_is_not_promoted(self) -> None:
        record = self.matched_run()
        setting = record["participants"][0]["generation_settings"][0]  # type: ignore[index]
        setting["status"] = "unknown"
        setting.pop("applied_value")
        report = self.report(self.atlas([record]))
        self.assertIn("single observation; raw point", report)
        self.assertIn("| not available |", report)
        self.assertIn('"status": "unknown"', report)
        self.assertIn('"requested_value": "deterministic"', report)
        self.assertNotIn('"applied_value"', report)
        self.assertNotIn("band", report.lower())

    def test_same_case_points_range_quality_counts_and_failed_ids_are_preserved(self) -> None:
        first = self.matched_run()
        first["run_id"] = "quality-pass-one"
        second = copy.deepcopy(first)
        second["run_id"] = "quality-pass-two"
        second["block_id"] = "block-two"
        failed = self.fail_run(first, "quality-fail-one")
        failed["block_id"] = "block-three"
        report = self.report(self.atlas([first, second, failed]))
        self.assertIn("pass=2; fail=1; unknown=0", report)
        self.assertIn("3 same-case observations; raw points", report)
        self.assertIn("(observed min/max)", report)
        self.assertIn("fixture-online-v1", report)
        self.assertIn("aggregate-check; 0/1", report)
        self.assertIn("online=fail", report)
        self.assertIn("failure=online-validation-failed", report)
        self.assertIn("fail | 1 |", report)

    def test_declared_criterion_score_is_rendered_without_reconstruction(self) -> None:
        record = self.matched_run()
        record["diagnostics"]["evaluator"]["checks"][0]["scope"] = "hidden"  # type: ignore[index]
        record["diagnostics"]["evaluator"]["score"] = {  # type: ignore[index]
            "resolution": "criterion",
            "passed": 1,
            "total": 1,
            "ratio": 1.0,
            "public_passed": 0,
            "public_total": 0,
            "hidden_passed": 1,
            "hidden_total": 1,
            "failed_check_ids": [],
            "all_checks_required": True,
        }
        report = self.report(self.atlas([record]))
        self.assertIn("criterion; 1/1; ratio=1.0; public=0/0; hidden=1/1", report)
        self.assertIn("| none |", report)
        self.assertNotIn("fixture-online-v1", report)

    def test_null_quality_score_and_censoring_remain_explicit(self) -> None:
        timeout = self.matched_run("timeout")
        timeout["run_id"] = "timeout-observation"
        report = self.report(self.atlas([timeout]))
        self.assertIn("complete=0; right=1; administrative=0", report)
        self.assertIn("right-censored; observed-terminal=32.0 ms; declared-cap=60000 ms", report)
        self.assertIn("infrastructure=timeout", report)
        self.assertIn("not-run | 0 | unavailable | unavailable", report)
        self.assertNotIn("fixture-online-v1", report)

    def test_catalog_digest_unknown_case_and_revision_differences_are_reported(self) -> None:
        matched_atlas = self.atlas([self.matched_run()])
        revised_catalog = copy.deepcopy(self.catalog)
        revised_catalog["revision"] += 1
        target = next(
            entry["case"]
            for entry in revised_catalog["entries"]
            if entry["case"]["case_id"] == MATCHED_CASE_ID
        )
        target["revision"] += 1
        revised = build_study_report(
            matched_atlas,
            catalog=revised_catalog,
            max_series=1,
            max_cases=1,
            max_output_bytes=2 * 1024 * 1024,
        )
        self.assertIn("Digest compatibility: mismatch", revised)
        self.assertIn("earlier catalog revision number is not encoded", revised)
        self.assertIn("Case revision differences (1)", revised)
        self.assertIn(f"{MATCHED_CASE_ID}: atlas=1 catalog=2", revised)

        unknown_atlas = self.atlas([build_fake_run("solo-complete")])
        unknown = self.report(unknown_atlas)
        self.assertIn("Observed supplied-catalog cells: 0 / 36", unknown)
        self.assertIn("Unmeasured supplied-catalog cells: 36 / 36", unknown)
        self.assertIn("Atlas case IDs absent from supplied catalog (1)", unknown)
        self.assertIn("F03-S-fixture", unknown)

    def test_catalog_is_optional_without_inventing_unmeasured_cells(self) -> None:
        atlas = self.atlas([self.matched_run()])
        report = build_study_report(
            atlas,
            catalog=None,
            max_series=1,
            max_cases=1,
            max_output_bytes=2 * 1024 * 1024,
        )
        self.assertIn("No catalog was supplied", report)
        self.assertIn("unmeasured reference cells cannot be determined", report)
        self.assertIn("Catalog comparison: unavailable", report)

    def test_caps_fail_closed_instead_of_silently_truncating(self) -> None:
        one = self.matched_run()
        one["run_id"] = "series-one"
        two = copy.deepcopy(one)
        two["run_id"] = "series-two"
        two["participants"][0]["runtime_identity"]["cli_version"] = "2"  # type: ignore[index]
        atlas = self.atlas([one, two])
        with self.assertRaisesRegex(StudyReportError, "exceeding explicit max-series"):
            self.report(atlas, max_series=1)
        with self.assertRaisesRegex(StudyReportError, "exceeding explicit max-cases"):
            self.report(atlas, max_cases=1)
        with self.assertRaisesRegex(StudyReportError, "exceeding explicit max-output-bytes"):
            self.report(atlas, max_output_bytes=100)
        with self.assertRaisesRegex(StudyReportError, "max-series must be between"):
            self.report(atlas, max_series=0)

    def test_deterministic_render_and_atomic_replace_preserve_old_file_until_ready(self) -> None:
        atlas = self.atlas([self.matched_run()])
        first = self.report(atlas)
        second = self.report(atlas)
        self.assertEqual(first, second)
        self.assertTrue(first.endswith("\n"))
        with tempfile.TemporaryDirectory(prefix="duration-study-report-atomic-") as raw:
            output = Path(raw) / "report.md"
            output.write_bytes(b"old-report\n")
            observed: list[bytes] = []

            def replace(source: Path, destination: Path) -> None:
                observed.append(destination.read_bytes())
                self.assertTrue(source.read_text(encoding="utf-8").startswith("# Agent"))
                os.replace(source, destination)

            atomic_write_study_report(
                output,
                first,
                max_output_bytes=len(first.encode("utf-8")),
                replace=replace,
            )
            self.assertEqual(observed, [b"old-report\n"])
            self.assertEqual(output.read_text(encoding="utf-8"), first)
            stable = output.read_bytes()
            with self.assertRaisesRegex(StudyReportError, "before writing"):
                atomic_write_study_report(output, first, max_output_bytes=1)
            self.assertEqual(output.read_bytes(), stable)

    def test_loader_rejects_raw_run_instead_of_treating_it_as_an_atlas(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-study-report-input-") as raw:
            path = Path(raw) / "raw-run.json"
            path.write_text(json.dumps(self.matched_run()), encoding="utf-8")
            with self.assertRaises(AtlasError):
                load_validated_atlas(path)

    def test_cli_requires_all_caps_and_replaces_derived_markdown_provider_free(self) -> None:
        atlas = self.atlas([self.matched_run()])
        with tempfile.TemporaryDirectory(prefix="duration-study-report-cli-") as raw:
            directory = Path(raw)
            atlas_path = directory / "atlas.json"
            output = directory / "reports" / "study.md"
            atlas_path.write_bytes(encode_atlas(atlas))
            incomplete = subprocess.run(
                [sys.executable, str(CLI), str(atlas_path), "--output", str(output)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(incomplete.returncode, 2)
            self.assertFalse(output.exists())
            command = [
                sys.executable,
                str(CLI),
                str(atlas_path),
                "--output",
                str(output),
                "--max-series",
                "1",
                "--max-cases",
                "1",
                "--max-output-bytes",
                str(2 * 1024 * 1024),
            ]
            for _iteration in range(2):
                completed = subprocess.run(command, text=True, capture_output=True, check=False)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                summary = json.loads(completed.stdout)
                self.assertEqual(summary["provider_calls"], 0)
                self.assertEqual(summary["source_run_set_digest"], atlas["source"]["run_set_digest"])  # type: ignore[index]
            markdown = output.read_text(encoding="utf-8")
            self.assertTrue(markdown.startswith("# Agent Duration Study Report"))
            self.assertIn("Observed supplied-catalog cells: 1 / 36", markdown)


if __name__ == "__main__":
    unittest.main()

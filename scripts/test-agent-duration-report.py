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
ROOT = SCRIPT_DIR.parent
CLI = SCRIPT_DIR / "agent-duration-study"
sys.path.insert(0, str(SCRIPT_DIR))

from agent_duration_report import (  # noqa: E402
    build_raw_sample_report,
    load_run_records,
    render_raw_sample_table,
)
from agent_duration_study import (  # noqa: E402
    DurationStudyError,
    atomic_write_json,
    build_fake_run,
    validate_run_record,
)


def quality_fail_record() -> dict[str, object]:
    record = copy.deepcopy(build_fake_run("solo-complete"))
    record["run_id"] = "fixture-quality-fail"
    record["outcome"].update(  # type: ignore[union-attr]
        {
            "online_acceptance": "fail",
            "quality_pass": False,
            "quality_basis": "online-fail",
            "failure_class": "online-validation-failed",
        }
    )
    evaluator = record["diagnostics"]["evaluator"]  # type: ignore[index]
    evaluator["status"] = "fail"
    evaluator["checks"][0].update(  # type: ignore[index]
        {"status": "fail", "exit_code": 1}
    )
    setting = record["participants"][0]["generation_settings"][0]  # type: ignore[index]
    setting.update({"requested_value": "low", "status": "unknown"})
    setting.pop("applied_value")
    validate_run_record(record)  # type: ignore[arg-type]
    return record


class AgentDurationReportTests(unittest.TestCase):
    def write_inventory(self, directory: Path) -> None:
        pass_record = build_fake_run("solo-complete")
        pass_record["run_id"] = "fixture-quality-pass"
        unknown_record = build_fake_run("provider-failure")
        unknown_record["run_id"] = "fixture-quality-unknown"
        for record in (pass_record, quality_fail_record(), unknown_record):
            atomic_write_json(directory / f"{record['run_id']}.json", record)

    def test_report_keeps_quality_populations_and_duration_roles_separate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-report-") as raw_temp:
            directory = Path(raw_temp) / "runs"
            directory.mkdir()
            self.write_inventory(directory)
            records = load_run_records([directory])
            report = build_raw_sample_report(records)

            self.assertEqual(report["aggregation"], "none")
            self.assertFalse(report["selection_rule_generated"])
            self.assertEqual(
                report["counts"]["quality_population"],
                {
                    "quality-pass": 1,
                    "quality-fail": 1,
                    "quality-unknown": 1,
                },
            )
            roles = {
                sample["quality_population"]: sample["reported_duration"]["role"]
                for sample in report["samples"]
            }
            self.assertEqual(roles["quality-pass"], "quality-pass-user-result")
            self.assertEqual(roles["quality-fail"], "failed-terminal")
            self.assertEqual(roles["quality-unknown"], "unknown-terminal")
            serialized = json.dumps(report, sort_keys=True)
            self.assertNotIn("typical", serialized)
            self.assertNotIn("quantile", serialized)
            self.assertNotIn("recommended", serialized)

    def test_report_filters_and_limit_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-report-filter-") as raw_temp:
            directory = Path(raw_temp) / "runs"
            directory.mkdir()
            self.write_inventory(directory)
            records = load_run_records([directory])

            failed = build_raw_sample_report(records, quality="fail")
            self.assertEqual(failed["counts"]["matched_records"], 1)
            self.assertEqual(failed["samples"][0]["quality_population"], "quality-fail")
            limited = build_raw_sample_report(records, limit=1)
            self.assertTrue(limited["truncated"])
            self.assertEqual(limited["counts"]["displayed_records"], 1)
            with self.assertRaises(DurationStudyError):
                build_raw_sample_report(records, limit=501)

    def test_table_and_cli_expose_unknown_setting_without_aggregation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-report-cli-") as raw_temp:
            directory = Path(raw_temp) / "runs"
            directory.mkdir()
            self.write_inventory(directory)
            report = build_raw_sample_report(load_run_records([directory]), quality="fail")
            table = render_raw_sample_table(report)
            self.assertIn("effort=low/unknown", table)
            self.assertIn("failed-terminal", table)
            self.assertIn("aggregation: none", table)

            completed = subprocess.run(
                [
                    str(CLI),
                    "report-runs",
                    str(directory),
                    "--quality",
                    "fail",
                    "--format",
                    "json",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["counts"]["matched_records"], 1)
            self.assertEqual(payload["samples"][0]["quality_population"], "quality-fail")

    def test_duplicate_run_ids_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-report-duplicate-") as raw_temp:
            directory = Path(raw_temp)
            record = build_fake_run("solo-complete")
            atomic_write_json(directory / "one.json", record)
            duplicate = copy.deepcopy(record)
            atomic_write_json(directory / "two.json", duplicate)
            with self.assertRaises(DurationStudyError):
                load_run_records([directory])


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from agent_contracts import load_json  # noqa: E402
from agent_duration_batch import load_and_validate_batch  # noqa: E402
from agent_duration_batch_plan import HARD_MAX_RUNS, Series, plan_batch  # noqa: E402
from agent_duration_study import (  # noqa: E402
    DurationStudyError,
    canonical_json_digest,
    validate_record,
)


CATALOG = ROOT / "experiments" / "multi-agent-duration" / "catalog" / "cases.json"
PLANNER = SCRIPT_DIR / "plan-agent-duration-batch"
FAMILY = "bounded-implementation"


class AgentDurationBatchPlanTests(unittest.TestCase):
    def plan(self, **overrides):
        arguments = {
            "batch_id": "c0-fixture-batch",
            "study_id": "duration-atlas-fixture",
            "block_id": "c0-fixture-block",
            "series": [Series("codex", "gpt-5.6-sol", "xhigh")],
            "families": [FAMILY],
            "rotation_seed": 0,
            "repeat": 1,
            "max_runs": HARD_MAX_RUNS,
            "deadline_seconds": 600,
            "timeout_seconds": 120,
            "evaluator_timeout_seconds": 30,
            "output_bytes_cap": 65536,
            "created_at": "2026-08-27T01:02:03Z",
        }
        arguments.update(overrides)
        return plan_batch(load_json(CATALOG), **arguments)

    def size_sequence(self, manifest):
        catalog = load_json(CATALOG)
        sizes = {entry["case"]["case_id"]: entry["case"]["size"] for entry in catalog["entries"]}
        return [sizes[entry["case_id"]] for entry in manifest["entries"]]

    def cli_base(self, output: Path) -> list[str]:
        return [
            sys.executable,
            str(PLANNER),
            "--catalog",
            str(CATALOG),
            "--output",
            str(output),
            "--batch-id",
            "cli-batch",
            "--study-id",
            "cli-study",
            "--block-id",
            "cli-block",
            "--provider",
            "codex",
            "--model",
            "gpt-5.6-sol",
            "--effort",
            "xhigh",
            "--family",
            FAMILY,
            "--rotation-seed",
            "17",
            "--repeat",
            "1",
            "--max-runs",
            "3",
            "--deadline-seconds",
            "600",
            "--timeout-seconds",
            "120",
            "--evaluator-timeout-seconds",
            "30",
            "--output-bytes-cap",
            "65536",
        ]

    def test_manifest_has_catalog_digest_and_conforms_to_existing_batch_contract(self) -> None:
        catalog = load_json(CATALOG)
        manifest = self.plan()
        validate_record("batch", manifest)
        self.assertEqual(manifest["catalog_digest"], canonical_json_digest(catalog))
        self.assertIn("repeat=1", manifest["purpose"])
        self.assertIn("rotation-seed=0", manifest["purpose"])
        self.assertIn("no routing recommendation or default winner", manifest["purpose"])
        self.assertEqual(manifest["safety"]["artifact_retention"], "task-artifacts")
        with tempfile.TemporaryDirectory(prefix="duration-plan-contract-") as raw:
            path = Path(raw) / "batch.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(load_and_validate_batch(path), manifest)

    def test_same_inputs_are_byte_for_byte_reproducible(self) -> None:
        first = self.plan()
        second = self.plan()
        self.assertEqual(first, second)
        self.assertEqual(
            json.dumps(first, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            json.dumps(second, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )

    def test_rotation_seed_rotates_deterministic_s_m_l_interleave(self) -> None:
        self.assertEqual(self.size_sequence(self.plan(rotation_seed=0))[:3], ["S", "M", "L"])
        self.assertEqual(self.size_sequence(self.plan(rotation_seed=1))[:3], ["M", "L", "S"])
        self.assertEqual(self.size_sequence(self.plan(rotation_seed=2))[:3], ["L", "S", "M"])
        self.assertNotEqual(
            [entry["run_id"] for entry in self.plan(rotation_seed=0)["entries"]],
            [entry["run_id"] for entry in self.plan(rotation_seed=1)["entries"]],
        )

    def test_explicit_zipped_matrix_and_repeat_emit_only_requested_series(self) -> None:
        requested = [
            Series("codex", "gpt-5.6-sol", "max"),
            Series("claude", "claude-opus-5", "xhigh"),
        ]
        manifest = self.plan(series=requested, repeat=2, max_runs=12)
        actual = Counter(
            (entry["provider"], entry["model"], entry["effort"])
            for entry in manifest["entries"]
        )
        self.assertEqual(
            actual,
            Counter(
                {
                    ("codex", "gpt-5.6-sol", "max"): 6,
                    ("claude", "claude-opus-5", "xhigh"): 6,
                }
            ),
        )
        self.assertEqual([entry["order"] for entry in manifest["entries"]], list(range(1, 13)))
        run_ids = [entry["run_id"] for entry in manifest["entries"]]
        self.assertEqual(len(run_ids), len(set(run_ids)))
        self.assertEqual(manifest["safety"]["max_runs"], 12)
        self.assertIn("repeat=2", manifest["purpose"])

    def test_misspelled_and_empty_intersection_filters_fail_closed(self) -> None:
        with self.assertRaisesRegex(DurationStudyError, "unknown case filter"):
            self.plan(families=[], case_ids=["F04-S-PY-OO1"])
        with self.assertRaisesRegex(DurationStudyError, "unknown family filter"):
            self.plan(families=["bounded-implemantation"])
        with self.assertRaisesRegex(DurationStudyError, "unknown size filter"):
            self.plan(families=[], sizes=["XL"])
        with self.assertRaisesRegex(DurationStudyError, "empty intersection"):
            self.plan(
                families=[],
                case_ids=["F04-S-PY-001"],
                sizes=["M"],
            )
        with self.assertRaisesRegex(DurationStudyError, "explicit case, family, or size filter"):
            self.plan(families=[])

    def test_run_caps_and_deadline_are_preflighted_before_manifest_output(self) -> None:
        two_series = [
            Series("codex", "gpt-5.6-sol", "xhigh"),
            Series("grok", "grok-code-fast-1", "max"),
        ]
        exact_cap = self.plan(series=two_series, repeat=6, max_runs=HARD_MAX_RUNS)
        self.assertEqual(len(exact_cap["entries"]), HARD_MAX_RUNS)
        with self.assertRaisesRegex(DurationStudyError, "hard C0 planner cap"):
            self.plan(series=two_series, repeat=7, max_runs=HARD_MAX_RUNS)
        with self.assertRaisesRegex(DurationStudyError, "explicit max_runs"):
            self.plan(series=two_series, max_runs=5)
        with self.assertRaisesRegex(DurationStudyError, "between 1 and 36"):
            self.plan(max_runs=HARD_MAX_RUNS + 1)
        with self.assertRaisesRegex(DurationStudyError, "cannot fit one declared"):
            self.plan(deadline_seconds=149)
        with self.assertRaisesRegex(DurationStudyError, "deadline_seconds"):
            self.plan(deadline_seconds=float("nan"))
        with self.assertRaisesRegex(DurationStudyError, "unsigned 63-bit"):
            self.plan(rotation_seed=2**63)
        with self.assertRaisesRegex(DurationStudyError, "positive integer"):
            self.plan(repeat=0)

    def test_provider_effort_allowlist_and_duplicate_series_are_enforced(self) -> None:
        with self.assertRaisesRegex(DurationStudyError, "unsupported by provider surface"):
            self.plan(series=[Series("grok", "grok-code-fast-1", "ultra")])
        allowed = self.plan(series=[Series("codex", "gpt-5.6-sol", "ultra")])
        self.assertTrue(all(entry["effort"] == "ultra" for entry in allowed["entries"]))
        duplicate = Series("codex", "gpt-5.6-sol", "max")
        with self.assertRaisesRegex(DurationStudyError, "duplicate explicit series"):
            self.plan(series=[duplicate, duplicate])

    def test_cli_requires_explicit_model_and_effort_and_writes_without_provider_execution(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-plan-cli-") as raw:
            output = Path(raw) / "batch.json"
            command = self.cli_base(output)
            for required_flag in ("--model", "--effort"):
                missing_required = command.copy()
                index = missing_required.index(required_flag)
                del missing_required[index : index + 2]
                rejected = subprocess.run(
                    missing_required,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(rejected.returncode, 2)
                self.assertIn(required_flag, rejected.stderr)
                self.assertFalse(output.exists())

            completed = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout)
            self.assertEqual(summary["provider_calls"], 0)
            self.assertEqual(summary["entries"], 3)
            self.assertTrue(output.is_file())
            manifest = load_and_validate_batch(output)
            self.assertEqual(
                {(entry["provider"], entry["model"], entry["effort"]) for entry in manifest["entries"]},
                {("codex", "gpt-5.6-sol", "xhigh")},
            )

    def test_cli_rejects_unaligned_explicit_series_rows(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-plan-cli-rows-") as raw:
            output = Path(raw) / "batch.json"
            command = self.cli_base(output)
            command.extend(("--model", "unpaired-model"))
            completed = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 2)
            self.assertIn("zipped series rows", completed.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()

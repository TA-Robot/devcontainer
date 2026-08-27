#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from agent_contracts import load_json  # noqa: E402
from agent_duration_batch import execute_batch, load_and_validate_batch  # noqa: E402
from agent_duration_study import (  # noqa: E402
    DurationStudyError,
    canonical_json_digest,
)


CATALOG = ROOT / "experiments" / "multi-agent-duration" / "catalog" / "cases.json"


class AgentDurationBatchTests(unittest.TestCase):
    def batch(self, entries: list[dict[str, object]]) -> dict[str, object]:
        return {
            "schema_version": 1,
            "batch_id": "fixture-batch",
            "study_id": "fixture-study",
            "catalog_digest": canonical_json_digest(load_json(CATALOG)),
            "created_at": "2026-08-27T00:00:00.000Z",
            "purpose": "exercise finite batch controls",
            "safety": {
                "max_runs": len(entries),
                "deadline_seconds": 60,
                "concurrency": 1,
                "automatic_retry": False,
                "continue_after_quality_fail": True,
            },
            "entries": entries,
        }

    def entry(self, order: int, *, effort: str = "medium") -> dict[str, object]:
        return {
            "order": order,
            "run_id": f"fixture-run-{order}",
            "block_id": "fixture-block",
            "case_id": "F04-S-PY-001",
            "provider": "codex",
            "model": "gpt-fixture",
            "effort": effort,
            "timeout_seconds": 30,
            "evaluator_timeout_seconds": 10,
            "output_bytes_cap": 4096,
        }

    def write_batch(self, directory: Path, value: dict[str, object]) -> Path:
        path = directory / "batch.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_validates_and_dry_runs_without_provider_calls(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-batch-") as raw:
            root = Path(raw)
            batch = load_and_validate_batch(
                self.write_batch(root, self.batch([self.entry(1), self.entry(2)]))
            )
            result = execute_batch(
                batch,
                output_dir=root / "runs",
                image="fixture-image",
                auth_files={},
                live_generation_authorized=False,
                execute=False,
            )
            self.assertEqual(result["stop_reason"], "dry-run")
            self.assertEqual([item["status"] for item in result["observations"]], ["planned", "planned"])

    def test_rejects_stale_digest_noncontiguous_order_and_provider_effort(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-batch-bad-") as raw:
            root = Path(raw)
            stale = self.batch([self.entry(1)])
            stale["catalog_digest"] = f"sha256:{'0' * 64}"
            with self.assertRaisesRegex(DurationStudyError, "catalog digest is stale"):
                load_and_validate_batch(self.write_batch(root, stale))
            wrong_order = self.batch([self.entry(2)])
            with self.assertRaisesRegex(DurationStudyError, "order must be contiguous"):
                load_and_validate_batch(self.write_batch(root, wrong_order))
            bad_effort = self.batch([self.entry(1)])
            bad_effort["entries"][0]["provider"] = "grok"
            bad_effort["entries"][0]["effort"] = "ultra"
            with self.assertRaisesRegex(DurationStudyError, "unsupported by provider"):
                load_and_validate_batch(self.write_batch(root, bad_effort))

    def test_execution_continues_after_quality_fail_without_retry(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-batch-execute-") as raw:
            root = Path(raw)
            batch = self.batch([self.entry(1), self.entry(2)])
            calls: list[str] = []

            def fake_run_once(provider, case_id, output_dir, **kwargs):
                calls.append(kwargs["run_id"])
                quality = len(calls) > 1
                return (
                    {
                        "outcome": {
                            "infrastructure": "success",
                            "quality_pass": quality,
                        }
                    },
                    output_dir.resolve() / f"{kwargs['run_id']}.json",
                )

            result = execute_batch(
                batch,
                output_dir=root / "runs",
                image="fixture-image",
                auth_files={"codex": root / "auth.json"},
                live_generation_authorized=True,
                execute=True,
                run_once=fake_run_once,
                monotonic=lambda: 0,
            )
            self.assertEqual(calls, ["fixture-run-1", "fixture-run-2"])
            self.assertEqual(result["stop_reason"], "completed")
            self.assertEqual([item["quality_pass"] for item in result["observations"]], [False, True])

    def test_execution_requires_explicit_live_authorization(self) -> None:
        with self.assertRaisesRegex(DurationStudyError, "explicit generation authorization"):
            execute_batch(
                self.batch([self.entry(1)]),
                output_dir=Path("runs"),
                image="fixture-image",
                auth_files={},
                live_generation_authorized=False,
                execute=True,
            )


if __name__ == "__main__":
    unittest.main()

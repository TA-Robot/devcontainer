#!/usr/bin/env python3

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
CATALOG = (
    ROOT
    / "experiments"
    / "multi-agent-duration"
    / "catalog"
    / "families"
    / "f03.json"
)
sys.path.insert(0, str(SCRIPT_DIR))

from agent_contracts import load_json  # noqa: E402
from agent_duration_case_testing import assert_family_calibrated  # noqa: E402
from agent_duration_fixtures import (  # noqa: E402
    _install_known_good_for_test,
    build_fixture,
    evaluate_fixture,
)


class FailingTestDiagnosisFamilyTests(unittest.TestCase):
    def test_family_is_calibrated(self) -> None:
        assert_family_calibrated(self, CATALOG)

    def test_fixture_snapshots_are_reproducible(self) -> None:
        catalog = load_json(CATALOG)
        self.assertIsInstance(catalog, dict)
        fixed_time = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory(prefix="duration-f03-repeat-") as raw:
            root = Path(raw)
            for entry in catalog["entries"]:
                case_id = entry["case"]["case_id"]
                first = build_fixture(
                    case_id,
                    root / f"first-{case_id.lower()}",
                    catalog_path=CATALOG,
                    fixture_id=f"first-{case_id.lower()}",
                    now=fixed_time,
                )
                second = build_fixture(
                    case_id,
                    root / f"second-{case_id.lower()}",
                    catalog_path=CATALOG,
                    fixture_id=f"second-{case_id.lower()}",
                    now=fixed_time,
                )
                with self.subTest(case_id=case_id):
                    self.assertEqual(first["case"], second["case"])
                    self.assertEqual(first["snapshot"], second["snapshot"])
                    self.assertEqual(first["workspace_files"], second["workspace_files"])

    def test_diagnosis_artifact_cannot_hide_fixture_modification(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-f03-integrity-") as raw:
            fixture_dir = Path(raw) / "fixture"
            build_fixture(
                "F03-S-PY-001",
                fixture_dir,
                catalog_path=CATALOG,
                fixture_id="f03-integrity",
                now=datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc),
            )
            workspace = fixture_dir / "workspace"
            _install_known_good_for_test("F03-S-PY-001", workspace)
            with (workspace / "limits.py").open("a", encoding="utf-8") as handle:
                handle.write("\n# unauthorized diagnosis-time edit\n")
            result = evaluate_fixture(fixture_dir)
            self.assertEqual(result["status"], "fail")
            self.assertIn("diagnosis-root-cause", result["score"]["failed_check_ids"])


if __name__ == "__main__":
    unittest.main()

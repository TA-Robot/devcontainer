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
    / "f09.json"
)
sys.path.insert(0, str(SCRIPT_DIR))

from agent_contracts import load_json  # noqa: E402
from agent_duration_case_testing import assert_family_calibrated  # noqa: E402
from agent_duration_fixtures import (  # noqa: E402
    _install_known_good_for_test,
    build_fixture,
    evaluate_fixture,
)


class SecurityIsolationFamilyTests(unittest.TestCase):
    def test_family_is_calibrated(self) -> None:
        assert_family_calibrated(self, CATALOG)

    def test_fixture_snapshots_are_reproducible(self) -> None:
        catalog = load_json(CATALOG)
        self.assertIsInstance(catalog, dict)
        fixed_time = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory(prefix="duration-f09-repeat-") as raw:
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

    def test_source_test_and_validator_tampering_is_rejected(self) -> None:
        protected_paths = {
            "F09-S-PY-001": "names.py",
            "F09-M-PYBASH-001": "tools/check_security_regression.py",
            "F09-L-PYBASHDOCKER-001": "scenarios/attack_simulator.py",
        }
        fixed_time = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory(prefix="duration-f09-integrity-") as raw:
            root = Path(raw)
            for case_id, raw_path in protected_paths.items():
                fixture = root / case_id.lower()
                build_fixture(
                    case_id,
                    fixture,
                    catalog_path=CATALOG,
                    fixture_id=f"integrity-{case_id.lower()}",
                    now=fixed_time,
                )
                workspace = fixture / "workspace"
                _install_known_good_for_test(case_id, workspace)
                path = workspace / raw_path
                path.write_text(
                    path.read_text(encoding="utf-8") + "\n# unauthorized calibration edit\n",
                    encoding="utf-8",
                )
                result = evaluate_fixture(fixture)
                with self.subTest(case_id=case_id, path=raw_path):
                    self.assertEqual(result["status"], "fail")
                    self.assertEqual(result["score"]["hidden_passed"], 0)


if __name__ == "__main__":
    unittest.main()

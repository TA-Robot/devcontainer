#!/usr/bin/env python3

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from agent_contracts import load_json  # noqa: E402
from agent_duration_case_testing import (  # noqa: E402
    FIXED_CALIBRATION_TIME,
    assert_family_calibrated,
)
from agent_duration_fixtures import (  # noqa: E402
    _install_known_good_for_test,
    build_fixture,
    evaluate_fixture,
)


CATALOG = ROOT / "experiments" / "multi-agent-duration" / "catalog" / "families" / "f11.json"


class DevcontainerOperationsFamilyTests(unittest.TestCase):
    def test_family_is_calibrated(self) -> None:
        assert_family_calibrated(self, CATALOG)

    def test_fixture_snapshots_are_reproducible_at_fixed_time(self) -> None:
        catalog = load_json(CATALOG)
        with tempfile.TemporaryDirectory(prefix="duration-f11-repro-") as raw:
            root = Path(raw)
            for entry in catalog["entries"]:
                case_id = entry["case"]["case_id"]
                first = build_fixture(
                    case_id,
                    root / f"first-{case_id.lower()}",
                    catalog_path=CATALOG,
                    fixture_id=f"repro-{case_id.lower()}",
                    now=FIXED_CALIBRATION_TIME,
                )
                second = build_fixture(
                    case_id,
                    root / f"second-{case_id.lower()}",
                    catalog_path=CATALOG,
                    fixture_id=f"repro-{case_id.lower()}",
                    now=FIXED_CALIBRATION_TIME,
                )
                self.assertEqual(first["workspace_files"], second["workspace_files"])
                self.assertEqual(first["snapshot"], second["snapshot"])

    def test_lifecycle_patch_cannot_modify_installer(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-f11-integrity-") as raw:
            fixture_dir = Path(raw) / "fixture"
            build_fixture(
                "F11-M-BASH-001",
                fixture_dir,
                catalog_path=CATALOG,
                fixture_id="f11-integrity",
                now=FIXED_CALIBRATION_TIME,
            )
            workspace = fixture_dir / "workspace"
            _install_known_good_for_test("F11-M-BASH-001", workspace)
            with (workspace / "install-cli").open("a", encoding="utf-8") as handle:
                handle.write("\n# unauthorized installer change\n")
            result = evaluate_fixture(fixture_dir)
            self.assertEqual(result["status"], "fail")
            self.assertIn("ops-ready-after-verify", result["score"]["failed_check_ids"])


if __name__ == "__main__":
    unittest.main()

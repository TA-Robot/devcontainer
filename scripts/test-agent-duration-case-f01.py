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
from agent_duration_fixtures import build_fixture  # noqa: E402


CATALOG = ROOT / "experiments" / "multi-agent-duration" / "catalog" / "families" / "f01.json"


class RepositoryTraceFamilyTests(unittest.TestCase):
    def test_family_is_calibrated(self) -> None:
        assert_family_calibrated(self, CATALOG)

    def test_fixture_snapshots_are_reproducible_at_fixed_time(self) -> None:
        catalog = load_json(CATALOG)
        with tempfile.TemporaryDirectory(prefix="duration-f01-repro-") as raw:
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


if __name__ == "__main__":
    unittest.main()

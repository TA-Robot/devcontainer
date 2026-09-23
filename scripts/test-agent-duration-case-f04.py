#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import sys
import unittest


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from agent_duration_case_testing import assert_family_calibrated  # noqa: E402


class F04DurationCaseTests(unittest.TestCase):
    def test_family_is_calibrated(self) -> None:
        assert_family_calibrated(
            self,
            ROOT
            / "experiments"
            / "multi-agent-duration"
            / "catalog"
            / "families"
            / "f04.json",
        )


if __name__ == "__main__":
    unittest.main()

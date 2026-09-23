from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).with_name("evaluate-robot-soccer-controller")
LOADER = importlib.machinery.SourceFileLoader("robot_soccer_seed_gate", str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)


class SeedGateTest(unittest.TestCase):
    def test_requires_exactly_three_distinct_seeds(self) -> None:
        self.assertEqual((1, 2, 3), MODULE.parse_seeds("1,2,3"))
        for invalid in ("1,2", "1,1,2", "1,2,3,4", "-1,2,3"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(argparse.ArgumentTypeError):
                    MODULE.parse_seeds(invalid)

    def test_gate_requires_every_seed_to_succeed(self) -> None:
        passing = [{"simulator_status": "success"} for _ in range(3)]
        self.assertTrue(MODULE.gate_passes(passing))
        passing[1]["simulator_status"] = "failure"
        self.assertFalse(MODULE.gate_passes(passing))
        self.assertFalse(MODULE.gate_passes(passing[:2]))

    def test_controller_placeholders_are_expanded_without_duplicate_flags(self) -> None:
        command = MODULE.controller_command(
            ["controller", "--server", "{base_url}", "--case", "{seed}"],
            "http://127.0.0.1:18080",
            7,
        )
        self.assertEqual(
            [
                "controller",
                "--server",
                "http://127.0.0.1:18080",
                "--case",
                "7",
            ],
            command,
        )


if __name__ == "__main__":
    unittest.main()

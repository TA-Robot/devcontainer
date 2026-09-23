from __future__ import annotations

import importlib.machinery
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("analyze-robot-soccer-traces")
LOADER = importlib.machinery.SourceFileLoader("robot_soccer_trace_analysis", str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)


class TraceAnalysisTest(unittest.TestCase):
    def test_extracts_terminal_motion_impulse_and_nearest_robots(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            trace = Path(raw) / "seed-17.jsonl"
            events = [
                {"at_unix_ms": 1000, "event": "episode_started", "payload": {}},
                {
                    "at_unix_ms": 1200,
                    "event": "observation_delivered",
                    "payload": {
                        "sequence": 2,
                        "ball": {"position": {"x": 0, "y": 0}, "velocity": {"x": 0, "y": 0}},
                        "robots": [
                            {"id": "friendly_0", "team": "friendly", "position": {"x": 0.2, "y": 0}},
                            {"id": "enemy_0", "team": "enemy", "position": {"x": 0.5, "y": 0}},
                        ],
                    },
                },
                {"at_unix_ms": 1250, "event": "command_received", "payload": [{"id": "friendly_0", "kick": True}]},
                {
                    "at_unix_ms": 1300,
                    "event": "observation_delivered",
                    "payload": {
                        "sequence": 5,
                        "ball": {"position": {"x": 0.3, "y": 0}, "velocity": {"x": 3, "y": 0}},
                        "robots": [
                            {"id": "friendly_0", "team": "friendly", "position": {"x": 0.2, "y": 0}},
                            {"id": "enemy_0", "team": "enemy", "position": {"x": 0.7, "y": 0}},
                        ],
                    },
                },
                {"at_unix_ms": 1500, "event": "episode_terminal", "payload": {"status": "success", "reason": "pass_and_goal", "elapsed_ms": 500}},
            ]
            trace.write_text(
                "\n".join(json.dumps(event) for event in events) + "\n",
                encoding="utf-8",
            )
            report = MODULE.analyze_trace(trace)
            self.assertEqual(17, report["seed"])
            self.assertEqual("success", report["terminal"]["status"])
            self.assertEqual({"friendly_0": 1}, report["kick_true_commands"])
            self.assertEqual(5, report["first_ball_motion"]["sequence"])
            impulse = report["largest_velocity_changes"][0]
            self.assertEqual(3.0, impulse["velocity_delta"])
            self.assertEqual("friendly_0", impulse["nearest_friendly"]["id"])

    def test_directory_resolution_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "seed-2.jsonl").write_text("", encoding="utf-8")
            (root / "seed-1.jsonl").write_text("", encoding="utf-8")
            self.assertEqual(
                ["seed-1.jsonl", "seed-2.jsonl"],
                [path.name for path in MODULE.resolve_traces([root])],
            )

    def test_summary_remaps_missing_container_absolute_trace(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            local_trace = root / "seed-9.jsonl"
            local_trace.write_text("", encoding="utf-8")
            summary = root / "summary.json"
            summary.write_text(
                json.dumps(
                    {
                        "runs": [
                            {"trace": "/workspace/foreign/revision/seed-9.jsonl"}
                        ]
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual([local_trace], MODULE.resolve_traces([summary]))


if __name__ == "__main__":
    unittest.main()

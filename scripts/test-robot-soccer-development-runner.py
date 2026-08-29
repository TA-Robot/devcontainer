from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("develop-robot-soccer-controller")
LOADER = importlib.machinery.SourceFileLoader("robot_soccer_development_runner", str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
assert SPEC is not None
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)


class DevelopmentRunnerTest(unittest.TestCase):
    def test_seed_list_is_distinct_and_bounded(self) -> None:
        self.assertEqual((1, 2, 8), MODULE.parse_seeds("1,2,8"))
        for invalid in ("", "1,1", "-1", ",".join(str(i) for i in range(65))):
            with self.subTest(invalid=invalid):
                with self.assertRaises(argparse.ArgumentTypeError):
                    MODULE.parse_seeds(invalid)

    def test_controller_command_uses_snapshot_and_placeholders(self) -> None:
        snapshot = Path("/tmp/revision/controller.py")
        command = MODULE.controller_command(
            ["python3", "{controller}", "--server={base_url}", "--case={seed}"],
            snapshot,
            "http://127.0.0.1:19000",
            7,
        )
        self.assertEqual(
            [
                "python3",
                str(snapshot),
                "--server=http://127.0.0.1:19000",
                "--case=7",
            ],
            command,
        )

    def test_snapshot_is_immutable_copy_with_digest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "controller.py"
            revision = root / "revision"
            revision.mkdir()
            source.write_text("print('one')\n", encoding="utf-8")
            snapshot, digest = MODULE.snapshot_controller(source, revision)
            source.write_text("print('two')\n", encoding="utf-8")
            self.assertEqual("print('one')\n", snapshot.read_text(encoding="utf-8"))
            self.assertEqual(12, len(digest))

    def test_revision_number_continues_across_runner_restarts(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "r0002-old").mkdir()
            (root / "r0007-new").mkdir()
            (root / "notes").mkdir()
            self.assertEqual(8, MODULE.next_revision_number(root))

    def test_cpu_order_uses_each_physical_core_before_smt_siblings(self) -> None:
        self.assertEqual(
            [0, 2, 4, 1, 3, 5],
            MODULE.order_cpus_by_core(
                [(0, 0), (1, 0), (2, 1), (3, 1), (4, 2), (5, 2)]
            ),
        )

    def test_trace_suffix_extracts_only_the_current_episode(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "worker.jsonl"
            destination = root / "episode.jsonl"
            source.write_bytes(b"old\n")
            offset = source.stat().st_size
            with source.open("ab") as handle:
                handle.write(b"new-1\nnew-2\n")
            MODULE.copy_trace_suffix(source, offset, destination)
            self.assertEqual(b"new-1\nnew-2\n", destination.read_bytes())

    def test_trace_timing_excludes_controller_process_startup(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            trace = Path(raw) / "episode.jsonl"
            trace.write_text(
                "\n".join(
                    (
                        '{"at_unix_ms":1000,"event":"episode_started","payload":{}}',
                        '{"at_unix_ms":4250,"event":"episode_terminal",'
                        '"payload":{"elapsed_ms":3200}}',
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            wall_s, ratio = MODULE.trace_episode_timing(trace)
            self.assertEqual(3.25, wall_s)
            self.assertAlmostEqual(1.015625, ratio)

    def test_summary_orders_seeds_and_requires_all_success(self) -> None:
        runs = [
            {"seed": 2, "simulator_status": "failure", "realtime_ratio": 1.2},
            {"seed": 1, "simulator_status": "success", "realtime_ratio": 1.0},
        ]
        summary = MODULE.summarize_runs("r1", "abc", Path("controller.py"), runs)
        self.assertFalse(summary["accepted"])
        self.assertEqual(1, summary["successes"])
        self.assertEqual([1, 2], [run["seed"] for run in summary["runs"]])
        self.assertEqual(1.1, summary["realtime_ratio_average"])
        self.assertEqual(1.2, summary["realtime_ratio_max"])


if __name__ == "__main__":
    unittest.main()

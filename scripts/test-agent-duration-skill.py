#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
WRAPPER = ROOT / "project/.codex/skills/lookup-agent-duration/scripts/query_atlas.py"


def load_wrapper():
    spec = importlib.util.spec_from_file_location("duration_skill_query", WRAPPER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load duration skill query wrapper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DurationSkillDiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_wrapper()

    def test_explicit_atlas_precedes_environment(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            explicit = directory / "explicit.json"
            configured = directory / "configured.json"
            explicit.write_text("{}\n", encoding="utf-8")
            configured.write_text("{}\n", encoding="utf-8")
            with mock.patch.dict(
                os.environ,
                {"AGENT_DURATION_ATLAS_PATH": str(configured)},
                clear=False,
            ):
                self.assertEqual(explicit.resolve(), self.module.discover_atlas(explicit))

    def test_invalid_environment_override_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            missing = Path(raw) / "missing.json"
            with mock.patch.dict(
                os.environ,
                {"AGENT_DURATION_ATLAS_PATH": str(missing)},
                clear=False,
            ):
                with self.assertRaisesRegex(ValueError, "does not name a file"):
                    self.module.discover_atlas(None)

    def test_nearest_project_aggregate_precedes_skill_and_system_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            nested = root / "a/b"
            aggregate = root / "generated/duration-atlas/current.json"
            nested.mkdir(parents=True)
            aggregate.parent.mkdir(parents=True)
            aggregate.write_text("{}\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
                Path, "cwd", return_value=nested
            ):
                self.assertEqual(aggregate.resolve(), self.module.discover_atlas(None))

    def test_skill_asset_precedes_system_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            script = root / "skill/scripts/query_atlas.py"
            asset = root / "skill/assets/current.json"
            system = root / "system/current.json"
            script.parent.mkdir(parents=True)
            asset.parent.mkdir(parents=True)
            system.parent.mkdir(parents=True)
            script.write_text("# fixture\n", encoding="utf-8")
            asset.write_text("{}\n", encoding="utf-8")
            system.write_text("{}\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
                self.module, "__file__", str(script)
            ), mock.patch.object(self.module, "SYSTEM_ATLAS", system), mock.patch.object(
                Path, "cwd", return_value=root / "unrelated"
            ):
                self.assertEqual(asset.resolve(), self.module.discover_atlas(None))


class DurationSkillCliTests(unittest.TestCase):
    def test_help_explains_that_atlas_positional_is_injected(self) -> None:
        environment = {
            **os.environ,
            "AGENT_DURATION_QUERY_COMMAND": str(ROOT / "scripts/query-agent-duration-atlas"),
        }
        completed = subprocess.run(
            [sys.executable, str(WRAPPER), "--help"],
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Discovers and injects the atlas positional argument", completed.stdout)
        self.assertIn("AGENT_DURATION_ATLAS_PATH", completed.stdout)
        self.assertIn("nearest generated/duration-atlas/current.json", completed.stdout)
        self.assertIn("exits without querying", completed.stdout)
        self.assertIn("--setting-requested-value", completed.stdout)

    def test_wrapper_forwards_selected_atlas_and_query_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            atlas = directory / "atlas.json"
            capture = directory / "capture.json"
            command = directory / "query-fixture"
            atlas.write_text("{}\n", encoding="utf-8")
            command.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, sys\n"
                "with open(os.environ['CAPTURE_PATH'], 'w', encoding='utf-8') as handle:\n"
                "    json.dump(sys.argv[1:], handle)\n",
                encoding="utf-8",
            )
            command.chmod(0o755)
            environment = {
                **os.environ,
                "AGENT_DURATION_QUERY_COMMAND": str(command),
                "CAPTURE_PATH": str(capture),
            }
            completed = subprocess.run(
                [
                    sys.executable,
                    str(WRAPPER),
                    "--atlas",
                    str(atlas),
                    "--mode",
                    "coverage",
                    "--max-rows",
                    "3",
                    "--max-output-bytes",
                    "4096",
                ],
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                [
                    str(atlas.resolve()),
                    "--mode",
                    "coverage",
                    "--max-rows",
                    "3",
                    "--max-output-bytes",
                    "4096",
                ],
                json.loads(capture.read_text(encoding="utf-8")),
            )

    def test_print_atlas_path_does_not_require_query_command(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            atlas = Path(raw) / "atlas.json"
            atlas.write_text("{}\n", encoding="utf-8")
            environment = {
                **os.environ,
                "AGENT_DURATION_QUERY_COMMAND": str(Path(raw) / "missing"),
            }
            completed = subprocess.run(
                [
                    sys.executable,
                    str(WRAPPER),
                    "--atlas",
                    str(atlas),
                    "--print-atlas-path",
                ],
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(str(atlas.resolve()), completed.stdout.strip())


if __name__ == "__main__":
    unittest.main()

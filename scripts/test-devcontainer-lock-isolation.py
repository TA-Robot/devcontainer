#!/usr/bin/env python3
"""Concurrent frozen build calls must not share the CLI's generated files."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FrozenBuildIsolationTests(unittest.TestCase):
    def test_parallel_cli_calls_own_scratch_and_preserve_failure_status(self):
        with tempfile.TemporaryDirectory(prefix="frozen-build-isolation-") as temporary:
            root = Path(temporary)
            binaries = root / "bin"
            binaries.mkdir()
            shared = root / "shared-tmp"
            shared.mkdir()
            docker = binaries / "docker"
            docker.write_text('#!/bin/sh\n[ "$1" = info ]\n')
            docker.chmod(0o755)
            cli = binaries / "devcontainer-probe"
            cli.write_text(
                '#!/usr/bin/env python3\nimport json,os,time\nfrom pathlib import Path\n'
                'scratch=Path(os.environ["TMPDIR"])\n'
                'Path(os.environ["PROBE_RECORD"]).write_text(json.dumps('
                '{"scratch":str(scratch),"exists":scratch.is_dir()}))\n'
                'time.sleep(.05)\nraise SystemExit(19)\n')
            cli.chmod(0o755)
            processes = []
            for number in range(2):
                environment = dict(os.environ, PATH=str(binaries) + os.pathsep + os.environ["PATH"],
                                   TMPDIR=str(shared), DEVCONTAINER_CLI_BIN=str(cli),
                                   PROBE_RECORD=str(root / f"record-{number}.json"),
                                   DEVCONTAINER_FROZEN_IMAGE=f"probe-{number}")
                processes.append(subprocess.Popen(
                    ["bash", str(ROOT / "scripts/test-devcontainer-lock.sh"), "--build"],
                    env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
            try:
                for process in processes:
                    stdout, stderr = process.communicate(timeout=30)
                    self.assertEqual(process.returncode, 19, stdout + stderr)
            finally:
                for process in processes:
                    if process.poll() is None:
                        process.kill()
                    process.communicate(timeout=5)
            records = [json.loads((root / f"record-{number}.json").read_text()) for number in range(2)]
            self.assertTrue(all(record["exists"] for record in records))
            self.assertNotEqual(records[0]["scratch"], records[1]["scratch"])
            for record in records:
                scratch = Path(record["scratch"])
                self.assertEqual(scratch.parent, shared)
                self.assertFalse(scratch.exists())
            self.assertTrue(shared.is_dir())


if __name__ == "__main__":
    unittest.main()

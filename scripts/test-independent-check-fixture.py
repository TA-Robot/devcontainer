"""Calibrate real-job fixtures without invoking a model or a future checker."""
import importlib.util
from pathlib import Path
import shlex
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "independent_check_fixture",
    ROOT / "experiments/development-harness/cycle-003/large-02/fixture.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class IndependentCheckFixtureTests(unittest.TestCase):
    def setUp(self):
        self.fixture = MODULE.Fixture(ROOT, ROOT / "project")
        self.addCleanup(self.fixture.close)

    def test_reported_success_is_distinct_from_actual_execution(self):
        fixture = self.fixture
        witness = fixture.root / "executed"
        extra = fixture.root / "result-only-command"
        command = f"printf checked > {shlex.quote(str(witness))}; exit 17"
        fixture.create([command], extra_reported=[f"touch {shlex.quote(str(extra))}"])
        result = fixture.invoke("job", "validate", fixture.job["job_id"], "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(witness.exists(), "legacy validation unexpectedly ran acceptance")
        self.assertFalse(extra.exists(), "provider-result commands must not execute")
        self.assertEqual(fixture.counter.read_text(), "1")

        # The external observation is executable evidence, not another claim.
        actual = subprocess.run(
            ["/bin/sh", "-c", command],
            cwd=fixture.attempt["workspace_path"],
            capture_output=True, timeout=5,
        )
        self.assertEqual(actual.returncode, 17)
        self.assertEqual(witness.read_text(), "checked")
        self.assertFalse(extra.exists())
        self.assertEqual(fixture.counter.read_text(), "1")

    def test_manual_only_task_has_no_command_evidence(self):
        fixture = self.fixture
        fixture.create([])
        result = fixture.invoke("job", "validate", fixture.job["job_id"], "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(fixture.counter.read_text(), "1")
        self.assertEqual(fixture.environment["CHECK_FIXTURE_REPORTED_COMMANDS"], "[]")


if __name__ == "__main__":
    unittest.main()

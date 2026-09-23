"""Calibrate real-job fixtures without invoking a model or a future checker."""
import importlib.util
import json
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
PROBE_SPEC = importlib.util.spec_from_file_location(
    "independent_execution_probe", SPEC.origin.replace("fixture.py", "evaluate_execution.py"),
)
PROBE = importlib.util.module_from_spec(PROBE_SPEC)
PROBE_SPEC.loader.exec_module(PROBE)


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


def executable_reference(fixture, commands):
    """Small disposable execution oracle, not a production checker implementation."""
    checks = []
    failed = False
    for command in commands:
        if failed:
            checks.append({"command": command, "status": "unexecuted", "exit_code": None})
            continue
        process = subprocess.run(
            ["/bin/sh", "-c", command], cwd=fixture.attempt["workspace_path"],
            capture_output=True, timeout=5,
        )
        failed = process.returncode != 0
        checks.append({"command": command, "status": "failed" if failed else "passed",
                       "exit_code": process.returncode})
    status = "no-checks" if not commands else "failed" if failed else "passed"
    return subprocess.CompletedProcess([], 0 if status == "passed" else 1, json.dumps({
        "schema_version": 1, "job_id": fixture.job["job_id"],
        "attempt_id": fixture.attempt["attempt_id"], "status": status, "checks": checks,
    }), "")


class ExecutionObservationCalibrationTests(unittest.TestCase):
    def fixture(self):
        value = MODULE.Fixture(ROOT, ROOT / "project")
        self.addCleanup(value.close)
        return value

    def test_real_execution_reference_satisfies_core_observations(self):
        for case in PROBE.CASES:
            with self.subTest(case=case):
                PROBE.observe_case(self.fixture(), case, executable_reference)

    def test_success_json_without_execution_is_rejected(self):
        def fabricated(fixture, commands):
            value = {"schema_version": 1, "job_id": fixture.job["job_id"],
                     "attempt_id": fixture.attempt["attempt_id"], "status": "passed",
                     "checks": [{"command": c, "exit_code": 0} for c in commands]}
            return subprocess.CompletedProcess([], 0, json.dumps(value), "")
        with self.assertRaisesRegex(AssertionError, "did not execute"):
            PROBE.observe_case(self.fixture(), "actual-success", fabricated)

    def test_actual_failure_cannot_be_overridden_by_success_report(self):
        def lying(fixture, commands):
            result = executable_reference(fixture, commands)
            value = json.loads(result.stdout)
            value["status"] = "passed"
            return subprocess.CompletedProcess([], 0, json.dumps(value), "")
        with self.assertRaisesRegex(AssertionError, "false success"):
            PROBE.observe_case(self.fixture(), "false-success-and-stop", lying)

    def test_result_only_side_effect_is_rejected_even_if_omitted_from_report(self):
        def wrong_authority(fixture, commands):
            result = executable_reference(fixture, commands)
            extra = json.loads(fixture.environment["CHECK_FIXTURE_REPORTED_COMMANDS"])[-1]
            subprocess.run(["/bin/sh", "-c", extra], check=True, timeout=5)
            return result
        with self.assertRaisesRegex(AssertionError, "only by the provider"):
            PROBE.observe_case(self.fixture(), "original-task-authority", wrong_authority)


if __name__ == "__main__":
    unittest.main()

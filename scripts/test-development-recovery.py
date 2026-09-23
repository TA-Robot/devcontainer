"""Calibrate declared recovery against real jobs, signals and a failed stop witness."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('recovery_observer', ROOT / 'experiments/development-harness/continuation/recovery.py')
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = recovery.StagedFixture(ROOT, ROOT / 'project')
        self.addCleanup(self.fixture.close)

    def test_documented_explicit_recovery_runs_after_confirmed_stop(self):
        result = recovery.observe(self.fixture, 'explicit')
        self.assertEqual(result['status'], 'passed', result)
        self.assertTrue(result['operator_confirmed_owned_process_group_stopped'])
        self.assertEqual(result['explicit_recovery_calls'], 1)
        self.assertEqual(result['provider_invocations'], 1)

    def test_automatic_procedure_accepts_executable_reference(self):
        spec = importlib.util.spec_from_file_location(
            'recovery_reference', ROOT / 'scripts/test-independent-check-staged.py')
        reference = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reference)
        fixture = reference.Reference()
        self.addCleanup(fixture.close)
        result = recovery.observe(fixture, 'automatic')
        self.assertEqual(result['status'], 'passed', result)
        self.assertEqual(result['explicit_recovery_calls'], 0)

    def test_automatic_recheck_does_not_masquerade_as_documented_explicit_procedure(self):
        result = recovery.observe(self.fixture, 'automatic')
        self.assertEqual(result['status'], 'failed', result)
        self.assertEqual(result['explicit_recovery_calls'], 0)

    def test_unverified_group_stop_never_triggers_recovery(self):
        with patch.object(recovery, 'group_running', return_value=True):
            result = recovery.observe(self.fixture, 'explicit')
        self.assertNotEqual(result['status'], 'passed', result)
        self.assertFalse(result['operator_confirmed_owned_process_group_stopped'])
        self.assertEqual(result['explicit_recovery_calls'], 0)

    def test_unreadable_group_is_unknown_and_cannot_authorize_recovery(self):
        with patch.object(recovery, 'group_running', side_effect=PermissionError('unreadable witness')):
            result = recovery.observe(self.fixture, 'explicit')
        self.assertEqual(result['status'], 'unknown', result)
        self.assertEqual(result['explicit_recovery_calls'], 0)


if __name__ == '__main__':
    unittest.main()

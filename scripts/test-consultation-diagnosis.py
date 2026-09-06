"""Calibrate a bounded causal-diagnosis task without live providers."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'experiments/development-harness/consultation/v1'
sys.path.insert(0, str(HERE))
import case
import calibrate
import observe


class ConsultationDiagnosisTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='test-consultation-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.workspace = self.root / 'workspace'
        case.create(self.workspace, 'effect-first')

    def good(self):
        plan, diagnosis = calibrate.reference(self.workspace, 'effect-first')
        calibrate.submit(self.workspace, plan, diagnosis)
        return plan, diagnosis

    def test_calibration_accepts_valid_answers_and_rejects_each_declared_defect(self):
        result = calibrate.calibrate()
        self.assertEqual(result['status'], 'pass', result)
        self.assertEqual(len(result['records']), 20)
        baselines = [r for r in result['records'] if r['calibration_id'] == 'public-tool-only-baseline']
        self.assertEqual(len(baselines), 2)
        self.assertTrue(all(r['evaluation']['status'] == 'pass' for r in baselines))

    def test_variant_changes_real_observation_and_rejects_copied_answer(self):
        plan, diagnosis = self.good()
        other = self.root / 'other'
        case.create(other, 'ack-first')
        other_plan, other_diagnosis = calibrate.reference(other, 'ack-first')
        self.assertEqual(diagnosis['outcome'], 'duplicate')
        self.assertEqual(other_diagnosis['outcome'], 'lost')
        self.assertEqual(diagnosis['before_restart'], {'offset': 0, 'effects': ['event-1']})
        self.assertEqual(diagnosis['after_restart'], {'offset': 1, 'effects': ['event-1', 'event-1']})
        self.assertEqual(other_diagnosis['before_restart'], {'offset': 1, 'effects': []})
        self.assertEqual(other_diagnosis['after_restart'], {'offset': 1, 'effects': []})
        self.assertNotEqual(plan, other_plan)
        calibrate.submit(other, plan, diagnosis)
        self.assertEqual(case.evaluate(other, 'ack-first')['status'], 'fail')

    def test_public_bundle_has_no_precomputed_answer_or_private_evaluator(self):
        inputs = case.files('effect-first')
        self.assertEqual(set(inputs), {'worker.py', 'journal.py', 'observe.py', 'TASK.md', 'AGENTS.md'})
        self.assertEqual(inputs['TASK.md'], case.files('ack-first')['TASK.md'])
        self.assertEqual(inputs['journal.py'], case.L_FILES['journal.py'])
        for source in inputs.values():
            self.assertNotIn('L_GOOD_DIAGNOSIS', source)
            self.assertNotIn('EXPECTED_RESULT', source)
            self.assertNotIn('effect-first', source)
            self.assertNotIn('ack-first', source)

    def test_public_observation_is_not_a_success_oracle(self):
        plan = {'stop_after': 'read-offset', 'restart_count': 1}
        (self.workspace / 'reproduction.json').write_text(json.dumps(plan))
        completed = subprocess.run([sys.executable, '-B', 'observe.py', 'reproduction.json'],
                                   cwd=self.workspace, text=True, capture_output=True, timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)['outcome'], 'once')

    def test_changed_public_tool_is_rejected_before_any_candidate_code_executes(self):
        self.good()
        marker = self.root / 'should-not-exist'
        (self.workspace / 'observe.py').write_text(f'open({str(marker)!r}, "w").write("executed")')
        with patch.object(observe, 'observe', side_effect=AssertionError('must not execute')):
            result = case.evaluate(self.workspace, 'effect-first')
        self.assertEqual(result['reason'], 'source-integrity')
        self.assertFalse(marker.exists())

    def test_unknown_observer_failure_is_not_a_candidate_quality_score(self):
        self.good()
        with patch.object(observe, 'observe', side_effect=TimeoutError):
            result = case.evaluate(self.workspace, 'effect-first')
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['reason'], 'observer-failure')

    def test_mid_evaluation_candidate_mutation_invalidates_source(self):
        self.good()
        real = observe.observe
        def changed(*args, **kwargs):
            value = real(*args, **kwargs)
            (self.workspace / 'diagnosis.json').write_text('{}')
            return value
        with patch.object(observe, 'observe', side_effect=changed):
            result = case.evaluate(self.workspace, 'effect-first')
        self.assertEqual(result['status'], 'fail')
        self.assertIn({'name': 'source-integrity', 'status': 'failed'}, result['checks'])

    def test_invalid_json_types_duplicate_keys_and_commands_fail_closed(self):
        plan, answer = self.good()
        for bad in ('{"stop_after":"read-offset","stop_after":"append-effect","restart_count":1}',
                    '{"stop_after":"append-effect","restart_count":true}',
                    '{"stop_after":"append-effect","restart_count":NaN}',
                    '{"stop_after":"append-effect","restart_count":1,"cleanup":"/tmp"}',
                    '[1,2]', '{'):
            with self.subTest(bad=bad):
                (self.workspace / 'reproduction.json').write_text(bad)
                self.assertEqual(case.evaluate(self.workspace, 'effect-first')['status'], 'fail')
        for key, value in (('event_order', None), ('before_restart', {'offset': False, 'effects': []}),
                           ('interruption', []), ('exactly_once_established', 0)):
            bad = copy.deepcopy(answer)
            bad[key] = value
            calibrate.submit(self.workspace, plan, bad)
            self.assertEqual(case.evaluate(self.workspace, 'effect-first')['status'], 'fail')

    def test_missing_oversized_symlink_fifo_and_extra_artifacts_are_rejected(self):
        self.assertEqual(case.evaluate(self.workspace, 'effect-first')['status'], 'fail')
        self.good()
        path = self.workspace / 'diagnosis.json'
        path.write_bytes(b' ' * 65537)
        self.assertEqual(case.evaluate(self.workspace, 'effect-first')['status'], 'fail')
        path.unlink()
        external = self.root / 'external'
        external.write_text('{}')
        path.symlink_to(external)
        self.assertEqual(case.evaluate(self.workspace, 'effect-first')['status'], 'fail')
        path.unlink()
        os.mkfifo(path)
        self.assertEqual(case.evaluate(self.workspace, 'effect-first')['status'], 'fail')
        path.unlink()
        self.good()
        (self.workspace / 'unexpected').mkdir()
        self.assertEqual(case.evaluate(self.workspace, 'effect-first')['status'], 'fail')

    def test_barrier_timeout_reaps_only_owned_child_and_preserves_other_files(self):
        sentinel = self.root / 'user-file'
        sentinel.write_text('preserve')
        (self.workspace / 'worker.py').write_text('import sys,time\nif "--stop-after" in sys.argv: time.sleep(60)\n')
        spawned = []
        real = subprocess.Popen
        def track(*args, **kwargs):
            child = real(*args, **kwargs)
            spawned.append(child)
            return child
        with patch.object(observe.subprocess, 'Popen', side_effect=track):
            with self.assertRaises(TimeoutError):
                observe.observe(self.workspace, {'stop_after': 'append-effect', 'restart_count': 1}, timeout=.1)
        self.assertTrue(spawned)
        self.assertTrue(all(child.poll() is not None for child in spawned))
        self.assertEqual(sentinel.read_text(), 'preserve')

    @unittest.skipUnless(os.environ.get('CONSULTATION_DIAGNOSIS_IMAGE'), 'set verified image ID')
    def test_readonly_docker_calibration_without_network_or_credentials(self):
        with tempfile.TemporaryDirectory(prefix='consultation-container-') as raw:
            completed = subprocess.run(['docker', 'run', '--rm', '--network', 'none', '--read-only',
                '--tmpfs', '/tmp:rw,exec,mode=1777', '-e', 'PYTHONDONTWRITEBYTECODE=1',
                '--mount', f'type=bind,src={ROOT},dst=/repo,readonly',
                '--mount', f'type=bind,src={raw},dst=/results', os.environ['CONSULTATION_DIAGNOSIS_IMAGE'],
                'python3', '/repo/experiments/development-harness/consultation/v1/calibrate.py',
                '--output', '/results/calibration.json'], capture_output=True, text=True, timeout=120)
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            result = json.loads((Path(raw) / 'calibration.json').read_text())
            self.assertEqual(result['status'], 'pass', result)


if __name__ == '__main__':
    unittest.main()

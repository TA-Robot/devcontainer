import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

HERE = Path(__file__).resolve().parents[1]/'experiments/development-harness/scheduling/deadline_capture_v1'
spec = importlib.util.spec_from_file_location('deadline_capture_tests', HERE/'capture.py')
capture = importlib.util.module_from_spec(spec); spec.loader.exec_module(capture)


class CaptureTests(unittest.TestCase):
    def test_frozen_evaluator_invalid_exit_and_unknown_results(self):
        grader = capture.load('capture_grader_status_test', HERE/'assessment.py')
        raw = {'status': 'withhold', 'all_containers_removed': True,
               'cases': [{'status': 'invalid-policy'}]}
        self.assertEqual(grader.quality_status(raw, 0), 'invalid-policy')
        self.assertEqual(grader.quality_status(raw, 1), 'withhold')
        self.assertEqual(grader.quality_status({**raw, 'all_containers_removed': False}, 0), 'withhold')
        self.assertEqual(grader.quality_status({**raw, 'cases': [{'status': 'unmeasured'}]}, 0), 'withhold')

    def test_deadline_is_distinct_from_normal_and_other_failures(self):
        report = {'condition': 'solo', 'quality': {'status': 'withhold'},
                  'cleanup': {'status': 'confirmed'}, 'source_unchanged': True,
                  'artifact': {'status': 'sealed', 'sha256': 'fixed'},
                  'budget': {'wall_clock': 'exceeded', 'output_tokens': 'unknown'},
                  'admission': 'withhold', 'elapsed_seconds': 9.2, 'usage': {'status': 'partial'},
                  'bridge': {'status': 'withhold', 'reason': 'TimeoutError: development deadline', 'development_seconds': 8.1},
                  'lifecycle': {'status': 'unknown', 'failures': [{'failure': 'unfinished participant'}],
                                'inventory': [{'model': 'gpt-6-astra', 'effort': 'high', 'cli_version': '0.153.0'}]}}
        original = copy.deepcopy(report)
        r = capture.classify(report, 8, 20)
        self.assertEqual(r['status'], 'evaluable'); self.assertFalse(r['normal_completion'])
        self.assertEqual(r['original_quality'], 'withhold'); self.assertEqual(report, original)
        for patch in ({'elapsed_seconds': 29}, {'elapsed_seconds': float('nan')},
                      {'source_unchanged': False}, {'failure': 'StopRequested'},
                      {'artifact': {'status': 'unavailable'}}, {'cleanup': {'status': 'unknown'}}):
            with self.subTest(patch=patch):
                self.assertEqual(capture.classify({**report, **patch}, 8, 20)['status'], 'withhold')
        for reason in ('unsupported model', 'inventory mismatch', 'unknown parent'):
            broken = copy.deepcopy(report); broken['lifecycle']['failures'].append({'failure': reason})
            self.assertEqual(capture.classify(broken, 8, 20)['status'], 'withhold')
        report['lifecycle']['inventory'][0]['effort'] = 'low'
        self.assertEqual(capture.classify(report, 8, 20)['status'], 'withhold')

    @unittest.skipUnless(os.environ.get('DEADLINE_CAPTURE_DOCKER') == '1', 'explicit synthetic Docker capture calibration')
    def test_normal_deadline_invalid_missing_and_active_child(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(os.environ.get('DEADLINE_CAPTURE_EVIDENCE', str(Path(d)/'captures')))
            root.mkdir(parents=True, mode=0o700, exist_ok=False)
            initial = capture.identity(); capture.save(root/'plan.json', {'source_sha256': initial, 'live_provider_calls': 0})
            for mode in ('normal', 'deadline', 'invalid', 'missing', 'child'):
                with self.subTest(mode=mode):
                    p = root/mode; r = capture.run(p, mode); actor = capture.read(p/'actor/result.json')
                    self.assertTrue(actor['removed'] and actor['credential_copy_removed'])
                    self.assertEqual(capture.read(p/'manifest.json')['source_sha256'], initial)
                    if mode == 'missing':
                        self.assertEqual(r['status'], 'withhold')
                        with self.assertRaises(ValueError): capture.assess(p)
                        continue
                    self.assertEqual(r['status'], 'evaluable', r)
                    self.assertEqual(r['normal_completion'], mode == 'normal')
                    if mode != 'normal':
                        self.assertEqual(actor['quality']['status'], 'withhold')
                        self.assertEqual(actor['bridge']['reason'], 'TimeoutError: development deadline')
                        self.assertEqual(r['original_budget']['wall_clock'], 'exceeded')
                    self.assertEqual(len(actor['lifecycle']['inventory']), 2 if mode == 'child' else 1)
                    before = capture.sha(p/'actor/result.json')
                    artifact_before = capture.sha(p/'actor/submission.py')
                    if mode == 'child':
                        self.assertTrue(b'# capture heartbeat' in (p/'actor/submission.py').read_bytes(),
                                        'child did not begin writing before capture')
                    a = capture.assess(p)
                    self.assertEqual(a['status'], 'invalid-policy' if mode == 'invalid' else 'measured', a)
                    self.assertEqual(a['evaluation']['cleanup'], 'confirmed')
                    self.assertEqual(capture.sha(p/'actor/result.json'), before)
                    self.assertEqual(capture.sha(p/'actor/submission.py'), artifact_before)
                    self.assertFalse(a['old_runs_reinterpreted'])
                    if mode == 'normal':
                        for name in ('actor/submission.py', 'public/probe.json', 'manifest.json'):
                            modified = Path(d)/('tampered-'+name.replace('/', '-'))
                            shutil.copytree(p, modified)
                            (modified/name).chmod(0o600); (modified/name).write_text('changed')
                            with self.assertRaises((ValueError, json.JSONDecodeError)): capture.assess(modified)
            self.assertEqual(capture.identity(), initial)

    @unittest.skipUnless(os.environ.get('DEADLINE_CAPTURE_DOCKER') == '1', 'explicit synthetic Docker capture calibration')
    def test_external_interrupt_is_not_an_admitted_deadline(self):
        with tempfile.TemporaryDirectory() as d:
            evidence = os.environ.get('DEADLINE_CAPTURE_EVIDENCE')
            p = Path(evidence+'-interrupted') if evidence else Path(d)/'interrupted'
            process = subprocess.Popen([sys.executable, str(HERE/'capture.py'), '--profile', 'deadline', '--output', str(p)],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                until = time.monotonic()+60; marker = p/'actor/work/capture-ready.txt'
                while not marker.exists() and time.monotonic()<until and process.poll() is None: time.sleep(.1)
                self.assertTrue(marker.exists())
                process.send_signal(signal.SIGTERM); process.communicate(timeout=40)
                actor = capture.read(p/'actor/result.json'); result = capture.read(p/'capture.json')
                self.assertEqual(result['status'], 'withhold')
                self.assertTrue(actor['removed'] and actor['credential_copy_removed'])
                self.assertFalse((p/'assessment.json').exists())
            finally:
                if process.poll() is None: process.terminate(); process.communicate(timeout=40)


if __name__ == '__main__': unittest.main()

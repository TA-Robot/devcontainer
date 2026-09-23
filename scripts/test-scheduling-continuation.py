import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

HERE = Path(__file__).resolve().parents[1]/'experiments/development-harness/scheduling/continuation_pair_v1'
spec = importlib.util.spec_from_file_location('continuation_pair_tests', HERE/'run.py')
pair = importlib.util.module_from_spec(spec); spec.loader.exec_module(pair)


class ContinuationTests(unittest.TestCase):
    def test_common_initial_source_and_public_boundary(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); sealed = pair.prepare_inputs(root, False)
            self.assertEqual(set(sealed['public']), {'ACTOR_ONLY', 'RUNTIME.md', 'TASK.md', 'development.json',
                'fifo.py', 'probe.json', 'public_check.py', 'runtime.py', 'transport.py', 'initial.py', 'INITIAL.md'})
            self.assertEqual(pair.sha(root/'public/initial.py'), pair.read(HERE/'config.json')['initial_sha256'])
            self.assertEqual((root/'public/initial.py').read_bytes(), (HERE/'initial-policy.txt').read_bytes())
            populations = pair.load('continuation_populations_test', pair.SCHEDULING/'refinement_cohort_v1/populations.py')
            new = populations.generate(pair.read(HERE/'config.json'))
            old = populations.generate(pair.read(pair.SCHEDULING/'refinement_cohort_v1/config.json'))
            for split in new:
                self.assertEqual(len(new[split]), 24)
                self.assertNotEqual(new[split], old[split])
            self.assertEqual(pair.read(pair.SCHEDULING/'native_recovery_v1/validation.json')['source_sha256'], pair.actor_module().identity())

    def test_barrier_requires_both_developers_and_same_initial_artifact(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); pair.prepare_inputs(root, True); actors = {}
            import shutil
            for name in ('solo', 'adaptive'):
                p = root/'actors'/name; p.mkdir(parents=True)
                shutil.copytree(root/'public', p/'public')
                (p/'submission.py').write_text('code data only')
                (p/'prompt.private.txt').write_text('prompt data')
                pair.save(root/('start-'+name+'.json'), {'prompt_sha256': pair.sha(p/'prompt.private.txt')})
                r = {'quality': {'status': 'eligible'}, 'cleanup': {'status': 'confirmed'},
                     'source_unchanged': True, 'artifact': {'status': 'sealed', 'sha256': pair.sha(p/'submission.py')}}
                pair.save(p/'result.json', r); actors[name] = r
            self.assertEqual(set(pair.barrier(root, actors)), {'initial', 'solo', 'adaptive'})
            (root/'actors/solo/prompt.private.txt').write_text('changed prompt')
            with self.assertRaisesRegex(ValueError, 'prompt changed'): pair.barrier(root, actors)
            (root/'actors/solo/prompt.private.txt').write_text('prompt data')
            with self.assertRaisesRegex(ValueError, 'all conditions'): pair.barrier(root, {'solo': actors['solo']})
            initial = (root/'public/initial.py').read_bytes()
            (root/'public/initial.py').write_text('changed baseline')
            with self.assertRaisesRegex(ValueError, 'baseline changed'): pair.barrier(root, actors)
            (root/'public/initial.py').write_bytes(initial)
            (root/'actors/adaptive/public/initial.py').write_text('different starting point')
            with self.assertRaisesRegex(ValueError, 'different public'): pair.barrier(root, actors)

    def test_source_mismatch_and_joint_triage(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); pair.save(root/'plan.json', {'source_sha256': {}})
            with self.assertRaisesRegex(ValueError, 'seal mismatch'): pair.execute(root, True, None, 'normal')
            self.assertFalse((root/'execution-start.json').exists())
        cases = pair.load('continuation_report_population', pair.SCHEDULING/'refinement_cohort_v1/populations.py').generate(pair.read(HERE/'config.json'))['qualification']
        def evaluation(value):
            return {'status': 'completed', 'all_containers_removed': True, 'cases': [
                {'id': c['id'], 'status': 'measured', 'execution': {'removed': True}, 'result': {
                    'on_time_value': value, 'offered_value': 20, 'unfinished_value': 0, 'deadline_deficit': 0,
                    'busy_worker_ticks': 3, 'interrupted_worker_ticks': 0, 'unfinished_worker_ticks': 0,
                    'service_classes': {'16': {'total': 1, 'on_time': 1}}, 'response_p95_completed': 3,
                    'response_sample_count': 1, 'trace': ['private trace'], 'completion_times': {}}} for c in cases]}
        raw = {'quality_status': 'measured', 'output_budget_admission': 'withhold',
               'assessments': {k: {'evaluation': evaluation(v)} for k, v in [('initial', 19), ('solo', 17), ('adaptive', 18)]}}
        reporter = pair.load('continuation_reporter_test', HERE/'report.py')
        result = reporter.summarize(raw, {})
        self.assertTrue(result['comparisons']['adaptive_vs_solo']['triage_promising'])
        self.assertFalse(result['pair_triage_promising'])
        self.assertEqual(result['output_budget_admission'], 'withhold')
        self.assertNotIn('private trace', json.dumps(result))
        self.assertIn('private trace', json.dumps(raw))
        raw['assessments']['initial']['evaluation'] = evaluation(16)
        self.assertTrue(reporter.summarize(raw, {})['pair_triage_promising'])

    @unittest.skipUnless(os.environ.get('SCHEDULING_CONTINUATION_DOCKER') == '1', 'explicit Docker continuation preflight')
    def test_frozen_pair_edit_repair_missing_cost_and_deadline(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(os.environ.get('SCHEDULING_CONTINUATION_EVIDENCE', str(Path(d)/'pairs')))
            base.mkdir(parents=True, mode=0o700, exist_ok=False)
            initial = pair.identity(); pair.save(base/'plan.json', {'source_sha256': initial, 'live_provider_calls': 0})
            for profile in ('normal', 'missing', 'cost', 'timeout'):
                with self.subTest(profile=profile):
                    path = base/profile; controller = pair.run(path, fake=True, fake_case=profile)
                    result = pair.read(path/'result.json')
                    self.assertTrue(all(controller['recovery'].values()), controller)
                    if profile == 'timeout':
                        self.assertEqual(controller['status'], 'withhold', result)
                        self.assertEqual(set(result['actors']), {'solo'})
                        self.assertFalse((path/'start-adaptive.json').exists())
                        self.assertFalse((path/'barrier.json').exists())
                        self.assertEqual(result['assessments'], {})
                        continue
                    self.assertEqual(controller['status'], 'completed', result)
                    self.assertEqual(controller['quality_status'], 'measured')
                    self.assertEqual(controller['output_budget_admission'], 'admitted' if profile == 'normal' else 'withhold')
                    self.assertEqual(set(pair.read(path/'barrier.json')['actors']), {'initial', 'solo', 'adaptive'})
                    baseline = result['assessments']['initial']['evaluation']['cases']
                    for name, row in result['actors'].items():
                        work = path/'actors'/name/'work'
                        self.assertFalse(pair.read(work/'broken.json')['valid'])
                        self.assertTrue(pair.read(work/'repaired.json')['valid'])
                        self.assertTrue(all(pair.read(work/'boundary.json').values()))
                        self.assertEqual(pair.read(work/'initial-hash.json')['sha256'], pair.read(HERE/'config.json')['initial_sha256'])
                        self.assertEqual((path/'actors'/name/'submission.py').read_bytes(), (HERE/'initial-policy.txt').read_bytes()+b'\n# synthetic verified continuation\n')
                        self.assertTrue(row['removed'] and row['credential_copy_removed'])
                        self.assertEqual(len(row['lifecycle']['inventory']), 1 if name == 'solo' else 2)
                        requests = pair.read(path/'actors'/name/'stdout.private.txt')['requests']
                        self.assertTrue(all(r['shell_available'] for r in requests))
                        self.assertTrue(all(r['spawn_available'] == (name == 'adaptive') for r in requests))
                        rows = result['assessments'][name]['evaluation']['cases']
                        self.assertEqual([r['result'] for r in rows], [r['result'] for r in baseline])
                    if profile == 'missing': self.assertEqual(result['actors']['solo']['budget']['output_tokens'], 'unknown')
                    if profile == 'cost': self.assertEqual(result['actors']['solo']['budget']['output_tokens'], 'exceeded')
                    with self.assertRaises(FileExistsError): pair.run(path, fake=True, fake_case=profile)
            self.assertEqual(pair.identity(), initial)

    @unittest.skipUnless(os.environ.get('SCHEDULING_CONTINUATION_DOCKER') == '1', 'explicit Docker continuation preflight')
    def test_outer_interrupt_stops_before_second_start(self):
        with tempfile.TemporaryDirectory() as d:
            evidence = os.environ.get('SCHEDULING_CONTINUATION_EVIDENCE')
            path = Path(evidence+'-interrupted') if evidence else Path(d)/'interrupted'
            process = subprocess.Popen([sys.executable, str(HERE/'run.py'), '--fake', '--fake-case', 'timeout',
                                        '--output', str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                until = time.monotonic()+60; marker = path/'actors/solo/work/probe-running.txt'
                while not marker.exists() and time.monotonic() < until and process.poll() is None: time.sleep(.1)
                self.assertTrue(marker.exists())
                process.send_signal(signal.SIGTERM); process.communicate(timeout=40)
                control = pair.read(path/'controller.json')
                self.assertEqual(control['status'], 'withhold')
                self.assertTrue(all(control['recovery'].values()), control)
                self.assertFalse((path/'start-adaptive.json').exists())
                self.assertFalse((path/'barrier.json').exists())
            finally:
                if process.poll() is None: process.terminate(); process.communicate(timeout=40)


if __name__ == '__main__': unittest.main()

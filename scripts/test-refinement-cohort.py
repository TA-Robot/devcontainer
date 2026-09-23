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

HERE = Path(__file__).resolve().parents[1]/'experiments/development-harness/scheduling/refinement_cohort_v1'
spec = importlib.util.spec_from_file_location('refinement_cohort', HERE/'run.py')
cohort = importlib.util.module_from_spec(spec); spec.loader.exec_module(cohort)
reporter = cohort.load('cohort_report_test', HERE/'report.py')


class CohortTests(unittest.TestCase):
    def test_new_populations_and_fixed_conditions(self):
        config = cohort.read(HERE/'config.json')
        self.assertEqual(config['conditions'], ['standard', 'refined', 'solo'])
        self.assertEqual(config['max_live_starts'], 3)
        populations = cohort.load('cohort_population_test', HERE/'populations.py').generate(config)
        old = cohort.load('old_cohort_population_test', cohort.SCHEDULING/'dynamic_v1/workloads.py')
        runtime = cohort.load('cohort_validity_test', cohort.SCHEDULING/'dynamic_v1/runtime.py')
        signatures = []
        for split in ('development', 'qualification'):
            cases = populations[split]
            self.assertEqual(len(cases), 24)
            self.assertEqual({r['id'] for r in cases}, {r['id'] for r in old.suite(split)})
            self.assertNotEqual(cases, old.suite(split))
            for c in cases:
                runtime.validate(c)
                signatures.append(json.dumps({k: v for k, v in c.items() if k != 'id'}, sort_keys=True))
        self.assertEqual(len(set(signatures)), 48)
        native = cohort.read(cohort.SCHEDULING/'native_recovery_v1/validation.json')
        self.assertEqual(native['source_sha256'], cohort.actor_module().identity())

    def test_missing_condition_and_changed_artifact_cannot_cross_barrier(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); actors = {}
            (root/'qualification.private.json').write_text('[]')
            for name in ('standard', 'refined', 'solo'):
                folder = root/'actors'/name; (folder/'public').mkdir(parents=True)
                (folder/'submission.py').write_text('not host executable')
                r = {'quality': {'status': 'eligible'}, 'cleanup': {'status': 'confirmed'},
                     'artifact': {'status': 'sealed', 'sha256': cohort.sha(folder/'submission.py')},
                     'source_unchanged': True}
                cohort.save(folder/'result.json', r); actors[name] = r
            cohort.save(root/'input-seal.json', {'public': {}, 'assessment_sha256': cohort.sha(root/'qualification.private.json')})
            self.assertEqual(set(cohort.barrier(root, actors)), set(actors))
            with self.assertRaisesRegex(ValueError, 'all conditions'):
                cohort.barrier(root, {k: v for k, v in actors.items() if k != 'solo'})
            (root/'actors/refined/submission.py').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'changed refined'):
                cohort.barrier(root, actors)

    def test_source_mismatch_rejects_before_start_and_empty_triage_does_not_win(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            cohort.save(root/'plan.json', {'source_sha256': {}})
            with self.assertRaisesRegex(ValueError, 'seal mismatch'):
                cohort.execute(root, True, None, 'normal')
            self.assertFalse((root/'execution-start.json').exists())
        comparison = {'overall': {'difference': {'on_time_value': 0, 'critical_on_time': 0}},
                      'bands': {'severe': {'difference': {'critical_on_time': 0}}}}
        self.assertFalse(reporter.promising(comparison))
        comparison['overall']['difference']['on_time_value'] = 1
        self.assertTrue(reporter.promising(comparison))
        comparison['bands']['severe']['difference']['critical_on_time'] = -1
        self.assertFalse(reporter.promising(comparison))

    def test_report_reuses_metrics_without_promoting_output_admission(self):
        population = cohort.load('report_population_test', HERE/'populations.py').generate(cohort.read(HERE/'config.json'))
        rows = [{'id': c['id'], 'status': 'measured', 'execution': {'removed': True}, 'result': {
                 'on_time_value': 16, 'offered_value': 16, 'unfinished_value': 0, 'deadline_deficit': 0,
                 'busy_worker_ticks': 3, 'interrupted_worker_ticks': 0, 'unfinished_worker_ticks': 0,
                 'service_classes': {'16': {'total': 1, 'on_time': 1}},
                 'response_p95_completed': 3, 'response_sample_count': 1, 'trace': ['TRACE'], 'completion_times': {'x': 3}}}
                for c in population['qualification']]
        evaluation = {'status': 'completed', 'all_containers_removed': True, 'cases': rows}
        r = {'quality_status': 'measured', 'output_budget_admission': 'withhold',
             'assessments': {n: {'evaluation': evaluation} for n in ('standard', 'refined', 'solo')}}
        summary = reporter.summarize(r, {'population': 'fresh'})
        self.assertEqual(summary['output_budget_admission'], 'withhold')
        self.assertEqual(summary['comparisons']['refined_vs_standard']['overall']['refined']['on_time_value'], 384)
        self.assertFalse(summary['comparisons']['refined_vs_standard']['triage_promising'])
        self.assertNotIn('TRACE', json.dumps(summary))
        self.assertEqual(rows[0]['result']['trace'], ['TRACE'])

    @unittest.skipUnless(os.environ.get('REFINEMENT_COHORT_DOCKER') == '1', 'explicit cohort Docker preflight')
    def test_frozen_cohort_barrier_cost_missing_and_deadline(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(os.environ.get('REFINEMENT_COHORT_EVIDENCE', str(Path(d)/'cohorts')))
            base.mkdir(parents=True, mode=0o700, exist_ok=False)
            initial = cohort.identity()
            cohort.save(base/'plan.json', {'source_sha256': initial, 'live_provider_calls': 0})
            for profile in ('normal', 'missing', 'cost', 'timeout'):
                with self.subTest(profile=profile):
                    path = base/profile
                    controller = cohort.run(path, fake=True, fake_case=profile)
                    result = cohort.read(path/'result.json')
                    self.assertTrue(all(controller['recovery'].values()), controller)
                    self.assertEqual(cohort.read(path/'plan.json')['source_sha256'], initial)
                    if profile == 'timeout':
                        self.assertEqual(controller['status'], 'withhold', result)
                        self.assertEqual(set(result['actors']), {'standard', 'refined'})
                        self.assertFalse((path/'start-solo.json').exists())
                        self.assertFalse((path/'barrier.json').exists())
                        self.assertEqual(result['assessments'], {})
                        continue
                    self.assertEqual(controller['status'], 'completed', result)
                    self.assertEqual(controller['quality_status'], 'measured')
                    expected = 'admitted' if profile == 'normal' else 'withhold'
                    self.assertEqual(controller['output_budget_admission'], expected)
                    sealed = cohort.read(path/'barrier.json')
                    self.assertEqual(set(sealed['actors']), {'standard', 'refined', 'solo'})
                    for name, row in result['actors'].items():
                        self.assertLess((path/'actors'/name/'result.json').stat().st_mtime_ns,
                                        (path/'barrier.json').stat().st_mtime_ns)
                        self.assertEqual(result['assessments'][name]['cleanup'], 'confirmed')
                        self.assertEqual(cohort.read(path/('start-'+name+'.json'))['prompt_sha256'], cohort.sha(cohort.PROMPTS[name]))
                    if profile == 'missing': self.assertEqual(result['actors']['refined']['budget']['output_tokens'], 'unknown')
                    if profile == 'cost': self.assertEqual(result['actors']['refined']['budget']['output_tokens'], 'exceeded')
                    with self.assertRaises(FileExistsError): cohort.run(path, fake=True, fake_case=profile)
            self.assertEqual(cohort.identity(), initial)

    @unittest.skipUnless(os.environ.get('REFINEMENT_COHORT_DOCKER') == '1', 'explicit cohort Docker preflight')
    def test_outer_interrupt_recovers_active_actor_without_next_start(self):
        with tempfile.TemporaryDirectory() as d:
            evidence = os.environ.get('REFINEMENT_COHORT_EVIDENCE')
            path = Path(evidence+'-interrupted') if evidence else Path(d)/'interrupted'
            process = subprocess.Popen([sys.executable, str(HERE/'run.py'), '--fake', '--fake-case', 'timeout',
                                        '--output', str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                deadline = time.monotonic()+60
                marker = path/'actors/refined/work/child-running.txt'
                while not marker.exists() and time.monotonic() < deadline and process.poll() is None:
                    time.sleep(.1)
                self.assertTrue(marker.exists())
                process.send_signal(signal.SIGTERM)
                process.communicate(timeout=40)
                control = cohort.read(path/'controller.json')
                self.assertEqual(control['status'], 'withhold')
                self.assertTrue(all(control['recovery'].values()), control)
                self.assertFalse((path/'start-solo.json').exists())
                self.assertFalse((path/'barrier.json').exists())
                for name in control['recovery']:
                    self.assertFalse((path/'actors'/name/'auth.private.json').exists())
            finally:
                if process.poll() is None:
                    process.terminate(); process.communicate(timeout=40)


if __name__ == '__main__': unittest.main()

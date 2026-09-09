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

HERE = Path(__file__).resolve().parents[1]/'experiments/development-harness/scheduling/termination_pair_v1'
spec = importlib.util.spec_from_file_location('continuation_pair_tests', HERE/'run.py')
pair = importlib.util.module_from_spec(spec); spec.loader.exec_module(pair)


class TerminationPairTests(unittest.TestCase):
    def test_pending_create_absence_and_late_appearance_do_not_certify_recovery(self):
        recovery = pair.load('termination_recovery_test', HERE/'recovery.py')
        from types import SimpleNamespace
        name = 'scheduling-native-'+'a'*32
        for appearance in (None, .4):
            now = [0.0]; removed = []
            def command(args, **kwargs):
                self.assertGreater(kwargs['timeout'], 0)
                self.assertLessEqual(kwargs['timeout'], 1-now[0]+1e-9)
                present = appearance is not None and now[0] >= appearance and not removed
                if args[1] == 'rm':
                    removed.append(args[-1]); return SimpleNamespace(returncode=0, stdout='', stderr='')
                return SimpleNamespace(returncode=0 if present else 1,
                    stdout=json.dumps([{'Name': '/'+name}]) if present else '', stderr='' if present else 'error: no such object: '+name)
            def pause(seconds): now[0] += seconds
            result = recovery.drain(name, create_completed=False, seconds=1, command=command, clock=lambda: now[0], pause=pause)
            self.assertEqual(result['status'], 'unknown')
            self.assertEqual(result['observed_container'], appearance is not None)
            self.assertEqual(removed, [] if appearance is None else [name])
            self.assertLessEqual(result['elapsed_seconds'], 1)
        result = recovery.drain(name, create_completed=True, seconds=1,
            command=lambda *a, **k: SimpleNamespace(returncode=1, stdout='', stderr='error: no such object: '+name))
        self.assertEqual(result['status'], 'confirmed')
        with self.assertRaisesRegex(ValueError, 'unowned'):
            recovery.drain('someone-elses-container', create_completed=False, seconds=1)

    def test_pending_create_propagates_from_authoritative_records(self):
        recovery = pair.load('termination_recovery_contract_test', HERE/'recovery.py')
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d); name = 'scheduling-native-'+'b'*32
            pair.save(folder/'start.json', {'container': name})
            pair.save(folder/'result.json', {'failure': 'Docker create timeout', 'cleanup': {'status': 'confirmed'}})
            (folder/'auth.private.json').write_text('synthetic, not a credential')
            with patch.object(recovery, 'drain', return_value={'status': 'unknown'}) as drain:
                result = recovery.actor(folder, 20)
                self.assertFalse(drain.call_args.kwargs['create_completed'])
                self.assertEqual(result['status'], 'unknown')
                self.assertFalse((folder/'auth.private.json').exists())
            (folder/'evaluation').mkdir()
            pair.save(folder/'evaluation/result.json', {'cases': [{'status': 'unmeasured',
                'failure': 'TimeoutExpired', 'failure_detail': "Command '['docker', 'create']' timed out",
                'execution': {'container': 'scheduling-policy-'+'c'*32, 'removed': True}}]})
            with patch.object(recovery, 'drain', return_value={'status': 'unknown'}) as drain:
                self.assertEqual(recovery.assessment(folder, 20), [{'status': 'unknown'}])
                self.assertFalse(drain.call_args.kwargs['create_completed'])
            record = pair.read(folder/'evaluation/result.json')
            record['cases'][0].update(failure='StopRequested', failure_detail='external interruption')
            (folder/'evaluation/result.json').write_text(json.dumps(record))
            with patch.object(recovery, 'drain', return_value={'status': 'unknown'}) as drain:
                recovery.assessment(folder, 20)
                self.assertFalse(drain.call_args.kwargs['create_completed'])
            record['cases'][0]['execution']['startup_seconds'] = .1
            (folder/'evaluation/result.json').write_text(json.dumps(record))
            with patch.object(recovery, 'drain', return_value={'status': 'confirmed'}) as drain:
                recovery.assessment(folder, 20)
                self.assertTrue(drain.call_args.kwargs['create_completed'])

    def test_common_initial_source_and_public_boundary(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); sealed = pair.prepare_inputs(root, False)
            self.assertEqual(set(sealed['public']), {'ACTOR_ONLY', 'RUNTIME.md', 'TASK.md', 'development.json',
                'fifo.py', 'probe.json', 'public_check.py', 'runtime.py', 'transport.py', 'initial.py', 'INITIAL.md'})
            self.assertEqual(pair.sha(root/'public/initial.py'), pair.read(HERE/'config.json')['initial_sha256'])
            self.assertEqual((root/'public/initial.py').read_bytes(), (pair.SCHEDULING/'continuation_pair_v1/initial-policy.txt').read_bytes())
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
            pair.save(root/'plan.json', {'source_sha256': pair.identity()})
            import shutil
            for name in ('solo', 'adaptive'):
                p = root/'actors'/name; p.mkdir(parents=True)
                shutil.copytree(root/'public', p/'public')
                (p/'submission.py').write_text('code data only')
                (p/'prompt.private.txt').write_text('prompt data')
                pair.save(root/('start-'+name+'.json'), {'prompt_sha256': pair.sha(p/'prompt.private.txt'), 'requested_development_seconds': 60, 'recovery_bound_seconds': 20})
                r = {'quality': {'status': 'eligible'}, 'cleanup': {'status': 'confirmed'},
                     'condition': name, 'elapsed_seconds': 2, 'bridge': {'development_seconds': 1},
                     'lifecycle': {'status': 'completed', 'inventory': [{'model': 'gpt-6-astra', 'effort': 'high', 'cli_version': '0.153.0'}]},
                     'budget': {}, 'admission': 'admitted', 'usage': {'status': 'complete'},
                     'source_unchanged': True, 'artifact': {'status': 'sealed', 'sha256': pair.sha(p/'submission.py')}}
                pair.save(p/'result.json', r); actors[name] = r
                pair.save(root/('capture-'+name+'.json'), {
                    'classification': pair.classify(r, pair.read(root/('start-'+name+'.json'))),
                    'actor_result_sha256': pair.sha(p/'result.json'),
                    'start_sha256': pair.sha(root/('start-'+name+'.json')),
                    'input_seal_sha256': pair.sha(root/'input-seal.json')})
            self.assertEqual(set(pair.barrier(root, actors)), {'initial', 'solo', 'adaptive'})
            (root/'actors/solo/prompt.private.txt').write_text('changed prompt')
            with self.assertRaisesRegex(ValueError, 'prompt changed'): pair.barrier(root, actors)
            (root/'actors/solo/prompt.private.txt').write_text('prompt data')
            with self.assertRaisesRegex(ValueError, 'all conditions'): pair.barrier(root, {'solo': actors['solo']})
            initial = (root/'public/initial.py').read_bytes()
            (root/'public/initial.py').write_text('changed baseline')
            with self.assertRaisesRegex(ValueError, 'root public projection changed'): pair.barrier(root, actors)
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
        raw = {'quality_status': 'measured', 'original_episode_admission': {}, 'captures': {}, 'output_budget_admission': 'withhold',
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

    @unittest.skipUnless(os.environ.get('TERMINATION_PAIR_DOCKER') == '1', 'explicit Docker pair preflight')
    def test_both_captures_barrier_assessment_and_failure_axes(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(os.environ.get('TERMINATION_PAIR_EVIDENCE', str(Path(d)/'pairs')))
            base.mkdir(parents=True, mode=0o700, exist_ok=False)
            initial = pair.identity(); pair.save(base/'plan.json', {'source_sha256': initial, 'live_provider_calls': 0})
            for profile in ('normal', 'usage', 'cost', 'deadline', 'invalid', 'missing'):
                with self.subTest(profile=profile):
                    path = base/profile; controller = pair.run(path, fake=True, fake_case=profile)
                    result = pair.read(path/'result.json')
                    self.assertTrue(all(controller['recovery'].values()), controller)
                    if profile == 'missing':
                        self.assertEqual(controller['status'], 'withhold', result)
                        self.assertEqual(set(result['actors']), {'solo'})
                        self.assertFalse((path/'start-adaptive.json').exists())
                        self.assertFalse((path/'barrier.json').exists())
                        self.assertEqual(result['assessments'], {})
                        continue
                    self.assertEqual(controller['status'], 'completed', result)
                    self.assertEqual(controller['quality_status'], 'invalid-policy' if profile == 'invalid' else 'measured')
                    self.assertEqual(controller['output_budget_admission'], 'admitted' if profile == 'normal' else 'withhold')
                    self.assertEqual(set(pair.read(path/'barrier.json')['actors']), {'initial', 'solo', 'adaptive'})
                    self.assertEqual(set(result['assessments']), {'initial', 'solo', 'adaptive'})
                    baseline = result['assessments']['initial']['evaluation']['cases']
                    for name, row in result['actors'].items():
                        folder = path/'actors'/name; work = folder/'work'
                        capture = result['captures'][name]['classification']
                        self.assertEqual(capture['status'], 'evaluable')
                        self.assertLessEqual(capture['capture_upper_bound_seconds'], capture['requested_development_seconds']+20)
                        self.assertTrue(row['removed'] and row['credential_copy_removed'])
                        self.assertEqual(len(row['lifecycle']['inventory']), 1 if name == 'solo' else 2)
                        self.assertEqual(pair.sha(folder/'public/initial.py'), pair.read(HERE/'config.json')['initial_sha256'])
                        if profile in ('deadline', 'invalid'):
                            self.assertEqual(capture['basis'], 'deadline_capture')
                            self.assertEqual(row['quality']['status'], 'withhold')
                            self.assertEqual(row['lifecycle']['status'], 'unknown')
                            self.assertEqual(row['budget']['wall_clock'], 'exceeded')
                            self.assertFalse(capture['normal_completion'])
                            if name == 'adaptive': self.assertIn(b'# capture heartbeat', (folder/'submission.py').read_bytes())
                        else:
                            self.assertEqual(capture['basis'], 'normal_completion')
                            self.assertFalse(pair.read(work/'broken.json')['valid'])
                            self.assertTrue(pair.read(work/'repaired.json')['valid'])
                            self.assertTrue(all(pair.read(work/'boundary.json').values()))
                            requests = pair.read(folder/'stdout.private.txt')['requests']
                            self.assertTrue(all(r['shell_available'] for r in requests))
                            self.assertTrue(all(r['spawn_available'] == (name == 'adaptive') for r in requests))
                        assessment = result['assessments'][name]
                        self.assertEqual(pair.sha(folder/'submission.py'), assessment['candidate_sha256'])
                        if profile == 'invalid' and name == 'solo':
                            self.assertEqual(assessment['status'], 'invalid-policy')
                        else:
                            self.assertEqual(assessment['status'], 'measured')
                            self.assertEqual([r['result'] for r in assessment['evaluation']['cases']], [r['result'] for r in baseline])
                    if profile == 'usage': self.assertEqual(result['actors']['solo']['budget']['output_tokens'], 'unknown')
                    if profile == 'cost': self.assertEqual(result['actors']['solo']['budget']['output_tokens'], 'exceeded')
                    # Tamper copies only: preserve original preflight evidence.
                    import shutil
                    changed = Path(d)/('changed-'+profile); shutil.copytree(path, changed)
                    start = changed/'start-solo.json'; start.write_text(start.read_text()+' ')
                    with self.assertRaisesRegex(ValueError, 'changed solo capture'): pair.barrier(changed, result['actors'])
                    with self.assertRaises(FileExistsError): pair.run(path, fake=True, fake_case=profile)
            self.assertEqual(pair.identity(), initial)

    @unittest.skipUnless(os.environ.get('TERMINATION_PAIR_DOCKER') == '1', 'explicit Docker continuation preflight')
    def test_outer_interrupt_stops_before_second_start(self):
        with tempfile.TemporaryDirectory() as d:
            evidence = os.environ.get('TERMINATION_PAIR_EVIDENCE')
            path = Path(evidence+'-interrupted') if evidence else Path(d)/'interrupted'
            process = subprocess.Popen([sys.executable, str(HERE/'run.py'), '--fake', '--fake-case', 'deadline',
                                        '--output', str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                until = time.monotonic()+60; marker = path/'actors/solo/work/capture-ready.txt'
                while not marker.exists() and time.monotonic() < until and process.poll() is None: time.sleep(.1)
                self.assertTrue(marker.exists())
                process.send_signal(signal.SIGTERM); process.communicate(timeout=40)
                control = pair.read(path/'controller.json')
                self.assertEqual(control['status'], 'withhold')
                audit = pair.read(path/'actors/solo/recovery-audit.json')
                actor = pair.read(path/'actors/solo/result.json')
                # An interrupted bridge may never seal proof that create
                # completed. Keep that uncertainty even when absence is seen.
                expected = 'confirmed' if actor.get('bridge') else 'unknown'
                self.assertEqual(audit['status'], expected, audit)
                self.assertEqual(control['recovery']['solo'], expected == 'confirmed')
                self.assertTrue(audit['credential_copy_absent'])
                observed = subprocess.run(['docker', 'inspect', actor['container']], capture_output=True, text=True, timeout=15)
                self.assertEqual(observed.returncode, 1)
                self.assertIn('no such object', observed.stderr.lower())
                self.assertFalse((path/'start-adaptive.json').exists())
                self.assertFalse((path/'barrier.json').exists())
            finally:
                if process.poll() is None: process.terminate(); process.communicate(timeout=40)


if __name__ == '__main__': unittest.main()

"""Real terminal recorder and optional Docker, deterministic providers only."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'experiments/development-harness/consultation'))
import flow_v1 as flow
sys.path.insert(0, str(flow.HERE / 'v1'))
import calibrate

PROVIDER = '''import json,sys,time
from pathlib import Path
root,payload,role,mode=Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3],sys.argv[4]
prompt=sys.stdin.read()
data=json.loads(payload.read_text())
if mode=='hang': time.sleep(60)
if role=='advisor':
 advice={'recommendation':'ADVICE_SENTINEL inspect the operation boundary',
         'evidence':['worker.py checkpoint'], 'uncertainty':'unverified until maker reproduces'}
 (root/'advice.json').write_text(json.dumps({} if mode=='bad-advice' else advice))
else:
 (root/'reproduction.json').write_text(json.dumps(data['plan']))
 (root/'diagnosis.json').write_text(json.dumps(data['diagnosis'] if mode!='bad-result' else {}))
(root/'DEVELOPMENT_HANDOFF.md').write_text('advice-seen' if 'ADVICE_SENTINEL' in prompt else 'no-advice')
if mode=='extra': (root/'ignored-by-mistake.txt').write_text('extra')
if mode=='source-edit': (root/'worker.py').write_text('fake source')
if mode!='unknown-usage':
 print(json.dumps({'type':'turn.completed','usage':{'input_tokens':100,'cached_input_tokens':20,'output_tokens':7}}),flush=True)
'''


class FakeTransport:
    provider_free = True
    image = 'sha256:' + 'b' * 64

    def __init__(self, workspace, role, provider, payload, mode):
        self.identity = uuid.uuid4().hex * 2
        self.workspace, self.role, self.provider, self.payload = workspace, role, provider, payload
        self.mode = mode
        self.running = False
        self.starts = 0

    def stopped(self):
        if self.running:
            raise ValueError('writer active')
        return {'stopped': True}

    def start(self):
        self.stopped()
        self.running = True
        self.starts += 1

    def stop_bounded(self, seconds):
        if self.mode == 'stop-failure':
            raise ValueError('no stop proof')
        self.running = False
        return {'stopped': True}

    def argv(self, manifest, seconds):
        return [sys.executable, str(self.provider), str(self.workspace), str(self.payload), self.role, self.mode]


class DockerTransport(flow.runner.Docker):
    provider_free = True

    def __init__(self, workspace, role, provider, payload, mode, image):
        name = 'consultation-test-' + uuid.uuid4().hex
        subprocess.run(['docker', 'create', '--name', name, '--label', 'dev.agentctl.benchmark=true',
                        '--network', 'none', '--read-only', '--tmpfs', '/tmp:rw,exec,mode=1777',
                        '--mount', f'type=bind,src={workspace},dst=/workspace',
                        '--mount', f'type=bind,src={provider},dst=/fake/provider.py,readonly',
                        '--mount', f'type=bind,src={payload},dst=/fake/payload.json,readonly',
                        image, 'sleep', 'infinity'], check=True, capture_output=True)
        super().__init__(name, workspace)
        self.role, self.mode = role, mode
        self.starts = 0

    def start(self):
        super().start()
        self.starts += 1

    def argv(self, manifest, seconds):
        return ['docker', 'exec', '-i', self.identity, 'python3', '-B', '/fake/provider.py',
                '/workspace', '/fake/payload.json', self.role, self.mode]


class ConsultationFlowTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='consultation-flow-test-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.provider = self.root / 'fake.py'
        self.provider.write_text(PROVIDER)
        source = self.root / 'reference'
        flow.case.create(source, 'effect-first')
        plan, diagnosis = calibrate.reference(source, 'effect-first')
        self.payload = self.root / 'payload.json'
        self.payload.write_text(json.dumps({'plan': plan, 'diagnosis': diagnosis}))
        self.config = {'kind': flow.KIND, 'execution': 'provider-free', 'variant': 'effect-first',
                       'order': ['solo', 'consult'], 'condition_seconds': 30, 'actor_seconds': 5,
                       'minimum_seconds': .1, 'minimum_output_tokens': 1, 'output_tokens': 100,
                       'stop_seconds': 2, 'capture_seconds': 5, 'capture_window_seconds': 2,
                       'snapshot_bytes': 1000000, 'advice_bytes': 4096}
        self.transports = {}
        self.modes = {}
        self.evaluations = 0
        self.output = self.root / 'run'

    def factory(self, condition, role, workspace):
        value = FakeTransport(workspace, role, self.provider, self.payload, self.modes.get((condition, role), 'ok'))
        self.transports[(condition, role)] = value
        return value

    def evaluator(self, source, variant):
        self.assertTrue(all(not t.running for t in self.transports.values()))
        self.evaluations += 1
        self.assertNotIn('advice.json', [p.name for p in source.iterdir()])
        self.assertFalse((source / flow.HANDOFF).exists())
        return flow.case.evaluate(source, variant)

    def run_flow(self):
        return flow.run(self.config, self.output, self.factory, self.evaluator)

    def test_pair_delivers_stopped_advice_counts_all_usage_and_grades_after_every_writer_stops(self):
        result = self.run_flow()
        self.assertEqual(result['status'], 'completed', result)
        self.assertTrue(result['all_writers_stopped'])
        self.assertEqual(self.evaluations, 2)
        a, b = result['conditions']['solo'], result['conditions']['consult']
        self.assertEqual(a['usage']['output_tokens'], 7)
        self.assertEqual(b['usage']['output_tokens'], 14)
        self.assertEqual(b['usage']['input_tokens'], 200)
        self.assertEqual(b['usage']['cached_input_tokens'], 40)
        self.assertEqual(a['quality']['status'], 'pass')
        self.assertEqual(b['quality']['status'], 'pass')
        self.assertEqual(b['advice']['semantic_adoption'], 'unknown')
        self.assertNotIn('ADVICE_SENTINEL', json.dumps(result))
        self.assertEqual((self.output / b['source'] / flow.HANDOFF).read_text(), 'advice-seen')
        self.assertEqual((self.output / a['source'] / flow.HANDOFF).read_text(), 'no-advice')
        for row in (a, b):
            self.assertGreater(row['execution_seconds'], sum(actor['clock']['development_seconds'] for actor in row['actors']))
        with self.assertRaises(FileExistsError):
            self.run_flow()

    def test_invalid_advice_and_unknown_usage_prevent_maker_dispatch(self):
        for mode in ('bad-advice', 'unknown-usage', 'extra', 'source-edit'):
            with self.subTest(mode=mode):
                self.output = self.root / mode
                self.transports = {}
                self.config['order'] = ['consult', 'solo']
                self.modes[('consult', 'advisor')] = mode
                result = self.run_flow()
                self.assertEqual(result['status'], 'interrupted')
                self.assertEqual(set(self.transports), {('consult', 'advisor')})
                self.assertEqual(result['conditions']['solo']['status'], 'not_started')
                self.assertEqual(self.evaluations, 0)

    def test_unconfirmed_stop_prevents_all_grading_including_completed_solo(self):
        self.modes[('consult', 'advisor')] = 'stop-failure'
        result = self.run_flow()
        self.assertFalse(result['all_writers_stopped'])
        self.assertEqual(result['failure'], 'stop-unconfirmed')
        self.assertEqual(self.evaluations, 0)

    def test_late_advisor_stops_and_cannot_dispatch_maker(self):
        self.config.update(order=['consult', 'solo'], actor_seconds=.15)
        self.modes[('consult', 'advisor')] = 'hang'
        result = self.run_flow()
        self.assertEqual(result['status'], 'interrupted')
        self.assertTrue(result['all_writers_stopped'])
        self.assertEqual(set(self.transports), {('consult', 'advisor')})

    def test_budget_exhaustion_is_shared_across_both_participants(self):
        self.config.update(order=['consult', 'solo'], output_tokens=7)
        result = self.run_flow()
        self.assertEqual(result['status'], 'interrupted')
        self.assertNotIn(('consult', 'maker'), self.transports)

    def test_maker_quality_failure_does_not_get_repaired_or_relabelled(self):
        self.modes[('consult', 'maker')] = 'bad-result'
        result = self.run_flow()
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['conditions']['consult']['quality']['status'], 'fail')
        self.assertEqual(len(self.transports), 3)

    def test_invalid_evaluator_result_remains_ungraded(self):
        broken = {'case_id': flow.case.CASE_ID, 'variant': 'effect-first', 'status': 'pass', 'checks': [None]}
        result = flow.run(self.config, self.output, self.factory, lambda *_: broken)
        self.assertEqual(result['status'], 'interrupted')
        self.assertIsNone(result['conditions']['solo']['quality'])
        for value in (None, {'status': 'pass'}, {**broken, 'checks': 'not-an-array'},
                      {**broken, 'checks': [{'name': c, 'status': 'failed'} for c in flow.case.CHECKS]}):
            self.assertFalse(flow.valid_quality(value, 'effect-first'))

    def test_live_mode_and_nonfinite_budgets_rejected_before_workspace_creation(self):
        for key, value in (('execution', 'live'), ('condition_seconds', float('nan')),
                           ('actor_seconds', True), ('advice_bytes', 100000)):
            config = copy.deepcopy(self.config)
            config[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                flow.run(config, self.output, self.factory)
            self.assertFalse(self.output.exists())

    @unittest.skipUnless(os.environ.get('CONSULTATION_FLOW_IMAGE'), 'set verified image ID')
    def test_real_docker_pair_and_external_evaluator(self):
        image = os.environ['CONSULTATION_FLOW_IMAGE']
        self.config.update(condition_seconds=60, capture_window_seconds=5)
        def factory(condition, role, workspace):
            value = DockerTransport(workspace, role, self.provider, self.payload,
                                    self.modes.get((condition, role), 'ok'), image)
            self.transports[(condition, role)] = value
            self.addCleanup(subprocess.run, ['docker', 'rm', '-f', value.identity], capture_output=True)
            return value
        def evaluator(source, variant):
            for transport in self.transports.values():
                self.assertTrue(transport.stopped()['stopped'])
            completed = subprocess.run(['docker', 'run', '--rm', '--network', 'none', '--read-only',
                '--tmpfs', '/tmp:rw,exec,mode=1777', '-e', 'PYTHONDONTWRITEBYTECODE=1',
                '--mount', f'type=bind,src={ROOT},dst=/repo,readonly',
                '--mount', f'type=bind,src={source},dst=/candidate,readonly', image, 'python3',
                '/repo/experiments/development-harness/consultation/v1/case.py', 'evaluate',
                '--workspace', '/candidate', '--variant', variant], capture_output=True, text=True, timeout=30)
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            return json.loads(completed.stdout)
        result = flow.run(self.config, self.output, factory, evaluator)
        self.assertEqual(result['status'], 'completed', result)
        self.assertTrue(all(r['quality']['status'] == 'pass' for r in result['conditions'].values()))
        # A real container writer is still running when the advisor deadline fires.
        # Stop proof must precede capture; no maker or evaluator may follow it.
        self.transports = {}
        self.config.update(order=['consult', 'solo'], actor_seconds=.4)
        self.modes[('consult', 'advisor')] = 'hang'
        late = flow.run(self.config, self.root / 'late-run', factory, evaluator)
        self.assertEqual(late['status'], 'interrupted', late)
        self.assertTrue(late['all_writers_stopped'])
        self.assertEqual(set(self.transports), {('consult', 'advisor')})
        self.assertIsNone(late['conditions']['consult']['quality'])
        self.assertEqual(late['conditions']['solo']['status'], 'not_started')


if __name__ == '__main__':
    unittest.main()

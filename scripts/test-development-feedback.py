"""P1 calibration: equal information, bounded feedback, immutable acceptance evidence."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'experiments/development-harness/feedback'))
import workflow
public = workflow.public
runner = workflow.runner

PROVIDER = '''import json,os,sys,subprocess
from pathlib import Path
root,release,mode=Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3]
prompt=sys.stdin.read()
(root/'last-prompt.txt').write_text(prompt)
good=mode=='self' or (mode!='always-bad' and 'Public check output from your submitted candidate' in prompt)
(root/'value.txt').write_text('good' if good else 'bad')
if mode=='self':
 p=subprocess.run([sys.executable,str(release/'value.py'),str(root)],capture_output=True)
 assert p.returncode==0
 (root/'self-checked').write_text('yes')
if mode!='unknown': print(json.dumps({'type':'turn.completed','usage':{'input_tokens':10,'output_tokens':5}}),flush=True)
'''
CHECK = '''import sys
from pathlib import Path
if (Path(sys.argv[1])/'value.txt').read_text()!='good':
 print('PUBLIC_VALUE_FAILURE: expected good'); raise SystemExit(1)
print('public value passed')
'''


class FakeDocker:
    image = 'sha256:' + 'a' * 64

    def __init__(self, row, provider):
        self.identity = public.sha(row['id'].encode())
        self.workspace = Path(row['workspace'])
        self.release = Path(row['release'])
        self.mode = row['mode']
        self.provider = provider
        self.running = False
        self.stop_seconds = 2
        self.start_delay = 0
        self.commands = []

    def stopped(self):
        if self.running:
            raise runner.Error('still running')
        return {'stopped': True}

    def environment(self):
        return {'fixture': 'shared synthetic environment'}

    def start(self):
        self.stopped()
        self.running = True
        time.sleep(self.start_delay)

    def stop_bounded(self, seconds):
        self.running = False
        return {'stopped': True}

    def argv(self, manifest, seconds):
        return [sys.executable, str(self.provider), str(self.workspace), str(self.release), self.mode]

    def check_argv(self, check):
        self.commands.append(check['id'])
        return [sys.executable, str(self.release / (check['id'] + '.py')), str(self.workspace)]


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='development-feedback-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        base = self.root / 'base'
        base.mkdir()
        (base / 'value.txt').write_text('initial')
        for args in (['init', '-q'], ['config', 'user.email', 'fixture@example.invalid'],
                     ['config', 'user.name', 'Fixture'], ['add', '.'], ['commit', '-qm', 'base']):
            subprocess.run(['git', '-C', str(base), *args], check=True)
        self.provider = self.root / 'provider.py'
        self.provider.write_text(PROVIDER)
        conditions = []
        for ident, mode in [('control', 'self'), ('improved', 'feedback')]:
            workspace, release = self.root / ident, self.root / (ident + '-public')
            subprocess.run(['git', 'clone', '-q', str(base), str(workspace)], check=True)
            release.mkdir()
            conditions.append({'id': ident, 'mode': mode, 'workspace': str(workspace),
                               'release': str(release), 'container': public.sha(ident.encode())})
        prompt = 'Implement the value requirement.'
        self.config = {'schema_version': 1, 'kind': workflow.KIND, 'task': 'duplicates-v1',
            'image': FakeDocker.image, 'legacy': None, 'capability_seconds': 5, 'observer_seconds': 10,
            'conditions': conditions, 'manifest': {'study_id': 'feedback-fixture', 'scale': 'small',
                'model': 'fake', 'effort': 'fake', 'cli_version': '0.153.0', 'max_seconds': 20,
                'max_sessions': 4, 'max_output_tokens': 100, 'max_snapshot_bytes': 1000000,
                'stop_seconds': 2, 'capture_seconds': 5, 'capture_window_seconds': 2,
                'phases': [{'id': 'phase-1', 'prompt': prompt, 'prompt_sha256': public.sha(prompt.encode()), 'seconds': 10}],
                'admission': {'schema_version': 1, 'kind': 'planning_prior', 'scope': 'fixture',
                    'rationale': 'bounded test', 'owner': 'test', 'update_when': 'fixture changes',
                    'stages': {'phase-1': {'minimum_seconds': .1, 'minimum_output_tokens': 1}}}},
            'public_checks': {'schema_version': 1, 'scope': 'fixture', 'rationale': 'bounded public tests',
                'owner': 'test', 'update_when': 'fixture changes', 'limits_kind': 'cost_cap',
                'max_source_bytes': 100000, 'max_output_bytes': 1024, 'max_feedback_rounds': 1,
                'retry_min_seconds': .1, 'retry_min_output_tokens': 1, 'network_access': True,
                'checks': [self.check('capability', 'capability', "print('capability ready')\n"),
                           self.check('value', 'required', CHECK)], 'phase_check_ids': {'1': ['value']}}}
        self.output = self.root / 'comparison'
        self.transports = {c['id']: FakeDocker(c, self.provider) for c in conditions}
        self.evaluated = []

    def check(self, ident, tier, source, phase=1):
        return {'id': ident, 'tier': tier, 'phase': phase, 'description': ident + ' public instructions',
                'source': source, 'sha256': public.sha(source.encode()), 'seconds': 2,
                'argv': ['python3', '/public-checks/' + ident + '.py', '/workspace']}

    def transport(self, config, row):
        return self.transports[row['id']]

    def seal(self):
        path = self.root / 'config.json'
        path.write_text(json.dumps(self.config))
        return workflow.seal(path, self.output, self.transport)

    def evaluator(self, record, output, row):
        self.assertTrue(all(not t.running for t in self.transports.values()))
        self.evaluated.append(row['condition'])
        passed = (Path(row['source']) / 'value.txt').read_text() == 'good'
        # Hidden feedback is intentionally different and must never enter prompts.
        checks = [{**c, 'status': 'passed' if passed else 'failed', 'detail': 'HIDDEN_ORACLE_SENTINEL'}
                  for c in record['catalog'] if c['phase'] <= row['phase']]
        return {'quality': workflow.legacy.grade({'source_unchanged': True, 'checks': checks}, record['catalog'])}

    def run_pair(self, evaluator=None):
        return workflow.run(self.seal(), self.output, self.transport, evaluator or self.evaluator)

    def test_same_public_information_and_finite_repair_preserve_old_attempt(self):
        result = self.run_pair()
        self.assertIsNone(result['failure'])
        a, b = (result['conditions'][k] for k in ('control', 'improved'))
        self.assertEqual(len(a['attempts']), 1)
        self.assertEqual(len(b['attempts']), 2)
        self.assertEqual(b['feedback_rounds'], 1)
        self.assertEqual(b['output_tokens'], 10)
        self.assertTrue((self.root / 'control/self-checked').exists())
        prompts = [Path(x['directory']) / 'session-00/prompt.private.txt' for x in b['attempts']]
        self.assertNotIn('PUBLIC_VALUE_FAILURE', prompts[0].read_text())
        self.assertIn('PUBLIC_VALUE_FAILURE', prompts[1].read_text())
        for path in prompts:
            self.assertNotIn('HIDDEN_ORACLE_SENTINEL', path.read_text())
        self.assertTrue(Path(b['attempts'][0]['directory'], 'session-00/terminal/workspace.tar').exists())
        self.assertGreater(b['elapsed_seconds'], b['public_check_seconds'])
        self.assertGreater(b['public_check_seconds'], 0)
        self.assertTrue(a['quality_and_budget_passed'])
        self.assertTrue(b['quality_and_budget_passed'])
        public_a = json.loads((self.root / 'control-public/checks.json').read_text())
        public_b = json.loads((self.root / 'improved-public/checks.json').read_text())
        self.assertEqual(public_a, public_b)
        with self.assertRaises(runner.Error):
            workflow.run(workflow.campaign.read(self.output / 'seal.json'), self.output, self.transport)

    def test_failed_common_capability_prevents_both_developers(self):
        self.config['public_checks']['checks'][0] = self.check('capability', 'capability', 'raise SystemExit(1)\n')
        result = self.run_pair()
        self.assertIsNotNone(result['failure'])
        self.assertTrue(all(c['status'] == 'not_started' for c in result['conditions'].values()))
        self.assertFalse(self.evaluated)
        self.assertFalse((self.root / 'control/last-prompt.txt').exists())

    def test_unknown_usage_does_not_start_public_checks_or_retry(self):
        self.transports['improved'].mode = 'unknown'
        result = self.run_pair()
        b = result['conditions']['improved']
        self.assertFalse(b['usage_complete'])
        self.assertEqual(len(b['attempts']), 1)
        self.assertEqual(self.transports['improved'].commands, ['capability'])
        self.assertFalse(b['quality_and_budget_passed'])

    def test_retry_round_limit_does_not_repeat_until_success(self):
        self.transports['improved'].mode = 'always-bad'
        result = self.run_pair()
        b = result['conditions']['improved']
        self.assertEqual(len(b['attempts']), 2)
        self.assertEqual(b['status'], 'halted')
        self.assertFalse(b['quality_and_budget_passed'])

    def test_public_checks_cannot_repair_the_candidate_themselves(self):
        # Make it pass, then change source: this is a check failure, not a repair.
        source = "import sys\nfrom pathlib import Path\n(Path(sys.argv[1])/'value.txt').write_text('good')\n"
        self.config['public_checks']['checks'][1] = self.check('value', 'required', source)
        result = self.run_pair()
        b = result['conditions']['improved']
        self.assertEqual(b['status'], 'interrupted')
        self.assertEqual(b['failure'], 'public_check_mutated_source')
        self.assertEqual(len(b['attempts']), 1)
        self.assertFalse(b['quality_and_budget_passed'])

    def test_future_check_source_and_names_are_not_published(self):
        contract = copy.deepcopy(self.config['public_checks'])
        contract['checks'].append(self.check('future', 'required', "print('FUTURE_SOURCE')\n", 2))
        contract['phase_check_ids']['2'] = ['value', 'future']
        public.validate(contract, 2)
        root = self.root / 'release'
        root.mkdir()
        public.publish(contract, 1, root)
        self.assertFalse((root / 'future.py').exists())
        self.assertNotIn('future', (root / 'checks.json').read_text())
        self.assertNotIn('future', public.instructions(contract, 1))
        public.publish(contract, 2, root)
        self.assertIn('FUTURE_SOURCE', (root / 'future.py').read_text())

    def test_untrusted_commands_and_missing_required_checks_are_rejected(self):
        for change in ('command', 'source', 'selection', 'network'):
            contract = copy.deepcopy(self.config['public_checks'])
            if change == 'command': contract['checks'][1]['argv'] = ['sh', '-c', 'candidate-suggested-command']
            if change == 'source': contract['checks'][1]['source'] += 'changed'
            if change == 'selection': contract['phase_check_ids']['1'] = []
            if change == 'network': contract['network_access'] = 'true'
            with self.subTest(change=change), self.assertRaises(runner.Error):
                public.validate(contract, 1)

    def test_output_capture_is_bounded_and_timeout_cannot_claim_pass(self):
        value = public.bounded([sys.executable, '-c', "print('x'*10000)"], 2, 100, [])
        self.assertEqual(len(value['output']), 100)
        self.assertTrue(value['output_truncated'])
        value = public.bounded([sys.executable, '-c', 'import time; time.sleep(30)'], .1, 100, [])
        self.assertEqual(value['reason'], 'timeout')

    def test_same_policy_declaration_for_developer_and_checker(self):
        transport = object.__new__(public.Docker)
        transport.identity = 'owned-container'
        transport.contract = self.config['public_checks']
        developer = transport.argv(workflow.base_manifest(self.config, 'control'), 5)
        check = transport.check_argv(self.config['public_checks']['checks'][1])
        for value in public.policy_args(transport.contract)[1::2]:
            self.assertIn(value, developer)
            self.assertIn(value, check)
        self.assertNotIn('--sandbox', developer)
        self.assertIn('DEVCONTAINER_CODEX_DANGEROUS_DEFAULT=0', developer)

    def test_token_and_session_caps_prevent_repair(self):
        for cap in ('max_output_tokens', 'max_sessions'):
            with self.subTest(cap=cap):
                config = copy.deepcopy(self.config)
                config['manifest'][cap] = 5 if cap == 'max_output_tokens' else 1
                condition = config['conditions'][1]
                public.publish(config['public_checks'], 1, Path(condition['release']))
                result = workflow.condition_run(config, condition, self.root / cap,
                                                self.transports['improved'], [])
                self.assertEqual(len(result['attempts']), 1)
                self.assertEqual(result['status'], 'halted')
                self.assertFalse(result['submitted_within_budget'])

    def test_startup_can_exhaust_budget_without_starting_provider(self):
        manifest = workflow.base_manifest(self.config, 'improved')
        self.transports['improved'].start_delay = .3
        row = self.config['conditions'][1]
        runner.initialize(manifest, Path(row['workspace']), self.output, self.transports['improved'])
        with runner.locked(self.output):
            result = runner._run_stage(self.output, self.transports['improved'], deadline=time.monotonic() + .1)
        self.assertEqual(len(result['sessions']), 1)
        self.assertEqual(result['sessions'][0]['observation']['stop_reason'], 'enclosing_budget_exhausted')
        self.assertFalse((Path(row['workspace']) / 'last-prompt.txt').exists())
        self.assertFalse(self.transports['improved'].running)
        self.assertGreater(result['sessions'][0]['clock']['preparation_seconds'], .3)

    def test_future_phase_reservations_apply_to_repairs(self):
        config = copy.deepcopy(self.config)
        manifest = config['manifest']
        manifest['phases'].append({'id': 'phase-2'})
        manifest['admission']['stages']['phase-2'] = {'minimum_seconds': 5, 'minimum_output_tokens': 10}
        manifest['max_sessions'] = 2
        state = {'_deadline': time.monotonic() + 10, 'attempts': [1], 'output_tokens': 90,
                 'usage_complete': True, 'feedback_rounds': 0}
        value = workflow.availability(config, state, 1, time.monotonic() + 10, retry=True)
        self.assertFalse(value['admitted'])
        self.assertLessEqual(value['seconds'], 5)
        self.assertEqual(value['output_tokens'], 0)

    def test_check_timeout_stops_writer_and_cannot_trigger_repair(self):
        self.config['public_checks']['checks'][1] = self.check('value', 'required', 'import time; time.sleep(30)\n')
        self.config['public_checks']['checks'][1]['seconds'] = .1
        result = self.run_pair()
        b = result['conditions']['improved']
        self.assertEqual(b['status'], 'interrupted')
        self.assertEqual(b['failure'], 'timeout')
        self.assertEqual(len(b['attempts']), 1)
        self.assertFalse(self.transports['improved'].running)

    def test_changed_initial_source_blocks_development(self):
        record = self.seal()
        (self.root / 'control/value.txt').write_text('tampered')
        result = workflow.run(record, self.output, self.transport, self.evaluator)
        self.assertIsNotNone(result['failure'])
        self.assertFalse(self.evaluated)
        self.assertFalse((self.root / 'control/last-prompt.txt').exists())

    def test_mismatched_environment_cannot_be_sealed(self):
        self.transports['improved'].environment = lambda: {'fixture': 'different cache'}
        with self.assertRaises(runner.Error):
            self.seal()

    def test_changed_environment_after_seal_blocks_development(self):
        record = self.seal()
        self.transports['improved'].environment = lambda: {'fixture': 'changed environment'}
        result = workflow.run(record, self.output, self.transport, self.evaluator)
        self.assertIsNotNone(result['failure'])
        self.assertFalse((self.root / 'control/last-prompt.txt').exists())
        self.assertFalse(self.evaluated)

    def test_three_phases_preserve_dirty_source_and_release_only_current_information(self):
        self.config.update(task='acceptance-v2', legacy=str(self.root / 'base'))
        manifest = self.config['manifest']
        manifest.update(scale='large', max_seconds=60, max_sessions=6)
        contract = self.config['public_checks']
        contract['max_feedback_rounds'] = 3
        for n in (2, 3):
            prompt = f'FUTURE_REQUIREMENT_{n}'
            manifest['phases'].append({'id': f'phase-{n}', 'prompt': prompt,
                'prompt_sha256': public.sha(prompt.encode()), 'seconds': 15})
            manifest['admission']['stages'][f'phase-{n}'] = {'minimum_seconds': .1, 'minimum_output_tokens': 1}
            contract['checks'].append(self.check(f'future-{n}', 'required', "print('released')\n", n))
            contract['phase_check_ids'][str(n)] = ['value'] + [f'future-{i}' for i in range(2, n + 1)]
        result = self.run_pair()
        self.assertIsNone(result['failure'])
        b = result['conditions']['improved']
        self.assertEqual(b['completed_phases'], 3)
        self.assertEqual(len(b['attempts']), 6)
        self.assertTrue(b['quality_and_budget_passed'])
        for attempt in b['attempts']:
            prompt = (Path(attempt['directory']) / 'session-00/prompt.private.txt').read_text()
            for n in range(attempt['phase'] + 1, 4):
                self.assertNotIn(f'FUTURE_REQUIREMENT_{n}', prompt)
                self.assertNotIn(f'future-{n}', prompt)
        self.assertIsNotNone(b['observations'][2]['previous'])


@unittest.skipUnless(os.environ.get('TERMINAL_DEVELOPMENT_IMAGE'), 'set verified image ID for real Docker checks')
class DockerFeedbackTests(unittest.TestCase):
    setUp = FeedbackTests.setUp
    check = FeedbackTests.check
    evaluator = FeedbackTests.evaluator
    transport = FeedbackTests.transport
    seal = FeedbackTests.seal
    run_pair = FeedbackTests.run_pair

    def real_pair(self):
        self.config['image'] = os.environ['TERMINAL_DEVELOPMENT_IMAGE']
        self.config['capability_seconds'] = 20
        self.config['manifest'].update(max_seconds=60, stop_seconds=5, capture_window_seconds=5)
        self.config['manifest']['phases'][0]['seconds'] = 50
        for check in self.config['public_checks']['checks']:
            check['seconds'] = 10
        for row in self.config['conditions']:
            binaries = self.root / ('bin-' + row['id'])
            binaries.mkdir()
            shim = binaries / 'codex'
            shim.write_text('#!/usr/bin/python3\nimport os,sys\n'
                "if sys.argv[1] != 'exec': os.execv('/opt/devcontainer-ai-cli/bin/codex', ['codex', *sys.argv[1:]])\n"
                + PROVIDER.replace('root,release,mode=Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3]',
                    "root,release,mode=Path('/workspace'),Path('/public-checks'),os.environ['FIXTURE_MODE']"))
            shim.chmod(0o755)
            name = 'feedback-test-' + uuid.uuid4().hex
            subprocess.run(['docker', 'create', '--name', name, '--network', 'none', '--privileged',
                '--label', 'dev.agentctl.benchmark=true',
                '--mount', f"type=bind,src={row['workspace']},dst=/workspace",
                '--mount', f"type=bind,src={row['release']},dst=/public-checks,readonly",
                '--mount', f'type=bind,src={binaries},dst=/fake,readonly',
                '-e', 'PATH=/fake:/usr/local/bin:/usr/bin:/bin',
                '--entrypoint', '/usr/bin/sleep', self.config['image'], 'infinity'], capture_output=True, check=True)
            self.addCleanup(lambda n=name: subprocess.run(['docker', 'rm', '-f', n], capture_output=True))
            transport = public.Docker(name, Path(row['workspace']), Path(row['release']), self.config['public_checks'])
            row['container'] = transport.identity
            transport.stop_seconds = 5
            transport.expected_cli_version = self.config['manifest']['cli_version']
            real_argv = transport.argv
            def argv(manifest, seconds, original=real_argv, mode=row['mode']):
                command = original(manifest, seconds)
                command[3:3] = ['-e', 'FIXTURE_MODE=' + mode]
                return command
            transport.argv = argv
            self.transports[row['id']] = transport
        # Legacy fixture evaluator expects a boolean running attribute.
        self.evaluated = []

    def test_real_named_sandbox_readonly_release_and_synthetic_repair(self):
        capability = '''import socket,tempfile
from pathlib import Path
with socket.socket() as s: s.bind(('127.0.0.1',0))
with tempfile.TemporaryDirectory(dir='/workspace') as d: (Path(d)/'probe').write_text('ok')
try: Path('/public-checks/unrequested').write_text('bad')
except OSError: pass
else: raise AssertionError('public release is writable')
try: Path('/home/devuser/outside-workspace-probe').write_text('bad')
except OSError: pass
else: raise AssertionError('outside-workspace write permitted')
print('loopback, workspace write, public readonly and outside denial passed')
'''
        self.config['public_checks']['checks'][0] = self.check('capability', 'capability', capability)
        self.real_pair()
        def evaluate(record, output, row):
            for transport in self.transports.values():
                transport.stopped()
                transport.running = False
            return self.evaluator(record, output, row)
        result = self.run_pair(evaluate)
        self.assertIsNone(result['failure'], json.dumps(result, indent=2))
        for value in result['capabilities'].values():
            self.assertEqual(value['status'], 'passed')
        a, b = (result['conditions'][k] for k in ('control', 'improved'))
        self.assertEqual(len(a['attempts']), 1)
        self.assertEqual(len(b['attempts']), 2)
        self.assertTrue(a['quality_and_budget_passed'])
        self.assertTrue(b['quality_and_budget_passed'])

    def test_real_check_timeout_stops_container(self):
        self.real_pair()
        row = self.config['conditions'][1]
        check = self.check('timeout', 'required', 'import time; time.sleep(30)\n')
        check['seconds'] = .2
        contract = {**self.config['public_checks'], 'checks': [check], 'phase_check_ids': {'1': ['timeout']}}
        public.publish(contract, 1, Path(row['release']))
        result = public.run(contract, ['timeout'], self.transports['improved'], Path(row['workspace']),
                            self.output, time.monotonic() + 20, [])
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['failure'], 'timeout')
        self.assertTrue(result['stopped'])
        self.assertFalse(self.transports['improved'].info()['State']['Running'])


if __name__ == '__main__':
    unittest.main()

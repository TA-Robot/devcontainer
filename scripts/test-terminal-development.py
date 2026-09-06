"""Terminal clock fault matrix: real recorder processes and optional real Docker."""
import copy
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'experiments/development-harness/terminal'
sys.path.insert(0, str(HERE))
import runner
import pair


PROVIDER = '''import json,os,sys,time
from pathlib import Path
root=Path(sys.argv[1]); mode=sys.argv[2]
prompt=sys.stdin.read()
(root/'provider.pid').write_text(str(os.getpid()))
with (root/'work.txt').open('a') as f: f.write('continued\\n')
print(json.dumps({'type':'item.completed','item':{'type':'reasoning','text':'PRIVATE_REASONING_SENTINEL'}}),flush=True)
if mode=='closed-pipes': os.close(1); os.close(2)
if mode in ('hang','closed-pipes'): time.sleep(30)
if mode=='archive-full': (root/'large.txt').write_bytes(b'x'*4096)
if mode=='bad-redaction':
 with (root/'scripts/agentctl_jobs.py').open('a') as f: f.write('\\ndef _redact_log_text(text): return text, 0\\n')
if mode=='late-write':
 time.sleep(.25); (root/'late.txt').write_text('after deadline'); time.sleep(30)
if mode=='late-write-docker':
 deadline=time.monotonic()+20
 while not Path('/fake/allow-late').exists() and time.monotonic()<deadline: time.sleep(.01)
 (root/'late.txt').write_text('after deadline'); time.sleep(30)
if mode!='unknown':
 print(json.dumps({'type':'turn.completed','usage':{'input_tokens':100,'cached_input_tokens':80,'output_tokens':7}}),flush=True)
if mode=='partial-usage': time.sleep(30)
'''


class FakeDocker:
    identity = 'a' * 64
    image = 'sha256:' + 'b' * 64

    def __init__(self, workspace, provider):
        self.workspace, self.provider = workspace, provider
        self.running = False
        self.delay = 0
        self.mode = 'success'
        self.stop_error = False
        self.starts = 0

    def stopped(self):
        if self.running:
            raise ValueError('developer still active')
        return {'stopped': True}

    def start(self):
        self.stopped()
        self.running = True
        self.starts += 1

    def stop_bounded(self, seconds):
        time.sleep(self.delay)
        if self.stop_error:
            raise ValueError('daemon unreachable')
        self.running = False
        return {'stopped': True}

    def argv(self, manifest, seconds):
        return [sys.executable, str(self.provider), str(self.workspace), self.mode]


class TerminalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='terminal-development-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.workspace = self.root / 'workspace'
        self.workspace.mkdir()
        for args in (['init', '-q'], ['config', 'user.email', 'fixture@example.invalid'],
                     ['config', 'user.name', 'Fixture']):
            subprocess.run(['git', '-C', str(self.workspace), *args], check=True)
        (self.workspace / 'base.txt').write_text('base\n')
        subprocess.run(['git', '-C', str(self.workspace), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.workspace), 'commit', '-qm', 'base'], check=True)
        self.provider = self.root / 'provider.py'
        self.provider.write_text(PROVIDER)
        self.output = self.root / 'state'
        self.transport = FakeDocker(self.workspace, self.provider)
        self.manifest = {'schema_version': 2, 'clock': runner.CLOCK, 'study_id': 'terminal-test',
                         'condition': 'control', 'scale': 'small', 'model': 'fake', 'effort': 'fake',
                         'cli_version': 'fake', 'max_seconds': 10, 'max_sessions': 3,
                         'max_output_tokens': 100, 'max_snapshot_bytes': 1000000,
                         'stop_seconds': 2, 'capture_seconds': 5, 'capture_window_seconds': .2,
                         'phases': []}
        self.set_phases(['first requirement'])

    def set_phases(self, prompts):
        self.manifest['phases'] = [{'id': f'phase-{i}', 'prompt': p,
                                    'prompt_sha256': runner.campaign.digest(p.encode()), 'seconds': 3}
                                   for i, p in enumerate(prompts)]
        self.manifest['admission'] = {'schema_version': 1, 'kind': 'planning_prior', 'scope': 'fixture',
            'rationale': 'finite calibration', 'owner': 'test', 'update_when': 'fixture changes',
            'stages': {p['id']: {'minimum_seconds': .05, 'minimum_output_tokens': 1}
                       for p in self.manifest['phases']}}

    def initialize(self):
        return runner.initialize(self.manifest, self.workspace, self.output, self.transport)

    def run_stage(self):
        return runner.run_stage(self.output, self.transport)

    def test_normal_submission_clock_excludes_slow_shutdown(self):
        self.initialize()
        self.transport.delay = .35
        state = self.run_stage()
        session = state['sessions'][0]
        self.assertEqual(state['status'], 'submitted')
        self.assertTrue(runner.assess(state)['submitted_within_budget'])
        clock = session['clock']
        self.assertGreater(clock['shutdown_seconds'], .3)
        self.assertGreater(clock['controller_seconds'], clock['development_seconds'] + .3)
        self.assertFalse(session['capture_window_ok'])
        event = runner.campaign.read(self.output / 'session-00/terminal-event.json')
        self.assertIsNone(event['clock']['shutdown_seconds'])
        self.assertEqual(event['clock']['development_seconds'], clock['development_seconds'])
        self.assertNotIn('PRIVATE_REASONING_SENTINEL', (self.output / 'session-00/events.private.jsonl').read_text())

    def test_stages_preserve_source_and_do_not_release_future_requirements(self):
        self.set_phases(['first', 'UNRELEASED_REQUIREMENT', 'THIRD_REQUIREMENT'])
        self.initialize()
        for i in range(3):
            state = self.run_stage()
            self.assertEqual(state['next_phase'], i + 1)
            prompt = (self.output / f'session-{i:02d}/prompt.private.txt').read_text()
            if i == 0:
                self.assertNotIn('UNRELEASED_REQUIREMENT', prompt)
            if i < 2:
                self.assertNotIn('THIRD_REQUIREMENT', prompt)
        self.assertEqual((self.workspace / 'work.txt').read_text(), 'continued\n' * 3)
        self.assertEqual(runner.assess(state)['output_tokens'], 21)
        self.assertFalse(list(self.output.glob('checkpoint-*')))
        with self.assertRaises(runner.Error):
            self.run_stage()

    def test_closed_pipes_and_timeout_still_stop_writer(self):
        self.manifest['phases'][0]['seconds'] = .2
        self.transport.mode = 'closed-pipes'
        self.initialize()
        state = self.run_stage()
        self.assertFalse(self.transport.running)
        session = state['sessions'][0]
        self.assertEqual(session['kind'], 'cutoff')
        self.assertIsNotNone(session['artifact'])
        self.assertFalse(runner.assess(state)['submitted_within_budget'])
        self.assertLess(session['clock']['controller_seconds'], 3)

    def test_delayed_stop_artifact_is_not_exact_budget_quality(self):
        self.manifest['phases'][0]['seconds'] = .15
        self.transport.mode = 'late-write'
        self.transport.delay = .4
        self.initialize()
        state = self.run_stage()
        self.assertTrue((self.workspace / 'late.txt').exists())
        self.assertFalse(state['sessions'][0]['capture_window_ok'])
        self.assertEqual(state['sessions'][0]['kind'], 'cutoff')

    def test_missing_usage_prevents_further_stages(self):
        self.set_phases(['first', 'future'])
        self.transport.mode = 'unknown'
        self.initialize()
        state = self.run_stage()
        self.assertFalse(runner.assess(state)['admitted'])
        self.assertFalse(runner.assess(state)['usage_complete'])
        self.assertEqual(self.transport.starts, 1)
        self.assertIsNotNone(state['sessions'][0]['artifact'])

    def test_cutoff_retains_known_usage_without_claiming_complete_usage(self):
        self.manifest['phases'][0]['seconds'] = .3
        self.transport.mode = 'partial-usage'
        self.initialize()
        state = self.run_stage()
        self.assertEqual(runner.assess(state)['output_tokens'], 7)
        self.assertFalse(runner.assess(state)['usage_complete'])
        self.assertEqual(state['sessions'][0]['kind'], 'cutoff')

    def test_recorder_sigkill_is_stopped_and_captured_by_supervisor(self):
        self.transport.mode = 'hang'
        self.initialize()
        killed = threading.Event()
        def kill_recorder():
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                state = runner.load(self.output)
                pid = state.get('active', {}).get('recorder_pid')
                if pid and (self.workspace / 'provider.pid').exists():
                    os.kill(pid, signal.SIGKILL)
                    killed.set()
                    return
                time.sleep(.01)
        thread = threading.Thread(target=kill_recorder)
        thread.start()
        try:
            state = self.run_stage()
        finally:
            thread.join(timeout=4)
        self.assertTrue(killed.is_set())
        session = state['sessions'][0]
        self.assertEqual(session['infrastructure_failure'], 'recorder_lost')
        self.assertTrue(self.transport.stopped()['stopped'])
        self.assertIsNotNone(session['artifact'])
        self.assertIsNone(session['clock']['development_seconds'])
        self.assertEqual(runner.assess(state)['reserved_unknown_seconds'], 3)
        self.assertFalse(runner.assess(state)['submitted_within_budget'])

    def test_stop_unconfirmed_never_captures(self):
        self.initialize()
        self.transport.stop_error = True
        with patch.object(runner, 'capture', side_effect=AssertionError('must not capture')):
            state = self.run_stage()
        self.assertEqual(state['sessions'][0]['infrastructure_failure'], 'stop_unconfirmed')
        self.assertIsNone(state['sessions'][0]['artifact'])
        self.assertIsNone(state['sessions'][0]['clock']['stop_confirmed_seconds'])

    def test_controller_term_finishes_stop_capture_and_interruption_record(self):
        self.transport.mode = 'hang'
        self.initialize()
        signalled = threading.Event()
        def interrupt():
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                if runner.load(self.output).get('active', {}).get('recorder_pid'):
                    os.kill(os.getpid(), signal.SIGTERM)
                    signalled.set()
                    return
                time.sleep(.01)
        thread = threading.Thread(target=interrupt)
        thread.start()
        try:
            state = self.run_stage()
        finally:
            thread.join(timeout=4)
        self.assertTrue(signalled.is_set())
        self.assertEqual(state['sessions'][0]['infrastructure_failure'], 'controller_interrupted')
        self.assertTrue(state['sessions'][0]['stop_evidence']['stopped'])
        self.assertIsNotNone(state['sessions'][0]['artifact'])
        self.assertFalse(runner.assess(state)['submitted_within_budget'])

    def test_capture_failure_keeps_submission_event_and_original_state(self):
        self.initialize()
        with patch.object(runner, 'capture', side_effect=runner.Error('incomplete archive')):
            state = self.run_stage()
        self.assertEqual(state['sessions'][0]['infrastructure_failure'], 'archive_failed')
        self.assertEqual(state['status'], 'interrupted')
        self.assertTrue((self.output / 'initial/workspace.tar').is_file())
        self.assertTrue((self.output / 'session-00/terminal-event.json').is_file())

    def test_start_failure_still_stops_and_preserves_source(self):
        self.initialize()
        def fail():
            self.transport.running = True
            raise runner.Error('startup probe failed')
        with patch.object(self.transport, 'start', side_effect=fail):
            state = self.run_stage()
        session = state['sessions'][0]
        self.assertEqual(session['infrastructure_failure'], 'startup_failed')
        self.assertIsNone(session['clock']['development_seconds'])
        self.assertIsNotNone(session['artifact'])
        self.assertTrue(self.transport.stopped()['stopped'])

    def test_stop_api_failure_can_preserve_artifact_only_with_independent_stop_proof(self):
        self.initialize()
        def stop(seconds):
            self.transport.running = False
            return {'stopped': True, 'errors': ['stop_api_error']}
        with patch.object(self.transport, 'stop_bounded', side_effect=stop):
            state = self.run_stage()
        self.assertEqual(state['sessions'][0]['infrastructure_failure'], 'stop_api_error')
        self.assertIsNotNone(state['sessions'][0]['artifact'])
        self.assertFalse(runner.assess(state)['admitted'])

    def test_old_schema_and_clock_rejected(self):
        for changed in ({'schema_version': 1}, {'clock': 'old'}, {'checkpoint_seconds': 1}):
            with self.subTest(changed=changed), self.assertRaises(runner.Error):
                runner.validate({**self.manifest, **changed})

    def prepare_pair(self):
        conditions, transports = [], {}
        for condition in ('control', 'improved'):
            workspace = self.root / condition
            subprocess.run(['git', 'clone', '-q', str(self.workspace), str(workspace)], check=True)
            transport = FakeDocker(workspace, self.provider)
            manifest = copy.deepcopy(self.manifest)
            manifest['condition'] = condition
            state = self.root / (condition + '-state')
            runner.initialize(manifest, workspace, state, transport)
            transports[str(workspace)] = transport
            conditions.append({'id': condition, 'state': str(state)})
        config = {'schema_version': 2, 'clock': runner.CLOCK, 'task': 'duplicates-v1',
                  'conditions': conditions, 'image': FakeDocker.image, 'legacy': None,
                  'observer_seconds': 30, 'observer_slots': 1, 'intervention_fields': []}
        config_path = self.root / 'pair.json'
        config_path.write_text(json.dumps(config))
        output = self.root / 'pair'
        proof = lambda s: transports[s['workspace']].stopped()
        with patch.object(pair.legacy, 'stopped_state', side_effect=proof):
            record = pair.seal(config_path, output)
        return record, output, transports, proof

    def test_pair_grades_quality_and_budget_without_replay(self):
        record, output, transports, proof = self.prepare_pair()
        def evaluator(record, output, row):
            value = {'source_unchanged': True, 'checks': [
                {**c, 'status': 'passed' if row['condition'] == 'improved' else 'failed'}
                for c in record['catalog']]}
            return {'quality': pair.legacy.grade(value, record['catalog']), 'observer_seconds': .01}
        with patch.object(pair.legacy, 'stopped_state', side_effect=proof):
            result = pair.run(record, output, lambda s: transports[s['workspace']], evaluator)
            with self.assertRaises(ValueError):
                pair.run(record, output)
        self.assertFalse(result['conditions']['control']['quality_and_budget_passed'])
        self.assertTrue(result['conditions']['improved']['quality_and_budget_passed'])
        self.assertIsNone(result['speed_ratio'])

    def test_pair_holds_all_state_locks_through_external_evaluation(self):
        record, output, transports, proof = self.prepare_pair()
        attempts = []
        def evaluator(record, output, row):
            other = self.root / 'improved-state'
            with self.assertRaises(BlockingIOError):
                runner.run_stage(other, transports[str(self.root / 'improved')])
            attempts.append(row['condition'])
            return {'quality': pair.legacy.grade({'source_unchanged': True, 'checks': [
                {**c, 'status': 'passed'} for c in record['catalog']]}, record['catalog'])}
        with patch.object(pair.legacy, 'stopped_state', side_effect=proof):
            result = pair.run(record, output, lambda s: transports[s['workspace']], evaluator)
        self.assertEqual(attempts, ['control', 'improved'])
        self.assertTrue(result['automatic_execution_completed'])

    def test_passing_cutoff_artifact_does_not_become_submission(self):
        self.manifest['phases'][0]['seconds'] = .2
        record, output, transports, proof = self.prepare_pair()
        transports[str(self.root / 'control')].mode = 'hang'
        def evaluator(record, output, row):
            return {'quality': pair.legacy.grade({'source_unchanged': True, 'checks': [
                {**c, 'status': 'passed'} for c in record['catalog']]}, record['catalog'])}
        with patch.object(pair.legacy, 'stopped_state', side_effect=proof):
            result = pair.run(record, output, lambda s: transports[s['workspace']], evaluator)
        control = result['conditions']['control']
        self.assertTrue(control['final_quality_accepted'])
        self.assertFalse(control['budget']['submitted_within_budget'])
        self.assertFalse(control['quality_and_budget_passed'])
        self.assertIsNone(result['speed_ratio'])

    def test_evaluator_failure_reports_unknown_and_leaves_next_condition_unstarted(self):
        record, output, transports, proof = self.prepare_pair()
        with patch.object(pair.legacy, 'stopped_state', side_effect=proof):
            result = pair.run(record, output, lambda s: transports[s['workspace']],
                              lambda *args: (_ for _ in ()).throw(ValueError('evaluator failed')))
        self.assertIsNone(result['conditions']['control']['final_quality_accepted'])
        self.assertEqual(result['conditions']['improved']['status'], 'ready')
        self.assertEqual(result['execution'][1]['status'], 'not_started')
        self.assertTrue((output / 'comparison.json').is_file())

    def test_pair_stop_failure_never_evaluates_or_launches_next_condition(self):
        record, output, transports, proof = self.prepare_pair()
        transports[str(self.root / 'control')].stop_error = True
        with patch.object(pair.legacy, 'stopped_state', side_effect=proof):
            result = pair.run(record, output, lambda s: transports[s['workspace']],
                              lambda *args: self.fail('must not evaluate'))
        self.assertEqual(result['execution'][0]['reason'], 'stop_unconfirmed')
        self.assertEqual(transports[str(self.root / 'improved')].starts, 0)


@unittest.skipUnless(os.environ.get('TERMINAL_DEVELOPMENT_IMAGE'), 'set verified image ID for real Docker fault matrix')
class DockerTerminalTests(unittest.TestCase):
    setUp = TerminalTests.setUp
    set_phases = TerminalTests.set_phases
    initialize = TerminalTests.initialize
    run_stage = TerminalTests.run_stage
    def real_transport(self, mode='success', workspace=None):
        workspace = workspace or self.workspace
        binaries = self.root / ('bin-' + uuid.uuid4().hex)
        binaries.mkdir()
        provider = binaries / 'codex'
        provider.write_text('#!/usr/bin/python3\n' + PROVIDER.replace(
            'root=Path(sys.argv[1]); mode=sys.argv[2]', f"root=Path('/workspace'); mode={mode!r}"))
        provider.chmod(0o755)
        name = 'terminal-test-' + uuid.uuid4().hex
        subprocess.run(['docker', 'create', '--name', name, '--network', 'none',
                        '--label', 'dev.agentctl.benchmark=true',
                        '--mount', f'type=bind,src={workspace},dst=/workspace',
                        '--mount', f'type=bind,src={binaries},dst=/fake,readonly',
                        '-e', 'PATH=/fake:/usr/local/bin:/usr/bin:/bin',
                        '--entrypoint', '/usr/bin/sleep', os.environ['TERMINAL_DEVELOPMENT_IMAGE'], 'infinity'],
                       capture_output=True, check=True)
        self.addCleanup(lambda: subprocess.run(['docker', 'rm', '-f', name], capture_output=True))
        transport = runner.Docker(name, workspace)
        transport.fixture_bin = binaries
        return transport

    def test_real_docker_submission_and_cutoff_do_not_pause(self):
        self.transport = self.real_transport('success')
        self.initialize()
        state = self.run_stage()
        self.assertEqual(state['status'], 'submitted')
        self.assertFalse(self.transport.info()['State']['Running'])
        self.assertIsNotNone(state['sessions'][0]['artifact'])

    def test_real_docker_timeout_stops_container_not_only_exec(self):
        self.transport = self.real_transport('hang')
        self.manifest['phases'][0]['seconds'] = .5
        self.initialize()
        state = self.run_stage()
        self.assertEqual(state['sessions'][0]['kind'], 'cutoff')
        self.assertFalse(self.transport.info()['State']['Running'])
        self.assertIsNotNone(state['sessions'][0]['artifact'])

    def test_real_docker_recorder_loss_stops_writer_and_recovers_artifact(self):
        self.transport = self.real_transport('hang')
        TerminalTests.test_recorder_sigkill_is_stopped_and_captured_by_supervisor(self)
        self.assertFalse(self.transport.info()['State']['Running'])

    def test_real_docker_controller_term_stops_and_captures(self):
        self.transport = self.real_transport('hang')
        TerminalTests.test_controller_term_finishes_stop_capture_and_interruption_record(self)
        self.assertFalse(self.transport.info()['State']['Running'])

    def test_real_archive_cap_keeps_partial_archive_out_of_grading(self):
        self.transport = self.real_transport('archive-full')
        self.manifest['max_snapshot_bytes'] = 256
        self.initialize()
        state = self.run_stage()
        session = state['sessions'][0]
        self.assertEqual(session['infrastructure_failure'], 'archive_failed')
        self.assertIsNone(session['artifact'])
        self.assertFalse(self.transport.info()['State']['Running'])

    def test_real_docker_delayed_stop_preserves_late_write_as_cutoff(self):
        self.transport = self.real_transport('late-write-docker')
        self.manifest['phases'][0]['seconds'] = .5
        self.initialize()
        original = self.transport.stop_bounded
        def delayed(seconds):
            (self.transport.fixture_bin / 'allow-late').touch()
            deadline = time.monotonic() + 2
            while not (self.workspace / 'late.txt').exists() and time.monotonic() < deadline:
                time.sleep(.01)
            time.sleep(.25)
            return original(seconds)
        with patch.object(self.transport, 'stop_bounded', side_effect=delayed):
            state = self.run_stage()
        self.assertGreater((self.workspace / 'late.txt').stat().st_mtime_ns,
                           (self.output / 'session-00/stop-request.json').stat().st_mtime_ns)
        self.assertFalse(state['sessions'][0]['capture_window_ok'])
        self.assertIsNotNone(state['sessions'][0]['artifact'])
        self.assertFalse(self.transport.info()['State']['Running'])

    def test_real_docker_stop_unconfirmed_leaves_grading_disabled(self):
        self.transport = self.real_transport('hang')
        self.manifest['phases'][0]['seconds'] = .5
        self.initialize()
        with patch.object(self.transport, 'stop_bounded', side_effect=runner.Error('stop API unavailable')):
            state = self.run_stage()
        self.assertEqual(state['sessions'][0]['infrastructure_failure'], 'stop_unconfirmed')
        self.assertIsNone(state['sessions'][0]['artifact'])
        self.assertTrue(self.transport.info()['State']['Running'])

    def test_real_docker_three_phases_preserve_source(self):
        self.transport = self.real_transport()
        self.set_phases(['first', 'second', 'third'])
        self.initialize()
        for _ in range(3):
            state = self.run_stage()
        self.assertEqual(state['status'], 'submitted')
        self.assertEqual((self.workspace / 'work.txt').read_text(), 'continued\n' * 3)
        self.assertEqual(runner.assess(state)['output_tokens'], 21)

    def test_real_pair_executes_stops_and_grades_both_conditions(self):
        (self.workspace / 'scripts').mkdir()
        for name in ('agentctl_jobs.py', 'agent_contracts.py'):
            shutil.copy2(ROOT / 'scripts' / name, self.workspace / 'scripts' / name)
        subprocess.run(['git', '-C', str(self.workspace), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.workspace), 'commit', '-qm', 'oracle fixture'], check=True)
        conditions = []
        for condition, mode in [('control', 'bad-redaction'), ('improved', 'success')]:
            workspace = self.root / condition
            subprocess.run(['git', 'clone', '-q', str(self.workspace), str(workspace)], check=True)
            transport = self.real_transport(mode, workspace)
            manifest = copy.deepcopy(self.manifest)
            manifest.update(condition=condition, capture_window_seconds=3)
            output = self.root / (condition + '-state')
            runner.initialize(manifest, workspace, output, transport)
            conditions.append({'id': condition, 'state': str(output)})
        config = {'schema_version': 2, 'clock': runner.CLOCK, 'task': 'redaction-v2',
                  'conditions': conditions, 'image': os.environ['TERMINAL_DEVELOPMENT_IMAGE'],
                  'legacy': None, 'observer_seconds': 60, 'observer_slots': 1, 'intervention_fields': []}
        path = self.root / 'pair.json'
        path.write_text(json.dumps(config))
        output = self.root / 'pair'
        record = pair.seal(path, output)
        result = pair.run(record, output)
        self.assertTrue(result['automatic_execution_completed'])
        self.assertFalse(result['conditions']['control']['quality_and_budget_passed'])
        self.assertTrue(result['conditions']['improved']['quality_and_budget_passed'])
        self.assertIsNone(result['speed_ratio'])
        self.assertEqual(len(result['conditions']['improved']['observations'][0]['quality']['checks']), 21)


if __name__ == '__main__':
    unittest.main()

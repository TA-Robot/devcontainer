#!/usr/bin/env python3
"""Provider-free fault tests for the finite development campaign recorder."""
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('campaign', ROOT / 'experiments/development-harness/campaign.py')
campaign = importlib.util.module_from_spec(spec)
spec.loader.exec_module(campaign)


class FakeContainer:
    identity = 'fake-container-identity'
    image = 'fake-image-identity'

    def __init__(self, workspace, provider):
        self.workspace = workspace
        self.provider = provider
        self.stopped = True
        self.pid = None
        self.mode = 'success'

    def start(self):
        if not self.stopped:
            raise campaign.CampaignError('duplicate start')
        self.stopped = False

    def info(self):
        return {'State': {'Running': not self.stopped}}

    def stop(self):
        marker = self.workspace / 'provider.pid'
        if marker.exists() and not self.stopped:
            try:
                os.killpg(int(marker.read_text()), signal.SIGTERM)
            except ProcessLookupError:
                pass
        self.stopped = True

    def checkpoint(self, workspace, destination, cap):
        return campaign.snapshot(workspace, destination, cap)

    def argv(self, manifest, seconds):
        return [sys.executable, str(self.provider), str(self.workspace), self.mode]


PROVIDER = '''import json,os,sys,time
from pathlib import Path
root=Path(sys.argv[1]); mode=sys.argv[2]
prompt=sys.stdin.read()
(root/'provider.pid').write_text(str(os.getpid()))
with (root/'work.txt').open('a') as f: f.write('continued\\n')
print(json.dumps({'type':'item.completed','item':{'type':'reasoning','text':'PRIVATE_REASONING_SENTINEL'}}),flush=True)
print(json.dumps({'type':'item.completed','item':{'type':'command_execution','command':'test-command','exit_code':0}}),flush=True)
if mode=='hang': time.sleep(30)
if mode=='closed-pipes':
    os.close(1); os.close(2); time.sleep(30)
if mode=='unknown': sys.exit(0)
print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'public completion'}}),flush=True)
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':100,'cached_input_tokens':80,'output_tokens':7}}),flush=True)
'''


class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='development-campaign-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / 'workspace'
        self.workspace.mkdir()
        self.output = self.root / 'evidence'
        self.provider = self.root / 'provider.py'
        self.provider.write_text(PROVIDER)
        for args in (['init', '-q'], ['config', 'user.email', 'test@example.invalid'],
                     ['config', 'user.name', 'Test']):
            subprocess.run(['git', '-C', str(self.workspace), *args], check=True)
        (self.workspace / 'base.txt').write_text('base\n')
        subprocess.run(['git', '-C', str(self.workspace), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.workspace), 'commit', '-qm', 'base'], check=True)
        self.transport = FakeContainer(self.workspace, self.provider)
        self.addCleanup(self.transport.stop)
        self.manifest = {'schema_version': 1, 'study_id': 'test', 'condition': 'control',
                         'scale': 'large', 'model': 'test-model', 'effort': 'test', 'cli_version': 'test',
                         'max_seconds': 30, 'max_sessions': 3, 'max_output_tokens': 50,
                         'checkpoint_seconds': 10, 'max_snapshot_bytes': 1_000_000,
                         'phases': []}
        for number, prompt in enumerate(('initial requirement', 'UNRELEASED_REQUIREMENT')):
            self.manifest['phases'].append({'id': f'phase-{number}', 'prompt': prompt,
                                           'prompt_sha256': campaign.digest(prompt.encode()), 'seconds': 10})

    def initialize(self):
        return campaign.initialize(self.manifest, self.workspace, self.output, self.transport)

    def test_execution_policy_requires_boolean_opt_in(self):
        for name in ('command_network_access', 'temporary_docker_config'):
            for value in ('false', 'true', 1, None):
                with self.subTest(name=name, value=value):
                    manifest = {**self.manifest, name: value}
                    with self.assertRaisesRegex(campaign.CampaignError, 'explicit boolean'):
                        campaign.validate(manifest)

    def test_network_setting_does_not_remove_filesystem_sandbox_or_enable_agents(self):
        transport = object.__new__(campaign.Docker)
        transport.identity = 'owned-container'
        for enabled in (False, True):
            command = transport.argv({**self.manifest, 'command_network_access': enabled,
                                      'temporary_docker_config': True}, 10)
            self.assertEqual(command[command.index('--sandbox') + 1], 'workspace-write')
            self.assertIn('sandbox_workspace_write.network_access=' + str(enabled).lower(), command)
            self.assertIn('DOCKER_CONFIG=/tmp/development-harness-docker', command)
            self.assertIn('approval_policy="never"', command)
            self.assertIn('agents.enabled=false', command)
            self.assertNotIn('--dangerously-bypass-approvals-and-sandbox', command)
        legacy = transport.argv(self.manifest, 10)
        self.assertFalse(any('network_access=' in arg or 'DOCKER_CONFIG=' in arg for arg in legacy))

    def test_stages_preserve_source_and_accumulate_usage_without_leaking_future(self):
        self.initialize()
        first = campaign.run_stage(self.output, self.transport)
        self.assertEqual(first['next_phase'], 1)
        self.assertEqual(first['output_tokens'], 7)
        self.assertIsNone(first['task_accepted'])
        prompt = (self.output / 'session-00/prompt.private.txt').read_text()
        self.assertNotIn('UNRELEASED_REQUIREMENT', prompt)
        second = campaign.run_stage(self.output, self.transport)
        self.assertEqual(second['status'], 'submitted')
        self.assertEqual(second['output_tokens'], 14)
        self.assertGreater(second['total_seconds'], first['total_seconds'])
        self.assertEqual((self.workspace / 'work.txt').read_text(), 'continued\ncontinued\n')
        prompt = (self.output / 'session-01/prompt.private.txt').read_text()
        self.assertIn('initial requirement', prompt)
        self.assertIn('UNRELEASED_REQUIREMENT', prompt)
        records = (self.output / 'session-00/events.private.jsonl').read_text()
        self.assertIn('public completion', records)
        self.assertNotIn('PRIVATE_REASONING_SENTINEL', records)
        self.assertTrue(self.transport.stopped)
        with self.assertRaises(campaign.CampaignError):
            campaign.run_stage(self.output, self.transport)

    def test_timeout_stops_owned_process_and_preserves_partial_source(self):
        self.manifest['phases'][0]['seconds'] = 0.3
        self.manifest['checkpoint_seconds'] = 0.1
        self.transport.mode = 'hang'
        self.initialize()
        state = campaign.run_stage(self.output, self.transport)
        observation = state['sessions'][0]['observation']
        self.assertEqual(observation['stop_reason'], 'wall_cap')
        self.assertLess(observation['wall_seconds'], 5)
        self.assertTrue(self.transport.stopped)
        self.assertEqual(state['next_phase'], 0)
        self.assertFalse(state['usage_complete'])
        self.assertTrue(state['checkpoints'])
        self.assertTrue((self.output / 'session-00/terminal/workspace.tar').is_file())
        with self.assertRaises(campaign.CampaignError):
            campaign.run_stage(self.output, self.transport)

    def test_unknown_usage_does_not_become_zero_cost(self):
        self.transport.mode = 'unknown'
        self.initialize()
        state = campaign.run_stage(self.output, self.transport)
        self.assertFalse(state['usage_complete'])
        with self.assertRaisesRegex(campaign.CampaignError, 'usage is unknown'):
            campaign.run_stage(self.output, self.transport)

    def test_session_admission_enforces_accumulated_cap(self):
        self.manifest['max_output_tokens'] = 7
        self.initialize()
        state = campaign.run_stage(self.output, self.transport)
        self.assertEqual(state['output_tokens'], 7)
        with self.assertRaisesRegex(campaign.CampaignError, 'cap reached'):
            campaign.run_stage(self.output, self.transport)

    def test_running_marker_prevents_duplicate_launch(self):
        state = self.initialize()
        state['status'] = 'running'
        campaign.save(self.output / 'state.json', state)
        with self.assertRaisesRegex(campaign.CampaignError, 'duplicate'):
            campaign.run_stage(self.output, self.transport)
        self.assertFalse((self.workspace / 'work.txt').exists())

    def test_snapshot_contains_dirty_ignored_and_empty_paths_without_following_links(self):
        self.initialize()
        (self.workspace / 'base.txt').write_text('edited\n')
        (self.workspace / '.gitignore').write_text('ignored\n')
        (self.workspace / 'ignored').write_text('persistent ignored state')
        (self.workspace / 'empty').mkdir()
        secret = self.root / 'outside-private'
        secret.write_text('MUST_NOT_BE_COPIED')
        (self.workspace / 'external-link').symlink_to(secret)
        destination = self.output / 'manual'
        campaign.snapshot(self.workspace, destination, 1_000_000)
        with tarfile.open(destination / 'workspace.tar') as archive:
            self.assertEqual(archive.extractfile('base.txt').read(), b'edited\n')
            self.assertEqual(archive.extractfile('ignored').read(), b'persistent ignored state')
            self.assertTrue(archive.getmember('external-link').issym())
            self.assertTrue(archive.getmember('empty').isdir())
        self.assertNotIn(b'MUST_NOT_BE_COPIED', (destination / 'workspace.tar').read_bytes())
        self.assertTrue((destination / 'history.bundle').exists())
        self.assertIn('+edited', (destination / 'changes.patch').read_text())

    def test_invalid_limits_and_prompt_mutation_are_rejected(self):
        for value in (0, -1, True, float('nan'), float('inf')):
            with self.subTest(value=value):
                changed = {**self.manifest, 'max_seconds': value}
                with self.assertRaises(campaign.CampaignError):
                    campaign.validate(changed)
        self.manifest['phases'][0]['prompt'] = 'changed after digest'
        with self.assertRaises(campaign.CampaignError):
            campaign.validate(self.manifest)

    def test_evidence_must_be_outside_workspace(self):
        with self.assertRaisesRegex(campaign.CampaignError, 'disjoint'):
            campaign.initialize(self.manifest, self.workspace, self.workspace / 'evidence', self.transport)

    def test_checkpoint_failure_stops_execution_and_marks_interruption(self):
        self.manifest['checkpoint_seconds'] = 0.05
        self.transport.mode = 'hang'
        self.initialize()
        original = self.transport.checkpoint
        self.transport.checkpoint = lambda *args: (_ for _ in ()).throw(campaign.CampaignError('snapshot failed'))
        with self.assertRaisesRegex(campaign.CampaignError, 'snapshot failed'):
            campaign.run_stage(self.output, self.transport)
        self.assertTrue(self.transport.stopped)
        self.assertEqual(campaign.read(self.output / 'state.json')['status'], 'interrupted')
        self.transport.checkpoint = original

    def test_closed_pipes_do_not_disable_deadline(self):
        self.manifest['phases'][0]['seconds'] = 0.3
        self.transport.mode = 'closed-pipes'
        self.initialize()
        state = campaign.run_stage(self.output, self.transport)
        observation = state['sessions'][0]['observation']
        self.assertEqual(observation['stop_reason'], 'wall_cap')
        self.assertLess(observation['wall_seconds'], 5)

    def test_recovery_requires_verified_stop_and_never_resets_budget(self):
        state = self.initialize()
        (self.output / 'session-00').mkdir()
        state['status'] = 'running'
        state['total_seconds'] = 2
        state['active'] = {'session': 'session-00', 'reserved_seconds': 10}
        campaign.save(self.output / 'state.json', state)
        self.transport.stopped = False
        with self.assertRaisesRegex(campaign.CampaignError, 'verified stopped'):
            campaign.recover(self.output, self.transport)
        self.transport.stop()
        recovered = campaign.recover(self.output, self.transport)
        self.assertEqual(recovered['total_seconds'], 12)
        self.assertEqual(recovered['status'], 'needs_review')
        self.assertFalse(recovered['usage_complete'])
        self.assertIsNone(recovered['task_accepted'])
        with self.assertRaises(campaign.CampaignError):
            campaign.run_stage(self.output, self.transport)


@unittest.skipUnless(os.environ.get('DEVELOPMENT_CAMPAIGN_IMAGE'), 'set DEVELOPMENT_CAMPAIGN_IMAGE for real Docker transport smoke')
class DockerCampaignTests(unittest.TestCase):
    # Use the same behavioral tests only for the injected local transport above;
    # this one test covers real inspect/start/exec/pause/stop and GNU timeout.
    setUp = CampaignTests.setUp
    initialize = CampaignTests.initialize

    def test_real_docker_transport(self):
        fake_bin = self.root / 'bin'
        fake_bin.mkdir()
        executable = fake_bin / 'codex'
        executable.write_text('#!/usr/bin/python3\n' + PROVIDER.replace(
            "root=Path(sys.argv[1]); mode=sys.argv[2]", "root=Path('/workspace'); mode='success'"))
        executable.chmod(0o755)
        name = 'campaign-test-' + str(os.getpid())
        subprocess.run(['docker', 'create', '--name', name, '--network', 'none',
                        '--label', 'dev.agentctl.benchmark=true',
                        '--mount', f'type=bind,src={self.workspace},dst=/workspace',
                        '--mount', f'type=bind,src={fake_bin},dst=/fake,readonly',
                        '--env', 'PATH=/fake:/usr/local/bin:/usr/bin:/bin',
                        '--entrypoint', '/usr/bin/sleep', os.environ['DEVELOPMENT_CAMPAIGN_IMAGE'],
                        'infinity'], check=True, capture_output=True)
        self.addCleanup(lambda: subprocess.run(['docker', 'rm', '-f', name], capture_output=True))
        self.transport = campaign.Docker(name, self.workspace)
        self.manifest['checkpoint_seconds'] = 0.01
        self.initialize()
        result = campaign.run_stage(self.output, self.transport)
        self.assertEqual(result['next_phase'], 1)
        self.assertEqual(result['output_tokens'], 7)
        self.assertFalse(self.transport.info()['State']['Running'])
        self.assertTrue(result['checkpoints'])


if __name__ == '__main__':
    unittest.main()

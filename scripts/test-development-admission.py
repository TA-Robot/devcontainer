"""Exercise prospective admission with real subprocess usage and immutable history."""
import copy
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load('admission', ROOT / 'experiments/development-harness/continuation/admission.py')
fixtures = load('campaign_test_fixtures', ROOT / 'scripts/test-development-campaign.py')


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.CampaignTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.output = self.fixture.output
        self.manifest = self.fixture.manifest
        self.manifest['admission'] = {
            'schema_version': 1, 'kind': 'planning_prior', 'scope': 'test campaign',
            'rationale': 'retain room for later requirements', 'owner': 'test owner',
            'update_when': 'prior does not predict stage needs',
            'stages': {p['id']: {'minimum_seconds': 1, 'minimum_output_tokens': 6}
                       for p in self.manifest['phases']}}

    def initialize(self):
        return self.fixture.initialize()

    def test_complete_two_stage_work_retains_cumulative_usage_and_quality_unknown(self):
        self.initialize()
        first = gate.run(self.output, lambda _: self.fixture.transport)
        self.assertTrue(first['admitted'])
        self.assertTrue(first['stage_started'])
        self.assertEqual(first['remaining']['output_tokens'], 43)
        final = gate.run(self.output, lambda _: self.fixture.transport)
        self.assertFalse(final['admitted'])
        self.assertTrue(final['submitted_within_observed_budget'])
        self.assertIsNone(final['quality_accepted'])
        self.assertIsNone(final['container_stopped'])
        factory = Mock(side_effect=AssertionError('must not construct transport'))
        gate.run(self.output, factory)
        factory.assert_not_called()
        self.assertEqual(len(list(self.output.glob('session-*'))), 2)

    def test_final_usage_overrun_is_denied_without_replacement_or_state_rewrite(self):
        self.fixture.provider.write_text(fixtures.PROVIDER.replace("'output_tokens':7", "'output_tokens':75"))
        self.initialize()
        result = gate.run(self.output, lambda _: self.fixture.transport)
        self.assertIn('output_tokens', result['observed_budget_exceeded'])
        self.assertFalse(result['submitted_within_observed_budget'])
        before = (self.output / 'state.json').read_bytes()
        factory = Mock()
        denied = gate.run(self.output, factory)
        self.assertFalse(denied['stage_started'])
        factory.assert_not_called()
        self.assertIn('observed_budget_exceeded', denied['reasons'])
        self.assertEqual(before, (self.output / 'state.json').read_bytes())
        self.assertEqual(len(list(self.output.glob('session-*'))), 1)

    def test_future_stage_reserve_denies_small_remainder(self):
        self.manifest['max_output_tokens'] = 20
        self.manifest['admission']['stages']['phase-1']['minimum_output_tokens'] = 14
        self.initialize()
        decision = gate.run(self.output, lambda _: self.fixture.transport)
        self.assertEqual(decision['remaining']['output_tokens'], 13)
        self.assertIn('remaining_stage_minimums_unavailable', decision['reasons'])
        self.assertFalse(decision['admitted'])

    def test_unknown_usage_and_active_session_deny_before_docker(self):
        self.fixture.transport.mode = 'unknown'
        self.initialize()
        decision = gate.run(self.output, lambda _: self.fixture.transport)
        self.assertIn('usage_unknown', decision['reasons'])
        state = gate.campaign.read(self.output / 'state.json')
        state['active'] = {'session': 'owned-elsewhere'}
        gate.campaign.save(self.output / 'state.json', state)
        factory = Mock()
        self.assertIn('active_session_requires_ownership_review', gate.run(self.output, factory)['reasons'])
        factory.assert_not_called()

    def test_policy_and_totals_cannot_be_rewritten_to_reset_budget(self):
        original = self.initialize()
        changed = copy.deepcopy(original)
        changed['manifest']['admission']['stages']['phase-1']['minimum_output_tokens'] = 1
        with self.assertRaisesRegex(gate.campaign.CampaignError, 'manifest changed'):
            gate.assess(changed)
        changed = copy.deepcopy(original)
        changed['output_tokens'] = 1
        with self.assertRaisesRegex(gate.campaign.CampaignError, 'cumulative'):
            gate.assess(changed)
        changed = copy.deepcopy(original)
        changed['next_phase'] = 1
        with self.assertRaisesRegex(gate.campaign.CampaignError, 'completed session'):
            gate.assess(changed)
        for field, value in [('minimum_seconds', True), ('minimum_output_tokens', 1.5),
                             ('minimum_seconds', 11)]:
            manifest = copy.deepcopy(self.manifest)
            manifest['admission']['stages']['phase-0'][field] = value
            with self.assertRaises(gate.campaign.CampaignError):
                gate.policy_for(manifest)

    def test_legacy_state_inspection_does_not_authorize_new_run(self):
        del self.manifest['admission']
        state = self.initialize()
        self.assertIn('prospective_admission_policy_absent', gate.assess(state)['reasons'])
        before = (self.output / 'state.json').read_bytes()
        factory = Mock()
        gate.run(self.output, factory)
        factory.assert_not_called()
        self.assertEqual(before, (self.output / 'state.json').read_bytes())

    def test_same_lock_rejects_concurrent_launcher(self):
        self.initialize()
        with (self.output / 'campaign.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            factory = Mock()
            with self.assertRaises(BlockingIOError):
                gate.run(self.output, factory)
            factory.assert_not_called()


@unittest.skipUnless(os.environ.get('DEVELOPMENT_CAMPAIGN_IMAGE'), 'set image for real Docker admission smoke')
class DockerAdmissionTests(unittest.TestCase):
    setUp = AdmissionTests.setUp
    initialize = AdmissionTests.initialize

    def test_real_container_records_final_overrun_and_stops(self):
        f = self.fixture
        fake_bin = f.root / 'bin'
        fake_bin.mkdir()
        executable = fake_bin / 'codex'
        executable.write_text('#!/usr/bin/python3\n' + fixtures.PROVIDER.replace(
            "root=Path(sys.argv[1]); mode=sys.argv[2]", "root=Path('/workspace'); mode='success'"))
        executable.chmod(0o755)
        name = 'admission-test-' + str(os.getpid())
        subprocess.run(['docker', 'create', '--name', name, '--network', 'none',
                        '--label', 'dev.agentctl.benchmark=true',
                        '--mount', f'type=bind,src={f.workspace},dst=/workspace',
                        '--mount', f'type=bind,src={fake_bin},dst=/fake,readonly',
                        '--env', 'PATH=/fake:/usr/local/bin:/usr/bin:/bin',
                        '--entrypoint', '/usr/bin/sleep', os.environ['DEVELOPMENT_CAMPAIGN_IMAGE'],
                        'infinity'], check=True, capture_output=True)
        self.addCleanup(lambda: subprocess.run(['docker', 'rm', '-f', name], capture_output=True))
        f.transport = gate.campaign.Docker(name, f.workspace)
        self.manifest['max_output_tokens'] = 13
        self.initialize()
        self.assertTrue(gate.run(self.output, lambda _: f.transport)['admitted'])
        final = gate.run(self.output, lambda _: f.transport)
        self.assertEqual(final['remaining']['output_tokens'], -1)
        self.assertFalse(final['submitted_within_observed_budget'])
        self.assertFalse(f.transport.info()['State']['Running'])
        factory = Mock()
        gate.run(self.output, factory)
        factory.assert_not_called()


if __name__ == '__main__':
    unittest.main()

"""Calibration: missing evidence, bogus success, unequal inputs and archive escapes."""
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('automatic_compare', ROOT / 'experiments/development-harness/automatic/compare.py')
compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare)
spec = importlib.util.spec_from_file_location('campaign_fixture', ROOT / 'scripts/test-development-campaign.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


class AutomaticComparisonTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.CampaignTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.expected = [{'name': 'real-command', 'phase': 1, 'dimension': 'execution'}]

    def value(self, status='passed'):
        return {'source_unchanged': True, 'accepted': True,
                'checks': [{**self.expected[0], 'status': status}]}

    def test_self_declared_success_cannot_override_failed_missing_or_unknown_evidence(self):
        self.assertFalse(compare.grade(self.value('failed'), self.expected)['accepted'])
        self.assertIsNone(compare.grade(self.value('unknown'), self.expected)['accepted'])
        self.assertIsNone(compare.grade({'source_unchanged': True, 'accepted': True, 'checks': []}, self.expected)['accepted'])
        self.assertIsNone(compare.grade(None, self.expected)['accepted'])
        value = self.value()
        value['checks'] *= 2
        self.assertIsNone(compare.grade(value, self.expected)['accepted'])
        value = self.value()
        value['checks'][0]['phase'] = 2
        self.assertIsNone(compare.grade(value, self.expected)['accepted'])

    def test_source_mutation_disqualifies_all_pass_claim(self):
        value = self.value()
        value['source_unchanged'] = False
        self.assertIsNone(compare.grade(value, self.expected)['accepted'])

    def pair(self):
        self.fixture.manifest['scale'] = 'small'
        self.fixture.manifest['phases'] = self.fixture.manifest['phases'][:1]
        state = self.fixture.initialize()
        state = fixtures.campaign.run_stage(self.fixture.output, self.fixture.transport)
        states = [copy.deepcopy(state), copy.deepcopy(state)]
        config = {'conditions': [{'id': 'control'}, {'id': 'improved'}], 'task': 'redaction-v2', 'mode': 'retrospective'}
        rows = [{'condition': name, 'kind': 'terminal', 'phase': 1, 'seconds': state['total_seconds'],
                 'quality': compare.grade(self.value(), self.expected)} for name in ('control', 'improved')]
        return config, states, rows

    def test_speed_requires_both_quality_and_budget_not_only_fast_exit(self):
        config, states, rows = self.pair()
        result = compare.summarize(config, states, rows, self.expected)
        self.assertAlmostEqual(result['speed_ratio'], 1)
        rows[1]['quality'] = compare.grade(self.value('failed'), self.expected)
        self.assertIsNone(compare.summarize(config, states, rows, self.expected)['speed_ratio'])
        rows[1]['quality'] = compare.grade(self.value(), self.expected)
        for state in states:
            state['manifest']['max_output_tokens'] = 6
            state['manifest_sha256'] = fixtures.campaign.digest(json.dumps(
                state['manifest'], sort_keys=True, ensure_ascii=False, allow_nan=False).encode())
        result = compare.summarize(config, states, rows, self.expected)
        self.assertIsNone(result['speed_ratio'])
        self.assertFalse(result['conditions']['control']['quality_and_budget_passed'])

    def test_common_phase_does_not_inherit_unknown_future_requirements(self):
        config, states, rows = self.pair()
        catalog = self.expected + [{'name': 'future', 'phase': 2, 'dimension': 'migration'}]
        rows[0].update(kind='checkpoint', requested_seconds=10)
        rows[1].update(kind='checkpoint', requested_seconds=10, phase=2)
        rows[1]['quality'] = compare.grade({'source_unchanged': True, 'checks': [
            {**self.expected[0], 'status': 'passed'}, {**catalog[1], 'status': 'unknown'}]}, catalog)
        result = compare.summarize(config, states, rows, catalog)
        common = result['common_time_quality'][0]
        self.assertEqual(common['common_phase'], 1)
        self.assertTrue(common['conditions']['improved']['quality']['accepted'])

    def test_artifact_hash_and_path_escape_rejected(self):
        root = self.fixture.root
        archive = root / 'bad.tar'
        with tarfile.open(archive, 'w') as stream:
            member = tarfile.TarInfo('../escaped');member.size = 4
            stream.addfile(member, io.BytesIO(b'evil'))
        with self.assertRaises(ValueError):
            compare.extract(archive, '0' * 64, root / 'wrong-hash', 100)
        with self.assertRaises(tarfile.FilterError):
            compare.extract(archive, compare.sha(archive), root / 'escape', 100)
        self.assertFalse((root / 'escaped').exists())

    def test_catalog_is_nonempty_and_unique_for_each_scale(self):
        for task, count in [('redaction-v2', 21), ('acceptance-v2', 44)]:
            catalog = compare.observer.catalog(task)
            self.assertEqual(len(catalog), count)
            self.assertEqual(len({x['name'] for x in catalog}), count)

    def test_actual_container_stop_required_and_daemon_failure_is_not_absence(self):
        state = {'container_id': 'c' * 64, 'image': 'sha256:' + 'd' * 64}
        info = {'Id': state['container_id'], 'Image': state['image'], 'State': {'Running': True}}
        with patch.object(compare.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, json.dumps([info]), '')):
            with self.assertRaisesRegex(ValueError, 'still active'):
                compare.stopped_state(state)
        with patch.object(compare.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'Cannot connect to Docker')):
            with self.assertRaisesRegex(ValueError, 'unavailable'):
                compare.stopped_state(state)
        with patch.object(compare.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'No such object')):
            self.assertTrue(compare.stopped_state(state)['removed'])

    def test_sealed_evaluator_change_is_rejected(self):
        source = self.fixture.root / 'observer.py'
        source.write_text('original')
        record = {'code_sha256': {str(source): compare.sha(source)},
                  'config': {'conditions': []}, 'legacy_hash': None}
        compare.verify(record)
        source.write_text('changed criterion')
        with self.assertRaisesRegex(ValueError, 'changed'):
            compare.verify(record)

    def test_three_stages_release_automatically_and_unknown_usage_stops_one_condition(self):
        root = self.fixture.root
        conditions, transports = [], {}
        for condition in ('control', 'improved'):
            workspace = root / condition
            subprocess.run(['git', 'clone', '-q', str(self.fixture.workspace), str(workspace)], check=True)
            transport = fixtures.FakeContainer(workspace, self.fixture.provider)
            self.addCleanup(transport.stop)
            if condition == 'control':
                transport.mode = 'unknown'
            transports[str(workspace)] = transport
            manifest = copy.deepcopy(self.fixture.manifest)
            manifest['condition'] = condition
            prompt = 'THIRD_STAGE_ONLY'
            manifest['phases'].append({'id': 'phase-2', 'prompt': prompt,
                                       'prompt_sha256': compare.campaign.digest(prompt.encode()), 'seconds': 10})
            manifest['admission'] = {'schema_version': 1, 'kind': 'planning_prior', 'scope': 'test',
                                     'rationale': 'finite stages', 'owner': 'test', 'update_when': 'fixture changes',
                                     'stages': {p['id']: {'minimum_seconds': 1, 'minimum_output_tokens': 1}
                                                for p in manifest['phases']}}
            state = root / (condition + '-state')
            compare.campaign.initialize(manifest, workspace, state, transport)
            conditions.append({'id': condition, 'state': str(state)})
        config = {'schema_version': 1, 'mode': 'prospective', 'task': 'acceptance-v2',
                  'conditions': conditions, 'image': 'sha256:' + 'a' * 64, 'legacy': str(self.fixture.workspace),
                  'include_checkpoints': True, 'observer_seconds': 60, 'observer_slots': 1,
                  'intervention_fields': []}
        path = root / 'config.json';path.write_text(json.dumps(config))
        output = root / 'pair'
        record = compare.seal(path, output)
        with patch.object(compare.campaign, 'Docker', side_effect=lambda identity, workspace, expected: transports[str(workspace)]):
            compare.execute_all(record, output)
        control = compare.campaign.read(root / 'control-state/state.json')
        improved = compare.campaign.read(root / 'improved-state/state.json')
        self.assertEqual(len(control['sessions']), 1)
        self.assertFalse(control['usage_complete'])
        self.assertEqual(improved['next_phase'], 3)
        prompts = [(root / f'improved-state/session-{n:02d}/prompt.private.txt').read_text() for n in range(3)]
        self.assertNotIn('THIRD_STAGE_ONLY', prompts[0])
        self.assertNotIn('THIRD_STAGE_ONLY', prompts[1])
        self.assertIn('THIRD_STAGE_ONLY', prompts[2])


@unittest.skipUnless(os.environ.get('AUTOMATIC_COMPARISON_IMAGE'), 'set pinned image for automated pair integration')
class DockerAutomaticPairTests(unittest.TestCase):
    def test_seal_develop_both_conditions_and_grade_without_human_decisions(self):
        with tempfile.TemporaryDirectory(prefix='automatic-pair-test-') as temporary:
            root = Path(temporary)
            base = root / 'base'
            (base / 'scripts').mkdir(parents=True)
            for name in ('agentctl_jobs.py', 'agent_contracts.py'):
                shutil.copy2(ROOT / 'scripts' / name, base / 'scripts' / name)
            for args in (['init', '-q'], ['config', 'user.name', 'Fixture'],
                         ['config', 'user.email', 'fixture@example.invalid'], ['add', '.'], ['commit', '-qm', 'base']):
                subprocess.run(['git', '-C', str(base), *args], check=True)
            binaries = root / 'bin'
            binaries.mkdir()
            provider = binaries / 'codex'
            provider.write_text(
                '#!/usr/bin/python3\nimport json,os,sys\nfrom pathlib import Path\nsys.stdin.read()\n'
                'if os.environ["FIXTURE_CONDITION"] == "control":\n'
                ' with Path("/workspace/scripts/agentctl_jobs.py").open("a") as f:\n'
                '  f.write("\\ndef _redact_log_text(text): return text, 0\\n")\n'
                'print(json.dumps({"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":5}}))\n')
            provider.chmod(0o755)
            image = os.environ['AUTOMATIC_COMPARISON_IMAGE']
            conditions, containers = [], []
            try:
                for condition in ('control', 'improved'):
                    workspace = root / condition
                    subprocess.run(['git', 'clone', '-q', str(base), str(workspace)], check=True)
                    name = 'automatic-pair-test-' + uuid.uuid4().hex
                    subprocess.run(['docker', 'create', '--name', name, '--network', 'none',
                                    '--label', 'dev.agentctl.benchmark=true',
                                    '--mount', f'type=bind,src={workspace},dst=/workspace',
                                    '--mount', f'type=bind,src={binaries},dst=/fake,readonly',
                                    '-e', 'PATH=/fake:/usr/local/bin:/usr/bin:/bin',
                                    '-e', 'FIXTURE_CONDITION=' + condition,
                                    '--entrypoint', '/usr/bin/sleep', image, 'infinity'],
                                   check=True, capture_output=True)
                    containers.append(name)
                    prompt = 'Run the synthetic comparison fixture.'
                    manifest = {'schema_version': 1, 'study_id': 'automatic-fixture', 'condition': condition,
                                'scale': 'small', 'model': 'fake', 'effort': 'fake', 'cli_version': 'fake',
                                'max_seconds': 30, 'max_sessions': 1, 'max_output_tokens': 100,
                                'checkpoint_seconds': 10, 'max_snapshot_bytes': 1000000,
                                'phases': [{'id': 'phase-1', 'prompt': prompt,
                                            'prompt_sha256': compare.campaign.digest(prompt.encode()), 'seconds': 30}],
                                'admission': {'schema_version': 1, 'kind': 'planning_prior', 'scope': 'fixture',
                                              'rationale': 'finite calibration', 'owner': 'test', 'update_when': 'fixture changes',
                                              'stages': {'phase-1': {'minimum_seconds': 1, 'minimum_output_tokens': 1}}}}
                    state = root / (condition + '-evidence')
                    compare.campaign.initialize(manifest, workspace, state, compare.campaign.Docker(name, workspace))
                    conditions.append({'id': condition, 'state': str(state)})
                config = {'schema_version': 1, 'mode': 'prospective', 'task': 'redaction-v2',
                          'conditions': conditions, 'image': image, 'legacy': None,
                          'include_checkpoints': True, 'observer_seconds': 60, 'observer_slots': 1,
                          'intervention_fields': []}
                path = root / 'config.json';path.write_text(json.dumps(config))
                output = root / 'comparison'
                record = compare.seal(path, output)
                compare.execute_all(record, output)
                result = compare.evaluate(record, output)
                self.assertTrue(result['conditions']['improved']['quality_and_budget_passed'])
                self.assertFalse(result['conditions']['control']['quality_and_budget_passed'])
                self.assertIsNone(result['speed_ratio'])
                self.assertFalse(result['human_grading'])
                with self.assertRaises(ValueError):
                    compare.execute_all(record, output)
            finally:
                for name in containers:
                    subprocess.run(['docker', 'rm', '-f', name], capture_output=True)


if __name__ == '__main__':
    unittest.main()

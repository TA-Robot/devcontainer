"""Calibrate the next task with correct behavior and independently chosen defects."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'experiments/development-harness/cycle-005'
sys.path.insert(0, str(HERE))
import evaluate_sync as oracle


class SyncOracleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='cli-sync-calibration-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.candidate = self.root / 'candidate'
        self.scripts = self.candidate / 'scripts'
        self.scripts.mkdir(parents=True)

    def reference(self, mutation=None):
        source = (HERE / 'reference_sync.py').read_text()
        if mutation == 'unlocked':
            source = source.replace('fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)', 'pass  # broken ownership')
        elif mutation == 'missing-check':
            source = source.replace("for line in Path(env['DEVCONTAINER_AI_CLI_VERSION_FILE']).read_text().splitlines():", 'for line in []:')
        (self.scripts / 'reference_sync.py').write_text(source)
        shutil.copyfile(ROOT / 'scripts/sync-host-ai-cli-versions', self.scripts / 'baseline-sync')
        (self.scripts / 'sync-host-ai-cli-versions').write_text('#!/bin/sh\nexec python3 "$(dirname "$0")/reference_sync.py"\n')

    def statuses(self, value):
        self.assertEqual([c['name'] for c in value['checks']], list(oracle.CASES))
        self.assertTrue(value['source_unchanged'])
        return {c['name']: c['status'] for c in value['checks']}

    def test_reference_passes_all_fixed_requirements(self):
        self.reference()
        result = oracle.evaluate(self.candidate)
        self.assertEqual(set(self.statuses(result).values()), {'passed'}, result)

    def test_original_fails_preservation_and_interruption_requirements(self):
        shutil.copyfile(ROOT / 'scripts/sync-host-ai-cli-versions', self.scripts / 'sync-host-ai-cli-versions')
        result = self.statuses(oracle.evaluate(self.candidate))
        self.assertEqual(result['stable'], 'passed')
        for name in ('curl-fail', 'npm-fail', 'term', 'kill'):
            self.assertEqual(result[name], 'failed')

    def test_constant_success_or_failure_cannot_pass(self):
        for code in (0, 1):
            with self.subTest(code=code):
                (self.scripts / 'sync-host-ai-cli-versions').write_text(f'exit {code}\n')
                result = self.statuses(oracle.evaluate(self.candidate))
                self.assertEqual(result['normal'], 'failed')
                self.assertEqual(result['invalid' if code == 0 else 'stable'], 'failed')

    def test_missing_executable_is_distinct_from_package_metadata(self):
        self.reference('missing-check')
        rows = oracle.sync_fixture.observe(self.candidate, ('missing-binary',))['checks']
        self.assertEqual(rows[0]['status'], 'failed', rows)
        self.assertEqual(rows[0]['detail'], 'incomplete update reported success')

    def test_unlocked_complete_updates_are_rejected(self):
        self.reference('unlocked')
        rows = oracle.sync_fixture.observe(self.candidate, ('concurrent',))['checks']
        self.assertEqual(rows[0]['status'], 'failed', rows)

    def test_candidate_source_mutation_invalidates_observation(self):
        (self.scripts / 'sync-host-ai-cli-versions').write_text('touch "$(dirname "$0")/changed"\nexit 1\n')
        result = oracle.evaluate(self.candidate)
        self.assertFalse(result['source_unchanged'])

    @unittest.skipUnless(os.environ.get('TERMINAL_DEVELOPMENT_IMAGE'), 'set verified image ID for the feedback adapter')
    def test_feedback_adapter_runs_fixed_oracle_after_submission(self):
        sys.path.insert(0, str(HERE.parent / 'feedback'))
        import workflow
        self.reference()
        record = {'config': {'task': 'cli-sync-v1', 'image': os.environ['TERMINAL_DEVELOPMENT_IMAGE'],
                            'observer_seconds': 90}, 'catalog': workflow.task_evaluation.catalog('cli-sync-v1', workflow.legacy)}
        output = self.root / 'comparison'
        output.mkdir()
        result = workflow.task_evaluation.evaluate_one(record, output,
            {'key': 'control-phase-1', 'source': str(self.candidate), 'phase': 1}, workflow.legacy)
        self.assertTrue(result['quality']['accepted'], result)
        self.assertEqual(len(result['quality']['checks']), 13)

    @unittest.skipUnless(os.environ.get('TERMINAL_DEVELOPMENT_IMAGE'), 'set verified image ID for installed runtime calibration')
    def test_reference_passes_in_readonly_image_without_authentication(self):
        self.reference()
        result = subprocess.run(['docker', 'run', '--rm', '--network', 'none', '--read-only',
            '--tmpfs', '/tmp:rw,exec,mode=1777', '-e', 'PYTHONDONTWRITEBYTECODE=1',
            '--mount', f'type=bind,src={HERE},dst=/oracle,readonly',
            '--mount', f'type=bind,src={self.candidate},dst=/candidate,readonly',
            os.environ['TERMINAL_DEVELOPMENT_IMAGE'], 'python3', '/oracle/evaluate_sync.py', '--candidate', '/candidate'],
            capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(set(self.statuses(value).values()), {'passed'}, value)


if __name__ == '__main__':
    unittest.main()

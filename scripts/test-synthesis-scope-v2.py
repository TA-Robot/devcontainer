"""Semantic scope calibration, public/external parity and stopped-snapshot boundaries."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'experiments/development-harness/consultation/synthesis_v2'
sys.path.insert(0, str(HERE))
import calibrate_synthesis as calibration
import synthesis_case as case
import synthesis_rules as rules


class SynthesisScopeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='test-synthesis-scope-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.workspace = self.root / 'workspace'
        case.create(self.workspace)
        self.answer = calibration.reference()
        calibration.submit(self.workspace, self.answer)

    def test_valid_diversity_and_each_invalid_structure_are_calibrated(self):
        value = calibration.calibrate()
        self.assertEqual(value['status'], 'pass', [r for r in value['records'] if r['status'] != 'pass'])
        self.assertEqual(len(value['records']), 39)
        self.assertEqual(value['live_provider_calls'], 0)
        self.assertFalse(value['general_quality_comparison_eligible'])
        boundaries = [r for r in value['records'] if r['unmeasured_boundary']]
        self.assertEqual(len(boundaries), 2)
        self.assertTrue(all(r['evaluation']['status'] == 'pass' for r in boundaries))

    def test_public_checker_matches_external_requirements_for_all_candidates(self):
        for row in calibration.candidates():
            with self.subTest(candidate=row['candidate']):
                calibration.submit(self.workspace, row['answer'])
                completed = subprocess.run([sys.executable, '-B', 'tools/synthesis_rules.py', 'check'],
                    cwd=self.workspace, capture_output=True, text=True, timeout=10)
                public = json.loads(completed.stdout)
                external = case.evaluate(self.workspace)
                self.assertEqual(public['status'], external['status'])
                self.assertEqual(public['checks'], external['checks'][1:])
                self.assertEqual(completed.returncode, int(public['status'] != 'pass'))

    def test_renderer_exposes_all_structured_fields_and_detects_stale_markdown(self):
        self.answer['unknowns'][0]['topics'].append('rollback')
        (self.workspace / 'decision-record.json').write_text(json.dumps(self.answer))
        result = case.evaluate(self.workspace)
        self.assertIn({'name': 'document-sync', 'status': 'failed'}, result['checks'])
        completed = subprocess.run([sys.executable, '-B', 'tools/synthesis_rules.py', 'render'],
            cwd=self.workspace, capture_output=True, text=True, timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(case.evaluate(self.workspace)['status'], 'pass')
        content = (self.workspace / 'DECISION-RECORD.md').read_text()
        self.assertIn('"scope"', content)
        self.assertIn('"rollback"', content)
        self.assertEqual(json.loads(content.split('```json\n')[1].split('\n```')[0]), self.answer)

    def test_old_records_are_rejected_without_implicit_conversion_or_rescoring(self):
        original = copy.deepcopy(case.f12.L_GOOD)
        calibration.submit(self.workspace, original)
        before = case.inventory(self.workspace)
        result = case.evaluate(self.workspace)
        self.assertEqual(result['status'], 'fail')
        self.assertIn({'name': 'artifact-contract', 'status': 'failed'}, result['checks'])
        self.assertEqual(case.inventory(self.workspace), before)
        self.assertEqual(case.f12.L_GOOD, original)

    def test_malformed_json_and_types_fail_without_crashing(self):
        path = self.workspace / 'decision-record.json'
        for content in ('{', '[]', '{"version":2,"version":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e309}',
                        '[' * 1100 + '0' + ']' * 1100):
            with self.subTest(content=content[:50]):
                path.write_text(content)
                self.assertEqual(case.evaluate(self.workspace)['status'], 'fail')
        for field, content in (('claims', [None]), ('unknowns', None), ('decision', []), ('controls', 'bad')):
            value = copy.deepcopy(self.answer)
            value[field] = content
            calibration.submit(self.workspace, value)
            self.assertEqual(case.evaluate(self.workspace)['status'], 'fail')
        for field, content in (('scope', []), ('evidence', ['BM-A-WARM', 'BM-A-WARM']),
                               ('provenance', {}), ('missing_evidence', [None])):
            value = copy.deepcopy(self.answer)
            value['claims'][0][field] = content
            calibration.submit(self.workspace, value)
            self.assertEqual(case.evaluate(self.workspace)['status'], 'fail')

    def test_changed_inputs_or_tools_fail_before_evaluation(self):
        marker = self.root / 'must-not-exist'
        (self.workspace / 'tools/synthesis_rules.py').write_text(f'open({str(marker)!r}, "w").write("ran")')
        with patch.object(rules, 'evaluate', side_effect=AssertionError('must not evaluate')):
            value = case.evaluate(self.workspace)
        self.assertEqual(value['reason'], 'source-integrity')
        self.assertFalse(marker.exists())

    def test_mid_evaluation_mutation_invalidates_result(self):
        real = rules.evaluate
        def changed(*args, **kwargs):
            value = real(*args, **kwargs)
            (self.workspace / 'decision-record.json').write_text('{}')
            return value
        with patch.object(rules, 'evaluate', side_effect=changed):
            self.assertEqual(case.evaluate(self.workspace)['reason'], 'source-integrity')

    def test_no_subprocess_or_git_config_execution_during_evaluation(self):
        (self.workspace / '.git').mkdir()
        (self.workspace / '.git/config').write_text('invalid git config')
        with patch.object(subprocess, 'Popen', side_effect=AssertionError('no candidate code')):
            self.assertEqual(case.evaluate(self.workspace)['status'], 'pass')

    def test_missing_oversized_symlink_fifo_and_extra_paths_fail_closed(self):
        path = self.workspace / 'decision-record.json'
        path.unlink()
        self.assertEqual(case.evaluate(self.workspace)['status'], 'fail')
        path.write_bytes(b' ' * (case.FILE_CAP + 1))
        self.assertEqual(case.evaluate(self.workspace)['status'], 'fail')
        path.unlink()
        path.symlink_to(self.root / 'absent')
        self.assertEqual(case.evaluate(self.workspace)['status'], 'fail')
        path.unlink()
        os.mkfifo(path)
        self.assertEqual(case.evaluate(self.workspace)['status'], 'fail')
        path.unlink()
        calibration.submit(self.workspace, self.answer)
        (self.workspace / 'extra').mkdir()
        self.assertEqual(case.evaluate(self.workspace)['status'], 'fail')

    def test_private_answers_and_old_validators_are_not_distributed(self):
        files = case.files()
        self.assertNotIn('calibrate_synthesis.py', files)
        self.assertNotIn('synthesis_case.py', files)
        self.assertEqual({p for p in files if p.startswith('tools/')}, {'tools/synthesis_rules.py'})
        for content in files.values():
            self.assertNotIn('L_GOOD', content)
            self.assertNotIn('universal winner', content)

    @unittest.skipUnless(os.environ.get('SYNTHESIS_SCOPE_IMAGE'), 'set verified image ID')
    def test_readonly_docker_calibration_without_network_or_credentials(self):
        name = 'synthesis-scope-test-' + uuid.uuid4().hex
        with tempfile.TemporaryDirectory(prefix='synthesis-scope-docker-') as raw:
            try:
                subprocess.run(['docker', 'create', '--name', name, '--network', 'none', '--read-only',
                    '--tmpfs', '/tmp:rw,exec,mode=1777', '-e', 'PYTHONDONTWRITEBYTECODE=1',
                    '--mount', f'type=bind,src={ROOT},dst=/repo,readonly',
                    '--mount', f'type=bind,src={raw},dst=/results', os.environ['SYNTHESIS_SCOPE_IMAGE'],
                    'python3', '/repo/experiments/development-harness/consultation/synthesis_v2/calibrate_synthesis.py',
                    '--output', '/results/calibration.json'], check=True, capture_output=True, timeout=30)
                completed = subprocess.run(['docker', 'start', '-a', name], capture_output=True, text=True, timeout=60)
                self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
                value = json.loads((Path(raw) / 'calibration.json').read_text())
                self.assertEqual(value['status'], 'pass', value)
                self.assertEqual(value['source_sha256'], calibration.calibrate()['source_sha256'])
            finally:
                removed = subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=30)
                self.assertEqual(removed.returncode, 0, removed.stderr)


if __name__ == '__main__':
    unittest.main()

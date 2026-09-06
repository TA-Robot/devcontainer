"""Check audit coverage and keep supplementary evidence separate from old scores."""
import hashlib
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
HERE = ROOT / 'experiments/development-harness/selection'
sys.path.insert(0, str(HERE))
import audit_f04_lifecycle as audit


class LifecycleAuditTests(unittest.TestCase):
    def workspace(self, label):
        temporary = tempfile.TemporaryDirectory(prefix='test-f04-audit-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        sources = next(s for name, s, _, _ in audit.candidates() if name == label)
        for name, content in {**audit.fixtures.L_FILES, **sources}.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        (root / 'bin/queuectl').chmod(0o755)
        return root

    def assert_audit(self, result):
        self.assertEqual(result['status'], 'pass', [r['candidate'] for r in result['records'] if r['status'] != 'pass'])
        rows = {r['candidate']: r for r in result['records']}
        self.assertEqual(len(rows), 9)
        for name in ('known-good', 'alternate-atomic-writer'):
            self.assertEqual(rows[name]['historical_score']['passed'], 4)
            self.assertTrue(all(p['status'] == 'pass' for p in rows[name]['supplementary_probes']))
        for name, probe in (('in-place-truncating-write', 'atomic-replacement-visible-to-reader'),
                            ('wrapper-splits-arguments', 'argument-boundaries')):
            self.assertEqual(rows[name]['historical_score']['passed'], 4)
            self.assertIn(probe, [p['probe'] for p in rows[name]['supplementary_probes'] if p['status'] == 'fail'])
        self.assertEqual(result['live_provider_calls'], 0)
        self.assertFalse(result['unmodified_task_admitted'])
        self.assertFalse(result['historical_scores_overwritten'])
        self.assertIn('process kill during write', result['unmeasured'])

    def test_calibration_demonstrates_false_positives_and_accepts_alternative(self):
        paths = [Path(audit.fixtures.__file__), audit.CATALOG, audit.CAPSULE]
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        self.assert_audit(audit.audit())
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})

    def test_atomic_probe_observes_old_descriptor_and_new_path_without_source_hooks(self):
        for label, expected in (('known-good', 'pass'), ('alternate-atomic-writer', 'pass'),
                                ('in-place-truncating-write', 'fail')):
            with self.subTest(candidate=label):
                result = audit.observe(self.workspace(label), 'atomic-replacement-visible-to-reader')
                self.assertEqual(result['status'], expected)
                observed = result['observations'][-1]
                self.assertEqual(observed['old_reader_retained_bytes'], expected == 'pass')
                self.assertTrue(observed['path_changed'])

    def test_arguments_are_checked_outside_workspace_with_whitespace_and_unicode(self):
        for label, expected in (('known-good', 'pass'), ('wrapper-splits-arguments', 'fail')):
            result = audit.observe(self.workspace(label), 'argument-boundaries')
            self.assertEqual(result['status'], expected)

    def test_timeout_is_unknown_and_cannot_be_reported_as_a_detected_defect(self):
        with patch.object(audit, 'run_queue', side_effect=subprocess.TimeoutExpired('queuectl', 5)):
            result = audit.observe(self.workspace('known-good'), 'fresh-process-idempotence')
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['reason'], 'command-timeout')

    def test_candidate_rewrites_fail_when_historical_source_does_not_match(self):
        for source in ('missing', 'old old'):
            with self.assertRaises(ValueError):
                audit.replace_once(source, 'old', 'new')

    def test_output_reservation_prevents_replay(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / 'existing.json'
            path.write_text('preserve')
            completed = subprocess.run([sys.executable, '-B', str(HERE / 'audit_f04_lifecycle.py'),
                '--output', str(path)], capture_output=True, text=True, timeout=10)
            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(path.read_text(), 'preserve')

    @unittest.skipUnless(os.environ.get('F04_AUDIT_IMAGE'), 'set verified image ID')
    def test_real_docker_audit_without_network_or_credentials(self):
        name = 'f04-audit-test-' + uuid.uuid4().hex
        with tempfile.TemporaryDirectory(prefix='f04-docker-result-') as raw:
            try:
                subprocess.run(['docker', 'create', '--name', name, '--network', 'none', '--read-only',
                    '--tmpfs', '/tmp:rw,exec,mode=1777', '-e', 'PYTHONDONTWRITEBYTECODE=1',
                    '--mount', f'type=bind,src={ROOT},dst=/repo,readonly',
                    '--mount', f'type=bind,src={raw},dst=/results', os.environ['F04_AUDIT_IMAGE'],
                    'python3', '/repo/experiments/development-harness/selection/audit_f04_lifecycle.py',
                    '--output', '/results/audit.json'], check=True, capture_output=True, timeout=30)
                completed = subprocess.run(['docker', 'start', '-a', name], capture_output=True,
                                           text=True, timeout=120)
                self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
                result = json.loads((Path(raw) / 'audit.json').read_text())
                self.assert_audit(result)
            finally:
                removed = subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=30)
                self.assertEqual(removed.returncode, 0, removed.stderr)


if __name__ == '__main__':
    unittest.main()

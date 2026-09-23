#!/usr/bin/env python3
"""Calibrate quality checks with real behavior and deliberately broken variants."""
import json
from pathlib import Path
import runpy
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
QUALITY = runpy.run_path(str(ROOT / 'experiments/development-harness/quality/lifecycle.py'))


class LifecycleQualityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='quality-calibration-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.candidate = self.root / 'candidate'
        scripts = self.candidate / 'scripts'
        scripts.mkdir(parents=True)
        self.cli = scripts / 'manage-agent-project'
        shutil.copy2(ROOT / 'scripts/manage-agent-project', self.cli)

    def scenario(self):
        directory = Path(tempfile.mkdtemp(dir=self.root))
        return QUALITY['Scenario'](directory, self.candidate)

    def wrap_cli(self, after):
        actual = self.cli.with_name('actual-cli')
        self.cli.rename(actual)
        self.cli.write_text(
            '#!/usr/bin/env python3\n'
            'import pathlib,subprocess,sys\n'
            f'p=subprocess.run([{str(actual)!r},*sys.argv[1:]])\n'
            'target=pathlib.Path(sys.argv[sys.argv.index("--target")+1])\n'
            + after + '\nraise SystemExit(p.returncode)\n')
        self.cli.chmod(0o755)

    def test_current_cli_passes_each_added_behavior(self):
        for name, action in QUALITY['SUPPLEMENTAL'].items():
            with self.subTest(name=name):
                action(self.scenario())

    def test_matching_bytes_and_executable_bits_do_not_require_all_modes_equal(self):
        text = self.cli.read_text()
        old = '(current["mode"] & 0o111) == (entry["mode"] & 0o111)'
        self.assertIn(old, text)
        self.cli.write_text(text.replace(old, 'current["mode"] == entry["mode"]'))
        with self.assertRaises(AssertionError):
            QUALITY['private_mode_adoption'](self.scenario())

    def test_success_claim_cannot_hide_permission_loss(self):
        self.wrap_cli('if sys.argv[1]=="adopt" and p.returncode==0:\n'
                      ' (target/"settings.txt").chmod(0o644)')
        with self.assertRaisesRegex(AssertionError, 'adoption changed'):
            QUALITY['private_mode_adoption'](self.scenario())

    def test_missing_private_exclusion_is_detected_using_actual_git(self):
        self.wrap_cli('if sys.argv[1]=="apply" and p.returncode==0:\n'
                      ' (target/".agent-project/.gitignore").unlink(missing_ok=True)')
        with self.assertRaisesRegex(AssertionError, 'visible in ordinary Git'):
            QUALITY['private_metadata_exclusion'](self.scenario())

    def test_old_overlap_guard_is_rejected(self):
        text = self.cli.read_text()
        start, end = text.index('def separate('), text.index('\ndef compute(')
        legacy = '''def separate(source, target):
    require(source.path != target.path and not source.path.startswith(target.path + "/")
            and not target.path.startswith(source.path + "/"), "overlap")

'''
        self.cli.write_text(text[:start] + legacy + text[end:])
        with self.assertRaisesRegex(AssertionError, 'overlapping source'):
            QUALITY['overlapping_roots'](self.scenario())

    def test_incomplete_observations_are_unknown_not_success(self):
        rows = QUALITY['summarize']([{'name': 'explicit-adoption', 'status': 'passed'}])
        self.assertTrue(all(row['status'] == 'unknown' for row in rows))

    def test_failure_is_not_hidden_by_missing_or_passing_checks(self):
        rows = QUALITY['summarize']([
            {'name': 'explicit-adoption', 'status': 'passed'},
            {'name': 'private-mode-adoption', 'status': 'failed'},
        ])
        adoption = next(row for row in rows if row['id'] == 'matching-adoption')
        self.assertEqual(adoption['status'], 'failed')

    def test_observer_failure_is_not_candidate_failure(self):
        def unavailable(_):
            raise PermissionError('observer cannot prepare fixture')
        result = QUALITY['observe']('probe', unavailable, self.candidate)
        self.assertEqual(result['status'], 'unknown')

    def test_catalog_covers_every_behavior_once_without_unknown_points(self):
        names = [name for _, _, _, checks in QUALITY['REQUIREMENTS'] for name in checks]
        expected = {name for name, _ in QUALITY['SHARED']['scenarios'](3)} | set(QUALITY['SUPPLEMENTAL'])
        self.assertEqual(set(names), expected)
        self.assertEqual(len(names), len(set(names)))
        with self.assertRaisesRegex(ValueError, 'unmapped'):
            QUALITY['summarize']([{'name': 'invented-quality-point', 'status': 'passed'}])

    def test_duplicate_observation_cannot_inflate_quality(self):
        check = {'name': 'explicit-adoption', 'status': 'passed'}
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            QUALITY['summarize']([check, check])


if __name__ == '__main__':
    unittest.main()

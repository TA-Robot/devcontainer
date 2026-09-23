"""Projection and classification tests; optional real Docker uses no provider/auth."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'experiments/development-harness/selection/lifecycle_v1/adapter.py'
spec = importlib.util.spec_from_file_location('lifecycle_selection_adapter', PATH)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class SelectionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='lifecycle-selection-test-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        audit, calibration = self.root / 'audit.json', self.root / 'calibration.json'
        calibration.write_text('{}')
        source_names = ['experiments/development-harness/quality/lifecycle.py',
                        'experiments/development-harness/multi-scale/large-01/evaluate.py',
                        *[f'experiments/development-harness/multi-scale/large-01/phase-{i}.md' for i in (1, 2, 3)]]
        hashes = {}
        for name in source_names:
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('synthetic public requirement or evaluator identity\n')
            hashes[name] = adapter.digest(path.read_bytes())
        rows = []
        for name in ('control', 'improved', 'integrated'):
            path = self.root / name
            (path / 'scripts').mkdir(parents=True)
            (path / 'scripts/manage-agent-project').write_text('#!/usr/bin/python3\nprint("public CLI")\n')
            (path / 'scripts/manage-agent-project').chmod(0o755)
            (path / 'PRIVATE-OLD-SCORES').write_text('must not project')
            labels = {'matching-adoption': 'failed' if name == 'improved' else 'passed',
                      'path-boundaries': 'passed' if name == 'integrated' else 'failed'}
            tree_hash = adapter.tree_hash(path)
            assessment = self.root / f'{name}.json'
            adapter.save(assessment, {'candidate_tree_sha256': tree_hash,
                'evaluator_sha256': hashes[source_names[0]], 'source_unchanged': True,
                'requirements': [{'id': k, 'status': v} for k, v in labels.items()]})
            rows.append({'name': name, 'directory': str(path), 'tree_sha256': tree_hash,
                         'saved_evaluation': str(assessment),
                         'saved_evaluation_sha256': adapter.digest(assessment.read_bytes())})
        adapter.save(audit, {'calibration_sha256': adapter.digest(calibration.read_bytes()),
                            'sources_sha256': hashes, 'candidates': rows})
        patches = mock.patch.multiple(adapter, ROOT=self.repo, AUDIT=audit, CALIBRATION=calibration)
        patches.start()
        self.addCleanup(patches.stop)
        self.task = self.root / 'task'
        self.seal = adapter.prepare(self.task)

    def decision(self, task=None):
        task = task or self.task
        seal = adapter.verify(task)
        return {'candidates': [{'id': n, 'scopes': {
            k: {'passed': 'acceptable', 'failed': 'needs-repair', 'unknown': 'unknown'}[v]
            for k, v in e['saved_scopes'].items()}, 'reason': 'fixture classification',
            'evidence': [f'candidates/{n}/manage-agent-project']}
            for n, e in seal['candidates'].items()], 'selected': None}

    def recorded(self, decision, task=None):
        task = task or self.task
        run = self.root / ('run-' + str(len(list(self.root.glob('run-*')))))
        run.mkdir()
        (run / 'probe.py').write_text('print("synthetic unit-test record")')
        data = decision if isinstance(decision, str) else json.dumps(decision)
        (run / 'probe.stdout').write_text(data)
        adapter.save(run / 'run.json', {'status': 'completed', 'returncode': 0,
            'owned_container_removed': True, 'source_unchanged': True,
            'task_seal_sha256': adapter.digest((task / 'private/seal.json').read_bytes()),
            'stdout_sha256': adapter.digest((run / 'probe.stdout').read_bytes()),
            'probe_sha256': adapter.digest((run / 'probe.py').read_bytes())})
        return run

    def test_projection_is_allowlisted_and_reference_requires_calibration(self):
        public = self.task / 'public'
        paths = {str(p.relative_to(public)) for p in public.rglob('*') if p.is_file()}
        self.assertEqual(paths, {'TASK.md', 'AGENTS.md', *[f'requirements/phase-{i}.md' for i in (1, 2, 3)],
            'candidates/candidate-1/manage-agent-project', 'candidates/candidate-2/manage-agent-project'})
        self.assertNotIn('must not project', ''.join(p.read_text() for p in public.rglob('*') if p.is_file()))
        with self.assertRaises(ValueError):
            adapter.prepare(self.root / 'bad', order=('control', 'improved', 'integrated'))
        with self.assertRaises(FileExistsError):
            adapter.prepare(self.task)
        with self.assertRaises(ValueError):
            adapter.prepare(self.root / 'control/new-task')
        other = self.root / 'reversed'
        adapter.prepare(other, order=('improved', 'control'))
        self.assertEqual(adapter.verify(other)['candidates']['candidate-1']['saved_scopes']['matching-adoption'], 'failed')

    def test_classification_defer_unknown_and_invalid_acceptance_are_distinct(self):
        decision = self.decision()
        value = adapter.assess(self.task, self.recorded(decision))
        self.assertEqual((value['status'], value['selection']), ('matched', 'deferred'))
        self.assertEqual(value['semantic_evidence_validity'], 'unknown')
        decision['candidates'][0]['scopes']['path-boundaries'] = 'unknown'
        self.assertEqual(adapter.assess(self.task, self.recorded(decision))['status'], 'incomplete')
        decision['candidates'][0]['scopes']['path-boundaries'] = 'acceptable'
        decision['selected'] = 'candidate-1'
        value = adapter.assess(self.task, self.recorded(decision))
        self.assertEqual((value['status'], value['selection']), ('contradicted', 'contradicted'))
        decision['candidates'][0]['scopes']['matching-adoption'] = 'needs-repair'
        self.assertEqual(adapter.assess(self.task, self.recorded(decision))['status'], 'withhold')

    def test_positive_calibration_does_not_force_selection(self):
        task = self.root / 'calibration-task'
        adapter.prepare(task, order=('integrated', 'improved', 'control'), calibration=True)
        decision = self.decision(task)
        decision['selected'] = 'candidate-1'
        value = adapter.assess(task, self.recorded(decision, task))
        self.assertEqual(value['selection'], 'supported-in-measured-scopes')
        self.assertTrue(value['calibration_only'])
        decision['selected'] = None
        self.assertEqual(adapter.assess(task, self.recorded(decision, task))['selection'], 'deferred')

    def test_malformed_duplicate_missing_and_escaping_outputs_are_withheld(self):
        good = self.decision()
        invalid = [None, [], {'candidates': [], 'selected': None},
                   '{"selected":null,"selected":null,"candidates":[]}',
                   '{"selected":NaN,"candidates":[]}',
                   '{"selected":1e999,"candidates":[]}', '['*1100+'0'+']'*1100]
        for field, value in [('id', 'alien'), ('evidence', ['../private/seal.json']),
                             ('evidence', ['missing']), ('evidence', ['probe.py', 'probe.py']),
                             ('evidence', ['']), ('scopes', {}), ('reason', '')]:
            row = copy.deepcopy(good)
            row['candidates'][0][field] = value
            invalid.append(row)
        duplicate = copy.deepcopy(good)
        duplicate['candidates'][1] = duplicate['candidates'][0]
        invalid.append(duplicate)
        for value in invalid:
            with self.subTest(value=value):
                self.assertEqual(adapter.assess(self.task, self.recorded(value))['status'], 'withhold')

    def test_changed_sources_labels_and_execution_evidence_are_rejected(self):
        decision = self.decision()
        run = self.recorded(decision)
        (run / 'probe.py').write_text('changed')
        self.assertEqual(adapter.assess(self.task, run)['status'], 'withhold')
        run = self.recorded(decision)
        record = json.loads((run / 'run.json').read_text())
        record['owned_container_removed'] = False
        (run / 'run.json').write_text(json.dumps(record))
        self.assertEqual(adapter.assess(self.task, run)['status'], 'withhold')
        (self.task / 'public/candidates/candidate-1/manage-agent-project').chmod(0o755)
        with self.assertRaises(ValueError):
            adapter.verify(self.task)

    def test_special_and_oversized_files_fail_without_blocking(self):
        os.mkfifo(self.root / 'pipe')
        (self.root / 'link').symlink_to(self.root / 'calibration.json')
        (self.root / 'linked-directory').symlink_to(self.root / 'control', target_is_directory=True)
        (self.root / 'big').write_bytes(b'12345')
        for name in ('pipe', 'link', 'linked-directory/scripts/manage-agent-project', 'big'):
            with self.subTest(name=name), self.assertRaises((OSError, ValueError)):
                adapter.read_file(self.root, name, 4)

    def test_archived_assessment_and_private_label_tampering_are_rejected(self):
        assessment = self.root / 'control.json'
        original = assessment.read_bytes()
        value = json.loads(original)
        value['requirements'][0]['status'] = 'failed'
        assessment.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, 'saved assessment changed'):
            adapter.verify(self.task)
        assessment.write_bytes(original)
        seal_path = self.task / 'private/seal.json'
        original_seal = seal_path.read_bytes()
        seal = json.loads(original_seal)
        seal['candidates']['candidate-1']['saved_scopes']['matching-adoption'] = 'failed'
        seal_path.write_text(json.dumps(seal))
        with self.assertRaisesRegex(ValueError, 'saved labels changed'):
            adapter.verify(self.task)
        seal_path.write_bytes(original_seal)
        (self.root / 'control/scripts/manage-agent-project').write_text('changed archive')
        with self.assertRaisesRegex(ValueError, 'archive identity changed'):
            adapter.verify(self.task)

    def test_regular_devcontainer_is_rejected_before_probe_launch(self):
        probe = self.root / 'probe.py'
        probe.write_text('print("should not run")')
        with self.assertRaisesRegex(ValueError, 'minimal probe image'):
            adapter.run_probe(self.task, probe, self.root / 'forbidden-run',
                image='sha256:760ecc736134756d8bb8d03312c01e97e1b865b58e12d40f7ca7328a6586e7f7', seconds=1)
        self.assertFalse((self.root / 'forbidden-run').exists())


@unittest.skipUnless(os.environ.get('LIFECYCLE_SELECTION_IMAGE'), 'set immutable image for isolated probes')
class DockerTests(unittest.TestCase):
    def test_archived_cli_behavior_and_classification_in_real_isolation(self):
        image = os.environ['LIFECYCLE_SELECTION_IMAGE']
        with tempfile.TemporaryDirectory(prefix='lifecycle-selection-docker-') as raw:
            root = Path(raw)
            task = root / 'task'
            adapter.prepare(task, order=('improved', 'integrated', 'control'), calibration=True)
            probe = root / 'probe.py'
            probe.write_text((PATH.parent / 'calibration_probe.py').read_text())
            record = adapter.run_probe(task, probe, root / 'run', image=image, seconds=30)
            self.assertEqual(record['status'], 'completed')
            self.assertEqual(record['returncode'], 0)
            self.assertTrue(record['owned_container_removed'])
            value = adapter.assess(task, root / 'run')
            self.assertEqual(value['status'], 'matched', value)
            self.assertEqual(value['selected'], 'candidate-2')
            self.assertFalse(value['current_environment_quality_regraded'])

    def test_timeout_output_cap_and_nonzero_are_not_success(self):
        image = os.environ['LIFECYCLE_SELECTION_IMAGE']
        with tempfile.TemporaryDirectory(prefix='lifecycle-selection-faults-') as raw:
            root = Path(raw)
            task = root / 'task'
            adapter.prepare(task)
            for name, script, seconds, expected in (
                ('timeout', 'import time; time.sleep(60)', 1, 'timeout'),
                ('overflow', 'print("x"*70000)', 20, 'invalid-or-excess-output'),
                ('failure', 'raise SystemExit(2)', 20, 'completed')):
                probe = root / f'{name}.py';probe.write_text(script)
                record = adapter.run_probe(task, probe, root / name, image=image, seconds=seconds)
                self.assertEqual(record['status'], expected)
                self.assertTrue(record['owned_container_removed'])
                self.assertEqual(adapter.assess(task, root / name)['status'], 'withhold')


if __name__ == '__main__':
    unittest.main()

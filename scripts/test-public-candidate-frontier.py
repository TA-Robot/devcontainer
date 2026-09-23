"""The upper-bound diagnostic must not confuse record completeness or objectives."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'experiments/development-harness/scheduling/public_frontier_v1/audit.py'
SPEC = importlib.util.spec_from_file_location('public_frontier', SOURCE)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class FrontierTest(unittest.TestCase):
    def test_read_only_inventory_renamed_source_and_input_mismatch(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'original'
            public = [{'id': f'development-{b}-{f}-{s}', 'jobs': [{'weight': 16}]}
                      for b in ('ordinary', 'contended', 'severe')
                      for f in ('burst', 'scarce', 'cache', 'mixed') for s in (0, 1)]
            raw_public = json.dumps(public).encode()
            report = {'valid': True, 'cases': [
                {'id': c['id'], 'status': 'measured', 'result': {'status': 'completed',
                 'offered_value': 16, 'on_time_value': 16, 'service_classes': {
                    '1': {'total': 0, 'on_time': 0}, '4': {'total': 0, 'on_time': 0},
                    '16': {'total': 1, 'on_time': 1}}}} for c in public]}
            source = b'raise RuntimeError("candidate code must never execute")\n'
            sha = AUDIT.digest(source)
            def write(name, data):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            write('public/development.json', raw_public)
            write('result.json', json.dumps({'status': 'withhold',
                                             'submission_sha256': {'solo': sha}}).encode())
            for actor, name in (('solo', 'public_final.json'), ('adaptive', 'submission_official.json')):
                write(f'actors/{actor}/public/development.json', raw_public)
                write(f'actors/{actor}/work/submission.py', source)
                write(f'actors/{actor}/work/{name}', json.dumps(report).encode())
            write('actors/adaptive/work/SELECTION.md', f'Final source SHA256: `{sha}`'.encode())
            report.update(source_sha256=sha, source_frozen_at_run_start=True,
                          candidate='/work/old-name.py', cases_sha256=AUDIT.digest(
                              json.dumps(public, sort_keys=True, separators=(',', ':')).encode()))
            write('actors/adaptive/work/comparison.json', json.dumps(report).encode())
            output = Path(folder) / 'audit'
            result = AUDIT.audit(root, output)
            plan = json.loads((output / 'plan.json').read_text())
            row = plan['inventory']['comparison.json']
            self.assertEqual(row['tier'], 'input_and_source_bound')
            self.assertEqual(row['matching_source_files'], ['submission.py'])
            self.assertTrue(result['all_read_inputs_unchanged'])
            self.assertEqual(result['original_status'], 'withhold')
            with self.assertRaises(FileExistsError):
                AUDIT.audit(root, output)
            report['cases_sha256'] = '0' * 64
            write('actors/adaptive/work/comparison.json', json.dumps(report).encode())
            with self.assertRaisesRegex(ValueError, 'input hash mismatch'):
                AUDIT.audit(root, Path(folder) / 'mismatch')
            self.assertFalse((Path(folder) / 'mismatch/result.json').exists())

    def test_tradeoff_is_not_reported_as_one_achieved_candidate(self):
        key = 'development-severe-burst-0'
        records = {'value': {key: {'value': 20, 'critical': 0}},
                   'critical': {key: {'value': 16, 'critical': 1}},
                   'bad': {key: {'value': 4, 'critical': 0}}}
        result = AUDIT.summarize(records, {key: {'value': 18, 'critical': 1}})['all']
        self.assertEqual(result['separate_objective_ceiling'], {'value': 20, 'critical': 1})
        self.assertEqual(set(result['nondominated_records']), {'value', 'critical'})
        self.assertNotIn(result['separate_objective_ceiling'], result['candidate_totals'].values())
        self.assertEqual(result['ceiling_minus_solo'], {'value': 2, 'critical': 0})

    def test_missing_duplicate_failed_and_fabricated_metrics_are_rejected(self):
        key = 'development-ordinary-burst-0'
        cases = {key: {'jobs': [{'weight': 16}, {'weight': 1}]}}
        row = {'id': key, 'status': 'measured', 'result': {'status': 'completed',
               'offered_value': 17, 'on_time_value': 16, 'service_classes': {
                   '1': {'total': 1, 'on_time': 0}, '4': {'total': 0, 'on_time': 0},
                   '16': {'total': 1, 'on_time': 1}}}}
        report = {'valid': True, 'cases': [row]}
        self.assertEqual(AUDIT.metrics(report, cases)[key], {'value': 16, 'critical': 1})
        for rows in ([], [row, row]):
            with self.assertRaises(ValueError):
                AUDIT.metrics({'valid': True, 'cases': rows}, cases)
        row['status'] = 'timeout'
        with self.assertRaises(ValueError):
            AUDIT.metrics(report, cases)
        row['status'] = 'measured'
        row['result']['on_time_value'] = 17
        with self.assertRaises(ValueError):
            AUDIT.metrics(report, cases)
        row['result']['on_time_value'] = 16
        row['result']['service_classes']['16']['on_time'] = True
        with self.assertRaises(ValueError):
            AUDIT.metrics(report, cases)


if __name__ == '__main__':
    unittest.main()

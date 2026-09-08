import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('profile_report', Path(__file__).with_name('report-dynamic-solo-profile.py'))
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


def results():
    raw = {'status': 'completed', 'all_containers_removed': True, 'cases': []}
    for b in module.BANDS:
        for f in module.FAMILIES:
            for i in range(2):
                raw['cases'].append({'id': f'qualification-{b}-{f}-{i}', 'status': 'measured', 'execution': {'removed': True},
                    'result': {**{k: 0 for k in module.SUMS}, 'on_time_value': 10, 'offered_value': 20,
                               'service_classes': {'16': {'total': 2, 'on_time': 1}}}})
    return {'submission': raw, 'reference': copy.deepcopy(raw)}


class ReportTests(unittest.TestCase):
    def test_all_cells_and_critical_regression_retained(self):
        r = results(); first = r['submission']['cases'][0]['result']
        first['on_time_value'] += 2; first['service_classes']['16']['on_time'] = 0
        s = module.summarize(r); self.assertEqual(len(s['cells']), 12)
        diff = s['cells']['ordinary/burst']['difference']
        self.assertEqual((diff['on_time_value'], diff['critical_on_time']), (2, -1))

    def test_missing_or_duplicate_cases_never_disappear(self):
        for duplicate in (False, True):
            r = results(); r['submission']['cases'].pop()
            if duplicate: r['submission']['cases'].append(r['submission']['cases'][0])
            with self.assertRaises(ValueError): module.summarize(r)

    def test_denominator_mismatch_rejected_and_empty_class_not_perfect(self):
        r = results(); r['reference']['cases'][0]['result']['offered_value'] += 1
        with self.assertRaises(ValueError): module.summarize(r)
        r = results()
        for raw in r.values():
            for row in raw['cases']: row['result']['service_classes'] = {}
        self.assertIsNone(module.summarize(r)['bands']['severe']['submission']['critical_fraction'])

    def test_withheld_profile_retains_partial_grader_without_promotion(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root/'assessment-submission').mkdir()
            (root/'result.json').write_text(json.dumps({'status': 'withhold', 'actor_started': True,
                'actor': {'status': 'completed'}, 'failure': 'incomplete assessment',
                'assessments': {'submission': {'cleanup': 'unknown'}}}))
            rows = [{'id': str(i), 'status': 'measured'} for i in range(21)]
            rows.append({'id': 'timeout', 'status': 'unmeasured', 'failure': 'TimeoutError', 'execution': {'removed': True}})
            (root/'assessment-submission/result.json').write_text(json.dumps({'status': 'withhold', 'all_containers_removed': True, 'cases': rows}))
            r = module.report(root, root/'summary.json')
            self.assertEqual(r['status'], 'withhold')
            self.assertNotIn('quality', r)
            c = r['assessment_coverage']['submission']
            self.assertEqual((c['measured'], c['unmeasured'], c['not_reached']), (21, 1, 2))
            self.assertTrue(c['grader_reported_cleanup'])
            self.assertFalse(r['assessment_coverage']['reference']['registered'])


if __name__ == '__main__': unittest.main()

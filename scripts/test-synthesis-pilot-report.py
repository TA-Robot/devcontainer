import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'experiments/development-harness/consultation'))
import synthesis_report as report


class ReportTests(unittest.TestCase):
    def values(self):
        rows = [{'candidate': n, 'status': 'pass', 'score': {'passed': 12, 'public_passed': 3}}
                for n in ('reference', 'explicitly-deny-generalization', 'additional-recovery-unknown')]
        condition = {'status': 'submitted', 'execution_seconds': 10, 'usage_complete': True,
                     'usage': {'input_tokens': 20, 'output_tokens': 10},
                     'quality': {'status': 'pass', 'score': {'passed': 12, 'total': 12}}}
        return {'status': 'completed', 'all_writers_stopped': True,
                'conditions': {'solo': copy.deepcopy(condition), 'consult': copy.deepcopy(condition)}}, {'records': rows}

    def test_false_negative_blocks_even_an_apparent_quality_pass_without_regrading(self):
        result, audit = self.values()
        audit['records'][1].update(status='fail', score={'passed': 11, 'public_passed': 3})
        original = copy.deepcopy(result)
        value = report.interpret(result, audit)
        self.assertFalse(value['quality_comparison_eligible'])
        self.assertIsNone(value['quality_conditioned_speed_ratio'])
        self.assertEqual(value['blocked_by_calibration'], ['explicitly-deny-generalization'])
        self.assertEqual(result, original)

    def test_unknown_usage_and_failed_quality_do_not_get_a_speed_ratio(self):
        for field, value in (('usage_complete', False), ('quality', {'status': 'fail', 'score': {'passed': 10}})):
            result, audit = self.values()
            result['conditions']['solo'][field] = value
            self.assertIsNone(report.interpret(result, audit)['quality_conditioned_speed_ratio'])

    def test_missing_calibration_and_nonfinite_times_are_rejected(self):
        result, audit = self.values()
        with self.assertRaises(ValueError):
            report.interpret(result, {'records': audit['records'][:2]})
        result['conditions']['solo']['execution_seconds'] = float('nan')
        with self.assertRaises(ValueError):
            report.interpret(result, audit)


if __name__ == '__main__':
    unittest.main()

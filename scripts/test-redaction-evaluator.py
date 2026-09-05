#!/usr/bin/env python3
import json
from pathlib import Path
import re
import runpy
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import agentctl_jobs as jobs
EVALUATOR = runpy.run_path(str(ROOT / 'experiments/development-harness/cycle-003/evaluate_redaction.py'))


def calibrated_reference(text):
    # Provider-free test double, kept outside candidate starting source.
    count = 0
    def visit(value):
        nonlocal count
        if isinstance(value, list):
            return [visit(item) for item in value]
        if isinstance(value, dict):
            result = {}
            for key, child in value.items():
                if isinstance(child, str) and child and (jobs.SECRET_ENV_NAME.search(key) or key.lower() == 'authorization'):
                    result[key] = '[MASKED]'
                    count += 1
                else:
                    result[key] = visit(child)
            return result
        return value
    output = []
    for line in text.splitlines(keepends=True):
        positions = [line.find(c) for c in ('{', '[') if c in line]
        if positions:
            start = min(positions)
            try:
                value, end = json.JSONDecoder().raw_decode(line[start:])
                line = line[:start] + json.dumps(visit(value), ensure_ascii=False) + line[start + end:]
            except json.JSONDecodeError:
                pass
        redacted, n = jobs._redact_log_text(line)
        count += n
        output.append(redacted)
    return ''.join(output), count


class RedactionEvaluatorTests(unittest.TestCase):
    def test_reference_preserves_useful_data_and_masks_all_cases(self):
        results = EVALUATOR['observations'](calibrated_reference)
        self.assertTrue(all(r['status'] == 'passed' for r in results), results)

    def test_current_bug_is_observable_without_invented_success(self):
        rows = {r['name']: r['status'] for r in EVALUATOR['observations'](jobs._redact_log_text)}
        self.assertEqual(rows['json-api_key'], 'failed')
        self.assertEqual(rows['ordinary-json'], 'passed')
        self.assertEqual(rows['assignment'], 'passed')

    def test_hiding_the_entire_log_is_not_quality_improvement(self):
        results = EVALUATOR['observations'](lambda text: ('[MASKED]', 1))
        self.assertTrue(any(r['status'] == 'failed' for r in results if r['dimension'] == 'structure-preservation'))
        self.assertTrue(any(r['status'] == 'failed' for r in results if r['dimension'] == 'log-context'))

    def test_zero_count_does_not_pass_secret_removal(self):
        def zero_count(text):
            return calibrated_reference(text)[0], 0
        results = EVALUATOR['observations'](zero_count)
        self.assertTrue(all(r['status'] == 'failed' for r in results if r['dimension'] == 'secret-removal'))

    def test_unknown_observer_failure_is_not_counted_as_success(self):
        def broken(text):
            raise OSError('observer unavailable')
        self.assertTrue(all(r['status'] == 'unknown' for r in EVALUATOR['observations'](broken)))


if __name__ == '__main__':
    unittest.main()

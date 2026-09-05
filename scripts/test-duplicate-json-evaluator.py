"""Calibrate the new task before either developer sees it."""
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('duplicate_observer', ROOT / 'experiments/development-harness/cycle-004/duplicates.py')
evaluator = importlib.util.module_from_spec(spec);spec.loader.exec_module(evaluator)


class Reference:
    class ContractValidationError(ValueError):
        pass

    allow_duplicates = False
    reject_all = False
    fold_case = False
    leak_values = False

    @classmethod
    def load_json(cls, path):
        def pairs(items):
            result = {}
            for key, value in items:
                name = key.lower() if cls.fold_case else key
                if name in result and not cls.allow_duplicates:
                    raise ValueError('duplicate property' + (str(items) if cls.leak_values else ''))
                result[name] = value
            return result
        def number(value):
            result = float(value)
            if not math.isfinite(result):
                raise ValueError('non-finite number')
            return result
        try:
            if cls.reject_all:
                raise ValueError('duplicate property')
            return json.loads(path.read_text(), object_pairs_hook=pairs, parse_float=number, parse_constant=number)
        except (OSError, ValueError) as error:
            raise cls.ContractValidationError(f'{path}: {error}')

    @classmethod
    def validate_file(cls, instance, schema):
        specification = cls.load_json(schema)
        value = cls.load_json(instance)
        if specification.get('type') == 'integer' and type(value) is not int:
            raise cls.ContractValidationError('schema type mismatch')


class DuplicateEvaluatorTests(unittest.TestCase):
    def test_correct_reference_passes_all_declared_requirements(self):
        rows = evaluator.observe(Reference)
        self.assertEqual(len(rows), 22)
        self.assertTrue(all(r['status'] == 'passed' for r in rows), rows)

    def test_last_wins_blanket_rejection_casefold_and_value_leak_are_detected(self):
        for field, witness in [('allow_duplicates', 'duplicate-root'), ('reject_all', 'siblings-allowed'),
                               ('fold_case', 'case-sensitive-names'), ('leak_values', 'duplicate-values-private')]:
            with self.subTest(mutant=field):
                variant = type('Mutant', (Reference,), {field: True})
                rows = {r['name']: r for r in evaluator.observe(variant)}
                self.assertEqual(rows[witness]['status'], 'failed', rows)

    def test_file_validation_cannot_bypass_the_shared_policy(self):
        variant = type('Bypass', (Reference,), {'validate_file': classmethod(lambda cls, instance, schema: None)})
        rows = {r['name']: r for r in evaluator.observe(variant)}
        self.assertEqual(rows['schema-duplicate']['status'], 'failed')
        self.assertEqual(rows['instance-duplicate']['status'], 'failed')


if __name__ == '__main__':
    unittest.main()

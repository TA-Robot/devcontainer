#!/usr/bin/env python3
"""External semantic acceptance for cycle 001. Run against a frozen checkout.

Only the candidate library is imported; candidate-authored tests are a separate
regression signal. These checks are not supplied to the development agent.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile


def evaluate(root: Path) -> dict:
    path = root / 'scripts/agent_contracts.py'
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location('candidate_contracts', path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    checks = []

    def check(name, action, reject=False):
        try:
            action()
            passed = not reject
            detail = None if passed else 'non-finite value accepted'
        except module.ContractValidationError:
            passed = reject
            detail = None if passed else 'valid value rejected'
        except Exception as exc:
            passed = False
            detail = type(exc).__name__
        checks.append({'name': name, 'passed': passed, 'detail': detail})

    wrappers = [lambda x: x, lambda x: {'opaque': [0, {'value': x}]},
                lambda x: [True, [None, {'other': {'x': x}}]]]
    for label, value in [('nan', float('nan')), ('posinf', float('inf')), ('neginf', -float('inf'))]:
        for index, wrap in enumerate(wrappers):
            instance = wrap(value)
            check(f'validate-{label}-shape-{index}',
                  lambda x=instance: module.validate(x, {}), reject=True)
        check(f'typed-{label}', lambda x=value: module.validate(x, {'type': 'number'}), reject=True)
    with tempfile.TemporaryDirectory(prefix='contract-acceptance-') as raw:
        instance_path = Path(raw) / 'value.json'
        for token in ['NaN', 'Infinity', '-Infinity', '1e309', '-1e309']:
            for index, content in enumerate([token, '{"opaque": [1, {"x": ' + token + '}]}']):
                instance_path.write_text(content)
                check(f'load-{token}-shape-{index}', lambda: module.load_json(instance_path), reject=True)
        finite = {'items': [True, False, None, 0, -7, 10**500, 1e308, 1e-300, 'NaN']}
        instance_path.write_text(json.dumps(finite, allow_nan=False))
        def roundtrip():
            assert module.load_json(instance_path) == finite
        check('finite-load-roundtrip', roundtrip)
        check('finite-unconstrained-nested', lambda: module.validate(finite, {}))
        instance_path.write_text('{bad json')
        check('malformed-json-remains-contract-error', lambda: module.load_json(instance_path), reject=True)
    for name, value, schema in [
        ('large-integer', 10**500, {'type': 'integer'}),
        ('large-integer-as-number', 10**500, {'type': 'number'}),
        ('bool', True, {'type': 'boolean'}),
        ('finite-boundary', 1.5, {'type': 'number', 'minimum': 1, 'maximum': 2}),
        ('optional-extra', {'x': 1, 'extra': ['Infinity']}, {'type': 'object', 'properties': {'x': {'type': 'integer'}}}),
    ]:
        check(name, lambda v=value, s=schema: module.validate(v, s))
    check('bool-not-number', lambda: module.validate(True, {'type': 'number'}), reject=True)
    check('range-check-preserved', lambda: module.validate(3, {'type': 'number', 'maximum': 2}), reject=True)
    check('required-key-preserved', lambda: module.validate({}, {'type': 'object', 'required': ['x']}), reject=True)
    unchanged = before == hashlib.sha256(path.read_bytes()).hexdigest()
    return {'schema_version': 1, 'candidate_sha256': before, 'source_unchanged': unchanged,
            'passed': sum(c['passed'] for c in checks), 'total': len(checks),
            'accepted': unchanged and all(c['passed'] for c in checks), 'checks': checks}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = evaluate(args.candidate.resolve())
    text = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(text + '\n')
    print(text)
    return 0 if report['accepted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

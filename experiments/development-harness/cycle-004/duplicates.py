"""Independent duplicate-key requirements; candidate code is loaded only for observation."""
import importlib.util
import json
from pathlib import Path
import tempfile


def cases():
    return [
        ('duplicate-root', 'ambiguity', 'reject', '{"x":1,"x":2}'),
        ('duplicate-nested', 'ambiguity', 'reject', '{"outer":{"x":1,"x":2}}'),
        ('duplicate-array-object', 'ambiguity', 'reject', '[{"x":1,"x":2}]'),
        ('escaped-equivalent-key', 'ambiguity', 'reject', '{"a":1,"\\u0061":2}'),
        ('equal-values-still-duplicate', 'ambiguity', 'reject', '{"x":1,"x":1}'),
        ('empty-key-duplicate', 'ambiguity', 'reject', '{"":0,"":1}'),
        ('siblings-allowed', 'compatibility', 'accept', '[{"x":1},{"x":2}]'),
        ('case-sensitive-names', 'compatibility', 'accept', '{"Key":1,"key":2}'),
        ('unicode-distinct-names', 'compatibility', 'accept', '{"é":1,"e\\u0301":2}'),
        ('ordinary-types', 'compatibility', 'accept', '{"s":"日本語","n":7,"f":1.25,"b":true,"z":null}'),
        ('top-level-scalar', 'compatibility', 'accept', '42'),
        ('top-level-array', 'compatibility', 'accept', '[false,null,"x",3]'),
        ('nonfinite-nan', 'compatibility', 'reject-number', 'NaN'),
        ('nonfinite-infinity', 'compatibility', 'reject-number', '{"n":Infinity}'),
        ('overflowing-float', 'compatibility', 'reject-number', '1e9999'),
        ('syntax-diagnostic', 'diagnostics', 'syntax', '{broken'),
        ('io-diagnostic', 'diagnostics', 'missing', None),
        ('duplicate-values-private', 'diagnostics', 'privacy', '{"x":"fixture-private-first","x":"fixture-private-last"}'),
        ('schema-duplicate', 'validation-entrypoints', 'schema', '{"type":"integer","type":"string"}'),
        ('instance-duplicate', 'validation-entrypoints', 'instance', '{"x":1,"x":2}'),
        ('schema-type-still-enforced', 'validation-entrypoints', 'schema-type', '"wrong type"'),
        ('valid-instance-still-accepted', 'validation-entrypoints', 'valid-instance', '7'),
    ]


def catalog():
    return [{'name': n, 'phase': 1, 'dimension': d} for n, d, _, _ in cases()]


def observe(module):
    rows = []
    with tempfile.TemporaryDirectory(prefix='duplicate-json-observer-') as temporary:
        root = Path(temporary)
        for name, dimension, kind, raw in cases():
            path = root / (name + '.json')
            if raw is not None:
                path.write_text(raw)
            before = path.read_bytes() if path.exists() else None
            try:
                if kind == 'valid-instance':
                    schema = root / 'valid-schema.json'
                    schema.write_text('{"type":"integer"}')
                    assert module.validate_file(path, schema) is None, 'validation interface changed'
                elif kind == 'accept':
                    actual = module.load_json(path)
                    expected = json.loads(raw)
                    assert actual == expected and type(actual) is type(expected), 'ordinary JSON changed'
                    if isinstance(expected, dict):
                        assert all(type(actual[k]) is type(v) for k, v in expected.items()), 'value type changed'
                else:
                    try:
                        if kind == 'schema-type':
                            schema = root / 'type-schema.json'
                            schema.write_text('{"type":"integer"}')
                            module.validate_file(path, schema)
                        elif kind in ('schema', 'instance'):
                            other = root / 'other.json'
                            other.write_text('1' if kind == 'schema' else '{"type":"object"}')
                            module.validate_file(other, path) if kind == 'schema' else module.validate_file(path, other)
                        else:
                            module.load_json(path)
                    except module.ContractValidationError as error:
                        message = str(error)
                        if kind != 'schema-type':
                            assert str(path) in message, 'input path missing from diagnostic'
                        if kind in ('reject', 'privacy', 'schema', 'instance'):
                            assert any(term in message.lower() for term in ('duplicat', 'repeated', '重複')), 'duplicate ambiguity not identified'
                        if kind == 'privacy':
                            assert 'fixture-private-first' not in message and 'fixture-private-last' not in message, 'values leaked'
                    else:
                        raise AssertionError('invalid or ambiguous input accepted')
                assert (path.read_bytes() if path.exists() else None) == before, 'input file mutated'
                status, detail = 'passed', None
            except (AssertionError, module.ContractValidationError) as error:
                status, detail = 'failed', str(error)
            except Exception as error:
                status, detail = 'unknown', type(error).__name__
            rows.append({'name': name, 'phase': 1, 'dimension': dimension, 'status': status, 'detail': detail})
    return rows


def evaluate(candidate):
    spec = importlib.util.spec_from_file_location('observed_contracts', candidate / 'scripts/agent_contracts.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {'checks': observe(module)}

#!/usr/bin/env python3
"""Independent small-02 requirements; synthetic secrets only, no model calls."""
from __future__ import annotations
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys

SECRET = 'fixture-private-value-123'


def require(value, detail):
    if not value:
        raise AssertionError(detail)


def observations(redact):
    def call(text):
        output, count = redact(text)
        require(isinstance(output, str) and type(count) is int and count >= 0,
                'redaction interface changed')
        return output, count

    def structured(value, expected, *, escaped=False):
        text = json.dumps(value, ensure_ascii=escaped)
        output, count = call(text)
        require(SECRET not in output, 'sensitive value remains in structured log')
        require(count > 0, 'redaction count omitted removed secret')
        decoded = json.loads(output)
        # Replace only the expected sensitive fields; a placeholder may be chosen
        # by the implementation, but it must not retain secret content.
        def check(actual, wanted):
            if wanted is MASK:
                require(isinstance(actual, str) and actual != SECRET and SECRET not in actual,
                        'sensitive field not masked')
            elif isinstance(wanted, dict):
                require(isinstance(actual, dict) and set(actual) == set(wanted), 'ordinary keys lost')
                for key in wanted:
                    check(actual[key], wanted[key])
            elif isinstance(wanted, list):
                require(isinstance(actual, list) and len(actual) == len(wanted), 'array structure lost')
                for a, w in zip(actual, wanted):
                    check(a, w)
            else:
                require(type(actual) is type(wanted) and actual == wanted, 'ordinary value changed')
        check(decoded, expected)

    MASK = object()
    cases = []
    for key in ('api_key', 'API-KEY', 'refresh_token', 'client_secret', 'password',
                'passwd', 'credential', 'private_key', 'Authorization'):
        cases.append((f'json-{key}', 'secret-removal',
                      lambda k=key: structured({k: SECRET, 'message': 'useful'}, {k: MASK, 'message': 'useful'})))
    cases.append(('nested-array', 'structure-preservation', lambda: structured(
        {'rows': [{'token': SECRET, 'n': 7}, {'message': '日本語'}], 'password': None, 'secret': False},
        {'rows': [{'token': MASK, 'n': 7}, {'message': '日本語'}], 'password': None, 'secret': False})))
    cases.append(('top-level-array', 'structure-preservation', lambda: structured(
        [{'credential': SECRET}, 3, 'ordinary'], [{'credential': MASK}, 3, 'ordinary'])))

    def escaped():
        value = SECRET + '"\\\n日本語'
        raw = '{"\\u0061pi_key":' + json.dumps(value, ensure_ascii=True) + ',"message":"kept"}'
        output, count = call(raw)
        decoded = json.loads(output)
        require(count > 0 and SECRET not in output and SECRET not in decoded['api_key'],
                'escaped secret or key bypassed redaction')
        require(decoded['message'] == 'kept', 'ordinary field lost')
    cases.append(('escaped-key-and-value', 'secret-removal', escaped))

    def mixed_lines():
        text = 'INFO payload ' + json.dumps({'api_key': SECRET, 'message': 'kept'}) + '\nordinary neighbor\n'
        output, count = call(text)
        require(SECRET not in output and count > 0, 'prefixed payload leaked secret')
        require('INFO payload ' in output and 'ordinary neighbor' in output and 'kept' in output,
                'useful log context lost')
    cases.append(('prefixed-multiline', 'log-context', mixed_lines))

    def ordinary():
        value = {'message': 'ordinary 日本語', 'token_count': 12, 'secret': None, 'ok': True}
        output, _ = call(json.dumps(value))
        require(json.loads(output) == value, 'nonsensitive structured content lost')
    cases.append(('ordinary-json', 'structure-preservation', ordinary))

    def legacy(text, secret):
        output, count = call(text)
        require(secret not in output and count > 0, 'existing redaction regressed')
        require('neighbor' in output, 'ordinary context lost')
    for name, text, secret in [
        ('assignment', f'API_KEY={SECRET} neighbor', SECRET),
        ('bearer', f'Authorization: Bearer {SECRET} neighbor', SECRET),
        ('basic', f'Authorization: Basic {SECRET} neighbor', SECRET),
        ('known-token', 'sk-proj-fixturevalue123456789 neighbor', 'sk-proj-fixturevalue123456789'),
        ('environment-value', f'embedded {SECRET} neighbor', SECRET),
    ]:
        def action(t=text, v=secret, n=name):
            if n == 'environment-value':
                os.environ['HARNESS_FIXTURE_SECRET'] = SECRET
            try:
                legacy(t, v)
            finally:
                if n == 'environment-value':
                    os.environ.pop('HARNESS_FIXTURE_SECRET', None)
        cases.append((name, 'legacy-compatibility', action))
    checks = []
    for name, dimension, action in cases:
        try:
            action()
            status, detail = 'passed', None
        except (AssertionError, json.JSONDecodeError, KeyError, TypeError) as error:
            status, detail = 'failed', type(error).__name__ + ': ' + str(error)[:300]
        except Exception as error:
            status, detail = 'unknown', type(error).__name__
        checks.append({'name': name, 'dimension': dimension, 'status': status, 'detail': detail})
    return checks


def evaluate(candidate):
    paths = [candidate / 'scripts' / name for name in ('agentctl_jobs.py', 'agent_contracts.py')]
    def hashes():
        return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    before = hashes()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(candidate / 'scripts'))
    for name in ('agentctl_jobs', 'agent_contracts'):
        sys.modules.pop(name, None)
    module = importlib.import_module('agentctl_jobs')
    require(Path(module.__file__).resolve() == paths[0].resolve(), 'wrong candidate module imported')
    checks = observations(module._redact_log_text)
    unchanged = hashes() == before
    return {'schema_version': 1, 'task': 'small-02', 'candidate_hashes': before,
            'evaluator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'source_unchanged': unchanged, 'checks': checks,
            'measurement_complete': unchanged and all(c['status'] != 'unknown' for c in checks),
            'accepted': unchanged and all(c['status'] == 'passed' for c in checks)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.candidate.resolve())
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'accepted': result['accepted'], 'checks': result['checks']}, indent=2))
    raise SystemExit(0 if result['measurement_complete'] else 2)

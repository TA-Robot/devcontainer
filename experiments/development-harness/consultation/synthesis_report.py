"""Derived pilot interpretation with an oracle-validity gate; never changes grades."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def number(value):
    return type(value) in (float, int) and math.isfinite(value) and value >= 0


def interpret(result, audit):
    calibration = {row['candidate']: row for row in audit['records']}
    expected = {'reference', 'explicitly-deny-generalization', 'additional-recovery-unknown'}
    if len(audit['records']) != 3 or set(calibration) != expected:
        raise ValueError('complete fixed validity calibration required')
    reference = calibration['reference']
    if reference['status'] != 'pass' or reference['score']['passed'] != 12:
        raise ValueError('reference calibration unavailable')
    blocked = []
    for name in sorted(expected - {'reference'}):
        row = calibration[name]
        if row['score']['public_passed'] != 3:
            raise ValueError('publicly valid alternative not established')
        if row['status'] != 'pass' or row['score']['passed'] != 12:
            blocked.append(name)
    observations = {}
    for name in ('solo', 'consult'):
        row = result['conditions'][name]
        value = {'status': row['status'], 'execution_seconds': row.get('execution_seconds'),
                 'usage_complete': row.get('usage_complete', False), 'usage': row.get('usage', {}),
                 'original_score': (row.get('quality') or {}).get('score'),
                 'original_quality_status': (row.get('quality') or {}).get('status')}
        if value['execution_seconds'] is not None and not number(value['execution_seconds']):
            raise ValueError('invalid measured time')
        if any(v is not None and not number(v) for v in value['usage'].values()):
            raise ValueError('invalid measured usage')
        observations[name] = value
    a, b = observations['solo'], observations['consult']
    eligible = (not blocked and result['all_writers_stopped'] and result['status'] == 'completed'
                and all(row['status'] == 'submitted' and row['usage_complete']
                        and row['original_quality_status'] == 'pass' for row in (a, b)))
    speed = (a['execution_seconds'] / b['execution_seconds'] if eligible
             and number(a['execution_seconds']) and number(b['execution_seconds'])
             and b['execution_seconds'] > 0 else None)
    return {'kind': 'synthesis-pilot-interpretation-v1', 'observations': observations,
            'quality_comparison_eligible': bool(eligible), 'blocked_by_calibration': blocked,
            'quality_conditioned_speed_ratio': speed,
            'disposition': 'withhold-quality-claim' if blocked else 'exploratory-observation-only',
            'automatic_pre_advice_default': 'not-adopted', 'historical_scores_overwritten': False}


def report(directory, audit_path):
    result = json.loads((directory / 'result.json').read_text())
    seal = json.loads((directory / 'seal.json').read_text())
    audit = json.loads(audit_path.read_text())
    if (result.get('kind') != 'synthesis-consultation-pilot-v1'
            or audit.get('kind') != 'f12-false-negative-calibration'
            or audit.get('case_id') != seal['fixture']['case']['case_id']
            or audit.get('revision') != seal['fixture']['case']['revision']):
        raise ValueError('case/revision mismatch')
    sources = [v for p, v in seal['code_sha256'].items() if p.endswith('/agent_duration_cases/f12.py')]
    if sources != [audit['case_source_sha256']]:
        raise ValueError('validity audit targets another oracle source')
    value = interpret(result, audit)
    value['source_sha256'] = {name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
                             for name in ('result.json', 'seal.json')}
    value['validity_sha256'] = hashlib.sha256(audit_path.read_bytes()).hexdigest()
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--validity', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    value = report(args.run, args.validity)
    with args.output.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

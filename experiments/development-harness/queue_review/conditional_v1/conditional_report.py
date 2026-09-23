"""Deterministic interpretation with stopped/usage/quality gates, separate from grading."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def interpret(result):
    conditions = result.get('conditions', {})
    eligible = (result.get('status') == 'completed' and result.get('all_writers_stopped') is True
                and result.get('private_credential_copy_removed') is True
                and bool(result.get('cleanup')) and all(r.get('removed') is True for r in result['cleanup'])
                and set(conditions) == {'control', 'informed'}
                and (result.get('initial_quality') or {}).get('status') == 'fail')
    rows = {}
    for name, row in conditions.items():
        seconds = row.get('execution_seconds')
        usage = row.get('usage', {})
        quality = row.get('quality') or {}
        valid = (row.get('status') == 'submitted' and row.get('usage_complete') is True
                 and type(seconds) in (int, float) and math.isfinite(seconds) and seconds > 0
                 and all(type(usage.get(k)) is int and usage[k] >= 0 for k in ('input_tokens', 'output_tokens'))
                 and quality.get('status') in ('pass', 'fail'))
        eligible &= valid
        rows[name] = {'status': row.get('status'), 'route': row.get('route'), 'seconds': seconds,
                      'usage': usage, 'quality': quality, 'draft_quality': row.get('draft_quality'),
                      'participants': len(row.get('actors', []))}
    ratio = None
    disposition = 'withhold'
    if eligible:
        a, b = rows['control'], rows['informed']
        both_pass = a['quality']['status'] == b['quality']['status'] == 'pass'
        if both_pass:
            ratio = b['seconds'] / a['seconds']
        improved = b['quality']['status'] == 'pass' and a['quality']['status'] == 'fail'
        if both_pass and ratio <= .9 and all(b['usage'][k] <= 1.1 * a['usage'][k] for k in ('input_tokens', 'output_tokens')):
            improved = True
        disposition = 'candidate-for-independent-confirmation' if improved else 'no-improvement-established'
    return {'kind': 'conditional-review-information-comparison-v1', 'observations': rows,
            'comparison_eligible': bool(eligible), 'quality_conditioned_time_ratio': ratio,
            'disposition': disposition, 'guidance_default': 'not-adopted',
            'general_effect_established': False, 'semantic_need_or_adoption': 'unknown',
            'historical_scores_overwritten': False}


def report(directory, output):
    with output.open('x') as stream:
        result = json.loads((directory / 'result.json').read_text())
        value = interpret(result)
        value['source_sha256'] = {name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
                                  for name in ('result.json', 'seal.json')}
        value['report_source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        value['private_evidence_directory'] = str(directory)
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps({'disposition': report(args.run, args.output)['disposition']}))

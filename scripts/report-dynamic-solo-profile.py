#!/usr/bin/env python3
"""Summarize every cell of a completed dynamic solo profile, without rescoring."""
import argparse
import hashlib
import json
from pathlib import Path

BANDS = ('ordinary', 'contended', 'severe')
FAMILIES = ('burst', 'scarce', 'cache', 'mixed')
SUMS = ('on_time_value', 'offered_value', 'unfinished_value', 'deadline_deficit',
        'busy_worker_ticks', 'interrupted_worker_ticks', 'unfinished_worker_ticks')


def summarize(results):
    expected = {f'qualification-{b}-{f}-{i}' for b in BANDS for f in FAMILIES for i in range(2)}
    indexed = {}
    for name in ('submission', 'reference'):
        raw = results[name]
        if raw.get('status') != 'completed' or not raw.get('all_containers_removed'):
            raise ValueError('incomplete assessment')
        rows = raw['cases']
        if len(rows) != 24 or {r['id'] for r in rows} != expected:
            raise ValueError('qualification coverage')
        if any(r['status'] != 'measured' or r['execution'].get('removed') is not True for r in rows):
            raise ValueError('unmeasured or unremoved case')
        indexed[name] = {r['id']: r['result'] for r in rows}
    for cid in expected:
        a, b = (indexed[n][cid] for n in ('submission', 'reference'))
        if a['offered_value'] != b['offered_value'] or {k: v['total'] for k, v in a['service_classes'].items()} != {k: v['total'] for k, v in b['service_classes'].items()}:
            raise ValueError('different populations')
    def group(ids):
        out = {}
        for name in indexed:
            rows = [indexed[name][cid] for cid in ids]
            values = {k: sum(r[k] for r in rows) for k in SUMS}
            values['critical_on_time'] = sum(r['service_classes'].get('16', {}).get('on_time', 0) for r in rows)
            values['critical_total'] = sum(r['service_classes'].get('16', {}).get('total', 0) for r in rows)
            values['on_time_fraction'] = values['on_time_value']/values['offered_value'] if values['offered_value'] else None
            values['critical_fraction'] = values['critical_on_time']/values['critical_total'] if values['critical_total'] else None
            out[name] = values
        out['difference'] = {k: out['submission'][k]-out['reference'][k] for k in (*SUMS, 'critical_on_time')}
        out['cases'] = sorted(ids)
        return out
    return {'cells': {f'{b}/{f}': group({f'qualification-{b}-{f}-{i}' for i in range(2)}) for b in BANDS for f in FAMILIES},
            'bands': {b: group({cid for cid in expected if cid.startswith('qualification-'+b+'-')}) for b in BANDS},
            'cases': {cid: {name: indexed[name][cid] for name in indexed} for cid in sorted(expected)}}


def report(root, output):
    source = root/'result.json'; raw = json.loads(source.read_text())
    value = {'kind': 'dynamic-solo-profile-summary-v1', 'status': 'withhold', 'raw_root': str(root),
             'raw_result_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
             'reporter_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'developer_start_attempts': 1 if raw.get('actor_started') else 0,
             'completed_developer_episodes': 1 if raw.get('actor', {}).get('status') == 'completed' else 0,
             'collaboration_effect_measured': False, 'outer_planning_usage': 'unmeasured',
             'first_attainment_time': 'unknown', 'confirmation_executed': raw.get('confirmation_executed'),
             'actor': raw.get('actor'), 'elapsed_seconds': raw.get('elapsed_seconds')}
    if raw['status'] == 'completed' and raw.get('owned_cleanup_confirmed') and raw.get('credential_copy_removed'):
        summary = summarize({n: raw['assessments'][n]['result'] for n in ('submission', 'reference')})
        # Keep every case metric; large traces/completion maps stay in the hashed raw report.
        for cases in summary['cases'].values():
            for name, row in cases.items(): cases[name] = {k: v for k, v in row.items() if k not in ('trace', 'completion_times')}
        value.update(status='completed', quality=summary, submission_sha256=raw['submission_sha256'])
    else:
        value['reason'] = raw.get('failure', raw['status'])
    value['assessment_coverage'] = {}
    for name in ('submission', 'reference'):
        path = root/f'assessment-{name}'/'result.json'
        coverage = {'registered': name in raw.get('assessments', {}), 'report_present': path.exists()}
        if path.exists():
            assessment = json.loads(path.read_text())
            rows = assessment.get('cases', [])
            coverage.update(raw_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                            measured=sum(r['status'] == 'measured' for r in rows),
                            unmeasured=sum(r['status'] == 'unmeasured' for r in rows),
                            invalid=sum(r['status'] == 'invalid-policy' for r in rows),
                            not_reached=24-len(rows), grader_reported_cleanup=assessment.get('all_containers_removed'),
                            failures=[{k: r.get(k) for k in ('id', 'status', 'failure', 'execution')}
                                      for r in rows if r['status'] != 'measured'])
        value['assessment_coverage'][name] = coverage
    # Raw actor messages/capability payloads stay private; usage and measured timings suffice.
    if value['actor']:
        value['actor'] = {k: value['actor'].get(k) for k in ('status', 'usage', 'development_seconds', 'commands', 'removed', 'image')}
    with output.open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False); f.write('\n')
    return value


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--run', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); report(a.run, a.output)

"""Authoring-only impossibility diagnostics; never an online performance target."""
import argparse
import hashlib
import json
from pathlib import Path

from runtime import validate


def bounds(s):
    validate(s)
    jobs = {j['id']: j for j in s['jobs']}
    earliest = {}
    while len(earliest) < len(jobs):
        for j in jobs.values():
            if j['id'] not in earliest and all(d in earliest for d in j['deps']):
                earliest[j['id']] = max([j['release'], *(earliest[d] for d in j['deps'])])+min(j['actual'].values())
    valued = [j for j in jobs.values() if j['weight'] > 0]
    impossible = [j['id'] for j in valued if earliest[j['id']] > j['deadline']]
    capacity = len(s['workers'])*s['horizon']-sum(o['end']-o['start'] for o in s['outages'])
    groups = {}
    for name, selected in [('all', valued), ('critical', [j for j in valued if j['weight'] == 16])]:
        needed = {j['id'] for j in selected}
        while True:
            expanded = needed | {d for jid in needed for d in jobs[jid]['deps']}
            if expanded == needed: break
            needed = expanded
        work = sum(min(jobs[j]['actual'].values()) for j in needed)
        memory_work = sum(min(jobs[j]['actual'].values())*jobs[j]['memory'] for j in needed)
        groups[name] = {'jobs': len(selected), 'required_worker_ticks_lower_bound': work,
                        'worker_ticks_available': capacity, 'required_memory_ticks_lower_bound': memory_work,
                        'memory_ticks_available': s['memory']*s['horizon'],
                        'all_completion_impossible_by_capacity': work > capacity or memory_work > s['memory']*s['horizon'],
                        'individual_deadline_impossible': sum(j['id'] in impossible for j in selected)}
    return {'id': s['id'], 'deadline_impossible_jobs': impossible, 'groups': groups,
            'feasibility_proven': False, 'online_attainability_proven': False}


def audit(source, output):
    plan = json.loads((source/'plan.json').read_text())
    path = source/'development.private.json'
    if hashlib.sha256(path.read_bytes()).hexdigest() != plan['case_sha256']:
        raise ValueError('case source mismatch')
    cases = json.loads(path.read_text())
    report = {'kind': 'dynamic-relaxed-bound-audit-v1', 'case_sha256': plan['case_sha256'],
              'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                                (Path(__file__), Path(__file__).with_name('runtime.py'))},
              'source_run': str(source), 'cases': [bounds(s) for s in cases],
              'uses_private_actual_durations': True, 'new_policy_executions': 0,
              'old_scores_changed': False, 'interpretation': 'Necessary bounds only; passing does not prove joint or online feasibility.'}
    with output.open('x') as f:
        json.dump(report, f, indent=2); f.write('\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--source-run', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); a = p.parse_args()
    audit(a.source_run, a.output)

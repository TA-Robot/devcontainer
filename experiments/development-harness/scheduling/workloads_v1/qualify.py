"""Calibrate real policy outcomes; freeze attainable reference targets before solo."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'v1'))
from evaluate import evaluate, save
from workloads import FAMILIES, suite


def aggregate(report):
    if report['status']!='completed' or not report['all_containers_removed']:
        raise ValueError('incomplete assessment')
    rows=report['cases']
    if len(rows)!=24 or len({r['id'] for r in rows})!=24:raise ValueError('population coverage')
    values={}
    for family in FAMILIES:
        group=[r for r in rows if '-'+family+'-' in r['id']]
        if len(group)!=6 or len({r['id'] for r in group})!=6:raise ValueError('coverage')
        successes=[r['result'] for r in group if r['id'].endswith('-success')]
        failures=[r['result'] for r in group if r['id'].endswith('-failure')]
        if any(r['status']!='completed' for r in successes) or any(r['status']!='blocked' for r in failures):raise ValueError('terminal mismatch')
        values[family]={'completion_sum':sum(r['completion_ticks'] for r in successes),
                        'blocker_sum':sum(r['blocker_ticks'] for r in failures),
                        'busy_sum':sum(r['result']['busy_worker_ticks'] for r in group)}
    return values


def run(output):
    output.mkdir(parents=True,mode=0o700,exist_ok=False)
    started=time.monotonic();reports={}
    paths={'fifo':HERE.parent/'v1/calibration/fifo.py',
           'rank_cache':HERE/'policies/rank_cache.py','risk_first':HERE/'policies/risk_first.py'}
    # Qualification is authoring data, never claimed as unseen confirmation.
    for split in ('development','qualification'):
        scenarios=suite(split);save(output/f'{split}.json',scenarios)
        reports[split]={}
        for name,path in paths.items():
            record=evaluate(path,scenarios,output/f'{split}-{name}')
            reports[split][name]=aggregate(record)
    sources=[HERE/'workloads.py',HERE/'qualify.py',*paths.values()]
    result={'kind':'scheduling-workload-qualification-v1','elapsed_seconds':time.monotonic()-started,
            'policy_source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
            'populations':reports,'target_policy':'rank_cache',
            'target_semantics':'Meet the fixed reference vector in every family; not a per-cell best-of portfolio.',
            'targets':{split:r['rank_cache'] for split,r in reports.items()},
            'strong_solo_difficulty_calibrated':False,'collaboration_effect_measured':False,
            'confirmation_executed':False,'live_provider_calls':0}
    save(output/'report.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    print(json.dumps({'seconds':run(a.output)['elapsed_seconds']}))

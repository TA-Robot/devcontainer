#!/usr/bin/env python3
"""Persist bounded, provider-free calibration in a fresh directory."""
import argparse
import hashlib
import json
from pathlib import Path
import time

from calibration_cases import cases
from evaluate import evaluate, save

HERE = Path(__file__).resolve().parent


def calibrate(output):
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    started = time.monotonic()
    reports = {}
    for name in ('fifo', 'scarcity'):
        report = evaluate(HERE/'calibration'/f'{name}.py', cases(), output/name)
        if report['status'] != 'completed' or not report['all_containers_removed']:
            raise RuntimeError('valid calibration did not complete')
        reports[name] = report
    actual = {name: [row['result'] for row in report['cases']] for name, report in reports.items()}
    assert actual['fifo'][0]['completion_ticks'] == 20
    assert actual['scarcity'][0]['completion_ticks'] == 10
    assert all(actual[name][1]['busy_worker_ticks'] == 4 and
               actual[name][1]['committed_worker_ticks'] == 12 for name in actual)
    mutants = {
        'score-spoof': 'import sys;sys.stdin.readline();print(\'{"status":"completed","completion_ticks":0}\',flush=True)',
        'duplicate-assignment': '''import sys,json
r=json.loads(sys.stdin.readline());print(json.dumps({'request_id':r['request_id'],'assignments':[{'job_id':'flex','worker_id':'cpu'}]*2}),flush=True)
''',
        'input-mutation': (HERE/'calibration/fifo.py').read_text().replace("state = request['state']", "state = request['state']\n    for j in state['jobs']:\n        for k in j['duration']: j['duration'][k] = 0"),
    }
    for name, code in mutants.items():
        source=output/f'{name}.py';source.write_text(code)
        report=evaluate(source,[cases()[0]],output/name)
        assert report['all_containers_removed']
        if name=='input-mutation':
            assert report['status']=='completed' and report['cases'][0]['result']['completion_ticks']==20
        else:
            assert report['status']=='withhold' and report['cases'][0]['status']=='invalid-policy'
        reports[name]=report
    sources=[*HERE.glob('*.py'), HERE/'TASK.md', *sorted((HERE/'calibration').glob('*.py'))]
    result={'kind':'scheduling-boundary-calibration-v1','status':'passed',
            'scope':'small constructed examples; not difficulty calibration',
            'hard_task_qualified':False,'live_provider_calls':0,
            'elapsed_seconds':time.monotonic()-started,
            'source_sha256':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
            'reports':{name:{'path':str(output/name/'result.json'),
                'sha256':hashlib.sha256((output/name/'result.json').read_bytes()).hexdigest(),
                'status':report['status'], 'all_containers_removed':report['all_containers_removed']} for name,report in reports.items()},
            'semantic_separation':{'fifo_completion_ticks':20,'scarcity_completion_ticks':10},
            'accounting':{'busy_worker_ticks_at_blocker':4,'committed_worker_ticks':12}}
    save(output/'calibration.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();print(json.dumps({'status':calibrate(a.output)['status']}))

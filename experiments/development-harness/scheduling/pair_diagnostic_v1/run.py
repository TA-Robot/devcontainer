"""Assess two fixed submitted artifacts after an accounting-withheld live pair.

No provider calls, no candidate selection, no promotion of the original result.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent


def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, x):
    with p.open('x') as f: json.dump(x, f, indent=2); f.write('\n')


class StopRequested(RuntimeError): pass


def copy_candidate(source, target):
    fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as f:
        if not stat.S_ISREG(os.fstat(f.fileno()).st_mode): raise ValueError('regular candidate required')
        data = f.read(65537)
    if not 0 < len(data) <= 65536: raise ValueError('candidate size')
    target.write_bytes(data); target.chmod(0o444)


def run(original, output):
    initial = read(original/'result.json'); control = read(original/'controller.json')
    if initial['status'] != 'withhold' or not all(control['recovery'].get(n) for n in ('solo','adaptive')):
        raise ValueError('requires withheld original pair and confirmed cleanup')
    for name in ('solo','adaptive'):
        actor = initial['actors'][name]
        if actor['bridge']['returncode'] != 0 or not actor['removed'] or not actor['credential_copy_removed']:
            raise ValueError('requires normally terminated developers and no credentials')
    output.mkdir(parents=True,mode=0o700,exist_ok=False)
    source = output/'source'; source.mkdir()
    frozen = original/'source/experiments/development-harness/scheduling/timing_diagnostic_v1'
    original_plan = read(original/'plan.json')
    sources = {}
    for name in ('runtime.py','transport.py','evaluate.py','TASK.md'):
        origin = frozen/name
        key = 'experiments/development-harness/scheduling/timing_diagnostic_v1/'+name
        if sha(origin) != original_plan['source_sha256'][key]: raise ValueError('original source changed')
        (source/name).write_bytes(origin.read_bytes()); (source/name).chmod(0o444)
        sources[name] = sha(source/name)
    candidates = {}
    for name in ('solo','adaptive'):
        copy_candidate(original/'actors'/name/'work/submission.py',output/(name+'.py'))
        candidates[name] = sha(output/(name+'.py'))
    if candidates['solo'] != initial['submission_sha256']['solo']: raise ValueError('solo seal changed')
    selection = original/'actors/adaptive/work/SELECTION.md'
    declared = re.search(r'Final source SHA256: `([0-9a-f]{64})`',selection.read_text())
    if declared is None or declared[1] != candidates['adaptive']: raise ValueError('adaptive declared submission changed')
    cases_path = output/'qualification.private.json'
    cases_path.write_bytes((original/'qualification.private.json').read_bytes())
    cases = read(cases_path)
    if len(cases)!=24 or len({c['id'] for c in cases})!=24: raise ValueError('coverage')
    (output/'controller-source.py').write_bytes((HERE/'run.py').read_bytes())
    reporter_path = original/'source/scripts/report-dynamic-solo-profile.py'
    if sha(reporter_path) != original_plan['source_sha256']['scripts/report-dynamic-solo-profile.py']:
        raise ValueError('reporter changed')
    (output/'reporter.py').write_bytes(reporter_path.read_bytes())
    save(output/'plan.json', {'kind':'fixed-pair-artifact-diagnostic-v1','original':str(original),
        'original_result_sha256':sha(original/'result.json'),'original_controller_sha256':sha(original/'controller.json'),
        'candidate_sha256':candidates,'adaptive_selection_sha256':sha(selection),'source_sha256':sources,
        'cases_sha256':sha(cases_path),'controller_sha256':sha(output/'controller-source.py'),
        'reporter_sha256':sha(output/'reporter.py'),'assessments':2,'seconds_each':900,
        'stop_on_first_failure':True,'live_provider_calls':0,'original_status_remains':'withhold'})
    result={'status':'withhold','original_status':'withhold','diagnostic_only':True,'cost_comparison_admitted':False,
            'live_provider_calls':0,'assessments':{}}
    began=time.monotonic()
    def stop(signum,frame): raise StopRequested('diagnostic interrupted')
    handlers={s:signal.signal(s,stop) for s in (signal.SIGINT,signal.SIGTERM)}
    try:
        for name in ('solo','adaptive'):
            folder=output/('assessment-'+name);row={'status':'withhold','cleanup':'unknown'}
            result['assessments'][name]=row;process=None
            try:
                process=subprocess.Popen([sys.executable,str(source/'evaluate.py'),'--candidate',str(output/(name+'.py')),
                    '--scenarios',str(cases_path),'--output',str(folder)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                process.communicate(timeout=900)
            finally:
                if process is not None and process.poll() is None:
                    process.terminate()
                    try:process.communicate(timeout=30)
                    except subprocess.TimeoutExpired:process.kill();process.communicate(timeout=3)
                if (folder/'result.json').exists():
                    row['result']=read(folder/'result.json')
                    if row['result'].get('all_containers_removed'):row['cleanup']='confirmed'
            raw=row.get('result',{});seal=read(folder/'seal.json')
            expected=hashlib.sha256(json.dumps(cases,sort_keys=True,allow_nan=False).encode()).hexdigest()
            if (process.returncode!=0 or raw.get('status')!='completed' or row['cleanup']!='confirmed'
                or len(raw['cases'])!=24 or {r['id'] for r in raw['cases']}!={c['id'] for c in cases}
                or seal['candidate_sha256']!=candidates[name] or seal['scenario_sha256']!=expected
                or seal['source_sha256']!=sources):raise ValueError('incomplete assessment')
            row['status']='completed'
        spec=importlib.util.spec_from_file_location('diagnostic_reporter',output/'reporter.py')
        reporter=importlib.util.module_from_spec(spec);spec.loader.exec_module(reporter)
        quality=reporter.summarize({'submission':result['assessments']['adaptive']['result'],
                                  'reference':result['assessments']['solo']['result']})
        for section in ('cells','bands','cases'):
            for row in quality[section].values():
                row['adaptive']=row.pop('submission');row['solo']=row.pop('reference')
        save(output/'quality.json',quality)
        result['status']='completed'
    except (StopRequested,OSError,ValueError,KeyError,subprocess.SubprocessError) as exc:
        result['failure']=type(exc).__name__+': '+str(exc)
    finally:
        result['elapsed_seconds']=time.monotonic()-began
        result['all_containers_removed']=bool(result['assessments']) and all(r['cleanup']=='confirmed' for r in result['assessments'].values())
        save(output/'result.json',result)
        for s,h in handlers.items():signal.signal(s,h)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--original',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=run(a.original,a.output);print(json.dumps({'status':r['status']}))
    raise SystemExit(0 if r['status']=='completed' else 1)

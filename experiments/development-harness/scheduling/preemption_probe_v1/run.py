"""Run the missing-usage notification probe using a copied, frozen actor tree."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

HERE=Path(__file__).resolve().parent


def run(original,output,*,control=False):
    output.mkdir(parents=True,mode=0o700,exist_ok=False)
    clone=output/'source'
    shutil.copytree(original/'source',clone)
    actor_dir=clone/'experiments/development-harness/scheduling/native_actor_v1'
    probe=actor_dir/'fake_adaptive.py';probe.chmod(0o644);probe.write_bytes((HERE/'probe.py').read_bytes());probe.chmod(0o444)
    spec=importlib.util.spec_from_file_location('preemption_actor',actor_dir/'actor.py')
    actor=importlib.util.module_from_spec(spec);spec.loader.exec_module(actor)
    actor.prepare_public(output/'public')
    result=actor.run(output/'actor',output/'public',condition='adaptive',prompt='Finite notification probe.',
                     fake=True,fake_mode='control' if control else 'preemption',seconds=30)
    fixture=json.loads((output/'actor/stdout.private.txt').read_text())
    failures=result.get('bridge',{}).get('accounting',{}).get('failures',[])
    passed=(result['status']=='withhold' and result['removed'] and fixture['partial_started'] and fixture['child_done']
        and result['bridge']['returncode']==0 and fixture['delayed_terminal_attempted']
        and any(r['partial'] and r.get('delayed_terminal_attempted') for r in fixture['requests'])
        and any('unmatched or unknown token observation' in r['failure'] for r in failures))
    if control:
        passed=(result['status']=='completed' and result['removed'] and fixture['partial_started']
                and fixture['delayed_terminal_attempted'] and not failures)
    completed=(result['removed'] and result.get('bridge',{}).get('returncode')==0
               and fixture['partial_started'] and fixture['delayed_terminal_attempted'])
    report={'status':'completed' if completed else 'withhold','original_pair_status_unchanged':True,
        'notification_hypothesis_reproduced':passed if not control else None,'control_passed':passed if control else None,
        'live_provider_calls':0,'actor':result,'fixture':fixture,
        'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.py')}}
    with (output/'result.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--original',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--control',action='store_true')
    a=p.parse_args();r=run(a.original,a.output,control=a.control);print(json.dumps({'status':r['status']}))
    raise SystemExit(0 if r['status']=='completed' else 1)

"""Public development feedback. Runs only inside the dedicated actor container."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

from runtime import simulate, validate
from transport import Policy


class LocalPolicy(Policy):
    def __enter__(self):
        self.started=time.monotonic();self.deadline=self.started+self.seconds
        self.process=subprocess.Popen(['python3','-u',str(self.snapshot)],stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':'/nonexistent','PYTHONDONTWRITEBYTECODE':'1'})
        for stream in (self.process.stdin,self.process.stdout,self.process.stderr):os.set_blocking(stream.fileno(),False)
        return self
    def close(self):
        self.process.kill();self.process.wait(timeout=3)
        for stream in (self.process.stdin,self.process.stdout,self.process.stderr):stream.close()
        self.record['removed']=True


def main():
    # This tool is never a host-side route for running candidate code.
    if not Path('/public/ACTOR_ONLY').is_file() or not Path('/.dockerenv').exists():
        raise RuntimeError('dedicated actor environment required')
    p=argparse.ArgumentParser();p.add_argument('--candidate',required=True,type=Path)
    p.add_argument('--cases',type=Path,default=Path('/public/development.json'))
    p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    rows=[]
    for case in json.loads(a.cases.read_text()):
        validate(case)
        try:
            with LocalPolicy(a.candidate) as policy:value=simulate(case,policy.choose)
            rows.append({'id':case['id'],'status':'measured','result':value})
        except Exception as e:rows.append({'id':case['id'],'status':'invalid','reason':type(e).__name__+': '+str(e)})
    families={}
    for name in ('chain','frontier','scarcity','cache'):
        group=[r for r in rows if '-'+name+'-' in r['id']]
        if group and all(r['status']=='measured' for r in group):
            families[name]={'completion_sum':sum(r['result']['completion_ticks'] or 0 for r in group),
                            'blocker_sum':sum(r['result']['blocker_ticks'] or 0 for r in group),
                            'busy_sum':sum(r['result']['busy_worker_ticks'] for r in group)}
    result={'valid':all(r['status']=='measured' for r in rows),'families':families,'cases':rows}
    with a.output.open('x') as stream:json.dump(result,stream,indent=2)
    print(json.dumps({'valid':result['valid'],'families':families,'details':str(a.output)}))


if __name__=='__main__':main()

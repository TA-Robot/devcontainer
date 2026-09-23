"""Authoring reference: downstream rank plus cache-aware resource assignment."""
import json
import sys


def choose(state):
    jobs={j['id']:j for j in state['jobs']}
    children={name:[] for name in jobs}
    for job in jobs.values():
        for parent in job['deps']:children[parent].append(job['id'])
    ranks={}
    def rank(name):
        if name not in ranks:
            ranks[name]=min(jobs[name]['duration'].values())+max((rank(n) for n in children[name]),default=0)
        return ranks[name]
    for name in jobs:rank(name)
    free=list(state['idle_workers']);result=[]
    ready=list(state['ready'])
    while free and ready:
        choices=[]
        for job in ready:
            compatible=[w for w in free if w['kind'] in job['compatible']]
            for w in compatible:
                duration=job['duration'][w['kind']]+(state['cold_start'] if w['last_cache']!=job['cache'] else 0)
                score=ranks[job['id']]/duration/len(compatible)
                choices.append((score,-duration,job['id'],w['id'],job,w))
        if not choices:break
        _,_,_,_,job,w=max(choices,key=lambda row:row[:4])
        result.append({'job_id':job['id'],'worker_id':w['id']})
        ready.remove(job);free.remove(w)
    return result


for line in sys.stdin:
    value=json.loads(line)
    print(json.dumps({'request_id':value['request_id'],'assignments':choose(value['state'])}),flush=True)

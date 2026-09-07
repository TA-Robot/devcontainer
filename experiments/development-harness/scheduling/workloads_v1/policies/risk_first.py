"""Authoring contrast: prioritize failure discovery per unit execution time."""
import json
import sys
for line in sys.stdin:
    value=json.loads(line);state=value['state'];free=list(state['idle_workers']);ready=list(state['ready']);result=[]
    while free and ready:
        choices=[]
        for job in ready:
            for worker in free:
                if worker['kind'] in job['compatible']:
                    duration=job['duration'][worker['kind']]+(state['cold_start'] if worker['last_cache']!=job['cache'] else 0)
                    choices.append((job['failure_probability']/duration,-duration,job['id'],worker['id'],job,worker))
        if not choices:break
        _,_,_,_,job,worker=max(choices,key=lambda row:row[:4])
        result.append({'job_id':job['id'],'worker_id':worker['id']});ready.remove(job);free.remove(worker)
    print(json.dumps({'request_id':value['request_id'],'assignments':result}),flush=True)

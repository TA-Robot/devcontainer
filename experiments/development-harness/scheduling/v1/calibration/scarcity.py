"""Different valid calibration policy: schedule least-compatible jobs first."""
import json
import sys
for line in sys.stdin:
    request = json.loads(line)
    state = request['state']
    free = list(state['idle_workers'])
    result = []
    for job in sorted(state['ready'], key=lambda j: (len(j['compatible']), j['id'])):
        worker = next((w for w in free if w['kind'] in job['compatible']), None)
        if worker:
            result.append({'job_id': job['id'], 'worker_id': worker['id']})
            free.remove(worker)
    print(json.dumps({'request_id': request['request_id'], 'assignments': result}), flush=True)

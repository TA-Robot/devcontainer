"""Calibration baseline. Source is never a hidden reference for a live actor."""
import json
import sys
for line in sys.stdin:
    request = json.loads(line)
    state = request['state']
    free = list(state['idle_workers'])
    result = []
    for job in state['ready']:
        worker = next((w for w in free if w['kind'] in job['compatible']), None)
        if worker:
            result.append({'job_id': job['id'], 'worker_id': worker['id']})
            free.remove(worker)
    print(json.dumps({'request_id': request['request_id'], 'assignments': result}), flush=True)

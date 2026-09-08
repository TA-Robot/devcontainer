import json
import sys

for line in sys.stdin:
    request = json.loads(line); s = request['state']; free = s['memory_free']; used = set(); actions = []
    for w in sorted(s['idle_workers'], key=lambda w: (sum(w['kind'] in j['estimate'] for j in s['ready']), w['id'])):
        for j in sorted(s['ready'], key=lambda j: (j['release'], j['id'])):
            if j['id'] not in used and w['kind'] in j['estimate'] and j['memory'] <= min(free, w['memory']):
                actions.append({'job_id': j['id'], 'worker_id': w['id']}); used.add(j['id']); free -= j['memory']; break
    print(json.dumps({'request_id': request['request_id'], 'assignments': actions}), flush=True)

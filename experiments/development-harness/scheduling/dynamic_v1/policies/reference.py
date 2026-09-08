"""Public-information reference approaches, not an optimum or target oracle."""
import json
import sys


def choose(s, mode='lookahead'):
    jobs = {j['id']: j for j in s['jobs']}
    ready = s['ready']
    workers = sorted(s['idle_workers'], key=lambda w: (sum(w['kind'] in j['estimate'] for j in ready), w['id']))
    free = s['memory_free']
    if mode in ('fifo', 'edf'):
        order = sorted(ready, key=lambda j: (j['release'] if mode == 'fifo' else j['deadline'], j['id']))
        result = []
        for w in workers:
            eligible = [j for j in order if w['kind'] in j['estimate'] and j['memory'] <= min(free, w['memory'])]
            if eligible:
                j = eligible[0]; order.remove(j); free -= j['memory']
                result.append({'job_id': j['id'], 'worker_id': w['id']})
        return result
    children = {jid: [] for jid in jobs}
    for j in jobs.values():
        for dep in j['deps']:
            children[dep].append(j['id'])
    rank = {}
    def downstream(jid):
        if jid not in rank:
            j = jobs[jid]
            rest = [downstream(c) for c in children[jid]]
            rank[jid] = (max([j['weight'], *(r[0] for r in rest)]), min([j['deadline'], *(r[1] for r in rest)]),
                         min(j['estimate'].values())+s['cold_start']+max([0, *(r[2] for r in rest)]))
        return rank[jid]
    def score(j, w):
        weight, deadline, remaining = downstream(j['id'])
        duration = j['estimate'][w['kind']]+(s['cold_start'] if w['last_cache'] != j['cache'] else 0)
        slack = deadline-s['now']-remaining
        urgency = 1+min(4, remaining/max(1, deadline-s['now']))
        feasibility = .15 if slack < -remaining else 1
        return max(.1, weight)*urgency*feasibility/max(1, duration)
    if mode == 'density':
        result, used = [], set()
        for w in workers:
            eligible = [j for j in ready if j['id'] not in used and w['kind'] in j['estimate'] and j['memory'] <= min(free, w['memory'])]
            if eligible:
                j = max(eligible, key=lambda j: score(j, w))
                result.append({'job_id': j['id'], 'worker_id': w['id']}); used.add(j['id']); free -= j['memory']
        return result
    # Bounded beam over joint assignments; includes idle choices and memory opportunity cost.
    beam = [(0., [], frozenset(), free)]
    for w in workers:
        candidates = sorted([j for j in ready if w['kind'] in j['estimate'] and j['memory'] <= w['memory']], key=lambda j: score(j, w), reverse=True)[:8]
        expanded = []
        for value, actions, used, available in beam:
            expanded.append((value, actions, used, available))
            for j in candidates:
                if j['id'] in used or j['memory'] > available:
                    continue
                # Prefer scarce kinds for jobs that need them; penalize memory occupation time.
                alternatives = sum(other['kind'] in j['estimate'] for other in workers)
                value_add = score(j, w)*(1+1/max(1, alternatives))/(1+j['memory']/max(1, s['memory']))
                expanded.append((value+value_add, actions+[{'job_id': j['id'], 'worker_id': w['id']}], used | {j['id']}, available-j['memory']))
        beam = sorted(expanded, key=lambda b: b[0], reverse=True)[:16]
    return beam[0][1]


if __name__ == '__main__':
    for line in sys.stdin:
        request = json.loads(line)
        print(json.dumps({'request_id': request['request_id'], 'assignments': choose(request['state'], globals().get('MODE', 'lookahead'))}), flush=True)

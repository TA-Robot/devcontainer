"""Authoritative online scheduling clock; no future events in observations."""
import copy
import json
import math


class Invalid(ValueError):
    pass


def require(value, message):
    if not value:
        raise Invalid(message)


def decode(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    def nonfinite(_):
        raise Invalid('nonfinite JSON')
    return json.loads(data, object_pairs_hook=pairs, parse_constant=nonfinite)


def integer(value, low, high):
    return type(value) is int and low <= value <= high


def label(value):
    return isinstance(value, str) and 0 < len(value) <= 64


def validate(s):
    require(isinstance(s, dict) and set(s) == {'id', 'horizon', 'heartbeat', 'memory', 'cold_start', 'jobs', 'workers', 'outages'}, 'scenario schema')
    require(label(s['id']), 'scenario id')
    require(integer(s['horizon'], 1, 10000) and integer(s['heartbeat'], 1, 100), 'clock bounds')
    require(integer(s['memory'], 1, 100000) and integer(s['cold_start'], 0, 1000), 'resource bounds')
    require(isinstance(s['workers'], list) and 1 <= len(s['workers']) <= 32, 'workers')
    workers = {}
    for w in s['workers']:
        require(isinstance(w, dict) and set(w) == {'id', 'kind', 'memory'}, 'worker schema')
        require(label(w['id']) and label(w['kind']) and integer(w['memory'], 1, 100000), 'worker values')
        require(w['id'] not in workers, 'duplicate worker')
        workers[w['id']] = w
    require(isinstance(s['jobs'], list) and 1 <= len(s['jobs']) <= 2048, 'jobs')
    jobs = {}
    for j in s['jobs']:
        require(isinstance(j, dict) and set(j) == {'id', 'release', 'deadline', 'weight', 'deps', 'estimate', 'actual', 'memory', 'cache'}, 'job schema')
        require(label(j['id']) and j['id'] not in jobs and label(j['cache']), 'job identity')
        require(integer(j['release'], 0, s['horizon']-1) and integer(j['deadline'], j['release']+1, s['horizon']), 'job times')
        require(integer(j['weight'], 0, 100) and integer(j['memory'], 1, s['memory']), 'job resources')
        require(isinstance(j['deps'], list) and all(label(d) for d in j['deps']) and len(set(j['deps'])) == len(j['deps']), 'dependencies')
        require(isinstance(j['estimate'], dict) and isinstance(j['actual'], dict) and j['estimate'] and set(j['estimate']) == set(j['actual']), 'duration schema')
        for kind, estimate in j['estimate'].items():
            require(label(kind) and integer(estimate, 1, 10000) and integer(j['actual'][kind], 1, 10000), 'duration values')
            require(any(w['kind'] == kind and w['memory'] >= j['memory'] for w in workers.values()), 'compatible memory')
        jobs[j['id']] = j
    reached = set()
    for j in jobs.values():
        require(all(d in jobs and jobs[d]['release'] <= j['release'] for d in j['deps']), 'dependency release')
    while True:
        nxt = reached | {j['id'] for j in jobs.values() if set(j['deps']) <= reached}
        if nxt == reached:
            break
        reached = nxt
    require(reached == set(jobs), 'dependency cycle')
    require(isinstance(s['outages'], list) and len(s['outages']) <= 256, 'outages')
    intervals = {w: [] for w in workers}
    for o in s['outages']:
        require(isinstance(o, dict) and set(o) == {'worker_id', 'start', 'end'}, 'outage schema')
        require(isinstance(o['worker_id'], str) and o['worker_id'] in workers, 'outage worker')
        require(integer(o['start'], 0, s['horizon']-1) and integer(o['end'], o['start']+1, s['horizon']), 'outage times')
        intervals[o['worker_id']].append((o['start'], o['end']))
    for spans in intervals.values():
        spans.sort()
        require(all(a[1] <= b[0] for a, b in zip(spans, spans[1:])), 'overlapping outage')


def simulate(scenario, choose):
    validate(scenario)
    s = copy.deepcopy(scenario)
    jobs = {j['id']: j for j in s['jobs']}
    workers = {w['id']: {**w, 'last_cache': None, 'online': True} for w in s['workers']}
    completed, running, attempts = {}, {}, {j: 0 for j in jobs}
    memory_used = busy = wasted = decisions = 0
    now = 0
    trace = []
    calendar = {s['horizon'], *range(0, s['horizon'], s['heartbeat']), *(j['release'] for j in jobs.values())}
    calendar.update(t for o in s['outages'] for t in (o['start'], o['end']))
    times = sorted(calendar)
    cursor = 0
    while True:
        events = []
        # A completion exactly at outage start succeeds; recovery precedes a new outage.
        for wid, r in list(running.items()):
            if r['finish'] == now:
                completed[r['job_id']] = now
                workers[wid]['last_cache'] = jobs[r['job_id']]['cache']
                memory_used -= jobs[r['job_id']]['memory']
                del running[wid]
                events.append({'type': 'completed', 'job_id': r['job_id'], 'worker_id': wid, 'elapsed': now-r['start']})
        for o in s['outages']:
            if o['end'] == now:
                workers[o['worker_id']]['online'] = True
                events.append({'type': 'recovered', 'worker_id': o['worker_id']})
        for o in s['outages']:
            if o['start'] == now:
                wid = o['worker_id']
                workers[wid].update(online=False, last_cache=None)
                if wid in running:
                    r = running.pop(wid)
                    lost = now-r['start']
                    wasted += lost
                    memory_used -= jobs[r['job_id']]['memory']
                    events.append({'type': 'interrupted', 'job_id': r['job_id'], 'worker_id': wid, 'elapsed': lost})
                events.append({'type': 'unavailable', 'worker_id': wid})
        if now == s['horizon']:
            break
        active_ids = {r['job_id'] for r in running.values()}
        visible = [{k: copy.deepcopy(v) for k, v in j.items() if k != 'actual'} for j in jobs.values() if j['release'] <= now]
        ready = [j for j in visible if j['id'] not in completed and j['id'] not in active_ids and set(j['deps']) <= completed.keys()]
        idle = [w for wid, w in workers.items() if w['online'] and wid not in running]
        # Called even when no assignment is possible: events and time are public observations.
        state = {'now': now, 'horizon': s['horizon'], 'heartbeat': s['heartbeat'], 'cold_start': s['cold_start'],
                 'memory': s['memory'], 'memory_free': s['memory']-memory_used, 'jobs': visible,
                 'workers': list(workers.values()), 'ready': ready, 'idle_workers': idle,
                 'completed': completed, 'attempts': {j['id']: attempts[j['id']] for j in visible},
                 'running': [{k: v for k, v in r.items() if k != 'finish'} for r in running.values()], 'events': events}
        action = choose(copy.deepcopy(state))
        require(isinstance(action, list) and len(action) <= len(idle), 'action list')
        ready_ids, idle_ids = {j['id'] for j in ready}, {w['id'] for w in idle}
        used_jobs, used_workers = set(), set()
        for a in action:
            require(isinstance(a, dict) and set(a) == {'job_id', 'worker_id'}, 'assignment schema')
            jid, wid = a['job_id'], a['worker_id']
            require(isinstance(jid, str) and isinstance(wid, str), 'assignment ids')
            require(jid in ready_ids and wid in idle_ids and jid not in used_jobs and wid not in used_workers, 'ready/idle/unique')
            j, w = jobs[jid], workers[wid]
            require(w['kind'] in j['estimate'] and j['memory'] <= w['memory'], 'compatibility')
            require(memory_used+j['memory'] <= s['memory'], 'shared memory capacity')
            cost = j['actual'][w['kind']] + (s['cold_start'] if w['last_cache'] != j['cache'] else 0)
            running[wid] = {'job_id': jid, 'worker_id': wid, 'start': now, 'finish': now+cost}
            memory_used += j['memory']; attempts[jid] += 1
            used_jobs.add(jid); used_workers.add(wid)
        trace.append({'now': now, 'events': events, 'assignments': copy.deepcopy(action), 'memory_used': memory_used})
        decisions += 1
        while cursor < len(times) and times[cursor] <= now:
            cursor += 1
        nxt = min([times[cursor], *(r['finish'] for r in running.values())])
        busy += (nxt-now)*len(running)
        now = nxt
    valued = [j for j in jobs.values() if j['weight'] > 0]
    response = sorted(completed[j['id']]-j['release'] for j in valued if j['id'] in completed)
    classes = {}
    for weight in sorted({j['weight'] for j in valued}):
        group = [j for j in valued if j['weight'] == weight]
        classes[str(weight)] = {'total': len(group), 'on_time': sum(j['id'] in completed and completed[j['id']] <= j['deadline'] for j in group)}
    return {'status': 'completed', 'on_time_value': sum(j['weight'] for j in valued if j['id'] in completed and completed[j['id']] <= j['deadline']),
            'offered_value': sum(j['weight'] for j in valued), 'completed_value': sum(j['weight'] for j in valued if j['id'] in completed),
            'unfinished_value': sum(j['weight'] for j in valued if j['id'] not in completed),
            'deadline_deficit': sum(j['weight']*max(0, completed.get(j['id'], s['horizon'])-j['deadline']) for j in valued),
            'response_p95_completed': response[math.ceil(len(response)*.95)-1] if response else None,
            'response_sample_count': len(response), 'service_classes': classes,
            'busy_worker_ticks': busy, 'interrupted_worker_ticks': wasted,
            'unfinished_worker_ticks': sum(now-r['start'] for r in running.values()),
            'attempts': sum(attempts.values()), 'decisions': decisions, 'completion_times': completed, 'trace': trace}

"""Evaluator-owned integer-tick scheduling. Candidate actions never contain scores."""
import copy
import hashlib
import json


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
    def nonfinite(value):
        raise Invalid('nonfinite JSON')
    return json.loads(data, object_pairs_hook=pairs, parse_constant=nonfinite)


def validate(scenario):
    require(isinstance(scenario, dict) and set(scenario) == {'id', 'jobs', 'workers', 'cold_start', 'failing_jobs'}, 'scenario schema')
    require(isinstance(scenario['id'], str), 'scenario id')
    require(type(scenario['cold_start']) is int and 0 <= scenario['cold_start'] <= 10000, 'cold start')
    jobs, workers = scenario['jobs'], scenario['workers']
    require(isinstance(jobs, list) and 1 <= len(jobs) <= 256, 'job count')
    require(isinstance(workers, list) and 1 <= len(workers) <= 32, 'worker count')
    ids, worker_ids, kinds = set(), set(), set()
    for worker in workers:
        require(isinstance(worker, dict) and set(worker) == {'id', 'kind'}, 'worker schema')
        require(all(isinstance(v, str) and 0 < len(v) <= 64 for v in worker.values()), 'worker values')
        require(worker['id'] not in worker_ids, 'duplicate worker')
        worker_ids.add(worker['id']); kinds.add(worker['kind'])
    for job in jobs:
        require(isinstance(job, dict) and set(job) == {'id', 'deps', 'duration', 'compatible', 'cache', 'failure_probability'}, 'job schema')
        require(isinstance(job['id'], str) and 0 < len(job['id']) <= 64 and job['id'] not in ids, 'job id')
        ids.add(job['id'])
        require(isinstance(job['cache'], str) and len(job['cache']) <= 64, 'cache')
        for key in ('deps', 'compatible'):
            require(isinstance(job[key], list) and all(isinstance(v, str) for v in job[key]) and len(set(job[key])) == len(job[key]), key)
        require(job['compatible'] and set(job['compatible']) <= kinds, 'compatibility')
        require(isinstance(job['duration'], dict) and set(job['duration']) == set(job['compatible']), 'durations')
        require(all(type(v) is int and 1 <= v <= 10000 for v in job['duration'].values()), 'positive integer ticks required')
        probability = job['failure_probability']
        require(type(probability) in (int, float) and 0 <= probability <= 1, 'probability')
    reached = set()
    for job in jobs:
        require(set(job['deps']) <= ids and job['id'] not in job['deps'], 'dependency')
    while True:
        nxt = {j['id'] for j in jobs if set(j['deps']) <= reached} | reached
        if nxt == reached:
            break
        reached = nxt
    require(reached == ids, 'cyclic graph')
    failing = scenario['failing_jobs']
    require(isinstance(failing, list) and all(isinstance(v, str) for v in failing) and len(set(failing)) == len(failing) and set(failing) <= ids, 'failing jobs')


def simulate(scenario, choose):
    validate(scenario)
    scenario = copy.deepcopy(scenario)
    jobs = {j['id']: j for j in scenario['jobs']}
    workers = {w['id']: {**w, 'last_cache': None} for w in scenario['workers']}
    started, completed, running = set(), set(), {}
    now, busy_ticks, committed_ticks, decisions = 0, 0, 0, 0
    trace = []
    while len(completed) < len(jobs):
        finished = [r for r in running.values() if r['finish'] == now]
        failed = sorted(r['job_id'] for r in finished if r['job_id'] in scenario['failing_jobs'])
        for r in finished:
            del running[r['worker_id']]
            workers[r['worker_id']]['last_cache'] = jobs[r['job_id']]['cache']
            if r['job_id'] not in failed:
                completed.add(r['job_id'])
        if failed:
            status = 'blocked'
            break
        if len(completed) == len(jobs):
            status = 'completed'
            break
        ready = [j for j in jobs.values() if j['id'] not in started and set(j['deps']) <= completed]
        idle = [w for wid, w in workers.items() if wid not in running]
        if ready and idle:
            observation = {'now': now, 'jobs': list(jobs.values()), 'workers': list(workers.values()),
                           'ready': ready, 'idle_workers': idle, 'completed': sorted(completed),
                           'running': list(running.values()), 'cold_start': scenario['cold_start']}
            # Even trusted in-process calibration callbacks cannot mutate evaluator state.
            action = choose(copy.deepcopy(observation))
            require(isinstance(action, list) and len(action) <= len(idle), 'action list')
            used_jobs, used_workers = set(), set()
            ready_ids, idle_ids = {j['id'] for j in ready}, {w['id'] for w in idle}
            for assignment in action:
                require(isinstance(assignment, dict) and set(assignment) == {'job_id', 'worker_id'}, 'assignment schema')
                jid, wid = assignment['job_id'], assignment['worker_id']
                require(isinstance(jid, str) and isinstance(wid, str), 'assignment ids')
                require(jid in ready_ids and wid in idle_ids and jid not in used_jobs and wid not in used_workers, 'ready/idle/unique')
                job, worker = jobs[jid], workers[wid]
                require(worker['kind'] in job['compatible'], 'incompatible worker')
                duration = job['duration'][worker['kind']] + (scenario['cold_start'] if worker['last_cache'] != job['cache'] else 0)
                running[wid] = {'job_id': jid, 'worker_id': wid, 'start': now, 'finish': now + duration}
                committed_ticks += duration
                started.add(jid); used_jobs.add(jid); used_workers.add(wid)
            trace.append({'now': now, 'action': copy.deepcopy(action)})
            decisions += 1
            require(decisions <= len(jobs) * 2, 'decision bound')
        require(running, 'deadlock')
        next_time = min(r['finish'] for r in running.values())
        busy_ticks += (next_time - now) * len(running)
        now = next_time
    return {'status': status, 'completion_ticks': now if status == 'completed' else None,
            'blocker_ticks': now if status == 'blocked' else None, 'busy_worker_ticks': busy_ticks,
            'committed_worker_ticks': committed_ticks, 'assignments': len(started), 'decisions': decisions,
            'trace': trace}

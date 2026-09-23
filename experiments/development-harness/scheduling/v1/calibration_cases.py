"""Authoring-only small calibration, not the hard-task or heldout population."""


def job(name, duration, deps=(), kinds=('cpu', 'gpu')):
    return {'id': name, 'deps': list(deps), 'duration': {k: duration for k in kinds},
            'compatible': list(kinds), 'cache': 'same', 'failure_probability': 0.2}


def cases():
    workers = [{'id': 'cpu', 'kind': 'cpu'}, {'id': 'gpu', 'kind': 'gpu'}]
    return [
        {'id': 'scarce-worker', 'workers': workers, 'cold_start': 0, 'failing_jobs': [],
         'jobs': [job('flex', 10), job('cpu-only', 10, kinds=('cpu',))]},
        {'id': 'blocker-accounting', 'workers': workers, 'cold_start': 0, 'failing_jobs': ['fast'],
         'jobs': [job('fast', 2), job('long', 10)]},
        {'id': 'exact-events-cache', 'workers': [workers[0]], 'cold_start': 3, 'failing_jobs': [],
         'jobs': [job('first', 1, kinds=('cpu',)), job('second', 1, ('first',), ('cpu',))]},
    ]

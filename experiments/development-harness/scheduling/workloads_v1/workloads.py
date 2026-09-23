"""Versioned heterogeneous workloads; no collaborative result influences selection."""
import random

FAMILIES = ('chain', 'frontier', 'scarcity', 'cache')
SPLITS = {'development': 1729, 'qualification': 2718, 'confirmation': 31415}


def generate(family, seed):
    rng = random.Random(seed)
    count = {'chain': 32, 'frontier': 72, 'scarcity': 48, 'cache': 48}[family]
    workers = [{'id': 'w'+str(i), 'kind': 'gpu' if i == 0 else 'cpu'} for i in range(4)]
    if family == 'frontier':
        workers += [{'id': 'w'+str(i), 'kind': 'gpu' if i == 4 else 'cpu'} for i in range(4, 8)]
    jobs = []
    names = ['j'+str(i) for i in range(count)]
    rng.shuffle(names)
    for index, name in enumerate(names):
        if family == 'chain':
            deps = [names[index-1]] if index and index % 4 else []
        elif family == 'frontier':
            deps = [] if index < count*3//4 else rng.sample(names[:count//2], 3)
        else:
            deps = rng.sample(names[:index], min(index, rng.choice([0, 1, 2])))
        kinds = ['cpu', 'gpu']
        if family == 'scarcity' and rng.random() < .35:
            kinds = [rng.choice(['cpu', 'gpu'])]
        cpu = rng.randint(4, 50)
        duration = {k: cpu if k == 'cpu' else rng.randint(2, 35) for k in kinds}
        jobs.append({'id': name, 'deps': deps, 'duration': duration, 'compatible': kinds,
                     'cache': 'c'+str(rng.randrange(4 if family=='cache' else 2)),
                     'failure_probability': rng.choice([.03, .12, .4, .7])})
    # Input order is unrelated to graph traversal or failure labels.
    rng.shuffle(jobs)
    risky = [j for j in jobs if j['failure_probability'] >= .4]
    failure = rng.choice(risky or jobs)['id']
    return {'workers': workers, 'jobs': jobs, 'cold_start': 15 if family=='cache' else 2}, failure


def suite(split):
    if split not in SPLITS:
        raise ValueError('unknown population')
    result = []
    for f_index, family in enumerate(FAMILIES):
        for replica in range(3):
            base, failing = generate(family, SPLITS[split] + f_index*100 + replica)
            # Paired success/failure scenarios have identical observable initial state.
            for mode in ('success', 'failure'):
                result.append(dict(base, id=f'{split}-{family}-{replica}-{mode}',
                                   failing_jobs=[] if mode=='success' else [failing]))
    return result

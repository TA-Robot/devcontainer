"""Authoring-only broad load bands. Never release this generator to a developer."""
import random

FAMILIES = ('burst', 'scarce', 'cache', 'mixed')
BANDS = {'ordinary': (96, 6), 'contended': (288, 8), 'severe': (768, 12)}


def case(family, band, seed, identifier):
    rng = random.Random(seed)
    count, worker_count = BANDS[band]
    workers = [{'id': f'w{i}', 'kind': 'gpu' if i < max(1, worker_count//4) else 'cpu', 'memory': 12} for i in range(worker_count)]
    cold = 14 if family in ('cache', 'mixed') else 3
    memory = worker_count*(4 if family in ('scarce', 'mixed') else 8)
    jobs = []
    for chain in range(count//3):
        release = rng.randrange(0, 800)
        if family in ('burst', 'mixed'):
            release = (release//160)*160+rng.randrange(12)
        weight = rng.choices([1, 4, 16], weights=[5, 3, 2])[0]
        cache = f'c{rng.randrange(8)}'
        stages = []
        for stage in range(3):
            base = rng.randrange(8, 35)
            estimate = {'cpu': base, 'gpu': max(3, base//2)}
            if family in ('scarce', 'mixed') and stage == 1 and rng.random() < .55:
                estimate = {'gpu': base}
            actual = {k: max(1, int(v*rng.choice([.7, 1, 1, 1.4, 1.8]))) for k, v in estimate.items()}
            stages.append({'id': f'j{chain*3+stage}', 'release': release, 'deadline': 0, 'weight': weight if stage == 2 else 0,
                           'deps': [f'j{chain*3+stage-1}'] if stage else [], 'estimate': estimate, 'actual': actual,
                           'memory': rng.randrange(3, 10), 'cache': cache if family == 'cache' else f'c{rng.randrange(8)}'})
        # Based on public estimates, not future actual work or outage knowledge.
        serial = sum(min(j['estimate'].values())+cold for j in stages)
        deadline = min(1200, release+serial*(2 if weight == 16 else 3)+30)
        for j in stages:
            j['deadline'] = deadline
        jobs.extend(stages)
    outages = []
    if family in ('scarce', 'mixed'):
        for i in range(worker_count):
            for start in (270+i*3, 650+i*2):
                outages.append({'worker_id': f'w{i}', 'start': start, 'end': start+rng.randrange(30, 100)})
    rng.shuffle(jobs)
    return {'id': identifier, 'horizon': 1200, 'heartbeat': 10, 'memory': memory, 'cold_start': cold,
            'jobs': jobs, 'workers': workers, 'outages': outages}


def suite(split='development'):
    if split not in ('development', 'qualification'):
        raise ValueError('only new authoring populations; no confirmation generation')
    base = 840001 if split == 'development' else 910003
    return [case(f, b, base+fi*1000+bi*100+i, f'{split}-{b}-{f}-{i}')
            for bi, b in enumerate(BANDS) for fi, f in enumerate(FAMILIES) for i in range(2)]

"""New fixed draws from the unchanged authoring-only workload generator."""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def generate(config):
    source = HERE.parent/'dynamic_v1/workloads.py'
    spec = importlib.util.spec_from_file_location('refinement_workloads', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    populations = {}
    for split, key in (('development', 'public_seed_base'), ('qualification', 'assessment_seed_base')):
        populations[split] = [module.case(f, b, config[key]+fi*1000+bi*100+i, f'{split}-{b}-{f}-{i}')
                             for bi, b in enumerate(module.BANDS) for fi, f in enumerate(module.FAMILIES)
                             for i in range(2)]
    return populations

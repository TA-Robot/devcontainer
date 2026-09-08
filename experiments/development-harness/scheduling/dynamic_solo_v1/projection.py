"""Project only public contracts, dev inputs and an executable FIFO baseline."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
BASE = HERE.parent/'dynamic_v1'


def cases(base, split):
    spec = importlib.util.spec_from_file_location('projected_workloads', base/'workloads.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.suite(split)


def probe():
    return [{'id': 'public-smoke', 'horizon': 12, 'heartbeat': 2, 'memory': 4, 'cold_start': 0,
             'workers': [{'id': 'w', 'kind': 'cpu', 'memory': 4}], 'outages': [{'worker_id': 'w', 'start': 3, 'end': 5}],
             'jobs': [{'id': 'a', 'release': 0, 'deadline': 10, 'weight': 16, 'deps': [], 'estimate': {'cpu': 2},
                       'actual': {'cpu': 4}, 'memory': 3, 'cache': 'x'}]}]


def prepare(output, base=BASE, actor=HERE):
    output.mkdir(parents=True, exist_ok=False)
    for name in ('runtime.py', 'transport.py'):
        shutil.copyfile(base/name, output/name)
    for name in ('public_check.py', 'fifo.py', 'TASK.md'):
        shutil.copyfile(actor/name, output/name)
    # Historical runtime contract is public, except its superseded future gate.
    text = (base/'TASK.md').read_text()
    old = 'No reference-vector pass threshold or live difficulty claim is\nfixed yet. A reachable demanding target will be fixed after non-agent calibration,\nbefore measured developer runs.'
    assert old in text
    (output/'RUNTIME.md').write_text(text.replace(old, 'This run profiles continuous quality; the current TASK.md defines its objectives and boundaries.'))
    (output/'ACTOR_ONLY').write_text('dynamic public development runtime\n')
    (output/'development.json').write_text(json.dumps(cases(base, 'development'))+'\n')
    (output/'probe.json').write_text(json.dumps(probe())+'\n')
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())}

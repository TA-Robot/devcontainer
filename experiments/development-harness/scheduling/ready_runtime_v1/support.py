"""Public projection and bounded dependency inventory for the new clock only."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SCHEDULING = HERE.parent


def read(path): return json.loads(path.read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path, value):
    with path.open('x') as stream: json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def identity():
    files = [*HERE.glob('*.py'), HERE/'READY.md', HERE/'TASK.md', ROOT/'scripts/test-ready-scheduling-runtime.py']
    files += [SCHEDULING/path for path in (
        'dynamic_solo_v1/projection.py', 'dynamic_solo_v1/fifo.py', 'dynamic_solo_v1/image.json',
        'dynamic_v1/workloads.py', 'dynamic_v1/TASK.md', 'native_actor_v1/TASK.md',
        'refinement_cohort_v1/populations.py', 'continuation_pair_v1/initial-policy.txt',
        'termination_pair_v1/INITIAL.md', 'termination_pair_v1/config.json',
        'termination_pair_v1/calibrate.py', 'termination_pair_v1/recovery.py')]
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(files)}


def prepare_public(output, *, smoke=False):
    output.mkdir(parents=True, exist_ok=False)
    for name in ('runtime.py', 'transport.py', 'public_check.py', 'launcher.py', 'recovery.py'):
        shutil.copyfile(HERE/name, output/name)
    shutil.copyfile(SCHEDULING/'dynamic_solo_v1/fifo.py', output/'fifo.py')
    shutil.copyfile(SCHEDULING/'continuation_pair_v1/initial-policy.txt', output/'initial.py')
    shutil.copyfile(SCHEDULING/'termination_pair_v1/INITIAL.md', output/'INITIAL.md')
    (output/'TASK.md').write_text((SCHEDULING/'native_actor_v1/TASK.md').read_text()+'\n'+(HERE/'READY.md').read_text())
    doc = (SCHEDULING/'dynamic_v1/TASK.md').read_text()
    old = 'No reference-vector pass threshold or live difficulty claim is\nfixed yet. A reachable demanding target will be fixed after non-agent calibration,\nbefore measured developer runs.'
    if old not in doc or 'response and 30 seconds per scenario' not in doc:
        raise ValueError('unexpected historical public contract')
    doc = doc.replace(old, 'This run profiles continuous quality; the current TASK.md defines its objectives and boundaries.')
    doc = doc.replace('response and 30 seconds per scenario', 'response and 90 seconds per scenario')
    (output/'RUNTIME.md').write_text(doc+'\n'+(HERE/'READY.md').read_text())
    (output/'ACTOR_ONLY').write_text('dynamic public development runtime\n')
    probe = load('ready_public_probe', SCHEDULING/'dynamic_solo_v1/projection.py').probe()
    cases = probe if smoke else load('ready_public_populations', SCHEDULING/'refinement_cohort_v1/populations.py').generate(
        read(SCHEDULING/'termination_pair_v1/config.json'))['development']
    save(output/'development.json', cases); save(output/'probe.json', probe)
    return {p.name: sha(p) for p in sorted(output.iterdir())}


def public_execution(public, output, name):
    helper = load('ready_frozen_public_container', SCHEDULING/'termination_pair_v1/calibrate.py')
    # Reuse only the existing fixed-image public container helper. Its source,
    # image and cleanup dependency are included in identity(); no old run changes.
    api = SimpleNamespace(read=read, load=load, save=save, SCHEDULING=SCHEDULING)
    return helper.public_execution(api, public, output, name)

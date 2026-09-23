"""Explicit public allowlist; no authoring generator/reference/qualification mount."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent
WORKLOAD=HERE.parent/'workloads_v1'
BASE=HERE.parent/'v1'
sys.path.insert(0,str(WORKLOAD))
from workloads import suite


def prepare(output):
    output.mkdir(parents=True,exist_ok=False)
    sources={'TASK.md':BASE/'TASK.md','WORKLOAD.md':WORKLOAD/'WORKLOAD.md',
             'runtime.py':BASE/'runtime.py','transport.py':BASE/'transport.py',
             'public_check.py':HERE/'public_check.py','fifo.py':BASE/'calibration/fifo.py'}
    for name,path in sources.items():shutil.copyfile(path,output/name)
    (output/'ACTOR_ONLY').write_text('public development runtime\n')
    (output/'development.json').write_text(json.dumps(suite('development'))+'\n')
    targets=json.loads((WORKLOAD/'qualification.json').read_text())['targets']['development']
    (output/'targets.json').write_text(json.dumps(targets,indent=2)+'\n')
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())}

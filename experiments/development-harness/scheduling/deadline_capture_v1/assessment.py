"""Assess captured bytes with the actual exit contract of the frozen evaluator."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
TIMING = HERE.parent/'timing_diagnostic_v1'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def quality_status(evaluated, returncode):
    # The frozen evaluate.py prints its report and exits zero even for an
    # invalid policy. Nonzero means an unexpected process failure, not a
    # known policy-invalid classification. Keep all raw statuses unchanged.
    rows = evaluated.get('cases', [])
    if returncode != 0 or not rows or not evaluated.get('all_containers_removed'):
        return 'withhold'
    if evaluated.get('status') == 'completed' and all(r['status'] == 'measured' for r in rows):
        return 'measured'
    if (evaluated.get('status') == 'withhold' and any(r['status'] == 'invalid-policy' for r in rows)
            and all(r['status'] in ('measured', 'invalid-policy') for r in rows)):
        return 'invalid-policy'
    return 'withhold'


def evaluate(candidate, scenarios, output, *, seconds=900):
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    result = {'status': 'withhold', 'kind': 'sealed-artifact-independent-assessment-v1', 'cleanup': 'unknown'}
    process = None
    try:
        expected = sha(candidate)
        input_file_sha256 = sha(scenarios)
        inputs = json.loads(scenarios.read_text())
        population = hashlib.sha256(json.dumps(inputs, sort_keys=True, allow_nan=False).encode()).hexdigest()
        sources = {n: sha(TIMING/n) for n in ('runtime.py', 'transport.py', 'evaluate.py', 'TASK.md')}
        process = subprocess.Popen([sys.executable, str(TIMING/'evaluate.py'), '--candidate', str(candidate),
                                    '--scenarios', str(scenarios), '--output', str(output/'evaluation')],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try: process.communicate(timeout=seconds)
        finally:
            if process.poll() is None:
                process.terminate()
                try: process.communicate(timeout=30)
                except subprocess.TimeoutExpired: process.kill(); process.communicate(timeout=3)
            if (output/'evaluation/result.json').exists():
                result['evaluation'] = json.loads((output/'evaluation/result.json').read_text())
                if result['evaluation'].get('all_containers_removed'): result['cleanup'] = 'confirmed'
        evaluated = result.get('evaluation', {})
        seal = json.loads((output/'evaluation/seal.json').read_text())
        if (candidate.is_symlink() or sha(candidate) != expected or seal['candidate_sha256'] != expected
                or seal['scenario_sha256'] != population or seal['source_sha256'] != sources
                or sha(scenarios) != input_file_sha256
                or {n: sha(TIMING/n) for n in sources} != sources
                or len(evaluated['cases']) != len(inputs)
                or {r['id'] for r in evaluated['cases']} != {c['id'] for c in inputs}
                or result['cleanup'] != 'confirmed'):
            raise ValueError('baseline assessment seal or coverage mismatch')
        result['status'] = quality_status(evaluated, process.returncode)
        result['candidate_sha256'] = expected
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        result['failure'] = type(exc).__name__+': '+str(exc)
    finally:
        with (output/'result.json').open('x') as stream:
            json.dump(result, stream, indent=2); stream.write('\n')
    return result

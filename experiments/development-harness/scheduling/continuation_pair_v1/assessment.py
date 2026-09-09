"""Grade a fixed non-agent baseline with the unchanged independent evaluator."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
TIMING = HERE.parent/'timing_diagnostic_v1'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(candidate, scenarios, output, *, seconds=900):
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    result = {'status': 'withhold', 'kind': 'fixed-non-agent-assessment', 'cleanup': 'unknown'}
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
        spec = importlib.util.spec_from_file_location('continuation_status', HERE.parent/'native_recovery_v1/assess.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        result['status'] = module.quality_status(evaluated['cases'], process.returncode)
        result['candidate_sha256'] = expected
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        result['failure'] = type(exc).__name__+': '+str(exc)
    finally:
        with (output/'result.json').open('x') as stream:
            json.dump(result, stream, indent=2); stream.write('\n')
    return result

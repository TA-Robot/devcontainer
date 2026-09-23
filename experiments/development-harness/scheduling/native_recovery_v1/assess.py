"""Independent Docker assessment of a sealed, normally completed artifact."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

TIMING = Path(__file__).resolve().parent.parent/'timing_diagnostic_v1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quality_status(rows, returncode):
    if rows and returncode == 0 and all(r['status'] == 'measured' for r in rows):
        return 'measured'
    if (rows and returncode == 1 and any(r['status'] == 'invalid-policy' for r in rows)
            and all(r['status'] in ('measured', 'invalid-policy') for r in rows)):
        return 'invalid-policy'
    return 'withhold'


def assess(actor, cases, output, *, seconds=120):
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    source = actor/'submission.py'
    report = json.loads((actor/'result.json').read_text())
    result = {'status': 'withhold', 'actor_result_sha256': sha(actor/'result.json'),
              'budget_admission': report['admission'], 'cleanup': 'unknown',
              'scope': 'sealed artifact quality; no promotion of budget admission'}
    process = None
    try:
        if report['quality']['status'] != 'eligible' or report['cleanup']['status'] != 'confirmed':
            raise ValueError('normal selected artifact not eligible')
        if source.is_symlink() or sha(source) != report['artifact']['sha256']:
            raise ValueError('submission seal mismatch')
        scenarios = json.loads(cases.read_text())
        expected_cases = hashlib.sha256(json.dumps(scenarios, sort_keys=True, allow_nan=False).encode()).hexdigest()
        expected_sources = {n: sha(TIMING/n) for n in ('runtime.py', 'transport.py', 'evaluate.py', 'TASK.md')}
        directory = output/'evaluation'
        process = subprocess.Popen([sys.executable, str(TIMING/'evaluate.py'), '--candidate', str(source),
                                    '--scenarios', str(cases), '--output', str(directory)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            process.communicate(timeout=seconds)
        finally:
            if process.poll() is None:
                process.terminate()
                try: process.communicate(timeout=30)
                except subprocess.TimeoutExpired: process.kill(); process.communicate(timeout=3)
            if (directory/'result.json').exists():
                result['evaluation'] = json.loads((directory/'result.json').read_text())
                if result['evaluation'].get('all_containers_removed'):
                    result['cleanup'] = 'confirmed'
        evaluation = result.get('evaluation', {})
        seal = json.loads((directory/'seal.json').read_text())
        if (seal['candidate_sha256'] != report['artifact']['sha256'] or seal['scenario_sha256'] != expected_cases
                or seal['source_sha256'] != expected_sources or sha(source) != report['artifact']['sha256']):
            raise ValueError('assessment seal mismatch')
        if (result['cleanup'] != 'confirmed' or len(evaluation['cases']) != len(scenarios)
                or {r['id'] for r in evaluation['cases']} != {s['id'] for s in scenarios}):
            raise ValueError('incomplete assessment')
        result['status'] = quality_status(evaluation['cases'], process.returncode)
        if result['status'] == 'withhold':
            result['failure'] = 'unmeasured cases or unexpected evaluator exit'
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        result['failure'] = type(exc).__name__ + ': ' + str(exc)
    finally:
        with (output/'result.json').open('x') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
    return result

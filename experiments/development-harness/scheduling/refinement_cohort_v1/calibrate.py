"""Frozen public FIFO calibration; no model calls or qualification scoring."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def module():
    spec = importlib.util.spec_from_file_location('calibration_cohort', HERE/'run.py')
    cohort = importlib.util.module_from_spec(spec); spec.loader.exec_module(cohort)
    return cohort


def execute(output):
    cohort = module(); plan = cohort.read(output/'plan.json')
    if cohort.identity() != plan['source_sha256']: raise ValueError('calibration source mismatch')
    inputs = cohort.prepare_inputs(output, False)
    result = {'status': 'withhold', 'source_sha256': plan['source_sha256'], 'input_seal': inputs,
              'live_provider_calls': 0, 'qualification_scored': False}
    process = None
    try:
        process = subprocess.Popen([sys.executable, str(cohort.SCHEDULING/'timing_diagnostic_v1/evaluate.py'),
            '--candidate', str(output/'public/fifo.py'), '--scenarios', str(output/'public/development.json'),
            '--output', str(output/'assessment')], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.communicate(timeout=900)
        evaluated = cohort.read(output/'assessment/result.json')
        seal = cohort.read(output/'assessment/seal.json')
        cases = cohort.read(output/'public/development.json')
        if (process.returncode != 0 or evaluated['status'] != 'completed' or not evaluated['all_containers_removed']
                or len(evaluated['cases']) != 24 or {r['id'] for r in evaluated['cases']} != {c['id'] for c in cases}
                or seal['candidate_sha256'] != cohort.sha(output/'public/fifo.py')
                or seal['scenario_sha256'] != hashlib.sha256(json.dumps(cases, sort_keys=True, allow_nan=False).encode()).hexdigest()
                or seal['source_sha256'] != {n: cohort.sha(cohort.SCHEDULING/'timing_diagnostic_v1'/n)
                                             for n in ('runtime.py', 'transport.py', 'evaluate.py', 'TASK.md')}):
            raise ValueError('incomplete or mismatched public calibration')
        result.update(status='passed', public_cases_measured=24, all_containers_removed=True,
                      raw_assessment_sha256=cohort.sha(output/'assessment/result.json'))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        result['failure'] = type(exc).__name__+': '+str(exc)
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try: process.communicate(timeout=30)
            except subprocess.TimeoutExpired: process.kill(); process.communicate(timeout=3)
        cohort.save(output/'result.json', result)
    return result


def run(output):
    cohort = module(); initial = cohort.identity()
    output = output.resolve(); output.mkdir(parents=True, mode=0o700, exist_ok=False)
    for name, expected in initial.items():
        data = (cohort.ROOT/name).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected: raise ValueError('source changed')
        target = output/'source'/name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data); target.chmod(0o444)
    cohort.save(output/'plan.json', {'source_sha256': initial})
    with (output/'controller.stdout').open('xb') as stdout, (output/'controller.stderr').open('xb') as stderr:
        subprocess.run([sys.executable, str(output/'source'/HERE.relative_to(cohort.ROOT)/'calibrate.py'),
                        '--execute', '--output', str(output)], check=True, stdout=stdout, stderr=stderr, timeout=1000)
    return cohort.read(output/'result.json')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--execute', action='store_true', help=argparse.SUPPRESS)
    a = p.parse_args(); value = execute(a.output) if a.execute else run(a.output)
    print(json.dumps({'status': value['status']})); raise SystemExit(0 if value['status'] == 'passed' else 1)

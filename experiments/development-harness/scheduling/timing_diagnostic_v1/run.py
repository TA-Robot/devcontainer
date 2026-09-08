"""Separate bounded diagnosis of the original frozen submission and reference."""
import argparse
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent


class StopRequested(RuntimeError):
    pass


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    with path.open('x') as f: json.dump(value, f, indent=2); f.write('\n')


def run(original, output):
    initial = read(original/'result.json')
    if initial['status'] != 'withhold' or initial.get('actor', {}).get('status') != 'completed':
        raise ValueError('requires the completed developer with withheld original assessment')
    if sha(original/'submission.py') != initial['submission_sha256']:
        raise ValueError('original submission changed')
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    source = output/'source'; source.mkdir()
    files = [*HERE.glob('*.py'), HERE/'TASK.md']
    hashes = {}
    for path in files:
        data = path.read_bytes(); hashes[path.name] = hashlib.sha256(data).hexdigest()
        (source/path.name).write_bytes(data); (source/path.name).chmod(0o444)
    cases_path = output/'qualification.private.json'
    cases_path.write_bytes((original/'assessment-submission.cases.private.json').read_bytes())
    cases = read(cases_path)
    if len(cases) != 24 or len({c['id'] for c in cases}) != 24: raise ValueError('coverage')
    old_seal = read(original/'assessment-submission/seal.json')
    if hashlib.sha256(json.dumps(cases, sort_keys=True, allow_nan=False).encode()).hexdigest() != old_seal['scenario_sha256']:
        raise ValueError('original cases changed')
    if sha(source/'runtime.py') != old_seal['source_sha256']['runtime.py']:
        raise ValueError('physical runtime changed')
    submission = output/'submission.py'; submission.write_bytes((original/'submission.py').read_bytes())
    ref = original/'source/experiments/development-harness/scheduling/dynamic_v1/policies/reference.py'
    old_sources = read(original/'seal.json')['source_sha256']
    ref_name = 'experiments/development-harness/scheduling/dynamic_v1/policies/reference.py'
    if sha(ref) != old_sources[ref_name]: raise ValueError('original reference changed')
    reference = output/'reference.py'; reference.write_bytes(b"MODE = 'lookahead'\n"+ref.read_bytes())
    artifact_hashes = {'submission': sha(submission), 'reference': sha(reference)}
    save(output/'plan.json', {'kind': 'post-run-timing-diagnostic-plan-v1', 'original': str(original),
         'original_result_sha256': sha(original/'result.json'), 'source_sha256': hashes,
         'candidate_sha256': artifact_hashes, 'case_sha256': sha(cases_path),
         'scenario_seconds': 90, 'response_seconds': 5, 'seconds_per_assessment': 900,
         'cleanup_reserve_seconds': 30, 'assessments': 2, 'live_provider_calls': 0,
         'original_profile_remains_withheld': True})
    result = {'kind': 'post-run-timing-diagnostic-v1', 'status': 'withhold', 'assessments': {},
              'original_profile_status': 'withhold', 'live_provider_calls': 0, 'diagnostic_only': True}
    began = time.monotonic(); interrupted = []
    def stop(signum, frame):
        if not interrupted: interrupted.append(signum); raise StopRequested('diagnostic interrupted')
    handlers = {s: signal.signal(s, stop) for s in (signal.SIGINT, signal.SIGTERM)}
    try:
        for name in ('submission', 'reference'):
            row = {'status': 'started', 'cleanup': 'unknown'}; result['assessments'][name] = row
            candidate = output/f'{name}.py'; folder = output/f'assessment-{name}'
            if sha(candidate) != artifact_hashes[name] or any(sha(source/n) != h for n, h in hashes.items()):
                raise ValueError('snapshot changed')
            p = None
            try:
                p = subprocess.Popen([sys.executable, str(source/'evaluate.py'), '--candidate', str(candidate),
                    '--scenarios', str(cases_path), '--output', str(folder)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p.communicate(timeout=900)
            except (OSError, StopRequested, subprocess.SubprocessError) as error:
                row['failure'] = type(error).__name__+': '+str(error)
            finally:
                if p is not None and p.poll() is None:
                    p.terminate()
                    try: p.communicate(timeout=30)
                    except subprocess.TimeoutExpired: p.kill(); p.communicate(timeout=3)
                if (folder/'result.json').exists():
                    row['result'] = read(folder/'result.json')
                    if row['result'].get('all_containers_removed'):
                        row['cleanup'] = 'confirmed'
            raw = row.get('result', {})
            seal = read(folder/'seal.json') if (folder/'seal.json').exists() else {}
            expected_sources = {n: hashes[n] for n in ('runtime.py', 'transport.py', 'evaluate.py', 'TASK.md')}
            if (row.get('failure') or p is None or p.returncode != 0 or raw.get('status') != 'completed'
                    or row['cleanup'] != 'confirmed' or len(raw.get('cases', [])) != 24
                    or {r['id'] for r in raw['cases']} != {c['id'] for c in cases}
                    or seal.get('candidate_sha256') != artifact_hashes[name]
                    or seal.get('scenario_sha256') != old_seal['scenario_sha256']
                    or seal.get('source_sha256') != expected_sources):
                row['status'] = 'withhold'; break
            row['status'] = 'completed'
        else: result['status'] = 'completed'
    except (OSError, ValueError, KeyError, StopRequested) as error:
        result['failure'] = type(error).__name__+': '+str(error)
    finally:
        result['elapsed_seconds'] = time.monotonic()-began
        result['owned_cleanup_confirmed'] = bool(result['assessments']) and all(r['cleanup'] == 'confirmed' for r in result['assessments'].values())
        save(output/'result.json', result)
        for s, h in handlers.items(): signal.signal(s, h)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--original-run', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); a = p.parse_args()
    result = run(a.original_run, a.output); print(json.dumps({'status': result['status']}))
    sys.exit(0 if result['status'] == 'completed' else 1)

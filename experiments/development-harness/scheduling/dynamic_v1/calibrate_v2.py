"""Snapshot-bound calibration controller; frozen v1 scoring remains unchanged."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
MODES = ('fifo', 'edf', 'density', 'lookahead')
FILES = ('runtime.py', 'transport.py', 'evaluate.py', 'workloads.py', 'TASK.md', 'policies/reference.py')


class StopRequested(RuntimeError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def load_workloads(path):
    spec = importlib.util.spec_from_file_location('frozen_workloads_'+uuid.uuid4().hex, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assess(raw, seal, cases, code_hash, source_hashes):
    expected = {c['id'] for c in cases}
    rows = raw.get('cases', [])
    if (raw.get('status') != 'completed' or not raw.get('all_containers_removed')
            or len(rows) != len(cases) or {r.get('id') for r in rows} != expected
            or any(r.get('status') != 'measured' or r.get('execution', {}).get('removed') is not True for r in rows)):
        raise ValueError('incomplete or mismatched assessment coverage')
    wanted = {name: source_hashes[name] for name in ('runtime.py', 'transport.py', 'evaluate.py', 'TASK.md')}
    if (seal.get('source_sha256') != wanted or seal.get('candidate_sha256') != code_hash
            or seal.get('scenario_sha256') != digest(json.dumps(cases, sort_keys=True, allow_nan=False).encode())):
        raise ValueError('assessment seal mismatch')


def run(output, max_cases):
    if max_cases != 24:
        raise ValueError('all 24 declared cases required')
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    began = time.monotonic()
    report = {'kind': 'dynamic-calibration-controller-v2', 'status': 'withhold', 'attempts': [],
              'live_provider_calls': 0, 'confirmation_executed': False, 'difficulty_calibrated': False}
    interrupted = []
    def stop(signum, frame):
        if not interrupted:
            interrupted.append(signum)
            raise StopRequested('controller interrupted')
    handlers = {s: signal.signal(s, stop) for s in (signal.SIGINT, signal.SIGTERM)}
    try:
        # All later imports and launches read this one private snapshot.
        payload = {name: (HERE/name).read_bytes() for name in FILES}
        source = output/'source'; source.mkdir()
        for name, data in payload.items():
            path = source/name; path.parent.mkdir(exist_ok=True)
            path.write_bytes(data); path.chmod(0o444)
        hashes = {name: digest(data) for name, data in payload.items()}
        cases = load_workloads(source/'workloads.py').suite('development')
        if len(cases) != 24 or len({c['id'] for c in cases}) != 24:
            raise ValueError('workload coverage')
        data_path = output/'development.private.json'; save(data_path, cases)
        data_hash = digest(data_path.read_bytes())
        save(output/'plan.json', {'source_sha256': hashes, 'controller_sha256': digest(Path(__file__).read_bytes()),
             'case_sha256': data_hash, 'modes': MODES, 'cases': 24, 'seconds_per_mode': 300,
             'cleanup_seconds_per_mode': 30, 'stop_on_failure': True})
        for mode in MODES:
            row = {'mode': mode, 'status': 'started', 'process_started': False, 'cleanup': 'not-started'}
            report['attempts'].append(row)
            folder = output/mode
            code = f'MODE = {mode!r}\n'.encode()+payload['policies/reference.py']
            candidate = output/f'{mode}.py'; candidate.write_bytes(code); candidate.chmod(0o444)
            if any(digest((source/n).read_bytes()) != h for n, h in hashes.items()) or digest(data_path.read_bytes()) != data_hash:
                raise ValueError('snapshot changed')
            save(output/f'{mode}.start.json', row)
            process = None
            try:
                process = subprocess.Popen([sys.executable, str(source/'evaluate.py'), '--candidate', str(candidate),
                    '--scenarios', str(data_path), '--output', str(folder)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                row.update(process_started=True, cleanup='unknown')
                stdout, stderr = process.communicate(timeout=300)
            finally:
                if process is not None and process.poll() is None:
                    process.terminate()
                    try:
                        process.communicate(timeout=30)
                    except subprocess.TimeoutExpired:
                        process.kill(); process.communicate(timeout=3)
            (output/f'{mode}.stdout').write_bytes(stdout)
            (output/f'{mode}.stderr').write_bytes(stderr)
            raw = json.loads((folder/'result.json').read_text())
            seal = json.loads((folder/'seal.json').read_text())
            assess(raw, seal, cases, digest(code), hashes)
            if any(digest((source/n).read_bytes()) != h for n, h in hashes.items()) or digest(data_path.read_bytes()) != data_hash:
                raise ValueError('snapshot changed during assessment')
            if process.returncode != 0:
                raise ValueError('assessment process failed')
            row.update(status='completed', cleanup='confirmed', assessment_sha256=digest((folder/'result.json').read_bytes()))
        report['status'] = 'completed'
    except (OSError, ValueError, TypeError, KeyError, StopRequested, subprocess.SubprocessError, KeyboardInterrupt) as error:
        report['failure'] = type(error).__name__+': '+str(error)
        if report['attempts']:
            report['attempts'][-1]['status'] = 'withhold'
    finally:
        # Do not infer successful cleanup from an empty set or a killed controller.
        report['all_started_assessments_cleanup_confirmed'] = (
            bool(report['attempts']) and all(r['cleanup'] == 'confirmed' for r in report['attempts']))
        report['elapsed_seconds'] = time.monotonic()-began
        save(output/'report.json', report)
        for s, handler in handlers.items(): signal.signal(s, handler)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--max-cases', type=int, required=True); a = p.parse_args()
    result = run(a.output, a.max_cases)
    print(json.dumps({'status': result['status']}))
    sys.exit(0 if result['status'] == 'completed' else 1)

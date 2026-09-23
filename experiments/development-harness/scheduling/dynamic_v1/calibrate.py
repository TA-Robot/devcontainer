"""Finite provider-free calibration of all declared load bands, no target selection."""
import argparse
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import sys
import time

from workloads import suite

HERE = Path(__file__).resolve().parent
MODES = ('fifo', 'edf', 'density', 'lookahead')


class StopRequested(RuntimeError):
    pass


def save(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def run(output, max_cases):
    if max_cases != 24:
        raise ValueError('this calibration covers all 24 declared family/band cases')
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    cases = suite('development')
    data = output/'development.private.json'; save(data, cases)
    files = [*HERE.glob('*.py'), HERE/'TASK.md', HERE/'policies/reference.py']
    hashes = {str(p.relative_to(HERE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    save(output/'plan.json', {'source_sha256': hashes, 'modes': MODES, 'cases': max_cases,
         'case_sha256': hashlib.sha256(data.read_bytes()).hexdigest(), 'seconds_per_mode': 300,
         'cleanup_reserve_seconds_per_mode': 30, 'failure_policy': 'stop_on_unmeasured_or_invalid',
         'live_provider_calls': 0, 'confirmation_executed': False})
    began = time.monotonic()
    report = {'kind': 'dynamic-scheduling-reference-calibration-v1', 'status': 'running', 'modes': {},
              'source_sha256': hashes, 'live_provider_calls': 0, 'confirmation_executed': False,
              'difficulty_calibrated': False, 'attainment_targets_fixed': False}
    def stop(signum, frame):
        raise StopRequested('calibration interrupted')
    handlers = {s: signal.signal(s, stop) for s in (signal.SIGINT, signal.SIGTERM)}
    try:
        for mode in MODES:
            candidate = output/f'{mode}.py'
            candidate.write_text(f'MODE = {mode!r}\n'+(HERE/'policies/reference.py').read_text())
            folder = output/mode
            process = subprocess.Popen([sys.executable, str(HERE/'evaluate.py'), '--candidate', str(candidate),
                '--scenarios', str(data), '--output', str(folder)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            interrupted = False
            try:
                stdout, stderr = process.communicate(timeout=300)
            except (subprocess.TimeoutExpired, StopRequested, KeyboardInterrupt):
                interrupted = True
                process.terminate()
                try:
                    stdout, stderr = process.communicate(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill(); stdout, stderr = process.communicate(timeout=3)
            (output/f'{mode}.stdout').write_bytes(stdout)
            (output/f'{mode}.stderr').write_bytes(stderr)
            raw = json.loads((folder/'result.json').read_text()) if (folder/'result.json').exists() else {}
            rows = []
            for row in raw.get('cases', []):
                r = row.get('result', {})
                rows.append({'id': row['id'], 'status': row['status'], **{k: r.get(k) for k in
                             ('on_time_value', 'offered_value', 'unfinished_value', 'deadline_deficit', 'service_classes',
                              'busy_worker_ticks', 'interrupted_worker_ticks', 'response_p95_completed', 'response_sample_count')}})
            report['modes'][mode] = {'status': raw.get('status', 'unmeasured'), 'interrupted': interrupted,
                'all_containers_removed': raw.get('all_containers_removed', False), 'cases': rows,
                'elapsed_seconds': raw.get('elapsed_seconds'), 'candidate_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest()}
            if interrupted or process.returncode != 0 or raw.get('status') != 'completed' or not raw.get('all_containers_removed'):
                report['status'] = 'withhold'; break
        else:
            report['status'] = 'completed'
    finally:
        report['elapsed_seconds'] = time.monotonic()-began
        report['all_recorded_containers_removed'] = all(r['all_containers_removed'] for r in report['modes'].values())
        save(output/'report.json', report)
        for s, h in handlers.items(): signal.signal(s, h)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output', required=True, type=Path)
    p.add_argument('--max-cases', required=True, type=int)
    a = p.parse_args()
    print(json.dumps({'status': run(a.output, a.max_cases)['status']}))

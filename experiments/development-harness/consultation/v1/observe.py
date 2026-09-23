"""Public bounded observation tool; observes files/processes, never grades a diagnosis."""
import argparse
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import tempfile
import time

OPERATIONS = ('append-effect', 'persist-offset', 'read-offset')  # vocabulary, not execution order
TIMEOUT = 3.0
MAX_JSON_BYTES = 16384


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError('non-finite JSON value')


def read_json(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError('expected a regular JSON file')
    with path.open('rb') as stream:
        data = stream.read(MAX_JSON_BYTES + 1)
    if len(data) > MAX_JSON_BYTES:
        raise ValueError('JSON exceeds size cap')
    return json.loads(data, object_pairs_hook=pairs, parse_constant=invalid_constant)


def validate_plan(plan):
    if (not isinstance(plan, dict) or set(plan) != {'stop_after', 'restart_count'}
            or plan['stop_after'] not in OPERATIONS
            or type(plan['restart_count']) is not int or plan['restart_count'] != 1):
        raise ValueError('plan requires one published operation and exactly one restart')


def state(root):
    path = root / 'journal.json'
    offset = json.loads(path.read_text())['offset'] if path.exists() else 0
    path = root / 'effects.log'
    return {'offset': offset, 'effects': path.read_text().splitlines() if path.exists() else []}


def command(workspace, root, stop_after=None):
    args = [sys.executable, '-B', str(workspace / 'worker.py'), '--events', str(root / 'events.json'),
            '--journal', str(root / 'journal.json'), '--effects', str(root / 'effects.log')]
    return args + (['--stop-after', stop_after] if stop_after else [])


def crash(workspace, root, operation, *, timeout=TIMEOUT):
    # Only this child is signalled. stdout is a synchronization event, not a grade.
    env = {'PATH': os.defpath, 'PYTHONDONTWRITEBYTECODE': '1', 'TZ': 'UTC'}
    process = subprocess.Popen(command(workspace, root, operation), cwd=workspace, env=env,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    events = []
    try:
        deadline = time.monotonic() + timeout
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            data = b''
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not selector.select(remaining):
                    raise TimeoutError('operation barrier was not reached')
                chunk = os.read(process.stdout.fileno(), 4096)
                if not chunk:
                    raise RuntimeError('worker exited before the operation barrier')
                data += chunk
                if len(data) > MAX_JSON_BYTES:
                    raise RuntimeError('worker observation exceeds cap')
                while b'\n' in data:
                    line, data = data.split(b'\n', 1)
                    event = json.loads(line)
                    if set(event) != {'event'} or event['event'] not in OPERATIONS:
                        raise RuntimeError('invalid worker event')
                    events.append(event['event'])
                    if len(events) > len(OPERATIONS):
                        raise RuntimeError('too many worker events')
                    if event['event'] == operation:
                        process.kill()
                        process.wait(timeout=timeout)
                        return events
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=timeout)
        process.stdin.close()
        process.stdout.close()


def observe(workspace, plan, *, events=None, offset=0, effects=None, timeout=TIMEOUT):
    validate_plan(plan)
    events = ['event-1'] if events is None else events
    effects = [] if effects is None else effects
    env = {'PATH': os.defpath, 'PYTHONDONTWRITEBYTECODE': '1', 'TZ': 'UTC'}
    with tempfile.TemporaryDirectory(prefix='consultation-observation-') as raw:
        root = Path(raw)
        baseline = root / 'baseline'
        baseline.mkdir()
        for target in (root, baseline):
            (target / 'events.json').write_text(json.dumps(events))
            (target / 'journal.json').write_text(json.dumps({'offset': offset}))
            (target / 'effects.log').write_text(''.join(e + '\n' for e in effects))
        subprocess.run(command(workspace, baseline), cwd=workspace, env=env,
                       stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                       stderr=subprocess.DEVNULL, timeout=timeout, check=True)
        prefix = crash(workspace, root, plan['stop_after'], timeout=timeout)
        before = state(root)
        restarted = subprocess.run(command(workspace, root), cwd=workspace, env=env,
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, timeout=timeout, check=True)
        after = state(root)
        count = after['effects'].count(events[offset])
        return {'before_restart': before, 'after_restart': after,
                'outcome': 'lost' if count == 0 else 'once' if count == 1 else 'duplicate',
                'uninterrupted': state(baseline),
                'observed_prefix': prefix,
                'restart_events': [json.loads(line)['event'] for line in restarted.stdout.splitlines()]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    args = parser.parse_args()
    try:
        result = observe(Path(__file__).resolve().parent, read_json(args.plan))
    except (ValueError, OSError, RuntimeError, RecursionError, TypeError, subprocess.SubprocessError) as exc:
        print(json.dumps({'status': 'observation-error', 'reason': type(exc).__name__}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

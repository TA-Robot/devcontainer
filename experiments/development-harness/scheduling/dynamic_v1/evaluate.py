#!/usr/bin/env python3
"""Fresh independent assessment; no candidate Python is imported/executed on host."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import time

from runtime import Invalid, decode, require, simulate, validate
from transport import Policy, CapacityError

HERE = Path(__file__).resolve().parent


class StopRequested(RuntimeError):
    """Distinct from InterruptedError, which selectors may transparently retry."""


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def evaluate(candidate, scenarios, output):
    require(isinstance(scenarios, list) and 1 <= len(scenarios) <= 64, 'scenario count')
    for case in scenarios:
        validate(case)
    require(len({s['id'] for s in scenarios}) == len(scenarios), 'duplicate scenario id')
    fd = os.open(candidate, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as source:
        require(stat.S_ISREG(os.fstat(source.fileno()).st_mode), 'regular policy file required')
        code = source.read(65537)
    require(0 < len(code) <= 65536, 'policy size')
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    snapshot = output / 'policy.py'
    snapshot.write_bytes(code); snapshot.chmod(0o444)
    identity = {name: digest((HERE/name).read_bytes()) for name in ('runtime.py', 'transport.py', 'evaluate.py', 'TASK.md')}
    save(output/'seal.json', {'source_sha256': identity, 'candidate_sha256': digest(code),
         'scenario_sha256': digest(json.dumps(scenarios, sort_keys=True, allow_nan=False).encode())})
    report = {'kind': 'scheduling-dynamic-external-evaluation-v1', 'status': 'running', 'cases': [],
              'live_provider_calls': 0, 'legacy_scores_overwritten': False, 'hard_task_qualified': False}
    began = time.monotonic()
    interrupted = []
    def stop(signum, frame):
        if not interrupted:
            interrupted.append(signum)
            raise StopRequested('evaluation interrupted')
    handlers = {s: signal.signal(s, stop) for s in (signal.SIGINT, signal.SIGTERM)}
    try:
        for case in scenarios:
            row = {'id': case['id'], 'status': 'started'}
            report['cases'].append(row)
            policy = Policy(snapshot)
            try:
                with policy:
                    result = simulate(case, policy.choose)
                row.update(status='measured', result=result)
            except (Invalid, json.JSONDecodeError, UnicodeError, RecursionError) as error:
                row.update(status='invalid-policy', failure=type(error).__name__ + ': ' + str(error))
            except (StopRequested, CapacityError, TimeoutError, OSError, subprocess.SubprocessError) as error:
                row.update(status='unmeasured', failure=type(error).__name__)
            finally:
                row['execution'] = policy.record
            if not policy.record['removed']:
                row['status'] = 'unmeasured'
            if row['status'] == 'unmeasured' or interrupted:
                break
        report['status'] = ('completed' if len(report['cases']) == len(scenarios)
                            and all(r['status'] == 'measured' for r in report['cases']) else 'withhold')
    finally:
        report['elapsed_seconds'] = time.monotonic() - began
        report['all_containers_removed'] = all(r.get('execution', {}).get('removed') is True for r in report['cases'])
        save(output/'result.json', report)
        for signum, handler in handlers.items():
            signal.signal(signum, handler)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--scenarios', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    require(args.scenarios.stat().st_size <= 4194304, 'scenario input cap')
    value = evaluate(args.candidate, decode(args.scenarios.read_bytes()), args.output)
    print(json.dumps({'status': value['status'], 'output': str(args.output)}))

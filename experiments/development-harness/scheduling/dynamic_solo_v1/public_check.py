"""Public experiments inside actor sandbox; external assessment remains authoritative."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

from runtime import Invalid, simulate, validate
from transport import Policy, CapacityError


class LocalPolicy(Policy):
    def __enter__(self):
        self.started = time.monotonic(); self.deadline = self.started+self.seconds
        self.process = subprocess.Popen(['python3', '-u', str(self.snapshot)], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
            env={'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': '/nonexistent', 'PYTHONDONTWRITEBYTECODE': '1'})
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr): os.set_blocking(stream.fileno(), False)
        return self

    def close(self):
        if self.process:
            try: os.killpg(self.process.pid, 9)
            except ProcessLookupError: pass
            self.process.wait(timeout=3)
            for stream in (self.process.stdin, self.process.stdout, self.process.stderr): stream.close()
        self.record['removed'] = True


def main():
    if not Path('/public/ACTOR_ONLY').is_file() or not Path('/.dockerenv').exists():
        raise RuntimeError('dedicated actor environment required')
    p = argparse.ArgumentParser(); p.add_argument('--candidate', required=True, type=Path)
    p.add_argument('--cases', type=Path, default=Path('/public/development.json'))
    p.add_argument('--output', required=True, type=Path); a = p.parse_args()
    cases = json.loads(a.cases.read_text())
    if not isinstance(cases, list) or not cases: raise ValueError('nonempty cases required')
    for case in cases: validate(case)
    rows = []
    for case in cases:
        try:
            with LocalPolicy(a.candidate) as policy: result = simulate(case, policy.choose)
            rows.append({'id': case['id'], 'status': 'measured', 'result': result})
        except (Invalid, json.JSONDecodeError, UnicodeError, RecursionError) as error:
            rows.append({'id': case['id'], 'status': 'invalid-policy', 'reason': str(error)})
        except (CapacityError, TimeoutError, OSError, subprocess.SubprocessError) as error:
            rows.append({'id': case['id'], 'status': 'unmeasured', 'reason': type(error).__name__})
    summary = [{'id': r['id'], 'status': r['status'], **{k: r.get('result', {}).get(k) for k in
               ('on_time_value', 'offered_value', 'service_classes', 'unfinished_value', 'busy_worker_ticks')}} for r in rows]
    result = {'valid': all(r['status'] == 'measured' for r in rows), 'cases': rows}
    with a.output.open('x') as f: json.dump(result, f, indent=2)
    print(json.dumps({'valid': result['valid'], 'cases': summary, 'details': str(a.output)}))


if __name__ == '__main__': main()

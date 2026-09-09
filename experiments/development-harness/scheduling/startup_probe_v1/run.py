"""Six fixed, non-agent observations of startup versus response deadlines."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TIMING = HERE.parent/'timing_diagnostic_v1'
MARKER = b'FIXED_RUNTIME_READY_V1\n'


def read(path): return json.loads(path.read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path, value):
    with path.open('x') as stream: json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def identity():
    files = [*HERE.glob('*.py'), HERE/'PLAN.md', ROOT/'scripts/test-scheduling-startup-probe.py',
             TIMING/'runtime.py', TIMING/'transport.py', HERE.parent/'termination_pair_v1/recovery.py']
    return {str(f.relative_to(ROOT)): sha(f) for f in sorted(files)}


def transport():
    runtime = load('startup_probe_runtime', TIMING/'runtime.py')
    previous = sys.modules.get('runtime'); sys.modules['runtime'] = runtime
    try: return load('startup_probe_transport', TIMING/'transport.py')
    finally:
        if previous is None: sys.modules.pop('runtime', None)
        else: sys.modules['runtime'] = previous


def wait_ready(policy, seconds=20):
    """A fixed fixture's marker is evidence here, not a candidate-ready contract."""
    began = time.monotonic(); pending = bytearray()
    with selectors.DefaultSelector() as selector:
        selector.register(policy.process.stderr, selectors.EVENT_READ)
        selector.register(policy.process.stdout, selectors.EVENT_READ)
        while True:
            remaining = min(policy.deadline, began+seconds)-time.monotonic()
            if remaining <= 0: raise TimeoutError('runtime_readiness_deadline')
            for key, _ in selector.select(min(remaining, .05)):
                data = os.read(key.fd, 4096)
                if not data: raise ValueError('fixture exited before readiness')
                if key.fileobj is policy.process.stdout: raise ValueError('response before readiness/request')
                pending.extend(data)
                if len(pending) > len(MARKER): raise ValueError('invalid readiness marker')
                if b'\n' in pending:
                    if pending != MARKER: raise ValueError('invalid readiness marker')
                    return time.monotonic()-began


def trial(output, profile, clock_mode):
    if profile not in ('normal', 'startup_delay', 'response_delay') or clock_mode not in ('legacy', 'ready'):
        raise ValueError('fixed diagnostic profile required')
    output.mkdir(mode=0o700, exist_ok=False)
    source = (HERE/'fixture.py').read_text().replace('PROFILE = "normal"', 'PROFILE = '+json.dumps(profile))
    policy_file = output/'policy.py'; policy_file.write_text(source); policy_file.chmod(0o444)
    policy = transport().Policy(policy_file, seconds=90, response_seconds=5)
    save(output/'start.json', {'container': policy.name, 'profile': profile, 'clock_mode': clock_mode,
                               'policy_sha256': sha(policy_file)})
    result = {'profile': profile, 'clock_mode': clock_mode, 'status': 'withhold',
              'readiness_wait_seconds': None, 'response_started': False}
    try:
        with policy:
            if clock_mode == 'ready': result['readiness_wait_seconds'] = wait_ready(policy)
            result['response_started'] = True
            if policy.choose({'diagnostic': 'fixed-empty-action'}) != []:
                raise ValueError('unexpected diagnostic response')
            result['status'] = 'responded'
    except TimeoutError as exc:
        result.update(status='deadline', reason=str(exc))
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        result['reason'] = type(exc).__name__+': '+str(exc)
    finally:
        result['execution'] = policy.record
        result['recovery'] = load('startup_probe_recovery', HERE.parent/'termination_pair_v1/recovery.py').drain(
            policy.name, create_completed='startup_seconds' in policy.record, seconds=20)
        result['policy_unchanged'] = sha(policy_file) == read(output/'start.json')['policy_sha256']
        save(output/'result.json', result)
    return result


def expected(profile, clock_mode):
    return 'deadline' if profile == 'response_delay' or (profile == 'startup_delay' and clock_mode == 'legacy') else 'responded'


def run(output):
    output = output.resolve(); output.mkdir(parents=True, mode=0o700, exist_ok=False)
    sources = identity()
    save(output/'plan.json', {'source_sha256': sources, 'max_trials': 6, 'live_provider_calls': 0,
         'profiles': ['normal', 'startup_delay', 'response_delay'], 'clocks': ['legacy', 'ready'],
         'scenario_seconds': 90, 'response_seconds': 5, 'readiness_seconds': 20,
         'scope': 'fixed non-agent causal clock diagnostic; no old score or candidate reclassification'})
    for name, digest in sources.items():
        data = (ROOT/name).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest: raise ValueError('source changed during snapshot')
        destination = output/'source'/name; destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data); destination.chmod(0o444)
    # Execute functions from the snapshot so editor changes cannot alter a trial.
    frozen = load('startup_probe_frozen', output/'source'/HERE.relative_to(ROOT)/'run.py')
    result = {'status': 'withhold', 'trials': [], 'live_provider_calls': 0, 'old_scores_changed': False}
    handlers = {}
    def stop(signum, frame): raise RuntimeError('diagnostic interrupted')
    try:
        for sig in (signal.SIGINT, signal.SIGTERM): handlers[sig] = signal.signal(sig, stop)
        for profile in ('normal', 'startup_delay', 'response_delay'):
            for clock_mode in ('legacy', 'ready'):
                row = frozen.trial(output/(profile+'-'+clock_mode), profile, clock_mode); result['trials'].append(row)
                if (row['status'] != expected(profile, clock_mode) or not row['policy_unchanged']
                        or row['recovery']['status'] != 'confirmed'
                        or (row['status'] == 'deadline' and row.get('reason') != 'response_deadline')):
                    raise ValueError('unexpected observation; stop without retry')
        if frozen.identity() != sources or identity() != sources: raise ValueError('source changed')
        result['status'] = 'observed_expected_separation'
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        result['reason'] = type(exc).__name__+': '+str(exc)
    finally:
        save(output/'result.json', result)
        for sig, previous in handlers.items(): signal.signal(sig, previous)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); result = run(args.output)
    print(json.dumps({'status': result['status'], 'trials': len(result['trials'])}))
    raise SystemExit(0 if result['status'] == 'observed_expected_separation' else 1)

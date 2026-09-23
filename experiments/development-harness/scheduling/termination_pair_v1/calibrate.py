"""Public FIFO/initial calibration; never execute policy code on the host."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent


def module():
    spec = importlib.util.spec_from_file_location('continuation_calibration', HERE/'run.py')
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value


def public_execution(cohort, public, output, name):
    output.mkdir(mode=0o700, exist_ok=False)
    image = cohort.read(cohort.SCHEDULING/'dynamic_solo_v1/image.json')['image']
    container = 'termination-public-'+uuid.uuid4().hex
    result = {'status': 'withhold', 'container': container, 'removed': False, 'image': image}
    process = None; created = False
    try:
        subprocess.run(['docker', 'create', '--name', container, '--init', '--network', 'none',
                        '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                        '--pids-limit', '256', '--memory', '2g', '--cpus', '1', '--log-driver', 'none',
                        '--user', f'{os.getuid()}:{os.getgid()}', '-e', 'PYTHONDONTWRITEBYTECODE=1',
                        '--tmpfs', '/tmp:rw,nosuid,nodev,size=64m,mode=1777',
                        '--mount', f'type=bind,src={public},dst=/public,readonly',
                        '--mount', f'type=bind,src={output},dst=/work', image,
                        'python3', '/public/public_check.py', '--candidate', '/public/'+name+'.py',
                        '--output', '/work/public-result.json'], check=True, capture_output=True, timeout=15)
        created = True
        process = subprocess.Popen(['docker', 'start', '-a', container], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.communicate(timeout=900)
        result['returncode'] = process.returncode
        measured = cohort.read(output/'public-result.json')
        if process.returncode != 0 or measured['valid'] is not True:
            raise ValueError('public execution incomplete')
        result['status'] = 'measured'
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        result['failure'] = type(exc).__name__+': '+str(exc)
    finally:
        recovery = cohort.load('termination_public_recovery', HERE/'recovery.py').drain(
            container, create_completed=created, seconds=cohort.read(HERE/'config.json')['cleanup_observation_seconds'])
        result['recovery_audit'] = recovery
        result['removed'] = recovery['status'] == 'confirmed'
        if process is not None and process.poll() is None: process.kill(); process.communicate(timeout=3)
        cohort.save(output/'controller.json', result)
    return result


def execute(output):
    cohort = module(); plan = cohort.read(output/'plan.json')
    if cohort.identity() != plan['source_sha256']: raise ValueError('calibration source changed')
    inputs = cohort.prepare_inputs(output, False)
    assess = cohort.load('continuation_calibration_assess', HERE.parent/'deadline_capture_v1/assessment.py')
    result = {'status': 'withhold', 'source_sha256': plan['source_sha256'], 'input_seal': inputs,
              'live_provider_calls': 0, 'qualification_scored': False, 'public_cases_measured': {},
              'public_execution_matches_external': False, 'all_containers_removed': False, 'assessments': {}}
    handlers = {}
    def stop(signum, frame): raise cohort.StopRequested('public calibration interrupted')
    try:
        for sig in (signal.SIGINT, signal.SIGTERM): handlers[sig] = signal.signal(sig, stop)
        for name in ('fifo', 'initial'):
            independent = assess.evaluate(output/'public'/(name+'.py'), output/'public/development.json', output/('external-'+name))
            result['assessments'][name] = {'external_status': independent['status'], 'cleanup': independent['cleanup']}
            public = public_execution(cohort, output/'public', output/('actor-public-'+name), name)
            result['assessments'][name]['public'] = public
            if independent['status'] != 'measured' or public['status'] != 'measured' or not public['removed']:
                raise ValueError('public calibration incomplete: '+name)
            a = {r['id']: r['result'] for r in independent['evaluation']['cases']}
            b = {r['id']: r['result'] for r in cohort.read(output/('actor-public-'+name)/'public-result.json')['cases']}
            if len(a) != 24 or a != b: raise ValueError('public/external metrics or trace mismatch: '+name)
            result['public_cases_measured'][name] = len(a)
        if (cohort.identity() != plan['source_sha256']
                or {p.name: cohort.sha(p) for p in (output/'public').iterdir()} != inputs['public']
                or cohort.sha(output/'qualification.private.json') != inputs['assessment_sha256']):
            raise ValueError('calibration source/input changed')
        result.update(status='passed', public_execution_matches_external=True, all_containers_removed=True)
    except (cohort.StopRequested, OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        result['failure'] = type(exc).__name__+': '+str(exc)
    finally:
        recovery = cohort.load('termination_calibration_recovery', HERE/'recovery.py')
        audits = {folder.name: recovery.assessment(folder, cohort.read(HERE/'config.json')['cleanup_observation_seconds'])
                  for folder in sorted(output.glob('external-*')) if folder.is_dir()}
        result['recovery_audits'] = audits
        if any(r['status'] != 'confirmed' for rows in audits.values() for r in rows):
            result.update(status='withhold', all_containers_removed=False)
        cohort.save(output/'result.json', result)
        for sig, previous in handlers.items(): signal.signal(sig, previous)
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
    process = None; handlers = {}
    def stop(signum, frame): raise cohort.StopRequested('calibration controller interrupted')
    try:
        for sig in (signal.SIGINT, signal.SIGTERM): handlers[sig] = signal.signal(sig, stop)
        with (output/'controller.stdout').open('xb') as stdout, (output/'controller.stderr').open('xb') as stderr:
            process = subprocess.Popen([sys.executable, str(output/'source'/HERE.relative_to(cohort.ROOT)/'calibrate.py'),
                                        '--execute', '--output', str(output)], stdout=stdout, stderr=stderr,
                                       start_new_session=True)
            process.wait(timeout=3700)
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try: process.wait(timeout=45)
            except subprocess.TimeoutExpired: os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=3)
        for sig, previous in handlers.items(): signal.signal(sig, previous)
    return cohort.read(output/'result.json')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--execute', action='store_true', help=argparse.SUPPRESS)
    a = p.parse_args(); value = execute(a.output) if a.execute else run(a.output)
    print(json.dumps({'status': value['status']})); raise SystemExit(0 if value['status'] == 'passed' else 1)

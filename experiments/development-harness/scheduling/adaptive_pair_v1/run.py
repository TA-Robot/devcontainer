"""Single-use prospective pair; source snapshot, serial actors, external grading."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SCHEDULING = HERE.parent


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2); f.write('\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def identity():
    files = [HERE/n for n in ('run.py', 'config.json', 'protocol.md', 'solo.md', 'adaptive.md')]
    files += list((SCHEDULING/'native_actor_v1').glob('*.py')) + [SCHEDULING/'native_actor_v1/TASK.md']
    files += [SCHEDULING/'dynamic_solo_v1'/n for n in ('projection.py', 'TASK.md', 'fifo.py',
        'public_check.py', 'policy.json', 'model-catalog.json', 'image.json', 'Actor.Dockerfile')]
    files += [SCHEDULING/'dynamic_v1'/n for n in ('runtime.py', 'transport.py', 'workloads.py', 'TASK.md')]
    files += [SCHEDULING/'timing_diagnostic_v1'/n for n in ('runtime.py', 'transport.py', 'evaluate.py', 'TASK.md')]
    files += [ROOT/'scripts'/n for n in ('agent_contracts.py', 'agent_duration_cases/__init__.py',
        'agent_duration_fixtures.py', 'agent_duration_live.py', 'agent_duration_study.py', 'report-dynamic-solo-profile.py')]
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(files)}


def freeze_submission(source, target):
    fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as f:
        if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):
            raise ValueError('regular submission required')
        data = f.read(65537)
    if not 0 < len(data) <= 65536:
        raise ValueError('submission size')
    target.write_bytes(data); target.chmod(0o444)
    return sha(target)


def execute(output, fake, auth):
    """Called in a fresh process from the sealed source tree only."""
    config = read(HERE/'config.json'); plan = read(output/'plan.json')
    if (identity() != plan['source_sha256'] or plan['config'] != config
            or plan['execution'] != ('synthetic' if fake else 'live')):
        raise ValueError('source seal mismatch')
    actor = load('pair_native_actor', SCHEDULING/'native_actor_v1/actor.py')
    result = {'status': 'withhold', 'execution': 'synthetic' if fake else 'live',
              'actors': {}, 'assessments': {}, 'submission_sha256': {}, 'confirmation': False}
    began = time.monotonic()
    try:
        actor.prepare_public(output/'public')
        save(output/'public-seal.json', {p.name: sha(p) for p in (output/'public').iterdir()})
        cases = read(output/'public/probe.json') if fake else load('pair_workloads', SCHEDULING/'dynamic_v1/workloads.py').suite('qualification')
        save(output/'qualification.private.json', cases)
        (output/'actors').mkdir()
        for condition in config['conditions']:
            # Exclusive start records are written before any possible model call.
            save(output/('start-'+condition+'.json'), {'condition': condition, 'ordinal': len(result['actors'])+1,
                                                     'prompt_sha256': sha(HERE/(condition+'.md'))})
            r = actor.run(output/'actors'/condition, output/'public', condition=condition,
                prompt=(HERE/(condition+'.md')).read_text(), auth=auth, fake=fake,
                seconds=60 if fake else config['development_seconds'],
                output_tokens=config['output_tokens_per_condition'])
            result['actors'][condition] = r
            if r['status'] != 'completed' or not r['removed'] or not r['credential_copy_removed']:
                raise ValueError('incomplete '+condition+' actor')
            result['submission_sha256'][condition] = freeze_submission(
                output/'actors'/condition/'work/submission.py', output/(condition+'.py'))
        # Neither developer is active when qualification is opened for scoring.
        for condition in config['conditions']:
            directory = output/('assessment-'+condition)
            row = {'status': 'withhold', 'cleanup': 'unknown'}; result['assessments'][condition] = row
            process = None
            try:
                process = subprocess.Popen([sys.executable, str(SCHEDULING/'timing_diagnostic_v1/evaluate.py'),
                    '--candidate', str(output/(condition+'.py')), '--scenarios', str(output/'qualification.private.json'),
                    '--output', str(directory)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process.communicate(timeout=config['assessment_seconds_each'])
            finally:
                if process is not None and process.poll() is None:
                    process.terminate()
                    try: process.communicate(timeout=30)
                    except subprocess.TimeoutExpired: process.kill(); process.communicate(timeout=3)
                if (directory/'result.json').exists():
                    row['result'] = read(directory/'result.json')
                    if row['result'].get('all_containers_removed'): row['cleanup'] = 'confirmed'
            raw = row.get('result', {})
            seal = read(directory/'seal.json')
            expected_sources = {n: sha(SCHEDULING/'timing_diagnostic_v1'/n) for n in ('runtime.py','transport.py','evaluate.py','TASK.md')}
            expected_cases = hashlib.sha256(json.dumps(cases, sort_keys=True, allow_nan=False).encode()).hexdigest()
            if (process.returncode != 0 or raw.get('status') != 'completed' or row['cleanup'] != 'confirmed'
                    or len(raw['cases']) != len(cases) or {r['id'] for r in raw['cases']} != {c['id'] for c in cases}
                    or seal['source_sha256'] != expected_sources or seal['scenario_sha256'] != expected_cases
                    or seal['candidate_sha256'] != result['submission_sha256'][condition]):
                raise ValueError('incomplete or mismatched '+condition+' assessment')
            row['status'] = 'completed'
        if not fake:
            reporter = load('pair_quality_report', ROOT/'scripts/report-dynamic-solo-profile.py')
            quality = reporter.summarize({'submission': result['assessments']['adaptive']['result'],
                                          'reference': result['assessments']['solo']['result']})
            # Reuse the checked arithmetic while naming the actual conditions.
            for section in ('cells', 'bands', 'cases'):
                for row in quality[section].values():
                    row['adaptive'] = row.pop('submission'); row['solo'] = row.pop('reference')
            save(output/'quality.json', quality)
        if identity() != plan['source_sha256']:
            raise ValueError('source changed during execution')
        result['status'] = 'completed'
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        result['failure'] = type(exc).__name__+': '+str(exc)
    finally:
        result['elapsed_seconds'] = time.monotonic()-began
        save(output/'result.json', result)
    return result


def run(output, *, fake=False, auth=None):
    config = read(HERE/'config.json'); initial = identity()
    if not fake:
        ready = read(HERE/'validation.json')
        if ready['status'] != 'passed' or ready['source_sha256'] != initial:
            raise ValueError('source-matched pair preflight required')
        expected = Path.home()/'.local/state/devcontainer-evaluations'/config['campaign']
        if output.resolve() != expected:
            raise ValueError('fixed single-use campaign location required')
    output = output.resolve(); output.mkdir(parents=True, mode=0o700, exist_ok=False)
    source = output/'source'
    for name, expected in initial.items():
        data = (ROOT/name).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected: raise ValueError('source changed during snapshot')
        target = source/name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data); target.chmod(0o444)
    save(output/'plan.json', {'source_sha256': initial, 'config': config, 'execution': 'synthetic' if fake else 'live'})
    args = [sys.executable, str(source/HERE.relative_to(ROOT)/'run.py'), '--execute', '--output', str(output)]
    if fake: args += ['--fake']
    if auth is not None: args += ['--auth', str(auth.resolve())]
    process = None; record = {'status': 'withhold', 'recovery': {}}
    began = time.monotonic()
    try:
        with (output/'controller.stdout').open('xb') as stdout, (output/'controller.stderr').open('xb') as stderr:
            process = subprocess.Popen(args, stdout=stdout, stderr=stderr, start_new_session=True)
            process.wait(timeout=240 if fake else config['outer_seconds'])
        record['returncode'] = process.returncode
    except (OSError, subprocess.SubprocessError) as exc:
        record['failure'] = type(exc).__name__
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try: process.wait(timeout=30)
            except subprocess.TimeoutExpired: os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=3)
        for condition in config['conditions']:
            start = output/'actors'/condition/'start.json'
            if start.exists():
                name = read(start)['container']
                removal = subprocess.run(['docker','rm','-f',name], capture_output=True, text=True, timeout=15)
                record['recovery'][condition] = removal.returncode == 0 or 'No such container' in removal.stderr
        if (output/'result.json').exists():
            inner = read(output/'result.json')
            if inner['status'] == 'completed' and record.get('returncode') == 0 and all(record['recovery'].values()):
                record['status'] = 'completed'
        record['elapsed_seconds'] = time.monotonic()-began
        save(output/'controller.json', record)
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--auth', type=Path)
    parser.add_argument('--fake', action='store_true')
    parser.add_argument('--execute', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    result = execute(args.output, args.fake, args.auth) if args.execute else run(args.output, fake=args.fake, auth=args.auth)
    print(json.dumps({'status': result['status']}))
    raise SystemExit(0 if result['status'] == 'completed' else 1)

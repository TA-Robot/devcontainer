"""Finite continuation pair from a shared strong artifact; immutable dependencies."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SCHEDULING = HERE.parent
PROMPTS = {name: SCHEDULING/'adaptive_pair_v1'/(name+'.md') for name in ('solo', 'adaptive')}


class StopRequested(RuntimeError): pass


def read(path): return json.loads(path.read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def actor_module(): return load('cohort_actor', SCHEDULING/'native_recovery_v1/actor.py')


def identity():
    result = actor_module().identity()
    files = list(HERE.glob('*.py')) + [HERE/'config.json', HERE/'protocol.md',
             SCHEDULING/'native_recovery_v1/validation.json',
             ROOT/'scripts/test-scheduling-continuation.py', ROOT/'scripts/report-dynamic-solo-profile.py',
             HERE/'initial-policy.txt', HERE/'INITIAL.md', SCHEDULING/'refinement_cohort_v1/populations.py']
    files += list(PROMPTS.values())
    result.update({str(path.relative_to(ROOT)): sha(path) for path in files})
    return dict(sorted(result.items()))


def prepare_inputs(output, fake):
    actor = actor_module(); actor.prepare_public(output/'public')
    populations = load('cohort_populations', SCHEDULING/'refinement_cohort_v1/populations.py').generate(read(HERE/'config.json'))
    runtime = load('cohort_public_runtime', SCHEDULING/'dynamic_v1/runtime.py')
    for cases in populations.values():
        for case in cases: runtime.validate(case)
    (output/'public/development.json').write_text(json.dumps(populations['development'])+'\n')
    cases = read(output/'public/probe.json') if fake else populations['qualification']
    initial = (HERE/'initial-policy.txt').read_bytes()
    if hashlib.sha256(initial).hexdigest() != read(HERE/'config.json')['initial_sha256']:
        raise ValueError('initial artifact changed')
    (output/'public/initial.py').write_bytes(initial)
    (output/'public/INITIAL.md').write_bytes((HERE/'INITIAL.md').read_bytes())
    save(output/'qualification.private.json', cases)
    seal = {'public': {p.name: sha(p) for p in sorted((output/'public').iterdir())},
            'assessment_sha256': sha(output/'qualification.private.json'),
            'population': read(HERE/'config.json')['campaign']}
    save(output/'input-seal.json', seal)
    return seal


def barrier(output, actors):
    config = read(HERE/'config.json'); inputs = read(output/'input-seal.json')
    if set(actors) != set(config['conditions']): raise ValueError('all conditions required before assessment')
    result = {}
    for name in config['conditions']:
        folder = output/'actors'/name; record = actors[name]
        if (read(folder/'result.json') != record or record['quality']['status'] != 'eligible'
                or record['cleanup']['status'] != 'confirmed' or record['artifact']['status'] != 'sealed'
                or not record['source_unchanged'] or (folder/'submission.py').is_symlink()
                or sha(folder/'submission.py') != record['artifact']['sha256']):
            raise ValueError('ineligible or changed '+name+' artifact')
        if {p.name: sha(p) for p in (folder/'public').iterdir()} != inputs['public']:
            raise ValueError('different public projection')
        if sha(folder/'public/initial.py') != config['initial_sha256']:
            raise ValueError('different initial source')
        if sha(folder/'prompt.private.txt') != read(output/('start-'+name+'.json'))['prompt_sha256']:
            raise ValueError('actor prompt changed')
        result[name] = {'submission_sha256': record['artifact']['sha256'], 'actor_result_sha256': sha(folder/'result.json')}
    if sha(output/'qualification.private.json') != inputs['assessment_sha256']:
        raise ValueError('assessment population changed')
    if sha(output/'public/initial.py') != config['initial_sha256']:
        raise ValueError('initial baseline changed')
    result['initial'] = {'submission_sha256': config['initial_sha256']}
    return result


def execute(output, fake, auth, fake_case):
    config = read(HERE/'config.json'); plan = read(output/'plan.json')
    if (identity() != plan['source_sha256'] or plan['config'] != config or plan['fake_case'] != fake_case
            or plan['execution'] != ('synthetic' if fake else 'live')):
        raise ValueError('source/config/execution seal mismatch')
    if not fake:
        if output != Path.home()/'.local/state/devcontainer-evaluations'/config['campaign']:
            raise ValueError('fixed live location required')
        if fake_case != 'normal' or plan['admission']['source_sha256'] != identity():
            raise ValueError('live admission required')
    save(output/'execution-start.json', {'execution': plan['execution'], 'monotonic_ns': time.monotonic_ns()})
    result = {'status': 'withhold', 'execution': plan['execution'], 'actors': {}, 'assessments': {},
              'quality_status': 'withhold', 'output_budget_admission': 'withhold', 'confirmation': False}
    began = time.monotonic()
    handlers = {}
    def stop(signum, frame): raise StopRequested('cohort interrupted')
    try:
        for sig in (signal.SIGTERM, signal.SIGINT): handlers[sig] = signal.signal(sig, stop)
        inputs = prepare_inputs(output, fake)
        if not fake and inputs != plan['admission']['public_calibration']['input_seal']:
            raise ValueError('inputs differ from source-matched public calibration')
        (output/'actors').mkdir()
        for name in config['conditions']:
            if len(result['actors']) >= config['max_live_starts']: raise ValueError('start cap')
            prompt = PROMPTS[name].read_text()+'\n'+(HERE/'INITIAL.md').read_text()
            save(output/('start-'+name+'.json'), {'condition': name, 'ordinal': len(result['actors'])+1,
                                                 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest()})
            mode = 'fork_none' if name == 'solo' else 'fork_all'
            seconds = 60 if fake else config['development_seconds']
            cap = config['output_tokens_per_condition']
            if fake and name == 'solo':
                if fake_case == 'missing': mode = 'missing_usage'
                elif fake_case == 'timeout': mode, seconds = 'timeout', 8
                elif fake_case == 'cost': cap = 10
            row = load('continuation_adapter', HERE/'adapter.py').run(
                output/'actors'/name, output/'public', condition=name,
                prompt=prompt,
                fake=fake, fake_mode=mode, seconds=seconds, output_tokens=cap, auth=auth)
            result['actors'][name] = row
            if row['quality']['status'] != 'eligible':
                raise ValueError('actor not eligible: '+name)
        sealed = barrier(output, result['actors'])
        save(output/'barrier.json', {'actors': sealed, 'monotonic_ns': time.monotonic_ns()})
        grader = load('cohort_grader', SCHEDULING/'native_recovery_v1/assess.py')
        for name in ('initial', *config['conditions']):
            if barrier(output, result['actors']) != sealed: raise ValueError('barrier changed')
            if name == 'initial':
                assessed = load('continuation_baseline_assess', HERE/'assessment.py').evaluate(
                    output/'public/initial.py', output/'qualification.private.json',
                    output/'assessment-initial', seconds=120 if fake else config['assessment_seconds_each'])
            else:
                assessed = grader.assess(output/'actors'/name, output/'qualification.private.json',
                                         output/('assessment-'+name), seconds=120 if fake else config['assessment_seconds_each'])
            result['assessments'][name] = assessed
            if assessed['status'] != 'measured': raise ValueError('assessment '+name+': '+assessed['status'])
        if identity() != plan['source_sha256']: raise ValueError('source changed during cohort')
        result['quality_status'] = 'measured'
        result['output_budget_admission'] = ('admitted' if all(r['admission'] == 'admitted' for r in result['actors'].values()) else 'withhold')
        if not fake:
            report = load('cohort_quality', HERE/'report.py').summarize(result, read(output/'input-seal.json'))
            save(output/'quality.json', report)
        result['status'] = 'completed'
    except (StopRequested, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        result['failure'] = type(exc).__name__+': '+str(exc)
    finally:
        result['elapsed_seconds'] = time.monotonic()-began
        save(output/'result.json', result)
        for sig, previous in handlers.items(): signal.signal(sig, previous)
    return result


def run(output, *, fake=False, auth=None, fake_case='normal'):
    config = read(HERE/'config.json'); initial = identity()
    if fake_case not in ('normal', 'missing', 'timeout', 'cost'): raise ValueError('fake case')
    admission = None
    if not fake:
        admission = read(HERE/'validation.json')
        native = read(SCHEDULING/'native_recovery_v1/validation.json')
        if (fake_case != 'normal' or admission['status'] != 'passed' or admission['source_sha256'] != initial
                or native['status'] != 'passed' or native['source_sha256'] != actor_module().identity()):
            raise ValueError('source-matched native and cohort validation required')
        calibrated = admission['public_calibration']
        if (calibrated['status'] != 'passed' or calibrated['source_sha256'] != initial
                or calibrated['public_cases_measured'] != {'fifo': 24, 'initial': 24} or not calibrated['all_containers_removed']
                or calibrated['public_execution_matches_external'] is not True):
            raise ValueError('full source-matched public calibration required')
        if output.resolve() != Path.home()/'.local/state/devcontainer-evaluations'/config['campaign']:
            raise ValueError('fixed single-use live location required')
        sys.path.insert(0, str(ROOT/'scripts'))
        from agent_duration_live import _validate_provider_credential_window
        if auth is None: raise ValueError('live credential required')
        _validate_provider_credential_window('codex', auth, timeout_seconds=config['outer_seconds'])
    output = output.resolve(); output.mkdir(parents=True, mode=0o700, exist_ok=False)
    for name, expected in initial.items():
        data = (ROOT/name).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected: raise ValueError('source changed during snapshot')
        target = output/'source'/name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data); target.chmod(0o444)
    save(output/'plan.json', {'source_sha256': initial, 'config': config, 'admission': admission,
                            'execution': 'synthetic' if fake else 'live', 'fake_case': fake_case})
    args = [sys.executable, str(output/'source'/HERE.relative_to(ROOT)/'run.py'), '--execute', '--output', str(output), '--fake-case', fake_case]
    if fake: args += ['--fake']
    if auth is not None: args += ['--auth', str(auth.resolve())]
    process = None; result = {'status': 'withhold', 'recovery': {}}
    began = time.monotonic()
    handlers = {}
    def stop(signum, frame): raise StopRequested('outer cohort interrupted')
    try:
        for sig in (signal.SIGTERM, signal.SIGINT): handlers[sig] = signal.signal(sig, stop)
        with (output/'controller.stdout').open('xb') as stdout, (output/'controller.stderr').open('xb') as stderr:
            process = subprocess.Popen(args, stdout=stdout, stderr=stderr, start_new_session=True)
            process.wait(timeout=300 if fake else config['outer_seconds'])
        result['returncode'] = process.returncode
    except (StopRequested, OSError, subprocess.SubprocessError) as exc:
        result['failure'] = type(exc).__name__
    finally:
        for sig in handlers: signal.signal(sig, signal.SIG_IGN)
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try: process.wait(timeout=30)
            except subprocess.TimeoutExpired: os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=3)
        for name in config['conditions']:
            folder = output/'actors'/name
            if not (folder/'start.json').exists(): continue
            try:
                container = read(folder/'start.json')['container']
                if not re.fullmatch(r'scheduling-native-[0-9a-f]{32}', container): raise ValueError('unowned container')
                removed = subprocess.run(['docker', 'rm', '-f', container], capture_output=True, text=True, timeout=15)
                (folder/'auth.private.json').unlink(missing_ok=True)
                result['recovery'][name] = (removed.returncode == 0 or 'No such container' in removed.stderr) and not (folder/'auth.private.json').exists()
            except (OSError, ValueError, KeyError, subprocess.SubprocessError): result['recovery'][name] = False
        if (output/'result.json').exists():
            inner = read(output/'result.json')
            result['quality_status'] = inner['quality_status']
            result['output_budget_admission'] = inner['output_budget_admission']
            if (inner['status'] == 'completed' and result.get('returncode') == 0
                    and set(result['recovery']) == set(config['conditions']) and all(result['recovery'].values())):
                result['status'] = 'completed'
        result['elapsed_seconds'] = time.monotonic()-began
        save(output/'controller.json', result)
        for sig, previous in handlers.items(): signal.signal(sig, previous)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--fake', action='store_true'); p.add_argument('--fake-case', default='normal')
    p.add_argument('--auth', type=Path); p.add_argument('--execute', action='store_true', help=argparse.SUPPRESS)
    a = p.parse_args()
    result = execute(a.output, a.fake, a.auth, a.fake_case) if a.execute else run(a.output, fake=a.fake, auth=a.auth, fake_case=a.fake_case)
    print(json.dumps({'status': result['status'], 'quality_status': result.get('quality_status'),
                      'output_budget_admission': result.get('output_budget_admission')}))
    raise SystemExit(0 if result['status'] == 'completed' else 1)

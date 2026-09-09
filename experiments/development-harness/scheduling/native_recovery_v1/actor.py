"""Seal after container removal, then separate lifecycle, usage and budget."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
SOLO = HERE.parent / 'dynamic_solo_v1'
LEGACY = HERE.parent / 'native_actor_v1'
TIMING = HERE.parent / 'timing_diagnostic_v1'
ROOT = HERE.parents[3]


def identity():
    files = list(HERE.glob('*.py')) + list(LEGACY.glob('*.py')) + [LEGACY/'TASK.md']
    files += [SOLO/n for n in ('projection.py', 'TASK.md', 'fifo.py', 'public_check.py',
                               'policy.json', 'model-catalog.json', 'image.json', 'Actor.Dockerfile')]
    files += [HERE.parent/'dynamic_v1'/n for n in ('runtime.py', 'transport.py', 'workloads.py', 'TASK.md')]
    files += [TIMING/n for n in ('runtime.py', 'transport.py', 'evaluate.py', 'TASK.md')]
    files += [ROOT/'scripts'/n for n in ('test-native-recovery.py', 'agent_contracts.py',
        'agent_duration_cases/__init__.py', 'agent_duration_fixtures.py', 'agent_duration_live.py', 'agent_duration_study.py')]
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(files)}


class StopRequested(RuntimeError):
    pass


def read(path):
    return json.loads(path.read_text())


def save(path, data):
    with path.open('x') as f:
        json.dump(data, f, indent=2)
        f.write('\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def freeze_submission(source, target):
    fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('regular submission required')
        data = stream.read(65537)
    if not 0 < len(data) <= 65536:
        raise ValueError('submission size')
    with target.open('xb') as stream:
        stream.write(data)
    target.chmod(0o444)
    return hashlib.sha256(data).hexdigest()


def finish(output, report, *, condition, seconds, output_tokens):
    """Container and credentials must be gone before model-owned bytes are sealed."""
    report.update(artifact={'status': 'unavailable'}, quality={'status': 'withhold'},
                  lifecycle={'status': 'unknown'}, usage={'status': 'unknown', 'known_usage': None},
                  budget={'wall_clock': 'unknown', 'output_tokens': 'unknown'},
                  cleanup={'status': 'confirmed' if report['removed'] and report['credential_copy_removed'] else 'unknown'},
                  milestones=[], admission='withhold')
    def mark(name):
        report['milestones'].append({'stage': name, 'monotonic_ns': time.monotonic_ns()})
    if report['cleanup']['status'] != 'confirmed' or not report['source_unchanged']:
        report['quality']['reason'] = 'cleanup or source integrity unknown'
        return
    mark('container_removed_and_credentials_absent')
    try:
        report['artifact'] = {'status': 'sealed', 'sha256': freeze_submission(
            output/'work/submission.py', output/'submission.py')}
        save(output/'submission-seal.json', report['artifact'])
        mark('artifact_sealed')
    except (OSError, ValueError) as exc:
        report['artifact']['reason'] = type(exc).__name__ + ': ' + str(exc)
    bridge = report.get('bridge', {})
    elapsed = bridge.get('development_seconds')
    if isinstance(elapsed, (int, float)) and not isinstance(elapsed, bool) and elapsed >= 0:
        report['budget']['wall_clock'] = 'within' if elapsed <= seconds else 'exceeded'
    try:
        mark('accounting_started')
        observation = load('recovery_observations', HERE/'observations.py').inspect(
            output/'observation/sessions.private', output/'observation/inventory.sqlite', condition)
        save(output/'observations.json', observation)
        report['lifecycle'] = observation['lifecycle']
        report['usage'] = observation['usage']
        mark('accounting_finished')
        known = observation['usage']['known_usage']
        if known is not None and known['output_tokens'] > output_tokens:
            report['budget']['output_tokens'] = 'exceeded'
        elif observation['usage']['status'] == 'complete':
            report['budget']['output_tokens'] = 'within'
    except (OSError, ValueError, KeyError, TypeError) as exc:
        report['observation_failure'] = type(exc).__name__ + ': ' + str(exc)
    normal = (bridge.get('status') == 'completed' and bridge.get('returncode') == 0
              and bridge.get('reason') is None and report.get('returncode') == 0
              and not report.get('failure') and not report.get('collection_failure'))
    if (normal and report['artifact']['status'] == 'sealed'
            and report['lifecycle']['status'] == 'completed' and report['budget']['wall_clock'] == 'within'):
        report['quality'] = {'status': 'eligible', 'scope': 'selected artifact, independent assessment pending'}
    else:
        report['quality']['reason'] = 'normal participant completion, time or selected source not established'
    report['admission'] = ('admitted' if report['quality']['status'] == 'eligible'
                           and report['usage']['status'] == 'complete'
                           and report['budget']['output_tokens'] == 'within' else 'withhold')
    report['status'] = 'recovered' if report['artifact']['status'] == 'sealed' else 'withhold'


def prepare_public(output):
    spec = importlib.util.spec_from_file_location('native_public_projection', SOLO / 'projection.py')
    projection = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(projection)
    projection.prepare(output)
    # Same revised prospective clock for both developer conditions. The
    # physical runtime is byte-identical; the old public source is untouched.
    shutil.copyfile(TIMING / 'transport.py', output / 'transport.py')
    shutil.copyfile(LEGACY / 'TASK.md', output / 'TASK.md')
    runtime_doc = output / 'RUNTIME.md'
    text = runtime_doc.read_text()
    if 'response and 30 seconds per scenario' not in text:
        raise ValueError('unexpected historical clock contract')
    runtime_doc.write_text(text.replace('response and 30 seconds per scenario', 'response and 90 seconds per scenario'))
    return {p.name: sha(p) for p in output.iterdir()}


def run(output, public, *, condition, prompt, auth=None, fake=False,
        fake_mode='fork_all', seconds=2400, output_tokens=80000):
    if condition not in ('solo', 'adaptive'):
        raise ValueError('condition')
    if seconds <= 0 or output_tokens <= 0:
        raise ValueError('positive budgets required')
    output = Path(output).resolve()
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    sources = output / 'source'; sources.mkdir()
    policy = output / 'policy'; policy.mkdir()
    work = output / 'work'; work.mkdir()
    observation = output / 'observation'; observation.mkdir(mode=0o700)
    exposed = output / 'public'
    shutil.copytree(public, exposed)
    shutil.copyfile(HERE / 'entry.py', sources / 'codex')
    shutil.copyfile(LEGACY / 'accounting.py', sources / 'accounting.py')
    fixture = (HERE/'notice_probe.py' if fake_mode.startswith('notice_') else
               LEGACY/('fake_adaptive.py' if condition == 'adaptive' else 'fake_solo.py'))
    shutil.copyfile(fixture, sources / 'probe.py')
    shutil.copyfile(HERE / 'actor.py', sources / 'actor.py')
    shutil.copyfile(HERE / 'observations.py', sources / 'observations.py')
    (sources / 'codex').chmod(0o555)
    config = read(SOLO / 'policy.json')
    config['features.multi_agent'] = condition == 'adaptive'
    catalog = read(SOLO / 'model-catalog.json')
    for model in catalog['models']:
        model['multi_agent_version'] = 'v2' if condition == 'adaptive' else None
    save(policy / 'policy.json', config)
    save(policy / 'model-catalog.json', catalog)
    save(policy / 'mode.json', {'mode': fake_mode})
    save(policy / 'limits.json', {'condition': condition, 'development_seconds': seconds,
                                 'output_tokens': output_tokens, 'output_bytes': 16777216})
    prompt_path = output / 'prompt.private.txt'; prompt_path.write_text(prompt)
    image = read(SOLO / 'image.json')['image']
    name = 'scheduling-native-' + uuid.uuid4().hex
    report = {'status': 'withhold', 'condition': condition, 'container': name, 'image': image,
              'removed': False, 'credential_copy_removed': False, 'admission': 'withhold',
              'execution': 'synthetic' if fake else 'live'}
    seal = {str(p.relative_to(output)): sha(p)
            for directory in (sources, policy, exposed) for p in directory.iterdir()}
    for directory in (sources, policy, exposed):
        for p in directory.iterdir():
            p.chmod(0o555 if p.name == 'codex' else 0o444)
    save(output / 'seal.json', seal)
    save(output / 'start.json', report)
    credential = output / 'auth.private.json'
    began = time.monotonic()
    process = None
    handlers = {}

    def stop(signum, frame):
        raise StopRequested('actor controller interrupted')

    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            handlers[sig] = signal.signal(sig, stop)
        if not fake:
            if auth is None:
                raise ValueError('live credential required')
            sys.path.insert(0, str(HERE.parents[3] / 'scripts'))
            from agent_duration_live import _validate_provider_credential_window
            ready = _validate_provider_credential_window('codex', auth, timeout_seconds=seconds + 45)
            shutil.copyfile(ready, credential); credential.chmod(0o600)
        args = ['docker', 'create', '-i', '--name', name, '--init', '--network', 'none' if fake else 'bridge',
                '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                '--security-opt', 'seccomp=unconfined', '--pids-limit', '256', '--memory', '2g', '--cpus', '1',
                '--user', f'{os.getuid()}:{os.getgid()}', '--log-driver', 'none',
                '--tmpfs', '/codex:rw,nosuid,nodev,size=64m,mode=1777',
                '--tmpfs', '/tmp:rw,nosuid,nodev,size=64m,mode=1777',
                '-e', 'PATH=/bridge:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin']
        for origin, dest, ro in [(sources, '/bridge', True), (sources, '/probe', True),
                                  (policy, '/policy', True), (exposed, '/public', True),
                                  (work, '/work', False), (observation, '/observation', False)]:
            args += ['--mount', f'type=bind,src={origin},dst={dest}' + (',readonly' if ro else '')]
        if not fake:
            args += ['--mount', f'type=bind,src={credential},dst=/codex/auth.json,readonly']
        args += [image]
        if fake:
            args += ['python3', '/probe/probe.py']
        else:
            args += ['/bridge/codex', 'exec', '--ignore-user-config', '--ignore-rules',
                     '--skip-git-repo-check', '--json', '--model', 'gpt-6-astra',
                     '-c', 'model_reasoning_effort="high"', '-c', 'model_catalog_json="/policy/model-catalog.json"']
            for key, value in config.items():
                args += ['-c', key + '=' + json.dumps(value)]
            args += ['-']
        subprocess.run(args, check=True, capture_output=True, timeout=15)
        with prompt_path.open('rb') as stdin, (output / 'stdout.private.txt').open('xb') as stdout, (output / 'stderr.private.txt').open('xb') as stderr:
            process = subprocess.Popen(['docker', 'start', '-ai', name], stdin=stdin, stdout=stdout, stderr=stderr)
            process.wait(timeout=seconds + 20)
        report['returncode'] = process.returncode
    except (StopRequested, OSError, ValueError, subprocess.SubprocessError) as exc:
        report['failure'] = type(exc).__name__ + ': ' + str(exc)
    finally:
        for sig in handlers:
            signal.signal(sig, signal.SIG_IGN)
        try:
            report['removed'] = subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=15).returncode == 0
        except (OSError, subprocess.SubprocessError):
            pass
        if process is not None and process.poll() is None:
            process.kill(); process.wait(timeout=3)
        credential.unlink(missing_ok=True)
        report['credential_copy_removed'] = not credential.exists()
        try:
            if (observation / 'bridge.json').exists():
                report['bridge'] = read(observation / 'bridge.json')
        except (OSError, ValueError, TypeError, KeyError) as exc:
            report['collection_failure'] = type(exc).__name__
        try:
            report['source_unchanged'] = all(sha(output / n) == h for n, h in seal.items())
        except OSError:
            report['source_unchanged'] = False
        finish(output, report, condition=condition, seconds=seconds, output_tokens=output_tokens)
        report['elapsed_seconds'] = time.monotonic() - began
        save(output / 'result.json', report)
        for sig, previous in handlers.items():
            signal.signal(sig, previous)
    return report

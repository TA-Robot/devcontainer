"""Fresh native solo/adaptive actor with one lifecycle bridge and private evidence."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
SOLO = HERE.parent / 'dynamic_solo_v1'
PROBE = HERE.parent / 'native_probe_v1'
TIMING = HERE.parent / 'timing_diagnostic_v1'


def read(path):
    return json.loads(path.read_text())


def save(path, data):
    with path.open('x') as f:
        json.dump(data, f, indent=2)
        f.write('\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_public(output):
    spec = importlib.util.spec_from_file_location('native_public_projection', SOLO / 'projection.py')
    projection = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(projection)
    projection.prepare(output)
    # Same revised prospective clock for both developer conditions. The
    # physical runtime is byte-identical; the old public source is untouched.
    shutil.copyfile(TIMING / 'transport.py', output / 'transport.py')
    shutil.copyfile(HERE / 'TASK.md', output / 'TASK.md')
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
    shutil.copyfile(PROBE / 'accounting.py', sources / 'accounting.py')
    shutil.copyfile(HERE / ('fake_adaptive.py' if condition == 'adaptive' else 'fake_solo.py'), sources / 'probe.py')
    shutil.copyfile(HERE / 'actor.py', sources / 'actor.py')
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
              'removed': False, 'credential_copy_removed': False, 'usage': None,
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
        raise InterruptedError('actor controller interrupted')

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
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
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
                if (report['removed'] and report.get('returncode') == 0
                        and report['bridge']['status'] == 'completed' and not report.get('failure')):
                    report['status'] = 'completed'
                    report['usage'] = report['bridge']['usage']
        except (OSError, ValueError, TypeError, KeyError) as exc:
            report['collection_failure'] = type(exc).__name__
            report['status'] = 'withhold'; report['usage'] = None
        try:
            report['source_unchanged'] = all(sha(output / n) == h for n, h in seal.items())
        except OSError:
            report['source_unchanged'] = False
        if not report['source_unchanged']:
            report['status'] = 'withhold'; report['usage'] = None
        report['elapsed_seconds'] = time.monotonic() - began
        save(output / 'result.json', report)
        for sig, previous in handlers.items():
            signal.signal(sig, previous)
    return report

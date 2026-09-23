"""Bounded first-task pilot. All repository execution and sealing is in Docker."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import time
import uuid

HERE = Path(__file__).resolve().parent
TASK_IMAGE = 'ghcr.io/scaleapi/swe-bench_pro-v2@sha256:74ef826866ce57312db8311f14ec0c2ce2d03570028b5951653607f0ed72fb79'


def save(path, value):
    with path.open('x') as out:
        json.dump(value, out, indent=2)
        out.write('\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_command(args, log, seconds):
    with log.open('xb') as out:
        return subprocess.run(args, stdout=out, stderr=subprocess.STDOUT, timeout=seconds).returncode


def capture_tar(name, source, target, limit):
    def cap():
        resource.setrlimit(resource.RLIMIT_FSIZE, (limit, limit))
    with target.open('xb') as out:
        subprocess.run(['docker', 'cp', name+':'+source, '-'], stdout=out,
                       stderr=subprocess.PIPE, timeout=120, check=True, preexec_fn=cap)


def actor(output, *, image, control, auth=None, fake=True):
    """One start; always attempt stopped source capture before destroying credentials."""
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    shutil.copytree(control, output/'control')
    control = output/'control'
    for p in HERE.glob('*.py'):
        shutil.copy2(p, control/p.name)
    observation = output/'observation'
    observation.mkdir()
    limits = json.loads((control/'limits.json').read_text())
    credential = output/'auth.private.json'
    name = 'repository-pilot-'+uuid.uuid4().hex
    record = {'container': name, 'image': image, 'kind': 'synthetic' if fake else 'live',
              'started_at': time.time(), 'removed': False, 'capture': 'unavailable'}
    sources = {str(p.relative_to(control)): sha(p) for p in control.iterdir()}
    save(output/'source-sha256.json', sources)
    # Exclusive output + start file is the no-retry ledger for this invocation.
    save(output/'start.json', record)
    started = time.monotonic()
    try:
        if fake:
            credential.write_text('synthetic sentinel, not a credential\n')
        else:
            if auth is None:
                raise ValueError('credential required')
            shutil.copyfile(auth, credential)
        credential.chmod(0o600)
        args = ['docker', 'create', '--name', name, '--init', '--network', 'none' if fake else 'bridge',
                '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--security-opt', 'seccomp=unconfined',
                '--cpus', '1', '--memory', '4g', '--pids-limit', '512', '--log-driver', 'none']
        for source, dest, ro in ((control, '/control', True), (observation, '/observation', False),
                                  (credential, '/codex/auth.json', True)):
            args += ['--mount', f'type=bind,src={source},dst={dest}'+(',readonly' if ro else '')]
        args += ['--entrypoint', 'python', image, '/control/probe.py' if fake else '/control/entry.py']
        subprocess.run(args, capture_output=True, check=True, timeout=30)
        record['container_returncode'] = run_command(['docker', 'start', '-a', name], output/'container.log', limits['development_seconds']+30)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        record['failure'] = type(exc).__name__+': '+str(exc)[:300]
    finally:
        stopped = subprocess.run(['docker', 'stop', '-t', '5', name], capture_output=True, timeout=15).returncode == 0
        record['stopped'] = stopped
        if stopped:
            try:
                capture_tar(name, '/app', output/'workspace.tar', 512*1024*1024)
                record['capture'] = 'stopped_workspace'
                # No auth.json, config, SQLite prompt columns or entire CODEX_HOME copy.
                capture_tar(name, '/codex/sessions', output/'sessions.private.tar', 64*1024*1024)
            except (OSError, subprocess.SubprocessError) as exc:
                record['capture_failure'] = type(exc).__name__+': '+str(exc)[:300]
        record['removed'] = subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=20).returncode == 0
        credential.unlink(missing_ok=True)
        record['credential_copy_removed'] = not credential.exists()
        record['source_unchanged'] = all(sha(control/n) == h for n, h in sources.items())
        record['elapsed_seconds'] = time.monotonic()-started
        save(output/'recovery.json', record)
    if not (record['removed'] and record['credential_copy_removed'] and record['source_unchanged']):
        raise RuntimeError('cleanup or source integrity unknown')
    if record['capture'] == 'stopped_workspace':
        sealed = output/'sealed'
        sealed.mkdir()
        seal_name = name+'-seal'
        try:
            rc = run_command(['docker', 'run', '--name', seal_name, '--network', 'none', '--cpus', '1', '--memory', '4g',
                '--mount', f'type=bind,src={output},dst=/input,readonly',
                '--mount', f'type=bind,src={sealed},dst=/output',
                '--entrypoint', 'python', TASK_IMAGE, '/input/control/seal.py'], output/'seal.log', 180)
            if rc != 0:
                raise RuntimeError('patch sealing failed')
        finally:
            subprocess.run(['docker', 'rm', '-f', seal_name], capture_output=True, timeout=20, check=True)
    return record


def evaluate(output, task, patch):
    output.mkdir(parents=True, exist_ok=False)
    name = 'repository-pilot-evaluate-'+uuid.uuid4().hex
    started = time.monotonic()
    result = {'patch_sha256': sha(patch), 'reward': None}
    try:
        result['returncode'] = run_command(['docker', 'run', '--name', name, '--network', 'none',
            '--cpus', '1', '--memory', '4g', '--pids-limit', '512',
            '--mount', f'type=bind,src={task}/tests,dst=/tests,readonly',
            '--mount', f'type=bind,src={patch},dst=/submission.patch,readonly',
            '--mount', f'type=bind,src={output},dst=/logs/verifier',
            '--entrypoint', '/bin/bash', TASK_IMAGE, '-c',
            'git apply --allow-empty /submission.patch && bash /tests/test.sh'], output/'container.log', 3000)
    except subprocess.TimeoutExpired:
        result['timeout'] = True
    finally:
        result['removed'] = subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=20).returncode == 0
        result['seconds'] = time.monotonic()-started
        if (output/'reward.txt').exists():
            result['reward'] = (output/'reward.txt').read_text().strip()
        save(output/'result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['probe', 'live', 'evaluate'])
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--image')
    parser.add_argument('--control', type=Path)
    parser.add_argument('--auth', type=Path)
    parser.add_argument('--task', type=Path)
    parser.add_argument('--patch', type=Path)
    args = parser.parse_args()
    if args.mode == 'evaluate':
        result = evaluate(args.output.resolve(), args.task.resolve(), args.patch.resolve())
    else:
        result = actor(args.output.resolve(), image=args.image, control=args.control.resolve(),
                       auth=args.auth, fake=args.mode == 'probe')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Finite, serial development stages; observations are not acceptance decisions.

Each stage gets a fresh ephemeral Codex session and the released task history.
Source persists across stages. No raw reasoning or automatic evaluator feedback
is retained. Evidence lives outside the candidate workspace.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import tarfile
import time


class CampaignError(RuntimeError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save(path: Path, data: dict) -> None:
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        os.chmod(temporary, 0o600)
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def positive(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise CampaignError(f'{name} must be finite and positive')
    return value


def validate(manifest: dict) -> None:
    if manifest.get('schema_version') != 1 or manifest.get('scale') not in ('small', 'large'):
        raise CampaignError('unsupported campaign schema or scale')
    for key in ('study_id', 'condition', 'model', 'effort', 'cli_version'):
        if not isinstance(manifest.get(key), str) or not manifest[key]:
            raise CampaignError(f'missing {key}')
    for key in ('max_seconds', 'max_sessions', 'max_output_tokens', 'checkpoint_seconds', 'max_snapshot_bytes'):
        positive(manifest.get(key), key)
    if type(manifest['max_sessions']) is not int or type(manifest['max_output_tokens']) is not int:
        raise CampaignError('session and output-token caps must be integers')
    phases = manifest.get('phases')
    if not isinstance(phases, list) or not phases:
        raise CampaignError('at least one phase is required')
    names = []
    for phase in phases:
        name = phase.get('id', '')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', name):
            raise CampaignError('invalid phase id')
        names.append(name)
        positive(phase.get('seconds'), 'phase seconds')
        if not isinstance(phase.get('prompt'), str) or not phase['prompt'].strip():
            raise CampaignError('empty phase prompt')
        if phase.get('prompt_sha256') != digest(phase['prompt'].encode()):
            raise CampaignError('phase prompt digest mismatch')
    if len(set(names)) != len(names) or manifest['max_sessions'] < len(phases):
        raise CampaignError('duplicate phases or insufficient session cap')


def command(argv: list[str], *, timeout=60) -> str:
    result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise CampaignError(f'{argv[0]} failed: {result.stderr[-1500:]}')
    return result.stdout


def snapshot(workspace: Path, destination: Path, max_bytes: int) -> dict:
    """Caller must quiesce writers; archive all workspace files, including ignored.

    Symlinks are archived as links, never followed. Git history is retained in a
    separate bundle; dirty/index changes remain in the source tar and diff.
    """
    destination.mkdir(mode=0o700)
    size = 0
    files = []
    for current, directories, names in os.walk(workspace, followlinks=False):
        directory = Path(current)
        if directory == workspace and '.git' in directories:
            directories.remove('.git')
        for name in list(directories):
            path = directory / name
            if path.is_symlink():
                directories.remove(name)
            files.append(path)
        for name in names:
            path = directory / name
            if directory == workspace and name == '.git':
                continue
            mode = path.lstat().st_mode
            if not (stat.S_ISREG(mode) or stat.S_ISLNK(mode)):
                raise CampaignError(f'unsupported snapshot node: {path.relative_to(workspace)}')
            size += path.lstat().st_size
            if size > max_bytes:
                raise CampaignError('snapshot byte cap exceeded; artifact is incomplete')
            files.append(path)
    archive = destination / 'workspace.tar'
    with tarfile.open(archive, 'w', dereference=False) as output:
        for path in sorted(files):
            output.add(path, arcname=str(path.relative_to(workspace)), recursive=False)
    git = ['git', '-C', str(workspace)]
    head = command(git + ['rev-parse', 'HEAD']).strip()
    (destination / 'changes.patch').write_text(command(git + [
        'diff', '--no-ext-diff', '--no-textconv', '--binary', 'HEAD']))
    (destination / 'index.patch').write_text(command(git + [
        'diff', '--cached', '--no-ext-diff', '--no-textconv', '--binary']))
    (destination / 'status.z').write_bytes(subprocess.check_output(git + ['status', '--porcelain=v1', '-z', '--untracked-files=all']))
    command(git + ['bundle', 'create', str(destination / 'history.bundle'), '--all'])
    hashes = {}
    for path in destination.iterdir():
        path.chmod(0o600)
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(chunk)
        hashes[path.name] = h.hexdigest()
    result = {'head': head, 'workspace_bytes': size, 'files': len(files), 'sha256': hashes}
    save(destination / 'snapshot.json', result)
    return result


class Docker:
    def __init__(self, container: str, workspace: Path, expected_id: str | None = None):
        info = json.loads(command(['docker', 'inspect', container]))[0]
        labels = info['Config'].get('Labels') or {}
        mounts = [m for m in info['Mounts'] if m['Destination'] == '/workspace']
        if labels.get('dev.agentctl.benchmark') != 'true' or len(mounts) != 1:
            raise CampaignError('container must be a dedicated benchmark container')
        if Path(mounts[0]['Source']).resolve() != workspace or mounts[0]['Type'] != 'bind':
            raise CampaignError('container workspace does not match candidate')
        self.identity = info['Id']
        self.image = info['Image']
        if expected_id and self.identity != expected_id:
            raise CampaignError('container identity changed')

    def info(self):
        return json.loads(command(['docker', 'inspect', self.identity]))[0]

    def start(self):
        info = self.info()
        if info['State']['Running'] or info['State'].get('Paused'):
            raise CampaignError('stage must start with its dedicated container stopped')
        command(['docker', 'start', self.identity])

    def stop(self):
        if self.info()['State'].get('Paused'):
            command(['docker', 'unpause', self.identity])
        command(['docker', 'stop', '--time', '5', self.identity], timeout=30)
        if self.info()['State']['Running']:
            raise CampaignError('container did not stop')

    def checkpoint(self, workspace, destination, cap):
        running = self.info()['State']['Running']
        if running:
            command(['docker', 'pause', self.identity])
        try:
            return snapshot(workspace, destination, cap)
        finally:
            if running:
                command(['docker', 'unpause', self.identity])

    def argv(self, manifest, seconds):
        return ['docker', 'exec', '-i', '-e', f"DEVCONTAINER_CODEX_CLI_VERSION={manifest['cli_version']}",
                '-w', '/workspace', self.identity,
                'timeout', '--signal=TERM', '--kill-after=5s', f'{seconds}s',
                'codex', 'exec', '--json', '--ephemeral', '--ignore-user-config',
                '-m', manifest['model'], '-c', f"model_reasoning_effort={json.dumps(manifest['effort'])}",
                '-c', 'approval_policy="never"', '-c', 'agents.enabled=false',
                '-c', 'features.multi_agent=false', '--sandbox', 'workspace-write', '-']


def initialize(manifest: dict, workspace: Path, output: Path, transport) -> dict:
    validate(manifest)
    workspace, output = workspace.resolve(), output.resolve()
    if output == workspace or workspace in output.parents or output in workspace.parents:
        raise CampaignError('evidence and candidate paths must be disjoint')
    if command(['git', '-C', str(workspace), 'status', '--porcelain']).strip():
        raise CampaignError('initial checkout must be clean')
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    manifest_bytes = json.dumps(manifest, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    state = {'schema_version': 1, 'manifest': manifest, 'manifest_sha256': digest(manifest_bytes),
             'workspace': str(workspace), 'container_id': transport.identity, 'image': transport.image,
             'next_phase': 0, 'sessions': [], 'checkpoints': [], 'status': 'ready',
             'total_seconds': 0.0, 'output_tokens': 0, 'usage_complete': True,
             'task_accepted': None, 'requested_model': manifest['model'],
             'applied_model': None, 'applied_effort': None}
    state['initial_snapshot'] = transport.checkpoint(workspace, output / 'initial', manifest['max_snapshot_bytes'])
    save(output / 'state.json', state)
    return state


def observe(argv, prompt: bytes, destination: Path, seconds: float, output_cap: int, checkpoint, stop):
    """Stream bounded records; a final usage event is required for admission later."""
    started = time.monotonic()
    observation = {'wall_seconds': 0.0, 'exit_code': None, 'stop_reason': None,
                   'commands_completed': 0, 'commands_nonzero': 0, 'parse_errors': 0,
                   'event_counts': {}, 'usage': [], 'prompt_sha256': digest(prompt),
                   'private_events_truncated': False}
    prompt_path = destination / 'prompt.private.txt'
    prompt_path.write_bytes(prompt)
    prompt_path.chmod(0o600)
    process = None
    selector = selectors.DefaultSelector()
    buffers = {}
    stderr_tail = b''
    try:
        with prompt_path.open('rb') as source:
            process = subprocess.Popen(argv, stdin=source, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, start_new_session=True)
        for stream in (process.stdout, process.stderr):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ)
            buffers[stream] = b''
        with (destination / 'events.private.jsonl').open('w') as events:
            os.chmod(events.name, 0o600)
            event_bytes = 0

            def consume(line):
                nonlocal event_bytes
                try:
                    event = json.loads(line)
                    if not isinstance(event, dict):
                        raise ValueError('not an event')
                except (ValueError, UnicodeError):
                    observation['parse_errors'] += 1
                    return
                kind = event.get('type', 'unknown')
                counts = observation['event_counts']
                counts[kind] = counts.get(kind, 0) + 1
                item = event.get('item') or {}
                retained = None
                if kind == 'turn.completed':
                    usage = event.get('usage', {})
                    if all(type(usage.get(k)) is int and usage[k] >= 0 for k in ('input_tokens', 'output_tokens')):
                        observation['usage'].append(usage)
                    retained = {'type': kind, 'usage': usage}
                elif kind == 'item.completed' and item.get('type') == 'command_execution':
                    observation['commands_completed'] += 1
                    observation['commands_nonzero'] += item.get('exit_code') not in (0, None)
                    retained = {'type': kind, 'item': {k: item.get(k) for k in ('type', 'command', 'exit_code', 'status')}}
                elif kind == 'item.completed' and item.get('type') == 'agent_message':
                    retained = {'type': kind, 'item': {'type': 'agent_message', 'text': item.get('text', '')}}
                elif kind in ('turn.failed', 'error'):
                    retained = event
                if retained is not None:
                    encoded = json.dumps(retained, ensure_ascii=False) + '\n'
                    if event_bytes + len(encoded.encode()) <= 64 * 1024 * 1024:
                        events.write(encoded)
                        events.flush()
                        event_bytes += len(encoded.encode())
                    else:
                        observation['private_events_truncated'] = True

            last_save = -1.0
            while selector.get_map():
                elapsed = time.monotonic() - started
                output_used = sum(u['output_tokens'] for u in observation['usage'])
                if elapsed >= seconds or output_used >= output_cap:
                    observation['stop_reason'] = 'wall_cap' if elapsed >= seconds else 'observed_output_cap'
                    stop()
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGTERM)
                    # Drain only for a bounded period after the container stopped.
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                    break
                checkpoint(elapsed)
                if elapsed - last_save >= 1:
                    observation['wall_seconds'] = round(elapsed, 3)
                    save(destination / 'progress.json', observation)
                    last_save = elapsed
                for key, _ in selector.select(timeout=min(0.2, max(0.001, seconds - elapsed))):
                    stream = key.fileobj
                    chunk = os.read(stream.fileno(), 65536)
                    if not chunk:
                        if stream is process.stdout and buffers[stream]:
                            consume(buffers[stream])
                        selector.unregister(stream)
                        continue
                    if stream is process.stderr:
                        stderr_tail = (stderr_tail + chunk)[-65536:]
                        continue
                    buffers[stream] += chunk
                    while b'\n' in buffers[stream]:
                        line, buffers[stream] = buffers[stream].split(b'\n', 1)
                        consume(line)
                    if len(buffers[stream]) > 8 * 1024 * 1024:
                        raise CampaignError('event line exceeds recorder byte cap')
            try:
                observation['exit_code'] = process.wait(timeout=max(0.001, seconds - (time.monotonic() - started)))
            except subprocess.TimeoutExpired:
                observation['stop_reason'] = 'wall_cap'
                stop()
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                observation['exit_code'] = process.wait(timeout=5)
    finally:
        selector.close()
        stop()
        if process is not None:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=10)
            process.stdout.close()
            process.stderr.close()
        observation['wall_seconds'] = round(time.monotonic() - started, 3)
        (destination / 'stderr.private.txt').write_bytes(stderr_tail)
        (destination / 'stderr.private.txt').chmod(0o600)
        save(destination / 'observation.json', observation)
    return observation


def run_stage(output: Path, transport) -> dict:
    state = read(output / 'state.json')
    manifest = state['manifest']
    validate(manifest)
    if digest(json.dumps(manifest, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()) != state['manifest_sha256']:
        raise CampaignError('stored manifest changed after initialization')
    if state['status'] != 'ready':
        raise CampaignError(f"campaign is {state['status']}; do not launch a duplicate session")
    if not state['usage_complete']:
        raise CampaignError('previous usage is unknown; another session is not admitted')
    phase_index = state['next_phase']
    if phase_index >= len(manifest['phases']):
        raise CampaignError('all phases already submitted; evaluate externally')
    remaining = manifest['max_seconds'] - state['total_seconds']
    token_remaining = manifest['max_output_tokens'] - state['output_tokens']
    if remaining <= 0 or token_remaining <= 0 or len(state['sessions']) >= manifest['max_sessions']:
        raise CampaignError('campaign admission cap reached')
    phase = manifest['phases'][phase_index]
    seconds = min(phase['seconds'], remaining)
    session = output / f"session-{len(state['sessions']):02d}"
    session.mkdir(mode=0o700)
    released = '\n\n'.join(f"Phase {p['id']}:\n{p['prompt']}" for p in manifest['phases'][:phase_index + 1])
    prompt = (released + '\n\nImplement the current phase in the existing checkout. Earlier requirements remain in force. '
              'This is a fresh session; inspect the existing source and DEVELOPMENT_HANDOFF.md if present. '
              'Keep a concise factual handoff there (decisions, completed behavior, checks, remaining issues). '
              'Keep persistent development artifacts in the workspace; disposable test targets outside it are not checkpoint state. '
              'Do not use other agents, contact people, publish externally, or change provider/model settings. '
              'Package retrieval needed by the existing declared builds is allowed; do not use unrelated services. '
              'Do not push. Leave edits and local commits for the outer integrator.').encode()
    state['status'] = 'running'
    state['active'] = {'session': session.name, 'phase': phase['id'], 'reserved_seconds': seconds,
                       'started_unix': time.time(), 'recorder_pid': os.getpid()}
    save(output / 'state.json', state)
    next_checkpoint = manifest['checkpoint_seconds']
    workspace = Path(state['workspace'])

    def checkpoint(elapsed):
        nonlocal next_checkpoint
        cumulative = state['total_seconds'] + elapsed
        boundary = math.floor(state['total_seconds'] / manifest['checkpoint_seconds']) * manifest['checkpoint_seconds'] + next_checkpoint
        if cumulative < boundary:
            return
        name = f"checkpoint-{len(state['checkpoints']):03d}"
        artifact = transport.checkpoint(workspace, output / name, manifest['max_snapshot_bytes'])
        state['checkpoints'].append({'directory': name, 'phase': phase['id'], 'requested_seconds': boundary,
                                     'observed_seconds': cumulative, 'artifact': artifact})
        next_checkpoint += manifest['checkpoint_seconds']
        save(output / 'state.json', state)

    try:
        transport.start()
        observation = observe(transport.argv(manifest, seconds), prompt, session, seconds,
                              token_remaining, checkpoint, transport.stop)
        artifact = transport.checkpoint(workspace, session / 'terminal', manifest['max_snapshot_bytes'])
        state['sessions'].append({'directory': session.name, 'phase': phase['id'], 'observation': observation,
                                  'artifact': artifact, 'task_accepted': None})
        state['total_seconds'] += observation['wall_seconds']
        state['output_tokens'] += sum(u['output_tokens'] for u in observation['usage'])
        state['usage_complete'] = bool(observation['usage']) and not observation['parse_errors']
        if observation['exit_code'] == 0 and observation['stop_reason'] is None:
            state['next_phase'] += 1
        state['status'] = 'submitted' if state['next_phase'] == len(manifest['phases']) else 'ready'
        state.pop('active')
        save(output / 'state.json', state)
        return state
    except BaseException:
        # No automatic retry. The remote timeout survives recorder loss; recovery
        # first verifies the exact container has stopped, then preserves artifacts.
        state['status'] = 'interrupted'
        save(output / 'state.json', state)
        raise


def recover(output: Path, transport) -> dict:
    state = read(output / 'state.json')
    if state['status'] not in ('running', 'interrupted') or transport.info()['State']['Running']:
        raise CampaignError('recovery requires an interrupted stage and verified stopped container')
    active = state['active']
    artifact = snapshot(Path(state['workspace']), output / active['session'] / 'recovered',
                        state['manifest']['max_snapshot_bytes'])
    state['total_seconds'] += active['reserved_seconds']
    state['usage_complete'] = False
    state['status'] = 'needs_review'
    state['recovery'] = {'artifact': artifact, 'charged_seconds': active['reserved_seconds'],
                         'reason': 'conservative reservation; recorder lost, usage unknown'}
    save(output / 'state.json', state)
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('init', 'run', 'status', 'recover'))
    parser.add_argument('--state', required=True, type=Path)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--workspace', type=Path)
    parser.add_argument('--container')
    args = parser.parse_args()
    os.umask(0o077)
    output = args.state.resolve()
    if args.action == 'init':
        if not all((args.manifest, args.workspace, args.container)):
            parser.error('init requires --manifest, --workspace and --container')
        workspace = args.workspace.resolve()
        result = initialize(read(args.manifest), workspace, output, Docker(args.container, workspace))
    elif args.action == 'status':
        state = read(output / 'state.json')
        info = Docker(state['container_id'], Path(state['workspace']), state['container_id']).info()
        # A state file or elapsed timeout alone never proves process termination.
        result = {k: state[k] for k in ('status', 'next_phase', 'total_seconds', 'output_tokens', 'usage_complete')}
        result['container_state'] = info['State']
        if state.get('active'):
            progress = output / state['active']['session'] / 'progress.json'
            result['active_progress'] = read(progress) if progress.exists() else None
    else:
        with (output / 'campaign.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            state = read(output / 'state.json')
            transport = Docker(state['container_id'], Path(state['workspace']), state['container_id'])
            if args.action == 'run':
                result = run_stage(output, transport)
            else:
                result = recover(output, transport)
    print(json.dumps({k: v for k, v in result.items() if k != 'manifest'}, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (CampaignError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'campaign: {error}', file=__import__('sys').stderr)
        raise SystemExit(2)

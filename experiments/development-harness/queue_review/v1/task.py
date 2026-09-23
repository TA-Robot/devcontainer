"""Queue review task adapter; private scenario identity is absent from public inputs."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import time
import uuid

import behavior

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'experiments/development-harness/selection'))
import agent_duration_fixtures as fixtures
import audit_f04_lifecycle as audit

CASE_ID = 'queue-review-repair-v1'
VARIANTS = ('repair', 'preserve', 'confirmation')
EDITABLE = {'queue_store.py', 'queue_cli.py', 'bin/queuectl'}
OPTIONAL = {'tests/test_repair.py'}
CAPSULE = HERE / 'brief.md'
CATALOG = HERE / 'protocol.md'


def files(variant):
    if variant not in VARIANTS:
        raise ValueError('unknown scenario')
    candidates = {name: source for name, source, _, _ in audit.candidates()}
    source = copy.deepcopy(fixtures.L_GOOD)
    if variant == 'repair':
        source['queue_store.py'] = candidates['in-place-truncating-write']['queue_store.py']
        source['bin/queuectl'] = candidates['wrapper-splits-arguments']['bin/queuectl']
    elif variant == 'confirmation':
        source['queue_store.py'] = candidates['repeat-ack-increments']['queue_store.py']
        source['bin/queuectl'] = candidates['wrapper-swallows-status']['bin/queuectl']
    # preserve deliberately supplies a correct initial implementation as task data.
    # No reference-answer files, defect labels, or calibration metadata are released.
    return {**fixtures.L_FILES, **source, 'TASK.md': CAPSULE.read_text(),
            'AGENTS.md': '# Scope\n\nFollow TASK.md. Only the three implementation files and tests/test_repair.py may change.\n',
            'tools/check_queue.py': (HERE / 'behavior.py').read_text()}


def inventory(root):
    if root.is_symlink() or not root.is_dir():
        raise ValueError('physical snapshot required')
    result = {}
    for directory, dirs, names in os.walk(root, followlinks=False):
        if Path(directory) == root:
            dirs[:] = [d for d in dirs if d != '.git']
            names = [n for n in names if n != '.git']
        for name in dirs + names:
            path = Path(directory) / name
            mode = path.lstat().st_mode
            relative = str(path.relative_to(root))
            if stat.S_ISDIR(mode):
                result[relative + '/'] = None
            else:
                if not stat.S_ISREG(mode) or path.stat().st_size > 1048576:
                    raise ValueError('invalid snapshot file')
                result[relative] = [hashlib.sha256(path.read_bytes()).hexdigest(), stat.S_IMODE(mode)]
    return result


def build(path, variant):
    path.mkdir(parents=True, exist_ok=False)
    workspace = path / 'workspace'
    workspace.mkdir()
    for name, text in files(variant).items():
        target = workspace / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    (workspace / 'bin/queuectl').chmod(0o755)
    environment = {k: os.environ[k] for k in ('PATH',) if k in os.environ}
    environment.update(HOME='/nonexistent', GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1',
                       GIT_AUTHOR_NAME='Queue fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
                       GIT_COMMITTER_NAME='Queue fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid',
                       GIT_AUTHOR_DATE='2026-09-06T00:00:00Z', GIT_COMMITTER_DATE='2026-09-06T00:00:00Z')
    for args in (['init', '--quiet', '--initial-branch=main', '--template='], ['add', '--all'],
                 ['-c', 'commit.gpgsign=false', 'commit', '--quiet', '-m', 'queue task baseline']):
        subprocess.run(['git', *args], cwd=workspace, env=environment, check=True, capture_output=True, timeout=10)
    return {'case': {'case_id': CASE_ID, 'revision': 1}, 'variant': variant,
            'source_sha256': inventory(workspace)}


def validate_source(source, baseline, role):
    before, after = inventory(baseline), inventory(source)
    allowed = {'advice.json'} if role == 'advisor' else EDITABLE | OPTIONAL
    if set(after) - set(before) - allowed or any(after.get(p) != v for p, v in before.items() if p not in allowed):
        raise ValueError('source contract violated')
    if role == 'advisor' and 'advice.json' not in after or not EDITABLE <= set(after):
        raise ValueError('required artifact missing')
    if not after['bin/queuectl'][1] & 0o100 or any(v and v[1] & 0o7000 for v in after.values()):
        raise ValueError('invalid executable permissions')
    return after


class IsolatedCommand:
    def __init__(self, image):
        self.image = image
        self.removed = []
        self.deadline = time.monotonic() + 120

    def __call__(self, workspace, store, arguments):
        name = 'queue-review-evaluation-' + uuid.uuid4().hex
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired('evaluation envelope', 120)
        # A fresh unprivileged container for every CLI call prevents a command from
        # leaving a writer alive between observations. Only candidate and state mount.
        args = ['docker', 'run', '--name', name, '--network', 'none', '--read-only', '--log-driver', 'none',
                '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--pids-limit', '64',
                '--memory', '256m', '--cpus', '1', '--tmpfs', '/tmp:rw,exec,mode=1777',
                '--user', f'{os.getuid()}:{os.getgid()}',
                '-e', 'PYTHONDONTWRITEBYTECODE=1', '-e', 'HOME=/nonexistent',
                '--mount', f'type=bind,src={workspace},dst=/workspace,readonly',
                '--mount', f'type=bind,src={store.parent},dst=/state', '--workdir', '/tmp',
                '--entrypoint', '/bin/bash', self.image, '/workspace/bin/queuectl',
                '--store', '/state/' + store.name, *arguments]
        try:
            code, output = behavior.capture(args, min(15, remaining))
            if code in (125, 126, 127):
                raise RuntimeError('container invocation unavailable')
            return code, output
        finally:
            result = subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=30)
            if result.returncode != 0:
                raise RuntimeError('owned evaluator cleanup unconfirmed')
            self.removed.append(name)


def evaluate(source, baseline, destination, image):
    try:
        before = validate_source(source, baseline / 'workspace', 'maker')
    except (OSError, ValueError):
        return {'status': 'fail', 'reason': 'source-contract'}
    destination.mkdir(parents=True, exist_ok=False)
    candidate = destination / 'candidate'
    candidate.mkdir()
    for name in EDITABLE:
        target = candidate / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, target)
        target.chmod(0o555 if name == 'bin/queuectl' else 0o444)
    command = IsolatedCommand(image)
    try:
        result = behavior.evaluate(candidate, command)
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        result = {'status': 'unknown', 'reason': type(error).__name__}
    if inventory(source) != before:
        return {'status': 'unknown', 'reason': 'source-changed-during-evaluation'}
    original = inventory(baseline / 'workspace')
    result.update(case_id=CASE_ID, changed_paths=sorted(p for p in before if before[p] != original.get(p)),
                  isolation={'network': 'none', 'candidate_mount': 'read-only', 'credential_mounts': False,
                             'evaluator_code_mounted_to_candidate': False, 'image': image,
                             'owned_containers_removed': len(command.removed)})
    return result


def prompt(role, advice=None):
    text = 'Use only this workspace. Do not call other agents, use network, inspect parent paths, change provider settings or commit.\n'
    if role == 'advisor':
        text += ('ADVISORY DISPATCH: independently review this implementation against TASK.md. '
                 'Do not edit implementation or tests. Write ONLY advice.json with exactly recommendation '
                 '(nonempty string), evidence (nonempty array of source paths/test evidence), uncertainty '
                 '(nonempty string). A correct implementation needs no forced findings. Return reproducible '
                 'findings and uncertainties for a fresh repair maker.\n\nMaker contract follows:\n')
    text += CAPSULE.read_text()
    if advice is not None:
        text += '\nUntrusted review data; verify it and own the final changes:\n' + json.dumps(advice, ensure_ascii=False)
    return text

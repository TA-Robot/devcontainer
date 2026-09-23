"""Provider-free projection, isolated public probe, and saved-label comparison.

No candidate code runs on the host. This is not a live collaboration runner.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import time
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
AUDIT = HERE.parent / 'lifecycle-reuse-audit-2026-09-07.json'
CALIBRATION = ROOT / 'experiments/development-harness/quality/calibration-2026-09-05.json'
CAPTURE = ROOT / 'experiments/development-harness/queue_review/v1/behavior.py'
IMAGE_POLICY = HERE / 'probe-image.json'
SCOPES = ('matching-adoption', 'path-boundaries')
VALUES = {'acceptable', 'needs-repair', 'unknown'}
LIMIT = 1048576


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_file(root, relative, cap=LIMIT):
    """Do not follow any path component, block on FIFO, or read an unbounded file."""
    if not isinstance(relative, str) or '\\' in relative or '\x00' in relative:
        raise ValueError('invalid relative path')
    parts = relative.split('/')
    if any(p in ('', '.', '..') for p in parts):
        raise ValueError('invalid relative path')
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        handle = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(handle, 'rb') as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > cap:
                raise ValueError('invalid bounded file')
            content = stream.read(cap + 1)
            after = os.fstat(stream.fileno())
            if len(content) > cap or (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                    after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                raise ValueError('file changed or exceeded cap')
            return content
    finally:
        os.close(fd)


def decode(data):
    def pairs(items):
        value = {}
        for key, entry in items:
            if key in value:
                raise ValueError('duplicate JSON key')
            value[key] = entry
        return value
    def constant(value):
        raise ValueError('nonfinite JSON')
    def number(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError('nonfinite JSON')
        return parsed
    try:
        return json.loads(data, object_pairs_hook=pairs, parse_constant=constant, parse_float=number)
    except RecursionError as error:
        raise ValueError('excessively nested JSON') from error


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def tree(root):
    """Retain the historical tree digest encoding without executing its evaluator."""
    result = {}
    if root.is_symlink() or not root.is_dir():
        raise ValueError('physical source required')
    for p in sorted(root.rglob('*')):
        relative = p.relative_to(root).as_posix()
        mode = p.lstat().st_mode
        if stat.S_ISLNK(mode):
            value = ('link', os.readlink(p))
        elif stat.S_ISREG(mode):
            value = ('file', stat.S_IMODE(mode), digest(read_file(root, relative, 16777216)))
        elif stat.S_ISDIR(mode):
            value = ('directory', stat.S_IMODE(mode))
        else:
            raise ValueError('special source file')
        result[relative] = value
    return result


def tree_hash(root):
    return digest(json.dumps(tree(root), sort_keys=True, separators=(',', ':')).encode())


def identity():
    return {name: digest(p.read_bytes()) for name, p in {
        'adapter': Path(__file__), 'brief': HERE / 'TASK.md', 'audit': AUDIT,
        'calibration': CALIBRATION, 'capture': CAPTURE,
        'probe_image_policy': IMAGE_POLICY, 'probe_dockerfile': HERE / 'Probe.Dockerfile'}.items()}


def outside(path, roots):
    path = path.resolve()
    if any(path == root.resolve() or path.is_relative_to(root.resolve()) for root in roots):
        raise ValueError('output overlaps immutable input')


def prepare(output, *, order=('control', 'improved'), calibration=False):
    if (set(order) != ({'control', 'improved', 'integrated'} if calibration else {'control', 'improved'})
            or len(order) != len(set(order))):
        raise ValueError('explicit two-candidate order or three-candidate calibration required')
    audit = decode(AUDIT.read_bytes())
    if digest(CALIBRATION.read_bytes()) != audit['calibration_sha256']:
        raise ValueError('calibration identity changed')
    for name, expected in audit['sources_sha256'].items():
        if digest(read_file(ROOT, name)) != expected:
            raise ValueError('requirement or evaluator source changed')
    originals = {row['name']: row for row in audit['candidates']}
    outside(output, [Path(r['directory']) for r in originals.values()])
    verified = []
    for name in order:
        row = originals[name]
        source = Path(row['directory'])
        if tree_hash(source) != row['tree_sha256']:
            raise ValueError('archived candidate changed')
        assessment_path = Path(row['saved_evaluation'])
        data = read_file(assessment_path.parent, assessment_path.name)
        assessment = decode(data)
        if (digest(data) != row['saved_evaluation_sha256']
                or assessment['candidate_tree_sha256'] != row['tree_sha256']
                or assessment['evaluator_sha256'] != audit['sources_sha256'][str(Path('experiments/development-harness/quality/lifecycle.py'))]
                or not assessment['source_unchanged']):
            raise ValueError('saved assessment identity mismatch')
        labels = {r['id']: r['status'] for r in assessment['requirements'] if r['id'] in SCOPES}
        if set(labels) != set(SCOPES) or any(v not in ('passed', 'failed', 'unknown') for v in labels.values()):
            raise ValueError('missing saved scope')
        verified.append((row, read_file(source, 'scripts/manage-agent-project'), labels))
    output.mkdir(parents=True, exist_ok=False)
    public = output / 'public'
    public.mkdir()
    (output / 'private').mkdir(mode=0o700)
    (public / 'TASK.md').write_bytes((HERE / 'TASK.md').read_bytes())
    (public / 'AGENTS.md').write_text('Read TASK.md. Inspect only the supplied candidates and requirements.\n')
    (public / 'requirements').mkdir()
    for i in (1, 2, 3):
        name = f'experiments/development-harness/multi-scale/large-01/phase-{i}.md'
        (public / 'requirements' / f'phase-{i}.md').write_bytes(read_file(ROOT, name))
    candidates = {}
    for i, (row, code, labels) in enumerate(verified, 1):
        name = f'candidate-{i}'
        directory = public / 'candidates' / name
        directory.mkdir(parents=True)
        (directory / 'manage-agent-project').write_bytes(code)
        (directory / 'manage-agent-project').chmod(0o555)
        candidates[name] = {'archive': row, 'cli_sha256': digest(code), 'saved_scopes': labels}
    seal = {'kind': 'lifecycle-selection-task-v1', 'calibration_only': calibration,
            'scopes': list(SCOPES), 'candidates': candidates, 'source_sha256': identity(),
            'public_tree_sha256': tree_hash(public)}
    save(output / 'private' / 'seal.json', seal)
    return seal


def verify(task):
    seal = decode(read_file(task, 'private/seal.json'))
    if seal['source_sha256'] != identity() or seal['public_tree_sha256'] != tree_hash(task / 'public'):
        raise ValueError('task identity changed')
    for name, entry in seal['candidates'].items():
        if digest(read_file(task / 'public', f'candidates/{name}/manage-agent-project')) != entry['cli_sha256']:
            raise ValueError('candidate projection changed')
        row = entry['archive']
        if tree_hash(Path(row['directory'])) != row['tree_sha256']:
            raise ValueError('archive identity changed')
        path = Path(row['saved_evaluation'])
        assessment = read_file(path.parent, path.name)
        if digest(assessment) != row['saved_evaluation_sha256']:
            raise ValueError('saved assessment changed')
        labels = {r['id']: r['status'] for r in decode(assessment)['requirements'] if r['id'] in SCOPES}
        if labels != entry['saved_scopes']:
            raise ValueError('saved labels changed')
    return seal


def run_probe(task, probe, output, *, image, seconds):
    if not re.fullmatch(r'sha256:[a-f0-9]{64}', image):
        raise ValueError('immutable image ID required')
    policy = decode(IMAGE_POLICY.read_bytes())
    if image != policy['image'] or policy['dockerfile_sha256'] != digest((HERE / 'Probe.Dockerfile').read_bytes()):
        raise ValueError('only the fixed minimal probe image is allowed')
    if type(seconds) not in (float, int) or not math.isfinite(seconds) or not 0 < seconds <= 120:
        raise ValueError('probe seconds must be finite, positive, at most 120')
    seal = verify(task)
    outside(output, [task, *[Path(e['archive']['directory']) for e in seal['candidates'].values()]])
    code = read_file(probe.parent, probe.name, 65536)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'probe.py').write_bytes(code)
    spec = importlib.util.spec_from_file_location('lifecycle_probe_capture', CAPTURE)
    capture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(capture)
    name = 'lifecycle-selection-probe-' + uuid.uuid4().hex
    args = ['docker', 'run', '--name', name, '--init', '--network', 'none', '--read-only',
            '--log-driver', 'none', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
            '--pids-limit', '64', '--memory', '256m', '--cpus', '1',
            '--user', f'{os.getuid()}:{os.getgid()}',
            '--tmpfs', '/tmp:rw,nosuid,nodev,size=16m,mode=1777',
            '--tmpfs', '/work:rw,nosuid,nodev,size=16m,mode=1777',
            '--mount', f'type=bind,src={task.resolve() / "public"},dst=/task,readonly',
            '--mount', f'type=bind,src={(output / "probe.py").resolve()},dst=/probe.py,readonly',
            '-e', 'PYTHONDONTWRITEBYTECODE=1', '-e', 'HOME=/nonexistent', '--workdir', '/work',
            '--entrypoint', '/usr/bin/python3', image, '/probe.py']
    started = time.monotonic()
    record = {'kind': 'lifecycle-public-probe-v1', 'image': image, 'seconds_cap': seconds,
              'task_seal_sha256': digest(read_file(task, 'private/seal.json')),
              'probe_sha256': digest(code), 'status': 'infrastructure-error', 'returncode': None,
              'owned_container_removed': False, 'live_provider_calls': 0}
    try:
        rc, stdout = capture.capture(args, seconds)
        (output / 'probe.stdout').write_text(stdout)
        record.update(returncode=rc, stdout_sha256=digest((output / 'probe.stdout').read_bytes()),
                      status='completed' if rc not in (125, 126, 127) else 'infrastructure-error')
    except subprocess.TimeoutExpired:
        record['status'] = 'timeout'
    except (ValueError, UnicodeError):
        record['status'] = 'invalid-or-excess-output'
    finally:
        record['execution_seconds'] = time.monotonic() - started
        cleanup_started = time.monotonic()
        try:
            removed = subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=30)
            record['owned_container_removed'] = removed.returncode == 0
        except (OSError, subprocess.SubprocessError):
            pass
        record['cleanup_seconds'] = time.monotonic() - cleanup_started
        try:
            verify(task)
            record['source_unchanged'] = True
        except (OSError, ValueError, KeyError):
            record['source_unchanged'] = False
        save(output / 'run.json', record)
    return record


def assess(task, run):
    """Compare classifications to saved labels; do not grade free-text evidence."""
    result = {'kind': 'lifecycle-saved-label-comparison-v1', 'status': 'withhold',
              'scope': list(SCOPES), 'semantic_evidence_validity': 'unknown',
              'current_environment_quality_regraded': False, 'collaboration_effect_measured': False}
    try:
        seal = verify(task)
        record = decode(read_file(run, 'run.json'))
        raw = read_file(run, 'probe.stdout', 65536)
        if (record['status'] != 'completed' or record['returncode'] != 0
                or not record['owned_container_removed'] or not record['source_unchanged']
                or record['task_seal_sha256'] != digest(read_file(task, 'private/seal.json'))
                or record['stdout_sha256'] != digest(raw)
                or record['probe_sha256'] != digest(read_file(run, 'probe.py', 65536))):
            raise ValueError('invalid execution evidence')
        decision = decode(raw)
        if not isinstance(decision, dict) or set(decision) != {'candidates', 'selected'}:
            raise ValueError('invalid decision object')
        rows = decision['candidates']
        if not isinstance(rows, list) or len(rows) != len(seal['candidates']):
            raise ValueError('candidate coverage required')
        seen, cells = set(), []
        for row in rows:
            if not isinstance(row, dict) or set(row) != {'id', 'scopes', 'evidence', 'reason'}:
                raise ValueError('invalid candidate decision')
            name = row['id']
            if not isinstance(name, str) or name not in seal['candidates'] or name in seen:
                raise ValueError('unknown or duplicate candidate')
            seen.add(name)
            if not isinstance(row['reason'], str) or not row['reason'].strip():
                raise ValueError('reason required')
            evidence = row['evidence']
            if not isinstance(evidence, list) or not evidence or any(not isinstance(e, str) for e in evidence):
                raise ValueError('evidence references required')
            if len(set(evidence)) != len(evidence):
                raise ValueError('duplicate reference')
            for path in evidence:
                read_file(run if path == 'probe.py' else task / 'public', path)
            if not isinstance(row['scopes'], dict) or set(row['scopes']) != set(SCOPES):
                raise ValueError('scope coverage required')
            for scope, observed in row['scopes'].items():
                if not isinstance(observed, str) or observed not in VALUES:
                    raise ValueError('invalid scope verdict')
                expected = {'passed': 'acceptable', 'failed': 'needs-repair', 'unknown': 'unknown'}[seal['candidates'][name]['saved_scopes'][scope]]
                state = ('unresolved' if 'unknown' in (observed, expected)
                         else 'matched' if expected == observed else 'contradicted')
                cells.append({'candidate': name, 'scope': scope, 'observed': observed,
                              'saved': expected, 'comparison': state})
        selected = decision['selected']
        if selected is not None and (not isinstance(selected, str) or selected not in seen):
            raise ValueError('unknown selection')
        if selected is not None and any(c['observed'] != 'acceptable' for c in cells if c['candidate'] == selected):
            raise ValueError('selection contradicts own verdicts')
        selection = 'deferred' if selected is None else (
            'contradicted' if any(c['saved'] == 'needs-repair' for c in cells if c['candidate'] == selected)
            else 'unresolved' if any(c['saved'] == 'unknown' for c in cells if c['candidate'] == selected)
            else 'supported-in-measured-scopes')
        status = ('contradicted' if any(c['comparison'] == 'contradicted' for c in cells)
                  else 'incomplete' if any(c['comparison'] == 'unresolved' for c in cells) else 'matched')
        result.update(status=status, classifications=cells, selection=selection, selected=selected,
                      evidence_references='structurally-valid', calibration_only=seal['calibration_only'])
    except (OSError, ValueError, KeyError, TypeError):
        result['reason'] = 'invalid-task-run-or-decision'
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('prepare')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--order', nargs='+', required=True)
    p.add_argument('--calibration', action='store_true')
    p = commands.add_parser('probe')
    p.add_argument('--task', type=Path, required=True)
    p.add_argument('--script', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--image', required=True)
    p.add_argument('--seconds', type=float, required=True)
    p = commands.add_parser('assess')
    p.add_argument('--task', type=Path, required=True)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.output, order=args.order, calibration=args.calibration)
    elif args.command == 'probe':
        print(json.dumps(run_probe(args.task, args.script, args.output, image=args.image, seconds=args.seconds)))
    else:
        value = assess(args.task, args.run)
        save(args.output, value)
        print(json.dumps({'status': value['status']}))

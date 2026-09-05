#!/usr/bin/env python3
"""Seal, run finite condition pairs, evaluate isolated artifacts, and report automatically."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import time
import uuid

HERE = Path(__file__).resolve().parent
HARNESS = HERE.parent
sys.path.insert(0, str(HARNESS / 'continuation'))
import admission
sys.path.insert(0, str(HERE))
import observer
campaign = admission.campaign


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def tree_hash(path):
    inventory = observer.staged.inventory(path)
    return hashlib.sha256(json.dumps(inventory, sort_keys=True).encode()).hexdigest()


def validate(config, states):
    if config.get('schema_version') != 1 or config.get('mode') not in ('prospective', 'retrospective'):
        raise ValueError('unsupported comparison mode/schema')
    if config.get('task') not in ('redaction-v2', 'acceptance-v2'):
        raise ValueError('unsupported task')
    if len(config['conditions']) != 2 or {r['id'] for r in config['conditions']} != {'control', 'improved'}:
        raise ValueError('exactly one control and one improved condition required')
    if not config['image'].startswith('sha256:') or len(config['image']) != 71:
        raise ValueError('evaluation image must be pinned by digest')
    campaign.positive(config['observer_seconds'], 'observer cost cap seconds')
    if type(config['observer_slots']) is not int or not 1 <= config['observer_slots'] <= 2:
        raise ValueError('observer slots must be 1 or 2 (local resource cost cap)')
    if type(config['include_checkpoints']) is not bool:
        raise ValueError('checkpoint selection must be explicit')
    allowed = set(config['intervention_fields'])
    if not allowed <= {'command_network_access', 'temporary_docker_config', 'model', 'effort', 'cli_version'}:
        raise ValueError('intervention cannot change task, source, or budgets')
    manifests = []
    initial_heads = []
    initial_images = []
    for condition, state in zip(config['conditions'], states):
        admission.assess(state)
        if state['manifest']['condition'] != condition['id']:
            raise ValueError('condition identity mismatch')
        if state['status'] in ('running', 'interrupted') or state.get('active'):
            raise ValueError('active/interrupted run cannot be compared or restarted')
        if config['mode'] == 'prospective' and (state['sessions'] or not admission.assess(state)['admitted']):
            raise ValueError('prospective sealing requires admitted, never-started states')
        expected_scale = 'small' if config['task'] == 'redaction-v2' else 'large'
        if state['manifest']['scale'] != expected_scale:
            raise ValueError('task scale mismatch')
        if len(state['manifest']['phases']) != (1 if expected_scale == 'small' else 3):
            raise ValueError('task phase count mismatch')
        manifests.append({k: v for k, v in state['manifest'].items() if k not in allowed | {'condition'}})
        initial_heads.append(state['initial_snapshot']['head'])
        initial_images.append(state['image'])
    if (manifests[0] != manifests[1] or len(set(initial_images)) != 1
            or (config['mode'] == 'prospective' and len(set(initial_heads)) != 1)):
        raise ValueError('conditions differ outside declared intervention')


def seal(config_path, output):
    config = campaign.read(config_path)
    states = [campaign.read(Path(c['state']) / 'state.json') for c in config['conditions']]
    validate(config, states)
    for state in states:
        for protected in (Path(state['workspace']).resolve(), Path(state['manifest'].get('evidence', state['workspace'])).resolve()):
            if output == protected or protected in output.parents:
                raise ValueError('comparison output must be outside developer workspace')
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    sources = [HERE / 'compare.py', HERE / 'observer.py', HARNESS / 'campaign.py',
               HARNESS / 'continuation/admission.py', HARNESS / 'continuation/recovery.py',
               HARNESS / 'cycle-003/evaluate_redaction.py',
               *sorted((HARNESS / 'cycle-003/large-02').glob('*.py'))]
    # Bind the actual initial source bytes/modes, not just the advertised Git HEAD.
    initial_sources = []
    for condition, state in zip(config['conditions'], states):
        source = output / ('initial-' + condition['id'])
        archive = Path(condition['state']) / 'initial/workspace.tar'
        extract(archive, state['initial_snapshot']['sha256']['workspace.tar'], source,
                state['manifest']['max_snapshot_bytes'])
        initial_sources.append(tree_hash(source))
    if len(set(initial_sources)) != 1:
        raise ValueError('initial source content/modes differ')
    record = {'schema_version': 1, 'config': config,
              'sealed_unix': time.time(), 'before_development': config['mode'] == 'prospective',
              'code_sha256': {str(p): sha(p) for p in sources},
              'state_sha256': {c['id']: sha(Path(c['state']) / 'state.json') for c in config['conditions']},
              'manifest_sha256': {c['id']: s['manifest_sha256'] for c, s in zip(config['conditions'], states)},
              'initial_source_hash': initial_sources[0], 'catalog': observer.catalog(config['task']),
              'initial_git_heads': {c['id']: s['initial_snapshot']['head'] for c, s in zip(config['conditions'], states)},
              'legacy_hash': tree_hash(Path(config['legacy'])) if config.get('legacy') else None}
    campaign.save(output / 'seal.json', record)
    return record


def verify(record, check_states=False):
    for path, digest in record['code_sha256'].items():
        if sha(Path(path)) != digest:
            raise ValueError('sealed observer/runner changed: ' + path)
    config = record['config']
    if record['legacy_hash'] and tree_hash(Path(config['legacy'])) != record['legacy_hash']:
        raise ValueError('legacy fixture source changed')
    for row in config['conditions']:
        state = campaign.read(Path(row['state']) / 'state.json')
        if state['manifest_sha256'] != record['manifest_sha256'][row['id']]:
            raise ValueError('run manifest identity changed')
        admission.assess(state)
        if check_states and sha(Path(row['state']) / 'state.json') != record['state_sha256'][row['id']]:
            raise ValueError('source run state changed since sealing')


def stopped_state(state):
    identity = state['container_id']
    if not re.fullmatch(r'[0-9a-f]{64}', identity):
        raise ValueError('full container identity required')
    result = subprocess.run(['docker', 'inspect', identity], capture_output=True, text=True, timeout=30)
    if result.returncode:
        if 'no such object' in result.stderr.lower() or 'no such container' in result.stderr.lower():
            return {'container_id': identity, 'stopped': True, 'removed': True}
        raise ValueError('container state unavailable; cannot assume stopped')
    info = json.loads(result.stdout)[0]
    if info['Id'] != identity or info['Image'] != state['image']:
        raise ValueError('container identity/image differs from recorded run')
    if info['State']['Running'] or info['State'].get('Paused'):
        raise ValueError('developer container is still active')
    return {'container_id': identity, 'stopped': True, 'removed': False,
            'finished_at': info['State'].get('FinishedAt')}


def extract(archive, expected, target, cap):
    if sha(archive) != expected:
        raise ValueError('snapshot archive hash mismatch')
    target.mkdir(mode=0o700)
    with tarfile.open(archive) as stream:
        members = stream.getmembers()
        if sum(m.size for m in members) > cap:
            raise ValueError('snapshot exceeds frozen source byte cap')
        if not hasattr(tarfile, 'data_filter'):
            raise ValueError('host Python needs tarfile.data_filter for safe artifact extraction')
        def safe(member, destination):
            if member.mode & 0o7000:
                raise ValueError('unsupported special source mode')
            checked = tarfile.data_filter(member, destination)
            if checked and (member.isfile() or member.isdir()):
                checked = checked.replace(mode=member.mode & 0o777)
            return checked
        stream.extractall(target, filter=safe)
    # Evaluated Python must be compiled from source; archive bytes remain intact.
    for path in sorted(target.rglob('__pycache__'), reverse=True):
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
    for path in target.rglob('*.pyc'):
        if path.is_file() and not path.is_symlink():
            path.unlink()


def execute_all(record, output):
    if not record['before_development']:
        raise ValueError('retrospective comparison cannot start developers')
    verify(record, check_states=True)
    if (output / 'execution-started.json').exists():
        raise ValueError('comparison already started; no automatic replay')
    campaign.save(output / 'execution-started.json', {'unix': time.time()})
    for row in record['config']['conditions']:
        path = Path(row['state'])
        state = campaign.read(path / 'state.json')
        for _ in range(state['manifest']['max_sessions']):
            before = campaign.read(path / 'state.json')
            decision = admission.run(path, lambda current: campaign.Docker(
                current['container_id'], Path(current['workspace']), current['container_id']))
            print(json.dumps({'condition': row['id'], 'admission': decision}), flush=True)
            after = campaign.read(path / 'state.json')
            if not decision['stage_started'] or after['next_phase'] <= before['next_phase'] or not decision['admitted']:
                break


def grade(value, expected):
    if not isinstance(value, dict) or value.get('source_unchanged') is not True:
        return {'accepted': None, 'measurement': 'unknown', 'reason': 'source identity unavailable', 'checks': []}
    checks = value.get('checks', [])
    names = [x.get('name') for x in checks]
    if len(names) != len(set(names)) or set(names) != {c['name'] for c in expected}:
        return {'accepted': None, 'measurement': 'unknown', 'reason': 'missing/duplicate/unexpected observations', 'checks': checks}
    for row in checks:
        criterion = next(c for c in expected if c['name'] == row['name'])
        if (row.get('phase') != criterion['phase'] or row.get('dimension') != criterion['dimension']
                or row.get('status') not in ('passed', 'failed', 'unknown')):
            return {'accepted': None, 'measurement': 'unknown', 'reason': 'observation contract mismatch', 'checks': checks}
    complete = all(x['status'] != 'unknown' for x in checks)
    return {'accepted': all(x['status'] == 'passed' for x in checks) if complete else None,
            'source_unchanged': True,
            'measurement': 'complete' if complete else 'unknown', 'checks': checks}


def evaluate_one(record, output, row):
    config = record['config']
    expected = [c for c in record['catalog'] if c['phase'] <= row['phase']]
    folder = output / 'observations' / row['key']
    folder.mkdir(parents=True, mode=0o700)
    name = 'automatic-eval-' + uuid.uuid4().hex
    arguments = ['docker', 'create', '--name', name, '--network', 'none', '--read-only',
                 '--tmpfs', '/tmp:rw,exec,mode=1777', '-e', 'PYTHONDONTWRITEBYTECODE=1',
                 '--mount', f'type=bind,src={HARNESS},dst=/oracle,readonly',
                 '--mount', f'type=bind,src={row["source"]},dst=/candidate,readonly',
                 '--mount', f'type=bind,src={folder},dst=/results']
    if config.get('legacy'):
        arguments += ['--mount', f'type=bind,src={config["legacy"]},dst=/legacy,readonly']
    if row['phase'] == 3 and row.get('previous'):
        arguments += ['--mount', f'type=bind,src={row["previous"]},dst=/previous,readonly']
    arguments += [config['image'], 'python3', '/oracle/automatic/observer.py', '--task', config['task'],
                  '--candidate', '/candidate', '--phase', str(row['phase']), '--output', '/results/result.json']
    if config.get('legacy'):
        arguments += ['--legacy', '/legacy']
    if row['phase'] == 3 and row.get('previous'):
        arguments += ['--previous', '/previous']
    started = time.monotonic()
    try:
        # Never trust archived bytecode. Compile the runtime modules without
        # executing them, using the exact observer Python in an owned export.
        # Repeated real CLI calls then reuse these source-derived caches.
        compile_args = ['docker', 'run', '--rm', '--name', name + '-compile', '--network', 'none',
                        '--mount', f'type=bind,src={row["source"]},dst=/candidate',
                        config['image'], 'python3', '-c',
                        'import pathlib,py_compile\n'
                        'p=pathlib.Path("/candidate/scripts")\n'
                        'for f in [*p.glob("agentctl*.py"),p/"agent_contracts.py"]:\n'
                        ' if f.is_file():\n'
                        '  try: py_compile.compile(str(f),doraise=True,invalidation_mode=py_compile.PycInvalidationMode.CHECKED_HASH)\n'
                        '  except py_compile.PyCompileError: pass\n']
        with (folder / 'compile.log').open('w') as log:
            subprocess.run(compile_args, stdout=log, stderr=subprocess.STDOUT, check=True,
                           timeout=config['observer_seconds'])
        subprocess.run(arguments, capture_output=True, check=True, timeout=30)
        context = json.loads(subprocess.check_output(['docker', 'inspect', name], text=True, timeout=30))[0]
        campaign.save(folder / 'context.json', {'image': context['Image'], 'mounts': context['Mounts'],
                      'network': context['HostConfig']['NetworkMode'], 'read_only': context['HostConfig']['ReadonlyRootfs']})
        with (folder / 'observer.log').open('w') as log:
            result = subprocess.run(['docker', 'start', '-a', name], stdout=log, stderr=subprocess.STDOUT,
                                    timeout=max(.01, config['observer_seconds'] - (time.monotonic() - started)))
        value = campaign.read(folder / 'result.json') if (folder / 'result.json').exists() and result.returncode == 0 else None
        quality = grade(value, expected)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        quality = {'accepted': None, 'measurement': 'unknown', 'reason': type(error).__name__, 'checks': []}
    finally:
        subprocess.run(['docker', 'rm', '-f', name, name + '-compile'], capture_output=True, timeout=30)
    response = {**row, 'quality': quality, 'observer_seconds': round(time.monotonic() - started, 3)}
    campaign.save(folder / 'observation.json', response)
    print(json.dumps({'artifact': row['key'], 'accepted': quality['accepted'], 'measurement': quality['measurement']}), flush=True)
    return response


def summarize(config, states, rows, catalog):
    result = {'schema_version': 1, 'task': config['task'], 'scale': states[0]['manifest']['scale'],
              'mode': config['mode'], 'quality_scope': 'fixed executable requirements; release acceptance not inferred',
              'human_grading': False, 'conditions': {}, 'common_time_quality': [], 'speed_ratio': None}
    for condition, state in zip(config['conditions'], states):
        selected = [r for r in rows if r['condition'] == condition['id']]
        terminals = [r for r in selected if r['kind'] == 'terminal']
        terminal = max(terminals, key=lambda r: r['seconds']) if terminals else None
        budget = admission.assess(state)
        accepted = (terminal['quality']['accepted'] if terminal and
                    terminal['phase'] == len(state['manifest']['phases']) else None)
        result['conditions'][condition['id']] = {
            'submitted_within_observed_budget': budget['submitted_within_observed_budget'],
            'final_quality_accepted': accepted, 'development_seconds': state['total_seconds'],
            'output_tokens': state['output_tokens'], 'usage_complete': budget['usage_complete'],
            'usage_by_session': [session['observation']['usage'] for session in state['sessions']],
            'requested_model': state['manifest']['model'], 'requested_effort': state['manifest']['effort'],
            'cli_version': state['manifest']['cli_version'], 'applied_model': state.get('applied_model'),
            'applied_effort': state.get('applied_effort'), 'monetary_cost': None,
            'quality_and_budget_passed': accepted is True and budget['submitted_within_observed_budget'],
            'terminal': terminal, 'observations': selected}
    a, b = result['conditions']['control'], result['conditions']['improved']
    if a['quality_and_budget_passed'] and b['quality_and_budget_passed'] and b['development_seconds'] > 0:
        result['speed_ratio'] = a['development_seconds'] / b['development_seconds']
    for requested in sorted({r['requested_seconds'] for r in rows if r['kind'] == 'checkpoint'}):
        chosen = {}
        for condition in result['conditions']:
            points = [r for r in rows if r['condition'] == condition]
            exact = [r for r in points if r['kind'] == 'checkpoint' and r['requested_seconds'] == requested]
            if exact:
                chosen[condition] = exact[0]
            else:
                terminals = [r for r in points if r['kind'] == 'terminal' and r['seconds'] <= requested]
                # Carry only a final, stopped artifact, never an earlier stage
                # whose source was still being modified without a checkpoint.
                if terminals and requested >= result['conditions'][condition]['development_seconds']:
                    chosen[condition] = max(terminals, key=lambda r: r['seconds'])
        if len(chosen) != 2:
            result['common_time_quality'].append({'requested_seconds': requested, 'measurement': 'unknown'})
            continue
        phase = min(r['phase'] for r in chosen.values())
        entry = {'requested_seconds': requested, 'common_phase': phase, 'conditions': {}}
        for condition, row in chosen.items():
            checks = [c for c in row['quality']['checks'] if c['phase'] <= phase]
            projected = grade({'source_unchanged': row['quality'].get('source_unchanged') is True, 'checks': checks},
                              [c for c in catalog if c['phase'] <= phase])
            entry['conditions'][condition] = {'actual_seconds': row['seconds'], 'carried_final': row['kind'] == 'terminal',
                                            'quality': projected}
        result['common_time_quality'].append(entry)
    return result


def evaluate(record, output):
    verify(record, check_states=not record['before_development'])
    config = record['config']
    states = [campaign.read(Path(c['state']) / 'state.json') for c in config['conditions']]
    if any(s.get('active') or s['status'] in ('running', 'interrupted') for s in states):
        raise ValueError('evaluation cannot overlap live developers')
    stops = [stopped_state(state) for state in states]
    campaign.save(output / 'developer-stop-evidence.json', {'conditions': stops})
    (output / 'artifacts').mkdir()
    rows = []
    for condition, state in zip(config['conditions'], states):
        previous = None
        seconds = 0
        points = []
        phases = {p['id']: i + 1 for i, p in enumerate(state['manifest']['phases'])}
        for session in state['sessions']:
            seconds += session['observation']['wall_seconds']
            points.append((session['directory'] + '/terminal', phases[session['phase']], seconds, 'terminal', None))
        if config['include_checkpoints']:
            points += [(c['directory'], phases[c['phase']], c['observed_seconds'], 'checkpoint', c['requested_seconds'])
                       for c in state['checkpoints']]
        for directory, phase, seconds, kind, requested in points:
            key = condition['id'] + '-' + directory.replace('/', '-')
            snapshot = Path(condition['state']) / directory
            metadata = campaign.read(snapshot / 'snapshot.json')
            source = output / 'artifacts' / key
            extract(snapshot / 'workspace.tar', metadata['sha256']['workspace.tar'], source,
                    state['manifest']['max_snapshot_bytes'])
            row = {'condition': condition['id'], 'key': key, 'source': str(source), 'phase': phase,
                   'seconds': seconds, 'kind': kind, 'requested_seconds': requested,
                   'archive_sha256': metadata['sha256']['workspace.tar'],
                   'previous': str(previous) if previous else None}
            rows.append(row)
            if kind == 'terminal' and phase == 2:
                previous = source
    with ThreadPoolExecutor(max_workers=config['observer_slots']) as pool:
        observations = list(pool.map(lambda row: evaluate_one(record, output, row), rows))
    verify(record, check_states=not record['before_development'])
    for state in states:
        stopped_state(state)
    result = summarize(config, states, observations, record['catalog'])
    result['seal_sha256'] = sha(output / 'seal.json')
    result['source_normalization'] = 'discard archived Python bytecode; compile runtime modules with pinned observer Python in owned exports; original archives preserved'
    campaign.save(output / 'comparison.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('seal', 'run', 'evaluate'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    output = args.output.resolve()
    if args.action == 'seal':
        if args.config is None:
            parser.error('seal requires config')
        seal(args.config.resolve(), output)
    else:
        with (output / 'comparison.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            record = campaign.read(output / 'seal.json')
            if args.action == 'run':
                execute_all(record, output)
            result = evaluate(record, output)
            print(json.dumps({k: v for k, v in result.items() if k != 'conditions' and k != 'common_time_quality'}, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, campaign.CampaignError, subprocess.SubprocessError) as error:
        print('automatic comparison: ' + str(error), file=sys.stderr)
        raise SystemExit(2)

#!/usr/bin/env python3
"""Version-two serial comparison: terminal capture, fixed grading, finite failure reports."""
import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import runner
legacy = runner.legacy
campaign = runner.campaign


def disjoint(left, right):
    return left != right and left not in right.parents and right not in left.parents


def seal(config_path, output):
    with ExitStack() as locks:
        config = campaign.read(config_path)
        for path in sorted({Path(c['state']).resolve() for c in config.get('conditions', [])}):
            locks.enter_context(runner.locked(path))
        return _seal(config, output)


def _seal(config, output):
    started = time.monotonic()
    if config.get('schema_version') != 2 or config.get('clock') != runner.CLOCK:
        raise ValueError('terminal pair requires schema 2 and terminal-v2')
    if config.get('task') not in ('duplicates-v1', 'redaction-v2', 'acceptance-v2'):
        raise ValueError('unsupported fixed evaluator')
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', config.get('image', '')):
        raise ValueError('pinned evaluator image required')
    campaign.positive(config.get('observer_seconds'), 'observer_seconds')
    if type(config.get('observer_slots')) is not int or config['observer_slots'] != 1:
        raise ValueError('P0 uses serial external evaluation')
    conditions = config.get('conditions', [])
    if len(conditions) != 2 or {c['id'] for c in conditions} != {'control', 'improved'}:
        raise ValueError('one control and one improved condition required')
    allowed = set(config.get('intervention_fields', []))
    if not allowed <= {'command_network_access', 'temporary_docker_config', 'model', 'effort', 'cli_version'}:
        raise ValueError('intervention cannot alter task or budgets')
    states = [runner.load(Path(c['state'])) for c in conditions]
    locations = [output.resolve()]
    manifests, heads, images = [], [], []
    for condition, state in zip(conditions, states):
        if state['sessions'] or not runner.assess(state)['admitted']:
            raise ValueError('new admitted states required; old runs cannot be replayed')
        if state['manifest']['condition'] != condition['id']:
            raise ValueError('condition identity mismatch')
        expected = 3 if config['task'] == 'acceptance-v2' else 1
        if len(state['manifest']['phases']) != expected or state['manifest']['scale'] != ('large' if expected == 3 else 'small'):
            raise ValueError('task scale or phase count mismatch')
        locations += [Path(condition['state']).resolve(), Path(state['workspace']).resolve()]
        manifests.append({k: v for k, v in state['manifest'].items() if k not in allowed | {'condition'}})
        heads.append(state['initial_snapshot']['head'])
        images.append(state['image'])
        legacy.stopped_state(state)
    if any(not disjoint(a, b) for i, a in enumerate(locations) for b in locations[i + 1:]):
        raise ValueError('comparison, state and candidate paths must be pairwise disjoint')
    if manifests[0] != manifests[1] or len(set(heads)) != 1 or len(set(images)) != 1:
        raise ValueError('conditions differ outside the declared intervention')
    if config['task'] == 'acceptance-v2' and not config.get('legacy'):
        raise ValueError('fixed migration source required')
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    hashes = []
    for condition, state in zip(conditions, states):
        target = output / ('initial-' + condition['id'])
        legacy.extract(Path(condition['state']) / 'initial/workspace.tar',
                       state['initial_snapshot']['sha256']['workspace.tar'], target,
                       state['manifest']['max_snapshot_bytes'])
        hashes.append(legacy.tree_hash(target))
    if hashes[0] != hashes[1]:
        raise ValueError('initial source bytes/modes differ')
    sources = sorted(runner.HERE.parent.rglob('*.py'))
    record = {'schema_version': 2, 'config': config, 'sealed_unix': time.time(),
              'clock': runner.CLOCK, 'catalog': legacy.observer.catalog(config['task']),
              'code_sha256': {str(p): legacy.sha(p) for p in sources},
              'initial_source_sha256': hashes[0],
              'sealing_seconds': time.monotonic() - started,
              'state_sha256': {c['id']: legacy.sha(Path(c['state']) / 'state.json') for c in conditions},
              'manifest_sha256': {c['id']: s['manifest_sha256'] for c, s in zip(conditions, states)},
              'legacy_hash': legacy.tree_hash(Path(config['legacy'])) if config.get('legacy') else None}
    campaign.save(output / 'seal.json', record)
    return record


def verify(record, initial=False):
    if record.get('schema_version') != 2 or record.get('clock') != runner.CLOCK:
        raise ValueError('old seals cannot use the terminal clock')
    for path, expected in record['code_sha256'].items():
        if legacy.sha(Path(path)) != expected:
            raise ValueError('sealed runner/evaluator changed: ' + path)
    if record['legacy_hash'] and legacy.tree_hash(Path(record['config']['legacy'])) != record['legacy_hash']:
        raise ValueError('legacy source changed')
    for c in record['config']['conditions']:
        state = runner.load(Path(c['state']))
        runner.assess(state)
        if state['manifest_sha256'] != record['manifest_sha256'][c['id']]:
            raise ValueError('manifest identity changed')
        if initial and legacy.sha(Path(c['state']) / 'state.json') != record['state_sha256'][c['id']]:
            raise ValueError('state changed after sealing')


def unknown(reason):
    return {'accepted': None, 'measurement': 'unknown', 'checks': [], 'reason': reason}


def evaluate_condition(record, output, condition, state, evaluate_one):
    """The v1 interrupted finalizer's stop/capture/grade boundaries, for v2 records.

    Do not project these clocks through its legacy reservation-as-duration state.
    Both versions reuse the same archive extractor and fixed evaluator/grade.
    """
    rows = []
    previous = None
    for index, session in enumerate(state['sessions']):
        key = condition['id'] + '-' + session['directory']
        row = {'condition': condition['id'], 'key': key, 'phase': index + 1,
               'kind': session['kind'], 'clock': session['clock'],
               'capture_window_ok': session['capture_window_ok'],
               'source': None, 'archive_sha256': None, 'previous': str(previous) if previous else None}
        if session['artifact'] is None:
            row['quality'] = unknown(session['infrastructure_failure'] or 'artifact_missing')
            rows.append(row)
            continue
        try:
            legacy.stopped_state(state)
            snapshot = Path(condition['state']) / session['directory'] / 'terminal'
            expected = session['artifact']['sha256']['workspace.tar']
            source = output / 'artifacts' / key
            legacy.extract(snapshot / 'workspace.tar', expected, source, state['manifest']['max_snapshot_bytes'])
            legacy.stopped_state(state)
            row.update(source=str(source), archive_sha256=expected)
            result = evaluate_one(record, output, row)
            # Treat malformed evaluator output as unavailable, never a success claim.
            expected_checks = [c for c in record['catalog'] if c['phase'] <= row['phase']]
            quality = result.get('quality') if isinstance(result, dict) else None
            row.update(quality=legacy.grade(quality, expected_checks),
                       observer_seconds=result.get('observer_seconds') if isinstance(result, dict) else None)
            legacy.stopped_state(state)
            verify(record)
            if row['phase'] == 2:
                previous = source
        except (OSError, ValueError, KeyError, TypeError, tarfile.TarError, subprocess.SubprocessError, runner.Error) as error:
            row['quality'] = unknown(type(error).__name__)
        rows.append(row)
        if row['quality']['measurement'] == 'unknown':
            break
    return rows


def summary(record, states, rows, execution):
    result = {'schema_version': 2, 'clock': runner.CLOCK, 'task': record['config']['task'],
              'conditions': {}, 'execution': execution, 'human_grading': False, 'speed_ratio': None,
              'quality_scope': 'fixed executable requirements; release acceptance unmeasured',
              'fixed_budget_quality_scope': 'artifact captured after the declared stop policy; exact budget-instant quality unmeasured'}
    for condition, state in zip(record['config']['conditions'], states):
        selected = [r for r in rows if r['condition'] == condition['id']]
        final = selected[-1] if selected else None
        budget = runner.assess(state)
        all_phases = bool(final and final['phase'] == len(state['manifest']['phases']))
        quality = final['quality']['accepted'] if all_phases else None
        window = bool(final and all(s['capture_window_ok'] is True for s in state['sessions']))
        result['conditions'][condition['id']] = {
            'status': state['status'], 'observations': selected, 'budget': budget,
            'final_quality_accepted': quality,
            'quality_and_budget_passed': quality is True and budget['submitted_within_budget'] and window,
            'same_budget_quality_eligible': window,
            'usage_by_session': [s['observation']['usage'] for s in state['sessions']],
            'requested_model': state['manifest']['model'], 'requested_effort': state['manifest']['effort'],
            'applied_model': None, 'applied_effort': None, 'monetary_cost': None,
            'release_accepted': None}
    a, b = (result['conditions'][key] for key in ('control', 'improved'))
    if (a['quality_and_budget_passed'] and b['quality_and_budget_passed']
            and b['budget']['known_development_seconds'] > 0):
        result['speed_ratio'] = a['budget']['known_development_seconds'] / b['budget']['known_development_seconds']
    return result


def run(record, output, factory=None, evaluate_one=None):
    factory = factory or (lambda state: runner.Docker(state['container_id'], Path(state['workspace']), state['container_id']))
    evaluate_one = evaluate_one or legacy.evaluate_one
    with ExitStack() as locks:
        locks.enter_context(runner.locked(output))
        for path in sorted({Path(c['state']).resolve() for c in record['config']['conditions']}):
            locks.enter_context(runner.locked(path))
        verify(record, initial=True)
        marker = output / 'execution-started.json'
        if marker.exists():
            raise ValueError('no automatic replay of a started comparison')
        campaign.save(marker, {'unix': time.time()})
        started = time.monotonic()
        (output / 'artifacts').mkdir(mode=0o700)
        execution, rows = [], []
        stop_remaining = False
        for condition in record['config']['conditions']:
            directory = Path(condition['state'])
            if stop_remaining:
                execution.append({'condition': condition['id'], 'status': 'not_started', 'reason': 'infrastructure_failure'})
                continue
            state = runner.load(directory)
            failure = None
            try:
                while runner.assess(state)['admitted']:
                    state = runner._run_stage(directory, factory(state))
                    failure = state['sessions'][-1]['infrastructure_failure']
                    if failure:
                        break
                # Any unconfirmed developer blocks all grading and later launches.
                for c in record['config']['conditions']:
                    legacy.stopped_state(runner.load(Path(c['state'])))
                rows += evaluate_condition(record, output, condition, state, evaluate_one)
                if any(r['quality']['measurement'] == 'unknown' for r in rows):
                    failure = failure or 'evaluation_unavailable'
            except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, runner.Error) as error:
                failure = failure or 'stop_or_state_unconfirmed'
            execution.append({'condition': condition['id'], 'status': 'interrupted' if failure else 'finished',
                              'reason': failure})
            stop_remaining = failure is not None
            states = [runner.load(Path(c['state'])) for c in record['config']['conditions']]
            campaign.save(output / 'progress.json', summary(record, states, rows, execution))
        states = [runner.load(Path(c['state'])) for c in record['config']['conditions']]
        result = summary(record, states, rows, execution)
        result['automatic_execution_completed'] = not stop_remaining
        result['comparison_elapsed_seconds'] = time.monotonic() - started
        result['comparison_elapsed_scope'] = 'execution, shutdown, capture and evaluation; excludes prior sealing/image preparation'
        campaign.save(output / 'comparison.json', result)
        return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('seal', 'run'))
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
        result = run(campaign.read(output / 'seal.json'), output)
        print(json.dumps({'completed': result['automatic_execution_completed'], 'speed_ratio': result['speed_ratio']}))

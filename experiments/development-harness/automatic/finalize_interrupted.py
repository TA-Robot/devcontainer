#!/usr/bin/env python3
"""Grade stopped interrupted artifacts without replaying developers or changing original records."""
import argparse
import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare


def projected_state(original):
    """Use the frozen recovery charge; never fabricate a submitted session or usage."""
    state = copy.deepcopy(original)
    compare.admission.assess(state)
    active = state.get('active')
    if state['status'] not in ('running', 'interrupted'):
        if active:
            raise ValueError('active state outside interruption contract')
        return state
    if not isinstance(active, dict) or state.get('recovery'):
        raise ValueError('interruption must identify one unrecovered session')
    phase = state['manifest']['phases'][state['next_phase']]
    reserved = active['reserved_seconds']
    compare.campaign.positive(reserved, 'reserved seconds')
    if (active['phase'] != phase['id'] or not re.fullmatch(r'session-[0-9]+', active['session'])
            or reserved > min(phase['seconds'], state['manifest']['max_seconds'] - state['total_seconds'])):
        raise ValueError('active reservation does not match the released phase')
    state['status'] = 'needs_review'
    state['interrupted_session'] = state.pop('active')
    state['usage_complete'] = False
    state['total_seconds'] += reserved
    state['recovery'] = {'charged_seconds': reserved,
                         'reason': 'conservative reservation; recorder lost, usage unknown'}
    compare.admission.assess(state)
    return state


def finalize(sealed, output):
    record = compare.campaign.read(sealed / 'seal.json')
    compare.verify(record)
    config = record['config']
    originals = [compare.campaign.read(Path(c['state']) / 'state.json') for c in config['conditions']]
    if not any(s['status'] in ('running', 'interrupted') for s in originals):
        raise ValueError('this entrypoint requires an interrupted comparison')
    for s in originals:
        for protected in (Path(s['workspace']).resolve(),):
            if output == protected or protected in output.parents or output in protected.parents:
                raise ValueError('finalization must be disjoint from developer workspaces')
    for protected in [sealed, *[Path(c['state']).resolve() for c in config['conditions']]]:
        if output == protected or protected in output.parents or output in protected.parents:
            raise ValueError('finalization must not overwrite or contain original evidence')
    # No launch/stop/retry here: stopped processes must be established first.
    stops = [compare.stopped_state(s) for s in originals]
    states = [projected_state(s) for s in originals]
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    hashes = {c['id']: compare.sha(Path(c['state']) / 'state.json') for c in config['conditions']}
    provenance = {'schema_version': 1, 'kind': 'interrupted-artifact-finalization',
                  'started_unix': time.time(), 'source_seal_sha256': compare.sha(sealed / 'seal.json'),
                  'finalizer_sha256': compare.sha(Path(__file__)), 'original_state_sha256': hashes,
                  'developer_stop_evidence': stops, 'model_restarts': 0,
                  'grading_contract': 'unchanged sealed catalog, observer, and grade function',
                  'recovered_source_is_submission': False}
    compare.campaign.save(output / 'provenance.json', provenance)
    for c, original, state in zip(config['conditions'], originals, states):
        compare.campaign.save(output / ('original-' + c['id'] + '.json'), original)
        compare.campaign.save(output / ('projected-' + c['id'] + '.json'), state)
    (output / 'artifacts').mkdir()
    rows = []
    for c, original, state in zip(config['conditions'], originals, states):
        phases = {p['id']: i + 1 for i, p in enumerate(state['manifest']['phases'])}
        points = []
        seconds = 0
        for session in state['sessions']:
            seconds += session['observation']['wall_seconds']
            points.append((Path(c['state']) / session['directory'] / 'terminal',
                           session['directory'] + '-terminal', phases[session['phase']], seconds, 'terminal', None))
        if config['include_checkpoints']:
            points += [(Path(c['state']) / p['directory'], p['directory'], phases[p['phase']],
                        p['observed_seconds'], 'checkpoint', p['requested_seconds']) for p in state['checkpoints']]
        if state.get('interrupted_session'):
            recovered = output / ('recovered-' + c['id'])
            compare.campaign.snapshot(Path(state['workspace']), recovered, state['manifest']['max_snapshot_bytes'])
            compare.stopped_state(original)
            points.append((recovered, 'recovered', phases[state['interrupted_session']['phase']], None, 'recovered', None))
        previous = None
        for snapshot, suffix, phase, elapsed, kind, requested in points:
            metadata = compare.campaign.read(snapshot / 'snapshot.json')
            key = c['id'] + '-' + suffix
            source = output / 'artifacts' / key
            compare.extract(snapshot / 'workspace.tar', metadata['sha256']['workspace.tar'], source,
                            state['manifest']['max_snapshot_bytes'])
            row = {'condition': c['id'], 'key': key, 'source': str(source), 'phase': phase,
                   'seconds': elapsed, 'kind': kind, 'requested_seconds': requested,
                   'archive_sha256': metadata['sha256']['workspace.tar'], 'previous': str(previous) if previous else None}
            rows.append(row)
            if kind == 'terminal' and phase == 2:
                previous = source
    with ThreadPoolExecutor(max_workers=config['observer_slots']) as pool:
        observations = list(pool.map(lambda row: compare.evaluate_one(record, output, row), rows))
    compare.verify(record)
    for c, original in zip(config['conditions'], originals):
        compare.stopped_state(original)
        if compare.sha(Path(c['state']) / 'state.json') != hashes[c['id']]:
            raise ValueError('original state changed during finalization')
    result = compare.summarize(config, states, observations, record['catalog'])
    for c, state in zip(config['conditions'], states):
        value = result['conditions'][c['id']]
        value['development_seconds_kind'] = 'conservative_reservation' if state.get('recovery') else 'observed_with_shutdown'
        value['recovered_artifact'] = next((r for r in value['observations'] if r['kind'] == 'recovered'), None)
        value['interruption'] = state.get('interrupted_session')
        if state.get('recovery'):
            value['output_tokens_kind'] = 'completed_sessions_only; interrupted session usage unknown'
    result.update(seal_sha256=compare.sha(sealed / 'seal.json'),
                  finalization=provenance, automatic_execution_completed=False)
    compare.campaign.save(output / 'comparison.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sealed', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    finalize(args.sealed.resolve(), args.output.resolve())

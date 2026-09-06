"""Versioned consultation diagnosis task, separate from historical atlas cases."""
import argparse
import hashlib
import json
from pathlib import Path
import stat
import sys

import observe

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from agent_duration_cases.f03 import L_FILES  # unchanged durable journal implementation

CASE_ID = 'consultation-crash-diagnosis-v1'
VARIANTS = ('effect-first', 'ack-first')
OUTPUTS = {'reproduction.json', 'diagnosis.json'}
CHECKS = ('source-integrity', 'artifact-contract', 'anomaly-reproduced', 'causal-order',
          'crash-boundary', 'observed-state', 'observed-outcome', 'claim-scope', 'repeat-and-transfer')
WORKER = '''import argparse
import json
import os
from pathlib import Path
import sys
from journal import read_offset, write_offset


def checkpoint(operation, selected):
    print(json.dumps({'event': operation}), flush=True)
    if selected == operation:
        sys.stdin.readline()


def main():
    parser = argparse.ArgumentParser()
    for name in ('events', 'journal', 'effects'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--stop-after', choices=('append-effect', 'persist-offset', 'read-offset'))
    args = parser.parse_args()
    events = json.loads(args.events.read_text())
    offset = read_offset(args.journal)
    checkpoint('read-offset', args.stop_after)
    if offset >= len(events):
        return
__OPERATIONS__


if __name__ == '__main__':
    main()
'''
EFFECT = '''    with args.effects.open('a') as stream:
        stream.write(events[offset] + '\\n')
        stream.flush()
        os.fsync(stream.fileno())
    checkpoint('append-effect', args.stop_after)
'''
ACK = '''    write_offset(args.journal, offset + 1)
    checkpoint('persist-offset', args.stop_after)
'''


def files(variant):
    if variant not in VARIANTS:
        raise ValueError('unknown task variant')
    return {'worker.py': WORKER.replace('__OPERATIONS__', EFFECT + ACK if variant == 'effect-first' else ACK + EFFECT),
            'journal.py': L_FILES['journal.py'], 'observe.py': (HERE / 'observe.py').read_text(),
            'TASK.md': (HERE / 'brief.md').read_text(),
            'AGENTS.md': '# Task scope\n\nFollow TASK.md. Only diagnosis.json and reproduction.json are deliverables.\n'}


def create(path, variant):
    path.mkdir(parents=True, exist_ok=False)
    for name, text in files(variant).items():
        (path / name).write_text(text)


def regular_bytes(path, limit):
    # Reject symlinks/FIFOs before opening; caller supplies a stopped private snapshot.
    if not stat.S_ISREG(path.lstat().st_mode) or path.stat().st_size > limit:
        raise ValueError('invalid artifact file')
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError('artifact exceeds cap')
    return data


def inventory(path):
    result = {}
    if path.is_symlink() or not path.is_dir():
        raise ValueError('snapshot must be a physical directory')
    for item in path.iterdir():
        if item.name == '.git':
            continue  # controller metadata; never read or executed by this evaluator
        result[item.name] = hashlib.sha256(regular_bytes(item, 65536)).hexdigest()
    return result


def contract(diagnosis):
    required = {'event_order', 'interruption', 'before_restart', 'after_restart', 'outcome',
                'exactly_once_established', 'explanation'}
    if not isinstance(diagnosis, dict) or set(diagnosis) != required:
        return False
    order = diagnosis['event_order']
    if (not isinstance(order, list) or len(order) != 3
            or any(not isinstance(op, str) for op in order) or set(order) != set(observe.OPERATIONS)):
        return False
    window = diagnosis['interruption']
    if (not isinstance(window, dict) or set(window) != {'after', 'before'}
            or any(op not in observe.OPERATIONS for op in window.values())):
        return False
    for key in ('before_restart', 'after_restart'):
        state = diagnosis[key]
        if (not isinstance(state, dict) or set(state) != {'offset', 'effects'}
                or type(state['offset']) is not int or state['offset'] < 0
                or not isinstance(state['effects'], list)
                or any(not isinstance(e, str) for e in state['effects'])):
            return False
    return (diagnosis['outcome'] in ('duplicate', 'lost', 'once')
            and type(diagnosis['exactly_once_established']) is bool
            and isinstance(diagnosis['explanation'], str) and bool(diagnosis['explanation'].strip()))


def evaluate(candidate, variant):
    import tempfile
    import subprocess
    expected_files = files(variant)
    rows = {key: None for key in CHECKS}

    def result(status, reason=None):
        return {'case_id': CASE_ID, 'variant': variant, 'status': status, 'reason': reason,
                'checks': [{'name': key, 'status': 'unknown' if value is None else 'passed' if value else 'failed'}
                           for key, value in rows.items()]}

    try:
        before = inventory(candidate)
        rows['source-integrity'] = (set(before) <= set(expected_files) | OUTPUTS
            and all(before.get(key) == hashlib.sha256(value.encode()).hexdigest()
                    for key, value in expected_files.items()))
        if not rows['source-integrity']:
            return result('fail', 'source-integrity')
        plan = observe.read_json(candidate / 'reproduction.json')
        diagnosis = observe.read_json(candidate / 'diagnosis.json')
        observe.validate_plan(plan)
        rows['artifact-contract'] = contract(diagnosis)
        if not rows['artifact-contract']:
            return result('fail', 'artifact-contract')
    except (OSError, ValueError, TypeError, RecursionError):
        rows['artifact-contract'] = False
        return result('fail', 'invalid-artifact')

    try:
        # Never import/run candidate source, public tool, or submitted commands.
        with tempfile.TemporaryDirectory(prefix='consultation-oracle-') as raw:
            trusted = Path(raw) / 'workspace'
            create(trusted, variant)
            measurements = [observe.observe(trusted, plan) for _ in range(2)]
            transferred = observe.observe(trusted, plan, events=['previous', 'pending-other'],
                                          offset=1, effects=['previous'])
        value = measurements[0]
        order = ['read-offset'] + (['append-effect', 'persist-offset'] if variant == 'effect-first'
                                  else ['persist-offset', 'append-effect'])
        rows['anomaly-reproduced'] = (value['outcome'] in ('duplicate', 'lost')
                                     and value['uninterrupted'] == {'offset': 1, 'effects': ['event-1']})
        rows['causal-order'] = diagnosis['event_order'] == order
        window = diagnosis['interruption']
        index = order.index(plan['stop_after'])
        rows['crash-boundary'] = (index + 1 < len(order) and window ==
                                  {'after': order[index], 'before': order[index + 1]})
        rows['observed-state'] = all(diagnosis[key] == value[key] for key in ('before_restart', 'after_restart'))
        rows['observed-outcome'] = diagnosis['outcome'] == value['outcome']
        rows['claim-scope'] = diagnosis['exactly_once_established'] is False
        rows['repeat-and-transfer'] = (measurements[0] == measurements[1]
                                      and transferred['outcome'] == value['outcome'])
        rows['source-integrity'] = inventory(candidate) == before
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        return result('unknown', 'observer-failure')
    return result('pass' if all(value is True for value in rows.values()) else 'fail')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('create', 'evaluate'))
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--variant', choices=VARIANTS, required=True)
    args = parser.parse_args()
    if args.action == 'create':
        create(args.workspace, args.variant)
        return 0
    result = evaluate(args.workspace, args.variant)
    print(json.dumps(result, sort_keys=True))
    return 0 if result['status'] == 'pass' else 1 if result['status'] == 'fail' else 2


if __name__ == '__main__':
    raise SystemExit(main())

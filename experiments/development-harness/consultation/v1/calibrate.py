"""Private, provider-free calibration. Never copy this module into developer inputs."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import time
import subprocess
import sys

import case
import observe


def reference(workspace, variant):
    order = ['read-offset'] + (['append-effect', 'persist-offset'] if variant == 'effect-first'
                              else ['persist-offset', 'append-effect'])
    plan = {'stop_after': order[1], 'restart_count': 1}
    observed = observe.observe(workspace, plan)
    diagnosis = {'event_order': order, 'interruption': {'after': order[1], 'before': order[2]},
                 'before_restart': observed['before_restart'], 'after_restart': observed['after_restart'],
                 'outcome': observed['outcome'], 'exactly_once_established': False,
                 'explanation': 'The persisted offset and external effect straddle the interrupted operation.'}
    return plan, diagnosis


def submit(workspace, plan, diagnosis):
    (workspace / 'reproduction.json').write_text(json.dumps(plan))
    (workspace / 'diagnosis.json').write_text(json.dumps(diagnosis, ensure_ascii=False))


def public_tool_baseline(workspace):
    """A non-agent baseline using only the published vocabulary and observation CLI.

    No variant, reference source, hidden oracle or expected state is an input.
    This deliberately checks whether the bounded task collapses to enumeration.
    """
    observations = []
    for operation in observe.OPERATIONS:
        plan = {'stop_after': operation, 'restart_count': 1}
        (workspace / 'reproduction.json').write_text(json.dumps(plan))
        completed = subprocess.run([sys.executable, '-B', 'observe.py', 'reproduction.json'],
                                   cwd=workspace, capture_output=True, text=True, timeout=15, check=True)
        observations.append((plan, json.loads(completed.stdout)))
    order = max((value['observed_prefix'] for _, value in observations), key=len)
    plan, value = next((plan, value) for plan, value in observations if value['outcome'] != 'once')
    index = order.index(plan['stop_after'])
    diagnosis = {'event_order': order, 'interruption': {'after': order[index], 'before': order[index + 1]},
                 'before_restart': value['before_restart'], 'after_restart': value['after_restart'],
                 'outcome': value['outcome'], 'exactly_once_established': False,
                 'explanation': 'Enumerated the published interruption points and compared observed states.'}
    return plan, diagnosis


def calibrate():
    started = time.monotonic()
    records = []
    for variant in case.VARIANTS:
        with tempfile.TemporaryDirectory(prefix='consultation-calibration-') as raw:
            workspace = Path(raw) / 'workspace'
            case.create(workspace, variant)
            plan, diagnosis = reference(workspace, variant)
            variants = [('known-good', plan, diagnosis, 'pass', None)]
            baseline_plan, baseline_diagnosis = public_tool_baseline(workspace)
            variants.append(('public-tool-only-baseline', baseline_plan, baseline_diagnosis, 'pass', None))
            alternative = {key: value for key, value in reversed(list(diagnosis.items()))}
            alternative['explanation'] = '中断時に残った進捗と副作用を確認し、再起動後の結果と照合した。'
            variants.append(('alternative-expression', plan, alternative, 'pass', None))
            for name, key, value, failed in (
                    ('wrong-cause', 'event_order', list(reversed(diagnosis['event_order'])), 'causal-order'),
                    ('wrong-boundary', 'interruption', {'after': 'read-offset', 'before': 'append-effect'}, 'crash-boundary'),
                    ('fabricated-state', 'before_restart', {'offset': 99, 'effects': []}, 'observed-state'),
                    ('false-success', 'outcome', 'once', 'observed-outcome'),
                    ('overclaim', 'exactly_once_established', True, 'claim-scope')):
                bad = copy.deepcopy(diagnosis)
                bad[key] = value
                variants.append((name, plan, bad, 'fail', failed))
            variants.append(('non-reproducing-plan', {'stop_after': 'read-offset', 'restart_count': 1},
                             diagnosis, 'fail', 'anomaly-reproduced'))
            variants.append(('arbitrary-command', {**plan, 'command': ['sh', '-c', 'exit 0']},
                             diagnosis, 'fail', 'artifact-contract'))
            for name, reproduction, answer, expected, failed in variants:
                submit(workspace, reproduction, answer)
                result = case.evaluate(workspace, variant)
                failures = [row['name'] for row in result['checks'] if row['status'] == 'failed']
                accepted = result['status'] == expected and (failed is None or failed in failures)
                records.append({'variant': variant, 'calibration_id': name, 'expected': expected,
                                'status': 'pass' if accepted else 'fail', 'evaluation': result})
    return {'case_id': case.CASE_ID, 'kind': 'provider-free-calibration',
            'status': 'pass' if all(r['status'] == 'pass' for r in records) else 'fail',
            'duration_seconds': time.monotonic() - started,
            'source_sha256': {name: hashlib.sha256((case.HERE / name).read_bytes()).hexdigest()
                              for name in ('case.py', 'observe.py', 'brief.md', 'calibrate.py')},
            'inherited_journal_sha256': hashlib.sha256(case.L_FILES['journal.py'].encode()).hexdigest(),
            'records': records}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    # Reserve a fresh file before doing work; never overwrite prior evidence.
    with args.output.open('x') as stream:
        result = calibrate()
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'records': len(result['records'])}))
    raise SystemExit(result['status'] != 'pass')

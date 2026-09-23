"""Retain fresh, provider-free projection/probe/assessment evidence."""
import argparse
import hashlib
import json
from pathlib import Path

import adapter


def calibrate(output, image):
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for name, order, reference in (
            ('standard', ('improved', 'control'), False),
            ('reference-calibration', ('control', 'integrated', 'improved'), True)):
        task = output / f'{name}-task'
        adapter.prepare(task, order=order, calibration=reference)
        run = output / f'{name}-run'
        record = adapter.run_probe(task, Path(__file__).with_name('calibration_probe.py'),
                                   run, image=image, seconds=30)
        assessment = adapter.assess(task, run)
        adapter.save(output / f'{name}-assessment.json', assessment)
        expected_selection = 'candidate-2' if reference else None
        rows.append({'name': name, 'execution_status': record['status'],
                     'owned_container_removed': record['owned_container_removed'],
                     'assessment': assessment,
                     'expected_classifications_and_selection': assessment['status'] == 'matched'
                         and assessment.get('selected') == expected_selection,
                     'run_sha256': adapter.digest((run / 'run.json').read_bytes())})
        if not rows[-1]['expected_classifications_and_selection']:
            break
    value = {'kind': 'lifecycle-selection-calibration-v1', 'image': image,
             'status': 'passed' if len(rows) == 2 and all(r['expected_classifications_and_selection'] for r in rows) else 'failed',
             'cases': rows, 'source_sha256': adapter.identity(),
             'calibration_probe_sha256': hashlib.sha256(Path(__file__).with_name('calibration_probe.py').read_bytes()).hexdigest(),
             'live_provider_calls': 0, 'current_environment_quality_regraded': False,
             'semantic_evidence_validity': 'unknown', 'collaboration_effect_measured': False}
    adapter.save(output / 'calibration.json', value)
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--image', required=True)
    args = parser.parse_args()
    result = calibrate(args.output, args.image)
    print(json.dumps({'status': result['status'], 'live_provider_calls': 0}))
    raise SystemExit(0 if result['status'] == 'passed' else 1)

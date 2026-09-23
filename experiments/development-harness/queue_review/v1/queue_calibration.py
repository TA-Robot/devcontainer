"""Private finite calibration and source-matched live admission; no provider calls."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

import behavior
import task
import pilot


def source_identity():
    return {str(Path(name).relative_to(task.ROOT)): digest
            for name, digest in pilot.binding('repair', pilot.IMAGE).identity().items()}


def calibrate(image):
    records = []
    for label, sources, _, expected_failures in task.audit.candidates():
        with tempfile.TemporaryDirectory(prefix='queue-review-calibration-') as raw:
            root = Path(raw)
            task.build(root / 'fixture', 'repair')
            candidate = root / 'candidate'
            import shutil
            shutil.copytree(root / 'fixture/workspace', candidate)
            for name, source in sources.items():
                (candidate / name).write_text(source)
            local = behavior.evaluate(candidate)
            external = task.evaluate(candidate, root / 'fixture', root / 'evaluation', image)
            expected = 'fail' if expected_failures else 'pass'
            mapping = dict(zip(task.audit.PROBES, behavior.CHECKS))
            required = {mapping[name] for name in expected_failures}
            detected = {row['name'] for row in external.get('checks', []) if row['status'] == 'fail'}
            records.append({'candidate': label, 'expected': expected,
                            'required_failures': sorted(required),
                            'status': 'pass' if local['status'] == external['status'] == expected and required <= detected else 'fail',
                            'public': local, 'external': external})
    return {'kind': 'queue-review-calibration-v1', 'status': 'pass' if all(r['status'] == 'pass' for r in records) else 'fail',
            'image': image, 'source_sha256': source_identity(), 'records': records,
            'live_provider_calls': 0, 'historical_scores_overwritten': False,
            'general_collaboration_effect_established': False}


def verify_preflight():
    calibration = json.loads((task.HERE / 'calibration.json').read_text())
    validation = json.loads((task.HERE / 'validation.json').read_text())
    sources = source_identity()
    if (calibration.get('status') != 'pass' or validation.get('status') != 'pass'
            or calibration.get('image') != pilot.IMAGE or validation.get('image') != pilot.IMAGE
            or calibration.get('source_sha256') != sources or validation.get('source_sha256') != sources
            or validation.get('paired_scenarios') != ['repair', 'preserve']
            or validation.get('calibration_sha256') != hashlib.sha256((task.HERE / 'calibration.json').read_bytes()).hexdigest()):
        raise ValueError('source-matched calibration and paired preflight required')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as stream:
        result = calibrate(args.image)
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'candidates': len(result['records'])}))
    raise SystemExit(result['status'] != 'pass')

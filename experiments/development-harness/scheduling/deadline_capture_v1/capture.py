"""Prospective budget-end artifact contract; synthetic-provider calibration only."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RECOVERY = HERE.parent/'native_recovery_v1'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value


def read(path): return json.loads(path.read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path, value):
    with path.open('x') as stream: json.dump(value, stream, indent=2); stream.write('\n')


def identity():
    result = load('capture_identity_native', RECOVERY/'actor.py').identity()
    files = [*HERE.glob('*.py'), HERE/'CONTRACT.md', ROOT/'scripts/test-deadline-capture.py',
             HERE.parent/'continuation_pair_v1/initial-policy.txt']
    result.update({str(p.relative_to(ROOT)): sha(p) for p in files})
    return dict(sorted(result.items()))


def classify(report, requested_seconds, recovery_bound_seconds):
    """Keep the original quality/lifecycle/budget axes, and add capture eligibility."""
    value = {'status': 'withhold', 'original_quality': report['quality']['status'],
             'original_lifecycle': report['lifecycle']['status'], 'original_budget': report['budget'],
             'requested_development_seconds': requested_seconds,
             'recovery_bound_seconds': recovery_bound_seconds,
             'scope': 'artifact after observed termination; not exact-cutoff quality or normal completion',
             'billing_completeness': 'unknown'}
    if (report.get('cleanup', {}).get('status') != 'confirmed' or not report.get('source_unchanged')
            or report.get('artifact', {}).get('status') != 'sealed' or report.get('failure')
            or report.get('collection_failure')):
        value['reason'] = 'artifact, integrity, recovery or execution failure'; return value
    elapsed = report.get('elapsed_seconds'); development = report.get('bridge', {}).get('development_seconds')
    valid_number = lambda x: isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x >= 0
    if (not valid_number(elapsed) or not valid_number(development) or development > elapsed
            or elapsed > requested_seconds+recovery_bound_seconds):
        value['reason'] = 'capture time unknown or beyond prospective recovery bound'; return value
    life = report['lifecycle']; inventory = life.get('inventory', [])
    if (not inventory or any((r.get('model'), r.get('effort'), r.get('cli_version'))
                            != ('gpt-6-astra', 'high', '0.153.0') for r in inventory)):
        value['reason'] = 'model binding not established'; return value
    if report['condition'] == 'solo' and len(inventory) != 1:
        value['reason'] = 'solo participant mismatch'; return value
    deadline = (report.get('bridge', {}).get('status') == 'withhold'
                and report['bridge'].get('reason') == 'TimeoutError: development deadline'
                and development >= requested_seconds)
    allowed = {'unfinished participant', 'incomplete or aborted turn'}
    if report['quality']['status'] == 'eligible' and life['status'] == 'completed':
        basis = 'normal_completion'
    elif (deadline and life['status'] == 'unknown' and life.get('failures')
          and all(r['failure'] in allowed for r in life['failures'])):
        basis = 'deadline_capture'
    else:
        value['reason'] = 'termination or participant contract not established'; return value
    value.update(status='evaluable', basis=basis, artifact_sha256=report['artifact']['sha256'],
                 observed_development_seconds=development, capture_upper_bound_seconds=elapsed,
                 normal_completion=basis == 'normal_completion',
                 original_admission=report['admission'], usage_status=report['usage']['status'])
    return value


def run(output, profile):
    if profile not in ('normal', 'deadline', 'invalid', 'missing', 'child'):
        raise ValueError('finite synthetic profile required')
    output = output.resolve(); output.mkdir(parents=True, mode=0o700, exist_ok=False)
    initial = identity(); condition = 'adaptive' if profile == 'child' else 'solo'
    seconds = 30 if profile == 'normal' else 8
    manifest = {'kind': 'prospective-deadline-capture-calibration-v1', 'execution': 'synthetic',
                'profile': profile, 'condition': condition, 'source_sha256': initial,
                'requested_development_seconds': seconds, 'recovery_bound_seconds': 20,
                'live_provider_calls': 0}
    save(output/'manifest.json', manifest)
    native = load('capture_run_native', RECOVERY/'actor.py')
    native.prepare_public(output/'public')
    shutil.copyfile(HERE.parent/'continuation_pair_v1/initial-policy.txt', output/'public/initial.py')
    save(output/'public-seal.json', {p.name: sha(p) for p in (output/'public').iterdir()})
    fixture = output/'fixture'; fixture.mkdir()
    shutil.copyfile(native.LEGACY/'accounting.py', fixture/'accounting.py')
    for name in ('fake_solo.py', 'fake_adaptive.py'): shutil.copyfile(HERE/'probe.py', fixture/name)
    for p in fixture.iterdir(): p.chmod(0o444)
    native.LEGACY = fixture
    report = native.run(output/'actor', output/'public', condition=condition,
                        prompt='Finite synthetic deadline capture calibration.', fake=True, fake_mode=profile,
                        seconds=seconds, output_tokens=160000)
    capture = classify(report, seconds, 20)
    if identity() != initial:
        capture.update(status='withhold', reason='calibration source changed')
    capture.update(actor_result_sha256=sha(output/'actor/result.json'), manifest_sha256=sha(output/'manifest.json'),
                   public_seal_sha256=sha(output/'public-seal.json'))
    save(output/'capture.json', capture)
    return capture


def assess(output):
    manifest = read(output/'manifest.json'); capture = read(output/'capture.json')
    actor = read(output/'actor/result.json')
    if (manifest['execution'] != 'synthetic' or actor['execution'] != 'synthetic'
            or manifest['source_sha256'] != identity() or capture['status'] != 'evaluable'
            or capture['manifest_sha256'] != sha(output/'manifest.json')
            or capture['public_seal_sha256'] != sha(output/'public-seal.json')
            or read(output/'public-seal.json') != {p.name: sha(p) for p in (output/'public').iterdir()}
            or capture['actor_result_sha256'] != sha(output/'actor/result.json')
            or capture['artifact_sha256'] != sha(output/'actor/submission.py')):
        raise ValueError('synthetic capture seal or eligibility mismatch')
    expected = classify(actor, manifest['requested_development_seconds'], manifest['recovery_bound_seconds'])
    if any(capture.get(k) != v for k, v in expected.items()): raise ValueError('capture contract changed')
    grader = load('capture_independent_grader', HERE/'assessment.py')
    evaluated = grader.evaluate(output/'actor/submission.py', output/'public/probe.json', output/'assessment', seconds=120)
    result = {'kind': 'synthetic-deadline-capture-assessment-v1', 'status': evaluated['status'],
              'capture_sha256': sha(output/'capture.json'), 'scope': capture['scope'],
              'original_quality': actor['quality']['status'], 'original_budget': actor['budget'],
              'evaluation': evaluated, 'live_provider_calls': 0, 'old_runs_reinterpreted': False}
    save(output/'assessment.json', result)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--profile', choices=('normal', 'deadline', 'invalid', 'missing', 'child'), required=True)
    a = p.parse_args(); value = run(a.output, a.profile)
    print(json.dumps(value)); raise SystemExit(0 if value['status'] == 'evaluable' else 1)

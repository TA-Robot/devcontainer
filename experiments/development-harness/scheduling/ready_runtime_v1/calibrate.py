"""Finite public-only calibration, frozen before any fixed policy is run."""
import argparse
import importlib.util
from pathlib import Path
import signal

HERE = Path(__file__).resolve().parent


def load_support(path):
    spec = importlib.util.spec_from_file_location('ready_support', path)
    module = importlib.util.module_from_spec(spec)
    # The public helper receives this module object as its explicit dependency.
    import sys
    sys.modules[spec.name] = module; spec.loader.exec_module(module); return module


def run(output):
    support = load_support(HERE/'support.py'); sources = support.identity()
    output = output.resolve(); output.mkdir(parents=True, mode=0o700, exist_ok=False)
    support.save(output/'plan.json', {'source_sha256': sources, 'max_cases_per_policy': 24,
        'fixed_policies': ['fifo', 'initial'], 'live_provider_calls': 0, 'qualification_scored': False})
    for name, digest in sources.items():
        source = support.ROOT/name
        if support.sha(source) != digest: raise ValueError('source changed during snapshot')
        target = output/'source'/name; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes()); target.chmod(0o444)
    frozen = load_support(output/'source'/HERE.relative_to(support.ROOT)/'support.py')
    assessor = frozen.load('ready_frozen_assessor', frozen.HERE/'assessment.py')
    result = {'status': 'withhold', 'source_sha256': sources, 'assessments': {},
              'public_cases_measured': {}, 'live_provider_calls': 0, 'qualification_scored': False}
    handlers = {}
    def stop(signum, frame): raise RuntimeError('calibration interrupted')
    try:
        for sig in (signal.SIGINT, signal.SIGTERM): handlers[sig] = signal.signal(sig, stop)
        result['public_seal'] = frozen.prepare_public(output/'public')
        for name in ('fifo', 'initial'):
            independent = assessor.evaluate(output/'public'/(name+'.py'), output/'public/development.json', output/('external-'+name))
            result['assessments'][name] = {'external': independent['status']}
            if independent['status'] != 'measured': raise ValueError('external calibration incomplete: '+name)
            public = frozen.public_execution(output/'public', output/('actor-public-'+name), name)
            result['assessments'][name]['public'] = public
            if public['status'] != 'measured' or not public['removed']: raise ValueError('public calibration incomplete: '+name)
            a = {r['id']: r['result'] for r in independent['evaluation']['cases']}
            b = {r['id']: r['result'] for r in frozen.read(output/('actor-public-'+name)/'public-result.json')['cases']}
            if len(a) != 24 or a != b: raise ValueError('public/external result or trace mismatch: '+name)
            result['public_cases_measured'][name] = 24
        if (frozen.identity() != sources or support.identity() != sources
                or {p.name: frozen.sha(p) for p in (output/'public').iterdir()} != result['public_seal']):
            raise ValueError('source/public seal changed')
        result.update(status='passed', public_execution_matches_external=True)
    except (OSError, ValueError, RuntimeError) as exc:
        result['reason'] = type(exc).__name__+': '+str(exc)
    finally:
        support.save(output/'result.json', result)
        for sig, previous in handlers.items(): signal.signal(sig, previous)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(); result = run(args.output)
    print(result['status']); raise SystemExit(0 if result['status'] == 'passed' else 1)

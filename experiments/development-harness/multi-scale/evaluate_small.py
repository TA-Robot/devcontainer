#!/usr/bin/env python3
"""Provider-free acceptance of small-01's actual supervisor configuration path."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile


def hashes(root):
    return {name: hashlib.sha256((root / 'scripts' / name).read_bytes()).hexdigest()
            for name in ('agentctl_supervisor.py', 'agentctl_jobs.py', 'agent_contracts.py')}


def evaluate(root):
    before = hashes(root)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(root / 'scripts'))
    for name in ('agentctl_supervisor', 'agentctl_jobs', 'agent_contracts'):
        sys.modules.pop(name, None)
    jobs = importlib.import_module('agentctl_jobs')
    supervisor = importlib.import_module('agentctl_supervisor')
    if Path(supervisor.__file__).resolve() != (root / 'scripts/agentctl_supervisor.py').resolve():
        raise RuntimeError('candidate module identity mismatch')
    original_environment = dict(os.environ)
    checks = []
    try:
        for name in list(os.environ):
            if name.startswith('AGENTCTL_'):
                del os.environ[name]
        with tempfile.TemporaryDirectory(prefix='orphan-configuration-acceptance-') as raw:
            cases = [(None, 30.0), ('0.1', 0.1), ('0.125', 0.125), ('3.75', 3.75),
                     (' 30 ', 30.0), ('97.5', 97.5), ('65536', 65536.0), ('1e308', 1e308)]
            cases += [(text, None) for text in ('nan', 'NaN', 'inf', '+Infinity', '-inf',
                                               '1e309', '-1e309', '0', '0.099', '-1', '', 'broken', 'true')]
            for text, expected in cases:
                if text is None:
                    os.environ.pop('AGENTCTL_ORPHAN_AFTER_SECONDS', None)
                else:
                    os.environ['AGENTCTL_ORPHAN_AFTER_SECONDS'] = text
                try:
                    instance = supervisor.Supervisor(jobs.StatePaths(Path(raw)), root / 'scripts/agentctl')
                    passed = expected is not None and instance.orphan_after_seconds == expected
                    detail = None if passed else 'invalid threshold accepted or valid threshold changed'
                except jobs.AgentctlJobError as error:
                    passed = expected is None and 'AGENTCTL_ORPHAN_AFTER_SECONDS' in str(error)
                    detail = None if passed else 'valid threshold rejected or error omitted configuration identity'
                except Exception as error:
                    passed, detail = False, type(error).__name__
                checks.append({'input': text, 'passed': passed, 'detail': detail})
            no_state_created = not list(Path(raw).iterdir())
    finally:
        os.environ.clear()
        os.environ.update(original_environment)
    unchanged = before == hashes(root)
    return {'schema_version': 1, 'task': 'small-01', 'candidate_sha256': before,
            'evaluator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'source_unchanged': unchanged, 'no_runtime_state_created': no_state_created,
            'passed': sum(c['passed'] for c in checks), 'total': len(checks),
            'accepted': unchanged and no_state_created and all(c['passed'] for c in checks), 'checks': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = evaluate(args.candidate.resolve())
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'checks'}, indent=2))
    return 0 if result['accepted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Observe each distributed loader inside a delivery image, without runtime mounts."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import duplicates


PATHS = (
    '/usr/local/lib/agentctl/agent_contracts.py',
    '/usr/local/lib/mira-duration-atlas-runtime/scripts/agent_contracts.py',
    '/usr/local/share/agent-project/validation/agent_contracts.py',
)


def observe(expected):
    rows = []
    for number, name in enumerate(PATHS):
        row = {'path': name, 'sha256': None, 'matches_source': False, 'checks': [],
               'status': 'unknown'}
        try:
            path = Path(name)
            row['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            row['matches_source'] = row['sha256'] == expected
            spec = importlib.util.spec_from_file_location('installed_contracts_' + str(number), path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            row['checks'] = duplicates.observe(module)
            row['status'] = ('passed' if row['matches_source'] and
                             all(c['status'] == 'passed' for c in row['checks']) else 'failed')
        except Exception as error:
            row['error'] = type(error).__name__
        rows.append(row)
    return {'schema_version': 1, 'task': 'duplicates-v1', 'expected_sha256': expected,
            'installed_loaders': rows,
            'installed_threshold': all(r['status'] == 'passed' for r in rows),
            'mount_isolation': 'outer caller must record actual mounts; no runtime source allowed'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch('[0-9a-f]{64}', args.expected_sha256):
        parser.error('expected SHA-256 must identify the integrated source bytes')
    result = observe(args.expected_sha256)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    return 0 if result['installed_threshold'] else 2


if __name__ == '__main__':
    raise SystemExit(main())

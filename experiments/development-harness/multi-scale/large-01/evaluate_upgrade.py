#!/usr/bin/env python3
"""Release check: migrate real ownership state created by earlier deliveries.

This supplements the fixed 35-scenario suite. Synthetic current-version state
cannot establish compatibility with earlier stage implementations.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import time

from evaluate import Scenario, require, tree


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def evaluate_upgrade(candidate, old_candidates):
    current_before = tree(candidate)
    checks = []
    for old in old_candidates:
        previous_before = tree(old)
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix='project-lifecycle-upgrade-') as raw:
            try:
                scenario = Scenario(Path(raw), candidate)
                modern_cli = scenario.cli
                scenario.cli = old / 'scripts/manage-agent-project'
                scenario.install()
                scenario.cli = modern_cli
                original = 'first=local\nmiddle=stable\nlast=base\n'
                (scenario.target / 'settings.txt').write_text(original)
                previous_upstream = (scenario.target / 'space 日本.txt').read_bytes()
                (scenario.source / 'space 日本.txt').write_text('safe upstream update\n')
                updated = scenario.apply()
                require((scenario.target / 'settings.txt').read_text() == original,
                        'legacy-state upgrade lost a retained local edit')
                require((scenario.target / 'space 日本.txt').read_text() == 'safe upstream update\n',
                        'legacy-state upgrade did not apply safe upstream change')
                require(scenario.call('status', '--target', scenario.target).get('pending_transaction') is None,
                        'successful upgrade remains pending')
                scenario.call('rollback', '--target', scenario.target, '--transaction', updated['transaction_id'])
                require((scenario.target / 'settings.txt').read_text() == original,
                        'rollback after legacy-state upgrade lost prior customization')
                require((scenario.target / 'space 日本.txt').read_bytes() == previous_upstream,
                        'rollback after legacy-state upgrade did not restore changed file')
                scenario.apply()
                require((scenario.target / 'settings.txt').read_text() == original,
                        'update after rollback lost local customization')
                require((scenario.target / 'space 日本.txt').read_text() == 'safe upstream update\n',
                        'update after rollback failed')
                passed, detail = True, None
            except Exception as error:
                passed, detail = False, f'{type(error).__name__}: {error}'[-1000:]
        checks.append({'previous_candidate_tree_sha256': fingerprint(previous_before),
                       'previous_source_unchanged': previous_before == tree(old),
                       'passed': passed, 'detail': detail, 'wall_seconds': round(time.monotonic() - started, 3)})
    unchanged = current_before == tree(candidate)
    return {'schema_version': 1, 'candidate_tree_sha256': fingerprint(current_before),
            'source_unchanged': unchanged,
            'evaluator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'shared_scenario_sha256': hashlib.sha256(Path(__file__).with_name('evaluate.py').read_bytes()).hexdigest(),
            'upgrade_accepted': bool(checks) and unchanged and all(c['passed'] and c['previous_source_unchanged'] for c in checks),
            'checks': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--old-candidate', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = evaluate_upgrade(args.candidate.resolve(), [p.resolve() for p in args.old_candidate])
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['upgrade_accepted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

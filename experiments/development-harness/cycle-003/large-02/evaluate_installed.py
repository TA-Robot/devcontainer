"""Run inside the actual delivery image; no candidate checkout is mounted."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_staged import evaluate

SELECTED = ['actual-success', 'false-success-and-stop', 'original-task-authority',
            'manual-is-not-command-proof', 'cwd-valid', 'bounded-output-redaction',
            'fresh-read-only-gate', 'report-corruption', 'later-failure-retains-history',
            'real-clean-retry', 'exclusive-checker', 'sigterm-and-recheck', 'abrupt-death-and-recheck']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--expected-runtime', required=True, type=Path)
    args = parser.parse_args()
    expected = json.loads(args.expected_runtime.read_text())
    required = {'agentctl', 'agentctl_jobs.py', 'agentctl_supervisor.py', 'agent_contracts.py'}
    if not isinstance(expected, dict) or not required.issubset(expected) or not all(
            isinstance(k, str) and Path(k).name == k and isinstance(v, str)
            and re.fullmatch('[0-9a-f]{64}', v) for k, v in expected.items()):
        raise ValueError('expected runtime must identify the installed entrypoint and core modules')
    actual = {}
    for name in expected:
        path = Path('/usr/local/bin/agentctl') if name == 'agentctl' else Path('/usr/local/lib/agentctl') / name
        actual[name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    with tempfile.TemporaryDirectory(prefix='installed-checker-alias-') as temporary:
        candidate = Path(temporary)
        (candidate / 'scripts').symlink_to('/usr/local/bin', target_is_directory=True)
        result = evaluate(candidate, Path('/usr/local/share/agent-project/template'), 3, candidate, SELECTED)
    result.update({'installed_runtime_hashes': actual, 'runtime_matches_candidate': actual == expected,
                   'candidate_checkout_mounted': None,
                   'mount_context': 'outer caller must verify mount isolation; execution uses installed paths',
                   'installed_threshold': actual == expected and result['measurement_complete'] and
                   all(c['status'] == 'passed' for c in result['checks'])})
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['measurement_complete'] else 2


if __name__ == '__main__':
    raise SystemExit(main())

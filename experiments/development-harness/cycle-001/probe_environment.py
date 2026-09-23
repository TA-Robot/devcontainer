#!/usr/bin/env python3
"""Run inside the tested image with repository source mounted at /workspace.

No provider, network, credentials, or candidate-reported metrics are used.
The source sentinel is added only to a private temporary copy.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path('/workspace')
ENV = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}


def command(argv, cwd=ROOT):
    start = time.monotonic()
    result = subprocess.run(argv, cwd=cwd, env=ENV, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    return result, round(time.monotonic() - start, 3)


def main():
    checks = []
    result, wall = command([sys.executable, 'scripts/validate-agent-contracts.py'])
    checks.append({'name': 'template-validator', 'passed': result.returncode == 0,
                   'exit_code': result.returncode, 'wall_seconds': wall,
                   'failure_tail': result.stderr[-350:] if result.returncode else None})
    with tempfile.TemporaryDirectory(prefix='harness-source-probe-') as raw:
        target = Path(raw)
        shutil.copy2(ROOT / 'scripts/agentctl', target / 'agentctl')
        (target / 'agentctl_jobs.py').write_text("raise SystemExit('checkout-source-sentinel')\n")
        result, wall = command([sys.executable, str(target / 'agentctl'), '--version'], cwd=target)
        checks.append({'name': 'checkout-source-selection',
                       'passed': result.returncode == 1 and result.stderr.strip() == 'checkout-source-sentinel',
                       'exit_code': result.returncode, 'wall_seconds': wall})
    result, wall = command(['/usr/local/bin/agentctl', '--version'])
    checks.append({'name': 'installed-cli', 'passed': result.returncode == 0,
                   'exit_code': result.returncode, 'wall_seconds': wall})
    for repetition in range(5):
        result, wall = command([sys.executable, '-m', 'unittest',
            'scripts.test-agentctl-supervisor.AgentctlSupervisorTests.test_supervisor_log_rotates_in_place_and_keeps_its_live_descriptor'])
        checks.append({'name': f'retention-{repetition}', 'passed': result.returncode == 0,
                       'exit_code': result.returncode, 'wall_seconds': wall})
    print(json.dumps({'python_version': sys.version.split()[0], 'checks': checks,
                      'passed': sum(c['passed'] for c in checks), 'total': len(checks)}, indent=2))


if __name__ == '__main__':
    main()

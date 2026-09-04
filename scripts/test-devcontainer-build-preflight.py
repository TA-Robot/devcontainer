#!/usr/bin/env python3
"""Verify the real frozen-build entry point stops before unnecessary bootstrap."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parent.parent

FAKE = r'''#!/usr/bin/python3
import json,os,sys,time
from pathlib import Path
name=Path(sys.argv[0]).name
with open(os.environ['PREFLIGHT_TRACE'],'a') as stream:
    stream.write(json.dumps({'name':name,'args':sys.argv[1:]})+'\n')
if name=='docker':
    if os.environ['DOCKER_PROBE_MODE']=='timeout': time.sleep(30)
    if os.environ['DOCKER_PROBE_MODE']=='denied':
        print('fixture: Docker socket permission denied',file=sys.stderr)
        sys.exit(1)
    print('fixture-daemon-version')
    sys.exit(0)
sys.exit(43)
'''


class FrozenBuildPreflightTests(unittest.TestCase):
    def invoke(self, mode):
        with tempfile.TemporaryDirectory(prefix='frozen-build-preflight-') as raw:
            root = Path(raw)
            for name in ('docker', 'devcontainer', 'npx'):
                if mode == 'missing' and name == 'docker':
                    continue
                path = root / name
                path.write_text(FAKE.replace('#!/usr/bin/python3', f'#!{sys.executable}'))
                path.chmod(0o755)
            trace = root / 'trace.jsonl'
            env = {**os.environ, 'PATH': f'{root}:/usr/bin:/bin',
                   'PYTHONNOUSERSITE': '1', 'PYTHONDONTWRITEBYTECODE': '1',
                   'PREFLIGHT_TRACE': str(trace), 'DOCKER_PROBE_MODE': mode}
            env.pop('DEVCONTAINER_CLI_BIN', None)
            if mode == 'missing':
                (root / 'python3').symlink_to(sys.executable)
                (root / 'dirname').symlink_to('/usr/bin/dirname')
                env['PATH'] = str(root)
            start = time.monotonic()
            process = subprocess.run(['/bin/bash', str(ROOT / 'scripts/test-devcontainer-lock.sh'), '--build'],
                                     cwd=ROOT, env=env, capture_output=True, text=True, timeout=20)
            records = [json.loads(line) for line in trace.read_text().splitlines()] if trace.exists() else []
            return process, records, time.monotonic() - start

    def test_missing_docker_never_starts_bootstrap(self):
        process, trace, _ = self.invoke('missing')
        self.assertNotEqual(process.returncode, 0)
        self.assertIn('requires the Docker CLI', process.stderr)
        self.assertEqual(trace, [])

    def test_inaccessible_daemon_never_starts_cli_or_npx(self):
        process, trace, _ = self.invoke('denied')
        self.assertNotEqual(process.returncode, 0)
        self.assertIn('Docker socket permission denied', process.stderr)
        self.assertIn('frozen build was not run', process.stderr)
        self.assertEqual([event['name'] for event in trace], ['docker'])

    def test_healthy_daemon_reaches_unchanged_frozen_cli_command(self):
        process, trace, _ = self.invoke('ready')
        self.assertEqual(process.returncode, 43)
        self.assertEqual([event['name'] for event in trace], ['docker', 'devcontainer'])
        self.assertIn('--frozen-lockfile', trace[1]['args'])
        self.assertEqual(trace[1]['args'][0], 'build')

    def test_unresponsive_daemon_is_bounded_and_not_reported_as_success(self):
        process, trace, elapsed = self.invoke('timeout')
        self.assertNotEqual(process.returncode, 0)
        self.assertIn('exceeded 10 seconds', process.stderr)
        self.assertLess(elapsed, 15)
        self.assertEqual([event['name'] for event in trace], ['docker'])


if __name__ == '__main__':
    unittest.main()

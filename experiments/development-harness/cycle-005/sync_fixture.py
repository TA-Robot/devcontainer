"""Public, provider-free CLI-sync fixtures. Assertions observe files and processes."""
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import tempfile
import time

PACKAGES = {'codex': '@openai/codex', 'claude': '@anthropic-ai/claude-code', 'gemini': '@google/gemini-cli'}
KEYS = {'codex': 'CODEX_CLI_VERSION', 'claude': 'CLAUDE_CODE_VERSION',
        'gemini': 'GEMINI_CLI_VERSION', 'grok': 'GROK_CLI_VERSION'}
INSTALLER = r'''#!/usr/bin/python3
import json,os,sys,time
from pathlib import Path
args=sys.argv[1:]; root=Path(os.environ['FIXTURE_ROOT']); mode=os.environ.get('FIXTURE_MODE','ok')
if Path(sys.argv[0]).name=='npm':
 prefix=Path(args[args.index('--prefix')+1]); specs=[a for a in args if a.startswith('@')]
 with (root/'calls').open('a') as f: f.write('npm\n')
 active=root/'active-install'
 try: active.mkdir()
 except FileExistsError: (root/'overlap').touch()
 for spec in specs:
  package,version=spec.rsplit('@',1); name={'@openai/codex':'codex','@anthropic-ai/claude-code':'claude','@google/gemini-cli':'gemini'}[package]
  directory=prefix/'lib/node_modules'/package;directory.mkdir(parents=True,exist_ok=True)
  (directory/'package.json').write_text(json.dumps({'version':version}))
  binary=prefix/'bin'/name; binary.parent.mkdir(parents=True,exist_ok=True)
  if binary.is_symlink(): binary.unlink()
  binary.write_text('#!/bin/sh\necho '+name+' '+version+'\n');binary.chmod(0o755)
  if mode=='missing-binary': binary.unlink()
  if mode=='npm-fail': raise SystemExit(31)
 if mode=='hold':
  (root/'entered').touch()
  while not (root/'release').exists(): time.sleep(.01)
 try: active.rmdir()
 except FileNotFoundError: pass
else:
 with (root/'calls').open('a') as f: f.write('curl\n')
 if mode=='curl-fail': raise SystemExit(22)
 output=Path(args[args.index('-o')+1]);url=next(a for a in args if a.startswith('https://'))
 version=url.rsplit('/grok-',1)[1].split('-linux-',1)[0]
 if mode=='wrong-version': version='0.0.1'
 output.write_text('#!/bin/sh\necho grok '+version+'\n')
'''


def require(value, message):
    if not value:
        raise AssertionError(message)


def tree(root):
    result = {}
    if not root.is_dir():
        return None
    for current, directories, files in os.walk(root):
        for name in directories + files:
            path = Path(current) / name
            mode = path.lstat().st_mode
            relative = str(path.relative_to(root))
            result[relative] = (('link', os.readlink(path)) if stat.S_ISLNK(mode) else
                ('file', stat.S_IMODE(mode), path.read_bytes().hex()) if stat.S_ISREG(mode) else
                ('directory', stat.S_IMODE(mode)))
    return result


class Fixture:
    def __init__(self, candidate, version='2.3.4'):
        self.temporary = tempfile.TemporaryDirectory(prefix='cli-sync-observer-')
        self.root = Path(self.temporary.name)
        self.prefix = self.root / 'cli prefix'
        self.prefix.mkdir()
        self.candidate = candidate
        self.version = version
        self.manifest = self.root / 'versions.env'
        self.processes = []
        for name in KEYS:
            binary = self.prefix / 'bin' / name
            binary.parent.mkdir(exist_ok=True)
            binary.write_text(f'#!/bin/sh\necho {name} 1.0.0\n')
            binary.chmod(0o755)
            if name in PACKAGES:
                directory = self.prefix / 'lib/node_modules' / PACKAGES[name]
                directory.mkdir(parents=True)
                (directory / 'package.json').write_text('{"version":"1.0.0"}')
        self.untouched = self.prefix / 'user-owned'
        self.untouched.write_text('preserve bytes and permission\n')
        self.untouched.chmod(0o600)
        (self.prefix / 'user-link').symlink_to('user-owned')
        for name in ('npm', 'curl'):
            path = self.root / name
            path.write_text(INSTALLER)
            path.chmod(0o755)
        self.write_manifest()
        self.before = tree(self.prefix)

    def write_manifest(self, names=None, version=None, path=None):
        path = path or self.manifest
        path.write_text(''.join(f'{KEYS[n]}={version or self.version}\n' for n in (names or KEYS)))

    def start(self, mode='ok', **overrides):
        env = {k: v for k, v in os.environ.items() if not k.startswith('DEVCONTAINER_')}
        env.update(DEVCONTAINER_AI_CLI_CHANNEL='edge', DEVCONTAINER_AI_CLI_VERSION_FILE=str(self.manifest),
            DEVCONTAINER_AI_CLI_PREFIX=str(self.prefix), DEVCONTAINER_AI_CLI_NPM_BIN=str(self.root / 'npm'),
            DEVCONTAINER_AI_CLI_CURL_BIN=str(self.root / 'curl'), FIXTURE_ROOT=str(self.root), FIXTURE_MODE=mode)
        env.update(overrides)
        process = subprocess.Popen(['bash', str(self.candidate / 'scripts/sync-host-ai-cli-versions')],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        self.processes.append(process)
        return process

    def run(self, mode='ok', **overrides):
        process = self.start(mode, **overrides)
        return process.wait(timeout=12)

    def versions(self):
        result = {}
        for name in KEYS:
            command = self.prefix / 'bin' / name
            try:
                value = subprocess.run([str(command), '--version'], capture_output=True, text=True, timeout=2)
                result[name] = value.stdout.strip() if value.returncode == 0 else None
            except (OSError, subprocess.TimeoutExpired):
                result[name] = None
        return result

    def expected(self, names=None, version=None):
        names = names or KEYS
        return {n: f'{n} {version or self.version}' if n in names else f'{n} 1.0.0' for n in KEYS}

    def wait_entered(self, process):
        deadline = time.monotonic() + 5
        while not (self.root / 'entered').exists():
            require(process.poll() is None and time.monotonic() < deadline, 'installer barrier not reached')
            time.sleep(.01)

    def close(self):
        for process in self.processes:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=3)
        self.temporary.cleanup()


def exercise(f, case):
    if case in ('normal', 'unspecified', 'no-op'):
        names = ['codex'] if case == 'unspecified' else list(KEYS)
        f.write_manifest(names)
        require(f.run() == 0, 'normal sync failed')
        require(f.versions() == f.expected(names), 'requested executable versions differ')
        require(f.untouched.read_text() == 'preserve bytes and permission\n' and
                stat.S_IMODE(f.untouched.stat().st_mode) == 0o600 and
                os.readlink(f.prefix / 'user-link') == 'user-owned', 'unrelated input or permission changed')
        if case == 'no-op':
            before = tree(f.prefix)
            calls = (f.root / 'calls').read_bytes()
            require(f.run() == 0 and tree(f.prefix) == before and (f.root / 'calls').read_bytes() == calls,
                    'matching versions performed another installation or changed source')
    elif case in ('stable', 'disabled', 'invalid'):
        env = ({'DEVCONTAINER_AI_CLI_CHANNEL': 'stable'} if case == 'stable' else
               {'DEVCONTAINER_AI_CLI_SYNC': '0'} if case == 'disabled' else {})
        if case == 'invalid':
            f.manifest.write_text('CODEX_CLI_VERSION=not-a-version\n')
        code = f.run(**env)
        require((code != 0) if case == 'invalid' else (code == 0), 'policy exit status differs')
        require(tree(f.prefix) == f.before and not (f.root / 'calls').exists(), 'disabled/invalid sync mutated installation')
    elif case in ('npm-fail', 'curl-fail', 'wrong-version', 'missing-binary'):
        require(f.run(case) != 0, 'incomplete update reported success')
        require(tree(f.prefix) == f.before, 'failed update changed the usable installation')
        require(f.run() == 0 and f.versions() == f.expected(), 'retry did not converge')
    elif case in ('term', 'kill'):
        process = f.start('hold')
        f.wait_entered(process)
        os.killpg(process.pid, signal.SIGTERM if case == 'term' else signal.SIGKILL)
        require(process.wait(timeout=3) != 0, 'interrupted update reported success')
        # The old execution group is terminated before a fresh attempt.
        require(tree(f.prefix) == f.before, 'interrupted update changed the usable installation')
        (f.root / 'release').touch()
        # Fixture process marker is external diagnostic state, not updater state.
        if (f.root / 'active-install').exists():
            (f.root / 'active-install').rmdir()
        require(f.run() == 0 and f.versions() == f.expected(), 'fresh retry after stopped execution failed')
    elif case == 'concurrent':
        first = f.start('hold')
        f.wait_entered(first)
        other = f.root / 'other.env'
        f.write_manifest(version='7.8.9', path=other)
        second = f.start(DEVCONTAINER_AI_CLI_VERSION_FILE=str(other))
        # A second writer either fails promptly or waits for the owned update.
        deadline = time.monotonic() + .5
        while second.poll() is None and time.monotonic() < deadline and not (f.root / 'overlap').exists():
            time.sleep(.01)
        (f.root / 'release').touch()
        require(first.wait(timeout=12) == 0, 'first update failed')
        second_code = second.wait(timeout=12)
        require(not (f.root / 'overlap').exists(), 'concurrent installers share one update without ownership')
        expected = f.expected(version='7.8.9') if second_code == 0 else f.expected()
        require(f.versions() == expected, 'concurrent updates published a mixed or unexpected set')
        require(f.run(DEVCONTAINER_AI_CLI_VERSION_FILE=str(other)) == 0 and
                f.versions() == f.expected(version='7.8.9'), 'retry of later manifest did not converge')
    else:
        raise ValueError('unregistered fixture case')


PUBLIC_CASES = ('normal', 'no-op', 'stable', 'disabled', 'invalid', 'unspecified', 'curl-fail', 'term', 'concurrent')


def observe(candidate, cases=PUBLIC_CASES, version='2.3.4'):
    rows = []
    for case in cases:
        started = time.monotonic()
        fixture = Fixture(candidate, version)
        try:
            exercise(fixture, case)
            status, detail = 'passed', None
        except AssertionError as error:
            status, detail = 'failed', str(error)
        except Exception as error:
            status, detail = 'unknown', type(error).__name__
        finally:
            fixture.close()
        rows.append({'name': case, 'phase': 1, 'dimension': 'sync-integrity', 'status': status,
                     'detail': detail, 'elapsed_seconds': time.monotonic() - started})
    return {'checks': rows}


if __name__ == '__main__':
    import sys
    value = observe(Path(sys.argv[1]).resolve())
    print(json.dumps(value))
    raise SystemExit(0 if all(r['status'] == 'passed' for r in value['checks']) else 1)

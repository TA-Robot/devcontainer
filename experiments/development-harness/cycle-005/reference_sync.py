"""Linux-only calibration reference; never shipped or passed to developers."""
import ctypes
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    legacy = Path(__file__).with_name('baseline-sync')
    prefix = Path(os.environ['DEVCONTAINER_AI_CLI_PREFIX'])
    channel = os.environ.get('DEVCONTAINER_AI_CLI_CHANNEL', 'stable')
    switch = os.environ.get('DEVCONTAINER_AI_CLI_SYNC')
    if switch == '1':
        channel = 'edge'
    if switch == '0' or channel != 'edge':
        return subprocess.call(['bash', str(legacy)])
    prefix.parent.mkdir(parents=True, exist_ok=True)
    with (prefix.parent / (prefix.name + '.reference-lock')).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        stage = Path(tempfile.mkdtemp(prefix='.reference-stage-', dir=prefix.parent))
        try:
            shutil.copytree(prefix, stage, dirs_exist_ok=True, symlinks=True)
            env = {**os.environ, 'DEVCONTAINER_AI_CLI_PREFIX': str(stage)}
            result = subprocess.run(['bash', str(legacy)], env=env, pass_fds=(lock.fileno(),))
            if result.returncode:
                return result.returncode
            keys = {'CODEX_CLI_VERSION': 'codex', 'CLAUDE_CODE_VERSION': 'claude',
                    'GEMINI_CLI_VERSION': 'gemini', 'GROK_CLI_VERSION': 'grok'}
            for line in Path(env['DEVCONTAINER_AI_CLI_VERSION_FILE']).read_text().splitlines():
                key, separator, version = line.partition('=')
                if key not in keys or not separator:
                    continue
                name = keys[key]
                result = subprocess.run([str(stage / 'bin' / name), '--version'], capture_output=True, text=True, timeout=3)
                if result.returncode or version not in result.stdout.split():
                    return 1
            libc = ctypes.CDLL(None, use_errno=True)
            # RENAME_EXCHANGE publishes a complete directory without a missing-prefix window.
            if libc.renameat2(-100, os.fsencode(stage), -100, os.fsencode(prefix), 2):
                raise OSError(ctypes.get_errno(), 'reference publication failed')
            return 0
        finally:
            shutil.rmtree(stage)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.SubprocessError):
        raise SystemExit(1)

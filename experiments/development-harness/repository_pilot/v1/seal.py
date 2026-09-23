"""Run only in an unauthenticated disposable Docker container, never on host."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile

BASE = '9ab63986ad528a6ad5bf4c59fe104d5106d6ef9b'


def main():
    root = Path('/capture')
    root.mkdir()
    with tarfile.open('/input/workspace.tar') as archive:
        members = [m for m in archive.getmembers() if '.git' not in Path(m.name).parts]
        if any(not (m.isfile() or m.isdir() or m.issym()) for m in members):
            raise ValueError('unsupported archive entry')
        if sum(m.size for m in members) > 512 * 1024 * 1024:
            raise ValueError('workspace too large')
        archive.extractall(root, members=members, filter='data')
    tree = root/'app'
    if not (tree/'lib/ansible').is_dir():
        raise ValueError('missing repository')
    # Use only the pristine image's Git metadata; candidate .git is never loaded.
    env = {**os.environ, 'GIT_DIR': '/app/.git', 'GIT_WORK_TREE': str(tree),
           'GIT_INDEX_FILE': '/tmp/pilot-seal-index', 'GIT_CONFIG_NOSYSTEM': '1',
           'GIT_CONFIG_GLOBAL': '/dev/null'}
    git = ['git', '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false']
    subprocess.run(git+['read-tree', BASE], env=env, check=True)
    subprocess.run(git+['add', '--all', '--', '.'], cwd=tree, env=env, check=True)
    patch = subprocess.check_output(git+['diff', '--cached', '--binary', '--no-ext-diff', '--no-textconv', BASE], env=env)
    if len(patch) > 8 * 1024 * 1024:
        raise ValueError('patch cap exceeded')
    Path('/output/submission.patch').write_bytes(patch)
    Path('/output/seal.json').write_text(json.dumps({'base': BASE,
        'sha256': hashlib.sha256(patch).hexdigest(), 'bytes': len(patch)}, indent=2)+'\n')
    for path in Path('/output').iterdir():
        path.chmod(0o444)


if __name__ == '__main__':
    main()

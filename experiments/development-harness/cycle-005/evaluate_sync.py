"""Fixed external CLI-sync oracle; candidate exit claims never determine quality."""
import argparse
import hashlib
import json
from pathlib import Path
import stat
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync_fixture

CASES = sync_fixture.PUBLIC_CASES + ('npm-fail', 'wrong-version', 'missing-binary', 'kill')


def catalog():
    return [{'name': name, 'phase': 1, 'dimension': 'sync-integrity'} for name in CASES]


def identity(root):
    values = []
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if relative.parts[0] == '.git':
            continue
        mode = path.lstat().st_mode
        if path.is_symlink():
            content = str(path.readlink())
        elif path.is_file():
            content = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            content = None
        values.append((str(relative), mode, content))
    return hashlib.sha256(json.dumps(values).encode()).hexdigest()


def evaluate(candidate):
    before = identity(candidate)
    value = sync_fixture.observe(candidate, CASES, version='8.6.5')
    value['source_unchanged'] = before == identity(candidate)
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = evaluate(args.candidate.resolve())
    text = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end='')

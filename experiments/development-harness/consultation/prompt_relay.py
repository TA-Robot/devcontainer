"""Replace only the obsolete terminal prompt envelope, with both hashes recorded."""
import hashlib
import json
import os
from pathlib import Path
import sys


def main(path):
    spec = json.loads(path.read_text())
    incoming = sys.stdin.buffer.read(1048577)
    if hashlib.sha256(incoming).hexdigest() != spec['terminal_prompt_sha256']:
        raise ValueError('terminal prompt identity mismatch')
    actual = Path(spec['actual_prompt'])
    if actual.is_symlink() or hashlib.sha256(actual.read_bytes()).hexdigest() != spec['actual_prompt_sha256']:
        raise ValueError('actual prompt identity mismatch')
    with actual.open('rb') as stream:
        os.dup2(stream.fileno(), 0)
    os.execvp(spec['argv'][0], spec['argv'])


if __name__ == '__main__':
    main(Path(sys.argv[1]))

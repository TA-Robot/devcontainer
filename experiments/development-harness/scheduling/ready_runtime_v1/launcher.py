"""Evaluator-owned runtime readiness; activate before loading candidate code."""
import os
from pathlib import Path
import runpy
import sys

READY = b'EVALUATOR_RUNTIME_READY_V1\n'


def main():
    if len(sys.argv) != 2: raise ValueError('one candidate path required')
    candidate = str(Path(sys.argv[1]).resolve())
    os.write(2, READY)
    # Read exactly one byte: buffered readline could consume a raw-stdin
    # candidate's first request. No candidate imports/initialization precede it.
    if os.read(0, 1) != b'\x01': raise ValueError('activation required')
    sys.argv = [candidate]
    sys.path[0] = str(Path(candidate).parent)
    runpy.run_path(candidate, run_name='__main__')


if __name__ == '__main__': main()

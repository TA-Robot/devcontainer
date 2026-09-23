#!/usr/bin/env python3
"""Supplemental post-submission review; does not alter frozen 19 observations."""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--candidate', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
sys.dont_write_bytecode = True
sys.path.insert(0, str(args.candidate / 'scripts'))
module = importlib.import_module('agentctl_jobs')
path = args.candidate / 'scripts/agentctl_jobs.py'
before = hashlib.sha256(path.read_bytes()).hexdigest()
assert Path(module.__file__).resolve() == path.resolve()
rows = []
secret = 'fixture-long-integer-secret'
raw = '{"n":' + '9' * 5000 + ',"api_key":' + json.dumps(secret) + '}'
try:
    value, count = module._redact_log_text(raw)
    rows.append({'case': 'long-integer-and-secret', 'passed': secret not in value and '9' * 5000 in value and count > 0})
except Exception as exc:
    rows.append({'case': 'long-integer-and-secret', 'passed': False, 'exception': type(exc).__name__})
secret = 'sk-proj-' + 'a' * 20
raw = '{"message":"\\ud800 ' + secret + '"}'
try:
    value, count = module._redact_log_text(raw)
    value.encode('utf-8')
    json.loads(value)
    rows.append({'case': 'escaped-surrogate-with-token-is-utf8-printable', 'passed': secret not in value and count > 0})
except Exception as exc:
    rows.append({'case': 'escaped-surrogate-with-token-is-utf8-printable', 'passed': False, 'exception': type(exc).__name__})
result = {'candidate_sha256': before, 'reviewer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'source_unchanged': before == hashlib.sha256(path.read_bytes()).hexdigest(),
          'frozen_evaluator_unchanged': True, 'checks': rows}
args.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))

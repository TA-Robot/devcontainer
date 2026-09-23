"""Fixed diagnostic only; runs in the credential/network-free policy container."""
import json
import sys
import time

PROFILE = "normal"

if PROFILE == 'startup_delay':
    time.sleep(6)
sys.stderr.write('FIXED_RUNTIME_READY_V1\n')
sys.stderr.flush()
for line in sys.stdin:
    request = json.loads(line)
    if PROFILE == 'response_delay':
        time.sleep(6)
    print(json.dumps({'request_id': request['request_id'], 'assignments': []}), flush=True)

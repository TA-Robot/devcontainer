"""Do not treat one absent container as completed cleanup of a pending create."""
import json
from pathlib import Path
import re
import subprocess
import time


def drain(container, *, create_completed, seconds, command=subprocess.run,
          clock=time.monotonic, pause=time.sleep):
    if not re.fullmatch(r'(scheduling-native-|scheduling-policy-|termination-public-)[0-9a-f]{32}', container):
        raise ValueError('unowned container name')
    began = clock(); observed = False
    result = {'container': container, 'status': 'unknown', 'create_completed_before_audit': create_completed,
              'observation_bound_seconds': seconds, 'observed_container': False}
    def run(args):
        remaining = seconds-(clock()-began)
        if remaining <= 0: raise TimeoutError('recovery observation bound exceeded')
        return command(args, capture_output=True, text=True, timeout=min(15, remaining))
    try:
        while True:
            checked = run(['docker', 'inspect', container])
            if checked.returncode == 0:
                data = json.loads(checked.stdout)
                if len(data) != 1 or data[0]['Name'] != '/'+container:
                    raise ValueError('container identity mismatch')
                observed = True
                removed = run(['docker', 'rm', '-f', container])
                if removed.returncode != 0: raise ValueError('container removal failed')
            elif checked.returncode == 1 and ('no such object' in checked.stderr.lower() or 'no such container' in checked.stderr.lower()):
                if create_completed and clock()-began <= seconds:
                    result['status'] = 'confirmed'; break
                if observed:
                    result['reason'] = 'observed container removed; pending create completion unproven'; break
                if clock()-began >= seconds:
                    result['reason'] = 'create completion unobserved; absence does not prove recovery'; break
            else:
                raise ValueError('container observation failed')
            if clock()-began >= seconds:
                result['reason'] = 'recovery observation bound exceeded'; break
            pause(min(.2, max(0, seconds-(clock()-began))))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        result['reason'] = type(exc).__name__+': '+str(exc)
    result.update(observed_container=observed, elapsed_seconds=clock()-began)
    return result


def actor(folder, seconds):
    start = json.loads((folder/'start.json').read_text())
    report = json.loads((folder/'result.json').read_text()) if (folder/'result.json').exists() else {}
    # A bridge record proves the container ran. A mere start ledger does not.
    result = drain(start['container'], create_completed=bool(report.get('bridge')), seconds=seconds)
    (folder/'auth.private.json').unlink(missing_ok=True)
    result['credential_copy_absent'] = not (folder/'auth.private.json').exists()
    return result


def assessment(folder, seconds):
    """Audit authoritative evaluator records, never policy-returned container names."""
    path = folder/'evaluation/result.json'
    if not path.exists(): return []
    records = json.loads(path.read_text()); results = []
    for row in records.get('cases', []):
        execution = row.get('execution', {}); name = execution.get('container')
        if not name: continue
        # The frozen transport writes startup_seconds only after docker create
        # returned successfully. Error-message matching cannot establish that
        # fact, especially when an external signal interrupts create.
        completed = 'startup_seconds' in execution
        results.append(drain(name, create_completed=completed, seconds=seconds))
    return results

"""Study-only startup: wait for both nested Docker and the common cache."""
import importlib.util
import json
from pathlib import Path
import subprocess
import time

SPEC = importlib.util.spec_from_file_location('staged_campaign', Path(__file__).resolve().parents[2] / 'campaign.py')
campaign = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(campaign)

STARTUP = r'''set -eu
mkdir -p /tmp/harness-build-cache
cp /opt/harness-cache/index.json /opt/harness-cache/oci-layout /tmp/harness-build-cache/
ln -s /opt/harness-cache/blobs /tmp/harness-build-cache/blobs
cat > /tmp/harness-devcontainer-cache <<'SCRIPT'
#!/bin/sh
if [ "${1:-}" = build ]; then
    exec /usr/local/bin/devcontainer "$@" --cache-from type=local,src=/tmp/harness-build-cache
fi
exec /usr/local/bin/devcontainer "$@"
SCRIPT
chmod 0755 /tmp/harness-devcontainer-cache
touch /tmp/harness-cache-ready
exec sleep infinity
'''

PROBE = r'''import hashlib,json,pathlib,subprocess
marker=pathlib.Path('/tmp/harness-cache-ready')
if not marker.is_file(): raise SystemExit(1)
version=subprocess.check_output(['docker','info','--format','{{.ServerVersion}}'],text=True,timeout=3).strip()
index=pathlib.Path('/tmp/harness-build-cache/index.json')
print(json.dumps({'docker_version':version,'cache_index_sha256':hashlib.sha256(index.read_bytes()).hexdigest()}))
'''


class StudyDocker(campaign.Docker):
    def __init__(self, container, workspace, expected_id=None, *, cache_index_sha256):
        super().__init__(container, workspace, expected_id)
        self.expected_cache = cache_index_sha256
        self.preparation = None

    def start(self):
        started = time.monotonic()
        super().start()
        try:
            deadline = started + 60
            while time.monotonic() < deadline:
                try:
                    result = subprocess.run(['docker', 'exec', self.identity, 'python3', '-c', PROBE],
                                            capture_output=True, text=True, timeout=min(5, max(.01, deadline - time.monotonic())))
                except subprocess.TimeoutExpired:
                    continue
                if result.returncode == 0:
                    value = json.loads(result.stdout)
                    if value['cache_index_sha256'] != self.expected_cache:
                        raise campaign.CampaignError('common cache identity changed')
                    self.preparation = {**value, 'seconds': round(time.monotonic() - started, 3),
                                        'status': 'ready', 'model_started_during_preparation': False}
                    return
                time.sleep(min(.1, max(0, deadline - time.monotonic())))
            raise campaign.CampaignError('nested Docker/cache preparation exceeded 60 seconds')
        except BaseException:
            self.stop()
            self.preparation = {'status': 'failed', 'seconds': round(time.monotonic() - started, 3),
                                'model_started_during_preparation': False}
            raise

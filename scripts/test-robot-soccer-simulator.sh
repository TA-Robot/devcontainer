#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
image=robot-soccer-simulator:test
container="robot-soccer-test-$$"
trace_dir=$(mktemp -d)

cleanup() {
  docker rm -f "$container" >/dev/null 2>&1 || true
  rm -rf -- "$trace_dir"
}
trap cleanup EXIT

docker build \
  --file "$repo_root/experiments/robot-soccer-control/Dockerfile" \
  --tag "$image" \
  "$repo_root" >/dev/null

docker run --detach --rm \
  --name "$container" \
  --user "$(id -u):$(id -g)" \
  --publish 127.0.0.1::8080 \
  --volume "$trace_dir:/trace" \
  "$image" --log /trace/events.jsonl >/dev/null

port=$(docker port "$container" 8080/tcp | sed -n 's/.*://p')
base_url="http://127.0.0.1:$port"

for _ in $(seq 1 50); do
  if curl --fail --silent "$base_url/health" >/dev/null; then
    break
  fi
  sleep 0.1
done
curl --fail --silent "$base_url/health" >/dev/null

python3 - "$base_url" <<'PY'
import json
import sys
import time
import urllib.error
import urllib.request

base = sys.argv[1]

def call(path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(
        base + path,
        data=data,
        method="GET" if payload is None else "POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            body = response.read()
            return response.status, json.loads(body) if body else None
    except urllib.error.HTTPError as error:
        body = error.read()
        return error.code, json.loads(body) if body else None

status, spec = call("/v1/spec")
assert status == 200
assert len(spec["friendly_robot_ids"]) == 2
assert len(spec["enemy_robot_ids"]) == 3
assert spec["schema_version"] == 2
assert spec["observation_nominal_delay_ms"] == 200
encoded = json.dumps(spec)
for forbidden in ("kick_speed", "max_acceleration", "lateral_slip", "restitution"):
    assert forbidden not in encoded

status, started = call("/v1/start", {"seed": 41})
assert status == 201 and started["status"] == "running"
status, observation = call("/v1/observation")
assert status == 204 and observation is None

deadline = time.monotonic() + 1.5
while time.monotonic() < deadline:
    status, observation = call("/v1/observation")
    if status == 200:
        break
    time.sleep(0.03)
assert status == 200
assert len(observation["robots"]) == 5
assert "sample_time" not in observation
assert "contact" not in encoded

status, error = call(
    "/v1/command",
    {"robots": [{"id": "enemy_0", "velocity": {"x": 0, "y": 0}, "angular_velocity": 0, "kick": False}]},
)
assert status == 400 and "non-friendly" in error["error"]

status, accepted = call(
    "/v1/command",
    {"robots": [{"id": "friendly_0", "velocity": {"x": 0, "y": 0}, "angular_velocity": 0.2, "kick": False}]},
)
assert status == 200 and accepted["accepted"] == 1
PY

sleep 5.2
result=$(curl --fail --silent "$base_url/v1/result")
python3 - "$result" <<'PY'
import json
import sys
result = json.loads(sys.argv[1])
assert result["status"] == "failure", result
assert result["reason"] == "start_timeout", result
PY

python3 - "$trace_dir/events.jsonl" <<'PY'
import json
from pathlib import Path
import sys

text = Path(sys.argv[1]).read_text(encoding="utf-8")
events = [json.loads(line) for line in text.splitlines()]
kinds = {item["event"] for item in events}
assert {"server_started", "episode_started", "command_received", "observation_delivered", "terminal_snapshot", "episode_terminal"} <= kinds
delivered = [item["payload"] for item in events if item["event"] == "observation_delivered"]
terminal = next(item["payload"] for item in events if item["event"] == "terminal_snapshot")
assert len(terminal["robots"]) == 5
assert terminal["sequence"] > delivered[-1]["sequence"]
for forbidden in ("kick_speed", "max_acceleration", "lateral_slip", "observation_jitter_s"):
    assert forbidden not in text
PY

docker exec "$container" sh -c 'test ! -e /src && test ! -e /Cargo.toml'
echo "ok - robot soccer simulator core, hidden boundary, realtime API, and trace"

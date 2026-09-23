#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
image=${ROBOT_SOCCER_RENDERER_IMAGE:-robot-soccer-renderer:dev}
work=$(mktemp -d)

cleanup() {
  rm -rf -- "$work"
}
trap cleanup EXIT

python3 - "$work/events.jsonl" <<'PY'
import json
from pathlib import Path
import sys

path = Path(sys.argv[1])
robots = [
    ("friendly_0", "friendly", -1.7, 0.0, 0.0),
    ("friendly_1", "friendly", 0.4, 1.0, -0.4),
    ("enemy_0", "enemy", -0.5, 0.5, 3.14),
    ("enemy_1", "enemy", 3.5, 0.0, 3.14),
    ("enemy_2", "enemy", 2.8, -0.8, 3.14),
]
events = [{"event": "episode_started", "payload": {}}]
for sequence in range(1, 31):
    alpha = sequence / 30
    events.append(
        {
            "event": "observation_delivered",
            "payload": {
                "sequence": sequence,
                "robots": [
                    {
                        "id": robot_id,
                        "team": team,
                        "position": {"x": x + alpha * 0.2, "y": y},
                        "velocity": {"x": 0.2, "y": 0.0},
                        "heading": heading,
                        "angular_velocity": 0.0,
                    }
                    for robot_id, team, x, y, heading in robots
                ],
                "ball": {
                    "position": {"x": -1.3 + alpha * 2.0, "y": -0.2 * alpha},
                    "velocity": {"x": 2.0, "y": -0.2},
                },
            },
        }
    )
events.append(
    {
        "event": "episode_terminal",
        "payload": {"status": "success", "reason": "pass_and_goal", "elapsed_ms": 1000},
    }
)
path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
PY

if ! docker image inspect "$image" >/dev/null 2>&1; then
  "$repo_root/scripts/build-robot-soccer-renderer" >/dev/null
fi

"$repo_root/scripts/render-robot-soccer-trace" \
  "$work/events.jsonl" "$work/replay.mp4" >/dev/null

probe=$(docker run --rm \
  --entrypoint ffprobe \
  --volume "$work/replay.mp4:/video.mp4:ro" \
  "$image" \
  -v error \
  -show_entries stream=codec_name,width,height \
  -of csv=p=0 \
  /video.mp4)

[[ "$probe" == "h264,960,640" ]]
[[ -s "$work/replay.mp4" ]]
size=$(stat -c %s "$work/replay.mp4")
(( size < 1048576 ))

echo "ok - offline replay is compact H.264 and independent of simulator runtime"

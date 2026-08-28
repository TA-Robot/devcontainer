#!/usr/bin/env python3
"""Render a completed public robot-soccer JSONL trace to a compact MP4."""

from __future__ import annotations

import argparse
import collections
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any

from PIL import Image, ImageDraw, ImageFont

FIELD_LENGTH = 9.0
FIELD_WIDTH = 6.0
GOAL_WIDTH = 1.5
ROBOT_RADIUS = 0.09
KICKER_WIDTH = 0.108
OBSERVATION_HZ = 30

FRIENDLY_FILL = (42, 195, 222)
FRIENDLY_EDGE = (190, 247, 255)
ENEMY_FILL = (225, 74, 111)
ENEMY_EDGE = (255, 202, 214)


def wrap_angle(value: float) -> float:
    return (value + math.pi) % (2.0 * math.pi) - math.pi


def lerp(left: float, right: float, alpha: float) -> float:
    return left + (right - left) * alpha


def lerp_angle(left: float, right: float, alpha: float) -> float:
    return wrap_angle(left + wrap_angle(right - left) * alpha)


def load_episode(
    path: Path, requested: int
) -> tuple[list[dict[str, Any]], dict[str, Any], int]:
    episodes: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"invalid JSON at line {line_number}: {error}") from error
            kind = event.get("event")
            if kind == "episode_started":
                current = {"observations": [], "result": None}
                episodes.append(current)
            elif current is not None and kind == "observation_delivered":
                current["observations"].append(event.get("payload"))
            elif current is not None and kind == "episode_terminal":
                current["result"] = event.get("payload")

    if not episodes:
        raise ValueError("trace contains no episode_started event")
    index = requested - 1 if requested > 0 else requested
    try:
        episode = episodes[index]
    except IndexError as error:
        raise ValueError(
            f"episode {requested} is unavailable; trace contains {len(episodes)} episodes"
        ) from error
    observations = [item for item in episode["observations"] if isinstance(item, dict)]
    if not observations:
        raise ValueError("selected episode contains no delivered observations")
    deduplicated = {int(item["sequence"]): item for item in observations}
    frames = [deduplicated[key] for key in sorted(deduplicated)]
    resolved_episode = index + 1 if index >= 0 else len(episodes) + index + 1
    return (
        frames,
        episode["result"] or {"status": "incomplete", "reason": None},
        resolved_episode,
    )


def interpolate_observation(
    left: dict[str, Any], right: dict[str, Any], alpha: float, sequence: int
) -> dict[str, Any]:
    left_robots = {robot["id"]: robot for robot in left["robots"]}
    right_robots = {robot["id"]: robot for robot in right["robots"]}
    robots = []
    for robot_id in sorted(left_robots):
        before = left_robots[robot_id]
        after = right_robots.get(robot_id, before)
        robots.append(
            {
                "id": robot_id,
                "team": before["team"],
                "position": {
                    "x": lerp(before["position"]["x"], after["position"]["x"], alpha),
                    "y": lerp(before["position"]["y"], after["position"]["y"], alpha),
                },
                "heading": lerp_angle(before["heading"], after["heading"], alpha),
            }
        )
    return {
        "sequence": sequence,
        "robots": robots,
        "ball": {
            "position": {
                "x": lerp(
                    left["ball"]["position"]["x"],
                    right["ball"]["position"]["x"],
                    alpha,
                ),
                "y": lerp(
                    left["ball"]["position"]["y"],
                    right["ball"]["position"]["y"],
                    alpha,
                ),
            }
        },
    }


def expand_frames(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expanded = [observations[0]]
    for left, right in zip(observations, observations[1:]):
        gap = int(right["sequence"]) - int(left["sequence"])
        if gap <= 0:
            continue
        if gap > OBSERVATION_HZ * 10:
            raise ValueError(f"observation sequence gap is unexpectedly large: {gap}")
        for step in range(1, gap + 1):
            expanded.append(
                interpolate_observation(
                    left,
                    right,
                    step / gap,
                    int(left["sequence"]) + step,
                )
            )
    return expanded


class Painter:
    def __init__(self, width: int, height: int, trail_seconds: float) -> None:
        self.width = width
        self.height = height
        self.hud_height = max(42, height // 14)
        margin = max(22, width // 40)
        available_width = width - margin * 2
        available_height = height - self.hud_height - margin * 2
        self.scale = min(available_width / FIELD_LENGTH, available_height / FIELD_WIDTH)
        self.field_left = (width - FIELD_LENGTH * self.scale) / 2.0
        self.field_top = self.hud_height + (
            height - self.hud_height - FIELD_WIDTH * self.scale
        ) / 2.0
        self.field_right = self.field_left + FIELD_LENGTH * self.scale
        self.field_bottom = self.field_top + FIELD_WIDTH * self.scale
        self.trail_limit = max(1, round(trail_seconds * OBSERVATION_HZ))
        self.trails: dict[str, collections.deque[tuple[int, int]]] = {}
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        self.font = ImageFont.truetype(font_path, max(13, height // 38))
        self.small_font = ImageFont.truetype(font_path, max(10, height // 55))

    def point(self, x: float, y: float) -> tuple[int, int]:
        return (
            round(self.field_left + (x + FIELD_LENGTH / 2.0) * self.scale),
            round(self.field_top + (FIELD_WIDTH / 2.0 - y) * self.scale),
        )

    def draw_field(self, draw: ImageDraw.ImageDraw) -> None:
        draw.rectangle((0, 0, self.width, self.height), fill=(13, 20, 27))
        stripe_width = (self.field_right - self.field_left) / 12.0
        for index in range(12):
            color = (31, 112, 73) if index % 2 == 0 else (35, 122, 79)
            draw.rectangle(
                (
                    self.field_left + index * stripe_width,
                    self.field_top,
                    self.field_left + (index + 1) * stripe_width,
                    self.field_bottom,
                ),
                fill=color,
            )
        line = max(2, round(self.scale * 0.015))
        white = (225, 238, 229)
        draw.rectangle(
            (self.field_left, self.field_top, self.field_right, self.field_bottom),
            outline=white,
            width=line,
        )
        center_x = (self.field_left + self.field_right) / 2.0
        draw.line((center_x, self.field_top, center_x, self.field_bottom), fill=white, width=line)
        center_radius = self.scale * 0.5
        center_y = (self.field_top + self.field_bottom) / 2.0
        draw.ellipse(
            (
                center_x - center_radius,
                center_y - center_radius,
                center_x + center_radius,
                center_y + center_radius,
            ),
            outline=white,
            width=line,
        )
        goal_half = GOAL_WIDTH * self.scale / 2.0
        goal_depth = self.scale * 0.18
        for x, outer in (
            (self.field_left, self.field_left - goal_depth),
            (self.field_right, self.field_right + goal_depth),
        ):
            draw.rectangle(
                (min(x, outer), center_y - goal_half, max(x, outer), center_y + goal_half),
                outline=(178, 194, 204),
                width=line,
            )

    def draw_trails(self, draw: ImageDraw.ImageDraw, frame: dict[str, Any]) -> None:
        entities = [(robot["id"], robot["position"]) for robot in frame["robots"]]
        entities.append(("ball", frame["ball"]["position"]))
        for entity_id, position in entities:
            trail = self.trails.setdefault(
                entity_id, collections.deque(maxlen=self.trail_limit)
            )
            trail.append(self.point(position["x"], position["y"]))
            if len(trail) < 2:
                continue
            if entity_id == "ball":
                color = (242, 210, 92)
            elif entity_id.startswith("friendly"):
                color = (54, 157, 174)
            else:
                color = (169, 60, 86)
            draw.line(list(trail), fill=color, width=max(1, round(self.scale * 0.012)))

    def draw_robot(self, draw: ImageDraw.ImageDraw, robot: dict[str, Any]) -> None:
        cx, cy = self.point(robot["position"]["x"], robot["position"]["y"])
        radius = max(7, round(ROBOT_RADIUS * self.scale))
        fill, edge = (
            (FRIENDLY_FILL, FRIENDLY_EDGE)
            if robot["team"] == "friendly"
            else (ENEMY_FILL, ENEMY_EDGE)
        )
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=fill, outline=edge, width=2)
        heading = float(robot["heading"])
        front_distance = math.sqrt(
            ROBOT_RADIUS * ROBOT_RADIUS - (KICKER_WIDTH / 2.0) ** 2
        )
        front = front_distance * self.scale
        half = KICKER_WIDTH * self.scale / 2.0
        cosine, sine = math.cos(heading), math.sin(heading)
        front_center = (cx + cosine * front, cy - sine * front)
        tangent = (-sine, -cosine)
        chord = (
            front_center[0] + tangent[0] * half,
            front_center[1] + tangent[1] * half,
            front_center[0] - tangent[0] * half,
            front_center[1] - tangent[1] * half,
        )
        draw.line(chord, fill=(255, 224, 91), width=max(3, radius // 3))
        nose = (cx + cosine * radius * 1.22, cy - sine * radius * 1.22)
        draw.line((cx, cy, *nose), fill=(245, 250, 252), width=2)
        label = ("F" if robot["team"] == "friendly" else "E") + robot["id"].rsplit("_", 1)[-1]
        draw.text((cx + radius + 3, cy - radius), label, font=self.small_font, fill=(240, 245, 248))

    def render(
        self,
        frame: dict[str, Any],
        frame_index: int,
        first_sequence: int,
        episode_number: int,
        result: dict[str, Any],
    ) -> Image.Image:
        image = Image.new("RGB", (self.width, self.height))
        draw = ImageDraw.Draw(image)
        self.draw_field(draw)
        self.draw_trails(draw, frame)
        for robot in frame["robots"]:
            self.draw_robot(draw, robot)
        ball_x, ball_y = self.point(
            frame["ball"]["position"]["x"], frame["ball"]["position"]["y"]
        )
        ball_radius = max(3, round(0.0215 * self.scale))
        draw.ellipse(
            (
                ball_x - ball_radius,
                ball_y - ball_radius,
                ball_x + ball_radius,
                ball_y + ball_radius,
            ),
            fill=(250, 220, 102),
            outline=(255, 249, 214),
            width=2,
        )
        elapsed = (int(frame["sequence"]) - first_sequence) / OBSERVATION_HZ
        status = str(result.get("status", "incomplete")).upper()
        reason = result.get("reason") or ""
        draw.text(
            (18, 10),
            f"EP {episode_number}   T+{elapsed:05.2f}s   {status} {reason}",
            font=self.font,
            fill=(235, 241, 245),
        )
        draw.text(
            (self.width - 190, 14),
            f"FRAME {frame_index:04d}",
            font=self.small_font,
            fill=(152, 174, 187),
        )
        return image


def encode(
    frames: list[dict[str, Any]],
    result: dict[str, Any],
    output: Path,
    episode: int,
    width: int,
    height: int,
    output_fps: int,
    crf: int,
    preset: str,
    trail_seconds: float,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    painter = Painter(width, height, trail_seconds)
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pixel_format",
        "rgb24",
        "-video_size",
        f"{width}x{height}",
        "-framerate",
        str(OBSERVATION_HZ),
        "-i",
        "-",
        "-an",
        "-vf",
        f"fps={output_fps}",
        "-c:v",
        "libx264",
        "-preset",
        preset,
        "-crf",
        str(crf),
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert process.stdin is not None
    first_sequence = int(frames[0]["sequence"])
    try:
        for index, frame in enumerate(frames):
            image = painter.render(
                frame, index, first_sequence, episode, result
            )
            process.stdin.write(image.tobytes())
        process.stdin.close()
        return_code = process.wait()
    except BrokenPipeError:
        return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"ffmpeg exited with status {return_code}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--episode", type=int, default=-1, help="1-based index; -1 selects latest")
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=640)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--crf", type=int, default=30, help="higher is smaller; useful range 18-36")
    parser.add_argument(
        "--preset",
        choices=("medium", "slow", "slower"),
        default="slow",
    )
    parser.add_argument("--trail-seconds", type=float, default=0.8)
    args = parser.parse_args()
    if args.width % 2 or args.height % 2:
        parser.error("width and height must be even for yuv420p")
    if not 18 <= args.crf <= 40:
        parser.error("crf must be between 18 and 40")
    observations, result, resolved_episode = load_episode(args.trace, args.episode)
    frames = expand_frames(observations)
    encode(
        frames,
        result,
        args.output,
        resolved_episode,
        args.width,
        args.height,
        args.fps,
        args.crf,
        args.preset,
        args.trail_seconds,
    )
    size_mib = args.output.stat().st_size / (1024 * 1024)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "frames": len(frames),
                "fps": args.fps,
                "crf": args.crf,
                "size_mib": round(size_mib, 3),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)

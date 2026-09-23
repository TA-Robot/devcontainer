#!/usr/bin/env python3
"""Deliberately small baseline controller for API diagnosis, not evaluation gold."""

from __future__ import annotations

import argparse
import json
import math
import time
import urllib.error
import urllib.request


def request(base_url: str, path: str, payload: object | None = None) -> tuple[int, object | None]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    method = "GET" if payload is None else "POST"
    call = urllib.request.Request(
        base_url + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(call, timeout=1.0) as response:
            body = response.read()
            return response.status, json.loads(body) if body else None
    except urllib.error.HTTPError as error:
        body = error.read()
        return error.code, json.loads(body) if body else None


def wrap_angle(value: float) -> float:
    while value > math.pi:
        value -= 2.0 * math.pi
    while value < -math.pi:
        value += 2.0 * math.pi
    return value


def robot_command(robot: dict[str, object], target: tuple[float, float], face: tuple[float, float], kick: bool) -> dict[str, object]:
    position = robot["position"]
    heading = float(robot["heading"])
    dx = target[0] - float(position["x"])
    dy = target[1] - float(position["y"])
    distance = math.hypot(dx, dy)
    speed = min(1.25, distance * 3.0)
    if distance > 1e-6:
        gx, gy = dx / distance * speed, dy / distance * speed
    else:
        gx, gy = 0.0, 0.0
    cos, sin = math.cos(heading), math.sin(heading)
    local_x = cos * gx + sin * gy
    local_y = -sin * gx + cos * gy
    face_angle = math.atan2(face[1] - float(position["y"]), face[0] - float(position["x"]))
    angular = max(-4.0, min(4.0, wrap_angle(face_angle - heading) * 4.0))
    return {
        "id": robot["id"],
        "velocity": {"x": local_x, "y": local_y},
        "angular_velocity": angular,
        "kick": kick,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:18080")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    status, response = request(args.base_url, "/v1/start", {"seed": args.seed})
    if status != 201:
        raise SystemExit(f"start failed: HTTP {status}: {response}")

    phase = "pass"
    initial_ball = None
    last_sequence = -1
    while True:
        result_status, result = request(args.base_url, "/v1/result")
        if result_status != 200:
            raise SystemExit(f"result failed: HTTP {result_status}: {result}")
        if result["status"] not in {"idle", "running"}:
            print(json.dumps(result, ensure_ascii=False))
            return 0 if result["status"] == "success" else 1

        observation_status, observation = request(args.base_url, "/v1/observation")
        if observation_status == 204 or observation is None:
            time.sleep(1.0 / 60.0)
            continue
        if observation["sequence"] == last_sequence:
            time.sleep(1.0 / 60.0)
            continue
        last_sequence = observation["sequence"]
        robots = {item["id"]: item for item in observation["robots"]}
        ball = observation["ball"]["position"]
        ball_xy = (float(ball["x"]), float(ball["y"]))
        if initial_ball is None:
            initial_ball = ball_xy
        receiver = robots["friendly_1"]["position"]
        receiver_xy = (float(receiver["x"]), float(receiver["y"]))
        ball_velocity = observation["ball"]["velocity"]
        ball_speed = math.hypot(float(ball_velocity["x"]), float(ball_velocity["y"]))
        if phase == "pass" and (
            math.dist(ball_xy, initial_ball) > 0.22 or ball_speed > 0.65
        ):
            phase = "shoot"

        if phase == "pass":
            direction = (receiver_xy[0] - ball_xy[0], receiver_xy[1] - ball_xy[1])
            length = max(math.hypot(*direction), 1e-6)
            behind = (ball_xy[0] - 0.085 * direction[0] / length, ball_xy[1] - 0.085 * direction[1] / length)
            commands = [
                robot_command(robots["friendly_0"], behind, receiver_xy, True),
                robot_command(robots["friendly_1"], receiver_xy, ball_xy, False),
            ]
        else:
            goal = (4.6, 0.0)
            direction = (goal[0] - ball_xy[0], goal[1] - ball_xy[1])
            length = max(math.hypot(*direction), 1e-6)
            behind = (ball_xy[0] - 0.085 * direction[0] / length, ball_xy[1] - 0.085 * direction[1] / length)
            commands = [
                robot_command(robots["friendly_0"], (ball_xy[0] - 0.5, ball_xy[1] - 0.5), ball_xy, False),
                robot_command(robots["friendly_1"], behind, goal, True),
            ]
        command_status, command_response = request(
            args.base_url, "/v1/command", {"robots": commands}
        )
        if command_status != 200:
            raise SystemExit(
                f"command failed: HTTP {command_status}: {command_response}"
            )
        time.sleep(1.0 / 60.0)


if __name__ == "__main__":
    raise SystemExit(main())

# Public controller specification

This file is the complete simulator information supplied to a controller
developer. Values or behavior not stated here must be treated as unknown.

## Objective and rules

- One central controller operates `friendly_0`, `friendly_1`, and `friendly_2`.
- The simulator operates `enemy_0` and `enemy_1`.
- An episode begins when `POST /v1/start` succeeds and lasts at most 30 seconds
  of wall-clock time.
- A friendly robot must contact the ball within the first 5 seconds. Otherwise
  the episode fails.
- Until that first friendly contact, enemies must remain outside the published
  exclusion radius around the ball. After contact, they may approach and play
  the ball.
- Enemy contact does not end the episode. Friendly robots may recover the ball.
- A pass is complete when a friendly robot other than the first friendly to
  contact the ball subsequently contacts it. That receiving robot must then
  kick from its front kick segment before a goal can count.
- A ball crossing the attacking goal line within the goal mouth succeeds only
  after that pass-and-receiver-kick sequence. A direct goal fails.
- A ball leaving any other field boundary, or expiry at 30 seconds, fails.
- Touch and kick events used by the private referee are not exposed. The
  controller must infer the pass and shot from observed ball motion.

## Geometry

All distances are metres and all angles are radians.

- Field: 9.0 m long (`x`), 6.0 m wide (`y`). Friendly robots attack toward
  positive `x`.
- Goal mouth: 1.5 m wide and centred on `y = 0` at the positive `x` boundary.
- Robot radius: 0.09 m.
- Ball radius: 0.0215 m.
- A robot is a vertical cylinder whose front is cut by a flat chord. The flat
  front segment faces the robot's positive local `x` axis.
- The kick-capable segment is centred on that flat face and is 0.108 m wide,
  equal to 60% of the robot diameter.
- Robot/robot, robot/ball, and robot/field collisions are physical. The ball
  leaving the field is not reflected.

If `kick` is true while the ball newly contacts the kick-capable segment, the
simulator applies a forward kick. There is no time-based cooldown. A continuous
overlap does not apply another impulse on every internal physics tick; after
separation, another contact may kick immediately. Raising `kick` while already
in valid front contact may also kick once.

## Coordinates and observation

- Positions and measured velocities use global field coordinates.
- Robot heading `0` points along global positive `x`; positive rotation is
  counter-clockwise.
- Controller velocity commands use each robot's local frame at the simulator's
  current, hidden state.
- Observation frames are produced nominally at 30 Hz.
- Delivered observations are nominally 200 ms old and include latency jitter.
- The source timestamp, exact age, true current state, contact events, and kick
  events are not exposed.
- The observation includes position, global velocity, heading, and angular
  velocity for every robot, plus position and global velocity for the ball.

The controller must infer the current state from delayed frames, its command
history, and observed motion.

## Command semantics

Each friendly command contains only:

- desired local velocity `x` and `y`;
- desired angular velocity;
- boolean `kick`.

Commands are held until replaced. The robot does not instantly assume the
desired velocity. Hidden motor-control and physical dynamics move actual
velocity toward the command subject to response, acceleration, saturation,
friction, slip, collision, and other undisclosed effects. Sending a large value
does not bypass hidden saturation.

## HTTP API

The default runtime listens on `0.0.0.0:8080`. Every response body is JSON
except `GET /v1/observation`, which returns HTTP 204 until a delayed frame is
available.

### `GET /health`

Returns `{"ok":true}`.

### `GET /v1/spec`

Returns the public geometry, counts, timing rules, and observation contract.
It does not return dynamics, opponent policy, jitter distribution, or seed.

### `POST /v1/start`

Starts a fresh episode and discards the prior episode. An empty body or `{}` is
accepted. Development runtimes also accept `{"seed":<unsigned integer>}` for
repeatable local diagnosis; official evaluation may ignore or override it.

### `POST /v1/command`

```json
{
  "robots": [
    {
      "id": "friendly_0",
      "velocity": {"x": 0.7, "y": -0.2},
      "angular_velocity": 1.0,
      "kick": false
    }
  ]
}
```

The array may update one or more friendly robots atomically. Unknown, duplicate,
non-finite, or enemy IDs are rejected. Omitted friendly robots retain their
previous commands.

### `GET /v1/observation`

```json
{
  "sequence": 42,
  "robots": [
    {
      "id": "friendly_0",
      "team": "friendly",
      "position": {"x": -1.2, "y": 0.1},
      "velocity": {"x": 0.3, "y": 0.0},
      "heading": 0.02,
      "angular_velocity": 0.1
    }
  ],
  "ball": {
    "position": {"x": -1.0, "y": 0.0},
    "velocity": {"x": 0.0, "y": 0.0}
  }
}
```

The endpoint returns only the newest frame whose delayed release time has
arrived. Frames may be skipped if the client polls slowly.

### `GET /v1/result`

Returns one of:

```json
{"status":"idle","reason":null,"elapsed_ms":0}
{"status":"running","reason":null,"elapsed_ms":2100}
{"status":"success","reason":"pass_and_goal","elapsed_ms":12840}
{"status":"failure","reason":"pass_sequence_incomplete","elapsed_ms":7420}
{"status":"failure","reason":"start_timeout","elapsed_ms":5000}
{"status":"failure","reason":"ball_out","elapsed_ms":9310}
{"status":"failure","reason":"episode_timeout","elapsed_ms":30000}
```

`elapsed_ms` is lifecycle/result information and does not reveal an observation
frame's source timestamp.

## Hidden information

The controller is not given exact translational or rotational response,
acceleration, velocity limits, friction, slip, restitution, ball deceleration,
kick impulse, observation jitter distribution, opponent parameters, or their
episode-to-episode variation. Development agents may inspect only public API
traffic and the corresponding text trace supplied by the experiment operator.

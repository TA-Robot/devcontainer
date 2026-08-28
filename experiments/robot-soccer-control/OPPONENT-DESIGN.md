# Internal opponent-control design

This is an authoring-repository document. It describes hidden evaluation logic
and must not be shipped beside `PUBLIC-SPEC.md` to a controller developer.

## Design objective

The opponent is a centrally coordinated defensive team, not three independent
robots chasing the current ball position. Its objective is to deny the
pass-and-shot sequence while preserving the same physical dynamics, collision
model, field geometry, and pre-restart exclusion rule as the controlled team.

The implementation prioritizes these invariants:

- no active kick toward the opponent's own goal;
- no enemy entry into the restart exclusion area before friendly contact;
- one field defender pressures the predicted ball while the other preserves
  pass-lane and receiver coverage;
- roles change only when the alternative interceptor has a material advantage;
- the goalkeeper predicts the shot crossing rather than following ball `y`;
- motion commands respect acceleration, speed, angular-rate, and braking limits.

## Control pipeline

The policy runs on every 240 Hz physics tick using the simulator's true state.
It does not use or weaken the controller-facing 200 ms delayed observation API.

1. **Drag-aware ball prediction** integrates the analytic displacement under
   linear drag instead of using constant-velocity extrapolation.
2. **Reachability estimation** samples future ball positions and compares them
   with the distance each defender can cover under its current speed, maximum
   acceleration, velocity limit, and a rotation-time penalty.
3. **Role auction with hysteresis** assigns the materially faster field robot
   as ball winner. A 120 ms-equivalent intercept advantage and 300 ms switch
   hold prevent role chatter.
4. **Role-specific target generation** creates a goal-side striking pose for
   the winner and a ball-to-receiver shadow position for the cover defender.
5. **Braking-distance motion control** derives desired speed from
   `sqrt(v_arrival^2 + 2*a*distance)`, adds bounded target feed-forward, converts
   it to the robot-local command frame, and computes a bounded angular braking
   command.
6. **Short-range collision avoidance** adds repulsion from all other robots
   before the final speed clamp.

## Ball winner and safe clearance

The ball winner predicts an intercept point up to two seconds ahead. It chooses
a negative-`x` clearance direction biased toward field centre and away from the
nearest friendly attacker. The desired robot pose lies behind the predicted
ball relative to that clearance direction.

If the defender is still on the attacking side of the ball, it first moves
laterally, then around the ball, and only then closes the striking pose. Kicking
remains disabled until the defender is goal-side. This prevents the previous
failure mode where a defender reached the ball from the left and kicked toward
its own goal.

## Cover defender

The second field defender occupies the interior of the current
ball-to-receiver segment with a goal-side offset. Receiver velocity is used as
feed-forward so the marker does not trail a moving setup. It changes to a
clearance role when the ball enters its local pressure radius or when a shot is
already progressing through the defensive half.

## Goalkeeper

For a positive-`x` shot, the goalkeeper solves the time at which the drag-aware
ball trajectory crosses its guard plane and moves toward the corresponding
`y`. Feed-forward is derived from the remaining crossing time, so a sudden
trajectory reversal requests an immediate high-speed recovery rather than a
unit-gain position correction.

When no shot will reach the guard plane, the goalkeeper steps forward and uses
the line between the likely source and goal centre to reduce the open angle.
It may move beyond the goal-mouth `y` range to intercept a diagonal shot before
the goal line. Its kick is subject to the same goal-side clearance invariant as
the field defenders.

## Verification snapshot

The implementation is covered by tests for drag integration, reachability role
switching, braking-distance command strength, goalkeeper crossing prediction,
pre-restart exclusion, goal-side clearance, deterministic physics, and scoring
rules. The prior best development controller was also run against seeds 1–12:

- controller successes: `0/12`;
- `start_timeout`: 8;
- defensive `ball_out`: 3;
- `episode_timeout`: 1.

This corpus is evidence against the current controller, not proof of global
optimality. Future tuning should add diverse attacking controllers and compare
defensive success rate, illegal-entry count, own-goal count, time to possession,
shot suppression, and goalkeeper contact rate.

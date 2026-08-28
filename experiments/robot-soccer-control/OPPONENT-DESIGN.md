# Internal opponent-control design

This is an authoring-repository document. It describes hidden evaluation logic
and must not be shipped beside `PUBLIC-SPEC.md` to a controller developer.

## Purpose and standard of strength

The opponent is a centrally coordinated defensive team, not three independent
robots chasing the current ball position. It should force a development agent
to solve delayed observation, local-frame control, coordination, passing, and
shooting as a coupled problem. A controller that succeeds only because the
opponent stands still, blindly follows the ball, or kicks into its own goal is
not useful evidence about the devcontainer's multi-agent development quality.

"Strong" is therefore not a synonym for high speed or aggressive pressing.
The policy should:

- deny the pass-and-shot sequence over varied hidden dynamics and seeds;
- react to a real shot before optimizing against hypothetical later actions;
- cover distinct threats with distinct robots instead of duplicating effort;
- clear toward safe exits without creating own-goal trajectories;
- preserve restart exclusion, field boundaries, and collision safety;
- remain deterministic, inexpensive enough for a 240 Hz simulation, and
  explainable enough to diagnose benchmark failures.

The current implementation is a deterministic receding-horizon hybrid policy.
It combines a phase automaton, continuous possession belief, an adversarial
threat ensemble, acceleration-aware reachability, a two-role assignment
auction, minimax cover and goalkeeper placement, maximin clearance selection,
and sampled velocity-obstacle execution. It is deliberately more substantial
than an MVP heuristic, while avoiding a heavyweight optimizer whose numerical
runtime would become part of the benchmark.

## Objective hierarchy

The policy approximates a lexicographic objective. Earlier items dominate
later ones:

1. obey the restart exclusion and simulator rules;
2. prevent a valid goal and avoid an own goal;
3. intercept an observed in-flight shot;
4. win or remove the loose ball;
5. deny the legal receiver and high-value pass/shot lanes;
6. avoid collisions and boundary overshoot;
7. minimize travel time, role switching, and redundant coverage.

This ordering matters. A weighted sum alone can make a goalkeeper remain
central because several low-probability imagined shots collectively outweigh
one observed diagonal shot. The real in-flight trajectory is therefore given
evidential priority, and shot emergency can preempt phase hysteresis.

## Information boundary

The opponent runs inside the hidden simulator and uses the simulator's current
state and hidden dynamics. It does not consume, modify, or weaken the public
200 ms delayed observation stream. Controller authors still see only the
documented public API. No contact event, role, threat score, dynamics parameter,
or private terminal state is exposed.

Using true state here is intentional: this is the private environment policy,
not another contestant. Adding artificial perception error to the opponent
would confound controller quality with an undocumented opponent handicap.

## Layered control architecture

The control pipeline runs at 60 Hz while physics remains at 240 Hz:

1. update the defensive phase and attacker-control beliefs;
2. construct observed and counterfactual threat trajectories;
3. solve directed robot reachability and drag-aware ball interception;
4. compare both possible ball-winner/cover assignments;
5. optimize the cover target against threats not already handled by the GK;
6. optimize the GK guard-plane position with a minimax objective;
7. search safe clearance rays when an enemy can win the ball;
8. convert tactical poses to braking-distance nominal velocities;
9. sample collision- and boundary-safe local velocity alternatives;
10. issue local-frame translational, angular, and kick commands.

The boundaries between these layers are deliberate. Tactical planning reasons
about threats and responsibility. The execution layer reasons about dynamics
and safety. Mixing both in one collection of position `if` statements was the
main source of previous own goals, late saves, chatter, and collisions.

## Hybrid defensive phase

Five phases make discontinuous tactical priorities explicit:

- `Restart`: establish a lane block, mark the required receiver, keep the GK
  prepared, and project all field-player targets outside the exclusion disk.
- `FriendlyControl`: press an attacker likely to control the ball while the
  second defender denies its next action.
- `LooseBall`: auction the ball-winning role using predicted interception.
- `Clearance`: an enemy is close enough to establish control; prioritize a
  goal-side striking pose and safe exit ray.
- `ShotEmergency`: the ball is moving toward the defended goal with sufficient
  speed and either field position or a detected velocity jump indicates a
  shot. This phase takes effect immediately.

Non-emergency changes require a short dwell time. This is not a claim that one
fixed dwell is universally optimal; it is a local stabilizer for the simulator
tick rate. Emergency transitions bypass it, because tactical smoothness must
not delay a save.

## Continuous attacker-control belief

Distance to the ball is insufficient evidence of possession. For each friendly
robot, the policy computes a bounded control likelihood from:

- distance to the ball through a smooth logistic transition;
- whether the front/kicker direction faces the ball;
- relative closing speed rather than absolute robot speed;
- ball motion, which lowers confidence when the ball is escaping.

The score does not claim to be a calibrated probability. It is a continuous
belief used to rank threat hypotheses and avoid brittle distance thresholds.
The phase automaton also uses it to distinguish likely friendly control from a
merely nearby robot facing or moving away from the ball.

## Adversarial threat ensemble

The policy does not commit to one guessed attacking intent. It creates up to
16 concurrent trajectory hypotheses:

- the analytically predicted trajectory of a currently moving ball;
- direct ball-to-goal-centre and ball-to-post lanes;
- three possible shot lanes from the predicted pose of each attacker;
- three lead-pass targets from each attacker to the other attacker.

Each hypothesis has an origin, destination, estimated arrival time, and
importance weight. Weight depends on control likelihood, goal geometry, and
the special value of reaching the legal receiver. Arrival time includes robot
control acquisition and ball flight, rather than comparing geometric distance
alone.

An observed in-flight trajectory is evidence and receives much greater weight
than counterfactual future shots. This prevents robust/minimax planning from
becoming indecisive in an actual emergency.

The ensemble is intentionally small and structured. A dense continuous action
tree or learned intent model would require a representative attacker corpus
and a training/evaluation separation that does not yet exist.

## Dynamics-aware reachability

Ball prediction analytically integrates linear drag:

`p(t) = p(0) + v(0) * (1 - exp(-drag*t)) / drag`.

Robot reachability is directional. For a proposed target and time budget it:

- projects current velocity onto the target direction, retaining negative
  velocity when the robot is moving away;
- charges a bounded delay for heading reversal;
- integrates acceleration in 25 ms increments;
- applies the hidden velocity limit;
- includes robot and ball radii only at interception comparison time.

This corrects the optimistic scalar-speed model, which treated a robot running
away from a target as already moving toward it. The same reachability primitive
is shared by role selection, threat timing, cover selection, clearance safety,
and GK responsibility. Shared timing semantics are more important than
independently tuned heuristics in each role.

## Joint field-defender assignment

There are only two legal ball-winner assignments, so both are evaluated. For
each assignment the policy computes:

- the primary defender's earliest drag-aware ball interception;
- the other defender's optimized cover point;
- directed travel time to both responsibilities;
- a penalty when both targets collapse into the same small region.

The incumbent changes only when the alternate joint assignment has a material
advantage and the role hold has elapsed. Thus the auction is based on the pair's
combined defensive value, not simply which robot is nearest to the ball.

This is a compact joint optimizer, not three independent role rules. Exhaustive
assignment is preferable to a generic combinatorial solver because there are
only two field defenders and the exact search is trivial.

## Complementary cover optimization

Cover candidates are sampled on every shot and pass hypothesis, plus several
interior points on the current ball-to-receiver segment. Candidate scoring
combines:

- worst-case weighted distance to any important threat segment;
- a smaller aggregate residual over all hypotheses;
- directed travel time;
- minimum separation from the primary interception target;
- a goal-side marking preference;
- the fraction of the threat that the goalkeeper cannot already cover.

The final term coordinates field defenders with the goalkeeper. A lane the GK
can reach is discounted but not ignored; a lane outside the GK's directed
reachable set remains the field defender's responsibility. This reduces the
common failure where all three defenders follow the same ball line and leave
the receiver unmarked.

## Minimax goalkeeper

The goalkeeper searches a small guard-plane grid at multiple depths and across
lateral points. The candidate set includes regular goal-width samples and the
intersection of every threat hypothesis with each guard plane.

For each candidate it scores:

- the worst weighted residual opening across all threats;
- aggregate residual opening as a tie-breaker;
- whether directed GK arrival is later than ball arrival;
- travel cost;
- a phase-dependent depth cost.

During `ShotEmergency`, coverage deficit and arrival lateness for the observed
in-flight ball are a lexicographic first objective. Hypothetical future shots
and movement cost cannot trade away coverage of a ball that already exists.
The guaranteed corridor is the physical robot-plus-ball contact radius minus a
35 mm planning margin; the margin shrinks the corridor and never creates
fictitious physical reach.

The goalkeeper may move outside the nominal goal-mouth centre range to meet a
diagonal shot early, while its physical radius still covers the line. During a
shot emergency it favours a deeper guard plane; without an in-flight shot it
may step forward to reduce the angular opening. Lateral feed-forward is derived
from urgent arrival time rather than a fixed position gain.

When close enough to the ball, the goalkeeper is allowed to kick only while it
is goal-side and facing the ball, so a contact sends the ball away from its own
goal.

## Maximin clearance search

The ball winner never blindly kicks along its arrival heading. It first routes
around the ball to a striking pose on the own-goal side. Kick remains disabled
until that invariant is satisfied.

The clearance planner evaluates 21 rays spanning a broad downfield half-plane.
For each ray it:

- finds the first field-boundary intersection;
- samples six positions along the ball path;
- solves drag-aware ball arrival at every sample;
- compares arrival with both attackers' directed minimum travel time;
- measures interference with the two other enemy robots;
- rewards a fast safe field exit and downfield progress;
- gives a small preference to recoverable central outcomes only after safety.

The selected ray maximizes the worst interception margin rather than merely
pointing away from the nearest attacker. Every candidate has negative `x`, so
no active clearance can target the defended positive-`x` goal. A defensive
ball-out is legal and preferable to preserving possession under immediate goal
threat in this benchmark's terminal rules.

## Braking-distance pose control

For any tactical target, nominal translational speed follows

`v_request = sqrt(v_arrival^2 + 2*a*distance)`

up to the robot speed limit, plus bounded target feed-forward. Heading uses an
analogous angular braking request. Commands are finally rotated into each
robot's local frame, matching the public control model.

This produces rapid long-range movement without the slow response of a unit
position gain, while still decelerating near an interception or marking pose.

## Velocity-obstacle and boundary safety layer

A tactically correct target is not automatically a safe immediate velocity.
The execution layer creates 31 velocity candidates from:

- the nominal command;
- current velocity and a full stop;
- four speed fractions;
- seven angular offsets around the nominal direction.

Every candidate is projected over a 750 ms collision horizon against the
constant-velocity motion of all other robots. Predicted penetration of the hard
separation radius receives a dominating penalty; near misses receive a smooth,
time-weighted comfort penalty.

Field safety uses a control-barrier-like stopping-distance test on all four
boundaries. An outward velocity becomes prohibitively expensive before its
required braking distance plus margin exceeds available field space. The final
choice also considers tactical tracking error, acceleration discontinuity, and
nominal deviation.

This is a sampled dynamic-window/velocity-obstacle hybrid. It is deterministic,
has a small bounded cost, and handles the simulator's velocity-command dynamics
better than short-range position repulsion. It does not claim the completeness
of continuous ORCA or nonlinear MPC.

## Theory-to-implementation map

The design intentionally draws from several control and planning families:

- hybrid automata: explicit phase and emergency transitions;
- Bayesian-style intent reasoning: multiple weighted hypotheses rather than a
  single hard intent label;
- pursuit/evasion: time-to-intercept and adversarial arrival margins;
- assignment optimization: exhaustive two-role joint auction;
- robust optimization: worst-case plus aggregate threat residuals;
- model-predictive control: continuous replanning over finite future arrival;
- computational geometry: segment distance, lane intersection, guard planes;
- bang-bang/braking control: acceleration-limited arrival speed;
- velocity obstacles/dynamic window: sampled collision-safe velocity choice;
- control barrier functions: stopping-distance boundary protection;
- hysteresis control: role and non-emergency phase stability.

The held command is integrated by four physics steps between plans. This keeps
shot-reaction latency below 17 ms while preventing the robust search from
dominating CPU time during parallel benchmark episodes.

These ideas are used where their assumptions fit the tiny deterministic world.
Adding a named method without its needed state, horizon, or objective would not
make the opponent stronger.

## Rejected or deferred mechanisms

The following are plausible later upgrades, but are not silently claimed by
the current implementation:

- full nonlinear MPC over all three robots and collision constraints;
- Monte Carlo tree search over attacker/defender kick sequences;
- learned attacker-intent classification;
- online system identification of dynamics already known to the private policy;
- randomized mixed strategies against an exploitative trained attacker;
- a goalkeeper dive/contact trajectory optimizer;
- post-clearance possession and counterattack planning;
- offline self-play or population-based adversarial training.

They require a diverse attacker corpus, performance budgets, and separate
holdout seeds. Implementing them before those fixtures would mostly add
complexity and tune against one development controller.

## Failure modes explicitly removed

The current layers target concrete earlier defects:

- ball chase by all defenders -> joint primary/cover assignment;
- late reaction to diagonal shots -> drag-aware crossing and emergency phase;
- own goals from wrong-side contact -> goal-side pose and negative-`x` rays;
- role chatter -> joint-cost advantage plus hold time;
- marking a stale receiver pose -> lead-pass hypotheses and feed-forward;
- optimistic interception while moving away -> directed reachability;
- defender/GK coverage duplication -> GK-uncovered threat weighting;
- collisions from target crossing -> velocity-obstacle candidate search;
- wall impacts from high requested speed -> stopping-distance barrier;
- clearances directly to an attacker -> sampled maximin interception margin.

## Compact-wall and rebound upgrade

The corrected-goalkeeper controller search exposed two additional structural
weaknesses that were not represented by the earlier `0/24` corpus:

1. the secondary defender could follow a high moving receiver far enough to
   abandon the direct ball-to-goal corridor;
2. a goalkeeper save was treated as an ordinary loose ball on the next control
   tick, so the rebound response had no memory and frequently left one attacker
   unopposed.

The opponent now adds two bounded mechanisms:

- **early compact wall**: while the ball remains before `x=1.85`, the secondary
  defender occupies the alternate side of a goal-side guard plane instead of
  copying the receiver's high decoy motion. The primary still solves the direct
  interception, producing a staggered two-layer wall rather than duplicate
  ball chase;
- **latched rebound emergency**: a dangerous positive-to-negative ball-velocity
  reversal beyond `x=2.35` latches a 1.10-second emergency. The primary pursues
  the drag-aware interception while the secondary moves goal-side of the
  predicted rebound and nearest attacker as a backstop. This prevents the
  state machine from forgetting a save after one 60 Hz planning tick.

The backstop becomes a clearance intent when it is within 0.52 m of the
predicted ball. Both mechanisms retain the existing goal-side kick condition,
maximin negative-x clearance search, velocity-obstacle layer, and boundary
barrier. They do not raise robot dynamics above the same hidden limits applied
to every robot.

## Verification

Unit and integration coverage includes:

- drag integration and guard-plane crossing;
- directed reachability when moving/facing toward and away from a target;
- possession-belief sensitivity to distance, orientation, and closing speed;
- material-advantage role switching;
- immediate shot-emergency preemption;
- goal-side clearance and no own-goal clearance direction;
- braking-distance command strength;
- velocity-obstacle head-on collision rejection;
- boundary stopping-distance protection;
- diagonal goalkeeper tracking;
- restart exclusion, delayed observation, scoring, terminal trace, and
  deterministic replay.

After the complete minimax/safety upgrade, the prior best development controller
was run on seeds 1-24:

- controller successes: `0/24`;
- `start_timeout`: 19;
- defensive `ball_out`: 5;
- `episode_timeout`: 0.

The same 24 episodes were run four simulator containers at a time. After
decoupling planning from physics, 5-6 second simulated episodes again completed
in approximately 5-6 seconds of wall time under that concurrency. The simulator
test workload containing long deterministic advances dropped from 5.74 seconds
to 1.50 seconds in the same containerized debug-test setup.

This corpus is evidence against one known controller, not proof of global
optimality. The next meaningful strength increase should come from a diverse
attacker suite and holdout seeds, not from further tuning solely against this
controller.

After the compact-wall/rebound upgrade, the newer controller that had produced
one valid corrected-goalkeeper success was evaluated through the three-seed
gate on seeds `1,2,3`:

- accepted: `false`;
- controller successes: `0/3`;
- failures: three defensive `ball_out` terminals;
- infrastructure errors: `0`.

The content-bearing traces and gate summary are retained in the authoring temp
workspace. This is a regression check against a newly observed attack family,
not a claim that three development seeds constitute a sufficient hidden
benchmark.

## Required future evaluation

Defensive evaluation should retain at least these dimensions:

- valid-goal suppression across fixed development and unseen holdout seeds;
- start-touch denial without exclusion-rule violations;
- shot attempts, shot-on-target rate, and time from pass to interception;
- own-goal and unsafe-clearance count;
- ball-out, enemy possession, and episode-timeout decomposition;
- minimum robot separation and boundary contacts;
- role-switch frequency and duplicated-coverage duration;
- per-tick planning CPU time at p50, p95, and maximum;
- sensitivity to distinct attacking families, not parameter variants of one
  scripted play.

Only the first outcome decomposition is currently measured end-to-end. The
other metrics should be added to private authoring diagnostics before claiming
that one architecture is globally optimal.

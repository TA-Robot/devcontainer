use crate::math::Vec2;
use crate::protocol::{
    BallObservation, EpisodeResult, Observation, PublicSpec, RobotCommand, RobotObservation,
    ENEMY_IDS, FRIENDLY_IDS,
};
use std::collections::VecDeque;
use std::f64::consts::PI;

const BALL_START: (f64, f64) = (0.65, 2.80);
const FRIENDLY_STARTS: [(f64, f64, f64); 2] =
    [(0.20, 2.86, -1.10), (1.45, 0.55, 0.0)];
const ENEMY_STARTS: [(f64, f64, f64); 3] =
    [(1.10, 2.05, -1.10), (2.15, 0.75, PI), (4.08, 0.0, PI)];
const GOALKEEPER_COVERAGE_MARGIN_M: f64 = 0.035;
const FRIENDLY_MAX_VELOCITY_MULTIPLIER: f64 = 2.0;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Team {
    Friendly,
    Enemy,
}

fn maximum_velocity_for_team(enemy_maximum: f64, team: Team) -> f64 {
    match team {
        Team::Friendly => enemy_maximum * FRIENDLY_MAX_VELOCITY_MULTIPLIER,
        Team::Enemy => enemy_maximum,
    }
}

#[derive(Clone, Debug)]
struct Robot {
    id: &'static str,
    team: Team,
    position: Vec2,
    velocity: Vec2,
    heading: f64,
    angular_velocity: f64,
    command: RobotCommand,
    previous_kick: bool,
    kicker_contact: bool,
}

#[derive(Clone, Copy, Debug)]
struct Ball {
    position: Vec2,
    velocity: Vec2,
}

#[derive(Clone, Copy, Debug)]
struct OpponentIntent {
    position: Vec2,
    face: Vec2,
    feedforward_velocity: Vec2,
    speed_limit: f64,
    kick: bool,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum DefensivePhase {
    Restart,
    ShotEmergency,
    ReboundEmergency,
    FriendlyControl,
    LooseBall,
    Clearance,
}

#[derive(Clone, Copy, Debug)]
struct ThreatHypothesis {
    origin: Vec2,
    destination: Vec2,
    eta_s: f64,
    weight: f64,
}

#[derive(Clone, Copy, Debug)]
struct HiddenDynamics {
    robot_velocity_response: f64,
    robot_angular_response: f64,
    robot_max_acceleration: f64,
    robot_max_angular_acceleration: f64,
    robot_max_velocity: f64,
    robot_max_angular_velocity: f64,
    lateral_slip: f64,
    robot_restitution: f64,
    ball_restitution: f64,
    ball_linear_drag: f64,
    kick_speed: f64,
    observation_jitter_s: f64,
}

impl HiddenDynamics {
    fn from_rng(rng: &mut Rng64) -> Self {
        Self {
            robot_velocity_response: rng.range(4.7, 5.6),
            robot_angular_response: rng.range(6.0, 7.5),
            robot_max_acceleration: rng.range(2.5, 3.1),
            robot_max_angular_acceleration: rng.range(10.0, 13.0),
            robot_max_velocity: rng.range(1.65, 1.9),
            robot_max_angular_velocity: rng.range(5.2, 6.2),
            lateral_slip: rng.range(0.82, 0.94),
            robot_restitution: rng.range(0.08, 0.16),
            ball_restitution: rng.range(0.52, 0.66),
            ball_linear_drag: rng.range(0.42, 0.56),
            kick_speed: rng.range(4.8, 5.6),
            observation_jitter_s: 0.045,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Terminal {
    Running,
    Success(&'static str),
    Failure(&'static str),
}

#[derive(Clone, Debug)]
struct DelayedObservation {
    release_at: f64,
    observation: Observation,
}

#[derive(Clone, Debug)]
struct Rng64 {
    state: u64,
}

impl Rng64 {
    fn new(seed: u64) -> Self {
        Self {
            state: seed.max(1) ^ 0x9e37_79b9_7f4a_7c15,
        }
    }

    fn next_u64(&mut self) -> u64 {
        let mut value = self.state;
        value ^= value << 13;
        value ^= value >> 7;
        value ^= value << 17;
        self.state = value;
        value
    }

    fn unit(&mut self) -> f64 {
        (self.next_u64() >> 11) as f64 / ((1_u64 << 53) as f64)
    }

    fn range(&mut self, minimum: f64, maximum: f64) -> f64 {
        minimum + (maximum - minimum) * self.unit()
    }
}

pub struct Simulator {
    public: PublicSpec,
    hidden: HiddenDynamics,
    robots: Vec<Robot>,
    ball: Ball,
    elapsed_s: f64,
    play_started: bool,
    first_friendly_contact: Option<usize>,
    pass_received: bool,
    shot_after_pass: bool,
    terminal: Terminal,
    observation_accumulator: f64,
    observation_sequence: u64,
    delayed_observations: VecDeque<DelayedObservation>,
    latest_released: Option<Observation>,
    primary_defender: usize,
    last_role_switch_s: f64,
    defensive_phase: DefensivePhase,
    last_phase_switch_s: f64,
    rebound_emergency_until_s: f64,
    previous_ball_velocity: Vec2,
    next_opponent_control_s: f64,
    rng: Rng64,
}

impl Simulator {
    pub fn new(seed: u64) -> Self {
        let public = PublicSpec::default();
        let mut rng = Rng64::new(seed);
        let hidden = HiddenDynamics::from_rng(&mut rng);
        let ball = Ball {
            position: Vec2::new(BALL_START.0, BALL_START.1),
            velocity: Vec2::ZERO,
        };
        let robots = vec![
            Robot::new(
                FRIENDLY_IDS[0],
                Team::Friendly,
                FRIENDLY_STARTS[0].0,
                FRIENDLY_STARTS[0].1,
                FRIENDLY_STARTS[0].2,
            ),
            Robot::new(
                FRIENDLY_IDS[1],
                Team::Friendly,
                FRIENDLY_STARTS[1].0,
                FRIENDLY_STARTS[1].1,
                FRIENDLY_STARTS[1].2,
            ),
            Robot::new(
                ENEMY_IDS[0],
                Team::Enemy,
                ENEMY_STARTS[0].0,
                ENEMY_STARTS[0].1,
                ENEMY_STARTS[0].2,
            ),
            Robot::new(
                ENEMY_IDS[1],
                Team::Enemy,
                ENEMY_STARTS[1].0,
                ENEMY_STARTS[1].1,
                ENEMY_STARTS[1].2,
            ),
            Robot::new(
                ENEMY_IDS[2],
                Team::Enemy,
                ENEMY_STARTS[2].0,
                ENEMY_STARTS[2].1,
                ENEMY_STARTS[2].2,
            ),
        ];
        Self {
            public,
            hidden,
            robots,
            ball,
            elapsed_s: 0.0,
            play_started: false,
            first_friendly_contact: None,
            pass_received: false,
            shot_after_pass: false,
            terminal: Terminal::Running,
            observation_accumulator: 0.0,
            observation_sequence: 0,
            delayed_observations: VecDeque::new(),
            latest_released: None,
            primary_defender: FRIENDLY_IDS.len(),
            last_role_switch_s: 0.0,
            defensive_phase: DefensivePhase::Restart,
            last_phase_switch_s: 0.0,
            rebound_emergency_until_s: 0.0,
            previous_ball_velocity: Vec2::ZERO,
            next_opponent_control_s: 0.0,
            rng,
        }
    }

    pub fn set_friendly_commands(
        &mut self,
        updates: &[(usize, RobotCommand)],
    ) -> Result<(), &'static str> {
        if self.terminal != Terminal::Running {
            return Err("episode_not_running");
        }
        for (index, command) in updates {
            if *index >= FRIENDLY_IDS.len()
                || !command.local_velocity.is_finite()
                || !command.angular_velocity.is_finite()
            {
                return Err("invalid_command");
            }
        }
        for (index, command) in updates {
            self.robots[*index].command = *command;
        }
        Ok(())
    }

    pub fn advance(&mut self, dt: f64) {
        if self.terminal != Terminal::Running || !dt.is_finite() || dt <= 0.0 {
            self.release_observations();
            return;
        }
        self.elapsed_s += dt;
        if self.elapsed_s + 1e-9 >= self.next_opponent_control_s {
            self.update_enemy_commands();
            self.next_opponent_control_s = self.elapsed_s + 1.0 / 60.0;
        }
        self.integrate_robots(dt);
        self.resolve_robot_collisions();
        self.enforce_prestart_enemy_exclusion();
        self.resolve_robot_ball_contacts();
        self.integrate_ball(dt);
        self.check_rules();
        self.sample_observations(dt);
        self.release_observations();
    }

    pub fn latest_observation(&self) -> Option<Observation> {
        self.latest_released.clone()
    }

    pub fn terminal_snapshot(&self) -> Option<Observation> {
        if self.terminal == Terminal::Running {
            return None;
        }
        Some(self.make_observation(self.observation_sequence.max(1)))
    }

    pub fn result(&self) -> EpisodeResult {
        let elapsed_ms = (self.elapsed_s * 1000.0).round().max(0.0) as u64;
        match self.terminal {
            Terminal::Running => EpisodeResult {
                status: "running",
                reason: None,
                elapsed_ms,
            },
            Terminal::Success(reason) => EpisodeResult {
                status: "success",
                reason: Some(reason),
                elapsed_ms,
            },
            Terminal::Failure(reason) => EpisodeResult {
                status: "failure",
                reason: Some(reason),
                elapsed_ms,
            },
        }
    }

    pub fn is_running(&self) -> bool {
        self.terminal == Terminal::Running
    }

    fn predict_ball_position(&self, time_s: f64) -> Vec2 {
        let drag = self.hidden.ball_linear_drag;
        if drag <= 1e-9 {
            return self.ball.position + self.ball.velocity * time_s;
        }
        let travel = (1.0 - (-drag * time_s).exp()) / drag;
        self.ball.position + self.ball.velocity * travel
    }

    fn directed_reachable_distance(
        &self,
        robot_index: usize,
        target: Vec2,
        time_s: f64,
    ) -> f64 {
        let robot = &self.robots[robot_index];
        let direction = (target - robot.position).normalized_or(Vec2::ZERO);
        let target_heading = direction.y.atan2(direction.x);
        let heading_error = wrap_angle(target_heading - robot.heading).abs();
        let turning_delay = (heading_error / self.hidden.robot_max_angular_velocity * 0.38)
            .min(time_s);
        let mut remaining = time_s - turning_delay;
        let mut projected_speed = robot.velocity.dot(direction);
        let mut displacement = 0.0;
        while remaining > 1e-9 {
            let dt = remaining.min(0.025);
            projected_speed = (projected_speed + self.hidden.robot_max_acceleration * dt)
                .min(self.hidden.robot_max_velocity);
            displacement += projected_speed * dt;
            remaining -= dt;
        }
        displacement.max(0.0)
    }

    fn minimum_travel_time(&self, robot_index: usize, target: Vec2) -> f64 {
        let distance = (target - self.robots[robot_index].position).length();
        for sample in 0..=100 {
            let time_s = sample as f64 * 0.025;
            if self.directed_reachable_distance(robot_index, target, time_s) >= distance {
                return time_s;
            }
        }
        2.5 + distance / self.hidden.robot_max_velocity
    }

    fn update_defensive_phase(&mut self) {
        let friendly_control = (0..FRIENDLY_IDS.len())
            .map(|index| self.attacker_control_likelihood(index))
            .fold(0.0_f64, f64::max);
        let enemy_distance = self.robots[FRIENDLY_IDS.len()..]
            .iter()
            .map(|robot| (robot.position - self.ball.position).length())
            .fold(f64::INFINITY, f64::min);
        let velocity_jump = (self.ball.velocity - self.previous_ball_velocity).length();
        let dangerous_reversal = self.play_started
            && self.ball.position.x > 2.35
            && self.previous_ball_velocity.x > 0.55
            && self.ball.velocity.x < -0.45
            && velocity_jump > 1.4;
        if dangerous_reversal {
            self.rebound_emergency_until_s = self.elapsed_s + 1.10;
        }
        let requested = if !self.play_started {
            DefensivePhase::Restart
        } else if self.elapsed_s < self.rebound_emergency_until_s {
            DefensivePhase::ReboundEmergency
        } else if self.ball.velocity.x > 0.75
            && (self.ball.position.x > 1.2 || velocity_jump > 1.2)
        {
            DefensivePhase::ShotEmergency
        } else if enemy_distance < 0.22 && self.ball.velocity.x <= 0.75 {
            DefensivePhase::Clearance
        } else if friendly_control > 0.42 {
            DefensivePhase::FriendlyControl
        } else {
            DefensivePhase::LooseBall
        };
        let urgent = matches!(
            requested,
            DefensivePhase::ShotEmergency | DefensivePhase::ReboundEmergency
        );
        if requested != self.defensive_phase
            && (urgent || self.elapsed_s - self.last_phase_switch_s >= 0.10)
        {
            self.defensive_phase = requested;
            self.last_phase_switch_s = self.elapsed_s;
        }
        self.previous_ball_velocity = self.ball.velocity;
    }

    fn attacker_control_likelihood(&self, robot_index: usize) -> f64 {
        let robot = &self.robots[robot_index];
        let to_ball = self.ball.position - robot.position;
        let distance = to_ball.length();
        let forward = Vec2::new(robot.heading.cos(), robot.heading.sin());
        let orientation = ((forward.dot(to_ball.normalized_or(forward)) + 1.0) * 0.5)
            .clamp(0.0, 1.0);
        let closing_velocity = (robot.velocity - self.ball.velocity)
            .dot(to_ball.normalized_or(Vec2::ZERO));
        let distance_term = 1.0 / (1.0 + ((distance - 0.34) * 7.5).exp());
        let speed_term = (0.55 + closing_velocity * 0.20).clamp(0.18, 0.90);
        (distance_term * (0.35 + orientation * 0.65) * speed_term * 1.8).clamp(0.0, 1.0)
    }

    fn threat_hypotheses(&self) -> Vec<ThreatHypothesis> {
        let goal_x = self.public.field.length_m / 2.0;
        let goal_half = self.public.field.attacking_goal_width_m / 2.0 - 0.06;
        let mut threats = Vec::with_capacity(24);
        if let Some((time_s, crossing_y)) = self.ball_crossing_at_x(goal_x) {
            threats.push(ThreatHypothesis {
                origin: self.ball.position,
                destination: Vec2::new(goal_x, crossing_y),
                eta_s: time_s,
                // An observed in-flight ball is evidence, while the remaining
                // hypotheses are counterfactual options.  Emergency defence
                // must not average a real shot away with imagined future shots.
                weight: if crossing_y.abs() <= goal_half + 0.55 {
                    42.0
                } else {
                    10.0
                },
            });
        }
        let ball_distance = (Vec2::new(goal_x, 0.0) - self.ball.position).length();
        for goal_y in [-goal_half, 0.0, goal_half] {
            threats.push(ThreatHypothesis {
                origin: self.ball.position,
                destination: Vec2::new(goal_x, goal_y),
                eta_s: ball_distance / self.hidden.kick_speed + 0.18,
                weight: if goal_y == 0.0 { 2.8 } else { 2.4 },
            });
        }
        for attacker_index in 0..FRIENDLY_IDS.len() {
            let attacker = &self.robots[attacker_index];
            let control = self.attacker_control_likelihood(attacker_index);
            let control_eta = self.minimum_travel_time(attacker_index, self.ball.position);
            let predicted_origin = attacker.position + attacker.velocity * 0.24;
            let shot_distance = (Vec2::new(goal_x, 0.0) - predicted_origin).length();
            for goal_y in [-goal_half, 0.0, goal_half] {
                threats.push(ThreatHypothesis {
                    origin: predicted_origin,
                    destination: Vec2::new(goal_x, goal_y),
                    eta_s: control_eta + shot_distance / self.hidden.kick_speed + 0.10,
                    weight: 0.8 + control * if goal_y == 0.0 { 4.2 } else { 3.5 },
                });
            }
            let other_index = 1 - attacker_index;
            let other = &self.robots[other_index];
            for lead_s in [0.10, 0.32, 0.56] {
                let destination = other.position + other.velocity * lead_s;
                threats.push(ThreatHypothesis {
                    origin: self.ball.position,
                    destination,
                    eta_s: control_eta
                        + (destination - self.ball.position).length() / self.hidden.kick_speed,
                    weight: 1.2 + control * 3.0 + if other_index == 1 { 0.7 } else { 0.0 },
                });
            }
        }
        threats
    }

    fn goalkeeper_uncovered_fraction(&self, threat: ThreatHypothesis) -> f64 {
        let goalkeeper_index = FRIENDLY_IDS.len() + ENEMY_IDS.len() - 1;
        let guard_x = 4.02;
        let Some(crossing_y) = Self::threat_y_at_x(threat, guard_x) else {
            return 1.0;
        };
        let span = (threat.destination.x - threat.origin.x).abs().max(0.1);
        let fraction = ((guard_x - threat.origin.x).abs() / span).clamp(0.0, 1.0);
        let arrival = threat.eta_s * fraction;
        let goalkeeper = &self.robots[goalkeeper_index];
        let crossing = Vec2::new(guard_x, crossing_y);
        let reachable = self.directed_reachable_distance(goalkeeper_index, crossing, arrival)
            + self.public.robot.radius_m
            + self.public.ball_radius_m;
        let residual = ((crossing_y - goalkeeper.position.y).abs() - reachable).max(0.0);
        (0.12 + residual / 0.75).clamp(0.12, 1.0)
    }

    fn distance_to_segment(point: Vec2, start: Vec2, end: Vec2) -> f64 {
        let segment = end - start;
        let length_squared = segment.length_squared();
        if length_squared <= 1e-12 {
            return (point - start).length();
        }
        let fraction = ((point - start).dot(segment) / length_squared).clamp(0.0, 1.0);
        (point - (start + segment * fraction)).length()
    }

    fn threat_y_at_x(threat: ThreatHypothesis, x: f64) -> Option<f64> {
        let span = threat.destination.x - threat.origin.x;
        if span.abs() <= 1e-9 {
            return None;
        }
        let fraction = (x - threat.origin.x) / span;
        if !(0.0..=1.0).contains(&fraction) {
            return None;
        }
        Some(threat.origin.y + (threat.destination.y - threat.origin.y) * fraction)
    }

    fn interception_solution(&self, robot_index: usize) -> (f64, Vec2) {
        let robot_position = self.robots[robot_index].position;
        for sample in 1..=40 {
            let time_s = sample as f64 * 0.05;
            let ball = self.predict_ball_position(time_s);
            let reach = self.directed_reachable_distance(robot_index, ball, time_s)
                + self.public.robot.radius_m
                + self.public.ball_radius_m;
            if (ball - robot_position).length() <= reach {
                return (time_s, ball);
            }
        }
        (2.0, self.predict_ball_position(2.0))
    }

    fn optimized_cover_position(
        &self,
        robot_index: usize,
        primary_target: Vec2,
        threats: &[ThreatHypothesis],
    ) -> Vec2 {
        let receiver = &self.robots[1];
        let mut candidates = Vec::with_capacity(threats.len() * 3 + 4);
        for threat in threats {
            for fraction in [0.38, 0.55, 0.70] {
                candidates.push(
                    threat.origin + (threat.destination - threat.origin) * fraction,
                );
            }
        }
        for fraction in [0.38, 0.52, 0.66, 0.78] {
            candidates.push(
                self.ball.position
                    + (receiver.position - self.ball.position) * fraction,
            );
        }
        let half_length = self.public.field.length_m / 2.0 - 0.15;
        let half_width = self.public.field.width_m / 2.0 - 0.15;
        let mut best = receiver.position;
        let mut best_score = f64::INFINITY;
        for mut candidate in candidates {
            candidate.x = candidate.x.clamp(-half_length, half_length);
            candidate.y = candidate.y.clamp(-half_width, half_width);
            let travel = self.minimum_travel_time(robot_index, candidate);
            let mut worst_residual: f64 = 0.0;
            let mut aggregate = 0.0;
            for threat in threats {
                let distance = Self::distance_to_segment(
                    candidate,
                    threat.origin,
                    threat.destination,
                );
                let urgency = threat.weight / (0.20 + threat.eta_s);
                let goalkeeper_gap = self.goalkeeper_uncovered_fraction(*threat);
                let residual = urgency * distance.min(1.2) * goalkeeper_gap;
                worst_residual = worst_residual.max(residual);
                aggregate += residual;
            }
            let separation = (candidate - primary_target).length();
            let separation_penalty = if separation < 0.48 {
                (0.48 - separation) * 8.0
            } else {
                0.0
            };
            let receiver_goal_side = if candidate.x >= receiver.position.x {
                0.0
            } else {
                (receiver.position.x - candidate.x) * 0.45
            };
            let score = worst_residual
                + aggregate * 0.08
                + travel * 0.55
                + separation_penalty
                + receiver_goal_side;
            if score < best_score {
                best_score = score;
                best = candidate;
            }
        }
        best
    }

    fn update_defender_assignment(&mut self) {
        if !self.play_started {
            return;
        }
        let first = FRIENDLY_IDS.len();
        let candidates = [first, first + 1];
        let current = self.primary_defender;
        let challenger = if current == candidates[0] {
            candidates[1]
        } else {
            candidates[0]
        };
        let threats = self.threat_hypotheses();
        let (current_intercept, current_target) = self.interception_solution(current);
        let current_cover = self.optimized_cover_position(challenger, current_target, &threats);
        let current_cost = current_intercept
            + self.minimum_travel_time(challenger, current_cover) * 0.42;
        let (challenger_intercept, challenger_target) =
            self.interception_solution(challenger);
        let challenger_cover =
            self.optimized_cover_position(current, challenger_target, &threats);
        let challenger_cost = challenger_intercept
            + self.minimum_travel_time(current, challenger_cover) * 0.42;
        if self.elapsed_s - self.last_role_switch_s >= 0.30
            && challenger_cost + 0.12 < current_cost
        {
            self.primary_defender = challenger;
            self.last_role_switch_s = self.elapsed_s;
        }
    }

    fn project_outside_exclusion(&self, target: Vec2, fallback: Vec2) -> Vec2 {
        let minimum = self.public.prestart_enemy_exclusion_radius_m + 0.08;
        let delta = target - self.ball.position;
        if delta.length() >= minimum {
            target
        } else {
            self.ball.position + delta.normalized_or(fallback) * minimum
        }
    }

    fn optimized_clearance_direction(&self, robot_index: usize, origin: Vec2) -> Vec2 {
        let half_length = self.public.field.length_m / 2.0 - self.public.ball_radius_m;
        let half_width = self.public.field.width_m / 2.0 - self.public.ball_radius_m;
        let mut best = Vec2::new(-1.0, 0.0);
        let mut best_score = f64::NEG_INFINITY;
        for step in -10..=10 {
            let angle = PI + step as f64 * 0.115;
            let direction = Vec2::new(angle.cos(), angle.sin());
            let x_distance = if direction.x > 1e-9 {
                (half_length - origin.x) / direction.x
            } else if direction.x < -1e-9 {
                (-half_length - origin.x) / direction.x
            } else {
                f64::INFINITY
            };
            let y_distance = if direction.y > 1e-9 {
                (half_width - origin.y) / direction.y
            } else if direction.y < -1e-9 {
                (-half_width - origin.y) / direction.y
            } else {
                f64::INFINITY
            };
            let exit_distance = x_distance.min(y_distance).max(0.0);
            let landing = origin + direction * exit_distance.min(5.5);
            let mut adversarial_margin = f64::INFINITY;
            for fraction in [0.18, 0.32, 0.48, 0.64, 0.80, 0.94] {
                let along = exit_distance * fraction;
                let ratio = along * self.hidden.ball_linear_drag / self.hidden.kick_speed;
                let ball_time = if ratio < 0.995 {
                    -(1.0 - ratio).ln() / self.hidden.ball_linear_drag
                } else {
                    9.0
                };
                let sample = origin + direction * along;
                for friendly_index in 0..FRIENDLY_IDS.len() {
                    let interception_margin = self.minimum_travel_time(friendly_index, sample)
                        - ball_time;
                    adversarial_margin = adversarial_margin.min(interception_margin);
                }
            }
            let mut teammate_margin = f64::INFINITY;
            for (index, teammate) in self.robots.iter().enumerate().skip(FRIENDLY_IDS.len()) {
                if index == robot_index {
                    continue;
                }
                teammate_margin = teammate_margin.min(Self::distance_to_segment(
                    teammate.position,
                    origin,
                    landing,
                ));
            }
            let centre_value = 1.0 - (landing.y.abs() / half_width).min(1.0);
            let exit_value = 1.0 / (0.30 + exit_distance);
            let downfield_progress = (origin.x - landing.x).max(0.0);
            let score = exit_value * 5.0
                + adversarial_margin.clamp(-2.0, 2.0) * 4.5
                + teammate_margin.min(1.0) * 0.6
                + downfield_progress.min(4.0) * 0.35
                + centre_value * 0.15;
            if score > best_score {
                best_score = score;
                best = direction;
            }
        }
        best
    }

    fn clearance_intent(&self, robot_index: usize) -> OpponentIntent {
        let (intercept_time, intercept_ball) = self.interception_solution(robot_index);
        let robot = &self.robots[robot_index];
        let clearance = self.optimized_clearance_direction(robot_index, intercept_ball);
        let striking_pose = intercept_ball - clearance * 0.14;
        let relative = robot.position - intercept_ball;
        let side = if relative.y >= 0.0 { 1.0 } else { -1.0 };
        let target = if relative.x < 0.10 && relative.y.abs() < 0.24 {
            Vec2::new(robot.position.x, intercept_ball.y + side * 0.34)
        } else if relative.x < 0.10 {
            intercept_ball + Vec2::new(0.20, side * 0.30)
        } else {
            striking_pose
        };
        let can_clear = robot.position.x > self.ball.position.x + 0.05;
        OpponentIntent {
            position: target,
            face: intercept_ball,
            feedforward_velocity: self.ball.velocity * (0.35 + intercept_time.min(0.5)),
            speed_limit: self.hidden.robot_max_velocity,
            kick: can_clear,
        }
    }

    fn cover_intent(&self, robot_index: usize) -> OpponentIntent {
        let robot = &self.robots[robot_index];
        let receiver = &self.robots[1];
        if (self.ball.position - robot.position).length() < 0.72
            || (self.ball.position.x > 2.2 && self.ball.velocity.x > 0.2)
        {
            return self.clearance_intent(robot_index);
        }
        let threats = self.threat_hypotheses();
        let primary_target = self.interception_solution(self.primary_defender).1;
        let target = self.optimized_cover_position(robot_index, primary_target, &threats);
        OpponentIntent {
            position: target,
            face: self.ball.position,
            feedforward_velocity: receiver.velocity * 0.45,
            speed_limit: self.hidden.robot_max_velocity * 0.92,
            kick: robot.position.x > self.ball.position.x + 0.05,
        }
    }

    fn compact_wall_intent(&self, robot_index: usize) -> OpponentIntent {
        let goal = Vec2::new(self.public.field.length_m / 2.0, 0.0);
        let predicted_ball = self.predict_ball_position(0.16);
        let guard_x = (predicted_ball.x + 0.62).clamp(1.08, 2.45);
        let goal_span = (goal.x - predicted_ball.x).max(0.20);
        let fraction = ((guard_x - predicted_ball.x) / goal_span).clamp(0.0, 1.0);
        let centre_line_y = predicted_ball.y + (goal.y - predicted_ball.y) * fraction;
        let primary = &self.robots[self.primary_defender];
        let primary_side = (primary.position.y - centre_line_y).signum();
        let alternate_side = if primary_side.abs() < 0.5 {
            if robot_index % 2 == 0 { -1.0 } else { 1.0 }
        } else {
            -primary_side
        };
        let target = Vec2::new(guard_x, centre_line_y + alternate_side * 0.18);
        OpponentIntent {
            position: target,
            face: predicted_ball,
            feedforward_velocity: self.ball.velocity * 0.18,
            speed_limit: self.hidden.robot_max_velocity,
            kick: self.robots[robot_index].position.x > self.ball.position.x + 0.04,
        }
    }

    fn rebound_backstop_intent(&self, robot_index: usize) -> OpponentIntent {
        let predicted_ball = self.predict_ball_position(0.20);
        if (predicted_ball - self.robots[robot_index].position).length() < 0.52 {
            return self.clearance_intent(robot_index);
        }
        let goal = Vec2::new(self.public.field.length_m / 2.0, 0.0);
        let goal_side = (goal - predicted_ball).normalized_or(Vec2::new(1.0, 0.0));
        let nearest_attacker = (0..FRIENDLY_IDS.len())
            .min_by(|left, right| {
                let left_distance =
                    (self.robots[*left].position - predicted_ball).length_squared();
                let right_distance =
                    (self.robots[*right].position - predicted_ball).length_squared();
                left_distance.total_cmp(&right_distance)
            })
            .unwrap_or(0);
        let attacker = &self.robots[nearest_attacker];
        let attacker_lead = attacker.position + attacker.velocity * 0.22;
        let shot_side = (attacker_lead.y - predicted_ball.y).signum();
        let lateral = Vec2::new(-goal_side.y, goal_side.x)
            * if shot_side.abs() < 0.5 { 0.0 } else { shot_side * 0.10 };
        let target = predicted_ball + goal_side * 0.34 + lateral;
        OpponentIntent {
            position: target,
            face: predicted_ball,
            feedforward_velocity: self.ball.velocity * 0.42,
            speed_limit: self.hidden.robot_max_velocity,
            kick: self.robots[robot_index].position.x > self.ball.position.x + 0.04,
        }
    }

    fn ball_crossing_at_x(&self, target_x: f64) -> Option<(f64, f64)> {
        if self.ball.velocity.x <= 0.05 || target_x <= self.ball.position.x {
            return None;
        }
        let drag = self.hidden.ball_linear_drag;
        let ratio = (target_x - self.ball.position.x) * drag / self.ball.velocity.x;
        if ratio >= 1.0 {
            return None;
        }
        let time_s = -(1.0 - ratio).ln() / drag;
        let position = self.predict_ball_position(time_s);
        Some((time_s, position.y))
    }

    fn goalkeeper_intent(&self, robot_index: usize) -> OpponentIntent {
        let robot = &self.robots[robot_index];
        let intercept_limit = self.public.field.attacking_goal_width_m / 2.0 + 0.62;
        let threats = self.threat_hypotheses();
        let mut y_candidates = Vec::with_capacity(20);
        for step in -6..=6 {
            y_candidates.push(step as f64 * intercept_limit / 6.0);
        }
        for threat in &threats {
            for x in [3.68, 3.84, 4.02] {
                if let Some(y) = Self::threat_y_at_x(*threat, x) {
                    y_candidates.push(y.clamp(-intercept_limit, intercept_limit));
                }
            }
        }
        let mut best_position = Vec2::new(4.02, 0.0);
        let mut best_score = f64::INFINITY;
        let mut best_emergency_violation = f64::INFINITY;
        // A planning margin must shrink the guaranteed contact corridor.  Adding
        // it to the physical radii creates a fictitious annulus where the planner
        // reports a save even though collision detection cannot touch the ball.
        let physical_coverage = self.public.robot.radius_m + self.public.ball_radius_m;
        let coverage = (physical_coverage - GOALKEEPER_COVERAGE_MARGIN_M).max(0.0);
        for x in [3.68, 3.84, 4.02] {
            for y in &y_candidates {
                let candidate = Vec2::new(x, *y);
                let reach_time = self.minimum_travel_time(robot_index, candidate);
                let mut worst: f64 = 0.0;
                let mut aggregate = 0.0;
                for threat in &threats {
                    let Some(crossing_y) = Self::threat_y_at_x(*threat, x) else {
                        continue;
                    };
                    let span = (threat.destination.x - threat.origin.x).abs().max(0.1);
                    let fraction = ((x - threat.origin.x).abs() / span).clamp(0.0, 1.0);
                    let arrival = (threat.eta_s * fraction).max(0.04);
                    let lateral_gap = (crossing_y - y).abs() - coverage;
                    let lateness = (reach_time - arrival).max(0.0)
                        * self.hidden.robot_max_velocity;
                    let residual = threat.weight * (lateral_gap.max(0.0) + lateness)
                        / (0.15 + arrival);
                    worst = worst.max(residual);
                    aggregate += residual;
                }
                let movement_cost = reach_time * 0.30;
                let depth_cost = if self.defensive_phase == DefensivePhase::ShotEmergency {
                    (4.02 - x).abs() * 0.25
                } else {
                    (x - 3.78).abs() * 0.18
                };
                let score = worst + aggregate * 0.07 + movement_cost + depth_cost;
                let emergency_violation = if self.defensive_phase
                    == DefensivePhase::ShotEmergency
                {
                    if let Some((arrival, crossing_y)) = self.ball_crossing_at_x(x) {
                        let uncovered = ((crossing_y - y).abs() - coverage).max(0.0);
                        let late_distance = (reach_time - arrival).max(0.0)
                            * self.hidden.robot_max_velocity;
                        uncovered + late_distance
                    } else {
                        0.0
                    }
                } else {
                    0.0
                };
                let emergency_better = emergency_violation + 1e-9
                    < best_emergency_violation;
                let emergency_equal = (emergency_violation
                    - best_emergency_violation)
                    .abs()
                    <= 1e-9;
                if emergency_better || (emergency_equal && score < best_score) {
                    best_emergency_violation = emergency_violation;
                    best_score = score;
                    best_position = candidate;
                }
            }
        }
        let urgent_eta = threats
            .iter()
            .map(|threat| threat.eta_s)
            .fold(f64::INFINITY, f64::min);
        let feedforward_y = ((best_position.y - robot.position.y) / urgent_eta.max(0.10))
            .clamp(-self.hidden.robot_max_velocity, self.hidden.robot_max_velocity);
        OpponentIntent {
            position: best_position,
            face: self.ball.position,
            feedforward_velocity: Vec2::new(0.0, feedforward_y),
            speed_limit: self.hidden.robot_max_velocity,
            kick: robot.position.x > self.ball.position.x + 0.04,
        }
    }

    fn prestart_intents(&self) -> [OpponentIntent; 3] {
        let receiver = &self.robots[1];
        let goal = Vec2::new(self.public.field.length_m / 2.0, 0.0);
        let lane_direction = (receiver.position - self.ball.position)
            .normalized_or(Vec2::new(0.0, -1.0));
        let block = self.ball.position
            + lane_direction * (self.public.prestart_enemy_exclusion_radius_m + 0.08);
        let goal_side = (goal - receiver.position).normalized_or(Vec2::new(1.0, 0.0));
        let mark = self.project_outside_exclusion(
            receiver.position + goal_side * 0.40,
            Vec2::new(1.0, 0.0),
        );
        let goalkeeper = self.goalkeeper_intent(FRIENDLY_IDS.len() + 2);
        [
            OpponentIntent {
                position: block,
                face: self.ball.position,
                feedforward_velocity: receiver.velocity * 0.35,
                speed_limit: self.hidden.robot_max_velocity * 0.82,
                kick: false,
            },
            OpponentIntent {
                position: mark,
                face: self.ball.position,
                feedforward_velocity: receiver.velocity * 0.45,
                speed_limit: self.hidden.robot_max_velocity * 0.88,
                kick: false,
            },
            OpponentIntent {
                kick: false,
                ..goalkeeper
            },
        ]
    }

    fn opponent_motion_command(&self, robot_index: usize, intent: OpponentIntent) -> RobotCommand {
        let robot = &self.robots[robot_index];
        let half_length = self.public.field.length_m / 2.0 - self.public.robot.radius_m;
        let half_width = self.public.field.width_m / 2.0 - self.public.robot.radius_m;
        let bounded_target = Vec2::new(
            intent.position.x.clamp(-half_length, half_length),
            intent.position.y.clamp(-half_width, half_width),
        );
        let delta = bounded_target - robot.position;
        let distance = delta.length();
        let direction = delta.normalized_or(Vec2::ZERO);
        let arrival_speed = intent.feedforward_velocity.dot(direction).max(0.0);
        let braking_speed = (arrival_speed * arrival_speed
            + 2.0 * self.hidden.robot_max_acceleration * distance)
            .sqrt();
        let nominal_velocity = direction * braking_speed.min(intent.speed_limit)
            + intent.feedforward_velocity * 0.35;
        let desired_global = self.select_safe_opponent_velocity(
            robot_index,
            nominal_velocity.clamp_length(intent.speed_limit),
            bounded_target,
            intent.speed_limit,
        );
        let face_delta = intent.face - robot.position;
        let heading_target = face_delta.y.atan2(face_delta.x);
        let heading_error = wrap_angle(heading_target - robot.heading);
        let desired_angular = heading_error.signum()
            * (2.0 * self.hidden.robot_max_angular_acceleration * heading_error.abs())
                .sqrt()
                .min(self.hidden.robot_max_angular_velocity);
        RobotCommand {
            local_velocity: desired_global.rotate(-robot.heading),
            angular_velocity: desired_angular,
            kick: self.play_started && intent.kick,
        }
    }

    fn select_safe_opponent_velocity(
        &self,
        robot_index: usize,
        nominal: Vec2,
        target: Vec2,
        speed_limit: f64,
    ) -> Vec2 {
        let robot = &self.robots[robot_index];
        let mut candidates = Vec::with_capacity(48);
        candidates.push(nominal);
        candidates.push(robot.velocity.clamp_length(speed_limit));
        candidates.push(Vec2::ZERO);
        let base_angle = nominal.y.atan2(nominal.x);
        for speed_fraction in [1.0, 0.78, 0.55, 0.32] {
            for angle_offset in [0.0, -0.24, 0.24, -0.52, 0.52, -0.90, 0.90] {
                let angle = base_angle + angle_offset;
                candidates.push(
                    Vec2::new(angle.cos(), angle.sin()) * speed_limit * speed_fraction,
                );
            }
        }

        let mut best = Vec2::ZERO;
        let mut best_score = f64::INFINITY;
        for candidate in candidates {
            let candidate = candidate.clamp_length(speed_limit);
            let mut score = (candidate - nominal).length_squared() * 1.15;
            let projected = robot.position + candidate * 0.42;
            score += (projected - target).length_squared() * 0.24;
            score += (candidate - robot.velocity).length_squared() * 0.08;
            score += self.velocity_obstacle_penalty(robot_index, candidate);
            score += self.boundary_braking_penalty(robot_index, candidate);
            if score < best_score {
                best_score = score;
                best = candidate;
            }
        }
        best
    }

    fn velocity_obstacle_penalty(&self, robot_index: usize, candidate: Vec2) -> f64 {
        let robot = &self.robots[robot_index];
        let hard_separation = self.public.robot.radius_m * 2.0 + 0.035;
        let comfort_separation = hard_separation + 0.18;
        let mut penalty = 0.0;
        for (other_index, other) in self.robots.iter().enumerate() {
            if other_index == robot_index {
                continue;
            }
            let relative_position = other.position - robot.position;
            let relative_velocity = candidate - other.velocity;
            let speed_squared = relative_velocity.length_squared();
            let closest_time = if speed_squared > 1e-9 {
                (relative_position.dot(relative_velocity) / speed_squared).clamp(0.0, 0.75)
            } else {
                0.0
            };
            let closest = relative_position - relative_velocity * closest_time;
            let distance = closest.length();
            let time_weight = 1.0 / (0.10 + closest_time);
            if distance < hard_separation {
                penalty += 220.0
                    + (hard_separation - distance) * 420.0 * time_weight;
            } else if distance < comfort_separation {
                penalty += (comfort_separation - distance).powi(2) * 28.0 * time_weight;
            }
        }
        penalty
    }

    fn boundary_braking_penalty(&self, robot_index: usize, candidate: Vec2) -> f64 {
        let robot = &self.robots[robot_index];
        let half_length = self.public.field.length_m / 2.0 - self.public.robot.radius_m;
        let half_width = self.public.field.width_m / 2.0 - self.public.robot.radius_m;
        let acceleration = self.hidden.robot_max_acceleration;
        let margin = 0.10;
        let boundaries = [
            (half_length - robot.position.x, candidate.x.max(0.0)),
            (half_length + robot.position.x, (-candidate.x).max(0.0)),
            (half_width - robot.position.y, candidate.y.max(0.0)),
            (half_width + robot.position.y, (-candidate.y).max(0.0)),
        ];
        let mut penalty = 0.0;
        for (available, outward_speed) in boundaries {
            if outward_speed <= 0.0 {
                continue;
            }
            let stopping_distance = outward_speed * outward_speed / (2.0 * acceleration);
            let residual = stopping_distance + margin - available;
            if residual > 0.0 {
                penalty += 300.0 + residual * 500.0;
            } else if available < stopping_distance + 0.30 {
                penalty += (stopping_distance + 0.30 - available).powi(2) * 18.0;
            }
        }
        penalty
    }

    fn update_enemy_commands(&mut self) {
        self.update_defensive_phase();
        self.update_defender_assignment();
        let first = FRIENDLY_IDS.len();
        let intents = if !self.play_started {
            self.prestart_intents()
        } else {
            let secondary = if self.primary_defender == first {
                first + 1
            } else {
                first
            };
            let mut intents = [self.cover_intent(first); 3];
            intents[self.primary_defender - first] = self.clearance_intent(self.primary_defender);
            intents[secondary - first] = if self.defensive_phase
                == DefensivePhase::ReboundEmergency
            {
                self.rebound_backstop_intent(secondary)
            } else if self.ball.position.x < 1.85 {
                self.compact_wall_intent(secondary)
            } else {
                self.cover_intent(secondary)
            };
            intents[2] = self.goalkeeper_intent(first + 2);
            intents
        };
        for (offset, intent) in intents.into_iter().enumerate() {
            let index = first + offset;
            self.robots[index].command = self.opponent_motion_command(index, intent);
        }
    }

    fn integrate_robots(&mut self, dt: f64) {
        let half_length = self.public.field.length_m / 2.0;
        let half_width = self.public.field.width_m / 2.0;
        let radius = self.public.robot.radius_m;
        for robot in &mut self.robots {
            let maximum_velocity =
                maximum_velocity_for_team(self.hidden.robot_max_velocity, robot.team);
            let mut desired_global = robot.command.local_velocity.rotate(robot.heading);
            let forward = Vec2::new(robot.heading.cos(), robot.heading.sin());
            let lateral = Vec2::new(-forward.y, forward.x);
            let forward_component = desired_global.dot(forward);
            let lateral_component = desired_global.dot(lateral) * self.hidden.lateral_slip;
            desired_global = forward * forward_component + lateral * lateral_component;
            desired_global = desired_global.clamp_length(maximum_velocity);
            let acceleration = ((desired_global - robot.velocity)
                * self.hidden.robot_velocity_response)
                .clamp_length(self.hidden.robot_max_acceleration);
            robot.velocity += acceleration * dt;
            robot.position += robot.velocity * dt;

            let desired_angular = robot.command.angular_velocity.clamp(
                -self.hidden.robot_max_angular_velocity,
                self.hidden.robot_max_angular_velocity,
            );
            let angular_acceleration = ((desired_angular - robot.angular_velocity)
                * self.hidden.robot_angular_response)
                .clamp(
                    -self.hidden.robot_max_angular_acceleration,
                    self.hidden.robot_max_angular_acceleration,
                );
            robot.angular_velocity += angular_acceleration * dt;
            robot.heading = wrap_angle(robot.heading + robot.angular_velocity * dt);

            if robot.position.x < -half_length + radius {
                robot.position.x = -half_length + radius;
                robot.velocity.x = robot.velocity.x.abs() * self.hidden.robot_restitution;
            } else if robot.position.x > half_length - radius {
                robot.position.x = half_length - radius;
                robot.velocity.x = -robot.velocity.x.abs() * self.hidden.robot_restitution;
            }
            if robot.position.y < -half_width + radius {
                robot.position.y = -half_width + radius;
                robot.velocity.y = robot.velocity.y.abs() * self.hidden.robot_restitution;
            } else if robot.position.y > half_width - radius {
                robot.position.y = half_width - radius;
                robot.velocity.y = -robot.velocity.y.abs() * self.hidden.robot_restitution;
            }
        }
    }

    fn resolve_robot_collisions(&mut self) {
        let minimum = self.public.robot.radius_m * 2.0;
        for left in 0..self.robots.len() {
            for right in (left + 1)..self.robots.len() {
                let delta = self.robots[right].position - self.robots[left].position;
                let distance = delta.length();
                if distance >= minimum {
                    continue;
                }
                let normal = delta.normalized_or(Vec2::new(1.0, 0.0));
                let correction = normal * ((minimum - distance) * 0.5 + 1e-6);
                self.robots[left].position -= correction;
                self.robots[right].position += correction;
                let relative = self.robots[right].velocity - self.robots[left].velocity;
                let closing = relative.dot(normal);
                if closing < 0.0 {
                    let impulse = normal * (-(1.0 + self.hidden.robot_restitution) * closing * 0.5);
                    self.robots[left].velocity -= impulse;
                    self.robots[right].velocity += impulse;
                }
            }
        }
    }

    fn enforce_prestart_enemy_exclusion(&mut self) {
        if self.play_started {
            return;
        }
        let minimum = self.public.prestart_enemy_exclusion_radius_m;
        for robot in self.robots.iter_mut().skip(FRIENDLY_IDS.len()) {
            let delta = robot.position - self.ball.position;
            let distance = delta.length();
            if distance >= minimum {
                continue;
            }
            let normal = delta.normalized_or(Vec2::new(1.0, 0.0));
            robot.position = self.ball.position + normal * minimum;
            let inward_speed = robot.velocity.dot(normal);
            if inward_speed < 0.0 {
                robot.velocity -= normal * inward_speed;
            }
        }
    }

    fn resolve_robot_ball_contacts(&mut self) {
        let mut friendly_contacts = [false; FRIENDLY_IDS.len()];
        let mut friendly_kicks = [false; FRIENDLY_IDS.len()];
        let radius = self.public.robot.radius_m;
        let ball_radius = self.public.ball_radius_m;
        let kicker_half = self.public.robot.kicker_width_m / 2.0;
        let front_x = (radius * radius - kicker_half * kicker_half).sqrt();

        for (robot_index, robot) in self.robots.iter_mut().enumerate() {
            let relative_global = self.ball.position - robot.position;
            let relative_local = relative_global.rotate(-robot.heading);
            let closest_y = relative_local.y.clamp(-kicker_half, kicker_half);
            let segment_delta = relative_local - Vec2::new(front_x, closest_y);
            let segment_distance = segment_delta.length();
            let segment_contact = relative_local.x >= front_x - ball_radius
                && relative_local.x <= front_x + ball_radius * 1.5
                && segment_distance <= ball_radius + 1e-5;
            let on_removed_front =
                relative_local.x > front_x && relative_local.y.abs() < kicker_half;
            let circle_distance = relative_global.length();
            let circle_contact = !on_removed_front && circle_distance < radius + ball_radius;
            let contact = segment_contact || circle_contact;

            if contact {
                if robot.team == Team::Friendly {
                    friendly_contacts[robot_index] = true;
                }
                let normal = if segment_contact {
                    segment_delta
                        .normalized_or(
                            Vec2::new(robot.heading.cos(), robot.heading.sin())
                                .rotate(-robot.heading),
                        )
                        .rotate(robot.heading)
                } else {
                    relative_global.normalized_or(Vec2::new(1.0, 0.0))
                };
                let target_distance = if segment_contact {
                    ball_radius
                } else {
                    radius + ball_radius
                };
                let penetration = if segment_contact {
                    (target_distance - segment_distance).max(0.0)
                } else {
                    (target_distance - circle_distance).max(0.0)
                };
                self.ball.position += normal * (penetration + 1e-6);
                let relative_velocity = self.ball.velocity - robot.velocity;
                let closing = relative_velocity.dot(normal);
                if closing < 0.0 {
                    self.ball.velocity -= normal * ((1.0 + self.hidden.ball_restitution) * closing);
                }
                self.ball.velocity += robot.velocity * 0.035;

                let rising_kick = robot.command.kick && !robot.previous_kick;
                if segment_contact && robot.command.kick && (!robot.kicker_contact || rising_kick) {
                    let forward = Vec2::new(robot.heading.cos(), robot.heading.sin());
                    self.ball.velocity = self.ball.velocity * 0.25
                        + forward * self.hidden.kick_speed
                        + robot.velocity * 0.35;
                    if robot.team == Team::Friendly {
                        friendly_kicks[robot_index] = true;
                    }
                }
            }
            robot.kicker_contact = segment_contact;
            robot.previous_kick = robot.command.kick;
        }

        for (index, touched) in friendly_contacts.into_iter().enumerate() {
            if !touched {
                continue;
            }
            self.play_started = true;
            match self.first_friendly_contact {
                None => self.first_friendly_contact = Some(index),
                Some(first) if first != index => self.pass_received = true,
                Some(_) => {}
            }
        }
        if self.pass_received {
            for (index, kicked) in friendly_kicks.into_iter().enumerate() {
                if kicked && self.first_friendly_contact != Some(index) {
                    self.shot_after_pass = true;
                }
            }
        }
    }

    fn integrate_ball(&mut self, dt: f64) {
        let drag = (-self.hidden.ball_linear_drag * dt).exp();
        self.ball.velocity *= drag;
        if self.ball.velocity.length() < 0.005 {
            self.ball.velocity = Vec2::ZERO;
        }
        self.ball.position += self.ball.velocity * dt;
    }

    fn check_rules(&mut self) {
        let half_length = self.public.field.length_m / 2.0;
        let half_width = self.public.field.width_m / 2.0;
        let goal_half = self.public.field.attacking_goal_width_m / 2.0;
        if self.ball.position.x >= half_length && self.ball.position.y.abs() <= goal_half {
            self.terminal = if self.shot_after_pass {
                Terminal::Success("pass_and_goal")
            } else {
                Terminal::Failure("pass_sequence_incomplete")
            };
            return;
        }
        if self.ball.position.x <= -half_length
            || self.ball.position.x >= half_length
            || self.ball.position.y.abs() >= half_width
        {
            self.terminal = Terminal::Failure("ball_out");
            return;
        }
        if !self.play_started && self.elapsed_s >= self.public.start_touch_limit_ms as f64 / 1000.0
        {
            self.terminal = Terminal::Failure("start_timeout");
            return;
        }
        if self.elapsed_s >= self.public.episode_limit_ms as f64 / 1000.0 {
            self.terminal = Terminal::Failure("episode_timeout");
        }
    }

    fn sample_observations(&mut self, dt: f64) {
        self.observation_accumulator += dt;
        let period = 1.0 / self.public.observation_nominal_hz as f64;
        while self.observation_accumulator >= period {
            self.observation_accumulator -= period;
            self.observation_sequence += 1;
            let jitter = self.rng.range(
                -self.hidden.observation_jitter_s,
                self.hidden.observation_jitter_s,
            );
            let release_at =
                self.elapsed_s + self.public.observation_nominal_delay_ms as f64 / 1000.0 + jitter;
            self.delayed_observations.push_back(DelayedObservation {
                release_at,
                observation: self.make_observation(self.observation_sequence),
            });
        }
    }

    fn release_observations(&mut self) {
        while self
            .delayed_observations
            .front()
            .is_some_and(|item| item.release_at <= self.elapsed_s)
        {
            if let Some(item) = self.delayed_observations.pop_front() {
                self.latest_released = Some(item.observation);
            }
        }
    }

    fn make_observation(&self, sequence: u64) -> Observation {
        Observation {
            sequence,
            robots: self
                .robots
                .iter()
                .map(|robot| RobotObservation {
                    id: robot.id.to_string(),
                    team: match robot.team {
                        Team::Friendly => "friendly",
                        Team::Enemy => "enemy",
                    },
                    position: robot.position,
                    velocity: robot.velocity,
                    heading: robot.heading,
                    angular_velocity: robot.angular_velocity,
                })
                .collect(),
            ball: BallObservation {
                position: self.ball.position,
                velocity: self.ball.velocity,
            },
        }
    }
}

impl Robot {
    fn new(id: &'static str, team: Team, x: f64, y: f64, heading: f64) -> Self {
        Self {
            id,
            team,
            position: Vec2::new(x, y),
            velocity: Vec2::ZERO,
            heading,
            angular_velocity: 0.0,
            command: RobotCommand::default(),
            previous_kick: false,
            kicker_contact: false,
        }
    }
}

fn wrap_angle(mut angle: f64) -> f64 {
    while angle > PI {
        angle -= 2.0 * PI;
    }
    while angle < -PI {
        angle += 2.0 * PI;
    }
    angle
}

#[cfg(test)]
mod tests {
    use super::*;

    fn advance_for(simulator: &mut Simulator, seconds: f64) {
        let dt = 1.0 / 240.0;
        for _ in 0..(seconds / dt).round() as usize {
            simulator.advance(dt);
        }
    }

    #[test]
    fn observations_are_delayed_and_contain_five_robots() {
        let mut simulator = Simulator::new(7);
        advance_for(&mut simulator, 0.10);
        assert!(simulator.latest_observation().is_none());
        advance_for(&mut simulator, 0.20);
        let observation = simulator.latest_observation().expect("delayed frame");
        assert_eq!(observation.robots.len(), 5);
        assert!(observation.sequence > 0);
    }

    #[test]
    fn initial_layout_is_a_touchline_restart_with_two_attackers() {
        let simulator = Simulator::new(9);
        assert_eq!(FRIENDLY_IDS.len(), 2);
        assert_eq!(ENEMY_IDS.len(), 3);
        assert!(simulator.ball.position.x > 0.0);
        let upper_touchline = simulator.public.field.width_m / 2.0;
        assert!(upper_touchline - simulator.ball.position.y <= 0.25);
        assert!(simulator.robots[0].position.x < simulator.ball.position.x);
        assert!(simulator.robots[0].position.y > simulator.ball.position.y);
        assert!(simulator.robots[1].position.y < simulator.ball.position.y - 2.0);
        for enemy in simulator.robots.iter().skip(FRIENDLY_IDS.len()) {
            let distance = (enemy.position - simulator.ball.position).length();
            assert!(distance >= simulator.public.prestart_enemy_exclusion_radius_m);
        }
        assert_eq!(simulator.robots.last().unwrap().id, "enemy_2");
        assert!(simulator.robots.last().unwrap().position.x > 4.0);
    }

    #[test]
    fn no_friendly_touch_fails_at_five_seconds() {
        let mut simulator = Simulator::new(11);
        advance_for(&mut simulator, 5.1);
        let result = simulator.result();
        assert_eq!(result.status, "failure");
        assert_eq!(result.reason, Some("start_timeout"));
    }

    #[test]
    fn desired_velocity_is_not_applied_instantly() {
        let mut simulator = Simulator::new(17);
        simulator
            .set_friendly_commands(&[(
                0,
                RobotCommand {
                    local_velocity: Vec2::new(10.0, 0.0),
                    angular_velocity: 0.0,
                    kick: false,
                },
            )])
            .unwrap();
        simulator.advance(1.0 / 240.0);
        let speed = simulator.robots[0].velocity.length();
        assert!(speed > 0.0);
        assert!(speed < 0.1);
        advance_for(&mut simulator, 1.0);
        assert!(simulator.robots[0].velocity.length() > simulator.hidden.robot_max_velocity);
        assert!(
            simulator.robots[0].velocity.length()
                < simulator.hidden.robot_max_velocity * FRIENDLY_MAX_VELOCITY_MULTIPLIER
        );
    }

    #[test]
    fn friendly_maximum_velocity_is_twice_the_enemy_limit() {
        let simulator = Simulator::new(18);
        let enemy_maximum = simulator.hidden.robot_max_velocity;
        assert_eq!(
            maximum_velocity_for_team(enemy_maximum, Team::Friendly),
            enemy_maximum * 2.0
        );
        assert_eq!(
            maximum_velocity_for_team(enemy_maximum, Team::Enemy),
            enemy_maximum
        );
    }

    #[test]
    fn local_velocity_rotates_with_true_heading() {
        let mut simulator = Simulator::new(19);
        simulator.robots[0].position = Vec2::ZERO;
        simulator.robots[0].heading = PI / 2.0;
        simulator
            .set_friendly_commands(&[(
                0,
                RobotCommand {
                    local_velocity: Vec2::new(1.0, 0.0),
                    angular_velocity: 0.0,
                    kick: false,
                },
            )])
            .unwrap();
        advance_for(&mut simulator, 0.25);
        assert!(simulator.robots[0].velocity.y > 0.2);
        assert!(simulator.robots[0].velocity.x.abs() < 0.1);
    }

    #[test]
    fn front_contact_starts_play_and_kicks_forward() {
        let mut simulator = Simulator::new(21);
        let radius = simulator.public.robot.radius_m;
        let kicker_half = simulator.public.robot.kicker_width_m / 2.0;
        let front_x = (radius * radius - kicker_half * kicker_half).sqrt();
        simulator.robots[0].position = Vec2::ZERO;
        simulator.robots[0].heading = 0.0;
        simulator.ball.position = Vec2::new(front_x + simulator.public.ball_radius_m * 0.9, 0.0);
        simulator
            .set_friendly_commands(&[(
                0,
                RobotCommand {
                    local_velocity: Vec2::ZERO,
                    angular_velocity: 0.0,
                    kick: true,
                },
            )])
            .unwrap();

        simulator.advance(1.0 / 240.0);

        assert!(simulator.play_started);
        assert!(simulator.ball.velocity.x > 4.0);
        assert!(simulator.ball.velocity.y.abs() < 1e-9);
    }

    #[test]
    fn continuous_kicker_contact_does_not_repeat_impulse_each_tick() {
        let mut simulator = Simulator::new(22);
        let radius = simulator.public.robot.radius_m;
        let kicker_half = simulator.public.robot.kicker_width_m / 2.0;
        let front_x = (radius * radius - kicker_half * kicker_half).sqrt();
        simulator.robots[0].position = Vec2::ZERO;
        simulator.robots[0].heading = 0.0;
        simulator.ball.position = Vec2::new(front_x + simulator.public.ball_radius_m * 0.9, 0.0);
        simulator
            .set_friendly_commands(&[(
                0,
                RobotCommand {
                    local_velocity: Vec2::ZERO,
                    angular_velocity: 0.0,
                    kick: true,
                },
            )])
            .unwrap();

        simulator.advance(1.0 / 240.0);
        let first_speed = simulator.ball.velocity.x;
        simulator.ball.position = Vec2::new(front_x + simulator.public.ball_radius_m * 0.9, 0.0);
        simulator.ball.velocity = Vec2::ZERO;
        simulator.advance(1.0 / 240.0);

        assert!(first_speed > 4.0);
        assert!(simulator.ball.velocity.x.abs() < 0.01);
    }

    #[test]
    fn goal_and_other_boundary_crossings_have_distinct_results() {
        let mut goal = Simulator::new(24);
        goal.shot_after_pass = true;
        goal.ball.position = Vec2::new(goal.public.field.length_m / 2.0 + 0.01, 0.0);
        goal.check_rules();
        assert_eq!(goal.result().status, "success");
        assert_eq!(goal.result().reason, Some("pass_and_goal"));

        let mut out = Simulator::new(25);
        out.ball.position = Vec2::new(0.0, out.public.field.width_m / 2.0 + 0.01);
        out.check_rules();
        assert_eq!(out.result().status, "failure");
        assert_eq!(out.result().reason, Some("ball_out"));
    }

    #[test]
    fn direct_goal_without_pass_and_receiver_kick_fails() {
        let mut simulator = Simulator::new(26);
        simulator.ball.position = Vec2::new(simulator.public.field.length_m / 2.0 + 0.01, 0.0);
        simulator.check_rules();
        assert_eq!(simulator.result().status, "failure");
        assert_eq!(
            simulator.result().reason,
            Some("pass_sequence_incomplete")
        );
    }

    #[test]
    fn terminal_snapshot_contains_the_actual_boundary_crossing() {
        let mut simulator = Simulator::new(29);
        simulator.shot_after_pass = true;
        simulator.ball.position =
            Vec2::new(simulator.public.field.length_m / 2.0 + 0.01, 0.1);
        simulator.check_rules();

        let snapshot = simulator.terminal_snapshot().expect("terminal snapshot");
        assert!(snapshot.ball.position.x > simulator.public.field.length_m / 2.0);
        assert_eq!(snapshot.robots.len(), 5);
    }

    #[test]
    fn distinct_receiver_contact_and_kick_complete_the_scoring_sequence() {
        let mut simulator = Simulator::new(28);
        let radius = simulator.public.robot.radius_m;
        let kicker_half = simulator.public.robot.kicker_width_m / 2.0;
        let front_x = (radius * radius - kicker_half * kicker_half).sqrt();
        let contact_position = Vec2::new(
            front_x + simulator.public.ball_radius_m * 0.9,
            0.0,
        );

        simulator.robots[0].position = Vec2::ZERO;
        simulator.robots[0].heading = 0.0;
        simulator.ball.position = contact_position;
        simulator.advance(1.0 / 240.0);
        assert_eq!(simulator.first_friendly_contact, Some(0));

        simulator.robots[0].position = Vec2::new(-2.0, -2.0);
        simulator.robots[1].position = Vec2::ZERO;
        simulator.robots[1].heading = 0.0;
        simulator.ball.position = contact_position;
        simulator.ball.velocity = Vec2::ZERO;
        simulator
            .set_friendly_commands(&[(
                1,
                RobotCommand {
                    local_velocity: Vec2::ZERO,
                    angular_velocity: 0.0,
                    kick: true,
                },
            )])
            .unwrap();
        simulator.advance(1.0 / 240.0);

        assert!(simulator.pass_received);
        assert!(simulator.shot_after_pass);
        simulator.ball.position =
            Vec2::new(simulator.public.field.length_m / 2.0 + 0.01, 0.0);
        simulator.check_rules();
        assert_eq!(simulator.result().status, "success");
    }

    #[test]
    fn prestart_enemy_exclusion_is_a_hard_constraint() {
        let mut simulator = Simulator::new(27);
        let enemy = FRIENDLY_IDS.len();
        simulator.robots[enemy].position = simulator.ball.position + Vec2::new(0.1, 0.0);
        simulator.robots[enemy].velocity = Vec2::new(-1.0, 0.0);

        simulator.advance(1.0 / 240.0);

        let distance = (simulator.robots[enemy].position - simulator.ball.position).length();
        assert!(distance >= simulator.public.prestart_enemy_exclusion_radius_m - 1e-9);
    }

    #[test]
    fn prestart_defenders_reposition_while_respecting_exclusion() {
        let mut simulator = Simulator::new(29);
        let first_enemy = FRIENDLY_IDS.len();
        let goalkeeper = simulator.robots.len() - 1;
        let initial_defender = simulator.robots[first_enemy].position;
        simulator.robots[1].position = Vec2::new(-1.0, -2.0);

        advance_for(&mut simulator, 0.8);

        assert!(!simulator.play_started);
        assert_eq!(simulator.ball.position, Vec2::new(BALL_START.0, BALL_START.1));
        assert!((simulator.robots[first_enemy].position - initial_defender).length() > 0.1);
        assert!(
            simulator.robots[goalkeeper].position.y.abs()
                <= simulator.public.field.attacking_goal_width_m / 2.0 + 0.62
        );
        for enemy in simulator.robots.iter().skip(FRIENDLY_IDS.len()) {
            assert!(
                (enemy.position - simulator.ball.position).length()
                    >= simulator.public.prestart_enemy_exclusion_radius_m - 1e-9
            );
        }
    }

    #[test]
    fn goalkeeper_tracks_the_predicted_intersection_of_a_diagonal_shot() {
        let mut simulator = Simulator::new(31);
        let goalkeeper = simulator.robots.len() - 1;
        simulator.play_started = true;
        simulator.ball.position = Vec2::new(0.0, 2.0);
        simulator.ball.velocity = Vec2::new(4.0, -1.2);
        simulator.robots[goalkeeper].position.y = 0.62;

        advance_for(&mut simulator, 0.5);

        assert!(
            simulator.robots[goalkeeper].position.y > 0.65,
            "goalkeeper_y={} ball={:?} velocity={:?} phase={:?}",
            simulator.robots[goalkeeper].position.y,
            simulator.ball.position,
            simulator.ball.velocity,
            simulator.defensive_phase,
        );
        assert!(simulator.is_running());
    }

    #[test]
    fn goalkeeper_margin_stays_inside_the_physical_contact_radius() {
        let mut simulator = Simulator::new(32);
        let goalkeeper = simulator.robots.len() - 1;
        simulator.play_started = true;
        simulator.defensive_phase = DefensivePhase::ShotEmergency;
        simulator.ball.position = Vec2::new(0.997, 2.647);
        simulator.ball.velocity = Vec2::new(3.322, -2.118);
        simulator.robots[goalkeeper].position = Vec2::new(3.686, 0.570);
        simulator.robots[goalkeeper].heading = 2.507;

        let intent = simulator.goalkeeper_intent(goalkeeper);
        let (_, crossing_y) = simulator
            .ball_crossing_at_x(intent.position.x)
            .expect("shot reaches goalkeeper guard plane");
        let physical_coverage = simulator.public.robot.radius_m
            + simulator.public.ball_radius_m;
        let planned_gap = (crossing_y - intent.position.y).abs();

        assert!(
            planned_gap + GOALKEEPER_COVERAGE_MARGIN_M <= physical_coverage + 1e-9,
            "planned_gap={planned_gap} physical_coverage={physical_coverage} intent={intent:?}",
        );
    }

    #[test]
    fn defenders_route_goal_side_before_enabling_a_clearance_kick() {
        let mut simulator = Simulator::new(33);
        let defender = FRIENDLY_IDS.len();
        simulator.play_started = true;
        simulator.ball.position = Vec2::ZERO;
        simulator.ball.velocity = Vec2::ZERO;
        simulator.robots[defender].position = Vec2::new(-0.4, 0.0);
        simulator.robots[defender].heading = 0.0;

        simulator.update_enemy_commands();

        let route_command = simulator.robots[defender].command;
        let route_global = route_command
            .local_velocity
            .rotate(simulator.robots[defender].heading);
        assert!(!route_command.kick);
        assert!(route_global.x.abs() < 1e-9);
        assert!(route_global.y.abs() > 0.1);

        simulator.robots[defender].position = Vec2::new(0.20, 0.0);
        simulator.update_enemy_commands();

        let clear_command = simulator.robots[defender].command;
        let clear_global = clear_command
            .local_velocity
            .rotate(simulator.robots[defender].heading);
        assert!(clear_command.kick);
        assert!(clear_global.x < 0.0);
    }

    #[test]
    fn ball_prediction_integrates_linear_drag() {
        let mut simulator = Simulator::new(35);
        simulator.ball.position = Vec2::new(0.4, -0.2);
        simulator.ball.velocity = Vec2::new(2.0, 0.5);

        let predicted = simulator.predict_ball_position(1.0);
        let travel = (1.0 - (-simulator.hidden.ball_linear_drag).exp())
            / simulator.hidden.ball_linear_drag;

        assert_eq!(predicted, simulator.ball.position + simulator.ball.velocity * travel);
        assert!(predicted.x < simulator.ball.position.x + simulator.ball.velocity.x);
    }

    #[test]
    fn defender_assignment_switches_to_materially_faster_interceptor() {
        let mut simulator = Simulator::new(37);
        let first = FRIENDLY_IDS.len();
        simulator.play_started = true;
        simulator.elapsed_s = 1.0;
        simulator.primary_defender = first;
        simulator.last_role_switch_s = 0.0;
        simulator.ball.position = Vec2::ZERO;
        simulator.ball.velocity = Vec2::ZERO;
        simulator.robots[first].position = Vec2::new(3.0, 2.0);
        simulator.robots[first + 1].position = Vec2::new(0.3, 0.0);

        simulator.update_defender_assignment();

        assert_eq!(simulator.primary_defender, first + 1);
        assert_eq!(simulator.last_role_switch_s, simulator.elapsed_s);
    }

    #[test]
    fn opponent_motion_uses_braking_distance_instead_of_unit_position_gain() {
        let simulator = Simulator::new(39);
        let defender = FRIENDLY_IDS.len();
        let robot = &simulator.robots[defender];
        let intent = OpponentIntent {
            position: robot.position + Vec2::new(0.5, 0.0),
            face: simulator.ball.position,
            feedforward_velocity: Vec2::ZERO,
            speed_limit: simulator.hidden.robot_max_velocity,
            kick: false,
        };

        let command = simulator.opponent_motion_command(defender, intent);
        let desired_global = command.local_velocity.rotate(robot.heading);

        assert!(desired_global.length() > 1.0);
        assert!(desired_global.length() <= simulator.hidden.robot_max_velocity + 1e-9);
    }

    #[test]
    fn goalkeeper_solves_drag_aware_crossing_point() {
        let mut simulator = Simulator::new(41);
        simulator.ball.position = Vec2::new(0.0, 2.0);
        simulator.ball.velocity = Vec2::new(4.0, -1.2);

        let (time_s, crossing_y) = simulator.ball_crossing_at_x(4.02).expect("crossing");
        let predicted = simulator.predict_ball_position(time_s);

        assert!((predicted.x - 4.02).abs() < 1e-9);
        assert!((crossing_y - predicted.y).abs() < 1e-9);
        assert!(crossing_y < simulator.ball.position.y);
    }

    #[test]
    fn observed_shot_immediately_preempts_the_phase_hysteresis() {
        let mut simulator = Simulator::new(43);
        simulator.play_started = true;
        simulator.elapsed_s = 0.02;
        simulator.last_phase_switch_s = 0.0;
        simulator.defensive_phase = DefensivePhase::LooseBall;
        simulator.ball.position = Vec2::new(1.6, 0.4);
        simulator.ball.velocity = Vec2::new(2.8, -0.1);

        simulator.update_defensive_phase();

        assert_eq!(simulator.defensive_phase, DefensivePhase::ShotEmergency);
    }

    #[test]
    fn dangerous_rebound_is_latched_as_an_emergency() {
        let mut simulator = Simulator::new(44);
        simulator.play_started = true;
        simulator.elapsed_s = 2.0;
        simulator.defensive_phase = DefensivePhase::ShotEmergency;
        simulator.previous_ball_velocity = Vec2::new(3.4, -0.2);
        simulator.ball.position = Vec2::new(3.35, 0.45);
        simulator.ball.velocity = Vec2::new(-3.1, 0.8);

        simulator.update_defensive_phase();

        assert_eq!(
            simulator.defensive_phase,
            DefensivePhase::ReboundEmergency
        );
        let latched_until = simulator.rebound_emergency_until_s;
        assert!(latched_until >= 3.09);

        simulator.elapsed_s = 2.6;
        simulator.ball.position = Vec2::new(1.9, 0.8);
        simulator.ball.velocity = Vec2::new(-1.2, 0.2);
        simulator.update_defensive_phase();

        assert_eq!(
            simulator.defensive_phase,
            DefensivePhase::ReboundEmergency
        );
        assert_eq!(simulator.rebound_emergency_until_s, latched_until);
    }

    #[test]
    fn compact_wall_stays_goal_side_instead_of_following_a_high_decoy() {
        let mut simulator = Simulator::new(46);
        let secondary = FRIENDLY_IDS.len() + 1;
        simulator.play_started = true;
        simulator.ball.position = Vec2::new(0.85, 2.35);
        simulator.ball.velocity = Vec2::new(0.25, -0.1);
        simulator.robots[1].position = Vec2::new(1.9, 2.82);
        simulator.robots[simulator.primary_defender].position =
            Vec2::new(1.15, 2.20);

        let intent = simulator.compact_wall_intent(secondary);

        assert!(intent.position.x > simulator.ball.position.x + 0.20);
        assert!(intent.position.x < 2.5);
        assert!(intent.position.y < simulator.robots[1].position.y - 0.20);
    }

    #[test]
    fn rebound_backstop_is_goal_side_of_the_predicted_ball() {
        let mut simulator = Simulator::new(48);
        let secondary = FRIENDLY_IDS.len() + 1;
        simulator.play_started = true;
        simulator.ball.position = Vec2::new(3.25, 0.55);
        simulator.ball.velocity = Vec2::new(-3.0, 0.7);
        simulator.robots[secondary].position = Vec2::new(4.0, -0.4);

        let predicted = simulator.predict_ball_position(0.20);
        let intent = simulator.rebound_backstop_intent(secondary);

        assert!(intent.position.x > predicted.x);
        assert!(intent.speed_limit >= simulator.hidden.robot_max_velocity - 1e-9);
    }

    #[test]
    fn velocity_obstacle_scores_a_head_on_collision_as_unsafe() {
        let mut simulator = Simulator::new(45);
        let defender = FRIENDLY_IDS.len();
        simulator.robots[defender].position = Vec2::ZERO;
        simulator.robots[defender].velocity = Vec2::ZERO;
        simulator.robots[0].position = Vec2::new(0.52, 0.0);
        simulator.robots[0].velocity = Vec2::ZERO;
        for index in [1, defender + 1, defender + 2] {
            simulator.robots[index].position = Vec2::new(-3.0, index as f64 * 0.3);
        }

        let head_on = simulator.velocity_obstacle_penalty(defender, Vec2::new(1.6, 0.0));
        let retreat = simulator.velocity_obstacle_penalty(defender, Vec2::new(-1.0, 0.0));

        assert!(head_on > retreat + 100.0);
    }

    #[test]
    fn boundary_barrier_uses_stopping_distance_before_the_line() {
        let mut simulator = Simulator::new(47);
        let defender = FRIENDLY_IDS.len();
        let half_length = simulator.public.field.length_m / 2.0
            - simulator.public.robot.radius_m;
        simulator.robots[defender].position = Vec2::new(half_length - 0.14, 0.0);

        let outward = simulator.boundary_braking_penalty(defender, Vec2::new(1.7, 0.0));
        let inward = simulator.boundary_braking_penalty(defender, Vec2::new(-1.7, 0.0));

        assert!(outward > 300.0);
        assert_eq!(inward, 0.0);
    }

    #[test]
    fn clearance_search_never_selects_a_direction_toward_own_goal() {
        let simulator = Simulator::new(49);
        let defender = FRIENDLY_IDS.len();
        let direction = simulator.optimized_clearance_direction(
            defender,
            Vec2::new(3.2, 1.8),
        );

        assert!(direction.x < -0.30);
        assert!((direction.length() - 1.0).abs() < 1e-9);
    }

    #[test]
    fn reachability_penalizes_motion_and_heading_away_from_the_target() {
        let mut simulator = Simulator::new(51);
        let defender = FRIENDLY_IDS.len();
        let target = Vec2::new(1.5, 0.0);
        simulator.robots[defender].position = Vec2::ZERO;
        simulator.robots[defender].heading = 0.0;
        simulator.robots[defender].velocity = Vec2::new(1.0, 0.0);
        let approaching = simulator.minimum_travel_time(defender, target);

        simulator.robots[defender].heading = PI;
        simulator.robots[defender].velocity = Vec2::new(-1.0, 0.0);
        let retreating = simulator.minimum_travel_time(defender, target);

        assert!(retreating > approaching + 0.35);
    }

    #[test]
    fn attacker_control_belief_uses_distance_orientation_and_closing_speed() {
        let mut simulator = Simulator::new(53);
        simulator.ball.position = Vec2::ZERO;
        simulator.ball.velocity = Vec2::ZERO;
        simulator.robots[0].position = Vec2::new(-0.20, 0.0);
        simulator.robots[0].heading = 0.0;
        simulator.robots[0].velocity = Vec2::new(0.5, 0.0);
        let controlled = simulator.attacker_control_likelihood(0);

        simulator.robots[0].position = Vec2::new(-1.2, 0.0);
        simulator.robots[0].heading = PI;
        simulator.robots[0].velocity = Vec2::new(-0.5, 0.0);
        let unlikely = simulator.attacker_control_likelihood(0);

        assert!(controlled > 0.55);
        assert!(unlikely < 0.05);
    }

    #[test]
    fn opponent_planning_runs_at_sixty_hertz_not_every_physics_tick() {
        let mut simulator = Simulator::new(55);

        simulator.advance(1.0 / 240.0);
        let first_deadline = simulator.next_opponent_control_s;
        simulator.advance(1.0 / 240.0);
        simulator.advance(1.0 / 240.0);

        assert_eq!(simulator.next_opponent_control_s, first_deadline);
        simulator.advance(1.0 / 60.0);
        assert!(simulator.next_opponent_control_s > first_deadline);
    }

    #[test]
    fn public_spec_does_not_serialize_hidden_dynamics() {
        let encoded = serde_json::to_string(&PublicSpec::default()).unwrap();
        for forbidden in [
            "kick_speed",
            "max_acceleration",
            "lateral_slip",
            "restitution",
            "jitter_s",
        ] {
            assert!(!encoded.contains(forbidden));
        }
    }

    #[test]
    fn same_seed_and_commands_are_deterministic() {
        let mut left = Simulator::new(23);
        let mut right = Simulator::new(23);
        let command = RobotCommand {
            local_velocity: Vec2::new(0.7, -0.2),
            angular_velocity: 0.5,
            kick: true,
        };
        left.set_friendly_commands(&[(0, command)]).unwrap();
        right.set_friendly_commands(&[(0, command)]).unwrap();
        advance_for(&mut left, 1.2);
        advance_for(&mut right, 1.2);
        assert_eq!(left.robots[0].position, right.robots[0].position);
        assert_eq!(left.ball.position, right.ball.position);
        assert_eq!(
            left.latest_observation().unwrap().sequence,
            right.latest_observation().unwrap().sequence
        );
    }
}

use crate::math::Vec2;
use serde::{Deserialize, Serialize};

pub const FRIENDLY_IDS: [&str; 3] = ["friendly_0", "friendly_1", "friendly_2"];

#[derive(Clone, Debug, Default, Deserialize)]
pub struct StartRequest {
    #[serde(default)]
    pub seed: Option<u64>,
}

#[derive(Clone, Debug, Default, Deserialize)]
pub struct CommandRequest {
    pub robots: Vec<RobotCommandInput>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct RobotCommandInput {
    pub id: String,
    pub velocity: Vec2,
    pub angular_velocity: f64,
    pub kick: bool,
}

#[derive(Clone, Copy, Debug, Default)]
pub struct RobotCommand {
    pub local_velocity: Vec2,
    pub angular_velocity: f64,
    pub kick: bool,
}

#[derive(Clone, Debug, Serialize)]
pub struct PublicSpec {
    pub schema_version: u32,
    pub friendly_robot_ids: [&'static str; 3],
    pub enemy_robot_ids: [&'static str; 2],
    pub field: FieldSpec,
    pub robot: RobotGeometrySpec,
    pub ball_radius_m: f64,
    pub episode_limit_ms: u64,
    pub start_touch_limit_ms: u64,
    pub prestart_enemy_exclusion_radius_m: f64,
    pub observation_nominal_hz: u32,
    pub observation_nominal_delay_ms: u64,
    pub observation_has_latency_jitter: bool,
    pub command_frame: &'static str,
    pub observation_frame: &'static str,
}

impl Default for PublicSpec {
    fn default() -> Self {
        Self {
            schema_version: 1,
            friendly_robot_ids: FRIENDLY_IDS,
            enemy_robot_ids: ["enemy_0", "enemy_1"],
            field: FieldSpec {
                length_m: 9.0,
                width_m: 6.0,
                attacking_goal_width_m: 1.5,
                attacking_direction: "positive_x",
            },
            robot: RobotGeometrySpec {
                radius_m: 0.09,
                kicker_width_m: 0.108,
                shape: "cylinder_with_flat_front_chord",
            },
            ball_radius_m: 0.0215,
            episode_limit_ms: 30_000,
            start_touch_limit_ms: 5_000,
            prestart_enemy_exclusion_radius_m: 0.75,
            observation_nominal_hz: 30,
            observation_nominal_delay_ms: 200,
            observation_has_latency_jitter: true,
            command_frame: "robot_local",
            observation_frame: "global",
        }
    }
}

#[derive(Clone, Debug, Serialize)]
pub struct FieldSpec {
    pub length_m: f64,
    pub width_m: f64,
    pub attacking_goal_width_m: f64,
    pub attacking_direction: &'static str,
}

#[derive(Clone, Debug, Serialize)]
pub struct RobotGeometrySpec {
    pub radius_m: f64,
    pub kicker_width_m: f64,
    pub shape: &'static str,
}

#[derive(Clone, Debug, Serialize)]
pub struct Observation {
    pub sequence: u64,
    pub robots: Vec<RobotObservation>,
    pub ball: BallObservation,
}

#[derive(Clone, Debug, Serialize)]
pub struct RobotObservation {
    pub id: String,
    pub team: &'static str,
    pub position: Vec2,
    pub velocity: Vec2,
    pub heading: f64,
    pub angular_velocity: f64,
}

#[derive(Clone, Debug, Serialize)]
pub struct BallObservation {
    pub position: Vec2,
    pub velocity: Vec2,
}

#[derive(Clone, Debug, Serialize)]
pub struct EpisodeResult {
    pub status: &'static str,
    pub reason: Option<&'static str>,
    pub elapsed_ms: u64,
}

#[derive(Clone, Debug, Serialize)]
pub struct StartResponse {
    pub status: &'static str,
}

#[derive(Clone, Debug, Serialize)]
pub struct CommandResponse {
    pub accepted: usize,
}

#[derive(Clone, Debug, Serialize)]
pub struct ErrorResponse {
    pub error: String,
}

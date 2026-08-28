use robot_soccer_simulator::protocol::{
    CommandRequest, CommandResponse, EpisodeResult, ErrorResponse, PublicSpec, RobotCommand,
    StartRequest, StartResponse, FRIENDLY_IDS,
};
use robot_soccer_simulator::sim::Simulator;
use serde::Serialize;
use serde_json::json;
use std::collections::HashSet;
use std::fs::{File, OpenOptions};
use std::io::{Read, Write};
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use tiny_http::{Header, Method, Request, Response, Server, StatusCode};

const PHYSICS_HZ: u32 = 240;
const DEFAULT_BIND: &str = "0.0.0.0:8080";
const DEFAULT_LOG: &str = "/tmp/robot-soccer-simulator.jsonl";

struct Runtime {
    simulator: Option<Simulator>,
    latest_logged_sequence: u64,
    terminal_logged: bool,
    next_seed: u64,
}

impl Runtime {
    fn new() -> Self {
        Self {
            simulator: None,
            latest_logged_sequence: 0,
            terminal_logged: false,
            next_seed: system_millis() ^ 0x5eed_f00d_cafe_babe,
        }
    }

    fn start(&mut self, requested_seed: Option<u64>) {
        let seed = requested_seed.unwrap_or_else(|| {
            self.next_seed = self
                .next_seed
                .wrapping_mul(6364136223846793005)
                .wrapping_add(1);
            self.next_seed
        });
        self.simulator = Some(Simulator::new(seed));
        self.latest_logged_sequence = 0;
        self.terminal_logged = false;
    }

    fn result(&self) -> EpisodeResult {
        self.simulator
            .as_ref()
            .map(Simulator::result)
            .unwrap_or(EpisodeResult {
                status: "idle",
                reason: None,
                elapsed_ms: 0,
            })
    }
}

struct TraceWriter {
    file: Mutex<File>,
}

impl TraceWriter {
    fn open(path: PathBuf) -> Result<Self, std::io::Error> {
        let file = OpenOptions::new().create(true).append(true).open(path)?;
        Ok(Self {
            file: Mutex::new(file),
        })
    }

    fn event(&self, kind: &str, payload: serde_json::Value) {
        let record = json!({
            "at_unix_ms": system_millis(),
            "event": kind,
            "payload": payload,
        });
        if let Ok(mut file) = self.file.lock() {
            let _ = serde_json::to_writer(&mut *file, &record);
            let _ = file.write_all(b"\n");
            let _ = file.flush();
        }
    }
}

fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let (bind, log_path) = parse_arguments()
        .map_err(|message| std::io::Error::new(std::io::ErrorKind::InvalidInput, message))?;
    let runtime = Arc::new(Mutex::new(Runtime::new()));
    let trace = Arc::new(TraceWriter::open(log_path)?);
    spawn_physics_thread(runtime.clone(), trace.clone());

    let server = Server::http(&bind)?;
    trace.event("server_started", json!({ "bind": bind }));
    for request in server.incoming_requests() {
        handle_request(request, &runtime, &trace);
    }
    Ok(())
}

fn parse_arguments() -> Result<(String, PathBuf), String> {
    let mut bind = DEFAULT_BIND.to_string();
    let mut log_path = PathBuf::from(DEFAULT_LOG);
    let mut arguments = std::env::args().skip(1);
    while let Some(argument) = arguments.next() {
        match argument.as_str() {
            "--bind" => bind = arguments.next().ok_or("--bind requires a value")?,
            "--log" => log_path = PathBuf::from(arguments.next().ok_or("--log requires a value")?),
            "--help" | "-h" => {
                println!("usage: robot-soccer-simulator [--bind HOST:PORT] [--log PATH]");
                std::process::exit(0);
            }
            _ => return Err(format!("unknown argument: {argument}")),
        }
    }
    Ok((bind, log_path))
}

fn spawn_physics_thread(runtime: Arc<Mutex<Runtime>>, trace: Arc<TraceWriter>) {
    thread::spawn(move || {
        let step = Duration::from_secs_f64(1.0 / PHYSICS_HZ as f64);
        let dt = 1.0 / PHYSICS_HZ as f64;
        let mut next_tick = Instant::now() + step;
        loop {
            let now = Instant::now();
            if now < next_tick {
                thread::sleep(next_tick - now);
            }
            next_tick += step;
            if Instant::now().duration_since(next_tick) > Duration::from_millis(50) {
                next_tick = Instant::now() + step;
            }

            let mut delivered = None;
            let mut terminal = None;
            if let Ok(mut state) = runtime.lock() {
                let capture_terminal = !state.terminal_logged;
                let (latest, completed, terminal_snapshot) = match state.simulator.as_mut() {
                    Some(simulator) => {
                        simulator.advance(dt);
                        let latest = simulator.latest_observation();
                        let completed = (!simulator.is_running()).then(|| simulator.result());
                        let terminal_snapshot = if completed.is_some() && capture_terminal {
                            simulator.terminal_snapshot()
                        } else {
                            None
                        };
                        (latest, completed, terminal_snapshot)
                    }
                    None => (None, None, None),
                };
                if let Some(observation) = latest {
                    if observation.sequence > state.latest_logged_sequence {
                        state.latest_logged_sequence = observation.sequence;
                        delivered = Some(observation);
                    }
                }
                if completed.is_some() && !state.terminal_logged {
                    state.terminal_logged = true;
                    terminal = completed.zip(terminal_snapshot);
                }
            }
            if let Some(observation) = delivered {
                trace.event(
                    "observation_delivered",
                    serde_json::to_value(observation).unwrap_or_else(|_| json!({})),
                );
            }
            if let Some((result, snapshot)) = terminal {
                trace.event(
                    "terminal_snapshot",
                    serde_json::to_value(snapshot).unwrap_or_else(|_| json!({})),
                );
                trace.event(
                    "episode_terminal",
                    serde_json::to_value(result).unwrap_or_else(|_| json!({})),
                );
            }
        }
    });
}

fn handle_request(mut request: Request, runtime: &Arc<Mutex<Runtime>>, trace: &Arc<TraceWriter>) {
    let path = request
        .url()
        .split('?')
        .next()
        .unwrap_or(request.url())
        .to_string();
    let method = request.method().clone();
    let response = match (method, path.as_str()) {
        (Method::Get, "/health") => json_response(StatusCode(200), &json!({"ok": true})),
        (Method::Get, "/v1/spec") => json_response(StatusCode(200), &PublicSpec::default()),
        (Method::Post, "/v1/start") => {
            let parsed = read_json_body::<StartRequest>(&mut request, true);
            match parsed {
                Ok(start) => {
                    if let Ok(mut state) = runtime.lock() {
                        state.start(start.seed);
                    }
                    trace.event(
                        "episode_started",
                        json!({"development_seed_supplied": start.seed.is_some()}),
                    );
                    json_response(StatusCode(201), &StartResponse { status: "running" })
                }
                Err(message) => error_response(StatusCode(400), message),
            }
        }
        (Method::Post, "/v1/command") => {
            match read_json_body::<CommandRequest>(&mut request, false).and_then(validate_commands)
            {
                Ok((updates, public_trace)) => {
                    let result = runtime
                        .lock()
                        .map_err(|_| "runtime lock unavailable".to_string())
                        .and_then(|mut state| {
                            state
                                .simulator
                                .as_mut()
                                .ok_or_else(|| "episode_not_started".to_string())?
                                .set_friendly_commands(&updates)
                                .map_err(str::to_string)
                        });
                    match result {
                        Ok(()) => {
                            trace.event("command_received", public_trace);
                            json_response(
                                StatusCode(200),
                                &CommandResponse {
                                    accepted: updates.len(),
                                },
                            )
                        }
                        Err(message) => error_response(StatusCode(409), message),
                    }
                }
                Err(message) => error_response(StatusCode(400), message),
            }
        }
        (Method::Get, "/v1/observation") => {
            let observation = runtime.lock().ok().and_then(|state| {
                state
                    .simulator
                    .as_ref()
                    .and_then(Simulator::latest_observation)
            });
            match observation {
                Some(value) => json_response(StatusCode(200), &value),
                None => Response::from_data(Vec::new()).with_status_code(StatusCode(204)),
            }
        }
        (Method::Get, "/v1/result") => {
            let result = runtime
                .lock()
                .map(|state| state.result())
                .unwrap_or(EpisodeResult {
                    status: "failure",
                    reason: Some("runtime_unavailable"),
                    elapsed_ms: 0,
                });
            json_response(StatusCode(200), &result)
        }
        _ => error_response(StatusCode(404), "not_found".to_string()),
    };
    let _ = request.respond(response);
}

fn read_json_body<T: serde::de::DeserializeOwned>(
    request: &mut Request,
    empty_allowed: bool,
) -> Result<T, String>
where
    T: Default,
{
    let mut body = String::new();
    request
        .as_reader()
        .take(1024 * 1024)
        .read_to_string(&mut body)
        .map_err(|error| format!("cannot read request body: {error}"))?;
    if body.trim().is_empty() && empty_allowed {
        return Ok(T::default());
    }
    serde_json::from_str(&body).map_err(|error| format!("invalid JSON: {error}"))
}

fn validate_commands(
    request: CommandRequest,
) -> Result<(Vec<(usize, RobotCommand)>, serde_json::Value), String> {
    if request.robots.is_empty() || request.robots.len() > FRIENDLY_IDS.len() {
        return Err(format!(
            "robots must contain between one and {} updates",
            FRIENDLY_IDS.len()
        ));
    }
    let mut seen = HashSet::new();
    let mut updates = Vec::new();
    for input in &request.robots {
        let index = FRIENDLY_IDS
            .iter()
            .position(|candidate| *candidate == input.id)
            .ok_or_else(|| format!("unknown or non-friendly robot id: {}", input.id))?;
        if !seen.insert(index) {
            return Err(format!("duplicate robot id: {}", input.id));
        }
        if !input.velocity.is_finite() || !input.angular_velocity.is_finite() {
            return Err(format!("non-finite command for {}", input.id));
        }
        updates.push((
            index,
            RobotCommand {
                local_velocity: input.velocity,
                angular_velocity: input.angular_velocity,
                kick: input.kick,
            },
        ));
    }
    let public_trace = serde_json::to_value(&request.robots)
        .map_err(|error| format!("cannot encode command trace: {error}"))?;
    Ok((updates, public_trace))
}

fn json_response<T: Serialize>(
    status: StatusCode,
    value: &T,
) -> Response<std::io::Cursor<Vec<u8>>> {
    let body = serde_json::to_vec(value).unwrap_or_else(|_| b"{}".to_vec());
    let mut response = Response::from_data(body).with_status_code(status);
    if let Ok(header) = Header::from_bytes("Content-Type", "application/json; charset=utf-8") {
        response.add_header(header);
    }
    response
}

fn error_response(status: StatusCode, message: String) -> Response<std::io::Cursor<Vec<u8>>> {
    json_response(status, &ErrorResponse { error: message })
}

fn system_millis() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

FROM rust:1.85.1-slim-bookworm@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36 AS builder

WORKDIR /src
COPY experiments/robot-soccer-control/Cargo.toml \
     experiments/robot-soccer-control/Cargo.lock ./
COPY experiments/robot-soccer-control/src ./src
RUN cargo test --locked \
    && cargo build --release --locked

FROM debian:bookworm-slim@sha256:88200866dfff7ea7f5cbcb6ec7c8a701889efe6fe859fe64d6990e4b07ea4171

COPY --from=builder /src/target/release/robot-soccer-simulator \
    /usr/local/bin/robot-soccer-simulator
RUN useradd --system --uid 65532 --no-create-home simulator \
    && chmod 0555 /usr/local/bin/robot-soccer-simulator
USER 65532:65532
EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/robot-soccer-simulator"]

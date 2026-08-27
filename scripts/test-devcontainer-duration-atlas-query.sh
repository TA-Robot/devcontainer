#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repository_root="$(cd -- "$script_dir/.." && pwd -P)"
dockerfile="$repository_root/.devcontainer/Dockerfile"
shim="$script_dir/devcontainer-query-agent-duration-atlas"

fail() {
  echo "not ok - $*" >&2
  exit 1
}

bash -n "$shim"

PYTHONDONTWRITEBYTECODE=1 python3 - "$dockerfile" "$shim" <<'PY'
from __future__ import annotations

from pathlib import Path
import sys


dockerfile = Path(sys.argv[1])
shim = Path(sys.argv[2])
raw_lines = dockerfile.read_text(encoding="utf-8").splitlines()
logical: list[str] = []
pending = ""
for raw in raw_lines:
    stripped = raw.strip()
    if pending:
        pending += " " + stripped
    else:
        pending = stripped
    if pending.endswith("\\"):
        pending = pending[:-1].rstrip()
        continue
    logical.append(pending)
    pending = ""
if pending:
    raise AssertionError("Dockerfile ends in an unterminated continuation")

runtime_root = "/usr/local/lib/mira-duration-atlas-runtime"
snapshot_source = "generated/duration-atlas/current.json"
snapshot_target = "/usr/local/share/mira-duration-atlas/current.json"
validity_source = "generated/duration-atlas/current-validity.json"
validity_target = "/usr/local/share/mira-duration-atlas/current-validity.json"
shim_copy = (
    "COPY scripts/devcontainer-query-agent-duration-atlas "
    "/usr/local/bin/query-agent-duration-atlas"
)
if shim_copy not in logical:
    raise AssertionError("Dockerfile does not install the duration-atlas query shim")

module_sources = (
    "scripts/agent_contracts.py",
    "scripts/agent_duration_study.py",
    "scripts/agent_duration_atlas.py",
    "scripts/agent_duration_validity.py",
    "scripts/query_agent_duration_atlas.py",
)
module_copy = next(
    (
        line
        for line in logical
        if line.startswith("COPY ")
        and line.endswith(f"{runtime_root}/scripts/")
    ),
    None,
)
if module_copy is None or any(source not in module_copy.split() for source in module_sources):
    raise AssertionError("Dockerfile runtime module COPY surface is incomplete")

schema_sources = tuple(
    f"experiments/multi-agent-duration/schemas/{name}.schema.json"
    for name in (
        "study",
        "case",
        "case-catalog",
        "capability",
        "fixture",
        "run",
        "batch",
        "atlas",
        "validity",
    )
)
schema_copy = next(
    (
        line
        for line in logical
        if line.startswith("COPY ")
        and line.endswith(
            f"{runtime_root}/experiments/multi-agent-duration/schemas/"
        )
    ),
    None,
)
if schema_copy is None or any(source not in schema_copy.split() for source in schema_sources):
    raise AssertionError("Dockerfile runtime schema COPY surface is incomplete")

snapshot_copy = (
    f"COPY --chown=root:root {snapshot_source} {snapshot_target}"
)
if snapshot_copy not in logical:
    raise AssertionError("Dockerfile does not install the root-owned duration-atlas snapshot")
validity_copy = (
    f"COPY --chown=root:root {validity_source} {validity_target}"
)
if validity_copy not in logical:
    raise AssertionError("Dockerfile does not install the duration validity companion")
snapshot_permissions = next(
    (
        line
        for line in logical
        if line.startswith("RUN ")
        and "chmod 0444 " in line
        and snapshot_target in line
    ),
    None,
)
if snapshot_permissions is None:
    raise AssertionError("Dockerfile does not make the duration-atlas snapshot read-only")
if validity_target not in snapshot_permissions:
    raise AssertionError("Dockerfile does not make the validity companion read-only")

dockerfile_text = dockerfile.read_text(encoding="utf-8")
user_position = dockerfile_text.index("USER $USERNAME")
if dockerfile_text.index(shim_copy) > user_position:
    raise AssertionError("root-owned runtime must be installed before switching users")
if dockerfile_text.index("COPY --chown=root:root generated/duration-atlas/current.json") > user_position:
    raise AssertionError("root-owned snapshot must be installed before switching users")
if dockerfile_text.index("COPY --chown=root:root generated/duration-atlas/current-validity.json") > user_position:
    raise AssertionError("root-owned validity companion must be installed before switching users")

shim_text = shim.read_text(encoding="utf-8")
required_shim_lines = (
    "set -euo pipefail",
    f"runtime_root={runtime_root}",
    'export PYTHONPATH="$runtime_scripts"',
    'exec /usr/bin/python3 "$query_entrypoint" "$@"',
)
if any(line not in shim_text for line in required_shim_lines):
    raise AssertionError("duration-atlas query shim is not fixed to the runtime bundle")
if "${PYTHONPATH" in shim_text:
    raise AssertionError("duration-atlas query shim must not inherit caller PYTHONPATH")
PY

echo "ok - duration atlas query and snapshot Dockerfile COPY surface"

image_was_explicit=0
if [[ $# -gt 1 ]]; then
  fail "usage: $0 [IMAGE]"
elif [[ $# -eq 1 ]]; then
  image="$1"
  image_was_explicit=1
else
  image=devcontainer-smoke:latest
fi

if ! command -v docker >/dev/null 2>&1; then
  if [[ $image_was_explicit -eq 1 ]]; then
    fail "docker is unavailable for requested image smoke: $image"
  fi
  echo "ok - container smoke skipped because docker is unavailable"
  exit 0
fi
if ! docker image inspect "$image" >/dev/null 2>&1; then
  if [[ $image_was_explicit -eq 1 ]]; then
    fail "requested image is unavailable: $image"
  fi
  echo "ok - container smoke skipped because $image is unavailable"
  exit 0
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
chmod 0755 "$tmp"

PYTHONPATH="$repository_root/scripts" PYTHONDONTWRITEBYTECODE=1 \
  python3 - <<'PY' >"$tmp/atlas.json"
from __future__ import annotations

import sys

from agent_duration_atlas import build_atlas, encode_atlas
from agent_duration_study import build_fake_run


atlas = build_atlas(
    [build_fake_run("solo-complete")],
    max_records=1,
    max_input_bytes=1024 * 1024,
    max_output_bytes=1024 * 1024,
)
sys.stdout.buffer.write(encode_atlas(atlas))
PY
chmod 0644 "$tmp/atlas.json"
printf 'raise RuntimeError("caller PYTHONPATH shadowed the image runtime")\n' \
  >"$tmp/agent_duration_atlas.py"
chmod 0644 "$tmp/agent_duration_atlas.py"

docker run --rm \
  --workdir /tmp \
  --entrypoint /usr/local/bin/query-agent-duration-atlas \
  "$image" --help >/dev/null

docker run --rm \
  --entrypoint /bin/bash \
  "$image" -ceu '
runtime=/usr/local/lib/mira-duration-atlas-runtime
snapshot=/usr/local/share/mira-duration-atlas/current.json
validity=/usr/local/share/mira-duration-atlas/current-validity.json
test -x /usr/local/bin/query-agent-duration-atlas
for module in agent_contracts.py agent_duration_study.py agent_duration_atlas.py agent_duration_validity.py query_agent_duration_atlas.py; do
  test -r "$runtime/scripts/$module"
  test ! -w "$runtime/scripts/$module"
done
for schema in study case case-catalog capability fixture run batch atlas validity; do
  test -r "$runtime/experiments/multi-agent-duration/schemas/$schema.schema.json"
  test ! -w "$runtime/experiments/multi-agent-duration/schemas/$schema.schema.json"
done
observed_root="$(PYTHONPATH="$runtime/scripts" /usr/bin/python3 -c "import agent_duration_study; print(agent_duration_study.ROOT)")"
test "$observed_root" = "$runtime"
test -f "$snapshot"
test -r "$snapshot"
test ! -w "$snapshot"
test "$(stat -c %a "$snapshot")" = 444
test "$(stat -c %u:%g "$snapshot")" = 0:0
test -f "$validity"
test -r "$validity"
test ! -w "$validity"
test "$(stat -c %a "$validity")" = 444
test "$(stat -c %u:%g "$validity")" = 0:0
if (exec 2>/dev/null; printf x >>"$snapshot"); then
  echo "duration-atlas snapshot unexpectedly accepted a write" >&2
  exit 1
fi
if (exec 2>/dev/null; printf x >>"$validity"); then
  echo "duration validity companion unexpectedly accepted a write" >&2
  exit 1
fi
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$runtime/scripts" \
  /usr/bin/python3 - "$snapshot" "$validity" <<PY
from pathlib import Path
import json
import sys

from agent_duration_atlas import validate_atlas
from agent_duration_validity import validate_validity_record


with Path(sys.argv[1]).open(encoding="utf-8") as handle:
    atlas = json.load(handle)
validate_atlas(atlas)
with Path(sys.argv[2]).open(encoding="utf-8") as handle:
    validity = json.load(handle)
validate_validity_record(validity)
PY
'

echo "ok - bundled duration atlas is root-owned, read-only, and schema-valid"

docker run --rm \
  --entrypoint /usr/local/bin/query-agent-duration-atlas \
  "$image" \
  /usr/local/share/mira-duration-atlas/current.json \
  --validity /usr/local/share/mira-duration-atlas/current-validity.json \
  --mode coverage \
  --format json \
  --max-rows 1 \
  --max-output-bytes 32768 \
  >"$tmp/bundled-result.json"

jq -e '
  .query_kind == "bounded-duration-atlas-query"
  and .status == "measured"
  and .match.case_strata > 0
  and .match.displayed_rows == 1
  and .validity.status == "supplied"
  and (.rows | length) == 1
  and ([.. | objects | has("samples")] | any | not)
' "$tmp/bundled-result.json" >/dev/null \
  || fail "bundled duration-atlas query returned an invalid or sample-bearing result"

echo "ok - bundled duration atlas query is bounded and does not expose sample bodies"

docker run --rm \
  --workdir /tmp \
  --env PYTHONPATH=/fixture \
  --mount "type=bind,src=$tmp,dst=/fixture,readonly" \
  --entrypoint /usr/local/bin/query-agent-duration-atlas \
  "$image" \
  /fixture/atlas.json \
  --provider fixture \
  --max-rows 1 \
  --max-output-bytes 16384 \
  >"$tmp/result.json"

jq -e '
  .query_kind == "bounded-duration-atlas-query"
  and .status == "measured"
  and .match == {"case_strata": 1, "displayed_rows": 1}
  and (.rows | length) == 1
  and .rows[0].participants[0].provider == "fixture"
' "$tmp/result.json" >/dev/null || fail "container fixture query returned an invalid result"
if grep -Fq '"samples"' "$tmp/result.json"; then
  fail "container query leaked the atlas sample body"
fi

echo "ok - duration atlas query runtime works outside the image workspace"

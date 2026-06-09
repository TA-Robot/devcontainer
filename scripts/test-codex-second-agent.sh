#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
sa="${script_dir}/codex-second-agent"

tmp_paths=()

cleanup() {
  local path
  for path in "${tmp_paths[@]}"; do
    [[ -e "$path" || -L "$path" ]] || continue
    rm -rf "$path"
  done
}
trap cleanup EXIT

new_temp_dir() {
  local dir
  dir="$(mktemp -d)"
  tmp_paths+=("$dir")
  printf '%s\n' "$dir"
}

new_temp_file() {
  local file
  file="$(mktemp)"
  tmp_paths+=("$file")
  printf '%s\n' "$file"
}

new_repo() {
  local repo file
  repo="$(new_temp_dir)"
  git -C "$repo" init -q
  git -C "$repo" config user.email test@example.com
  git -C "$repo" config user.name test
  file="${2:-tracked.txt}"
  mkdir -p "$(dirname "$repo/$file")"
  : > "$repo/$file"
  git -C "$repo" add "$file"
  git -C "$repo" commit -qm "${1:-init}"
  printf '%s\n' "$repo"
}

assert_eq() {
  local expected="$1"
  local actual="$2"
  local message="$3"
  if [[ "$actual" != "$expected" ]]; then
    printf 'not ok - %s\nexpected: %s\nactual:   %s\n' "$message" "$expected" "$actual" >&2
    exit 1
  fi
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  local message="$3"
  if [[ "$haystack" != *"$needle"* ]]; then
    printf 'not ok - %s\nmissing: %s\nin: %s\n' "$message" "$needle" "$haystack" >&2
    exit 1
  fi
}

assert_not_contains() {
  local haystack="$1"
  local needle="$2"
  local message="$3"
  if [[ "$haystack" == *"$needle"* ]]; then
    printf 'not ok - %s\nunexpected: %s\nin: %s\n' "$message" "$needle" "$haystack" >&2
    exit 1
  fi
}

test_management_commands_are_side_effect_free() {
  local repo out err rc count state_count
  repo="$(new_repo)"
  out="$(new_temp_file)"
  err="$(new_temp_file)"

  if (cd "$repo" && "$sa" --agent reviewer status >"$out" 2>"$err"); then
    rc=0
  else
    rc=$?
  fi
  assert_eq "1" "$rc" "status returns nonzero when no session exists"
  count="$(git -C "$repo" worktree list | wc -l | tr -d ' ')"
  assert_eq "1" "$count" "status must not create a worktree"

  if (cd "$repo" && "$sa" --agent reviewer paths >"$out" 2>"$err"); then
    rc=0
  else
    rc=$?
  fi
  assert_eq "0" "$rc" "paths succeeds before workspace init"
  count="$(git -C "$repo" worktree list | wc -l | tr -d ' ')"
  assert_eq "1" "$count" "paths must not create a worktree"

  if (cd "$repo" && "$sa" agents >"$out" 2>"$err"); then
    rc=0
  else
    rc=$?
  fi
  assert_eq "0" "$rc" "agents succeeds before workspace init"
  count="$(git -C "$repo" worktree list | wc -l | tr -d ' ')"
  assert_eq "1" "$count" "agents must not create a worktree"
  state_count="$(find "$repo" -maxdepth 2 -name '.codex-second-agent' | wc -l | tr -d ' ')"
  assert_eq "0" "$state_count" "agents must not create state directories"

  if (cd "$repo" && "$sa" worktree list >"$out" 2>"$err"); then
    rc=0
  else
    rc=$?
  fi
  assert_eq "0" "$rc" "worktree list succeeds without existing worktrees"
  count="$(git -C "$repo" worktree list | wc -l | tr -d ' ')"
  assert_eq "1" "$count" "worktree list must not create a git worktree"
  state_count="$(find "$repo" -maxdepth 2 -name '.codex-second-agent' | wc -l | tr -d ' ')"
  assert_eq "0" "$state_count" "worktree list must not create state directories"
  printf 'ok - management commands stay side-effect free\n'
}

test_parent_workspace_cd_maps_into_agent_worktree() {
  local repo out err effective
  repo="$(new_repo init project/file.txt)"
  out="$(new_temp_file)"
  err="$(new_temp_file)"

  (
    cd "$repo"
    "$sa" workspace init . >/dev/null
    "$sa" --agent reviewer paths -- --cd project >"$out" 2>"$err"
  )

  effective="$(grep '^effective_cd:' "$out" | sed 's/^effective_cd: //')"
  assert_contains "$effective" "/worktrees/reviewer/project" "relative --cd should map into the agent worktree"
  printf 'ok - parent workspace relative --cd is rewritten into worktree path\n'
}

test_project_workspace_without_cd_uses_worktree_root() {
  local control project out err effective
  control="$(new_repo)"
  mkdir -p "$control/project/app"
  project="$control/project/app"
  git -C "$project" init -q
  git -C "$project" config user.email test@example.com
  git -C "$project" config user.name test
  : > "$project/app.txt"
  git -C "$project" add app.txt
  git -C "$project" commit -qm init
  out="$(new_temp_file)"
  err="$(new_temp_file)"

  (
    cd "$control"
    "$sa" workspace init project/app >/dev/null
    "$sa" --agent implementer paths >"$out" 2>"$err"
  )

  effective="$(grep '^effective_cd:' "$out" | sed 's/^effective_cd: //')"
  assert_contains "$effective" "/worktrees/implementer" "project workspace should default to agent worktree root"
  assert_not_contains "$effective" "/worktrees/implementer/project" "project workspace must not append project twice"
  printf 'ok - project workspace runs from worktree root without redundant --cd\n'
}

test_stale_workspace_is_rejected() {
  local control project out err rc stderr_text
  control="$(new_repo)"
  project="$(new_repo)"
  out="$(new_temp_file)"
  err="$(new_temp_file)"

  (
    cd "$control"
    "$sa" workspace init "$project" >/dev/null
  )
  rm -rf "$project"

  if (cd "$control" && "$sa" --agent reviewer "hello" >"$out" 2>"$err"); then
    rc=0
  else
    rc=$?
  fi

  stderr_text="$(tr '\n' ' ' <"$err" | sed 's/  */ /g')"
  assert_eq "2" "$rc" "stale workspace should stop execution"
  assert_contains "$stderr_text" "configured workspace is no longer a git repository" "stale workspace error should be explicit"
  printf 'ok - stale workspace configuration is rejected\n'
}

test_subagent_worktree_create_requires_workspace_init() {
  local repo out err rc stderr_text
  repo="$(new_repo)"
  out="$(new_temp_file)"
  err="$(new_temp_file)"

  if (cd "$repo" && "$sa" --agent reviewer worktree create reviewer >"$out" 2>"$err"); then
    rc=0
  else
    rc=$?
  fi

  stderr_text="$(tr '\n' ' ' <"$err" | sed 's/  */ /g')"
  assert_eq "2" "$rc" "sub-agent worktree create should require workspace init"
  assert_contains "$stderr_text" "target workspace is not configured" "worktree create should explain missing workspace"
  printf 'ok - sub-agent worktree management requires explicit workspace\n'
}

test_subagent_rejects_external_paths() {
  local repo other stub_dir capture out err rc stderr_text
  repo="$(new_repo init project/file.txt)"
  other="$(new_repo)"
  stub_dir="$(new_temp_dir)"
  capture="$(new_temp_file)"
  out="$(new_temp_file)"
  err="$(new_temp_file)"

  cat >"$stub_dir/codex" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$@" > "$capture"
printf '%s\n' '{"type":"thread.started","thread_id":"tid-123"}'
EOF
  chmod +x "$stub_dir/codex"

  (
    cd "$repo"
    "$sa" workspace init . >/dev/null
  )

  if (cd "$repo" && PATH="$stub_dir:$PATH" "$sa" --agent reviewer - -- --cd "$other" <<'EOF' >"$out" 2>"$err"
hello
EOF
  ); then
    rc=0
  else
    rc=$?
  fi

  stderr_text="$(tr '\n' ' ' <"$err" | sed 's/  */ /g')"
  assert_eq "2" "$rc" "sub-agent should reject external --cd"
  assert_contains "$stderr_text" "--cd must stay within configured workspace" "external --cd should be rejected explicitly"

  if (cd "$repo" && PATH="$stub_dir:$PATH" "$sa" --agent reviewer - -- --add-dir "$other" <<'EOF' >"$out" 2>"$err"
hello
EOF
  ); then
    rc=0
  else
    rc=$?
  fi

  stderr_text="$(tr '\n' ' ' <"$err" | sed 's/  */ /g')"
  assert_eq "2" "$rc" "sub-agent should reject external --add-dir"
  assert_contains "$stderr_text" "--add-dir must stay within configured workspace" "external --add-dir should be rejected explicitly"
  printf 'ok - sub-agent rejects external filesystem paths\n'
}

test_subagent_rewrites_internal_add_dir_into_worktree() {
  local repo stub_dir capture out err rc argv
  repo="$(new_repo init project/shared.txt)"
  stub_dir="$(new_temp_dir)"
  capture="$(new_temp_file)"
  out="$(new_temp_file)"
  err="$(new_temp_file)"

  cat >"$stub_dir/codex" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$@" > "$capture"
printf '%s\n' '{"type":"thread.started","thread_id":"tid-123"}'
EOF
  chmod +x "$stub_dir/codex"

  (
    cd "$repo"
    "$sa" workspace init . >/dev/null
  )

  if (cd "$repo" && PATH="$stub_dir:$PATH" "$sa" --agent reviewer - -- --add-dir project <<'EOF' >"$out" 2>"$err"
hello
EOF
  ); then
    rc=0
  else
    rc=$?
  fi

  argv="$(tr '\n' ' ' <"$capture" | sed 's/  */ /g')"
  assert_eq "0" "$rc" "sub-agent should allow workspace-internal --add-dir"
  assert_contains "$argv" "--add-dir $repo/.codex-second-agent/" "internal --add-dir should be rewritten into the agent worktree"
  assert_contains "$argv" "/worktrees/reviewer/project" "internal --add-dir should point inside the reviewer worktree"
  printf 'ok - workspace-internal add-dir is rewritten into worktree path\n'
}

test_model_overrides_are_stripped() {
  local repo stub_dir capture out err rc argv
  repo="$(new_repo)"
  stub_dir="$(new_temp_dir)"
  capture="$(new_temp_file)"
  out="$(new_temp_file)"
  err="$(new_temp_file)"

  cat >"$stub_dir/codex" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$@" > "$capture"
printf '%s\n' '{"type":"thread.started","thread_id":"tid-123"}'
EOF
  chmod +x "$stub_dir/codex"

  if (cd "$repo" && PATH="$stub_dir:$PATH" "$sa" - -- --config 'model="o3"' --config 'model_provider="oss"' --oss --profile alt --local-provider ollama <<'EOF' >"$out" 2>"$err"
hello
EOF
  ); then
    rc=0
  else
    rc=$?
  fi

  argv="$(tr '\n' ' ' <"$capture" | sed 's/  */ /g')"
  assert_eq "0" "$rc" "wrapper should still execute when model override flags are supplied"
  assert_contains "$argv" "--model gpt-5.5" "forced model should be passed"
  assert_not_contains "$argv" 'model="o3"' "model config override should be stripped"
  assert_not_contains "$argv" "model_provider=\"oss\"" "model provider override should be stripped"
  assert_not_contains "$argv" "--oss" "oss shortcut should be stripped"
  assert_contains "$argv" "--profile alt" "non-model profile settings should be preserved"
  assert_not_contains "$argv" "ollama" "local provider should be stripped"
  printf 'ok - model selection overrides are stripped and gpt-5.5 is forced\n'
}

test_filter_failure_returns_nonzero() {
  local repo stub_dir out err rc state key agent_dir logs_dir stderr_text
  repo="$(new_repo)"
  stub_dir="$(new_temp_dir)"
  out="$(new_temp_file)"
  err="$(new_temp_file)"

  cat >"$stub_dir/codex" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' '{"type":"thread.started","thread_id":"tid-123"}'
printf '%s\n' '{"type":"item.completed","item":{"type":"agent_message","text":"hello"}}'
EOF
  chmod +x "$stub_dir/codex"

  state="$repo/.codex-second-agent"
  key="$(printf '%s' "$repo" | sha256sum | awk '{print $1}')"
  agent_dir="$state/$key/agents/default"
  logs_dir="$agent_dir/logs"
  mkdir -p "$logs_dir"
  chmod 500 "$agent_dir"
  chmod 700 "$logs_dir"

  if (cd "$repo" && PATH="$stub_dir:$PATH" "$sa" "hello" >"$out" 2>"$err"); then
    rc=0
  else
    rc=$?
  fi

  stderr_text="$(tr '\n' ' ' <"$err" | sed 's/  */ /g')"
  assert_eq "1" "$rc" "session persistence failure should bubble up"
  assert_contains "$stderr_text" "failed to persist session_id" "session persistence failure should be reported"
  printf 'ok - persistence failures return nonzero\n'
}

test_raw_json_still_records_transcript() {
  local repo stub_dir out err rc state key transcript_line stdout_text
  repo="$(new_repo)"
  stub_dir="$(new_temp_dir)"
  out="$(new_temp_file)"
  err="$(new_temp_file)"

  cat >"$stub_dir/codex" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' '{"type":"thread.started","thread_id":"tid-123"}'
printf '%s\n' '{"type":"item.completed","item":{"type":"agent_message","text":"hello"}}'
EOF
  chmod +x "$stub_dir/codex"

  if (cd "$repo" && PATH="$stub_dir:$PATH" "$sa" --raw-json "hello" >"$out" 2>"$err"); then
    rc=0
  else
    rc=$?
  fi

  state="$repo/.codex-second-agent"
  key="$(printf '%s' "$repo" | sha256sum | awk '{print $1}')"
  if [[ ! -f "$state/$key/agents/default/logs/transcript.jsonl" ]]; then
    printf 'not ok - raw-json execution should still write transcript log\nmissing: %s\n' "$state/$key/agents/default/logs/transcript.jsonl" >&2
    exit 1
  fi
  transcript_line="$(tail -n 1 "$state/$key/agents/default/logs/transcript.jsonl")"
  stdout_text="$(cat "$out")"

  assert_eq "0" "$rc" "raw-json execution should succeed"
  assert_contains "$stdout_text" '"type":"thread.started"' "raw-json stdout should include codex events"
  assert_contains "$transcript_line" '"response": "hello"' "raw-json execution should still record transcript text"
  printf 'ok - raw-json execution still records transcript text\n'
}

test_nondefault_execution_creates_worktree_and_session() {
  local repo stub_dir out err rc state key count session_count
  repo="$(new_repo)"
  stub_dir="$(new_temp_dir)"
  out="$(new_temp_file)"
  err="$(new_temp_file)"

  cat >"$stub_dir/codex" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' '{"type":"thread.started","thread_id":"tid-123"}'
printf '%s\n' '{"type":"item.completed","item":{"type":"agent_message","text":"hello"}}'
EOF
  chmod +x "$stub_dir/codex"

  (
    cd "$repo"
    "$sa" workspace init . >/dev/null
  )

  if (cd "$repo" && PATH="$stub_dir:$PATH" "$sa" --agent reviewer "hello" >"$out" 2>"$err"); then
    rc=0
  else
    rc=$?
  fi

  state="$repo/.codex-second-agent"
  key="$(printf '%s' "$repo" | sha256sum | awk '{print $1}')"
  count="$(git -C "$repo" worktree list | wc -l | tr -d ' ')"
  session_count="$(find "$state/$key/agents/reviewer" -name session_id -type f | wc -l | tr -d ' ')"
  assert_eq "0" "$rc" "nondefault execution should succeed after workspace init"
  assert_eq "2" "$count" "nondefault execution should create a worktree"
  assert_eq "1" "$session_count" "nondefault execution should persist a session id"
  printf 'ok - nondefault execution creates worktree and session state\n'
}

test_target_workspace_state_is_shared_across_control_repos() {
  local control1 control2 target stub_dir capture1 capture2 out err rc argv
  local key target_session_count control1_session_count control2_session_count
  control1="$(new_repo)"
  control2="$(new_repo)"
  target="$(new_repo)"
  stub_dir="$(new_temp_dir)"
  capture1="$(new_temp_file)"
  capture2="$(new_temp_file)"
  out="$(new_temp_file)"
  err="$(new_temp_file)"

  cat >"$stub_dir/codex" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$@" > "$CAPTURE_PATH"
printf '%s\n' '{"type":"thread.started","thread_id":"tid-123"}'
printf '%s\n' '{"type":"item.completed","item":{"type":"agent_message","text":"hello"}}'
EOF
  chmod +x "$stub_dir/codex"

  (
    cd "$control1"
    "$sa" workspace init "$target" >/dev/null
  )
  (
    cd "$control2"
    "$sa" workspace init "$target" >/dev/null
  )

  if (cd "$control1" && CAPTURE_PATH="$capture1" PATH="$stub_dir:$PATH" "$sa" "hello" >"$out" 2>"$err"); then
    rc=0
  else
    rc=$?
  fi
  assert_eq "0" "$rc" "first control repo execution should succeed"

  if (cd "$control2" && CAPTURE_PATH="$capture2" PATH="$stub_dir:$PATH" "$sa" "hello" >"$out" 2>"$err"); then
    rc=0
  else
    rc=$?
  fi
  assert_eq "0" "$rc" "second control repo execution should succeed"

  key="$(printf '%s' "$target" | sha256sum | awk '{print $1}')"
  target_session_count="$(find "$target/.codex-second-agent/$key" -name session_id -type f | wc -l | tr -d ' ')"
  control1_session_count="$(find "$control1/.codex-second-agent" -name session_id -type f 2>/dev/null | wc -l | tr -d ' ')"
  control2_session_count="$(find "$control2/.codex-second-agent" -name session_id -type f 2>/dev/null | wc -l | tr -d ' ')"
  argv="$(tr '\n' ' ' <"$capture2" | sed 's/  */ /g')"

  assert_eq "1" "$target_session_count" "session state should live under the target workspace"
  assert_eq "0" "$control1_session_count" "control repo must not own runtime session state"
  assert_eq "0" "$control2_session_count" "other control repo must not own runtime session state"
  assert_contains "$argv" "resume tid-123" "second control repo should resume the shared target-workspace session"
  printf 'ok - target workspace runtime state is shared across control repos\n'
}

main() {
  test_management_commands_are_side_effect_free
  test_parent_workspace_cd_maps_into_agent_worktree
  test_project_workspace_without_cd_uses_worktree_root
  test_stale_workspace_is_rejected
  test_subagent_worktree_create_requires_workspace_init
  test_subagent_rejects_external_paths
  test_subagent_rewrites_internal_add_dir_into_worktree
  test_model_overrides_are_stripped
  test_filter_failure_returns_nonzero
  test_raw_json_still_records_transcript
  test_nondefault_execution_creates_worktree_and_session
  test_target_workspace_state_is_shared_across_control_repos
}

main "$@"
